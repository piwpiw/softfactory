# Payment System API Reference v2.0

> **Advanced Payment Processing** | KRW Conversion | Invoicing | Subscription Management
> Updated: 2026-02-26 | Production Ready

---

## Overview

The enhanced payment system provides comprehensive features for international transactions, invoice management, and flexible subscription billing.

**Key Features:**
- Automatic KRW/USD exchange rate conversion
- Multi-format invoice generation (PDF + Stripe)
- Flexible subscription plans with upgrade/downgrade
- 7-day refund policy enforcement
- Stripe webhook integration for auto-renewal

---

## Base URL

```
https://api.softfactory.com/api/payment
http://localhost:8000/api/payment (development)
```

---

## Authentication

All endpoints requiring authentication need the `Authorization` header:

```
Authorization: Bearer {jwt_token}
```

---

## Exchange Rate Management

### Get Current Exchange Rate

```http
GET /exchange-rate
```

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| base_currency | string | USD | Base currency code |
| target_currency | string | KRW | Target currency code |

**Response (200 OK):**
```json
{
  "base": "USD",
  "target": "KRW",
  "rate": 1250.50,
  "timestamp": "2026-02-26T10:30:45.123456"
}
```

**Error Response (400):**
```json
{
  "error": "Unsupported currency pair: EUR/JPY"
}
```

---

### Convert Currency

```http
POST /convert
Content-Type: application/json
```

**Request Body:**
```json
{
  "amount": 100,
  "from_currency": "USD",
  "to_currency": "KRW"
}
```

**Response (200 OK):**
```json
{
  "original_amount": 100,
  "from_currency": "USD",
  "to_currency": "KRW",
  "converted_amount": 125050,
  "rate": 1250.50
}
```

**Examples:**

USD to KRW:
```bash
curl -X POST https://api.softfactory.com/api/payment/convert \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 100,
    "from_currency": "USD",
    "to_currency": "KRW"
  }'
```

KRW to USD:
```bash
curl -X POST https://api.softfactory.com/api/payment/convert \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 125050,
    "from_currency": "KRW",
    "to_currency": "USD"
  }'
```

---

## Invoice Management

### Create Invoice

```http
POST /invoice
Authorization: Bearer {jwt_token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "order_id": 123,
  "amount_krw": 100000,
  "tax_rate": 0.10,
  "due_days": 30,
  "description": "Monthly subscription"
}
```

**Field Descriptions:**
| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| order_id | integer | No | null | Associated order ID |
| amount_krw | integer | Yes | - | Amount in KRW |
| tax_rate | float | No | 0.10 | Tax rate (10% VAT default) |
| due_days | integer | No | 30 | Payment due in N days |
| description | string | No | "Invoice Payment" | Invoice description |

**Response (201 Created):**
```json
{
  "invoice_id": 456,
  "invoice_number": "20260226-0001",
  "amount_krw": 100000,
  "tax_krw": 10000,
  "total_krw": 110000,
  "pdf_url": "https://s3.amazonaws.com/invoices/1/20260226-0001.pdf",
  "stripe_url": "https://invoice.stripe.com/...",
  "issued_date": "2026-02-26T10:30:45.123456",
  "due_date": "2026-03-28T10:30:45.123456"
}
```

**Example:**
```bash
curl -X POST https://api.softfactory.com/api/payment/invoice \
  -H "Authorization: Bearer {jwt_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "amount_krw": 100000,
    "tax_rate": 0.10,
    "due_days": 30,
    "description": "Monthly subscription - Starter Plan"
  }'
```

---

### Download Invoice PDF

```http
GET /invoices/{invoice_id}/download
Authorization: Bearer {jwt_token}
```

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| invoice_id | integer | Invoice ID |

**Response (200 OK):**
- Binary PDF file attachment
- Header: `Content-Type: application/pdf`
- Header: `Content-Disposition: attachment; filename="20260226-0001.pdf"`

**Response (404 Not Found):**
```json
{
  "error": "Invoice not found"
}
```

**Example:**
```bash
curl -X GET https://api.softfactory.com/api/payment/invoices/456/download \
  -H "Authorization: Bearer {jwt_token}" \
  -o invoice.pdf
```

---

## Subscription Management

### Get Subscription Plans

```http
GET /plans
```

