# SoftFactory Platform API Reference

**Version:** 2.1.0
**Last Updated:** 2026-02-25
**Base URL:** `http://localhost:8000` (dev) | `https://api.softfactory.com` (prod)

---

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Infrastructure & Health](#infrastructure--health)
4. [Authentication Endpoints](#authentication-endpoints)
5. [Payment Integration](#payment-integration)
6. [Platform Management](#platform-management)
7. [CooCook - Chef Booking](#coocook---chef-booking-service)
8. [SNS Auto - Social Media Automation](#sns-auto---social-media-automation)
9. [Review - Influencer Campaigns](#review---influencer-campaigns)
10. [AI Automation](#ai-automation)
11. [WebApp Builder](#webapp-builder)
12. [Experience Platform](#experience-platform)
13. [JARVIS - Multi-Agent System](#jarvis---multi-agent-system)
14. [Error Handling](#error-handling)
15. [Rate Limiting & Throttling](#rate-limiting--throttling)

---

## Overview

SoftFactory is a comprehensive multi-service platform with **47+ REST API endpoints** organized across 10 service modules. The API uses JWT-based authentication with optional demo mode support and follows REST conventions with standard HTTP status codes.

### Key Features
- **Multi-tenant Architecture:** Each user has isolated data
- **Subscription-based Access:** Products require active subscription (except demo users)
- **Stripe Integration:** Payment processing and webhook handling
- **Real-time Updates:** Server-Sent Events for team progress tracking
- **Admin Dashboard:** Revenue analytics and user management

### Supported Services
| Service | Module | Endpoints | Status |
|---------|--------|-----------|--------|
| CooCook | Chef Booking Platform | 10 | ✅ Production |
| SNS Auto | Social Media Automation | 8 | ✅ Production |
| Review | Influencer Campaigns | 8 | ✅ Production |
| AI Automation | Business Process Automation | 9 | ✅ Production |
| WebApp Builder | Educational Bootcamp | 8 | ✅ Production |
| Experience Platform | Crawler Integration | 6 | ✅ Production |
| JARVIS | Multi-Agent Management | 5 | ✅ Production |
| Payment | Stripe Integration | 5 | ✅ Production |
| Platform | Admin & Dashboard | 5 | ✅ Production |
| Authentication | User Auth & Tokens | 4 | ✅ Production |

---

## Authentication

### JWT Tokens

All protected endpoints require a Bearer token in the Authorization header:

```
Authorization: Bearer {access_token}
```

#### Token Types
- **Access Token:** Valid for 1 hour, used for API requests
- **Refresh Token:** Valid for 30 days, used to obtain new access tokens

#### Demo Mode
For testing without authentication setup, use the special token:
```
Authorization: Bearer demo_token
```

Demo users:
- ID: `1`
- Email: `demo@softfactory.com`
- Role: `user`
- Access: All services (full subscription automatically granted)

### Token Expiration

```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "expires_in": 3600
}
```

**Note:** Always implement token refresh logic on your client side to prevent authentication failures.

---

## Infrastructure & Health

### 🟢 Health Check (Public)

```http
GET /health
```

Basic health check endpoint.

**Response (200 OK):**
```json
{
  "status": "ok"
}
```

### 🟢 Infrastructure Health (Public)

```http
GET /api/infrastructure/health
```

Comprehensive system health check including database status and uptime.

**Response (200 OK):**
```json
{
  "overall_status": "healthy",
  "api_status": "ok",
  "database_status": "ok",
  "uptime": "24h 15m",
  "timestamp": 1708864525.123
}
```

**Status Values:** `healthy`, `degraded`, `unhealthy`

### 🟢 Active Processes (Public)

```http
GET /api/infrastructure/processes
```

Get information about active system processes.

**Response (200 OK):**
```json
{
  "processes": [
    {
      "name": "Flask API",
      "pid": 12345,
      "status": "running"
    }
  ],
  "total_count": 1
}
```

---

## Authentication Endpoints

### Register New User

```http
POST /api/auth/register
```

Create a new user account.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123",
  "name": "John Doe"
}
```

**Required Fields:** `email`, `password` (min 8 chars), `name`

**Response (201 Created):**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "name": "John Doe",
    "role": "user",
    "is_active": true
  }
}
```

**Error Responses:**
- `400 Bad Request:` Missing fields or email already registered

### Login

```http
POST /api/auth/login
```

Authenticate user and obtain tokens.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "name": "John Doe",
    "role": "user"
  }
}
```

**Error Responses:**
- `401 Unauthorized:` Invalid credentials
- `403 Forbidden:` Account is inactive

### Refresh Access Token

```http
POST /api/auth/refresh
```

Obtain a new access token using a refresh token.

**Request Body:**
```json
{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Error Responses:**
- `400 Bad Request:` Missing refresh token
- `401 Unauthorized:` Invalid or expired token

### Get Current User

```http
GET /api/auth/me
```

Get authenticated user information.

**Headers:** `Authorization: Bearer {access_token}`

**Response (200 OK):**
```json
{
  "id": 1,
  "email": "user@example.com",
  "name": "John Doe",
  "role": "user",
  "is_active": true
}
```

**Error Responses:**
- `401 Unauthorized:` Invalid or missing token

---

## Payment Integration

### Get All Product Plans

```http
GET /api/payment/plans
```

Get all available product plans (public endpoint).

**Query Parameters:** None

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "name": "CooCook",
    "slug": "coocook",
    "description": "Chef booking platform",
    "monthly_price": 29900,
    "annual_price": 299000,
    "is_active": true
  },
  {
    "id": 2,
    "name": "SNS Auto",
    "slug": "sns-auto",
    "description": "Social media automation",
    "monthly_price": 49900,
    "annual_price": 499000,
    "is_active": true
  }
  // ... more products
]
```

### Create Checkout Session

```http
POST /api/payment/checkout
```

Create a Stripe checkout session for subscription purchase.

**Headers:** `Authorization: Bearer {access_token}`

**Request Body:**
```json
{
  "product_id": 1,
  "plan_type": "monthly"
}
```

**Parameters:**
- `product_id` (integer, required): Product ID
- `plan_type` (string, optional): `"monthly"` or `"annual"`, default: `"monthly"`

**Response (200 OK):**
```json
{
  "checkout_url": "https://checkout.stripe.com/pay/cs_..."
}
```

**Error Responses:**
- `400 Bad Request:` Already subscribed or invalid product
- `404 Not Found:` Product not found

### Handle Checkout Success

```http
GET /api/payment/success?session_id={CHECKOUT_SESSION_ID}
```

Stripe redirects here after successful payment. Automatically creates subscription and payment records.

**Response (200 OK):**
```json
{
  "message": "Payment successful"
}
```

### Get User Subscriptions

```http
GET /api/payment/subscriptions
```

Get all active and past subscriptions for the authenticated user.

**Headers:** `Authorization: Bearer {access_token}`

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "user_id": 1,
    "product_id": 1,
    "product_name": "CooCook",
    "plan_type": "monthly",
    "status": "active",
    "current_period_end": "2026-03-25T10:30:00Z",
    "stripe_subscription_id": "sub_..."
  }
]
```

### Cancel Subscription

```http
DELETE /api/payment/subscriptions/{subscription_id}
```

Cancel an active subscription.

**Headers:** `Authorization: Bearer {access_token}`

**Response (200 OK):**
```json
{
  "message": "Subscription canceled"
}
```

**Error Responses:**
- `404 Not Found:` Subscription not found
- `403 Forbidden:` Not authorized to cancel

---

## Platform Management

### Get All Active Products

```http
GET /api/platform/products
```

Get list of all active products (public endpoint).

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "name": "CooCook",
    "slug": "coocook",
    "description": "Chef booking platform",
    "monthly_price": 29900,
    "annual_price": 299000,
    "is_active": true
  }
  // ... more products
]
```

### Get User Dashboard

```http
GET /api/platform/dashboard
```

Get personalized dashboard with user's subscriptions and available products.

**Headers:** `Authorization: Bearer {access_token}`

**Response (200 OK):**
```json
{
  "user": {
    "id": 1,
    "email": "user@example.com",
    "name": "John Doe",
    "role": "user"
  },
  "products": [
    {
      "id": 1,
      "name": "CooCook",
      "slug": "coocook",
      "subscribed": true,
      "subscription": {
        "id": 1,
        "status": "active",
        "plan_type": "monthly"
      }
    },
    {
      "id": 2,
      "name": "SNS Auto",
      "slug": "sns-auto",
      "subscribed": false
    }
  ],
  "subscription_count": 1
}
```

### Get All Users (Admin Only)

```http
GET /api/platform/admin/users
```

Retrieve paginated list of all users (requires admin role).

**Headers:** `Authorization: Bearer {admin_access_token}`

**Query Parameters:**
- `page` (integer, optional): Page number, default: `1`
- `per_page` (integer, optional): Items per page, default: `20`

**Response (200 OK):**
```json
{
  "users": [
    {
      "id": 1,
      "email": "user@example.com",
      "name": "John Doe",
      "role": "user",
      "is_active": true,
      "active_subscriptions": 2
    }
  ],
  "total": 50,
  "pages": 3,
  "current_page": 1
}
```

**Error Responses:**
- `403 Forbidden:` Admin access required

### Get Revenue Statistics (Admin Only)

```http
GET /api/platform/admin/revenue
```

Get revenue analytics including MRR, ARR, and breakdown by product.

**Headers:** `Authorization: Bearer {admin_access_token}`

**Response (200 OK):**
```json
{
  "mrr": 14950.50,
  "arr": 179406.00,
  "total_revenue": 299800.00,
  "total_users": 50,
  "active_subscriptions": 27,
  "revenue_by_product": [
    {
      "product_name": "CooCook",
      "subscriptions": 5,
      "monthly_revenue": 149750.00
    },
    {
      "product_name": "SNS Auto",
      "subscriptions": 3,
      "monthly_revenue": 149700.00
    }
  ]
}
```

---

## CooCook - Chef Booking Service

### List Chefs

```http
GET /api/coocook/chefs
```

Browse available chefs with optional filters (public endpoint).

**Query Parameters:**
- `cuisine` (string, optional): Filter by cuisine type (e.g., "Italian", "Korean")
- `location` (string, optional): Filter by location
- `page` (integer, optional): Page number, default: `1`
- `per_page` (integer, optional): Items per page, default: `12`

**Response (200 OK):**
```json
{
  "chefs": [
    {
      "id": 1,
      "name": "Chef Marco",
      "bio": "Expert in Italian cuisine with 10 years experience",
      "cuisine_type": "Italian",
      "location": "Seoul",
      "price_per_session": 100000,
      "rating": 4.8,
      "rating_count": 25
    }
  ],
  "total": 50,
  "pages": 5,
  "current_page": 1
}
```

### Get Chef Details

```http
GET /api/coocook/chefs/{chef_id}
```

Get detailed information about a specific chef (public endpoint).

**Response (200 OK):**
```json
{
  "id": 1,
  "name": "Chef Marco",
  "bio": "Expert in Italian cuisine with 10 years experience",
  "cuisine_type": "Italian",
  "location": "Seoul",
  "price_per_session": 100000,
  "rating": 4.8,
  "rating_count": 25,
  "user_id": 5
}
```

**Error Responses:**
- `404 Not Found:` Chef not found

### Register as Chef

```http
POST /api/coocook/chefs
```

Register the authenticated user as a chef.

**Headers:** `Authorization: Bearer {access_token}`

**Request Body:**
```json
{
  "name": "Chef Marco",
  "bio": "Expert in Italian cuisine",
  "cuisine_type": "Italian",
  "location": "Seoul",
  "price_per_session": 100000
}
```

**Required Fields:** `name`, `cuisine_type`, `location`, `price_per_session`

**Response (201 Created):**
```json
{
  "id": 1,
  "message": "Chef registered successfully"
}
```

**Error Responses:**
- `400 Bad Request:` Missing fields or already registered as chef

### Get Chef Reviews

```http
GET /api/coocook/chefs/{chef_id}/reviews
```

Get all reviews for a specific chef (public endpoint).

**Response (200 OK):**
```json
{
  "chef_id": 1,
  "chef_name": "Chef Marco",
  "average_rating": 4.8,
  "total_reviews": 25,
  "reviews": [
    {
      "id": 1,
      "user_id": 2,
      "rating": 5,
      "comment": "Excellent food and service!",
      "created_at": "2026-02-20T10:30:00Z"
    }
  ]
}
```

### Get User's Bookings

```http
GET /api/coocook/bookings
```

Get all bookings for the authenticated user (requires CooCook subscription).

**Headers:** `Authorization: Bearer {access_token}`

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "chef_name": "Chef Marco",
    "chef_cuisine": "Italian",
    "booking_date": "2026-03-15",
    "duration_hours": 3,
    "total_price": 300000,
    "status": "confirmed",
    "special_requests": "Extra spicy",
    "created_at": "2026-02-20T10:30:00Z"
  }
]
```

**Error Responses:**
- `403 Forbidden:` CooCook subscription required

### Create Booking

```http
POST /api/coocook/bookings
```

Book a chef for a date and duration (requires CooCook subscription).

**Headers:** `Authorization: Bearer {access_token}`

**Request Body:**
```json
{
  "chef_id": 1,
  "booking_date": "2026-03-15T19:00:00",
  "duration_hours": 3,
  "special_requests": "Extra spicy"
}
```

**Required Fields:** `chef_id`, `booking_date`, `duration_hours`

**Response (201 Created):**
```json
{
  "id": 1,
  "message": "Booking created successfully",
  "total_price": 300000
}
```

**Error Responses:**
- `400 Bad Request:` Past date or invalid duration
- `404 Not Found:` Chef not found
- `403 Forbidden:` CooCook subscription required

### Get Booking Details

```http
GET /api/coocook/bookings/{booking_id}
```

Get details of a specific booking (requires CooCook subscription).

**Headers:** `Authorization: Bearer {access_token}`

**Response (200 OK):**
```json
{
  "id": 1,
  "chef_id": 1,
  "chef_name": "Chef Marco",
  "booking_date": "2026-03-15",
  "duration_hours": 3,
  "total_price": 300000,
  "status": "pending",
  "special_requests": "Extra spicy",
  "created_at": "2026-02-20T10:30:00Z"
}
```

### Update Booking Status

```http
PUT /api/coocook/bookings/{booking_id}
```

Update booking status (only chef can update).

**Headers:** `Authorization: Bearer {access_token}`

**Request Body:**
```json
{
  "status": "confirmed"
}
```

**Status Values:** `pending`, `confirmed`, `completed`, `cancelled`

**Response (200 OK):**
```json
{
  "message": "Booking updated"
}
```

### Process Booking Payment

```http
POST /api/coocook/bookings/{booking_id}/pay
```

Process payment for a booking (requires CooCook subscription).

**Headers:** `Authorization: Bearer {access_token}`

**Request Body:**
```json
{
  "amount": 300000
}
```

**Response (200 OK):**
```json
{
  "message": "Payment processed successfully",
  "payment_id": 1,
  "booking_id": 1,
  "amount": 300000
}
```

**Error Responses:**
- `400 Bad Request:` Already paid or amount mismatch
- `403 Forbidden:` Not authorized

### Submit Review for Booking

```http
POST /api/coocook/bookings/{booking_id}/review
```

Submit a review after booking completion.

**Headers:** `Authorization: Bearer {access_token}`

**Request Body:**
```json
{
  "rating": 5,
  "comment": "Amazing experience! Highly recommended."
}
```

**Required Fields:** `rating` (1-5)

**Response (201 Created):**
```json
{
  "message": "Review submitted successfully",
  "review_id": 1,
  "chef_rating": 4.8,
  "rating_count": 26
}
```

**Error Responses:**
- `400 Bad Request:` Can only review completed bookings or already reviewed

---

## SNS Auto - Social Media Automation

### Get SNS Accounts

```http
GET /api/sns/accounts
```

Get all linked SNS accounts (requires SNS Auto subscription).

**Headers:** `Authorization: Bearer {access_token}`

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "platform": "instagram",
    "account_name": "myaccount",
    "is_active": true,
    "post_count": 15,
    "created_at": "2026-02-10T10:30:00Z"
  }
]
```

### Link SNS Account

```http
POST /api/sns/accounts
```

Link a new social media account (requires SNS Auto subscription).

**Headers:** `Authorization: Bearer {access_token}`

**Request Body:**
```json
{
  "platform": "instagram",
  "account_name": "myaccount"
}
```

**Required Fields:** `platform`, `account_name`

**Supported Platforms:** `instagram`, `tiktok`, `youtube`, `blog`

**Response (201 Created):**
```json
{
  "id": 1,
  "message": "Account linked successfully"
}
```

**Error Responses:**
- `400 Bad Request:` Account already linked

### Unlink SNS Account

```http
DELETE /api/sns/accounts/{account_id}
```

Remove a linked SNS account.

**Headers:** `Authorization: Bearer {access_token}`

**Response (200 OK):**
```json
{
  "message": "Account unlinked"
}
```

### Get SNS Posts

```http
GET /api/sns/posts
```

Get all SNS posts with optional filters (requires SNS Auto subscription).

**Headers:** `Authorization: Bearer {access_token}`

**Query Parameters:**
- `account_id` (integer, optional): Filter by account
- `status` (string, optional): Filter by status (`draft`, `scheduled`, `published`)
- `page` (integer, optional): Page number, default: `1`

**Response (200 OK):**
```json
{
  "posts": [
    {
      "id": 1,
      "account_name": "myaccount",
      "platform": "instagram",
      "content": "Amazing new product launch...",
      "status": "published",
      "template_type": "carousel",
      "scheduled_at": null,
      "created_at": "2026-02-20T10:30:00Z"
    }
  ],
  "total": 50,
  "pages": 3,
  "current_page": 1
}
```

### Create SNS Post

```http
POST /api/sns/posts
```

Create a new SNS post (requires SNS Auto subscription).

**Headers:** `Authorization: Bearer {access_token}`

**Request Body:**
```json
{
  "account_id": 1,
  "content": "Amazing new product launch coming soon!",
  "template_type": "carousel"
}
```

**Required Fields:** `account_id`, `content`, `template_type`

**Template Types:** `card_news`, `reel`, `shorts`, `carousel`, `blog_post`

**Response (201 Created):**
```json
{
  "id": 1,
  "message": "Post created successfully"
}
```

### Publish or Schedule Post

```http
POST /api/sns/posts/{post_id}/publish
```

Publish immediately or schedule for later (requires SNS Auto subscription).

**Headers:** `Authorization: Bearer {access_token}`

**Request Body:**
```json
{
  "scheduled_at": "2026-02-25T15:00:00"
}
```

**Optional Fields:**
- `scheduled_at`: Schedule for future time; if omitted, publishes immediately

**Response (200 OK):**
```json
{
  "id": 1,
  "status": "scheduled",
  "message": "Post scheduled"
}
```

### Delete Post

```http
DELETE /api/sns/posts/{post_id}
```

Delete a draft or scheduled post.

**Headers:** `Authorization: Bearer {access_token}`

**Response (200 OK):**
```json
{
  "message": "Post deleted"
}
```

**Error Responses:**
- `400 Bad Request:` Cannot delete published posts

### Get Template Library

```http
GET /api/sns/templates
```

Get available SNS post templates (requires authentication).

**Headers:** `Authorization: Bearer {access_token}`

**Response (200 OK):**
```json
{
  "card_news": {
    "name": "Card News",
    "platforms": ["instagram", "tiktok"]
  },
  "blog_post": {
    "name": "Blog Post",
    "platforms": ["blog"]
  },
  "reel": {
    "name": "Reel",
    "platforms": ["instagram"]
  },
  "shorts": {
    "name": "YouTube Shorts",
    "platforms": ["youtube"]
  },
  "carousel": {
    "name": "Carousel",
    "platforms": ["instagram"]
  }
}
```

---

## Review - Influencer Campaigns

### List Campaigns

```http
GET /api/review/campaigns
```

Browse active review campaigns (public endpoint).

**Query Parameters:**
- `category` (string, optional): Filter by category
- `page` (integer, optional): Page number, default: `1`
- `per_page` (integer, optional): Items per page, default: `12`

**Response (200 OK):**
```json
{
  "campaigns": [
    {
      "id": 1,
      "title": "Winter Jacket Review Campaign",
      "product_name": "TechJacket Pro",
      "category": "Fashion",
      "reward_type": "cash",
      "reward_value": 50000,
      "max_reviewers": 10,
      "applications_count": 5,
      "deadline": "2026-03-15T23:59:59Z",
      "created_at": "2026-02-20T10:30:00Z"
    }
  ],
  "total": 20,
  "pages": 2,
  "current_page": 1
}
```

### Get Campaign Details

```http
GET /api/review/campaigns/{campaign_id}
```

Get detailed information about a campaign (public endpoint).

**Response (200 OK):**
```json
{
  "id": 1,
  "title": "Winter Jacket Review Campaign",
  "description": "Test our new waterproof winter jacket and share honest reviews",
  "product_name": "TechJacket Pro",
  "category": "Fashion",
  "reward_type": "cash",
  "reward_value": 50000,
  "max_reviewers": 10,
  "applications_count": 5,
  "spots_available": 5,
  "deadline": "2026-03-15T23:59:59Z",
  "status": "active",
  "created_at": "2026-02-20T10:30:00Z"
}
```

### Create Campaign

```http
POST /api/review/campaigns
```

Create a new review campaign (requires Review subscription).

**Headers:** `Authorization: Bearer {access_token}`

**Request Body:**
```json
{
  "title": "Winter Jacket Review Campaign",
  "description": "Test our new waterproof winter jacket and share honest reviews",
  "product_name": "TechJacket Pro",
  "category": "Fashion",
  "reward_type": "cash",
  "reward_value": 50000,
  "max_reviewers": 10,
  "deadline": "2026-03-15T23:59:59Z"
}
```

**Required Fields:** All fields above

**Reward Types:** `cash`, `product`, `mixed`

**Response (201 Created):**
```json
{
  "id": 1,
  "message": "Campaign created successfully"
}
```

### Apply to Campaign

```http
POST /api/review/campaigns/{campaign_id}/apply
```

Apply as a reviewer for a campaign.

**Headers:** `Authorization: Bearer {access_token}`

**Request Body:**
```json
{
  "message": "I would love to review this product. I have 50k followers on Instagram.",
  "sns_link": "https://instagram.com/myaccount",
  "follower_count": 50000
}
```

**Required Fields:** `message`

**Response (201 Created):**
```json
{
  "id": 1,
  "message": "Application submitted successfully"
}
```

**Error Responses:**
- `400 Bad Request:` Already applied or campaign full
- `404 Not Found:` Campaign not found or closed

### Get My Campaigns

```http
GET /api/review/my-campaigns
```

Get all campaigns created by the authenticated user (requires Review subscription).

**Headers:** `Authorization: Bearer {access_token}`

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "title": "Winter Jacket Review Campaign",
    "product_name": "TechJacket Pro",
    "category": "Fashion",
    "max_reviewers": 10,
    "applications_count": 7,
    "deadline": "2026-03-15T23:59:59Z",
    "status": "active"
  }
]
```

### Get My Applications

```http
GET /api/review/my-applications
```

Get all campaigns the user has applied to.

**Headers:** `Authorization: Bearer {access_token}`

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "campaign_title": "Winter Jacket Review Campaign",
    "product_name": "TechJacket Pro",
    "reward_value": 50000,
    "status": "pending",
    "applied_at": "2026-02-22T15:30:00Z"
  }
]
```

### Get Campaign Applications

```http
GET /api/review/campaigns/{campaign_id}/applications
```

Get all applications for a campaign (creator only, requires Review subscription).

**Headers:** `Authorization: Bearer {access_token}`

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "user_name": "Jane Smith",
    "user_email": "jane@example.com",
    "message": "I have extensive fashion review experience",
    "sns_link": "https://instagram.com/janefashion",
    "follower_count": 50000,
    "status": "pending"
  }
]
```

**Error Responses:**
- `403 Forbidden:` Not the campaign creator

### Update Application Status

```http
PUT /api/review/applications/{application_id}
```

Approve or reject an application (creator only, requires Review subscription).

**Headers:** `Authorization: Bearer {access_token}`

**Request Body:**
```json
{
  "status": "approved"
}
```

**Status Values:** `pending`, `approved`, `rejected`

**Response (200 OK):**
```json
{
  "message": "Application updated"
}
```

---

## AI Automation

### Get Subscription Plans

```http
GET /api/ai-automation/plans
```

Get available AI Automation subscription plans (public endpoint).

**Response (200 OK):**
```json
{
  "starter": {
    "name": "Starter",
    "price": 49000,
    "hours_saved": "10시간",
    "features": [
      "기본 레슨",
      "월 2개 시나리오 토큰",
      "커뮤니티 Q&A"
    ]
  },
  "ambassador": {
    "name": "Ambassador",
    "price": 89000,
    "hours_saved": "15시간",
    "features": [
      "전체 레슨 + 워크샵",
      "월 4개 시나리오 토큰",
      "1:1 코칭"
    ]
  },
  "enterprise": {
    "name": "Enterprise",
    "price": 290000,
    "hours_saved": "30시간",
    "features": [
      "무제한 레슨 + 워크샵",
      "무제한 시나리오 토큰",
      "전담 코칭"
    ]
  }
}
```

### Get Available Scenarios

```http
GET /api/ai-automation/scenarios
```

Get available automation scenarios (public endpoint).

**Query Parameters:**
- `category` (string, optional): Filter by category

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "name": "Email Automation",
    "category": "Communication",
    "description": "Automate email responses and filing",
    "difficulty": "beginner"
  }
]
```

### Get Scenario Details

```http
GET /api/ai-automation/scenarios/{scenario_id}
```

Get detailed information about a scenario (public endpoint).

**Response (200 OK):**
```json
{
  "id": 1,
  "name": "Email Automation",
  "category": "Communication",
  "description": "Automate email responses and filing",
  "difficulty": "beginner",
  "estimated_savings_hours": 10
}
```

### Get AI Employees

```http
GET /api/ai-automation/employees
```

Get all AI employees for the authenticated user (requires AI Automation subscription).

**Headers:** `Authorization: Bearer {access_token}`

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "name": "EmailBot",
    "scenario_type": "email",
    "status": "active",
    "monthly_savings_hours": 15,
    "deployed_at": "2026-02-15T10:30:00Z"
  }
]
```

### Create AI Employee

```http
POST /api/ai-automation/employees
```

Create a new AI employee (requires AI Automation subscription).

**Headers:** `Authorization: Bearer {access_token}`

**Request Body:**
```json
{
  "name": "EmailBot",
  "scenario_type": "email",
  "description": "Automates email responses and filing"
}
```

**Required Fields:** `name`, `scenario_type`

**Scenario Types:** `email`, `social`, `customer_service`, `data_entry`, `scheduling`

**Response (201 Created):**
```json
{
  "id": 1,
  "message": "AI Employee created successfully",
  "employee": {
    "id": 1,
    "name": "EmailBot",
    "scenario_type": "email",
    "status": "draft"
  }
}
```

### Get AI Employee Details

```http
GET /api/ai-automation/employees/{employee_id}
```

Get detailed information about an AI employee.

**Headers:** `Authorization: Bearer {access_token}`

**Response (200 OK):**
```json
{
  "id": 1,
  "name": "EmailBot",
  "scenario_type": "email",
  "description": "Automates email responses and filing",
  "status": "active",
  "monthly_savings_hours": 15,
  "deployed_at": "2026-02-15T10:30:00Z"
}
```

### Deploy AI Employee

```http
POST /api/ai-automation/employees/{employee_id}/deploy
```

Deploy an AI employee (move from draft to training).

**Headers:** `Authorization: Bearer {access_token}`

**Request Body (optional):**
```json
{
  "savings_hours": 15
}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "message": "AI Employee deployed successfully",
  "status": "training"
}
```

### Activate AI Employee

```http
POST /api/ai-automation/employees/{employee_id}/activate
```

Activate an AI employee (move from training to active).

**Headers:** `Authorization: Bearer {access_token}`

**Response (200 OK):**
```json
{
  "message": "AI Employee activated successfully",
  "status": "active"
}
```

### Delete AI Employee

```http
DELETE /api/ai-automation/employees/{employee_id}
```

Delete an AI employee (cannot delete if active).

**Headers:** `Authorization: Bearer {access_token}`

**Response (200 OK):**
```json
{
  "message": "AI Employee deleted"
}
```

**Error Responses:**
- `400 Bad Request:` Cannot delete active employee

### Get Automation Dashboard

```http
GET /api/ai-automation/dashboard
```

Get dashboard summary with all AI employees and savings.

**Headers:** `Authorization: Bearer {access_token}`

**Response (200 OK):**
```json
{
  "total_employees": 3,
  "active_employees": 2,
  "total_monthly_savings_hours": 45,
  "estimated_annual_savings": "₩675,000",
  "employees": [
    {
      "id": 1,
      "name": "EmailBot",
      "scenario_type": "email",
      "status": "active",
      "monthly_savings_hours": 15
    }
  ]
}
```

---

## WebApp Builder

### Get Bootcamp Plans

```http
GET /api/webapp-builder/plans
```

Get available bootcamp plans (public endpoint).

**Response (200 OK):**
```json
{
  "weekday": {
    "name": "평일반 (월~금)",
    "price": 590000,
    "duration": "8주",
    "schedule": "19:00~21:00 (2시간/일, 5일/주)",
    "seats": 3,
    "available": 3
  },
  "weekend": {
    "name": "주말반 (토~일)",
    "price": 590000,
    "duration": "8주",
    "schedule": "10:00~14:00 (4시간/일, 2일/주)",
    "seats": 0,
    "available": 0
  }
}
```

### Get Bootcamp Courses

```http
GET /api/webapp-builder/courses
```

Get all bootcamp courses (public endpoint).

**Response (200 OK):**
```json
{
  "automation_1": {
    "name": "업무 자동화 1: 이메일 + 데이터 입력",
    "duration_weeks": 2,
    "difficulty": "beginner",
    "description": "반복 업무를 AI로 자동화. 8시간/주"
  },
  "automation_2": {
    "name": "업무 자동화 2: 고객 관리 시스템",
    "duration_weeks": 2,
    "difficulty": "intermediate",
    "description": "고객 데이터 자동 정리 및 분석"
  },
  "automation_3": {
    "name": "업무 자동화 3: 리포팅 자동화",
    "duration_weeks": 2,
    "difficulty": "intermediate",
    "description": "일일/주간/월간 리포트 자동 생성"
  },
  "webapp": {
    "name": "나만의 웹앱 만들기",
    "duration_weeks": 2,
    "difficulty": "advanced",
    "description": "AI 보조로 풀스택 웹앱 개발. HTML + Python + DB"
  }
}
```

### Enroll in Bootcamp

```http
POST /api/webapp-builder/enroll
```

Enroll in a bootcamp class (requires WebApp Builder subscription).

**Headers:** `Authorization: Bearer {access_token}`

**Request Body:**
```json
{
  "plan_type": "weekday"
}
```

**Plan Types:** `weekday`, `weekend`

**Response (201 Created):**
```json
{
  "id": 1,
  "message": "Enrolled in 평일반 (월~금)",
  "enrollment": {
    "id": 1,
    "plan_type": "weekday",
    "start_date": "2026-02-25T00:00:00Z",
    "end_date": "2026-04-22T00:00:00Z",
    "status": "in_progress"
  }
}
```

**Error Responses:**
- `400 Bad Request:` No seats available or already enrolled

### Get Bootcamp Enrollments

```http
GET /api/webapp-builder/enrollments
```

Get all bootcamp enrollments for the user (requires WebApp Builder subscription).

**Headers:** `Authorization: Bearer {access_token}`

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "plan_type": "weekday",
    "start_date": "2026-02-25T00:00:00Z",
    "end_date": "2026-04-22T00:00:00Z",
    "status": "in_progress"
  }
]
```

### Get User's WebApps

```http
GET /api/webapp-builder/webapps
```

Get all created webapp projects (requires WebApp Builder subscription).

**Headers:** `Authorization: Bearer {access_token}`

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "name": "My First WebApp",
    "description": "A task management application",
    "status": "draft",
    "url": null,
    "deployed_at": null
  }
]
```

