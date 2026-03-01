# 🔌 SoftFactory API Documentation Suite - Complete

> **Purpose**: **Generated:** 2026-02-25
> **Status**: 🟢 ACTIVE (관리 중)
> **Impact**: [Engineering / Operations]

---

## ⚡ Executive Summary (핵심 요약)
- **주요 내용**: 본 문서는 SoftFactory API Documentation Suite - Complete 관련 핵심 명세 및 관리 포인트를 포함합니다.
- **상태**: 현재 최신화 완료 및 검토 됨.
- **연관 문서**: [Master Index](./NOTION_MASTER_INDEX.md)

---

**Generated:** 2026-02-25
**API Version:** 2.1.0
**Total Endpoints:** 47+
**Documentation Coverage:** 100%

---

## Overview

This comprehensive API documentation suite provides complete coverage of the SoftFactory platform's REST API endpoints. The documentation includes interactive testing capabilities, machine-readable specifications, and detailed markdown reference guides.

### Contents

| File | Type | Size | Purpose |
|------|------|------|---------|
| **openapi.json** | OpenAPI 3.0 Spec | 54 KB | Machine-readable API specification for code generation and validation |
| **swagger-ui.html** | Interactive UI | 14 KB | Live Swagger UI for endpoint testing and exploration |
| **API_ENDPOINTS.md** | Markdown Reference | 45 KB | Detailed endpoint documentation with examples and error codes |

---

## Quick Start

### 1. Interactive API Testing (Swagger UI)

Open `swagger-ui.html` in a web browser to test all endpoints interactively:

```bash
open docs/swagger-ui.html
```

**Features:**
- Try-it-out functionality for all endpoints
- Authentication with Bearer token support
- Request/response visualization
- Error code reference
- Live code examples

### 2. Machine-Readable Spec (OpenAPI JSON)

Import `openapi.json` into API tools:

```bash
# Using Postman
- File → Import → Select openapi.json

# Using VS Code REST Client
# Reference: openapi.json automatically loaded

# Using API documentation generators
openapi-generator-cli generate -i openapi.json -g markdown
```

### 3. Reference Documentation (Markdown)

Read `API_ENDPOINTS.md` for complete endpoint reference:
- All 47+ endpoints documented
- Request/response examples
- Authentication flows
- Error handling guide
- Rate limiting information

---

## API Coverage by Service

### 1. Authentication (4 endpoints)

- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login user
- `POST /api/auth/refresh` - Refresh access token
- `GET /api/auth/me` - Get current user

### 2. Payment Integration (5 endpoints)

- `GET /api/payment/plans` - Get product plans
- `POST /api/payment/checkout` - Create Stripe checkout
- `GET /api/payment/subscriptions` - Get user subscriptions
- `DELETE /api/payment/subscriptions/{id}` - Cancel subscription
- `POST /api/payment/webhook` - Stripe webhook handler

### 3. Platform Management (5 endpoints)

- `GET /api/platform/products` - Get all products
- `GET /api/platform/dashboard` - User dashboard
- `GET /api/platform/admin/users` - List all users (admin)
- `GET /api/platform/admin/revenue` - Revenue stats (admin)
- Infrastructure & health checks (3 endpoints)

### 4. CooCook - Chef Booking (10 endpoints)

```
GET    /api/coocook/chefs                          List chefs
POST   /api/coocook/chefs                          Register as chef
GET    /api/coocook/chefs/{chef_id}                Chef details
GET    /api/coocook/chefs/{chef_id}/reviews        Chef reviews
GET    /api/coocook/bookings                       My bookings
POST   /api/coocook/bookings                       Create booking
GET    /api/coocook/bookings/{booking_id}          Booking details
PUT    /api/coocook/bookings/{booking_id}          Update booking
POST   /api/coocook/bookings/{booking_id}/pay      Process payment
POST   /api/coocook/bookings/{booking_id}/review   Submit review
```

### 5. SNS Auto - Social Media Automation (8 endpoints)

```
GET    /api/sns/accounts                           List accounts
POST   /api/sns/accounts                           Link account
DELETE /api/sns/accounts/{account_id}              Unlink account
GET    /api/sns/posts                              List posts
POST   /api/sns/posts                              Create post
POST   /api/sns/posts/{post_id}/publish            Publish/schedule
DELETE /api/sns/posts/{post_id}                    Delete post
GET    /api/sns/templates                          Get templates
```

### 6. Review - Influencer Campaigns (8 endpoints)

