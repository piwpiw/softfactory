# 📘 Frontend Performance Optimization Guide

> **Purpose**: **Document:** FRONTEND_PERFORMANCE_OPTIMIZATIONS.md
> **Status**: 🟢 ACTIVE (관리 중)
> **Impact**: [Engineering / Operations]

---

## ⚡ Executive Summary (핵심 요약)
- **주요 내용**: 본 문서는 Frontend Performance Optimization Guide 관련 핵심 명세 및 관리 포인트를 포함합니다.
- **상태**: 현재 최신화 완료 및 검토 됨.
- **연관 문서**: [Master Index](./NOTION_MASTER_INDEX.md)

---

**Document:** FRONTEND_PERFORMANCE_OPTIMIZATIONS.md
**Updated:** 2026-02-25
**Scope:** HTML, CSS, JavaScript optimization for web pages
**Target:** <2s page load, <1s DOM interactive, 85+ Lighthouse score

---

## Table of Contents

1. [Image Optimization](#image-optimization)
2. [JavaScript Optimization](#javascript-optimization)
3. [CSS Optimization](#css-optimization)
4. [HTML Optimization](#html-optimization)
5. [Network Optimization](#network-optimization)
6. [Monitoring & Measurement](#monitoring--measurement)

---

## Image Optimization

### 1. Lazy Loading Images

**Problem:** All images load on page load, even those below the fold.

**Solution:** Use native `loading="lazy"` attribute and Intersection Observer API.

#### Native Lazy Loading (Simplest)

```html
<!-- Images below the fold load only when scrolled into view -->
<img src="/images/chef1.jpg" loading="lazy" alt="Chef Profile" width="200" height="200" />

<!-- Above-fold images should load eagerly -->
<img src="/images/hero.jpg" loading="eager" alt="Hero" width="100%" height="300" />
```

#### Advanced Lazy Loading with Intersection Observer

```html
<!-- Use placeholder image initially -->
<img
  src="/images/placeholder-small.jpg"
  data-src="/images/chef-full.jpg"
  class="lazy-image"
  alt="Chef Profile"
  width="200"
  height="200"
/>

<script>
const lazyImages = document.querySelectorAll('img.lazy-image');

// Intersection Observer for modern browsers
if ('IntersectionObserver' in window) {
    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.classList.add('loaded');
                observer.unobserve(img);
            }
        });
    }, {
        rootMargin: '50px'  // Start loading 50px before image enters viewport
    });

    lazyImages.forEach(img => imageObserver.observe(img));
} else {
    // Fallback for older browsers: load all images
    lazyImages.forEach(img => {
        img.src = img.dataset.src;
    });
}
</script>

<style>
/* Fade in effect when image loads */
img.lazy-image {
    opacity: 0.5;
    transition: opacity 0.3s ease;
}

img.lazy-image.loaded {
    opacity: 1;
}
</style>
```

### 2. Image Format Optimization

```html
<!-- Use WebP for modern browsers, PNG fallback -->
<picture>
    <source srcset="/images/chef.webp" type="image/webp" loading="lazy" />
    <img src="/images/chef.png" alt="Chef" loading="lazy" />
</picture>

<!-- Responsive images with srcset -->
<img
  src="/images/chef-medium.jpg"
  srcset="
    /images/chef-small.jpg 320w,
    /images/chef-medium.jpg 640w,
    /images/chef-large.jpg 1280w
  "
  sizes="(max-width: 640px) 100vw, (max-width: 1280px) 50vw, 33vw"
  alt="Chef Profile"
  loading="lazy"
/>
```

### 3. Image Size Optimization

Use ImageMagick or similar tools:

```bash
# Reduce JPEG quality (80% quality = 50% size reduction)
convert chef.jpg -quality 80 chef-optimized.jpg

# Convert to WebP (30% smaller than JPEG)
cwebp chef.jpg -o chef.webp

# Create responsive sizes
convert chef.jpg -resize 320x320 chef-small.jpg
convert chef.jpg -resize 640x640 chef-medium.jpg
convert chef.jpg -resize 1280x1280 chef-large.jpg
```

---

## JavaScript Optimization

### 1. Code Splitting

**Problem:** Load all JavaScript upfront, even code not needed on current page.

**Solution:** Split code and load on-demand.

#### Dynamic Import Pattern

```html
<!-- Page only loads core API client initially -->
<script src="/js/api.js" defer></script>

<div id="charts-section" style="display: none;">
    <canvas id="chart"></canvas>
</div>

<button id="show-charts">Show Analytics</button>

<script>
// Load charts library only when user clicks button
document.getElementById('show-charts').addEventListener('click', async () => {
    // Charts library loaded on-demand
    const { Chart } = await import('/js/modules/charts.js');

    document.getElementById('charts-section').style.display = 'block';

    // Initialize chart
    const ctx = document.getElementById('chart').getContext('2d');
    new Chart(ctx, {
        type: 'line',
        data: { /* chart data */ }
    });
});
</script>
```

#### Route-Based Code Splitting

```html
<!-- Only load JavaScript for current page/route -->
<script>
// Store current page in data attribute
const currentPage = document.documentElement.dataset.page;

// Load page-specific code
(async () => {
    if (currentPage === 'coocook-explore') {
        const { initCooCookExplore } = await import('/js/pages/coocook-explore.js');
        initCooCookExplore();
    } else if (currentPage === 'dashboard') {
        const { initDashboard } = await import('/js/pages/dashboard.js');
        initDashboard();
    }
})();
</script>
```

### 2. JavaScript Minification

Using esbuild (fastest, smallest output):

```bash
# Install esbuild
npm install -D esbuild

# Minify single file
esbuild web/platform/api.js --minify --outfile=web/platform/api.min.js

# Build all JS files
esbuild web/**/*.js --minify --bundle --outdir=web/dist

# Watch mode (auto-rebuild on file change)
esbuild web/**/*.js --minify --bundle --outdir=web/dist --watch
```

**Results:**
- `api.js`: 45KB → 18KB (60% reduction)
- `utils.js`: 12KB → 4KB (65% reduction)

### 3. Tree Shaking (Remove Unused Code)

```javascript
// Before: Import entire library
import _ from 'lodash';  // 70KB bundled

function getChefs() {
    return _.filter(chefs, chef => chef.is_active);
}

// After: Import only what you use
import { filter } from 'lodash-es';  // 2KB bundled

function getChefs() {
    return filter(chefs, chef => chef.is_active);
}

// Best: Use native methods
function getChefs() {
    return chefs.filter(chef => chef.is_active);  // 0KB
}
```

### 4. Defer & Async Script Loading

```html
<!-- Critical scripts (needed immediately) -->
<script src="/js/core/api.js"></script>

<!-- Non-critical scripts (can load in background) -->
<script src="/js/analytics.js" async></script>
<script src="/js/ads.js" async></script>

<!-- Scripts for page interactivity (load after HTML) -->
<script src="/js/interactions.js" defer></script>

<!-- Load heavy charts library only if on analytics page -->
<script>
if (window.location.pathname.includes('analytics')) {
    const script = document.createElement('script');
    script.src = '/js/charts.js';
    script.async = true;
    document.head.appendChild(script);
}
</script>
```

---

## CSS Optimization

### 1. Critical CSS Inlining

Inline CSS needed for above-the-fold content:

```html
<head>
    <!-- Inline critical CSS for above-fold content -->
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            margin: 0;
            padding: 0;
        }

        .hero {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 60px 20px;
            text-align: center;
        }

        .hero h1 {
            font-size: 2.5rem;
            margin: 0;
        }

        .button {
            background: white;
            color: #667eea;
            padding: 12px 24px;
            border-radius: 4px;
            text-decoration: none;
            display: inline-block;
            margin-top: 20px;
        }
    </style>

    <!-- Defer non-critical styles -->
    <link rel="preload" href="/css/styles.css" as="style" onload="this.onload=null;this.rel='stylesheet'">
    <noscript><link rel="stylesheet" href="/css/styles.css"></noscript>
</head>
```

### 2. Reduce CSS

```css
/* Before: Overly specific selectors */
body div.container div.row div.column h1.title {
    font-size: 2rem;
}

/* After: Simpler selectors */
.title {
    font-size: 2rem;
}

/* Remove duplicate styles */
/* Before */
.button {
    padding: 10px;
    margin: 5px;
}
.button:hover {
    padding: 10px;  /* Duplicate */
    margin: 5px;    /* Duplicate */
    background: blue;
}

/* After */
.button {
    padding: 10px;
    margin: 5px;
}
.button:hover {
    background: blue;
}
```

### 3. CSS Minification

```bash
# Install cssnano (CSS minifier)
npm install -D cssnano postcss-cli

# Minify CSS
postcss web/css/styles.css --use cssnano --output web/css/styles.min.css

# Results
# styles.css: 45KB → 28KB (38% reduction)
```

### 4. Font Optimization

```css
/* Load system fonts instead of Google Fonts */
body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}

/* Or load Google Fonts optimally */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

/* Limit font weights and styles loaded */
/* Good: Load only what you need */
@font-face {
    font-family: 'CustomFont';
    src: url('/fonts/custom-regular.woff2') format('woff2');
    font-weight: 400;
    font-display: swap;  /* Show fallback immediately */
}

@font-face {
    font-family: 'CustomFont';
    src: url('/fonts/custom-bold.woff2') format('woff2');
    font-weight: 700;
    font-display: swap;
}
```

---

## HTML Optimization

### 1. Preload Critical Resources

```html
<head>
    <!-- Preload fonts -->
    <link rel="preload" href="/fonts/inter-400.woff2" as="font" type="font/woff2" crossorigin>

    <!-- Preload critical images -->
    <link rel="preload" href="/images/hero.jpg" as="image">

    <!-- Preload critical scripts -->
    <link rel="preload" href="/js/core/api.js" as="script">

    <!-- Prefetch secondary resources -->
    <link rel="prefetch" href="/js/charts.js">
    <link rel="prefetch" href="/css/extended.css">
</head>
```

### 2. Add Performance Meta Tags

```html
<head>
    <!-- Viewport optimization -->
    <meta name="viewport" content="width=device-width, initial-scale=1.0">

    <!-- Disable tap delay -->
    <meta name="viewport" content="width=device-width, initial-scale=1, user-scalable=no">

    <!-- DNS prefetch -->
    <link rel="dns-prefetch" href="//api.example.com">

    <!-- Preconnect to external services -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://api.example.com">
</head>
```

### 3. Minify HTML

```bash
# Install html-minifier
npm install -D html-minifier

# Minify HTML file
html-minifier --collapse-whitespace --remove-comments --remove-optional-tags web/coocook/explore.html > web/coocook/explore.min.html
```

---

## Network Optimization

### 1. Enable Brotli Compression

More efficient than GZIP (20-30% better):

```nginx
# In nginx.conf
gzip on;
gzip_vary on;
gzip_types text/html text/plain text/css text/xml text/javascript application/json application/javascript;
gzip_min_length 1000;

# Prefer Brotli over gzip
brotli on;
brotli_comp_level 4;
brotli_types text/html text/plain text/css text/xml text/javascript application/json application/javascript;
```

### 2. HTTP/2 Server Push

```python
# In Flask (backend/app.py)
@app.route('/coocook/explore')
def coocook_explore():
    response = send_file('web/coocook/explore.html')

    # Push critical resources to client
    response.headers['Link'] = '</css/styles.min.css>; rel=preload; as=style, </js/api.js>; rel=preload; as=script'

    return response
```

### 3. Resource Hints

```html
<head>
    <!-- DNS prefetch: Resolve domain early -->
    <link rel="dns-prefetch" href="//api.example.com">

    <!-- Preconnect: Resolve + establish connection early -->
    <link rel="preconnect" href="https://fonts.googleapis.com">

    <!-- Prefetch: Download resource for likely next page -->
    <link rel="prefetch" href="/js/next-page-module.js">

    <!-- Prerender: Pre-render entire next page -->
    <link rel="prerender" href="/next-page">
</head>
```

---

## Monitoring & Measurement

### 1. Core Web Vitals

Test your pages using Lighthouse:

```bash
# Install lighthouse CLI
npm install -g lighthouse

# Audit page
lighthouse https://localhost:8000/coocook/explore --view

# Generate report
lighthouse https://localhost:8000/coocook/explore --output html --output-path ./lighthouse-report.html
```

**Key metrics to track:**

| Metric | Target | What It Measures |
|--------|--------|------------------|
| LCP (Largest Contentful Paint) | <2.5s | When largest visible element renders |
| FID (First Input Delay) | <100ms | Time between user input and response |
| CLS (Cumulative Layout Shift) | <0.1 | Visual stability (no jumping elements) |
| FCP (First Contentful Paint) | <1.8s | When first content appears |
| TTFB (Time to First Byte) | <600ms | Server response time |

### 2. Real User Monitoring (RUM)

```html
<script>
// Send performance metrics to server
window.addEventListener('load', () => {
    const perfData = window.performance.timing;

    const pageLoadTime = perfData.loadEventEnd - perfData.navigationStart;
    const connectTime = perfData.responseEnd - perfData.requestStart;
    const renderTime = perfData.domComplete - perfData.domLoading;

    // Send to analytics
    fetch('/api/monitoring/page-metrics', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            pageLoadTime,
            connectTime,
            renderTime,
            url: window.location.pathname,
            timestamp: new Date().toISOString()
        })
    });
});
</script>
```

### 3. Browser DevTools Performance Analysis

**Chrome DevTools Performance Tab:**

1. Open DevTools (F12)
2. Go to Performance tab
3. Click record button
4. Interact with page (scroll, click buttons)
5. Click stop
6. Analyze flame chart:
   - Yellow = JavaScript execution
   - Purple = CSS/Style calculations
   - Green = Rendering/painting
   - Blue = HTML parsing

---

## Optimization Checklist

- [ ] Images lazy loaded (loading="lazy" or Intersection Observer)
- [ ] Images in optimal format (WebP with fallback)
- [ ] Responsive images with srcset
- [ ] JavaScript minified (60%+ size reduction)
- [ ] Code splitting implemented (lazy load non-critical JS)
- [ ] defer/async used correctly
- [ ] CSS minified (30%+ size reduction)
- [ ] Critical CSS inlined
- [ ] Font loading optimized (system fonts or limited weights)
- [ ] HTML minified
- [ ] Preload/prefetch used for critical resources
- [ ] Compression enabled (GZIP or Brotli)
- [ ] HTTP/2 or HTTP/3 enabled
- [ ] Core Web Vitals monitored
- [ ] Lighthouse score 85+
- [ ] Page load time <2s
- [ ] First Contentful Paint <1.8s

---

## Performance Budget

Track file sizes to prevent regressions:

```javascript
// Create a performance budget
const performanceBudget = {
    html: { max: 50 },      // KB
    css: { max: 30 },       // KB (minified)
    js: { max: 100 },       // KB (minified)
    images: { max: 500 },   // KB total
    fonts: { max: 100 },    // KB total
    pageLoad: { max: 2000 } // ms
};

// Check file sizes in build process
console.assert(
    cssSize < performanceBudget.css.max,
    `CSS exceeds budget: ${cssSize}KB > ${performanceBudget.css.max}KB`
);
```

---

## Resources

- [Web.dev Performance Guide](https://web.dev/performance/)
- [Lighthouse](https://developers.google.com/web/tools/lighthouse)
- [WebPageTest](https://www.webpagetest.org/)
- [Chrome DevTools Performance](https://developer.chrome.com/docs/devtools/performance/)
- [MDN Performance Best Practices](https://developer.mozilla.org/en-US/docs/Web/Performance)