### Create WebApp Project

```http
POST /api/webapp-builder/webapps
```

Create a new webapp project (requires WebApp Builder subscription).

**Headers:** `Authorization: Bearer {access_token}`

**Request Body:**
```json
{
  "name": "My First WebApp",
  "description": "A task management application"
}
```

**Required Fields:** `name`

**Response (201 Created):**
```json
{
  "id": 1,
  "message": "WebApp project created",
  "webapp": {
    "id": 1,
    "name": "My First WebApp",
    "description": "A task management application",
    "status": "draft"
  }
}
```

### Get WebApp Details

```http
GET /api/webapp-builder/webapps/{webapp_id}
```

Get detailed information about a webapp project.

**Headers:** `Authorization: Bearer {access_token}`

**Response (200 OK):**
```json
{
  "id": 1,
  "name": "My First WebApp",
  "description": "A task management application",
  "status": "draft",
  "url": null,
  "code_repo": null,
  "created_at": "2026-02-25T10:30:00Z",
  "deployed_at": null
}
```

### Deploy WebApp

```http
POST /api/webapp-builder/webapps/{webapp_id}/deploy
```

Deploy a webapp project to live.

**Headers:** `Authorization: Bearer {access_token}`

**Request Body (optional):**
```json
{
  "url": "https://mywebapp.com",
  "repo": "https://github.com/user/webapp"
}
```