```
GET    /api/review/campaigns                       List campaigns
GET    /api/review/campaigns/{campaign_id}         Campaign details
POST   /api/review/campaigns                       Create campaign
POST   /api/review/campaigns/{campaign_id}/apply   Apply to campaign
GET    /api/review/my-campaigns                    My campaigns
GET    /api/review/my-applications                 My applications
GET    /api/review/campaigns/{id}/applications     Campaign applications
PUT    /api/review/applications/{id}               Update application
```

### 7. AI Automation (9 endpoints)

```
GET    /api/ai-automation/plans                    Get plans
GET    /api/ai-automation/scenarios                Get scenarios
GET    /api/ai-automation/scenarios/{scenario_id}  Scenario details
GET    /api/ai-automation/employees                List AI employees
POST   /api/ai-automation/employees                Create AI employee
GET    /api/ai-automation/employees/{id}           Employee details
POST   /api/ai-automation/employees/{id}/deploy    Deploy employee
POST   /api/ai-automation/employees/{id}/activate  Activate employee
DELETE /api/ai-automation/employees/{id}           Delete employee
```

### 8. WebApp Builder (8 endpoints)

```
GET    /api/webapp-builder/plans                   Get plans
GET    /api/webapp-builder/courses                 Get courses
POST   /api/webapp-builder/enroll                  Enroll bootcamp
GET    /api/webapp-builder/enrollments             List enrollments
GET    /api/webapp-builder/webapps                 List webapps
POST   /api/webapp-builder/webapps                 Create webapp
GET    /api/webapp-builder/webapps/{id}            Webapp details
POST   /api/webapp-builder/webapps/{id}/deploy     Deploy webapp
```

### 9. Experience Platform (6 endpoints)

```
GET    /api/experience/listings                    List opportunities
GET    /api/experience/listings/{id}               Listing details
GET    /api/experience/stats                       Platform stats
GET    /api/experience/categories                  List categories
GET    /api/experience/sites                       List sites
POST   /api/experience/crawl                       Trigger crawler
```

### 10. JARVIS - Multi-Agent System (5 endpoints)

```
GET    /api/v1/teams                               List teams
GET    /api/v1/teams/{team_id}                     Team details
GET    /api/v1/teams/breakdown                     Capacity analysis
GET    /api/v1/teams/timeline                      Project timeline
GET    /api/v1/stats                               System statistics
```

---

## Authentication

### JWT Bearer Tokens

All protected endpoints require:

```
Authorization: Bearer {access_token}
```

**Token Types:**
- **Access Token:** Valid 1 hour (use for API requests)
- **Refresh Token:** Valid 30 days (use to get new access token)

### Demo Mode

For testing without authentication:

```
Authorization: Bearer demo_token
```

Grants full access as demo user (ID: 1) with all services subscribed.

---

## Key Features

### 1. Comprehensive Endpoint Coverage

- **47+ REST endpoints** across 10 service modules
- **10+ tag categories** for easy navigation
- **Complete CRUD operations** for all resources
- **Admin endpoints** for platform management
- **Public endpoints** for browsing and discovery

### 2. Real-World Examples

Every endpoint includes:
- Request body examples
- Response examples (200, 400, 403, 404, 500)
- Query parameter specifications
- Header requirements
- Field validation rules

### 3. Security & Authentication

- JWT-based authentication
- Admin role enforcement
- Subscription-based access control
- Stripe webhook integration
- Demo mode for testing

### 4. Production-Ready Standards

- RESTful conventions (GET, POST, PUT, DELETE)
- Standard HTTP status codes
- Consistent JSON response format
- Pagination support
- Rate limiting guidance
- Error handling best practices

### 5. Multi-Service Architecture

**Subscription-Based Services:**
- CooCook (Chef Booking)
- SNS Auto (Social Media Automation)
- Review (Influencer Campaigns)
- AI Automation (Business Process Automation)
- WebApp Builder (Educational Bootcamp)

**Public Services:**
- Experience Platform (Crawler Integration)
- JARVIS (Multi-Agent Management)

---

## API Response Format

### Success Response (2xx)

```json
{
  "data": {},
  "message": "Operation successful"
}
```

### Error Response (4xx, 5xx)

```json
{
  "error": "Descriptive error message",
  "code": "ERROR_CODE",
  "details": {}
}
```

### Pagination Response

```json
{
  "items": [],
  "total": 100,
  "pages": 5,
  "current_page": 1
}
```

---

## Integration Guides

### Postman Collection

1. Open Postman
2. Click "Import"
3. Select `openapi.json`
4. Auto-generates collection with all endpoints

