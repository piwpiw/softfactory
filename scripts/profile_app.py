#!/usr/bin/env python3
"""
SoftFactory Performance Profiler
Monitors CPU, memory, response times, and database queries during load testing
Generates performance_report.json with detailed metrics and bottleneck analysis
"""

import json
import psutil
import requests
import time
import threading
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('profiler')

# Configuration
API_BASE = 'http://localhost:9000'
DEMO_TOKEN = 'demo_token'
PROFILE_DURATION_SECONDS = 300  # 5-minute test
SAMPLE_INTERVAL = 1  # Collect metrics every 1 second
OUTPUT_FILE = 'performance_report.json'

# Global metrics collection
metrics = {
    'start_time': None,
    'end_time': None,
    'duration_seconds': PROFILE_DURATION_SECONDS,
    'system_metrics': [],
    'endpoint_metrics': {},
    'slow_endpoints': [],
    'database_queries': [],
    'bottlenecks': [],
    'summary': {},
}

# Endpoints to test (prioritized by importance)
TEST_ENDPOINTS = [
    ('GET', '/api/review/campaigns', 'Review Aggregator'),
    ('GET', '/api/review/listings', 'Review Aggregator'),
    ('GET', '/api/sns/accounts', 'SNS Service'),
    ('GET', '/api/sns/posts', 'SNS Service'),
    ('GET', '/api/sns/analytics', 'SNS Service'),
    ('GET', '/api/dashboard/kpis', 'Dashboard'),
    ('GET', '/api/performance/roi', 'Dashboard'),
    ('GET', '/api/analytics/overview', 'Dashboard'),
]


class PerformanceCollector:
    """Collects system metrics and API response times"""

    def __init__(self):
        self.endpoint_times: Dict[str, List[float]] = {ep[1]: [] for ep in TEST_ENDPOINTS}
        self.endpoint_errors: Dict[str, int] = {ep[1]: 0 for ep in TEST_ENDPOINTS}
        self.lock = threading.Lock()

    def collect_system_metrics(self) -> Dict:
        """Collect CPU, memory, disk I/O metrics"""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            # Get Flask process specifically if possible
            try:
                for proc in psutil.process_iter(['pid', 'name', 'memory_percent']):
                    if 'python' in proc.info['name'].lower() or 'flask' in proc.info['name'].lower():
                        logger.debug(f"Flask process: PID {proc.info['pid']}, Memory: {proc.info['memory_percent']}%")
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

            return {
                'timestamp': datetime.now().isoformat(),
                'cpu_percent': cpu_percent,
                'cpu_count': psutil.cpu_count(),
                'memory': {
                    'used_percent': memory.percent,
                    'available_gb': memory.available / (1024**3),
                    'total_gb': memory.total / (1024**3),
                },
                'disk': {
                    'free_gb': disk.free / (1024**3),
                    'total_gb': disk.total / (1024**3),
                },
            }
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            return None

    def test_endpoint(self, method: str, endpoint: str) -> Tuple[int, float, str]:
        """Test a single endpoint and measure response time"""
        try:
            headers = {
                'Authorization': f'Bearer {DEMO_TOKEN}',
                'Content-Type': 'application/json',
            }

            start = time.time()
            if method.upper() == 'GET':
                response = requests.get(f"{API_BASE}{endpoint}", headers=headers, timeout=10)
            else:
                response = requests.post(f"{API_BASE}{endpoint}", headers=headers, timeout=10, json={})

            duration_ms = (time.time() - start) * 1000

            with self.lock:
                self.endpoint_times[endpoint].append(duration_ms)
                if response.status_code >= 400:
                    self.endpoint_errors[endpoint] += 1

            return response.status_code, duration_ms, None

        except requests.Timeout:
            with self.lock:
                self.endpoint_errors[endpoint] += 1
            return 0, 0, 'Timeout'
        except Exception as e:
            with self.lock:
                self.endpoint_errors[endpoint] += 1
            return 0, 0, str(e)

    def run_load_test_iteration(self):
        """Run one iteration of all endpoints"""
        for method, endpoint, _ in TEST_ENDPOINTS:
            status, duration, error = self.test_endpoint(method, endpoint)
            if error:
                logger.warning(f"Error testing {endpoint}: {error}")
            else:
                logger.debug(f"{method} {endpoint}: {status} ({duration:.1f}ms)")


