# 🎯 5 Critical Tasks Per Team — Error Mitigation & Production Readiness

**Date:** 2026-02-26
**Status:** ✅ Validation Complete (40/40 checks) → Now Execute Fixes
**Token Strategy:** Minimal intervention, clear action items, parallel execution allowed

---

## 📋 Team A: OAuth & Social Login

**Team Character:** Security-focused, authentication experts, spec-first
**Current Status:** ✅ 5/5 checks pass
**Primary Skills:** JWT, OAuth 2.0, secure token handling, user model design

### 5 Critical Tasks

1. **Verify demo_token is actually used by frontend**
   - Check: `web/platform/login.html` actually sets `localStorage.access_token = 'demo_token'` after manual login
   - File: `web/platform/login.html` (line ~150)
   - Action: Grep for localStorage token assignment, confirm key name matches auth.py expectations
   - Why: Token handling mismatch between frontend and backend causes 401 errors
   - Estimated effort: 5 min (read + 1 line search)

2. **Test OAuth callback actually returns JWT**
   - Check: `/api/auth/oauth/{provider}/callback` actually returns `{access_token: "jwt_string"}`
   - File: `backend/auth.py` (oauth callback handler)
   - Action: Run `curl -X GET "http://localhost:8000/api/auth/oauth/google/callback?code=TEST_CODE"` and verify JSON response includes `access_token` field
   - Why: Frontend expects JWT token in response to store in localStorage
   - Estimated effort: 3 min (1 curl call)

3. **Verify User model oauth_id is actually unique** (database constraint)
   - Check: SQLAlchemy `unique=True` constraint on User.oauth_id is actually created in schema
   - File: `backend/models.py` (User model, oauth_id field)
   - Action: Run `sqlite3 platform.db "PRAGMA table_info(user);"` | grep oauth_id
   - Why: Duplicate oauth_id would cause "unique constraint failed" errors
   - Estimated effort: 2 min (1 SQL command)

4. **Confirm @require_auth decorator doesn't block demo_token**
   - Check: The `@require_auth` decorator in `backend/auth.py` accepts demo_token as valid
   - File: `backend/auth.py` (require_auth function)
   - Action: Grep for "demo_token" in auth.py, verify it's accepted without timestamp validation
   - Why: If decorator rejects demo_token, all protected endpoints return 401
   - Estimated effort: 2 min (grep + read 5 lines)

5. **Run real browser test: Login → See authenticated user**
   - Check: Browser -> http://localhost:8000/web/platform/login.html → click "Email Login" → see dashboard
   - Action: Manual test in browser or Puppeteer script (1 minute)
   - Why: Integration test catches token storage/auth flow issues tests don't catch
   - Estimated effort: 3 min (browser test)

---

## 📄 Team B: create.html & Direct Post Creation

**Team Character:** UX-focused, frontend engineers, integration specialists
**Current Status:** ✅ 5/5 checks pass
**Primary Skills:** HTML/CSS/JavaScript, DOM manipulation, form handling, localStorage

### 5 Critical Tasks

1. **Verify 3-mode tabs actually switch correctly**
   - Check: Clicking "Direct" vs "AI" vs "Automation" tabs actually shows/hides correct content
   - File: `web/sns-auto/create.html` (tab switching logic)
   - Action: Browser test or grep for tab event listeners, confirm DOM elements toggle correctly
   - Why: If tabs don't switch, users can't access AI or Automation modes
   - Estimated effort: 3 min (browser click test or grep)

2. **Test character counter updates in real-time**
   - Check: Typing in textarea → character count updates for each platform
   - File: `web/sns-auto/create.html` (character counter JavaScript)
   - Action: Type in textarea, observe counter updates (manual 1 min) or grep for keyup listener
   - Why: Wrong character count confuses users, may silently truncate posts
   - Estimated effort: 2 min (manual test)

