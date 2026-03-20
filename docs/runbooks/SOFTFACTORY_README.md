# 📝 SoftFactory Platform

> **Purpose**: **One Platform. Unlimited Services.**
> **Status**: 🟢 ACTIVE (관리 중)
> **Impact**: [Engineering / Operations]

---

## ⚡ Executive Summary (핵심 요약)
- **주요 내용**: 본 문서는 SoftFactory Platform 관련 핵심 명세 및 관리 포인트를 포함합니다.
- **상태**: 현재 최신화 완료 및 검토 됨.
- **연관 문서**: [Master Index](./NOTION_MASTER_INDEX.md)

---

**One Platform. Unlimited Services.**

A comprehensive SaaS platform built with Flask + SQLAlchemy, featuring three integrated services: CooCook (Chef Booking), SNS Auto (Social Media Automation), and Review Campaigns.

---

## ⚡ Quick Start

### Prerequisites
- Python 3.8+
- pip

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Run the platform
python start_platform.py
```

The platform will start on **http://localhost:8000**

---

## 🏗️ Architecture

```
SoftFactory Platform (Port 8000)
├── Platform Hub (Authentication, Billing, Dashboard)
├── CooCook Service (Chef Booking)
├── SNS Auto Service (Social Media Automation)
└── Review Campaign Service (Influencer Campaigns)
```

### Backend Structure
```
backend/
├── app.py              # Flask application factory
├── models.py           # SQLAlchemy models
├── auth.py             # JWT authentication
├── payment.py          # Stripe integration
├── platform.py         # Platform management
└── services/
    ├── coocook.py      # Chef booking endpoints
    ├── sns_auto.py     # SNS automation endpoints
    └── review.py       # Campaign management endpoints
```

### Frontend Structure
```
web/
├── platform/
│   ├── api.js          # Common API module
│   ├── index.html      # Landing page
│   ├── login.html      # Login form
│   ├── register.html   # Registration form
│   ├── dashboard.html  # Main dashboard
│   ├── billing.html    # Subscription management
│   └── admin.html      # Admin panel
├── coocook/
│   ├── index.html      # CooCook home
│   ├── explore.html    # Chef browsing
│   └── booking.html    # Booking form
├── sns-auto/
│   ├── index.html      # Account management
│   ├── create.html     # Create posts
│   └── schedule.html   # Scheduled posts
└── review/
    ├── index.html      # Campaign browsing
    ├── create.html     # Create campaign
    └── apply.html      # Apply to campaign
