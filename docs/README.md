# SoftFactory Platform - Complete API Documentation

**Version:** 2.1.0
**Last Updated:** 2026-02-25
**Status:** Production Ready
**Endpoints:** 47+
**Services:** 10

---

## Welcome to SoftFactory API Documentation

This directory contains comprehensive documentation for the SoftFactory platform's REST API, including machine-readable specifications, interactive testing consoles, and integration guides.

### 📚 Documentation Files

| File | Type | Purpose |
|------|------|---------|
| **README.md** | Index | This file - quick navigation |
| **API_ENDPOINTS.md** | Reference | Complete endpoint documentation with examples |
| **openapi.json** | Spec | OpenAPI 3.0 machine-readable specification |
| **swagger-ui.html** | UI | Interactive Swagger UI for testing endpoints |
| **INTEGRATION_GUIDE.md** | Guide | Code examples and integration patterns |
| **API_DOCUMENTATION_SUMMARY.md** | Summary | Overview and quick reference |

---

## Quick Start (30 minutes)

### 1️⃣ API Overview (5 min)
Read **API_DOCUMENTATION_SUMMARY.md** for overview of all services.

### 2️⃣ Interactive Testing (10 min)
Open **swagger-ui.html** in your browser to test endpoints.

### 3️⃣ Reference Guide (10 min)
Skim **API_ENDPOINTS.md** for authentication and your target service.

### 4️⃣ Code Integration (5 min)
Review relevant section in **INTEGRATION_GUIDE.md** for your language.

---

## Service Overview

### 🔐 Core Services
- **Authentication** (4 endpoints) - Login, register, token management
- **Payment** (5 endpoints) - Stripe integration, subscriptions
- **Platform** (5 endpoints) - Dashboard, admin analytics

### 📱 SaaS Services
- **CooCook** (10 endpoints) - Chef booking platform
- **SNS Auto** (8 endpoints) - Social media automation
- **Review** (8 endpoints) - Influencer campaigns
- **AI Automation** (9 endpoints) - Business process automation
- **WebApp Builder** (8 endpoints) - 8-week bootcamp

### 🌐 Public Services
- **Experience Platform** (6 endpoints) - Aggregated opportunities
- **JARVIS** (5 endpoints) - Multi-agent system monitoring

---

## Authentication

### Demo Token (Fastest)

```bash
curl -X GET http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer demo_token"
```

### Real Authentication

```bash
# 1. Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password"}'

# 2. Use returned access_token
curl -X GET http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer {access_token}"
```

---

## Tools

### Interactive Testing
- **Swagger UI:** Open `swagger-ui.html` in browser
- **Postman:** Import `openapi.json` via File → Import
- **cURL/REST Client:** Use examples from API_ENDPOINTS.md

### Code Generation
```bash
openapi-generator-cli generate -i openapi.json -g python -o ./client
```

---

## Common Tasks

### Register & Subscribe
1. `POST /api/auth/register` - Create account
2. `POST /api/auth/login` - Get tokens
3. `GET /api/payment/plans` - Browse products
4. `POST /api/payment/checkout` - Create checkout
5. Complete Stripe payment (redirected)

### Book a Chef (CooCook)
1. `GET /api/coocook/chefs` - Browse chefs
2. `GET /api/coocook/chefs/{chef_id}` - View details
3. `POST /api/coocook/bookings` - Create booking
4. `POST /api/coocook/bookings/{booking_id}/pay` - Pay

### Create SNS Post
1. `POST /api/sns/accounts` - Link account
2. `POST /api/sns/posts` - Create post
3. `POST /api/sns/posts/{post_id}/publish` - Schedule/publish

### Run Campaign
1. `POST /api/review/campaigns` - Create campaign
2. `GET /api/review/campaigns/{campaign_id}/applications` - View apps
3. `PUT /api/review/applications/{app_id}` - Approve/reject

---

## Status Codes

| Code | Meaning | Next Step |
|------|---------|-----------|
| 200/201 | Success | Use response data |
| 400 | Bad Request | Check parameters in API_ENDPOINTS.md |
| 401 | Unauthorized | Login or refresh token |
| 403 | Forbidden | Check subscription |
| 404 | Not Found | Verify resource ID |
| 429 | Rate Limited | Wait and retry |

---

## Demo Credentials

```
Email: demo@softfactory.com
Token: demo_token (recommended for testing)
Access: All services with full subscriptions
```

---

## File Guide

- **API_ENDPOINTS.md** - 45 KB, 2,346 lines - Complete reference with all endpoints
- **openapi.json** - 54 KB, 2,096 lines - Machine-readable spec
- **swagger-ui.html** - 14 KB, 419 lines - Interactive testing UI
- **INTEGRATION_GUIDE.md** - 22 KB, 852 lines - Code examples
- **API_DOCUMENTATION_SUMMARY.md** - 14 KB, 492 lines - Overview

---

## Support

**Email:** support@softfactory.com
**Docs:** https://docs.softfactory.com
**Status:** https://status.softfactory.com

---

**SoftFactory API v2.1.0 | Generated 2026-02-25 | Production Ready**
