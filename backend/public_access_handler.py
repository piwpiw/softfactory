"""
SoftFactory Public Access Handler
Manages ngrok tunnel URL updates, CORS configuration, and public access logging
"""

import os
import json
import logging
from datetime import datetime, timedelta
from functools import wraps
from pathlib import Path
from typing import Optional, Dict, Any, List

import requests
from flask import request, jsonify, current_app

logger = logging.getLogger(__name__)


class PublicAccessManager:
    """Manages public URL discovery, whitelist enforcement, and access logging"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize PublicAccessManager

        Args:
            config: Configuration dict with keys:
                - whitelist_file: Path to IP whitelist JSON file
                - access_log_file: Path to access log file
                - ngrok_url_file: Path to ngrok URL file
                - enable_logging: Enable/disable access logging
                - whitelist_enabled: Enable/disable IP whitelist enforcement
        """
        self.config = config or {}
        self.whitelist_file = self.config.get('whitelist_file', 'access_whitelist.json')
        self.access_log_file = self.config.get('access_log_file', 'logs/access.log')
        self.ngrok_url_file = self.config.get('ngrok_url_file', 'logs/ngrok-url.txt')
        self.enable_logging = self.config.get('enable_logging', True)
        self.whitelist_enabled = self.config.get('whitelist_enabled', False)

        # Create log directory if needed
        os.makedirs(os.path.dirname(self.access_log_file), exist_ok=True)

        # Load whitelist on initialization
        self._whitelist = self._load_whitelist()
        self._public_url = None
        self._url_last_updated = None

    @staticmethod
    def get_client_ip(request_obj=None) -> str:
        """
        Extract client IP from request, accounting for proxies

        Args:
            request_obj: Flask request object (uses current_request if None)

        Returns:
            Client IP address
        """
        if request_obj is None:
            request_obj = request

        # Check for IP from reverse proxy headers (set by ngrok)
        if request_obj.headers.getlist("X-Forwarded-For"):
            return request_obj.headers.getlist("X-Forwarded-For")[0].split(',')[0]

        # Check CF-Connecting-IP (CloudFlare)
        if request_obj.headers.get("CF-Connecting-IP"):
            return request_obj.headers.get("CF-Connecting-IP")

        # Fallback to direct connection
        return request_obj.remote_addr or "unknown"

    def _load_whitelist(self) -> Dict[str, Any]:
        """Load IP whitelist from JSON file"""
        if not os.path.exists(self.whitelist_file):
            logger.info(f"Whitelist file not found: {self.whitelist_file}")
            return {"enabled": False, "ips": [], "updated_at": None}

        try:
            with open(self.whitelist_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load whitelist: {e}")
            return {"enabled": False, "ips": [], "updated_at": None}

    def save_whitelist(self, ips: List[str], enabled: bool = True) -> bool:
        """Save IP whitelist to file"""
        try:
            whitelist = {
                "enabled": enabled,
                "ips": ips,
                "updated_at": datetime.utcnow().isoformat(),
                "description": "IP whitelist for SoftFactory public access"
            }

            os.makedirs(os.path.dirname(self.whitelist_file), exist_ok=True)
            with open(self.whitelist_file, 'w') as f:
                json.dump(whitelist, f, indent=2)

            self._whitelist = whitelist
            logger.info(f"Whitelist saved: {len(ips)} IPs")
            return True
        except Exception as e:
            logger.error(f"Failed to save whitelist: {e}")
            return False

    def is_ip_whitelisted(self, ip: str) -> bool:
        """Check if IP is whitelisted"""
        if not self._whitelist.get("enabled", False):
            return True  # No restrictions if disabled

        return ip in self._whitelist.get("ips", [])

    def log_access(self, method: str, path: str, status_code: int,
                   response_time: float, error: Optional[str] = None) -> None:
        """
        Log access attempt

        Args:
            method: HTTP method
            path: Request path
            status_code: Response status code
            response_time: Request processing time in ms
            error: Error message if applicable
        """
        if not self.enable_logging:
            return

        try:
            client_ip = self.get_client_ip()
            timestamp = datetime.utcnow().isoformat()

            log_entry = {
                "timestamp": timestamp,
                "client_ip": client_ip,
                "method": method,
                "path": path,
                "status": status_code,
                "response_time_ms": response_time,
                "error": error,
                "whitelisted": self.is_ip_whitelisted(client_ip)
            }

            # Append to log file
            os.makedirs(os.path.dirname(self.access_log_file), exist_ok=True)
            with open(self.access_log_file, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')

        except Exception as e:
            logger.error(f"Failed to log access: {e}")

    def get_public_url(self, force_refresh: bool = False) -> Optional[str]:
        """
        Get current public URL from ngrok

        Args:
            force_refresh: Force refresh from ngrok API

        Returns:
            Public URL or None if not available
        """
        # Check if we have a cached URL and it's still fresh
        if self._public_url and not force_refresh:
            if self._url_last_updated and \
               datetime.utcnow() - self._url_last_updated < timedelta(minutes=5):
                return self._public_url

        # Try to fetch from ngrok file first (fastest)
        if os.path.exists(self.ngrok_url_file):
            try:
                with open(self.ngrok_url_file, 'r') as f:
                    url = f.read().strip()
                    if url and url.startswith('http'):
                        self._public_url = url
                        self._url_last_updated = datetime.utcnow()
                        return url
            except Exception as e:
                logger.warning(f"Failed to read ngrok URL file: {e}")

        # Try ngrok API (backup)
        try:
            response = requests.get('http://127.0.0.1:4040/api/tunnels', timeout=2)
            if response.status_code == 200:
                tunnels = response.json().get('tunnels', [])
                for tunnel in tunnels:
                    if tunnel.get('proto') == 'http':
                        url = tunnel.get('public_url')
                        if url:
                            self._public_url = url
                            self._url_last_updated = datetime.utcnow()
                            return url
        except Exception as e:
            logger.warning(f"Failed to fetch ngrok URL from API: {e}")

        return self._public_url  # Return cached if available

    def get_access_stats(self) -> Dict[str, Any]:
        """
        Get access log statistics

        Returns:
            Stats dict with counts, errors, IP distribution, etc.
        """
        if not os.path.exists(self.access_log_file):
            return {
                "total_requests": 0,
                "errors": 0,
                "ips": {},
                "paths": {},
                "status_codes": {}
            }

        stats = {
            "total_requests": 0,
            "errors": 0,
            "ips": {},
            "paths": {},
            "status_codes": {},
            "avg_response_time": 0,
            "last_24h": 0
        }

        response_times = []
        cutoff_time = datetime.utcnow() - timedelta(hours=24)

        try:
            with open(self.access_log_file, 'r') as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        stats["total_requests"] += 1

                        # Count errors
                        if entry.get('error'):
                            stats["errors"] += 1

                        # Track response times
                        if 'response_time_ms' in entry:
                            response_times.append(entry['response_time_ms'])

                        # Count IPs
                        ip = entry.get('client_ip', 'unknown')
                        stats["ips"][ip] = stats["ips"].get(ip, 0) + 1

                        # Count paths
                        path = entry.get('path', 'unknown')
                        stats["paths"][path] = stats["paths"].get(path, 0) + 1

                        # Count status codes
                        status = str(entry.get('status', 'unknown'))
                        stats["status_codes"][status] = stats["status_codes"].get(status, 0) + 1

                        # Count last 24h
                        if datetime.fromisoformat(entry.get('timestamp', '')) > cutoff_time:
                            stats["last_24h"] += 1

                    except json.JSONDecodeError:
                        continue

            # Calculate average response time
            if response_times:
                stats["avg_response_time"] = sum(response_times) / len(response_times)

        except Exception as e:
            logger.error(f"Failed to read access stats: {e}")

        return stats

    def get_recent_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent access log entries"""
        logs = []

        if not os.path.exists(self.access_log_file):
            return logs

        try:
            with open(self.access_log_file, 'r') as f:
                lines = f.readlines()
                for line in lines[-limit:]:
                    try:
                        logs.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            logger.error(f"Failed to read recent logs: {e}")

        return logs


# Singleton instance
_access_manager: Optional[PublicAccessManager] = None


def get_access_manager() -> PublicAccessManager:
    """Get or create the PublicAccessManager singleton"""
    global _access_manager
    if _access_manager is None:
        config = {
            'whitelist_file': 'access_whitelist.json',
            'access_log_file': 'logs/access.log',
            'ngrok_url_file': 'logs/ngrok-url.txt',
            'enable_logging': True,
            'whitelist_enabled': False
        }
        _access_manager = PublicAccessManager(config)
    return _access_manager


def require_public_access(f):
    """
    Decorator to enforce public access restrictions

    Usage:
        @app.route('/api/public/data')
        @require_public_access
        def get_public_data():
            return jsonify({'data': 'public'})
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        manager = get_access_manager()
        client_ip = manager.get_client_ip()

        # Check whitelist
        if not manager.is_ip_whitelisted(client_ip):
            logger.warning(f"Access denied for non-whitelisted IP: {client_ip}")
            return jsonify({'error': 'Access denied'}), 403

        return f(*args, **kwargs)

    return decorated_function


def log_access_decorator(f):
    """
    Decorator to log all public access requests

    Usage:
        @app.route('/api/public/data')
        @log_access_decorator
        def get_public_data():
            return jsonify({'data': 'public'})
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        import time
        start_time = time.time()
        manager = get_access_manager()

        try:
            result = f(*args, **kwargs)
            status_code = result[1] if isinstance(result, tuple) else 200
        except Exception as e:
            status_code = 500
            result = None
            raise
        finally:
            response_time = (time.time() - start_time) * 1000  # Convert to ms
            manager.log_access(
                method=request.method,
                path=request.path,
                status_code=status_code,
                response_time=response_time
            )

        return result

    return decorated_function


def register_public_access_endpoints(app):
    """
    Register public access management endpoints

    Adds the following endpoints:
    - GET /api/public/url - Get current public URL
    - GET /api/public/stats - Get access statistics
    - GET /api/public/logs - Get recent access logs
    - POST /api/admin/whitelist - Update IP whitelist
    - GET /api/admin/whitelist - Get current whitelist
    """
    manager = get_access_manager()

    @app.route('/api/public/url', methods=['GET'])
    def get_public_url():
        """Get current public URL"""
        url = manager.get_public_url(force_refresh=request.args.get('refresh') == 'true')
        return jsonify({
            'public_url': url,
            'local_url': 'http://localhost:8000',
            'status': 'active' if url else 'inactive',
            'timestamp': datetime.utcnow().isoformat()
        }), 200

    @app.route('/api/public/stats', methods=['GET'])
    def get_access_stats():
        """Get access statistics"""
        stats = manager.get_access_stats()
        return jsonify({
            'stats': stats,
            'timestamp': datetime.utcnow().isoformat()
        }), 200

    @app.route('/api/public/logs', methods=['GET'])
    def get_access_logs():
        """Get recent access logs"""
        limit = request.args.get('limit', 100, type=int)
        logs = manager.get_recent_logs(limit=limit)
        return jsonify({
            'logs': logs,
            'count': len(logs),
            'timestamp': datetime.utcnow().isoformat()
        }), 200

    @app.route('/api/admin/whitelist', methods=['GET'])
    def get_whitelist():
        """Get current IP whitelist"""
        if not manager._whitelist.get('enabled'):
            return jsonify({'error': 'Whitelist not enabled'}), 400

        return jsonify({
            'whitelist': manager._whitelist,
            'timestamp': datetime.utcnow().isoformat()
        }), 200

    @app.route('/api/admin/whitelist', methods=['POST'])
    def update_whitelist():
        """Update IP whitelist (requires auth in production)"""
        data = request.get_json() or {}
        ips = data.get('ips', [])
        enabled = data.get('enabled', True)

        if not isinstance(ips, list):
            return jsonify({'error': 'ips must be a list'}), 400

        if manager.save_whitelist(ips, enabled):
            return jsonify({
                'message': 'Whitelist updated',
                'count': len(ips),
                'enabled': enabled,
                'timestamp': datetime.utcnow().isoformat()
            }), 200
        else:
            return jsonify({'error': 'Failed to save whitelist'}), 500

    logger.info("Public access endpoints registered")