**Query Parameters:** None

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "name": "Starter",
    "slug": "starter",
    "description": "Entry-level plan",
    "monthly_price_krw": 29900,
    "annual_price_krw": 299000,
    "monthly_price_usd": 23.92,
    "annual_price_usd": 239.20,
    "features": ["Basic analytics", "Up to 3 projects", "1 team member"],
    "max_projects": 3,
    "max_users": 1,
    "is_active": true
  },
  {
    "id": 2,
    "name": "Pro",
    "slug": "pro",
    "description": "Professional plan",
    "monthly_price_krw": 99900,
    "annual_price_krw": 999000,
    "monthly_price_usd": 79.92,
    "annual_price_usd": 799.20,
    "features": ["Advanced analytics", "Up to 10 projects", "5 team members"],
    "max_projects": 10,
    "max_users": 5,
    "is_active": true
  }
]
```

**Example:**
```bash
curl https://api.softfactory.com/api/payment/plans
```

---

### Create Subscription

```http
POST /subscribe
Authorization: Bearer {jwt_token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "plan_id": 1,
  "billing_period": "monthly",
  "stripe_token": "tok_visa"
}
```

**Field Descriptions:**
| Field | Type | Required | Options | Description |
|-------|------|----------|---------|-------------|
| plan_id | integer | Yes* | - | Subscription plan ID |
| plan_slug | string | Yes* | - | Plan slug (alternative to plan_id) |
| billing_period | string | No | monthly, annual | Default: monthly |
| stripe_token | string | No | - | Stripe payment method token |

*Either plan_id or plan_slug required

**Response (201 Created):**
```json
{
  "subscription_id": 789,
  "plan_name": "Starter",
  "next_billing_date": "2026-03-26T10:30:45.123456",
  "stripe_subscription_id": "sub_JiPO6mZv8zF5Xz",
  "amount_krw": 29900,
  "period": "monthly",
  "status": "active"
}
```

**Example:**
```bash
curl -X POST https://api.softfactory.com/api/payment/subscribe \
  -H "Authorization: Bearer {jwt_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "plan_id": 1,
    "billing_period": "monthly"
  }'
```

---

### Upgrade/Downgrade Subscription

```http
PUT /subscribe/{subscription_id}
Authorization: Bearer {jwt_token}
Content-Type: application/json
```

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| subscription_id | integer | Subscription ID |

**Request Body:**
```json
{
  "plan_id": 2,
  "billing_period": "monthly"
}
```

**Response (200 OK):**
```json
{
  "subscription_id": 789,
  "plan_name": "Pro",
  "next_billing_date": "2026-03-26T10:30:45.123456",
  "new_amount_krw": 99900,
  "old_amount_krw": 29900,
  "proration_credit_krw": 15000,
  "status": "active"
}
```

**Proration Details:**
- Credit calculated based on remaining days in billing period
- Applied to next invoice automatically
- Upgrade charges immediately, downgrade credits on next cycle

**Example:**
```bash
curl -X PUT https://api.softfactory.com/api/payment/subscribe/789 \
  -H "Authorization: Bearer {jwt_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "plan_id": 2,
    "billing_period": "monthly"
  }'
```

---

### Cancel Subscription

```http
DELETE /subscribe/{subscription_id}
Authorization: Bearer {jwt_token}
```

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| subscription_id | integer | Subscription ID |

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| cancel_at_end | boolean | false | Cancel at period end instead of immediately |

**Response (200 OK):**
```json
{
  "subscription_id": 789,
  "status": "canceled",
  "cancellation_date": "2026-02-26T10:30:45.123456",
  "refund_eligible": true,
  "refund_amount_krw": 29900,
  "message": "Subscription canceled immediately"
}
```

**Refund Policy:**
- Refunds available within 7 days of subscription creation
- Full refund amount if eligible
- Automatic refund processing through Stripe

**Examples:**

Immediate cancellation:
```bash
curl -X DELETE https://api.softfactory.com/api/payment/subscribe/789 \
  -H "Authorization: Bearer {jwt_token}"
```

Cancel at period end:
```bash
curl -X DELETE "https://api.softfactory.com/api/payment/subscribe/789?cancel_at_end=true" \
  -H "Authorization: Bearer {jwt_token}"
