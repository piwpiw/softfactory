# 📘 SoftFactory Demo Mode Guide

> **Purpose**: ```bash
> **Status**: 🟢 ACTIVE (관리 중)
> **Impact**: [Engineering / Operations]

---

## ⚡ Executive Summary (핵심 요약)
- **주요 내용**: 본 문서는 SoftFactory Demo Mode Guide 관련 핵심 명세 및 관리 포인트를 포함합니다.
- **상태**: 현재 최신화 완료 및 검토 됨.
- **연관 문서**: [Master Index](./NOTION_MASTER_INDEX.md)

---

## Quick Start

### 1. Start the Platform
```bash
python start_platform.py
```

### 2. Access Demo Mode
Visit: **http://localhost:8000/web/platform/login.html**

**Demo Passkey:** `demo2026`

Click "Enter Demo Mode" button - instant access, no credentials needed!

---

## Complete Feature Walkthrough

### Demo Mode Credentials
- **Passkey:** `demo2026`
- **Email (alternative):** `demo@softfactory.com`
- **Password (alternative):** `demo123`

### Real Login (if backend running)
- **Email:** `admin@softfactory.com`
- **Password:** `admin123`

---

## Service Features by Module

### 🍳 CooCook - Chef Booking Marketplace

**Pages:**
1. `/web/coocook/index.html` - Featured chefs & homepage
2. `/web/coocook/explore.html` - Chef search with filters (cuisine, location)
3. `/web/coocook/booking.html?chef_id=1` - Interactive booking

**Features:**
- Search 5 sample chefs (Korean, Italian, Japanese, French, Mexican)
- Filter by cuisine type and location
- View ratings and reviews
- Book experiences with date/duration selection
- Auto-calculate pricing
- View booking history

**Sample Data:**
- Chef Park (Korean, ₩120/session, 4.9★)
- Chef Marco (Italian, ₩130/session, 4.8★)
- Chef Tanaka (Japanese, ₩150/session, 4.9★)
- Chef Dubois (French, ₩140/session, 4.7★)
- Chef Garcia (Mexican, ₩110/session, 4.8★)

---

### 📱 SNS Auto - Social Media Automation

**Pages:**
1. `/web/sns-auto/index.html` - Connected accounts & recent posts
2. `/web/sns-auto/create.html` - 3-step wizard for creating posts
3. `/web/sns-auto/schedule.html` - Scheduled posts calendar

**Features:**
- Connect SNS accounts (Instagram, Blog, TikTok, YouTube Shorts)
- Create posts with templates (card news, blog, reel, shorts)
- Schedule posts for future publishing
- View publishing history
- Automatic scheduling

**Sample Data:**
- 2 connected accounts (Instagram @demo_user, Blog demo-blog)
- 4 post templates available
- 1 published post example

---

### ⭐ Review Campaign - Influencer & Brand Reviews

**Pages:**
1. `/web/review/index.html` - Browse campaigns by category
2. `/web/review/create.html` - Create new campaign
3. `/web/review/apply.html?campaign_id=1` - Apply to campaigns

**Features:**
- Browse campaigns by category (beauty, food, tech, fashion)
- Search and filter campaigns
- Apply to be a reviewer (with SNS link, follower count)
- View application status
- Campaign details (reward, deadline, requirements)

**Sample Data:**
- 3 active campaigns:
  1. GlowSkin Pro (Beauty, ₩150k reward, 5 applications)
  2. BeanBliss Coffee (Food, ₩50k reward, 3 applications)
  3. SmartHub X3 (Tech, ₩75k bonus, 8 applications)

---

### 🤖 AI Automation - 24/7 AI Employees

**Pages:**
1. `/web/ai-automation/index.html` - Plans, scenarios, employees dashboard
2. `/web/ai-automation/create.html` - Deploy new AI employee

**Features:**
- 3 subscription tiers (Starter ₩49k, Ambassador ₩89k, Enterprise ₩290k)
- Deploy AI employees for different scenarios
- 5 pre-built scenarios:
  - Email Response (15 hrs/month savings)
  - Social Media Posting (20 hrs/month)
  - Customer Support Bot (30 hrs/month)
  - Data Entry (25 hrs/month)
  - Meeting Scheduling (10 hrs/month)
- Track active employees and time savings
- Dashboard with statistics

**Sample Data:**
- 1 active AI employee (Email Bot)
- 15 hours monthly savings
- ₩1,800,000 annual savings estimate

---

### 💻 WebApp Builder - 8-Week Bootcamp

**Pages:**
1. `/web/webapp-builder/index.html` - Plans, courses, enrollments
2. `/web/webapp-builder/enroll.html` - Enrollment form
3. `/web/webapp-builder/create.html` - Create new webapp project

**Features:**
- 2 bootcamp plans (Weekday & Weekend, ₩590k each)
- 4-course curriculum:
  - Automation 1 (2 weeks, beginner)
  - Automation 2 (2 weeks, intermediate)
  - Automation 3 (2 weeks, intermediate)
  - WebApp Building (2 weeks, advanced)
- Track progress (0-100%)
- Monitor remaining days
- Manage webapp projects (draft → deployed)

**Sample Data:**
- Weekday plan: Mon-Fri 7-9pm (3 seats available)
- Weekend plan: Sat-Sun 10am-2pm (FULL)
- 1 active enrollment (25% progress, 56 days remaining)
- 1 webapp in development

---

## Complete User Journey

### Path 1: First-Time User
1. Visit `http://localhost:8000/web/platform/login.html`
2. Enter passkey `demo2026`
3. Redirected to dashboard
4. Click on service (e.g., CooCook)
5. Explore features