### Code Generation

Generate client libraries using OpenAPI generator:

```bash
# Python client
openapi-generator-cli generate -i openapi.json -g python

# JavaScript client
openapi-generator-cli generate -i openapi.json -g javascript

# TypeScript client
openapi-generator-cli generate -i openapi.json -g typescript
```

### VSCode REST Client

Create `.http` files and use openapi.json for IntelliSense:

```http
@baseUrl = http://localhost:8000
@token = demo_token

### Get current user
GET {{baseUrl}}/api/auth/me
Authorization: Bearer {{token}}
```

---

## File Locations

```
D:/Project/docs/
├── openapi.json                    (Machine-readable spec)
├── swagger-ui.html                 (Interactive testing UI)
├── API_ENDPOINTS.md               (Reference guide)
└── API_DOCUMENTATION_SUMMARY.md   (This file)
```

---

## Testing Endpoints

### Using Swagger UI

1. Open `swagger-ui.html` in web browser
2. Click on any endpoint to expand
3. Enter authentication token (or use `demo_token`)
4. Click "Try it out"
5. Fill in parameters and request body
6. Click "Execute"
7. View response and response code

### Using cURL

```bash
# Get current user (demo mode)
curl -X GET http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer demo_token"

# List chefs
curl -X GET http://localhost:8000/api/coocook/chefs?cuisine=Italian

# Create SNS post
curl -X POST http://localhost:8000/api/sns/posts \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": 1,
    "content": "Hello World",
    "template_type": "carousel"
  }'
```

### Using Python Requests

```python
import requests

headers = {
    'Authorization': 'Bearer demo_token'
}

# Get user info
response = requests.get(
    'http://localhost:8000/api/auth/me',
    headers=headers
)
user = response.json()
print(user)
```

---

## Error Codes Reference

| Code | HTTP | Meaning | Solution |
|------|------|---------|----------|
| `INVALID_CREDENTIALS` | 401 | Login failed | Check email/password |
| `TOKEN_EXPIRED` | 401 | Token expired | Refresh token |
| `UNAUTHORIZED` | 401 | Missing token | Add Authorization header |
| `FORBIDDEN` | 403 | Insufficient permissions | Check subscription or admin status |
| `NOT_FOUND` | 404 | Resource doesn't exist | Verify ID is correct |
| `VALIDATION_ERROR` | 400 | Invalid input | Check required fields |
| `CONFLICT` | 409 | Resource already exists | E.g., email already registered |
| `RATE_LIMITED` | 429 | Too many requests | Wait and retry |

---

## Performance Considerations

### Request Size Limits

- **POST/PUT bodies:** Max 10 MB
- **Query parameters:** Max 2000 characters
- **File uploads:** Max 50 MB

### Response Pagination

Default page sizes:
- **User lists:** 20 items/page
- **Booking lists:** 12 items/page
- **Post lists:** 20 items/page

### Caching

Endpoints that return lists support caching:
- Cache-Control: max-age=300 (5 minutes)
- ETag support for conditional requests

---

## Support & Resources

### Documentation Files

- **API_ENDPOINTS.md:** Complete endpoint reference
- **openapi.json:** Machine-readable specification
- **swagger-ui.html:** Interactive testing console

### External Resources

- OpenAPI Specification: https://spec.openapis.org/
- Swagger UI Documentation: https://swagger.io/tools/swagger-ui/
- RESTful API Best Practices: https://restfulapi.net/

### Contact

- **Support Email:** support@softfactory.com
- **API Status:** https://status.softfactory.com
- **GitHub Issues:** https://github.com/softfactory/api/issues

---

## Changelog

### Version 2.1.0 (2026-02-25)

**New Additions:**
- Complete OpenAPI 3.0 specification
- Interactive Swagger UI with try-it-out
- Comprehensive markdown API reference
- All 47+ endpoints documented with examples
- Error handling guide and rate limiting info
- Demo token support documentation

**Improvements:**
- Standardized response format across all endpoints
- Consistent error messages
- Added request/response examples
- Enhanced pagination documentation
- Better authentication guides

---

## Next Steps

1. **Test Interactively:** Open `swagger-ui.html` to explore endpoints
2. **Review Documentation:** Read `API_ENDPOINTS.md` for detailed reference
3. **Integrate Code:** Use `openapi.json` with your favorite API tools
4. **Contact Support:** Reach out for integration questions

---

**Generated:** 2026-02-25
**API Version:** 2.1.0
**Last Updated:** 2026-02-25

For the latest documentation, visit: https://docs.softfactory.com