# Payment & Billing API

**Version:** 2.0
**Status:** Production Ready
**Base URL:** `/api/payment`

## Overview

Enhanced payment system with KRW support, PDF invoices, subscriptions, and Stripe integration.

- **Currency:** KRW (Korean Won) + multiple currencies
- **Invoicing:** PDF generation with ReportLab
- **Subscriptions:** Flexible monthly/annual plans
- **Payment Methods:** Stripe + bank transfer
- **Compliance:** Tax calculation, audit trail

---

## Core Endpoints

### 1. Create Invoice

**POST** `/api/payment/invoice`

Generate an invoice for an order with PDF.

**Headers:**
```
Authorization: Bearer {jwt_token}
Content-Type: application/json
```

**Request:**
```json
{
  "order_id": 42,
  "amount_krw": 99000,
  "tax_krw": 9900,
  "due_days": 30
}
```

**Response:** (201 Created)
```json
{
  "invoice_id": 15,
  "invoice_number": "20260226-0001",
  "pdf_url": "https://softfactory-uploads.s3.us-east-1.amazonaws.com/invoices/123/20260226-0001.pdf",
  "stripe_url": "https://invoice.stripe.com/i/acct_...",
  "total_krw": 108900
}
```

**Parameters:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `order_id` | int | No | Associated order |
| `amount_krw` | int | Yes | Invoice amount in KRW |
| `tax_krw` | int | No | Tax amount (default: 0) |
| `due_days` | int | No | Days until due (default: 30) |

**Errors:**
- `400 Bad Request` — Invalid amount
- `500 Server Error` — PDF generation or S3 upload failed

---

### 2. Create Subscription

**POST** `/api/payment/subscribe`

Create or upgrade a subscription plan.

**Headers:**
```
Authorization: Bearer {jwt_token}
Content-Type: application/json
```

**Request:**
```json
{
  "plan_slug": "pro-monthly",
  "billing_period": "monthly",
  "stripe_token": "tok_visa"
}
```

**Response:** (201 Created)
```json
{
  "subscription_id": 8,
  "plan_name": "Pro Plan",
  "next_billing_date": "2026-03-26T14:30:22",
  "stripe_subscription_id": "sub_1N8z...",
  "amount_krw": 29900,
  "period": "monthly",
  "status": "active"
}
```

**Parameters:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `plan_id` | int | No | Plan ID (alternative to slug) |
| `plan_slug` | string | No | Plan identifier (e.g., "pro-monthly") |
| `billing_period` | string | Yes | "monthly" or "annual" |
| `stripe_token` | string | No | Card token for new payment method |

**Plan Slugs:**
- `starter-monthly` — 9,900 KRW/month
- `starter-annual` — 99,000 KRW/year
- `pro-monthly` — 29,900 KRW/month
- `pro-annual` — 299,000 KRW/year
- `enterprise-monthly` — 99,900 KRW/month
- `enterprise-annual` — 999,000 KRW/year

**Errors:**
- `404 Not Found` — Plan not found
- `400 Bad Request` — Stripe error or missing configuration
- `500 Server Error` — Database error

---

### 3. Get Payment History

**GET** `/api/payment/history`

Retrieve user's payment and invoice history.

**Headers:**
```
Authorization: Bearer {jwt_token}
```

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `status` | string | (all) | Filter: "paid", "pending", "canceled" |
| `limit` | int | 50 | Max results per page (max 100) |
| `offset` | int | 0 | Pagination offset |

**Example:**
```bash
GET /api/payment/history?status=paid&limit=20&offset=0
```

**Response:** (200 OK)
```json
{
  "total": 47,
  "limit": 20,
  "offset": 0,
  "history": [
    {
      "id": 42,
      "type": "invoice",
      "date": "2026-02-26T14:30:22",
      "amount_krw": 108900,
      "status": "paid",
      "invoice_number": "20260226-0001",
      "invoice_url": "https://...",
      "due_date": "2026-03-28T14:30:22"
    },
    {
      "id": 41,
      "type": "payment",
      "date": "2026-02-25T10:15:00",
      "amount": 99000,
      "status": "completed",
      "stripe_payment_id": "pi_1N8z..."
    }
  ]
}
```

---

### 4. Get Subscription Plans

**GET** `/api/payment/plans`

Retrieve all active subscription plans.

**Response:** (200 OK)
```json
[
  {
    "id": 1,
    "name": "Starter Plan",
    "slug": "starter-monthly",
    "description": "Perfect for small businesses",
    "monthly_price_krw": 9900,
    "annual_price_krw": 99000,
    "features": [
      "Up to 5 projects",
      "Basic analytics",
      "Email support"
    ],
    "max_projects": 5,
    "max_users": 3,
    "is_active": true
  },
  {
    "id": 2,
    "name": "Pro Plan",
    "slug": "pro-monthly",
    "description": "For growing teams",
    "monthly_price_krw": 29900,
    "annual_price_krw": 299000,
    "features": [
      "Unlimited projects",
      "Advanced analytics",
      "Priority support",
      "Custom integrations"
    ],
    "max_projects": null,
    "max_users": 10,
    "is_active": true
  }
]
```

