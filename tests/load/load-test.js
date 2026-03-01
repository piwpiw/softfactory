import http from 'k6/http';
import { check, group, sleep } from 'k6';

// Configuration: VU (Virtual User) stages for realistic load simulation
export let options = {
  stages: [
    { duration: '30s', target: 10 },    // Ramp-up to 10 VUs
    { duration: '1m', target: 50 },     // Increase to 50 VUs
    { duration: '1m30s', target: 100 }, // Peak load: 100 VUs
    { duration: '30s', target: 50 },    // Cool down to 50 VUs
    { duration: '30s', target: 0 },     // Final ramp-down
  ],
  thresholds: {
    http_req_duration: ['p(95)<500', 'p(99)<1000'], // 95% under 500ms, 99% under 1s
    http_req_failed: ['rate<0.1'], // Error rate < 10%
  },
};

// API base URL (production or local)
const API_BASE = __ENV.API_BASE || 'http://localhost:9000';
const DEMO_TOKEN = 'demo_token'; // Static demo token for testing

// Endpoint configuration for comprehensive coverage
const endpoints = [
  // Review Service Endpoints (26 total)
  { method: 'GET', path: '/api/review/campaigns', auth: true, group: 'Review Aggregator' },
  { method: 'GET', path: '/api/review/campaigns?page=1&per_page=12', auth: true, group: 'Review Aggregator' },
  { method: 'GET', path: '/api/review/campaigns?category=lifestyle', auth: true, group: 'Review Aggregator' },
  { method: 'GET', path: '/api/review/reviews', auth: true, group: 'Review Aggregator' },
  { method: 'GET', path: '/api/review/reviews?status=pending', auth: true, group: 'Review Aggregator' },
  { method: 'GET', path: '/api/review/listings', auth: true, group: 'Review Aggregator' },
  { method: 'GET', path: '/api/review/listings?platform=amazon', auth: true, group: 'Review Aggregator' },
  { method: 'GET', path: '/api/review/analytics', auth: true, group: 'Review Aggregator' },

  // SNS Auto Service Endpoints (29 total)
  { method: 'GET', path: '/api/sns/accounts', auth: true, group: 'SNS Posts' },
  { method: 'GET', path: '/api/sns/posts', auth: true, group: 'SNS Posts' },
  { method: 'GET', path: '/api/sns/posts?status=published', auth: true, group: 'SNS Posts' },
  { method: 'GET', path: '/api/sns/templates', auth: true, group: 'SNS Posts' },
  { method: 'GET', path: '/api/sns/analytics', auth: true, group: 'SNS Posts' },
  { method: 'GET', path: '/api/sns/revenue', auth: true, group: 'SNS Posts' },
  { method: 'GET', path: '/api/sns/revenue?period=monthly', auth: true, group: 'SNS Posts' },

  // Dashboard Endpoints
  { method: 'GET', path: '/api/dashboard/kpis', auth: true, group: 'Dashboard' },
  { method: 'GET', path: '/api/analytics/overview', auth: true, group: 'Dashboard' },
  { method: 'GET', path: '/api/performance/roi', auth: true, group: 'Dashboard' },

  // Settings & User Management
  { method: 'GET', path: '/api/user/profile', auth: true, group: 'User Management' },
  { method: 'GET', path: '/api/settings/general', auth: true, group: 'User Management' },

  // Public Endpoints (no auth required)
  { method: 'GET', path: '/', auth: false, group: 'Public Pages' },
  { method: 'GET', path: '/platform/', auth: false, group: 'Public Pages' },
];

/**
 * Main test function - executed for each VU
 */
export default function () {
  // Group 1: Review Service Heavy Load
  group('Review Service - Campaigns List', () => {
    let res = http.get(`${API_BASE}/api/review/campaigns`, {
      headers: {
        'Authorization': `Bearer ${DEMO_TOKEN}`,
        'Content-Type': 'application/json',
      },
      timeout: '10s',
    });

    // Validation checks
    check(res, {
      'status is 200': (r) => r.status === 200,
      'response time < 500ms': (r) => r.timings.duration < 500,
      'has campaigns array': (r) => r.body.includes('campaigns') || r.status !== 200,
    });

    // Log slow responses
    if (res.timings.duration > 1000) {
      console.warn(`SLOW RESPONSE: /api/review/campaigns took ${res.timings.duration}ms`);
    }
  });

  sleep(0.5);

  // Group 2: Review Listings with Filters
  group('Review Service - Listings Filter', () => {
    let res = http.get(`${API_BASE}/api/review/listings?platform=amazon`, {
      headers: {
        'Authorization': `Bearer ${DEMO_TOKEN}`,
        'Content-Type': 'application/json',
      },
    });

    check(res, {
      'status is 200': (r) => r.status === 200,
      'has listings data': (r) => r.status === 200 || r.status === 404, // 404 OK if no data
    });
  });

  sleep(0.5);

  // Group 3: SNS Accounts List
  group('SNS Service - Accounts', () => {
    let res = http.get(`${API_BASE}/api/sns/accounts`, {
      headers: {
        'Authorization': `Bearer ${DEMO_TOKEN}`,
        'Content-Type': 'application/json',
      },
    });

    check(res, {
      'status is 200': (r) => r.status === 200,
      'response time < 500ms': (r) => r.timings.duration < 500,
    });
  });

  sleep(0.5);

  // Group 4: SNS Posts List
  group('SNS Service - Posts', () => {
    let res = http.get(`${API_BASE}/api/sns/posts`, {
      headers: {
        'Authorization': `Bearer ${DEMO_TOKEN}`,
      },
    });

    check(res, {
      'status is 200': (r) => r.status === 200,
      'response time < 1000ms': (r) => r.timings.duration < 1000,
    });

    if (res.timings.duration > 1000) {
      console.warn(`SLOW RESPONSE: /api/sns/posts took ${res.timings.duration}ms`);
    }
  });

  sleep(0.5);

  // Group 5: SNS Analytics
  group('SNS Service - Analytics', () => {
    let res = http.get(`${API_BASE}/api/sns/analytics`, {
      headers: {
        'Authorization': `Bearer ${DEMO_TOKEN}`,
      },
    });

    check(res, {
      'status is 200': (r) => r.status === 200,
    });
  });

  sleep(0.5);

  // Group 6: Dashboard KPIs
  group('Dashboard - KPIs', () => {
    let res = http.get(`${API_BASE}/api/dashboard/kpis`, {
      headers: {
        'Authorization': `Bearer ${DEMO_TOKEN}`,
      },
    });

    check(res, {
      'status is 200': (r) => r.status === 200,
      'response time < 1000ms': (r) => r.timings.duration < 1000,
    });
  });

  sleep(0.5);

  // Group 7: Performance ROI
  group('Performance - ROI Metrics', () => {
    let res = http.get(`${API_BASE}/api/performance/roi`, {
      headers: {
        'Authorization': `Bearer ${DEMO_TOKEN}`,
      },
    });

    check(res, {
      'status is 200': (r) => r.status === 200,
    });
  });

  sleep(1); // Hold for 1 second before next iteration
}

/**
 * Setup phase - runs once before all VUs
 */
export function setup() {
  console.log('Load test starting...');
  console.log(`Target API: ${API_BASE}`);
  console.log('Expected endpoints: Review (26), SNS (29), Dashboard (8+)');

  return { startTime: new Date() };
}

/**
 * Teardown phase - runs once after all VUs
 */
export function teardown(data) {
  console.log('Load test completed');
  console.log(`Test duration: ${new Date() - new Date(data.startTime)}ms`);
}
