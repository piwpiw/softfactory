"""
Performance Profiling Tool for SoftFactory Flask API
Measures endpoint response times, identifies bottlenecks, and provides optimization recommendations
"""

import time
import timeit
import json
import statistics
from datetime import datetime
from typing import Dict, List, Tuple
import requests
from contextlib import contextmanager


class PerformanceProfiler:
    """Profile API endpoint performance"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results = {}
        self.auth_token = None

    @contextmanager
    def timer(self, name: str):
        """Context manager for timing code blocks"""
        start = time.perf_counter()
        try:
            yield
        finally:
            elapsed = time.perf_counter() - start
            print(f"⏱️  {name}: {elapsed*1000:.2f}ms")

    def authenticate(self) -> bool:
        """Get auth token for protected endpoints"""
        try:
            response = requests.post(
                f"{self.base_url}/api/auth/login",
                json={"email": "demo@softfactory.com", "password": "demo123"},
                timeout=5
            )
            if response.status_code == 200:
                self.auth_token = response.json().get('token')
                return True
        except Exception as e:
            print(f"⚠️  Authentication failed: {e}")
        return False

    def profile_endpoint(self, method: str, endpoint: str,
                        samples: int = 10, payload: Dict = None) -> Dict:
        """Profile a single endpoint with multiple requests"""

        url = f"{self.base_url}{endpoint}"
        headers = {"Content-Type": "application/json"}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"

        times = []
        errors = 0

        print(f"\n📊 Profiling {method} {endpoint}")

        for i in range(samples):
            try:
                start = time.perf_counter()

                if method.upper() == "GET":
                    response = requests.get(url, headers=headers, timeout=10)
                elif method.upper() == "POST":
                    response = requests.post(url, json=payload, headers=headers, timeout=10)
                else:
                    continue

                elapsed = (time.perf_counter() - start) * 1000  # Convert to ms

                if response.status_code < 400:
                    times.append(elapsed)
                    print(f"  Sample {i+1}/{samples}: {elapsed:.2f}ms [OK]")
                else:
                    errors += 1
                    print(f"  Sample {i+1}/{samples}: Status {response.status_code} [ERROR]")

            except requests.Timeout:
                errors += 1
                print(f"  Sample {i+1}/{samples}: TIMEOUT [ERROR]")
            except Exception as e:
                errors += 1
                print(f"  Sample {i+1}/{samples}: {str(e)[:50]} [ERROR]")

        # Calculate statistics
        stats = {
            'endpoint': endpoint,
            'method': method,
            'samples': len(times),
            'success_rate': f"{(len(times)/samples)*100:.1f}%",
            'errors': errors,
        }

        if times:
            stats.update({
                'min_ms': f"{min(times):.2f}",
                'max_ms': f"{max(times):.2f}",
                'mean_ms': f"{statistics.mean(times):.2f}",
                'median_ms': f"{statistics.median(times):.2f}",
                'stdev_ms': f"{statistics.stdev(times):.2f}" if len(times) > 1 else "N/A",
                'p95_ms': f"{sorted(times)[int(len(times)*0.95)]:.2f}" if len(times) > 1 else "N/A",
                'p99_ms': f"{sorted(times)[int(len(times)*0.99)] if int(len(times)*0.99) < len(times) else len(times)-1]:.2f}" if len(times) > 1 else "N/A",
            })

        self.results[endpoint] = stats
        return stats

    def profile_database_queries(self) -> Dict:
        """Measure database query performance"""
        print("\n🗄️  Database Query Profiling")

        from backend.app import create_app
        from backend.models import Chef, User, Booking

        app = create_app()

        query_times = {}

        with app.app_context():
            # Test 1: Simple SELECT
            with self.timer("User.query.all()"):
                users = User.query.all()

            # Test 2: Filtered query
            with self.timer("Chef.query.filter_by(is_active=True)"):
                chefs = Chef.query.filter_by(is_active=True).all()

            # Test 3: Paginated query
            with self.timer("Chef.query.paginate(page=1, per_page=12)"):
                result = Chef.query.paginate(page=1, per_page=12)

            # Test 4: Relationship loading (N+1 potential)
            with self.timer("Loading chef relationships"):
                chefs = Chef.query.all()
                for chef in chefs:
                    _ = chef.bookings

            # Test 5: Count query
            with self.timer("Chef.query.count()"):
                count = Chef.query.count()

        return query_times


class LoadTester:
    """Load testing tool for concurrent request simulation"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.auth_token = None

    def authenticate(self) -> bool:
        """Get auth token"""
        try:
            response = requests.post(
                f"{self.base_url}/api/auth/login",
                json={"email": "demo@softfactory.com", "password": "demo123"},
                timeout=5
            )
            if response.status_code == 200:
                self.auth_token = response.json().get('token')
                return True
        except:
            pass
        return False

    def load_test(self, endpoint: str, concurrent_requests: int = 50,
                  method: str = "GET", payload: Dict = None) -> Dict:
        """Simulate concurrent requests using threading"""

        import threading
        import queue

        url = f"{self.base_url}{endpoint}"
        headers = {"Content-Type": "application/json"}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"

        results_queue = queue.Queue()
        errors_queue = queue.Queue()

        def make_request():
            try:
                start = time.perf_counter()

                if method.upper() == "GET":
                    response = requests.get(url, headers=headers, timeout=10)
                else:
                    response = requests.post(url, json=payload, headers=headers, timeout=10)

                elapsed = (time.perf_counter() - start) * 1000

                results_queue.put({
                    'status': response.status_code,
                    'time_ms': elapsed,
                    'success': response.status_code < 400
                })
            except Exception as e:
                errors_queue.put(str(e))

        print(f"\n⚡ Load Testing {method} {endpoint}")
        print(f"   Concurrent requests: {concurrent_requests}")

        # Create and start threads
        threads = []
        start_time = time.perf_counter()

        for i in range(concurrent_requests):
            t = threading.Thread(target=make_request)
            t.start()
            threads.append(t)

        # Wait for all threads
        for t in threads:
            t.join()

        total_time = time.perf_counter() - start_time

        # Collect results
        all_results = []
        while not results_queue.empty():
            all_results.append(results_queue.get())

        error_count = errors_queue.qsize()

        # Calculate statistics
        response_times = [r['time_ms'] for r in all_results]
        successful = sum(1 for r in all_results if r['success'])

        stats = {
            'endpoint': endpoint,
            'method': method,
            'concurrent_requests': concurrent_requests,
            'total_time_sec': f"{total_time:.2f}",
            'successful_requests': successful,
            'failed_requests': error_count,
            'success_rate': f"{(successful/(successful+error_count))*100:.1f}%" if (successful+error_count) > 0 else "0%",
            'throughput_rps': f"{concurrent_requests/total_time:.2f}",
        }

        if response_times:
            stats.update({
                'min_ms': f"{min(response_times):.2f}",
                'max_ms': f"{max(response_times):.2f}",
                'mean_ms': f"{statistics.mean(response_times):.2f}",
                'median_ms': f"{statistics.median(response_times):.2f}",
                'p95_ms': f"{sorted(response_times)[int(len(response_times)*0.95)]:.2f}",
                'p99_ms': f"{sorted(response_times)[int(len(response_times)*0.99)]:.2f}",
            })

        return stats