**Response (200 OK):**
```json
{
  "message": "WebApp deployed successfully",
  "webapp": {
    "id": 1,
    "name": "My First WebApp",
    "status": "deployed",
    "url": "https://mywebapp.com",
    "deployed_at": "2026-02-25T15:30:00Z"
  }
}
```

### Get WebApp Dashboard

```http
GET /api/webapp-builder/dashboard
```

Get bootcamp dashboard with enrollments and webapps.

**Headers:** `Authorization: Bearer {access_token}`

**Response (200 OK):**
```json
{
  "active_enrollment": {
    "id": 1,
    "plan_type": "weekday",
    "status": "in_progress"
  },
  "total_enrollments": 1,
  "webapps_created": 3,
  "webapps_deployed": 1,
  "courses": {
    "automation_1": {
      "name": "업무 자동화 1: 이메일 + 데이터 입력",
      "duration_weeks": 2
    }
  }
}
```

---

## Experience Platform

### Get Experience Listings

```http
GET /api/experience/listings
```

Get experience opportunity listings from partner sites (public endpoint).

**Query Parameters:**
- `site` (string, optional): Filter by site
- `category` (string, optional): Filter by category
- `page` (integer, optional): Page number, default: `1`
- `per_page` (integer, optional): Items per page, default: `12`

