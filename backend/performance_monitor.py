"""Performance Monitoring & Metrics Collection"""
import time
import os
from functools import wraps
from flask import request, g, jsonify
from datetime import datetime
import json
from pathlib import Path
import psutil

class PerformanceMonitor:
    """Track API request performance and system metrics"""

    def __init__(self):
        self.metrics = []
        self.log_path = Path(__file__).parent.parent / 'logs' / 'performance.jsonl'
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def record_request(self, endpoint, method, duration_ms, status_code, db_queries=0, cache_hits=0):
        """Record a request metric"""
        metric = {
            'timestamp': datetime.utcnow().isoformat(),
            'endpoint': endpoint,
            'method': method,
            'duration_ms': duration_ms,
            'status_code': status_code,
            'db_queries': db_queries,
            'cache_hits': cache_hits
        }
        self.metrics.append(metric)
        self._write_to_log(metric)

    def _write_to_log(self, metric):
        """Write metric to JSONL log file"""
        try:
            with open(self.log_path, 'a') as f:
                f.write(json.dumps(metric) + '\n')
        except Exception as e:
            print(f"Failed to write performance metric: {e}")

    def get_system_metrics(self):
        """Get current system resource usage"""
        process = psutil.Process(os.getpid())
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'memory_mb': process.memory_info().rss / 1024 / 1024,
            'cpu_percent': process.cpu_percent(interval=0.1),
            'num_threads': process.num_threads(),
            'open_files': len(process.open_files()) if hasattr(process, 'open_files') else 0
        }

# Global monitor instance
_monitor = PerformanceMonitor()

def monitor_performance(f):
    """Decorator to monitor endpoint performance"""
    @wraps(f)
    def decorated(*args, **kwargs):
        start_time = time.time()
        g.request_start_time = start_time
        g.db_query_count = 0
        g.cache_hits = 0

        try:
            result = f(*args, **kwargs)
            status_code = result[1] if isinstance(result, tuple) else 200
        except Exception as e:
            status_code = 500
            raise
        finally:
            duration_ms = (time.time() - start_time) * 1000
            endpoint = request.endpoint or 'unknown'
            method = request.method

            db_queries = getattr(g, 'db_query_count', 0)
            cache_hits = getattr(g, 'cache_hits', 0)

            _monitor.record_request(
                endpoint=endpoint,
                method=method,
                duration_ms=round(duration_ms, 2),
                status_code=status_code,
                db_queries=db_queries,
                cache_hits=cache_hits
            )

        return result
    return decorated

def get_performance_stats(endpoint=None, method=None, minutes=60):
    """Get performance statistics from metrics"""
    from datetime import datetime, timedelta

    cutoff = datetime.utcnow() - timedelta(minutes=minutes)
    metrics = []

    try:
        if _monitor.log_path.exists():
            with open(_monitor.log_path, 'r') as f:
                for line in f:
                    try:
                        m = json.loads(line)
                        ts = datetime.fromisoformat(m['timestamp'])
                        if ts >= cutoff:
                            if (not endpoint or m['endpoint'] == endpoint) and \
                               (not method or m['method'] == method):
                                metrics.append(m)
                    except:
                        continue
    except Exception as e:
        print(f"Error reading metrics: {e}")

    if not metrics:
        return None

    durations = [m['duration_ms'] for m in metrics]
    db_queries = [m['db_queries'] for m in metrics]

    return {
        'count': len(metrics),
        'response_time': {
            'min': min(durations),
            'max': max(durations),
            'avg': sum(durations) / len(durations),
            'p95': sorted(durations)[int(len(durations) * 0.95)] if len(durations) > 20 else max(durations),
            'p99': sorted(durations)[int(len(durations) * 0.99)] if len(durations) > 100 else max(durations)
        },
        'db_queries': {
            'min': min(db_queries) if db_queries else 0,
            'max': max(db_queries) if db_queries else 0,
            'avg': sum(db_queries) / len(db_queries) if db_queries else 0
        },
        'errors': len([m for m in metrics if m['status_code'] >= 400])
    }

def register_performance_routes(app):
    """Register performance monitoring endpoints"""

    @app.route('/api/monitoring/metrics')
    def get_metrics():
        """Get system and request metrics"""
        try:
            system = _monitor.get_system_metrics()

            # Get stats for common endpoints
            endpoints_stats = {}
            for endpoint in ['auth.login', 'platform.get_products', 'coocook.get_chefs']:
                stats = get_performance_stats(endpoint=endpoint, minutes=60)
                if stats:
                    endpoints_stats[endpoint] = stats

            return jsonify({
                'system': system,
                'endpoints': endpoints_stats,
                'collected_samples': len(_monitor.metrics)
            }), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/monitoring/metrics/<endpoint>')
    def get_endpoint_metrics(endpoint):
        """Get metrics for specific endpoint"""
        stats = get_performance_stats(endpoint=f'auth.{endpoint}' if '.' not in endpoint else endpoint, minutes=int(request.args.get('minutes', 60)))

        if not stats:
            return jsonify({'error': 'No metrics found for endpoint'}), 404

        return jsonify(stats), 200

    @app.route('/api/monitoring/system')
    def get_system_status():
        """Get system resource status"""
        return jsonify(_monitor.get_system_metrics()), 200