---

## Legacy Endpoints (Still Supported)

### Get Plans
**GET** `/api/payment/plans`
- Returns active product plans

### Checkout Session
**POST** `/api/payment/checkout`
- Creates Stripe checkout session (deprecated, use `/subscribe`)

### Get Subscriptions
**GET** `/api/payment/subscriptions`
- Lists user's active subscriptions

### Cancel Subscription
**DELETE** `/api/payment/subscriptions/{subscription_id}`
- Cancels an active subscription

### Webhook Handler
**POST** `/api/payment/webhook`
- Stripe webhook handler for subscription events

---

## Database Schema

### Order Model
```python
class Order(db.Model):
    id: int
    user_id: int (FK)
    order_number: str (unique)
    status: str (pending/confirmed/shipped/delivered/canceled)
    items_json: str (JSON array)
    subtotal_krw: int
    tax_krw: int
    discount_krw: int
    total_amount_krw: int
    invoice_id: int (FK Invoices)
    created_at: datetime
    updated_at: datetime
```

### Invoice Model
```python
class Invoice(db.Model):
    id: int
    user_id: int (FK)
    order_id: int (FK Orders)
    invoice_number: str (unique, e.g., "20260226-0001")
    pdf_file_id: int (FK FileUploads)
    amount_krw: int
    tax_krw: int
    total_krw: int
    status: str (draft/issued/paid/canceled)
    issued_date: datetime
    due_date: datetime
    paid_date: datetime
    stripe_invoice_id: str
    payment_method: str (stripe/bank_transfer/etc)
```

### SubscriptionPlan Model
```python
class SubscriptionPlan(db.Model):
    id: int
    name: str
    slug: str (unique)
    description: str
    monthly_price_krw: int
    annual_price_krw: int
    stripe_price_id_monthly: str
    stripe_price_id_annual: str
    features_json: str (JSON array)
    max_projects: int
    max_users: int
    is_active: bool
```

---

## Workflow Examples

### Complete Purchase Flow

1. **Create Order**
   ```bash
   POST /api/orders
   { "items": [...], "customer": {...} }
   ```

2. **Generate Invoice**
   ```bash
   POST /api/payment/invoice
   { "order_id": 42, "amount_krw": 99000 }
   ```

3. **Process Payment via Stripe**
   - User receives PDF invoice
   - User visits Stripe URL
   - Payment confirmed via webhook

4. **Track History**
   ```bash
   GET /api/payment/history?status=paid
   ```

### Subscription Management

1. **View Plans**
   ```bash
   GET /api/payment/plans
   ```

2. **Subscribe**
   ```bash
   POST /api/payment/subscribe
   {
     "plan_slug": "pro-monthly",
     "billing_period": "monthly",
     "stripe_token": "tok_visa"
   }
   ```

3. **Upgrade (Auto-Cancel Old)**
   ```bash
   POST /api/payment/subscribe
   {
     "plan_slug": "enterprise-monthly",
     "stripe_token": "tok_visa"
   }
   ```

4. **Cancel**
   ```bash
   DELETE /api/payment/subscriptions/8
   ```

---

## Configuration

Set these in `.env`:

```env
# Stripe
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# AWS S3 (for invoice PDFs)
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
AWS_S3_BUCKET=softfactory-uploads
AWS_S3_REGION=us-east-1
CLOUDFRONT_DOMAIN=d123...cloudfront.net
```

---

## Tax & Currency

**Default:** KRW (Korean Won)

**Tax Rates:**
- VAT: 10% (configurable per item)
- Apply to line items or invoice total

**Multi-Currency Support:**
- Store original currency with amount
- Exchange rates updated daily
- Stripe handles conversion

---

## Error Handling

| Code | Error | Solution |
|------|-------|----------|
| 400 | Invalid amount | Ensure amount_krw > 0 |
| 404 | Plan not found | Check plan_id or plan_slug |
| 400 | S3 not configured | Set AWS credentials in .env |
| 500 | Stripe error | Check API keys and network |
| 403 | Unauthorized | Verify JWT token |

---

## Best Practices

1. **Invoice Storage:** Always upload PDF to S3 for audit trail
2. **Subscription:** Confirm via Stripe webhook before marking active
3. **Currency:** Always show KRW with comma formatting (99,000 KRW)
4. **Tax:** Calculate and display separately from subtotal
5. **Receipts:** Email PDF invoice to customer automatically
6. **Reconciliation:** Monthly audit of Stripe vs. database records

---

## Rate Limiting (Recommended)

- Create invoice: 100/min per user
- Subscribe: 10/min per user
- Get history: 1000/min per user
- Webhook: Unlimited (IP-whitelisted)

---

## Migration from v1.0

**v1.0 → v2.0 Changes:**
- Added KRW support (was USD only)
- PDF invoice generation (was Stripe only)
- Order management (new)
- SubscriptionPlan flexibility (was fixed Products)
- Presigned URLs and CDN support

**Backward Compatibility:** All v1.0 endpoints still functional