**Response (200 OK):**
```json
{
  "total": 12,
  "page": 1,
  "per_page": 12,
  "pages": 1,
  "data": [
    {
      "site": "coupang_eats",
      "title": "[쿠팡이츠] 맛집 배달 리뷰 체험단",
      "url": "https://www.coupangeats.com",
      "deadline": "2026-02-28T23:59:59Z",
      "category": "음식",
      "reward": "무료 음식 + 현금 2만원",
      "description": "신규 맛집의 배달 음식을 먹고 솔직한 리뷰를 남겨주세요",
      "image_url": "https://via.placeholder.com/300x200"
    }
  ]
}
```

### Get Listing Details

```http
GET /api/experience/listings/{listing_id}
```

Get detailed information about a specific listing (public endpoint).

**Response (200 OK):**
```json
{
  "id": 1001,
  "site": "coupang_eats",
  "title": "[쿠팡이츠] 맛집 배달 리뷰 체험단",
  "url": "https://www.coupangeats.com",
  "deadline": "2026-02-28T23:59:59Z",
  "category": "음식",
  "reward": "무료 음식 + 현금 2만원",
  "description": "신규 맛집의 배달 음식을 먹고 솔직한 리뷰를 남겨주세요",
  "image_url": "https://via.placeholder.com/300x200"
}
```

