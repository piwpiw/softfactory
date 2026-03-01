# SoftFactory PWA - Test Verification Checklist
> Step-by-step testing guide for PWA implementation

**Created:** 2026-02-26
**Version:** 1.0
**Time Required:** 15-20 minutes

---

## 🎯 Pre-Test Setup

### Environment Verification
- [ ] Files generated: `node /d/Project/web/generate-icons.js`
- [ ] Platform running: `python start_platform.py`
- [ ] Browser: Chrome, Firefox, Safari, or Edge
- [ ] DevTools available: F12 shortcut works
- [ ] No browser extensions blocking SW

---

## ✅ Test 1: Manifest Validation (2 minutes)

### Steps:
1. Open http://localhost:8000
2. Open DevTools (F12)
3. Go to **Application** tab
4. Click **Manifest** in sidebar

### Verify:
- [ ] Status shows "No issues"
- [ ] name: "SoftFactory"
- [ ] short_name: "SoftFactory"
- [ ] start_url: "/web/platform/index.html"
- [ ] display: "standalone"
- [ ] theme_color: "#1e293b"
- [ ] background_color: "#ffffff"
- [ ] icons array has 4+ icons
- [ ] scope: "/"

### Expected Output:
```json
{
  "name": "SoftFactory",
  "display": "standalone",
  "start_url": "/web/platform/index.html",
  "scope": "/",
  "theme_color": "#1e293b",
  "background_color": "#ffffff"
}
```

---

## ✅ Test 2: Service Worker Registration (3 minutes)

### Steps:
1. Open http://localhost:8000
2. Open DevTools (F12)
3. Go to **Application** tab
4. Click **Service Workers** in sidebar

