"""Locust Load Testing Script for SoftFactory Platform"""
import os
import sys
from locust import HttpUser, task, between, TaskSet, constant_pacing
from datetime import datetime
import json

# Configuration
API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:8000')
DEMO_TOKEN = 'demo_token'
CONCURRENT_USERS = int(os.getenv('CONCURRENT_USERS', 100))
SPAWN_RATE = int(os.getenv('SPAWN_RATE', 10))
DURATION = os.getenv('DURATION', '10m')  # 10 minutes by default

class PlatformBehavior(TaskSet):
    """User behavior tasks"""

    @task(5)
    def get_products(self):
        """Get products list"""
        self.client.get(
            '/api/platform/products',
            headers={'Authorization': f'Bearer {DEMO_TOKEN}'},
            name='GET /api/platform/products'
        )

    @task(3)
    def get_chefs(self):
        """Get CooCook chefs list"""
        self.client.get(
            '/api/coocook/chefs',
            name='GET /api/coocook/chefs'
        )

    @task(2)
    def get_chef_detail(self):
        """Get single chef detail"""
        self.client.get(
            '/api/coocook/chefs/1',
            name='GET /api/coocook/chefs/{id}'
        )

    @task(3)
    def get_user_dashboard(self):
        """Get user dashboard"""
        self.client.get(
            '/api/platform/dashboard',
            headers={'Authorization': f'Bearer {DEMO_TOKEN}'},
            name='GET /api/platform/dashboard'
        )

    @task(2)
    def create_booking(self):
        """Create a booking"""
        self.client.post(
            '/api/coocook/bookings',
            json={
                'chef_id': 1,
                'booking_date': '2026-03-15',
                'duration_hours': 2
            },
            headers={'Authorization': f'Bearer {DEMO_TOKEN}'},
            name='POST /api/coocook/bookings'
        )

    @task(2)
    def get_sns_accounts(self):
        """Get SNS accounts"""
        self.client.get(
            '/api/sns-auto/accounts',
            headers={'Authorization': f'Bearer {DEMO_TOKEN}'},
            name='GET /api/sns-auto/accounts'
        )

    @task(1)
    def get_ai_employees(self):
        """Get AI employees"""
        self.client.get(
            '/api/ai-automation/employees',
            headers={'Authorization': f'Bearer {DEMO_TOKEN}'},
            name='GET /api/ai-automation/employees'
        )

    @task(2)
    def get_reviews(self):
        """Get reviews"""
        self.client.get(
            '/api/review/reviews',
            headers={'Authorization': f'Bearer {DEMO_TOKEN}'},
            name='GET /api/review/reviews'
        )

    @task(1)
    def health_check(self):
        """Health check endpoint"""
        self.client.get(
            '/health',
            name='GET /health'
        )


class SoftFactoryUser(HttpUser):
    """Base user class"""
    tasks = [PlatformBehavior]
    wait_time = between(1, 3)

    def on_start(self):
        """Called when user starts"""
        pass


class AuthenticatedUser(HttpUser):
    """User with authentication"""
    tasks = [PlatformBehavior]
    wait_time = constant_pacing(1)

    def on_start(self):
        """Login before starting tasks"""
        response = self.client.post(
            '/api/auth/login',
            json={
                'email': 'demo@softfactory.com',
                'password': 'demo123'
            },
            name='POST /api/auth/login'
        )

        if response.status_code == 200:
            data = response.json()
            self.auth_token = data.get('access_token')
        else:
            self.auth_token = DEMO_TOKEN


def run_load_test():
    """Run load test from command line"""
    import subprocess

    cmd = [
        'locust',
        f'--host={API_BASE_URL}',
        f'--users={CONCURRENT_USERS}',
        f'--spawn-rate={SPAWN_RATE}',
        f'--run-time={DURATION}',
        '--headless',
        f'--csv={os.path.dirname(__file__)}/../docs/load_test_results',
        '--loglevel=INFO'
    ]

    print(f"Starting load test...")
    print(f"Target: {API_BASE_URL}")
    print(f"Concurrent users: {CONCURRENT_USERS}")
    print(f"Spawn rate: {SPAWN_RATE} users/sec")
    print(f"Duration: {DURATION}")
    print(f"\nCommand: {' '.join(cmd)}")

    result = subprocess.run(cmd, cwd=os.path.dirname(__file__))
    return result.returncode


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--run':
        sys.exit(run_load_test())
    else:
        print("Load testing module for SoftFactory")
        print("\nUsage:")
        print("  locust -f load_test.py --host=http://localhost:8000")
        print("  python load_test.py --run")
        print("\nEnvironment variables:")
        print(f"  API_BASE_URL (default: {API_BASE_URL})")
        print(f"  CONCURRENT_USERS (default: {CONCURRENT_USERS})")
        print(f"  SPAWN_RATE (default: {SPAWN_RATE})")
        print(f"  DURATION (default: {DURATION})")