### Get Platform Statistics

```http
GET /api/experience/stats
```

Get platform statistics and crawler status (public endpoint).

**Response (200 OK):**
```json
{
  "total_listings": 12,
  "total_sites": 4,
  "sites": {
    "coupang_eats": {
      "count": 2,
      "categories": ["음식"]
    },
    "danggeun": {
      "count": 3,
      "categories": ["카페", "편의점", "음식"]
    }
  },
  "categories": {
    "음식": 5,
    "카페": 1,
    "편의점": 1,
    "생활서비스": 1,
    "인테리어": 1,
    "뷰티": 1
  },
  "last_updated": "2026-02-25T10:30:00Z"
}
```

### Get Available Categories

```http
GET /api/experience/categories
```

Get all available experience categories (public endpoint).

**Response (200 OK):**
```json
{
  "categories": [
    "음식",
    "카페",
    "편의점",
    "뷰티",
    "생활서비스",
    "인테리어"
  ]
}
```

### Get Available Sites

```http
GET /api/experience/sites
```

Get all crawled partner sites (public endpoint).

**Response (200 OK):**
```json
{
  "sites": {
    "coupang_eats": {
      "name": "Coupang Eats",
      "count": 2
    },
    "danggeun": {
      "name": "Danggeun",
      "count": 3
    },
    "soomgo": {
      "name": "Soomgo",
      "count": 2
    },
    "today_deal": {
      "name": "Today Deal",
      "count": 1
    }
  }
}
```