3. **Verify localStorage.access_token is read correctly on page load**
   - Check: On page load, token is retrieved and used in API headers
   - File: `web/sns-auto/create.html` (top-level <script> section)
   - Action: Grep for "localStorage.getItem('access_token')" or "localStorage.getItem('token')" - confirm key name consistency with Team A
   - Why: Wrong key name = undefined token = 401 errors on all API calls
   - Estimated effort: 2 min (grep)

4. **Test media upload picker actually opens**
   - Check: Click "Upload Media" → file picker dialog appears
   - File: `web/sns-auto/create.html` (file input element)
   - Action: Manual browser test (click button) or grep for file input element, confirm it's not hidden
   - Why: If input is hidden or broken, users can't upload images
   - Estimated effort: 2 min (browser test)

5. **Confirm API call on "Publish" includes all required fields**
   - Check: When user clicks "Publish", POST to `/api/sns/posts` includes platform, content, media_ids
   - File: `web/sns-auto/create.html` (publish button handler)
   - Action: Grep for "fetch.*api/sns/posts" or "POST.*api/sns", inspect payload structure
   - Why: Missing fields cause 400 Bad Request errors from backend
   - Estimated effort: 3 min (grep + read 10 lines)

---

## 💰 Team C: Monetization Pages (Link-in-Bio, Monetize, Viral, Competitor)

**Team Character:** Revenue-focused, analytics specialists, data-driven
**Current Status:** ⚠️ 5/5 checks pass (1 medium warning: ApexCharts rendering)
**Primary Skills:** ApexCharts, analytics data binding, affiliate integration, metrics calculation

### 5 Critical Tasks

1. **Fix ApexCharts initialization with real data** (MEDIUM WARNING)
   - Check: Charts display correctly with live API data, not just placeholder
   - Files: `web/sns-auto/monetize.html`, `web/sns-auto/viral.html` (ApexCharts sections)
   - Action:
     * Test in browser with Chrome DevTools Network tab: Are API calls successful (200)?
     * If 200, but charts empty: Add `console.log(data)` before chart.render() to verify data structure
     * If data structure wrong: Update chart initialization to match API response format
   - Why: Charts may silently fail to render, looking like broken page
   - Estimated effort: 5 min (browser + 1 debug line)

2. **Verify Link-in-Bio CRUD endpoint exists and returns proper 200**
   - Check: `GET /api/sns/linkinbio` returns 200 with JSON array
   - Action: `curl -H "Authorization: Bearer demo_token" http://localhost:8000/api/sns/linkinbio`
   - Expected: `{"linkinbios": [...]}` or `[{...}]`
   - Why: If endpoint is 404, link-in-bio.html can't load any data
   - Estimated effort: 2 min (1 curl)

3. **Test "Create New Link-in-Bio" form submission**
   - Check: Form POST to `/api/sns/linkinbio` with {title, links, theme} actually succeeds (201)
   - File: `web/sns-auto/link-in-bio.html` (create form)
   - Action: Grep for "fetch.*POST.*linkinbio", check payload structure matches backend expectations
   - Why: If POST fails, users can't create new link-in-bio pages
   - Estimated effort: 3 min (grep + read)

4. **Verify trending endpoint returns sorted data**
   - Check: `GET /api/sns/trending?platform=instagram` returns most-trending first
   - Action: `curl -H "Authorization: Bearer demo_token" "http://localhost:8000/api/sns/trending?platform=instagram"` | jq '.data | .[0:2]'
   - Expected: First item has highest engagement_score or similar ranking metric
   - Why: If unsorted, "trending" content is not actually trending, user feature fails
   - Estimated effort: 2 min (curl + inspect)

5. **Test competitor tracking data persistence**
   - Check: After POST to `/api/sns/competitor`, can GET same competitor and see tracked data
   - Action:
     * POST competitor: `curl -X POST -H "Authorization: Bearer demo_token" -d '{"platform":"instagram","username":"test_user"}' http://localhost:8000/api/sns/competitor`
     * GET competitor: `curl -H "Authorization: Bearer demo_token" http://localhost:8000/api/sns/competitor?username=test_user`
   - Expected: 201 from POST, 200 from GET with tracked metrics
   - Why: Without persistence, competitor analysis is lost on page reload
   - Estimated effort: 3 min (2 curl calls)

