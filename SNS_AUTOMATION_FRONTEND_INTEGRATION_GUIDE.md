# 📘 SNS Automation v2.0 - Frontend Integration Guide

> **Purpose**: 1. [Quick Start](#quick-start)
> **Status**: 🟢 ACTIVE (관리 중)
> **Impact**: [Engineering / Operations]

---

## ⚡ Executive Summary (핵심 요약)
- **주요 내용**: 본 문서는 SNS Automation v2.0 - Frontend Integration Guide 관련 핵심 명세 및 관리 포인트를 포함합니다.
- **상태**: 현재 최신화 완료 및 검토 됨.
- **연관 문서**: [Master Index](./NOTION_MASTER_INDEX.md)

---

> **Complete setup & deployment instructions for 4 SNS Automation frontend pages**
> **Version:** 1.0 | **Date:** 2026-02-26

---

## Table of Contents
1. [Quick Start](#quick-start)
2. [File Structure](#file-structure)
3. [Installation & Setup](#installation--setup)
4. [Feature Integration](#feature-integration)
5. [API Endpoints](#api-endpoints)
6. [Deployment Checklist](#deployment-checklist)
7. [Troubleshooting](#troubleshooting)

---

## Quick Start

### Prerequisites
- Modern web browser (Chrome 90+, Firefox 88+, Safari 14+)
- Backend API server running on `http://localhost:8000`
- Node.js 18+ (for local development only)

### Installation (1 minute)
```bash
# 1. Navigate to project
cd D:/Project

# 2. Files already exist - no installation needed!
# The 4 pages are in: web/sns-auto/

# 3. Start backend server
python backend/app.py
# Server runs on http://localhost:8000

# 4. Access frontend
# http://localhost:8000/web/sns-auto/index.html
# http://localhost:8000/web/sns-auto/link-in-bio.html
# http://localhost:8000/web/sns-auto/monetize.html
# http://localhost:8000/web/sns-auto/viral.html
# http://localhost:8000/web/sns-auto/competitor.html
```

---

## File Structure

### Core Pages (4 Required)
```
D:/Project/web/sns-auto/
├── link-in-bio.html          (242 lines) — Link management + bio builder
├── monetize.html              (294 lines) — Revenue dashboard + affiliates
├── viral.html                 (300 lines) — Trending hashtags + viral tips
├── competitor.html            (424 lines) — Competitor analysis + tracking
│
├── [Supporting Pages]
├── index.html                 (Dashboard overview)
├── create.html                (Post composition)
├── analytics.html             (Performance metrics)
├── accounts.html              (SNS account management)
├── inbox.html                 (Messages center)
├── campaigns.html             (Campaign management)
├── schedule.html              (Post scheduling)
├── templates.html             (Content templates)
└── settings.html              (User preferences)
```

### New Enhancement Modules (Add These)
```
D:/Project/web/sns-auto/
├── qr-code-generator.js       (NEW) — QR code generation utility
├── pdf-export.js              (NEW) — PDF export functionality
└── analytics-advanced.js       (NEW) — Advanced charting & analytics
```

### Shared Resources
```
D:/Project/web/
├── platform/
│   ├── api.js                 (932 lines) — API client module
│   └── responsive-framework.css
├── responsive-framework.css
└── mobile-optimization.js
```

---

## Installation & Setup

### Step 1: Verify Backend API
```bash
# Check if backend is running
curl http://localhost:8000/api/health

# Expected response: { "status": "ok", "version": "2.0" }
```

### Step 2: Test Frontend Access
```bash
# Open in browser
http://localhost:8000/web/sns-auto/link-in-bio.html

# Expected: Page loads, shows authentication requirement
# Click "Demo Mode" or provide valid credentials
```

### Step 3: Enable Demo Mode (Testing Only)
```javascript
// In browser console, enable demo mode:
localStorage.setItem('demo_mode', 'true');
enableDemoMode();
location.reload();

// This disables authentication & loads mock data
```

### Step 4: Add Enhancement Libraries (Optional)

#### For QR Code Generation
```html
<!-- Add to <head> of link-in-bio.html -->
<script src="https://cdnjs.cloudflare.com/ajax/libs/qrcode.js/1.5.3/qrcode.min.js"></script>
<script src="../sns-auto/qr-code-generator.js"></script>
```

#### For PDF Export
```html
<!-- Add to <head> of monetize.html, viral.html, competitor.html -->
<script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
<script src="../sns-auto/pdf-export.js"></script>
```

---

## Feature Integration

### Page 1: Link-in-Bio Builder

**Location:** `/web/sns-auto/link-in-bio.html`

#### Features
- ✅ Link CRUD (Create, Read, Update, Delete)
- ✅ Theme selection (Purple, Blue, Pink, Green)
- ✅ Real-time preview
- ✅ Click statistics
- ⏳ QR code generation (add via qr-code-generator.js)

#### API Endpoint
```javascript
// POST /api/sns/linkinbio
await apiFetch('/api/sns/linkinbio', {
    method: 'POST',
    body: JSON.stringify({
        title: "내 링크 모음",
        description: "설명",
        theme: "pink",
        links: [
            { title: "블로그", url: "https://...", clicks: 1250, created: "..." }
        ],
        totalClicks: 1250
    })
});
```

#### Usage Example
```html
<!-- Link in Bio Page -->
<script src="../platform/api.js"></script>
<script src="./qr-code-generator.js"></script>

<script>
// Generate QR code for bio link
const slug = generateBioSlug('myusername', '내 링크 모음');
const bioURL = createBioLinkURL(slug);
generateQRCode(bioURL, 'qr-preview-container', 256);

// Download QR code
function downloadBioQR() {
    downloadQRCode('my-linkinbio', 'png');
}
</script>
```

---

### Page 2: 수익화 대시보드

**Location:** `/web/sns-auto/monetize.html`

#### Features
- ✅ ROI calculator
- ✅ Revenue trend chart (ApexCharts)
- ✅ Affiliate program management (Amazon, CJ, Google AdSense)
- ✅ Top revenue sources
- ⏳ PDF export (add via pdf-export.js)

#### API Endpoints
```javascript
// GET /api/sns/roi
// Returns: { revenue, roi_percent, channels, trends }

// POST /api/sns/ai/repurpose
// Returns: { repurposed_content, suggestions }
```

#### Usage Example
```html
<!-- Monetization Dashboard -->
<script src="../platform/api.js"></script>
<script src="https://cdn.jsdelivr.net/npm/apexcharts"></script>
<script src="./pdf-export.js"></script>

<script>
// Export revenue report as PDF
async function exportReport() {
    await exportMonetizationReport('my-revenue-report');
}

// Button to trigger
<button onclick="exportReport()" class="px-4 py-2 bg-green-600 rounded">
    📥 PDF 다운로드
</button>
</script>
```

---

### Page 3: 바이럴 콘텐츠 발견

**Location:** `/web/sns-auto/viral.html`

#### Features
- ✅ Trending hashtags (platform-specific)
- ✅ Content type recommendations
- ✅ Viral checklist with progress tracking
- ✅ Real-time trend refresh
- ⏳ CSV export
- ⏳ WebSocket for live updates

#### API Endpoint
```javascript
// GET /api/sns/trending
// Returns: { hashtags: [], topics: [], predictions: [] }
```

#### Usage Example
```html
<!-- Viral Content Page -->
<script src="../platform/api.js"></script>

<script>
// Refresh trending data from API
async function refreshTrends() {
    try {
        const response = await apiFetch('/api/sns/trending');
        updateHashtagDisplay(response.hashtags);
        showSuccess('트렌드 업데이트됨!');
    } catch (error) {
        showError('트렌드 업데이트 실패');
    }
}

// Use hashtag in new post
function useHashtag(hashtag) {
    window.location.href = `create.html?hashtag=${encodeURIComponent(hashtag)}`;
}

// Copy hashtag to clipboard
function copyHashtag(hashtag) {
    navigator.clipboard.writeText(hashtag);
    showSuccess(`${hashtag} 복사됨`);
}
</script>
```

---

### Page 4: 경쟁사 분석

**Location:** `/web/sns-auto/competitor.html`

#### Features
- ✅ Add competitor accounts (by username/URL)
- ✅ Follower tracking with growth trends
- ✅ Post comparison (engagement, frequency)
- ✅ Content type analysis
- ✅ Competitive benchmarking
- ⏳ PDF export (add via pdf-export.js)

#### API Endpoints
```javascript
// POST /api/sns/competitor
// Body: { username: "fashion_guru", platform: "instagram" }
// Returns: { competitor_data: {...} }

// GET /api/sns/competitor
// Returns: { competitors: [{...}, {...}] }
```

#### Usage Example
```html
<!-- Competitor Analysis Page -->
<script src="../platform/api.js"></script>
<script src="./pdf-export.js"></script>

<script>
// Add new competitor
async function addCompetitor() {
    const username = prompt('경쟁사 사용자명 입력:');
    if (!username) return;

    try {
        const response = await apiFetch('/api/sns/competitor', {
            method: 'POST',
            body: JSON.stringify({ username })
        });
        updateCompetitorList(response.competitor_data);
        showSuccess(`@${username} 추가됨!`);
    } catch (error) {
        showError('추가 실패: ' + error.message);
    }
}

// Export analysis as PDF
async function exportAnalysis() {
    await exportCompetitorAnalysis('competitor-analysis-feb2026');
}
</script>
```

---

## API Endpoints

### Summary Table

| Feature | Method | Endpoint | Status |
|---------|--------|----------|--------|
| Get Link in Bio | GET | `/api/sns/linkinbio` | ✅ Ready |
| Create Link in Bio | POST | `/api/sns/linkinbio` | ✅ Ready |
| Get Bio Stats | GET | `/api/sns/linkinbio/stats` | ✅ Ready |
| Get ROI Data | GET | `/api/sns/roi` | ✅ Ready |
| AI Repurpose | POST | `/api/sns/ai/repurpose` | ✅ Ready |
| Get Trending | GET | `/api/sns/trending` | ✅ Ready |
| Add Competitor | POST | `/api/sns/competitor` | ✅ Ready |
| Get Competitors | GET | `/api/sns/competitor` | ✅ Ready |
| Update Tracking | PUT | `/api/sns/competitor/{id}` | ✅ Ready |

### Complete Endpoint Specifications

#### `/api/sns/linkinbio` (POST)
```
Request:
{
    "title": "내 링크 모음",
    "description": "설명",
    "theme": "pink",
    "links": [
        {
            "title": "블로그",
            "url": "https://blog.example.com",
            "clicks": 100,
            "created": "2026-02-26T00:00:00Z"
        }
    ],
    "totalClicks": 100
}

Response:
{
    "id": 1,
    "slug": "my-linkinbio-123abc",
    "url": "/bio/my-linkinbio-123abc",
    "qr_code": "data:image/png;base64,...",
    "created": "2026-02-26T00:00:00Z",
    "message": "Link in Bio saved successfully"
}
```

#### `/api/sns/trending` (GET)
```
Response:
{
    "hashtags": [
        {
            "tag": "#트렌드",
            "growth": 45,
            "posts": "1.2M",
            "platform": "Instagram",
            "updated": "2026-02-26T12:00:00Z"
        }
    ],
    "topics": [
        {
            "name": "쇼츠",
            "engagement": "15-20%",
            "category": "video"
        }
    ],
    "predictions": [...]
}
```

#### `/api/sns/competitor` (POST)
```
Request:
{
    "username": "fashion_guru",
    "platform": "instagram"
}

Response:
{
    "id": 1,
    "username": "fashion_guru",
    "platform": "instagram",
    "followers": 245000,
    "follower_growth": 2.3,
    "engagement": 8.5,
    "weekly_posts": 12,
    "top_post_likes": 42000,
    "content_types": ["코디", "뷰티"],
    "tracked_since": "2026-02-26T00:00:00Z",
    "message": "Competitor added successfully"
}
```

---

## Deployment Checklist

### Pre-Deployment (1-2 hours)

- [ ] **Code Review**
  - [ ] Run `npm run lint` (if webpack configured)
  - [ ] Validate HTML syntax
  - [ ] Check for console errors in DevTools
  - [ ] Verify no hardcoded API URLs

- [ ] **Testing**
  - [ ] Test on Chrome, Firefox, Safari
  - [ ] Test on iPhone and Android
  - [ ] Test network throttling (slow 3G)
  - [ ] Test with demo mode enabled
  - [ ] Test all button interactions

- [ ] **Assets**
  - [ ] Verify all images load
  - [ ] Verify Tailwind CSS loads
  - [ ] Verify ApexCharts loads
  - [ ] Verify api.js loads
  - [ ] Check for 404 errors in DevTools Network tab

- [ ] **Performance**
  - [ ] Run Lighthouse audit (target: 90+ score)
  - [ ] Check page load time (target: < 2s)
  - [ ] Check First Contentful Paint (target: < 1s)
  - [ ] Check Largest Contentful Paint (target: < 2.5s)

### Deployment (1 hour)

- [ ] **Setup**
  - [ ] Copy all HTML files to `D:/Project/web/sns-auto/`
  - [ ] Copy new JS modules (qr-code-generator.js, pdf-export.js)
  - [ ] Update navigation links in all pages
  - [ ] Verify symlinks/references work

- [ ] **Backend Integration**
  - [ ] Verify all 32 API endpoints are implemented
  - [ ] Test API response times (target: < 500ms)
  - [ ] Test error handling (404, 500, timeout)
  - [ ] Verify CORS headers are set correctly

- [ ] **Deployment**
  - [ ] Deploy to staging environment
  - [ ] Run smoke tests
  - [ ] Deploy to production
  - [ ] Verify pages accessible via public URL

### Post-Deployment (ongoing)

- [ ] **Monitoring**
  - [ ] Set up error tracking (Sentry/Bugsnag)
  - [ ] Monitor API error rates
  - [ ] Monitor page performance (Datadog/New Relic)
  - [ ] Check user analytics (Google Analytics)

- [ ] **User Feedback**
  - [ ] Send feedback survey to beta users
  - [ ] Collect feature requests
  - [ ] Monitor support tickets
  - [ ] Plan Phase 2 improvements

- [ ] **Maintenance**
  - [ ] Update libraries (Tailwind, ApexCharts, etc.)
  - [ ] Fix reported bugs within 24 hours
  - [ ] Optimize based on analytics
  - [ ] Document lessons learned

---

## Troubleshooting

### Common Issues

#### 1. Pages Load but Show "Authentication Required"
**Problem:** Pages redirect to login even with demo credentials
**Solution:**
```javascript
// In browser console:
localStorage.setItem('demo_mode', 'true');
localStorage.setItem('access_token', 'demo_token');
location.reload();
```

#### 2. Charts Not Rendering (ApexCharts)
**Problem:** Black box where chart should be
**Cause:** ApexCharts library not loading
**Solution:**
```html
<!-- Verify CDN link in HTML -->
<script src="https://cdn.jsdelivr.net/npm/apexcharts"></script>

<!-- If still failing, use local copy -->
<script src="/vendor/apexcharts.min.js"></script>
```

#### 3. API Calls Returning 404
**Problem:** "POST /api/sns/linkinbio returned 404"
**Cause:** Backend not running or endpoint not implemented
**Solution:**
```bash
# Check if backend is running
curl http://localhost:8000/api/health

# Verify endpoint exists in backend/services/sns_auto.py
# Restart backend if needed
python backend/app.py
```

#### 4. Dark Mode Not Working
**Problem:** Pages show light theme instead of dark
**Cause:** Tailwind not loading or wrong color classes
**Solution:**
```html
<!-- Add dark mode meta tag to <head> -->
<meta name="color-scheme" content="dark">

<!-- Verify Tailwind CDN -->
<script src="https://cdn.tailwindcss.com"></script>

<!-- Force dark mode -->
<body class="bg-slate-950 text-slate-100">
```

#### 5. Mobile Layout Broken
**Problem:** Pages don't resize properly on mobile
**Cause:** Viewport meta tag missing
**Solution:**
```html
<!-- Verify in <head> -->
<meta name="viewport" content="width=device-width, initial-scale=1.0">
```

#### 6. QR Code Not Generating
**Problem:** "QR code generation failed" error
**Solution:**
```html
<!-- Add QR code library -->
<script src="https://cdnjs.cloudflare.com/ajax/libs/qrcode.js/1.5.3/qrcode.min.js"></script>

<!-- Call with container ID -->
<div id="qr-container"></div>
<script>
generateQRCode('https://example.com', 'qr-container');
</script>
```

#### 7. PDF Export Not Working
**Problem:** "PDF generation failed" or button does nothing
**Solution:**
```html
<!-- Verify PDF libraries loaded -->
<script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
<script src="./pdf-export.js"></script>

<!-- Call function -->
<button onclick="exportMonetizationReport()">PDF 내보내기</button>
```

### Debug Mode

Enable console logging for debugging:
```javascript
// Set in browser console or add to HTML head
localStorage.setItem('debug', 'true');

// All API calls will log to console
// Check DevTools Console tab for detailed logs
```

### Performance Issues

If pages load slowly:

```javascript
// Check what's slow
console.time('page-load');
// ... page loads ...
console.timeEnd('page-load');

// Check API response times
const start = Date.now();
await apiFetch('/api/sns/trending');
console.log(`API took ${Date.now() - start}ms`);

// Reduce chart complexity
// - Limit data points to last 30 days
// - Use simpler chart types
// - Lazy load charts on scroll
```

---

## Support & Documentation

### Quick Links
- **API Documentation:** `backend/SNS_PRD_v2.md`
- **Architecture:** `orchestrator/README.md`
- **Patterns & Pitfalls:** `shared-intelligence/patterns.md`
- **Code Examples:** `web/sns-auto/index.html` (dashboard)

### Contact
- **Issues:** Post in issue tracker
- **Questions:** Check FAQ section below
- **Feature Requests:** Submit in roadmap document

### FAQ

**Q: Can I use these pages in production?**
A: Yes! All 4 pages are production-ready. Follow deployment checklist first.

**Q: How do I customize the theme colors?**
A: Modify Tailwind color classes. E.g., change `bg-slate-950` to `bg-gray-900`

**Q: Can I use these without the backend?**
A: Partially. Demo mode provides mock data for testing UI/UX.

**Q: How do I add more features?**
A: See Phase 2 recommendations in review document.

**Q: Where's the source code?**
A: All source in `/web/sns-auto/*.html`. JavaScript inline for simplicity.

---

## Next Steps

1. ✅ **Deploy Pages** — Follow deployment checklist
2. ⏳ **Gather Feedback** — Run user testing
3. ⏳ **Plan Phase 2** — QR codes, PDF export, WebSocket
4. ⏳ **Optimize Performance** — Monitor Lighthouse scores
5. ⏳ **Scale Backend** — Upgrade to production DB, caching

---

**Created:** 2026-02-26
**Status:** PRODUCTION-READY
**Last Updated:** 2026-02-26