### Trigger Web Crawler

```http
POST /api/experience/crawl
```

Trigger the web crawler to update listings (public endpoint).

**Request Body (optional):**
```json
{
  "site": "coupang_eats"
}
```

**Response (200 OK):**
```json
{
  "status": "success",
  "site": "coupang_eats",
  "listings_found": 2,
  "timestamp": "2026-02-25T10:30:00Z"
}
```

---

## JARVIS - Multi-Agent System

### Get All Teams

```http
GET /api/v1/teams
```

Get information about all 10 agent teams (public endpoint).

**Response (200 OK):**
```json
{
  "teams": [
    {
      "id": 1,
      "name": "Team 01 — Dispatcher",
      "progress": 85,
      "skills": 8,
      "status": "active",
      "color": "#10b981"
    }
  ],
  "total_teams": 10,
  "active_teams": 2,
  "total_skills": 70,
  "avg_progress": 51.5,
  "timestamp": "2026-02-25T10:30:00Z"
}
```

### Get Team Details

```http
GET /api/v1/teams/{team_id}
```

Get detailed information about a specific team (public endpoint).

**Response (200 OK):**
```json
{
  "team": {
    "id": 1,
    "name": "Team 01 — Dispatcher",
    "progress": 85,
    "skills": 8,
    "status": "active"
  },
  "skills_breakdown": {
    "completed": 8,
    "in_progress": 0,
    "pending": 0
  },
  "timeline": [
    {
      "date": "2026-02-25",
      "event": "Team initialized",
      "status": "complete"
    }
  ]
}
```