---

## 🕷️ Team D: Review Scrapers & Background Jobs

**Team Character:** Infrastructure-focused, data engineers, reliability obsessed
**Current Status:** ✅ 5/5 checks pass
**Primary Skills:** Web scraping, BeautifulSoup, scheduling, error handling, pagination

### 5 Critical Tasks

1. **Verify APScheduler job is actually running every 60 seconds**
   - Check: Background scraper job executes, not stuck
   - Files: `backend/scheduler.py`, `backend/app.py` (scheduler initialization)
   - Action:
     * Check Flask logs: Look for "Scraping revu.net..." messages
     * Alternative: Add `print(f"[SCRAPE] {datetime.now()}")` to scraper and tail backend output
   - Why: If scheduler doesn't run, review data is never updated
   - Estimated effort: 3 min (log tail)

2. **Test `/api/review/scrape/now` endpoint returns JSON (not 404)**
   - Check: `POST /api/review/scrape/now` succeeds with 200, includes status
   - Action: `curl -X POST -H "Authorization: Bearer demo_token" http://localhost:8000/api/review/scrape/now`
   - Expected: `{"status": "started", "sources": 9}` or similar (not 404)
   - Why: If 404, UI can't trigger immediate scrapes
   - Estimated effort: 2 min (1 curl)

3. **Verify scraper HTML parsing doesn't crash silently**
   - Check: Scraper logs show parsing errors, not silent failures
   - Files: `backend/services/review_scrapers/*.py` (try/except blocks)
   - Action: Grep for `except` in scraper files, verify errors are logged not silently caught
   - Why: Silent failures = empty results with no indication of what broke
   - Estimated effort: 3 min (grep + read)

4. **Test pagination limit (5 pages max per scraper)**
   - Check: Scraper stops after 5 pages, doesn't run forever
   - Files: `backend/services/review_scrapers/revu_scraper.py` etc. (pagination logic)
   - Action: Grep for pagination loop, verify `max_pages=5` or `pages < 5` condition
   - Why: Without limit, scraper runs all night, consuming server resources
   - Estimated effort: 2 min (grep)

5. **Verify listing data is actually saved to database**
   - Check: After scrape completes, `SELECT COUNT(*) FROM review_listing;` returns > 0
   - Action: `sqlite3 platform.db "SELECT COUNT(*) FROM review_listing;"`
   - Expected: Number > 0 (not 0)
   - Why: If data isn't saved, listings never appear in UI
   - Estimated effort: 2 min (1 SQL query)

---

## 🔌 Team E: API Endpoints & Blueprint Registration

**Team Character:** API architects, backend specialists, standards-enforced
**Current Status:** ✅ 5/5 checks pass
**Primary Skills:** Flask blueprints, HTTP methods, route registration, error responses

### 5 Critical Tasks

1. **Test SNS routes are actually registered in Flask (not 404)**
   - Check: `GET /api/sns/campaigns` returns 200 (not 404), even with empty data
   - Action: `curl -H "Authorization: Bearer demo_token" http://localhost:8000/api/sns/campaigns`
   - Expected: 200 with JSON (e.g., `{"campaigns": []}` or `[]`)
   - Not expected: 404 "Not Found"
   - Why: This is the root cause of user's "APIs not working" - routes must be registered
   - Estimated effort: 2 min (1 curl)

2. **Test Review routes are actually registered in Flask (not 404)**
   - Check: `GET /api/review/aggregated` returns 200 (not 404)
   - Action: `curl -H "Authorization: Bearer demo_token" http://localhost:8000/api/review/aggregated`
   - Expected: 200 with JSON (e.g., `{"listings": []}`)
   - Why: Same as SNS - verify review routes work
   - Estimated effort: 2 min (1 curl)