### Path 2: Browse Services
1. Visit `http://localhost:8000/web/platform/index.html`
2. See service overview with pricing
3. Click "Get Started" → Login page
4. Enter demo passkey
5. Access specific service

### Path 3: Complete Workflow Example (CooCook)
1. Login with passkey
2. Dashboard → Open CooCook
3. Explore chefs (use filters)
4. Click "Book Experience"
5. Select date, duration, requests
6. Confirm booking
7. View booking history

---

## API Response Format (Demo Mode)

All endpoints return realistic mock data matching production API format:

### CooCook
```javascript
GET /api/coocook/chefs → { chefs: [...], pages: 1 }
GET /api/coocook/chefs/1 → { id, name, bio, rating, rating_count, ... }
POST /api/coocook/bookings → { id, status, total_price, ... }
```

### SNS Auto
```javascript
GET /api/sns/accounts → { accounts: [...] }
GET /api/sns/posts → { posts: [...] }
GET /api/sns/templates → [{ id, name, type, ... }, ...]
```

### Review Campaign
```javascript
GET /api/review/campaigns → { campaigns: [...] }
POST /api/review/campaigns/:id/apply → { id, status, message }
```

### AI Automation
```javascript
GET /api/ai-automation/plans → { 'starter': {...}, 'ambassador': {...}, ... }
GET /api/ai-automation/employees → [{ id, name, status, ... }, ...]
GET /api/ai-automation/dashboard → { active_employees, total_monthly_savings_hours, ... }
```

### WebApp Builder
```javascript
GET /api/webapp-builder/plans → { 'weekday': {...}, 'weekend': {...} }
GET /api/webapp-builder/enrollments → [{ id, status, progress, ... }, ...]
GET /api/webapp-builder/webapps → [{ id, name, status, ... }, ...]
```

---

## Testing Checklist

### Authentication
- [ ] Enter wrong passkey → Error message
- [ ] Enter correct passkey → Dashboard loads
- [ ] Click Logout → Redirected to login
- [ ] Navigate to service → Works without re-login

### Navigation
- [ ] All service cards clickable from landing page
- [ ] Back buttons return to correct pages
- [ ] Dashboard shows all services
- [ ] Billing page accessible

### Services - CooCook
- [ ] Filter by cuisine type
- [ ] Filter by location
- [ ] Pagination works
- [ ] Book button → booking page
- [ ] Date selection working
- [ ] Price calculation correct

### Services - SNS Auto
- [ ] View connected accounts
- [ ] Create post with template
- [ ] Schedule post for future
- [ ] Publish button works
- [ ] View post history

### Services - Review Campaign
- [ ] Browse campaigns
- [ ] Filter by category
- [ ] View campaign details
- [ ] Apply to campaign
- [ ] View applications

### Services - AI Automation
- [ ] View subscription plans
- [ ] View available scenarios
- [ ] Deploy new AI employee
- [ ] View dashboard stats
- [ ] Track savings

### Services - WebApp Builder
- [ ] View bootcamp plans
- [ ] View course curriculum
- [ ] Enroll in bootcamp
- [ ] Create new webapp
- [ ] Track progress

### UI/UX
- [ ] All pages responsive (mobile, tablet, desktop)
- [ ] Toast notifications appear
- [ ] Forms validate input
- [ ] Links have proper styling
- [ ] Navigation bar consistent

---

## Troubleshooting

### "Backend not running" Error
**Solution:** Start the backend
```bash
python start_platform.py
```

### Pages show "Not Found" (404)
**Solution:** Verify file paths are correct
- Pages should be in `/web/service/` folders
- Check that all HTML files exist

### Demo mode not activating
**Solution:** Ensure passkey is exactly `demo2026`
- Check localStorage: `localStorage.getItem('demo_mode')`
- Clear browser cache if needed

### Navigation not working
**Solution:** Check that links use correct relative paths
- Service pages: `../../platform/api.js`
- Platform pages: `api.js`

### No data showing in tables
**Solution:** Check browser console for errors
- Open DevTools (F12)
- Check Console tab for API errors
- Verify apiFetch function is called

---

## Demo Mode Technical Details

### How Demo Mode Works
1. **Passkey Entry:** `demo2026` triggers `enableDemoMode()`
2. **Mock Storage:** localStorage stores demo tokens
3. **API Interception:** `apiFetch()` detects demo mode
4. **Mock Responses:** Returns pre-generated data
5. **Network Simulation:** 300ms delay for realism

### Mock Data Generation
- `generateMockData(path, options)` creates responses
- Format matches real API exactly
- Realistic sample sizes (2-5 items per list)
- Complete object structures with all properties

### Limitations
- Changes not persisted (refresh = reset)
- No actual booking/subscription
- No backend synchronization
- Network requests are instant (after 300ms delay)

---

## Next Steps

### To Connect Real Backend
1. Ensure Flask server running on port 8000
2. Toggle `isDemoMode()` off
3. Login with real credentials
4. All API calls forward to real backend

### To Add More Demo Data
Edit `generateMockData()` in `/web/platform/api.js`:
```javascript
if (path === '/api/your-endpoint') {
    return { data: [...your-mock-data...] };
}
```

### To Customize Demo
- Edit passkey: Change `DEMO_PASSKEY` in api.js
- Edit user: Modify `DEMO_USER` object
- Edit data: Update sample arrays in mock functions

---

## Support

For issues or questions:
1. Check browser console (F12)
2. Verify all files are in correct locations
3. Check that demo passkey is correct
4. Review this guide for common solutions

---

**Demo Mode Enabled!** 🚀
All SoftFactory services ready for testing.