### Get Team Breakdown

```http
GET /api/v1/teams/breakdown
```

Get detailed capacity analysis and bottleneck identification (public endpoint).

**Response (200 OK):**
```json
{
  "capacity_analysis": {
    "high_capacity": {
      "count": 3,
      "teams": [
        {"id": 1, "name": "Team 01", "progress": 85}
      ],
      "avg_progress": 76.7
    },
    "medium_capacity": {
      "count": 4,
      "teams": [],
      "avg_progress": 61.25
    },
    "low_capacity": {
      "count": 3,
      "teams": [],
      "avg_progress": 26
    }
  },
  "bottlenecks": [
    {
      "team": "Team 05 (Backend)",
      "issue": "Low progress (62%)",
      "impact": "High",
      "recommendation": "Allocate senior resources"
    }
  ]
}
```

### Get Project Timeline

```http
GET /api/v1/teams/timeline
```

Get milestone timeline and critical path (public endpoint).

**Response (200 OK):**
```json
{
  "milestones": [
    {
      "date": "2026-02-25",
      "title": "Governance v3.0 배포",
      "status": "complete"
    }
  ],
  "critical_path": [
    "Team 01 Dispatcher — Setup",
    "Team 04 Architect — Design",
    "Team 05 Backend — Implementation (BOTTLENECK)"
  ],
  "project_timeline": {
    "start_date": "2026-02-22",
    "target_completion": "2026-03-15",
    "days_remaining": 21,
    "phases": [
      {
        "name": "Planning & Design",
        "progress": 100,
        "end_date": "2026-02-25"
      }
    ]
  }
}
```