3. **Verify @require_auth decorator is applied LAST (innermost) in decorator stack**
   - Check: Decorator order is `@bp.route()` → other decorators → `@require_auth` (BOTTOM)
   - Files: `backend/services/sns_auto.py`, `backend/services/review.py` (all route handlers)
   - Action: Grep for `@require_auth`, look at lines above it - should be route decorator first
   - Why: Wrong decorator order = 500 errors or incorrect auth behavior
   - Estimated effort: 3 min (grep + spot-check 3 routes)

4. **Test error responses are proper JSON with status codes**
   - Check: 404/500 errors return JSON (not HTML error page)
   - Action: `curl -I -H "Authorization: Bearer bad_token" http://localhost:8000/api/sns/campaigns` (expect 401)
   - Expected: Response headers include `Content-Type: application/json`
   - Why: Frontend expects JSON, HTML error pages break API client
   - Estimated effort: 2 min (1 curl -I)

5. **Verify all 12 blueprints are registered in app.py**
   - Check: `app.register_blueprint()` called for all 12 blueprints
   - File: `backend/app.py`
   - Action: Grep for "register_blueprint", count lines (should be ~12)
   - Why: Missing blueprint = all its routes are 404
   - Estimated effort: 2 min (grep + count)

---

## 📱 Team F: Review UI Pages (Aggregator, Applications, Accounts, Auto-Apply)

**Team Character:** UX/UI focused, data-driven interfaces, user empathy
**Current Status:** ✅ 5/5 checks pass
**Primary Skills:** HTML layout, data binding, status indicators, form UX

### 5 Critical Tasks

1. **Test aggregator.html actually loads listings from API**
   - Check: Page loads → API call to `/api/review/aggregated` succeeds → table shows data rows
   - Action: Browser: Open `http://localhost:8000/web/review/aggregator.html` → Open DevTools Network tab → look for `/api/review/aggregated` request (200 status)
   - Expected: Network shows 200 response, table has rows
   - Not expected: Network shows 404, table is empty
   - Why: This is the core feature - aggregator must show listings
   - Estimated effort: 3 min (browser test)

2. **Test application status updates (selected/rejected/pending)**
   - Check: UI correctly displays application status from API
   - File: `web/review/applications.html` (status display logic)
   - Action: Grep for status indicator (badge/label), confirm it's data-bound to API response field
   - Why: Wrong status display confuses users about which listings they applied to
   - Estimated effort: 2 min (grep)

3. **Verify "Add Account" button works in accounts.html**
   - Check: Click button → modal appears → form submits to POST `/api/review/accounts`
   - File: `web/review/accounts.html` (add account form)
   - Action: Browser test or grep for "fetch.*POST.*accounts"
   - Why: Without this, users can't add accounts to apply from
   - Estimated effort: 3 min (browser or grep)

4. **Test auto-apply rule creation (form → POST → rule appears in list)**
   - Check: Fill form → click "Save Rule" → rule appears in table below
   - File: `web/review/auto-apply.html` (form + POST handler)
   - Action: Grep for POST to `/api/review/auto-apply`, check if response updates UI or page refreshes
   - Why: Without feedback, user doesn't know if rule was saved
   - Estimated effort: 3 min (grep + read)

5. **Verify demo_token is sent in all API headers**
   - Check: Every fetch call includes `Authorization: Bearer demo_token`
   - Files: `web/review/aggregator.html`, `applications.html`, `accounts.html`, `auto-apply.html` (script sections)
   - Action: Grep for "fetch.*api/review" in all 4 files, check for "Authorization" header
   - Why: Missing token = 401 unauthorized = feature completely broken
   - Estimated effort: 3 min (grep 4 files)

---

## 🔐 Team G: SNS API Services (auto.py, linkinbio, ai generation, caching)

**Team Character:** Backend architects, performance-conscious, data consistency focused
**Current Status:** ✅ 5/5 checks pass
**Primary Skills:** Flask routing, database optimization, caching strategy, response formatting

