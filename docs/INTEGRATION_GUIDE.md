# SoftFactory API Integration Guide

**Last Updated:** 2026-02-25
**API Version:** 2.1.0

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Authentication](#authentication)
3. [Common Workflows](#common-workflows)
4. [Code Examples](#code-examples)
5. [Postman Setup](#postman-setup)
6. [Error Handling](#error-handling)
7. [Troubleshooting](#troubleshooting)

---

## Getting Started

### Prerequisites

- HTTP client library or tool (cURL, Postman, Insomnia, etc.)
- Base URL: `http://localhost:8000` (development) or `https://api.softfactory.com` (production)
- API Documentation: See `API_ENDPOINTS.md` for complete reference

### Environment Setup

```bash
# Set environment variables
export SOFTFACTORY_BASE_URL="http://localhost:8000"
export SOFTFACTORY_TOKEN="demo_token"  # Or your actual token

# Test connectivity
curl -X GET $SOFTFACTORY_BASE_URL/health
```

---

## Authentication

### JWT Authentication Flow

```
┌─────────────────┐
│  User Input     │
│ (email/pass)    │
└────────┬────────┘
         │
         ▼
    POST /api/auth/login
         │
    ┌────┴──────────────────────────────┐
    │                                    │
    ▼                                    ▼
Returns tokens                    Store tokens securely
    │                                    │
    └────┬──────────────────────────────┘
         │
    ┌────┴────────────────────────┐
    │ Add to request header:       │
    │ Authorization: Bearer {token}│
    └─────────────────────────────┘
```

### Implementation Examples

#### Python

```python
import requests
from datetime import datetime, timedelta

class SoftFactoryClient:
    def __init__(self, base_url, email, password):
        self.base_url = base_url
        self.email = email
        self.password = password
        self.access_token = None
        self.refresh_token = None
        self.token_expiry = None

    def login(self):
        """Login and obtain tokens"""
        response = requests.post(
            f"{self.base_url}/api/auth/login",
            json={
                "email": self.email,
                "password": self.password
            }
        )
        if response.status_code == 200:
            data = response.json()
            self.access_token = data['access_token']
            self.refresh_token = data['refresh_token']
            self.token_expiry = datetime.utcnow() + timedelta(hours=1)
            return True
        return False

    def refresh_tokens(self):
        """Refresh access token"""
        response = requests.post(
            f"{self.base_url}/api/auth/refresh",
            json={"refresh_token": self.refresh_token}
        )
        if response.status_code == 200:
            data = response.json()
            self.access_token = data['access_token']
            self.refresh_token = data['refresh_token']
            self.token_expiry = datetime.utcnow() + timedelta(hours=1)
            return True
        return False

    def request(self, method, endpoint, **kwargs):
        """Make authenticated request"""
        # Check if token needs refresh
        if self.token_expiry and datetime.utcnow() > self.token_expiry:
            self.refresh_tokens()

        headers = kwargs.get('headers', {})
        headers['Authorization'] = f'Bearer {self.access_token}'
        kwargs['headers'] = headers

        url = f"{self.base_url}{endpoint}"
        return requests.request(method, url, **kwargs)

    def get(self, endpoint, **kwargs):
        return self.request('GET', endpoint, **kwargs)

    def post(self, endpoint, **kwargs):
        return self.request('POST', endpoint, **kwargs)

# Usage
client = SoftFactoryClient("http://localhost:8000", "user@example.com", "password")
client.login()

# Get current user
response = client.get("/api/auth/me")
print(response.json())

# Get dashboard
response = client.get("/api/platform/dashboard")
print(response.json())
```

#### JavaScript/Node.js

```javascript
class SoftFactoryClient {
    constructor(baseUrl, email, password) {
        this.baseUrl = baseUrl;
        this.email = email;
        this.password = password;
        this.accessToken = null;
        this.refreshToken = null;
        this.tokenExpiry = null;
    }

    async login() {
        const response = await fetch(`${this.baseUrl}/api/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                email: this.email,
                password: this.password
            })
        });

        if (response.ok) {
            const data = await response.json();
            this.accessToken = data.access_token;
            this.refreshToken = data.refresh_token;
            this.tokenExpiry = new Date(Date.now() + 3600000); // 1 hour
            return true;
        }
        return false;
    }

    async refreshTokens() {
        const response = await fetch(`${this.baseUrl}/api/auth/refresh`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ refresh_token: this.refreshToken })
        });

        if (response.ok) {
            const data = await response.json();
            this.accessToken = data.access_token;
            this.refreshToken = data.refresh_token;
            this.tokenExpiry = new Date(Date.now() + 3600000);
            return true;
        }
        return false;
    }

    async request(method, endpoint, body = null) {
        // Check if token needs refresh
        if (this.tokenExpiry && new Date() > this.tokenExpiry) {
            await this.refreshTokens();
        }

        const options = {
            method,
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${this.accessToken}`
            }
        };

        if (body) options.body = JSON.stringify(body);

        const response = await fetch(`${this.baseUrl}${endpoint}`, options);
        return response.json();
    }

    get(endpoint) {
        return this.request('GET', endpoint);
    }

    post(endpoint, body) {
        return this.request('POST', endpoint, body);
    }
}

// Usage
const client = new SoftFactoryClient("http://localhost:8000", "user@example.com", "password");
await client.login();

const user = await client.get("/api/auth/me");
console.log(user);
```

### Demo Mode (No Authentication)

For quick testing without credentials:

```bash
# All demo requests use this token
export DEMO_TOKEN="demo_token"

# Example request
curl -X GET http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer demo_token"
```

---

## Common Workflows

### Workflow 1: User Registration & Subscription

```
1. Register user
2. Login and get tokens
3. Browse products
4. Create checkout session
5. Redirect to Stripe
6. Handle payment success
7. Access subscribed services
```

**Implementation:**

```python
# 1. Register
register_response = requests.post(
    f"{base_url}/api/auth/register",
    json={
        "email": "newuser@example.com",
        "password": "SecurePassword123",
        "name": "John Doe"
    }
)
access_token = register_response.json()['access_token']

# 2. (Already logged in from registration)

# 3. Browse products
products = requests.get(
    f"{base_url}/api/payment/plans"
).json()

# 4. Create checkout session
checkout = requests.post(
    f"{base_url}/api/payment/checkout",
    headers={'Authorization': f'Bearer {access_token}'},
    json={
        "product_id": 1,
        "plan_type": "monthly"
    }
).json()

# 5. Open checkout_url in browser
print(f"Complete payment at: {checkout['checkout_url']}")

# 6-7. Payment success redirects to /api/payment/success
#      which creates subscription automatically
```

### Workflow 2: Book a Chef (CooCook)

```
1. Browse available chefs
2. Select a chef and view details
3. Create booking
4. Process payment
5. Chef confirms booking
6. Complete booking
7. Submit review
```

**Implementation:**

```python
# 1. Browse chefs
chefs = requests.get(
    f"{base_url}/api/coocook/chefs",
    params={"cuisine": "Italian", "location": "Seoul"}
).json()

# 2. View chef details
chef_id = chefs['chefs'][0]['id']
chef_detail = requests.get(
    f"{base_url}/api/coocook/chefs/{chef_id}"
).json()

# 3. Create booking
booking = requests.post(
    f"{base_url}/api/coocook/bookings",
    headers={'Authorization': f'Bearer {access_token}'},
    json={
        "chef_id": chef_id,
        "booking_date": "2026-03-15T19:00:00",
        "duration_hours": 3,
        "special_requests": "Vegetarian options"
    }
).json()
booking_id = booking['id']

# 4. Process payment
payment = requests.post(
    f"{base_url}/api/coocook/bookings/{booking_id}/pay",
    headers={'Authorization': f'Bearer {access_token}'},
    json={"amount": booking['total_price']}
).json()

# 5. Chef confirms booking (from chef dashboard)

# 6. Complete booking

# 7. Submit review
review = requests.post(
    f"{base_url}/api/coocook/bookings/{booking_id}/review",
    headers={'Authorization': f'Bearer {access_token}'},
    json={
        "rating": 5,
        "comment": "Amazing experience!"
    }
).json()
```

### Workflow 3: Create and Publish SNS Post

```
1. Link SNS account
2. Get account details
3. Create post (draft)
4. Schedule or publish post
5. Monitor post status
```

**Implementation:**

```python
# 1. Link SNS account
account = requests.post(
    f"{base_url}/api/sns/accounts",
    headers={'Authorization': f'Bearer {access_token}'},
    json={
        "platform": "instagram",
        "account_name": "myinstagram"
    }
).json()
account_id = account['id']

# 2. Get account details
accounts = requests.get(
    f"{base_url}/api/sns/accounts",
    headers={'Authorization': f'Bearer {access_token}'}
).json()

# 3. Create post (draft)
post = requests.post(
    f"{base_url}/api/sns/posts",
    headers={'Authorization': f'Bearer {access_token}'},
    json={
        "account_id": account_id,
        "content": "Check out our new product! #excited",
        "template_type": "carousel"
    }
).json()
post_id = post['id']

# 4. Schedule post
scheduled = requests.post(
    f"{base_url}/api/sns/posts/{post_id}/publish",
    headers={'Authorization': f'Bearer {access_token}'},
    json={
        "scheduled_at": "2026-02-26T15:00:00"
    }
).json()

# 5. Monitor status
post_details = requests.get(
    f"{base_url}/api/sns/posts",
    headers={'Authorization': f'Bearer {access_token}'},
    params={"post_id": post_id}
).json()
```

### Workflow 4: Create Review Campaign

```
1. Create campaign
2. Get applications
3. Review applications
4. Approve/reject applications
5. Monitor campaign progress
```

**Implementation:**

```python
# 1. Create campaign
campaign = requests.post(
    f"{base_url}/api/review/campaigns",
    headers={'Authorization': f'Bearer {access_token}'},
    json={
        "title": "Winter Jacket Review",
        "product_name": "TechJacket Pro",
        "category": "Fashion",
        "reward_type": "cash",
        "reward_value": 50000,
        "max_reviewers": 10,
        "deadline": "2026-03-15T23:59:59Z",
        "description": "Review our new winter jacket"
    }
).json()
campaign_id = campaign['id']

# 2. Get applications
applications = requests.get(
    f"{base_url}/api/review/campaigns/{campaign_id}/applications",
    headers={'Authorization': f'Bearer {access_token}'}
).json()

# 3. Review applications
for app in applications['applications']:
    print(f"{app['user_name']}: {app['follower_count']} followers")

# 4. Approve application
approval = requests.put(
    f"{base_url}/api/review/applications/{app['id']}",
    headers={'Authorization': f'Bearer {access_token}'},
    json={"status": "approved"}
).json()

# 5. Monitor progress
campaign_detail = requests.get(
    f"{base_url}/api/review/campaigns/{campaign_id}"
).json()
print(f"Applications: {campaign_detail['applications_count']}/{campaign_detail['max_reviewers']}")
```

---

## Code Examples

### Complete Client Library Template

```python
"""
SoftFactory API Client
Complete implementation with error handling, retry logic, and token management
"""

import requests
import json
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

class SoftFactoryAPI:
    def __init__(self, base_url: str, email: str = None, password: str = None, token: str = None):
        self.base_url = base_url.rstrip('/')
        self.email = email
        self.password = password
        self.access_token = token or "demo_token"
        self.refresh_token = None
        self.token_expiry = None
        self.session = requests.Session()
        self.max_retries = 3
        self.retry_delay = 1

    def login(self) -> bool:
        """Authenticate with email and password"""
        if not self.email or not self.password:
            return False

        response = self.session.post(
            f"{self.base_url}/api/auth/login",
            json={"email": self.email, "password": self.password}
        )

        if response.status_code == 200:
            data = response.json()
            self.access_token = data['access_token']
            self.refresh_token = data['refresh_token']
            self.token_expiry = datetime.utcnow() + timedelta(hours=1)
            return True
        return False

    def _ensure_valid_token(self):
        """Refresh token if expired"""
        if not self.token_expiry:
            return

        if datetime.utcnow() > self.token_expiry - timedelta(minutes=5):
            self._refresh_token()

    def _refresh_token(self) -> bool:
        """Get new access token using refresh token"""
        if not self.refresh_token:
            return False

        response = self.session.post(
            f"{self.base_url}/api/auth/refresh",
            json={"refresh_token": self.refresh_token}
        )

        if response.status_code == 200:
            data = response.json()
            self.access_token = data['access_token']
            self.refresh_token = data['refresh_token']
            self.token_expiry = datetime.utcnow() + timedelta(hours=1)
            return True
        return False

    def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request with retry logic"""
        self._ensure_valid_token()

        headers = kwargs.get('headers', {})
        headers['Authorization'] = f'Bearer {self.access_token}'
        headers['Content-Type'] = 'application/json'
        kwargs['headers'] = headers

        url = f"{self.base_url}{endpoint}"

        for attempt in range(self.max_retries):
            try:
                response = self.session.request(method, url, **kwargs)

                if response.status_code == 429:  # Rate limited
                    time.sleep(self.retry_delay ** attempt)
                    continue

                return response
            except requests.RequestException as e:
                if attempt == self.max_retries - 1:
                    raise
                time.sleep(self.retry_delay ** attempt)

        raise Exception(f"Failed to {method} {endpoint}")

    def get(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """GET request"""
        response = self._request('GET', endpoint, **kwargs)
        return response.json() if response.status_code < 400 else {"error": response.text}

    def post(self, endpoint: str, data: Dict[str, Any] = None, **kwargs) -> Dict[str, Any]:
        """POST request"""
        if data:
            kwargs['json'] = data
        response = self._request('POST', endpoint, **kwargs)
        return response.json() if response.status_code < 400 else {"error": response.text}

    def put(self, endpoint: str, data: Dict[str, Any] = None, **kwargs) -> Dict[str, Any]:
        """PUT request"""
        if data:
            kwargs['json'] = data
        response = self._request('PUT', endpoint, **kwargs)
        return response.json() if response.status_code < 400 else {"error": response.text}

    def delete(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """DELETE request"""
        response = self._request('DELETE', endpoint, **kwargs)
        return response.json() if response.status_code < 400 else {"error": response.text}

# Usage
api = SoftFactoryAPI("http://localhost:8000", token="demo_token")
user = api.get("/api/auth/me")
print(user)
```

---

## Postman Setup

### Step 1: Import OpenAPI Spec

1. Open Postman
2. Click **Import** button (top left)
3. Select **openapi.json** from docs folder
4. Click **Import**

Postman will automatically create a collection with all endpoints.

### Step 2: Set Environment Variables

1. Click **Environments** (left sidebar)
2. Create new environment: `SoftFactory`
3. Add variables:

```json
{
  "base_url": "http://localhost:8000",
  "token": "demo_token",
  "user_id": "1"
}
```

4. Select environment in top right dropdown

### Step 3: Update Requests

Add auth header to requests:

```
Authorization: Bearer {{token}}
```

### Step 4: Test Endpoints

1. Expand any endpoint in collection
2. Click **Send**
3. View response in bottom panel

---

## Error Handling

### Response Status Codes

| Code | Handling | Example |
|------|----------|---------|
| 200 | Success | Request completed successfully |
| 201 | Created | Resource created successfully |
| 400 | Bad Request | Check input parameters |
| 401 | Unauthorized | Login again or refresh token |
| 403 | Forbidden | Check subscription/permissions |
| 404 | Not Found | Verify resource ID |
| 500 | Server Error | Retry request after delay |

### Error Response Format

```json
{
  "error": "Subscription to coocook required"
}
```

### Handling Errors

```python
response = requests.post(
    f"{base_url}/api/coocook/bookings",
    headers={'Authorization': f'Bearer {token}'},
    json=booking_data
)

if response.status_code == 403:
    error = response.json()
    print(f"Error: {error['error']}")
    # Handle specific error
elif response.status_code == 400:
    error = response.json()
    print(f"Validation error: {error['error']}")
    # Handle validation error
elif response.status_code == 200:
    booking = response.json()
    print(f"Booking created: {booking['id']}")
```

---

## Troubleshooting

### "Unauthorized" (401 Error)

**Cause:** Invalid or missing token

**Solution:**
```python
# Check token
print(f"Token: {access_token}")

# Refresh token if expired
if token_expired:
    refresh_token()

# Or login again
login()
```

### "Subscription required" (403 Error)

**Cause:** User doesn't have subscription to service

**Solution:**
```python
# Check subscriptions
subscriptions = requests.get(
    f"{base_url}/api/payment/subscriptions",
    headers={'Authorization': f'Bearer {token}'}
).json()

# Create checkout for product
checkout = requests.post(
    f"{base_url}/api/payment/checkout",
    headers={'Authorization': f'Bearer {token}'},
    json={"product_id": 1}
).json()

# Complete Stripe payment
# Open checkout_url
```

### "Resource not found" (404 Error)

**Cause:** Invalid resource ID

**Solution:**
```python
# List resources to find correct ID
chefs = requests.get(
    f"{base_url}/api/coocook/chefs"
).json()

# Use correct ID from list
correct_chef_id = chefs['chefs'][0]['id']
```

### "Too many requests" (429 Error)

**Cause:** Rate limit exceeded

**Solution:**
```python
import time

# Implement backoff
for attempt in range(3):
    try:
        response = requests.get(endpoint)
        if response.status_code == 429:
            wait_time = 2 ** attempt  # Exponential backoff
            time.sleep(wait_time)
            continue
        break
    except Exception as e:
        print(f"Attempt {attempt+1} failed: {e}")
```

---

## Best Practices

### 1. Token Management

```python
# Always check token expiry
if token_expiry and datetime.utcnow() > token_expiry:
    refresh_token()

# Use refresh token before expiry
if datetime.utcnow() > token_expiry - timedelta(minutes=5):
    refresh_token()
```

### 2. Error Handling

```python
try:
    response = requests.post(endpoint, json=data)
    response.raise_for_status()
    return response.json()
except requests.exceptions.HTTPError as e:
    # Handle HTTP error
    error_data = e.response.json()
    print(f"Error: {error_data['error']}")
except requests.exceptions.ConnectionError:
    # Handle connection error
    print("Cannot connect to API")
```

### 3. Pagination

```python
page = 1
all_results = []

while True:
    response = requests.get(
        endpoint,
        params={'page': page, 'per_page': 20}
    ).json()

    all_results.extend(response['items'])

    if page >= response['pages']:
        break

    page += 1
```

### 4. Rate Limiting

```python
# Implement request queue
import time

requests_made = 0
start_time = time.time()
RATE_LIMIT = 100  # requests per minute

while requests_to_make:
    if requests_made >= RATE_LIMIT:
        elapsed = time.time() - start_time
        if elapsed < 60:
            time.sleep(60 - elapsed)
        requests_made = 0
        start_time = time.time()

    make_request()
    requests_made += 1
```

---

**For more information, see API_ENDPOINTS.md or openapi.json**