```

---

## 📋 API Endpoints

### Authentication
- `POST /api/auth/register` - Create account
- `POST /api/auth/login` - Login
- `POST /api/auth/refresh` - Refresh token
- `GET /api/auth/me` - Get current user

### Platform
- `GET /api/platform/products` - List services
- `GET /api/platform/dashboard` - User dashboard
- `GET /api/platform/admin/users` - List users (admin)
- `GET /api/platform/admin/revenue` - Revenue stats (admin)

### Payments
- `GET /api/payment/plans` - Pricing plans
- `POST /api/payment/checkout` - Create checkout
- `GET /api/payment/subscriptions` - User subscriptions
- `DELETE /api/payment/subscriptions/<id>` - Cancel subscription

### CooCook
- `GET /api/coocook/chefs` - List chefs
- `GET /api/coocook/chefs/<id>` - Chef details
- `POST /api/coocook/bookings` - Create booking
- `GET /api/coocook/bookings` - User bookings

### SNS Auto
- `GET /api/sns/accounts` - User accounts
- `POST /api/sns/accounts` - Link account
- `GET /api/sns/posts` - User posts
- `POST /api/sns/posts` - Create post
- `POST /api/sns/posts/<id>/publish` - Publish/schedule

### Review Campaigns
- `GET /api/review/campaigns` - List campaigns
- `POST /api/review/campaigns` - Create campaign
- `POST /api/review/campaigns/<id>/apply` - Apply to campaign
- `GET /api/review/my-applications` - User applications

---

## 👤 Demo Accounts

### Admin
- **Email:** `admin@softfactory.com`
- **Password:** `admin123`
- **Role:** Admin (full access + revenue dashboard)

### Regular User
- **Email:** `demo@softfactory.com`
- **Password:** `demo123`
- **Role:** User (standard access)

---

## 💾 Database

SQLite database (`platform.db`) is automatically created on first run with:
- 3 Product seeds (CooCook, SNS Auto, Review Campaign)
- 1 Admin account
- 1 Demo user
- 5 Sample chefs
- 3 Sample campaigns

---

## 🔐 Environment Variables

Required:
```env
PLATFORM_SECRET_KEY=your_secret_key
PLATFORM_URL=http://localhost:8000
```

Optional (for Stripe payments):
```env
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_test_...
```

---

## 🎯 Features

### Platform Hub
- User authentication (JWT)
- Service catalog and subscription management
- Multi-tenant architecture
- Admin revenue dashboard

### CooCook
- Browse local chefs by cuisine & location
- Book chef experiences with custom duration
- Real-time price calculation
- Chef profiles with ratings

### SNS Auto
- Connect multiple SNS accounts (Instagram, Blog, TikTok, YouTube)
- Create posts with templates
- Schedule posts for later
- Post management dashboard

### Review Campaigns
- Create review campaigns with rewards
- Browse active campaigns by category
- Apply as reviewer/influencer
- Campaign creator approval system

---

## 🚀 Adding New Services

Creating a 4th service takes ~10-30 minutes:

1. **Backend:** Create `backend/services/newservice.py`
   - Define endpoints with `@require_subscription('slug')`
   - Register blueprint in `app.py`

2. **Frontend:** Create `web/newservice/` folder
   - Add pages (index, detail, etc.)
   - Import `api.js` for API calls

3. **Models:** Add tables to `models.py`
   - Product seed in `init_db()`

4. **Done!** Service available to all users

---

## 🔗 URLs

| Page | URL |
|------|-----|
| Landing | http://localhost:8000/web/platform/index.html |
| Dashboard | http://localhost:8000/web/platform/dashboard.html |
| Billing | http://localhost:8000/web/platform/billing.html |
| Admin | http://localhost:8000/web/platform/admin.html |
| CooCook | http://localhost:8000/web/coocook/index.html |
| SNS Auto | http://localhost:8000/web/sns-auto/index.html |
| Campaigns | http://localhost:8000/web/review/index.html |

---

## 📊 Default Pricing

| Service | Monthly | Annual |
|---------|---------|--------|
| CooCook | $29 | $290 |
| SNS Auto | $49 | $490 |
| Review Campaign | $39 | $390 |

---

## ⚙️ Configuration

### CORS
Allowed origins:
- `http://localhost:5000` (JARVIS)
- `http://localhost:8000` (SoftFactory)
- `null` (browser extensions)

### Database
- Type: SQLite
- Location: `./platform.db`
- Auto-created on startup

### Payments
- Provider: Stripe (optional)
- Disabled in dev mode without keys
- Buttons visible but non-functional without credentials

---

## 📝 Notes

- All services run on port **8000** (separate from JARVIS on 5000)
- Subscriptions required for most features
- No API conflicts with existing JARVIS backend
- Each service is independently scalable
- SharedUser authentication across all services
- Single source of truth for models

---

## 🔧 Troubleshooting

### Port Already in Use
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# macOS/Linux
lsof -i :8000
kill -9 <PID>
```

### Database Locked
Delete `platform.db` and restart - new database will be created with seed data.

### Import Errors
```bash
pip install -r requirements.txt --upgrade
```

---

## 📞 Support

All services share common infrastructure:
- JWT auth from `backend/auth.py`
- Models from `backend/models.py`
- API calls via `web/platform/api.js`

---

**Built with ❤️ for SoftFactory**