```

---

### Get Subscriptions

```http
GET /subscriptions
Authorization: Bearer {jwt_token}
```

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| status | string | - | Filter by status: active, canceled, expired |
| limit | integer | 50 | Max results (max 100) |
| offset | integer | 0 | Pagination offset |

**Response (200 OK):**
```json
{
  "total": 1,
  "limit": 50,
  "offset": 0,
  "subscriptions": [
    {
      "id": 789,
      "plan_name": "Pro",
      "plan_slug": "pro",
      "period": "monthly",
      "amount_krw": 99900,
      "status": "active",
      "started_date": "2026-02-26T10:30:45.123456",
      "next_billing_date": "2026-03-26T10:30:45.123456",
      "days_until_billing": 28,
      "refund_eligible": true,
      "refund_amount_krw": 99900
    }
  ]
}
```

**Example:**
```bash
curl "https://api.softfactory.com/api/payment/subscriptions?status=active&limit=10" \
  -H "Authorization: Bearer {jwt_token}"
```

---

## Webhook Handling

### Stripe Webhook Events

The system handles the following Stripe webhook events:

**customer.subscription.deleted**
- Marks subscription as canceled
- Disables access to plan features

**customer.subscription.updated**
- Updates billing period end date
- Syncs subscription state with Stripe

**invoice.payment_succeeded**
- Marks invoice as paid
- Records payment date

**invoice.payment_failed**
- Marks invoice as pending
- Triggers retry logic

---

## Error Handling

### Common Error Codes

| Status | Error Code | Description |
|--------|-----------|-------------|
| 400 | INVALID_AMOUNT | Amount is <= 0 |
| 400 | INVALID_PLAN | Plan not found or inactive |
| 400 | INVALID_CURRENCY | Unsupported currency pair |
| 401 | UNAUTHORIZED | Missing or invalid auth token |
| 403 | FORBIDDEN | User not authorized for resource |
| 404 | NOT_FOUND | Resource not found |
| 500 | STRIPE_ERROR | Stripe API error |

**Error Response Format:**
```json
{
  "error": "Detailed error message"
}
```

---

## Rate Limits

- **Unauthenticated endpoints**: 60 requests per minute
- **Authenticated endpoints**: 120 requests per minute
- **Stripe webhooks**: Unlimited (signature verified)

---

## Pricing Models

### Starter Plan (29,900 KRW/month)
- Basic analytics
- Up to 3 projects
- 1 team member
- Email support

### Pro Plan (99,900 KRW/month)
- Advanced analytics
- Up to 10 projects
- 5 team members
- Priority support

### Enterprise Plan (Contact sales)
- Unlimited projects
- Unlimited team members
- Dedicated support
- Custom integrations

---

## Integration Examples

### Python (requests)

```python
import requests

BASE_URL = "https://api.softfactory.com/api/payment"
TOKEN = "your_jwt_token"

# Create invoice
response = requests.post(
    f"{BASE_URL}/invoice",
    headers={"Authorization": f"Bearer {TOKEN}"},
    json={
        "amount_krw": 100000,
        "tax_rate": 0.10,
        "due_days": 30
    }
)
invoice = response.json()
print(f"Invoice created: {invoice['invoice_number']}")

# Subscribe to plan
response = requests.post(
    f"{BASE_URL}/subscribe",
    headers={"Authorization": f"Bearer {TOKEN}"},
    json={
        "plan_id": 1,
        "billing_period": "monthly"
    }
)
subscription = response.json()
print(f"Subscription created: {subscription['subscription_id']}")
```

### JavaScript (fetch)

```javascript
const TOKEN = 'your_jwt_token';
const BASE_URL = 'https://api.softfactory.com/api/payment';

// Create invoice
const invoiceResponse = await fetch(`${BASE_URL}/invoice`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${TOKEN}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    amount_krw: 100000,
    tax_rate: 0.10,
    due_days: 30
  })
});
const invoice = await invoiceResponse.json();
console.log(`Invoice: ${invoice.invoice_number}`);

// Get subscription plans
const plansResponse = await fetch(`${BASE_URL}/plans`);
const plans = await plansResponse.json();
console.log(`Available plans: ${plans.map(p => p.name).join(', ')}`);
```

---

## Best Practices

1. **Always include authorization header** for authenticated endpoints
2. **Use plan_slug** instead of plan_id for better portability
3. **Handle webhook signatures** for Stripe events
4. **Cache exchange rates** to reduce API calls
5. **Implement refund checks** before offering cancellation
6. **Store invoice PDFs** locally after download
7. **Use annual billing** for cost optimization (20% discount)
8. **Monitor subscription renewal** dates proactively

---

## Support & Documentation

- **API Status**: https://status.softfactory.com
- **Stripe Docs**: https://stripe.com/docs
- **Support Email**: support@softfactory.com