def run_baseline_profiling():
    """Run baseline performance profiling"""

    print("=" * 80)
    print("🚀 SOFTFACTORY API BASELINE PERFORMANCE PROFILING")
    print("=" * 80)

    profiler = PerformanceProfiler()

    # Try to authenticate
    print("\n🔐 Authenticating...")
    profiler.authenticate()

    # Profile endpoints
    endpoints = [
        ("GET", "/health", None),
        ("GET", "/api/coocook/chefs", None),
        ("GET", "/api/coocook/chefs?cuisine=Korean", None),
        ("GET", "/api/products", None),
    ]

    baseline_results = {}
    for method, endpoint, payload in endpoints:
        try:
            stats = profiler.profile_endpoint(method, endpoint, samples=10, payload=payload)
            baseline_results[endpoint] = stats
        except Exception as e:
            print(f"❌ Error profiling {endpoint}: {e}")

    print("\n" + "=" * 80)
    print("📊 BASELINE RESULTS SUMMARY")
    print("=" * 80)

    for endpoint, stats in baseline_results.items():
        print(f"\n{endpoint}")
        for key, value in stats.items():
            if key != 'endpoint':
                print(f"  {key}: {value}")

    return baseline_results


def run_load_tests():
    """Run load tests with increasing concurrency"""

    print("\n" + "=" * 80)
    print("⚡ LOAD TESTING")
    print("=" * 80)

    tester = LoadTester()
    tester.authenticate()

    load_test_configs = [
        ("/api/coocook/chefs", 50),
        ("/api/coocook/chefs", 100),
        ("/api/coocook/chefs", 500),
        ("/health", 100),
    ]

    load_results = []
    for endpoint, concurrent in load_test_configs:
        try:
            stats = tester.load_test(endpoint, concurrent_requests=concurrent)
            load_results.append(stats)
            print(f"\n✅ Results:")
            for key, value in stats.items():
                if key not in ['endpoint', 'method']:
                    print(f"   {key}: {value}")
        except Exception as e:
            print(f"❌ Error testing {endpoint}: {e}")

    return load_results


if __name__ == "__main__":
    baseline = run_baseline_profiling()
    load_tests = run_load_tests()

    # Save results
    output = {
        'timestamp': datetime.now().isoformat(),
        'baseline_profiling': baseline,
        'load_tests': load_tests
    }

    with open('D:/Project/performance_baseline.json', 'w') as f:
        json.dump(output, f, indent=2)

    print("\n✅ Results saved to performance_baseline.json")