### 5 Critical Tasks

1. **Verify `/api/sns/automate` POST endpoint returns automation rule ID**
   - Check: POST to `/api/sns/automate` with valid data returns 201 with rule ID
   - Action: `curl -X POST -H "Authorization: Bearer demo_token" -H "Content-Type: application/json" -d '{"topic":"fashion","platforms":["instagram"],"frequency":"daily"}' http://localhost:8000/api/sns/automate`
   - Expected: 201 with `{automation_id: 123, ...}`
   - Why: UI needs ID to later update/delete the rule
   - Estimated effort: 3 min (curl)

2. **Test `/api/sns/ai/generate` actually uses Claude API (or mock)**
   - Check: POST to endpoint returns generated content (not error)
   - Action: `curl -X POST -H "Authorization: Bearer demo_token" -d '{"topic":"travel"}' http://localhost:8000/api/sns/ai/generate`
   - Expected: 200 with `{content: "generated text here"}`
   - Why: If Claude API key missing, endpoint fails silently
   - Estimated effort: 3 min (curl)

3. **Verify Link-in-Bio stats endpoint returns valid click metrics**
   - Check: GET `/api/sns/linkinbio/stats?id=123` returns click_count and other metrics
   - Action: First create link-in-bio, get ID, then: `curl -H "Authorization: Bearer demo_token" "http://localhost:8000/api/sns/linkinbio/stats?id=123"`
   - Expected: 200 with `{click_count: 0, ...}` (at minimum)
   - Why: Without stats, monetization dashboard can't show ROI
   - Estimated effort: 3 min (2 curl calls)

4. **Test caching layer actually caches API responses (15-min TTL)**
   - Check: First call to endpoint takes 1s, second call takes <100ms (cached)
   - Files: `backend/services/sns_cache.py` (cache decorator)
   - Action:
     * Time first request: `time curl ... > /dev/null`
     * Time second request: `time curl ... > /dev/null`
     * Second should be much faster if cached
   - Why: Without caching, every request hits database, slowing platform
   - Estimated effort: 3 min (2 timed curl calls)

5. **Verify all SNS responses include proper HTTP status codes**
   - Check: Success = 200, Created = 201, Bad request = 400, Not found = 404, Server error = 500
   - Action: Test a few endpoints with valid, invalid, and missing data:
     * Valid: `curl -X GET ... ` → expect 200
     * Invalid auth: `curl -X GET -H "Authorization: Bearer bad" ... ` → expect 401
     * Missing required field: `curl -X POST -d '{}' ... ` → expect 400
   - Why: Frontend relies on status codes to show appropriate error messages
   - Estimated effort: 4 min (3-4 curl calls)

---

## 🔗 Team H: api.js - Client-Side API Integration

**Team Character:** Integration specialists, JavaScript experts, error handling specialists
**Current Status:** ✅ 5/5 checks pass
**Primary Skills:** Fetch API, async/await, error handling, request/response mapping

### 5 Critical Tasks

1. **Verify all 48 exported API functions have correct endpoint paths**
   - Check: Function paths match backend routes exactly (no typos)
   - File: `web/platform/api.js` (all export functions)
   - Action: Spot-check 5 critical functions:
     * `getListings()` → uses `/api/review/aggregated`? (Grep: "getListings")
     * `createPost()` → uses `/api/sns/posts`?
     * `createAutoApplyRule()` → uses `/api/review/auto-apply/rules`?
   - Why: Typo in path = 404 errors for that feature
   - Estimated effort: 3 min (grep + verify 5 paths)

2. **Test OAuth callback handler properly stores JWT token**
   - Check: `handleOAuthCallback(provider, code)` stores returned JWT in localStorage
   - File: `web/platform/api.js` (handleOAuthCallback function)
   - Action: Grep for `handleOAuthCallback`, check if response token is stored with correct key name
   - Why: Wrong key name = token lost = all subsequent API calls fail with 401
   - Estimated effort: 2 min (grep)