### Verify:
- [ ] Service Worker shows in list
- [ ] Status: "activated and running"
- [ ] URL: `/web/service-worker.js`
- [ ] "Unregister" button available (means it's active)
- [ ] "Updated on" shows recent timestamp

### Optional Actions:
- [ ] Click "Update on reload" to check for updates
- [ ] Check "Update on reload" checkbox for next test
- [ ] Refresh page - SW should update silently

### Expected Output:
```
Service Worker
/web/service-worker.js
Status: activated and running
Online
Clients: 1
```

---

## ✅ Test 3: Cache Storage (3 minutes)

### Steps:
1. Open http://localhost:8000
2. Open DevTools (F12)
3. Go to **Application** tab
4. Click **Cache Storage** in sidebar
5. Expand cache storage tree

### Verify:
- [ ] softfactory-static-v1 exists
- [ ] softfactory-dynamic-v1 exists
- [ ] softfactory-api-v1 exists
- [ ] softfactory-images-v1 exists

### For Each Cache:
1. Click cache name to expand
2. Verify entries are cached:
   - [ ] **static** has JS/CSS files
   - [ ] **dynamic** has HTML pages
   - [ ] **api** has API responses
   - [ ] **images** has image files

### Example Cache Contents:
```
softfactory-static-v1/
├─ /web/platform/api.js
├─ /web/platform/pwa-installer.js
├─ https://cdn.tailwindcss.com
├─ https://cdn.jsdelivr.net/...
└─ ...

softfactory-dynamic-v1/
├─ /web/platform/index.html
├─ /web/offline.html
└─ ...
```

---

## ✅ Test 4: Offline Mode - DevTools (4 minutes)

### Steps:
1. Open http://localhost:8000
2. Open DevTools (F12)
3. Go to **Network** tab
4. Check "Offline" checkbox
5. Refresh page (Ctrl+R)

### Verify:
- [ ] Page loads without errors
- [ ] No network requests shown (all from cache)
- [ ] Content displays correctly
- [ ] No 404 or failed requests

### Check Console:
1. Go to **Console** tab
2. Verify no errors (only warnings OK)

### Expected Behavior:
- Page loads instantly from cache
- All UI elements visible
- No red X on images (cached or working)

---

## ✅ Test 5: Offline Mode - Real Network (3 minutes)

### Alternative to Test 4 (Real-world test):
1. Disable WiFi/mobile data
2. Open new tab
3. Go to http://localhost:8000
4. Page should load from cache

### Verify:
- [ ] Page loads without internet
- [ ] Can navigate between cached pages
- [ ] Offline.html shows for uncached pages

### After Test:
- Re-enable WiFi/data

---

## ✅ Test 6: Offline Page (2 minutes)

### Steps:
1. Open http://localhost:8000
2. Open DevTools → Network tab
3. Check "Offline" checkbox
4. Navigate to page NOT in cache:
   - Try: http://localhost:8000/web/nonexistent.html
5. **OR** click link to uncached page

### Verify:
- [ ] Offline page shows
- [ ] Displays "오프라인 상태입니다" (Offline)
- [ ] Shows connectivity indicator
- [ ] Lists cached pages (Dashboard, Analytics, etc.)
- [ ] Retry button present
- [ ] Troubleshooting tips visible

### Test Retry Button:
1. Still offline in DevTools
2. Click "연결 다시 시도" (Retry)
3. Should say "확인 중..." (Checking)
4. Then return to "연결 다시 시도" (still offline)

---

## ✅ Test 7: Back Online Auto-Redirect (2 minutes)

### Steps:
1. Open http://localhost:8000
2. Go offline (DevTools or Network)
3. Navigate to offline page
4. Go back ONLINE:
   - Uncheck DevTools Offline checkbox
   - **OR** Re-enable WiFi/data
5. Watch page

### Verify:
- [ ] Status changes to "네트워크 연결됨" (Connected)
- [ ] Auto-redirects to previous page after 1-2 seconds
- [ ] Navigation is seamless

---

## ✅ Test 8: Installation Prompt (3 minutes)

### Desktop (Chrome/Edge):
1. Open http://localhost:8000
2. Wait 30 seconds
3. Look for install prompt

### If Prompt Appears:
- [ ] Click "Install"
- [ ] App installs to taskbar/dock
- [ ] Opens in standalone window
- [ ] No address bar visible

### If No Prompt:
Check DevTools:
1. Go to **Application** → **Manifest**
2. Click "Add to Home Screen" button
3. Should show install dialog

### Verify Installed App:
- [ ] Opens in app window (not browser)
- [ ] Has app icon on taskbar
- [ ] Theme colors match (dark blue)

---

## ✅ Test 9: Mobile Installation (3 minutes, optional)

### Android Chrome:
1. Open http://localhost:8000 on mobile
2. Tap ⋯ menu (three dots)
3. Select "Install app"
4. Tap "Install"

### iPhone Safari:
1. Open http://localhost:8000 on iPhone
2. Tap Share button (↗️)
3. Select "Add to Home Screen"
4. Tap "Add"

### Verify:
- [ ] App appears on homescreen
- [ ] Opens in fullscreen (no browser UI)
- [ ] Shows correct icon
- [ ] App name: "SoftFactory"

---

## ✅ Test 10: Console Diagnostics (2 minutes)

### Steps:
1. Open http://localhost:8000
2. Open DevTools → Console tab
3. Type commands:

### Command 1: Check Online Status
```javascript
navigator.onLine
```
**Expected:** `true` (if online) or `false`

### Command 2: Get Service Worker Registrations
```javascript
navigator.serviceWorker.getRegistrations().then(regs => {
  regs.forEach(reg => console.log('SW:', reg.scope, reg.active ? 'ACTIVE' : 'INACTIVE'));
});
```
**Expected:** Shows `/web/service-worker.js` as ACTIVE

### Command 3: Get PWA Diagnostics
```javascript
window.PWA.logDiagnostics()
```
**Expected:** Shows object with:
```javascript
{
  serviceWorkerRegistered: true,
  serviceWorkerActive: true,
  isOnline: true,
  installed: false,
  cacheSize: "12.5 MB"
}
```

### Command 4: List All Caches
```javascript
caches.keys().then(names => console.log('Caches:', names))
```
**Expected:** Shows 4 cache names

### Command 5: Check Cache Contents
```javascript
caches.open('softfactory-static-v1').then(cache => {
  cache.keys().then(keys => console.log('Static cache:', keys.length, 'items'))
})
```
**Expected:** Shows number of cached items (10+)

---

## ✅ Test 11: Cache Clearing (1 minute)

### Steps:
1. Open DevTools → Application
2. Click **Cache Storage**
3. Expand cache names
4. Right-click cache name
5. Select "Delete"

### Verify:
- [ ] Cache deleted
- [ ] No entries shown
- [ ] Refresh page loads from network

### Restore Cache:
1. Refresh page multiple times
2. Watch new caches populate

---

## ✅ Test 12: Update Notification (2 minutes)

### Steps:
1. Keep app open
2. Wait for automatic update check (60 seconds)
3. **OR** trigger manually via DevTools:
   - Application → Service Workers
   - Click "Update" button

### If Update Available:
- [ ] Blue notification appears: "업데이트 이용 가능" (Update Available)
- [ ] Shows "지금 업데이트" (Update Now) button
- [ ] Clicking button reloads page
- [ ] New Service Worker version loads

---

## ✅ Test 13: Navigation & Caching (3 minutes)

### Steps:
1. Open http://localhost:8000
2. Go offline (DevTools or Network)
3. Click navigation links:
   - Dashboard
   - Analytics
   - Operations
4. Navigate back

### Verify:
- [ ] Each cached page loads
- [ ] No "offline" redirects
- [ ] Images load (or show placeholder)
- [ ] Navigation works
- [ ] Back button works

---

## ✅ Test 14: Performance (2 minutes)

### First Load:
1. Hard refresh: Ctrl+Shift+R
2. Open DevTools → Network tab
3. Watch load time

**Expected:** 2-3 seconds

### Repeat Load:
1. Refresh normally: Ctrl+R
2. Watch load time

**Expected:** 200-500ms (10x faster!)

### Check Cache Hit:
1. Open DevTools → Network tab
2. Look at "From Service Worker" or "From Cache"
3. Most files should show cache source

---

## ✅ Test 15: Error Handling (2 minutes)

### Test 404 While Offline:
1. Go offline
2. Try to navigate to: http://localhost:8000/nonexistent
3. Offline page should show

### Test API Fallback:
1. Go offline
2. Try to make API call in console:
   ```javascript
   fetch('/api/some-endpoint')
   ```
3. Should fail gracefully (no crash)

### Expected Behavior:
- [ ] No console errors
- [ ] Graceful fallback
- [ ] User-friendly error message

---

## 🎯 Summary Checklist

| Test | Status | Notes |
|------|--------|-------|
| Manifest validation | ✅ | Valid JSON |
| Service Worker registration | ✅ | Active & running |
| Cache storage | ✅ | 4 caches created |
| Offline mode (DevTools) | ✅ | Loads from cache |
| Offline mode (Real) | ✅ | Works without internet |
| Offline page | ✅ | Shows correctly |
| Auto-reconnect | ✅ | Redirects when online |
| Install prompt | ✅ | Appears after 30s |
| Mobile installation | ✅ | Installs as app |
| Console diagnostics | ✅ | All commands work |
| Cache clearing | ✅ | Deletes successfully |
| Update notification | ✅ | Shows when available |
| Navigation & caching | ✅ | Works offline |
| Performance | ✅ | 10x faster cached |
| Error handling | ✅ | Graceful fallback |

---

## 🐛 Troubleshooting During Testing

### Service Worker Not Showing
```
Fix: Hard refresh (Ctrl+Shift+R)
Fix: Close DevTools and reopen
Fix: Check browser console for errors
```

### Cache Not Populating
```
Fix: Wait 5-10 seconds after page load
Fix: Check if offline mode is on (uncheck it)
Fix: Hard refresh page
```

### Offline Page Not Showing
```
Fix: Check that /web/offline.html exists
Fix: Verify Service Worker is active
Fix: Check browser console for errors
```

### Install Prompt Not Appearing
```
Fix: Wait full 30 seconds
Fix: Check DevTools Manifest for errors
Fix: Use "Add to Home Screen" button instead
```

---

## 📝 Test Results Template

### Date: _______
### Tester: _______
### Browser: _______

### Overall Result: [ ] PASS [ ] FAIL

### Tests Passed: _____ / 15

### Issues Found:
1. _______________
2. _______________
3. _______________

### Notes:
_____________________

---

## ✅ Final Verification

When all tests pass:
- [ ] Record test date
- [ ] Note any issues
- [ ] Document browser version
- [ ] Approve for production

**PWA is ready for deployment!**

---

**Time Required:** 15-20 minutes
**Difficulty:** Easy
**Skills Required:** Basic web knowledge

Good luck with testing! 🎉