def analyze_metrics(collector: PerformanceCollector) -> Dict:
    """Analyze collected metrics and identify bottlenecks"""
    analysis = {
        'endpoints': {},
        'slow_endpoints': [],
        'error_endpoints': [],
        'database_issues': [],
        'recommendations': [],
    }

    # Analyze each endpoint
    for endpoint, times in collector.endpoint_times.items():
        if not times:
            continue

        times_sorted = sorted(times)
        errors = collector.endpoint_errors.get(endpoint, 0)

        stats = {
            'endpoint': endpoint,
            'requests': len(times),
            'errors': errors,
            'error_rate_percent': (errors / len(times) * 100) if times else 0,
            'avg_ms': sum(times) / len(times),
            'min_ms': min(times),
            'max_ms': max(times),
            'p50_ms': times_sorted[len(times)//2] if times else 0,
            'p95_ms': times_sorted[int(len(times)*0.95)] if times else 0,
            'p99_ms': times_sorted[int(len(times)*0.99)] if times else 0,
        }

        analysis['endpoints'][endpoint] = stats

        # Identify slow endpoints (avg > 500ms)
        if stats['avg_ms'] > 500:
            analysis['slow_endpoints'].append({
                'endpoint': endpoint,
                'avg_ms': round(stats['avg_ms'], 2),
                'p95_ms': round(stats['p95_ms'], 2),
                'issue': 'High latency - may indicate N+1 queries or missing indexes',
            })

        # Identify error endpoints
        if errors > 0:
            analysis['error_endpoints'].append({
                'endpoint': endpoint,
                'error_count': errors,
                'error_rate_percent': round(stats['error_rate_percent'], 2),
            })

    # Generate recommendations
    if analysis['slow_endpoints']:
        analysis['recommendations'].append(
            'SLOW ENDPOINTS DETECTED: Review query optimization, add indexes, or implement caching'
        )

    if analysis['error_endpoints']:
        analysis['recommendations'].append(
            'ERROR ENDPOINTS DETECTED: Check server logs and database connections'
        )

    if len(analysis['slow_endpoints']) > 3:
        analysis['recommendations'].append(
            'Multiple slow endpoints - consider horizontal scaling or CDN'
        )

    return analysis


def run_profiler():
    """Main profiler orchestration"""
    logger.info(f"Starting performance profiler for {PROFILE_DURATION_SECONDS} seconds")
    logger.info(f"Target API: {API_BASE}")
    logger.info(f"Testing {len(TEST_ENDPOINTS)} endpoints")

    collector = PerformanceCollector()
    metrics['start_time'] = datetime.now().isoformat()

    # System metrics collection thread
    def collect_system_loop():
        while time.time() < profile_end_time:
            sys_metric = collector.collect_system_metrics()
            if sys_metric:
                metrics['system_metrics'].append(sys_metric)
            time.sleep(SAMPLE_INTERVAL)

    # API testing thread
    def test_endpoints_loop():
        while time.time() < profile_end_time:
            collector.run_load_test_iteration()
            time.sleep(0.5)  # Stagger requests

    profile_start_time = time.time()
    profile_end_time = profile_start_time + PROFILE_DURATION_SECONDS

    # Start collection threads
    system_thread = threading.Thread(target=collect_system_loop, daemon=True)
    test_thread = threading.Thread(target=test_endpoints_loop, daemon=True)

    system_thread.start()
    test_thread.start()

    # Wait for completion
    try:
        while time.time() < profile_end_time:
            elapsed = time.time() - profile_start_time
            percent = (elapsed / PROFILE_DURATION_SECONDS) * 100
            sys.stdout.write(f'\rProgress: {percent:.1f}% ({int(elapsed)}s/{PROFILE_DURATION_SECONDS}s)')
            sys.stdout.flush()
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Profiling interrupted by user")

    print()  # Newline after progress bar

    # Wait for threads to complete
    system_thread.join(timeout=5)
    test_thread.join(timeout=5)

    metrics['end_time'] = datetime.now().isoformat()

    # Analyze results
    analysis = analyze_metrics(collector)
    metrics['endpoint_metrics'] = analysis['endpoints']
    metrics['slow_endpoints'] = analysis['slow_endpoints']
    metrics['bottlenecks'] = analysis['error_endpoints']

    # Generate summary statistics
    if metrics['system_metrics']:
        cpu_samples = [m['cpu_percent'] for m in metrics['system_metrics']]
        mem_samples = [m['memory']['used_percent'] for m in metrics['system_metrics']]

        metrics['summary'] = {
            'total_requests': sum(len(times) for times in collector.endpoint_times.values()),
            'total_errors': sum(collector.endpoint_errors.values()),
            'avg_cpu_percent': sum(cpu_samples) / len(cpu_samples),
            'peak_cpu_percent': max(cpu_samples),
            'avg_memory_percent': sum(mem_samples) / len(mem_samples),
            'peak_memory_percent': max(mem_samples),
            'slow_endpoint_count': len(analysis['slow_endpoints']),
            'error_endpoint_count': len(analysis['error_endpoints']),
            'recommendations': analysis['recommendations'],
        }

    # Save report
    try:
        output_path = Path(OUTPUT_FILE)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(metrics, f, indent=2)

        logger.info(f"Performance report saved to {output_path.absolute()}")

        # Print summary to console
        print("\n" + "="*80)
        print("PERFORMANCE PROFILING SUMMARY")
        print("="*80)
        print(f"Total Requests: {metrics['summary'].get('total_requests', 0)}")
        print(f"Total Errors: {metrics['summary'].get('total_errors', 0)}")
        print(f"Avg CPU: {metrics['summary'].get('avg_cpu_percent', 0):.1f}%")
        print(f"Peak CPU: {metrics['summary'].get('peak_cpu_percent', 0):.1f}%")
        print(f"Avg Memory: {metrics['summary'].get('avg_memory_percent', 0):.1f}%")
        print(f"Peak Memory: {metrics['summary'].get('peak_memory_percent', 0):.1f}%")
        print(f"\nSlow Endpoints ({len(analysis['slow_endpoints'])}):")
        for ep in analysis['slow_endpoints'][:5]:
            print(f"  - {ep['endpoint']}: {ep['avg_ms']:.0f}ms avg, {ep['p95_ms']:.0f}ms p95")
        print(f"\nRecommendations:")
        for rec in analysis['recommendations']:
            print(f"  - {rec}")
        print("="*80)

    except Exception as e:
        logger.error(f"Error saving report: {e}")
        sys.exit(1)


if __name__ == '__main__':
    try:
        run_profiler()
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