3. **Verify error responses are logged (not silently swallowed)**
   - Check: Failed API calls log error to console or return error object
   - File: `web/platform/api.js` (fetch .catch() blocks)
   - Action: Grep for `.catch(`, verify each contains `console.error()` or error return
   - Why: Silent errors = user doesn't know what failed
   - Estimated effort: 2 min (grep .catch)

4. **Test SNS posting flow: createPost() → publishPost(id)**
   - Check: Both functions work together (create returns ID, publish uses that ID)
   - File: `web/platform/api.js` (createPost and publishPost functions)
   - Action: Grep for both functions, verify return value flows to next function call
   - Why: If ID not returned, publish will fail with "undefined" error
   - Estimated effort: 3 min (grep + read)

5. **Verify demo_token is used as fallback if localStorage is empty**
   - Check: If user hasn't logged in yet, API calls use hardcoded demo_token
   - File: `web/platform/api.js` (token retrieval logic)
   - Action: Grep for "access_token", look for fallback to "demo_token" || "Bearer demo_token"
   - Why: Without fallback, unauthenticated users see immediate 401 errors
   - Estimated effort: 2 min (grep)

---

## 📊 Task Execution Summary

| Team | Task Count | Est. Time | Token Cost | Blocker Risk |
|------|-----------|-----------|-----------|-------------|
| A (OAuth) | 5 | 15 min | Low | Medium: demo_token not used |
| B (create.html) | 5 | 12 min | Low | Medium: localStorage key mismatch |
| C (Monetization) | 5 | 15 min | Low | Low (charts secondary) |
| D (Scrapers) | 5 | 12 min | Low | Medium: scraper not running |
| E (API) | 5 | 11 min | Low | **HIGH: Routes may be 404** |
| F (Review UI) | 5 | 14 min | Low | High: API endpoint 404 |
| G (SNS API) | 5 | 16 min | Low | **HIGH: Routes may be 404** |
| H (api.js) | 5 | 12 min | Low | Medium: endpoint path typos |
| **TOTAL** | **40** | **107 min** | **Very Low** | **See blockers below** |

---

## 🚨 Critical Path Issues (Address These First)

### **BLOCKER-1: SNS & Review APIs returning 404 (Teams E, G)**
**Why it's critical:** Without this, ALL downstream features fail

**Quick test:**
```bash
curl -H "Authorization: Bearer demo_token" http://localhost:8000/api/sns/campaigns
curl -H "Authorization: Bearer demo_token" http://localhost:8000/api/review/aggregated
```

If both return 404 → **This is the root issue**

**Root causes to check:**
1. Blueprint import failed in app.py (silent exception)
2. Route decorator syntax error
3. Blueprint not actually registered

**Fix strategy:**
- Team E: Run full import test: `python3 -c "from backend.app import create_app; app = create_app(); print([bp for bp in app.blueprints])"`
- If blueprints missing → check app.py imports for exceptions

### **BLOCKER-2: Token mismatch (Teams A, B, H)**
**Why it's critical:** Frontend can't authenticate → all API calls fail with 401

**Quick test:**
- Open browser console → run: `localStorage.getItem('access_token')` → should return 'demo_token'
- If undefined → localStorage key mismatch (Team B using wrong key name)

---

## ✅ Execution Protocol

**Phase 1 (Parallel - 5 min):**
- Team E runs quick 404 test (blocker check)
- Team A runs demo_token test (blocker check)
- All teams: Start reading their 5 tasks

**Phase 2 (Parallel - ~20 min):**
- Execute 5 tasks per team (curl tests, grep checks, browser tests)
- Log any failures with exact error message

**Phase 3 (Sequential - ~30 min):**
- Fix blockers first (E, A, B)
- Then all other issues
- Commit fixes with test verification

**Completion:** All 40 tasks ✓ → All APIs working → Production ready

---

**Generated:** 2026-02-26 | Strategy: Token-minimal, parallel-first, blocker-prioritized

