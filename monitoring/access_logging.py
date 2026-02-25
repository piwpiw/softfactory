"""
SoftFactory Access Logging and Monitoring
Comprehensive audit trail for public access with real-time monitoring capabilities
"""

import os
import json
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, List, Any
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class AccessLevel(Enum):
    """Access level classification"""
    PUBLIC = "public"
    AUTHENTICATED = "authenticated"
    ADMIN = "admin"
    SYSTEM = "system"


class RequestStatus(Enum):
    """Request status classification"""
    SUCCESS = "success"
    CLIENT_ERROR = "client_error"  # 4xx
    SERVER_ERROR = "server_error"  # 5xx
    TIMEOUT = "timeout"
    BLOCKED = "blocked"


@dataclass
class AccessLogEntry:
    """Structured access log entry"""
    timestamp: str
    request_id: str
    client_ip: str
    method: str
    path: str
    status_code: int
    response_time_ms: float
    request_size_bytes: int
    response_size_bytes: int
    access_level: str
    user_agent: str
    referer: Optional[str]
    error: Optional[str]
    whitelisted: bool
    authenticated: bool
    user_id: Optional[str]
    session_id: Optional[str]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)

    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict())


class AccessMonitor:
    """
    Real-time access monitoring with metrics, alerts, and historical analysis
    """

    def __init__(self, log_dir: str = 'logs'):
        """
        Initialize AccessMonitor

        Args:
            log_dir: Directory for log files
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Log files
        self.access_log = self.log_dir / 'access_detailed.jsonl'
        self.metrics_log = self.log_dir / 'metrics.json'
        self.incidents_log = self.log_dir / 'incidents.jsonl'

        # In-memory metrics (last 1000 requests)
        self.recent_requests = deque(maxlen=1000)

        # Aggregated metrics
        self.metrics = {
            'total_requests': 0,
            'total_errors': 0,
            'total_blocked': 0,
            'avg_response_time': 0,
            'p95_response_time': 0,
            'p99_response_time': 0,
            'status_codes': defaultdict(int),
            'methods': defaultdict(int),
            'paths': defaultdict(int),
            'ips': defaultdict(int),
            'errors': defaultdict(int),
            'endpoints': defaultdict(lambda: {
                'count': 0,
                'avg_response_time': 0,
                'errors': 0
            })
        }

        # Rate limiting state
        self.ip_request_times = defaultdict(deque)  # IP -> deque of timestamps
        self.rate_limit_threshold = 100  # requests per minute
        self.rate_limit_window = 60  # seconds

        # Load existing metrics if available
        self._load_metrics()

    def _load_metrics(self) -> None:
        """Load existing metrics from file"""
        if self.metrics_log.exists():
            try:
                with open(self.metrics_log, 'r') as f:
                    data = json.load(f)
                    self.metrics.update(data)
                logger.info(f"Loaded existing metrics: {self.metrics['total_requests']} total requests")
            except Exception as e:
                logger.error(f"Failed to load metrics: {e}")

    def _save_metrics(self) -> None:
        """Persist metrics to file"""
        try:
            metrics_copy = {
                k: v if not isinstance(v, defaultdict) else dict(v)
                for k, v in self.metrics.items()
            }
            with open(self.metrics_log, 'w') as f:
                json.dump(metrics_copy, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save metrics: {e}")

    def log_request(self, entry: AccessLogEntry) -> None:
        """
        Log a request

        Args:
            entry: AccessLogEntry object
        """
        try:
            # Write to detailed log
            with open(self.access_log, 'a') as f:
                f.write(entry.to_json() + '\n')

            # Add to in-memory cache
            self.recent_requests.append(entry.to_dict())

            # Update metrics
            self._update_metrics(entry)

            # Check for incidents
            self._check_incidents(entry)

        except Exception as e:
            logger.error(f"Failed to log request: {e}")

    def _update_metrics(self, entry: AccessLogEntry) -> None:
        """Update aggregated metrics"""
        self.metrics['total_requests'] += 1

        # Status code
        self.metrics['status_codes'][entry.status_code] += 1

        # Error tracking
        if entry.status_code >= 400:
            self.metrics['total_errors'] += 1
            if entry.error:
                self.metrics['errors'][entry.error] += 1

        # Blocked requests
        if not entry.whitelisted:
            self.metrics['total_blocked'] += 1

        # Methods and paths
        self.metrics['methods'][entry.method] += 1
        self.metrics['paths'][entry.path] += 1
        self.metrics['ips'][entry.client_ip] += 1

        # Endpoint metrics
        endpoint_key = f"{entry.method} {entry.path}"
        self.metrics['endpoints'][endpoint_key]['count'] += 1
        self.metrics['endpoints'][endpoint_key]['errors'] += 1 if entry.status_code >= 400 else 0

        # Response time
        response_times = [r['response_time_ms'] for r in self.recent_requests]
        if response_times:
            self.metrics['avg_response_time'] = sum(response_times) / len(response_times)
            sorted_times = sorted(response_times)
            self.metrics['p95_response_time'] = sorted_times[int(len(sorted_times) * 0.95)]
            self.metrics['p99_response_time'] = sorted_times[int(len(sorted_times) * 0.99)]

        # Rate limiting check
        self._check_rate_limit(entry.client_ip, entry.timestamp)

        # Persist metrics periodically
        if self.metrics['total_requests'] % 100 == 0:
            self._save_metrics()

    def _check_incidents(self, entry: AccessLogEntry) -> None:
        """Check for notable incidents and log them"""
        incidents = []

        # High response time
        if entry.response_time_ms > 5000:
            incidents.append({
                'type': 'SLOW_RESPONSE',
                'threshold_ms': 5000,
                'actual_ms': entry.response_time_ms,
                'endpoint': f"{entry.method} {entry.path}"
            })

        # Server errors
        if entry.status_code >= 500:
            incidents.append({
                'type': 'SERVER_ERROR',
                'status': entry.status_code,
                'error': entry.error
            })

        # Repeated 4xx errors from same IP
        ip_errors = sum(1 for r in self.recent_requests
                       if r.get('client_ip') == entry.client_ip and r.get('status_code', 0) >= 400)
        if ip_errors > 10:
            incidents.append({
                'type': 'REPEATED_CLIENT_ERRORS',
                'ip': entry.client_ip,
                'count': ip_errors
            })

        # Log incidents
        for incident in incidents:
            self._log_incident({
                'timestamp': entry.timestamp,
                'request_id': entry.request_id,
                'incident': incident
            })

    def _check_rate_limit(self, ip: str, timestamp_str: str) -> None:
        """Track rate limiting"""
        try:
            timestamp = datetime.fromisoformat(timestamp_str).timestamp()
        except:
            timestamp = time.time()

        # Clean old timestamps
        cutoff = timestamp - self.rate_limit_window
        self.ip_request_times[ip] = deque(
            t for t in self.ip_request_times[ip] if t > cutoff,
            maxlen=self.rate_limit_threshold + 10
        )

        # Add current request
        self.ip_request_times[ip].append(timestamp)

        # Check if rate limit exceeded
        if len(self.ip_request_times[ip]) > self.rate_limit_threshold:
            self._log_incident({
                'timestamp': timestamp_str,
                'incident': {
                    'type': 'RATE_LIMIT_EXCEEDED',
                    'ip': ip,
                    'requests_in_window': len(self.ip_request_times[ip]),
                    'threshold': self.rate_limit_threshold
                }
            })

    def _log_incident(self, incident: Dict[str, Any]) -> None:
        """Log an incident"""
        try:
            with open(self.incidents_log, 'a') as f:
                f.write(json.dumps(incident) + '\n')
        except Exception as e:
            logger.error(f"Failed to log incident: {e}")

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get metrics summary"""
        return {
            'total_requests': self.metrics['total_requests'],
            'total_errors': self.metrics['total_errors'],
            'total_blocked': self.metrics['total_blocked'],
            'error_rate': self.metrics['total_errors'] / max(self.metrics['total_requests'], 1),
            'avg_response_time_ms': self.metrics['avg_response_time'],
            'p95_response_time_ms': self.metrics['p95_response_time'],
            'p99_response_time_ms': self.metrics['p99_response_time'],
            'top_ips': sorted(self.metrics['ips'].items(), key=lambda x: x[1], reverse=True)[:10],
            'top_paths': sorted(self.metrics['paths'].items(), key=lambda x: x[1], reverse=True)[:10],
            'status_codes': dict(self.metrics['status_codes']),
            'methods': dict(self.metrics['methods']),
            'recent_requests': len(self.recent_requests),
            'timestamp': datetime.utcnow().isoformat()
        }

    def get_incidents(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent incidents"""
        incidents = []

        if not self.incidents_log.exists():
            return incidents

        try:
            with open(self.incidents_log, 'r') as f:
                lines = f.readlines()
                for line in lines[-limit:]:
                    try:
                        incidents.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            logger.error(f"Failed to read incidents: {e}")

        return incidents

    def get_top_endpoints(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get top endpoints by request count"""
        endpoints = sorted(
            [
                {
                    'endpoint': k,
                    'requests': v['count'],
                    'errors': v['errors'],
                    'error_rate': v['errors'] / max(v['count'], 1)
                }
                for k, v in self.metrics['endpoints'].items()
            ],
            key=lambda x: x['requests'],
            reverse=True
        )
        return endpoints[:limit]

    def get_traffic_by_hour(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get hourly traffic statistics"""
        hourly_stats = defaultdict(lambda: {'requests': 0, 'errors': 0})

        if not self.access_log.exists():
            return []

        try:
            cutoff = datetime.utcnow() - timedelta(hours=hours)
            with open(self.access_log, 'r') as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        timestamp = datetime.fromisoformat(entry['timestamp'])
                        if timestamp > cutoff:
                            hour_key = timestamp.strftime('%Y-%m-%d %H:00:00')
                            hourly_stats[hour_key]['requests'] += 1
                            if entry['status_code'] >= 400:
                                hourly_stats[hour_key]['errors'] += 1
                    except (json.JSONDecodeError, ValueError):
                        continue
        except Exception as e:
            logger.error(f"Failed to read traffic stats: {e}")

        return [
            {'hour': k, **v}
            for k, v in sorted(hourly_stats.items())
        ]

    def generate_report(self) -> str:
        """Generate a comprehensive monitoring report"""
        summary = self.get_metrics_summary()
        incidents = self.get_incidents(limit=10)
        endpoints = self.get_top_endpoints(limit=10)
        traffic = self.get_traffic_by_hour(hours=24)

        report = f"""
# SoftFactory Access Monitoring Report
Generated: {datetime.utcnow().isoformat()}

## Summary
- Total Requests: {summary['total_requests']:,}
- Total Errors: {summary['total_errors']:,} ({summary['error_rate']*100:.1f}%)
- Blocked Requests: {summary['total_blocked']:,}
- Avg Response Time: {summary['avg_response_time_ms']:.1f}ms
- P95 Response Time: {summary['p95_response_time_ms']:.1f}ms
- P99 Response Time: {summary['p99_response_time_ms']:.1f}ms

## Top IPs
"""
        for ip, count in summary['top_ips']:
            report += f"- {ip}: {count:,} requests\n"

        report += "\n## Top Endpoints\n"
        for ep in endpoints:
            report += f"- {ep['endpoint']}: {ep['requests']} requests ({ep['error_rate']*100:.1f}% errors)\n"

        if incidents:
            report += f"\n## Recent Incidents ({len(incidents)})\n"
            for incident in incidents[:5]:
                report += f"- {incident.get('incident', {}).get('type', 'UNKNOWN')}: {incident['timestamp']}\n"

        return report


# Singleton instance
_monitor: Optional[AccessMonitor] = None


def get_monitor() -> AccessMonitor:
    """Get or create the AccessMonitor singleton"""
    global _monitor
    if _monitor is None:
        _monitor = AccessMonitor()
    return _monitor