### Get System Statistics

```http
GET /api/v1/stats
```

Get comprehensive system statistics (public endpoint).

**Response (200 OK):**
```json
{
  "summary": {
    "total_teams": 10,
    "active_teams": 2,
    "in_progress_teams": 3,
    "pending_teams": 5,
    "total_skills": 70,
    "completed_skills": 48,
    "overall_progress": 51.5
  },
  "by_status": {
    "active": 2,
    "progress": 3,
    "pending": 5
  },
  "top_performers": [
    {"id": 1, "name": "Team 01", "progress": 85}
  ],
  "needs_attention": [
    {"id": 10, "name": "Team 10", "progress": 15}
  ],
  "estimated_completion": "2026-03-15",
  "health_status": "GOOD",
  "timestamp": "2026-02-25T10:30:00Z"
}
```

---

## Error Handling

### HTTP Status Codes

| Code | Meaning | Common Causes |
|------|---------|---------------|
| `200` | OK | Successful GET/PUT request |
| `201` | Created | Successful POST request |
| `400` | Bad Request | Invalid input, missing fields |
| `401` | Unauthorized | Missing or invalid token |
| `403` | Forbidden | Insufficient permissions or subscription |
| `404` | Not Found | Resource doesn't exist |
| `500` | Server Error | Internal server error |

### Error Response Format

All error responses follow this format:

```json
{
  "error": "Error message describing what went wrong"
}
```

### Common Error Messages

| Error | HTTP Code | Solution |
|-------|-----------|----------|
| Missing authorization header | 401 | Add `Authorization: Bearer {token}` header |
| Invalid or expired token | 401 | Refresh token or login again |
| Admin access required | 403 | Only admin users can access this endpoint |
| Product subscription required | 403 | User must subscribe to the product first |
| Already subscribed | 400 | Unsubscribe before subscribing again |
| Resource not found | 404 | Check the ID and try again |
| Email already registered | 400 | Use a different email or login |
| Invalid request body | 400 | Check required fields in documentation |

---

## Rate Limiting & Throttling

### Rate Limits

The API implements the following rate limits per user:

- **Authentication endpoints:** 10 requests/minute
- **Payment endpoints:** 20 requests/hour
- **General endpoints:** 100 requests/minute
- **Admin endpoints:** 50 requests/hour

### Handling Rate Limits

When rate limited, the API returns:

```
HTTP/1.1 429 Too Many Requests
Retry-After: 60
```

**Recommendation:** Implement exponential backoff in your client with a maximum wait time of 60 seconds.

---

## Pagination

Endpoints that return lists support pagination with these query parameters:

- `page` (integer, default: 1): Page number
- `per_page` (integer, default: varies): Items per page

**Response format:**
```json
{
  "items": [],
  "total": 100,
  "pages": 5,
  "current_page": 1
}
```

---

## Demo Account Credentials

For testing without setting up authentication:

**Email:** demo@softfactory.com
**Token:** demo_token
**Access:** All services with full subscriptions

### Example Request with Demo Token

```bash
curl -X GET http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer demo_token"
```

---

## Support & Documentation

- **Documentation:** https://docs.softfactory.com
- **Status Page:** https://status.softfactory.com
- **Support Email:** support@softfactory.com
- **GitHub:** https://github.com/softfactory/api

---

**Last Updated:** 2026-02-25 | **API Version:** 2.1.0
