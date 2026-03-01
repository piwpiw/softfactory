# 📘 Web Scraper Security - Quick Start Guide

> **Purpose**: Copy and paste into your `.env` file:
> **Status**: 🟢 ACTIVE (관리 중)
> **Impact**: [Engineering / Operations]

---

## ⚡ Executive Summary (핵심 요약)
- **주요 내용**: 본 문서는 Web Scraper Security - Quick Start Guide 관련 핵심 명세 및 관리 포인트를 포함합니다.
- **상태**: 현재 최신화 완료 및 검토 됨.
- **연관 문서**: [Master Index](./NOTION_MASTER_INDEX.md)

---

## 30-Minute Setup (Complete)

### 1. Environment Setup (5 minutes)

Copy and paste into your `.env` file:

```bash
# Choose ONE proxy provider:

# Option A: ScraperAPI (RECOMMENDED - easiest)
SCRAPERAPI_KEY=your_scraperapi_key_here

# Option B: BrightData
# BRIGHTDATA_KEY=customer_id:password

# Option C: Direct proxies
# DIRECT_PROXIES=http://proxy1:8080,http://proxy2:8080

# CAPTCHA Solving
2CAPTCHA_KEY=your_2captcha_api_key_here

# Scraper Settings
PROXY_ROTATION_STRATEGY=round-robin
RETRY_MAX_ATTEMPTS=3
ENABLE_PROXY_ROTATION=true
ENABLE_CAPTCHA_SOLVING=true
```

### 2. Get API Keys (10 minutes)

#### ScraperAPI Setup

1. Go to https://www.scraperapi.com
2. Click "Sign up"
3. Verify email
4. Copy API key from dashboard
5. Paste into `.env`

**Cost:** ~$0.005 per request (very cheap)

#### 2Captcha Setup

1. Go to https://2captcha.com
2. Click "Sign up"
3. Verify email
4. Navigate to Settings → API Key
5. Copy API key
6. Paste into `.env`

**Cost:** ~$0.0003 per CAPTCHA (negligible)

### 3. Update Your Scraper (5 minutes)

```python
# In your scraper class
from backend.services.review_scrapers.base_scraper import BaseScraper

class YourPlatformScraper(BaseScraper):
    def __init__(self):
        # Simply add use_proxy=True
        super().__init__(
            platform_name='yourplatform',
            base_url='https://yourplatform.com',
            use_proxy=True,              # Automatic proxy rotation
            use_captcha_solver=True      # Automatic CAPTCHA solving
        )

    def parse_listings(self):
        # fetch_page() now uses proxies automatically!
        soup = self.fetch_page('https://yourplatform.com/listings')
        # ... parse listings ...
        return listings
```

That's it! No other changes needed.

### 4. Test Setup (5 minutes)

```bash
cd D:/Project

# Run tests
python -m pytest tests/test_scraper_resilience.py -v

# Should see: 33 passed in 8.26s
```

### 5. Verify Configuration (5 minutes)

```python
# Quick test script
from backend.services.proxy_manager import ProxyManager
from backend.services.captcha_solver import CaptchaSolver

# Test proxy manager
pm = ProxyManager(provider='scraperapi')
proxy = pm.get_proxy()
print(f"✓ Proxy: {proxy[:40]}...")

health = pm.test_proxy_health(proxy)
print(f"✓ Health: {health['healthy']}, Latency: {health['latency']}ms")

# Test CAPTCHA solver
solver = CaptchaSolver()
balance = solver.get_balance()
print(f"✓ 2Captcha balance: ${balance:.2f}")
```

---

## What It Does

### Automatic Features

When you enable proxy rotation:
1. Every request gets a different IP address
2. Bypasses IP blocking automatically
3. Rotates proxies on retry
4. Tracks proxy health

When you enable CAPTCHA solving:
1. Detects CAPTCHA challenges (future version)
2. Solves them automatically with 2Captcha
3. Returns solution token
4. Tracks costs

### Real Example

```python
# Before (will get blocked)
response = requests.get('https://revu.net/campaigns')
# ❌ HTTP 403 Forbidden (IP blocked)

# After (with proxy rotation)
scraper = RevuScraper()  # Uses proxy rotation
listings = scraper.parse_listings()
# ✅ Success! 50 listings scraped
```

---

## Costs

### Proxy Costs

| Provider | Price | Good For |
|----------|-------|----------|
| ScraperAPI | $0.005/req | General scraping |
| BrightData | Higher | Premium needs |
| Direct | Custom | Budget |

**Example:** Scraping 1,000 listings with ScraperAPI = $5

### CAPTCHA Costs

| Type | Cost |
|------|------|
| Image CAPTCHA | $0.0002 |
| reCAPTCHA v2 | $0.0003 |
| hCaptcha | $0.0003 |

**Example:** Solving 100 CAPTCHAs = $0.03

**Total for 1,000 listings with 5% CAPTCHAs = ~$5.05**

---

## Troubleshooting

### "SCRAPERAPI_KEY not configured"

**Fix:** Add to `.env`:
```bash
SCRAPERAPI_KEY=your_actual_key_here
```

### "Proxy health check failed"

**Fix:** Check internet connection and proxy provider status

### "Failed to solve CAPTCHA"

**Fix:** Check 2Captcha balance with:
```python
from backend.services.captcha_solver import CaptchaSolver
solver = CaptchaSolver()
print(solver.get_balance())
```

---

## Testing Your Setup

```bash
# Run full test suite
pytest tests/test_scraper_resilience.py -v

# Run specific test
pytest tests/test_scraper_resilience.py::TestProxyManager::test_get_scraperapi_proxy -v

# Run with debug output
pytest tests/test_scraper_resilience.py -v -s
```

---

## Monitoring

```python
# Check proxy health
pm = ProxyManager(provider='scraperapi')
stats = pm.get_stats()
print(f"Provider: {stats['provider']}")
print(f"Strategy: {stats['strategy']}")
print(f"Healthy proxies: {stats['healthy_proxies']}/{stats['total_proxies']}")

# Check CAPTCHA costs
solver = CaptchaSolver()
stats = solver.get_stats()
print(f"Total solved: {stats['total_solved']}")
print(f"Total cost: ${stats['total_cost_usd']:.4f}")
print(f"Avg cost: ${stats['avg_cost_per_solve']:.6f}")
```

---

## Next Steps

1. ✅ Set up environment variables
2. ✅ Get API keys (ScraperAPI + 2Captcha)
3. ✅ Add `use_proxy=True` to your scrapers
4. ✅ Run tests
5. ✅ Monitor costs and performance
6. 📊 Check logs in `D:/Project/logs`

---

## Key Files

| File | Purpose | Size |
|------|---------|------|
| `backend/services/proxy_manager.py` | Proxy rotation | 600 lines |
| `backend/services/captcha_solver.py` | CAPTCHA solving | 650 lines |
| `tests/test_scraper_resilience.py` | Test suite | 600+ lines |
| `docs/SCRAPER_SECURITY.md` | Full documentation | — |
| `.env` | Configuration | Added 15 lines |

---

## Support

**Documentation:** See `docs/SCRAPER_SECURITY.md` for complete reference

**Tests:** Run `pytest tests/test_scraper_resilience.py -v` to verify

**Issues:** Check logs in `D:/Project/logs/` directory

---

## Summary

✅ **30-minute setup complete**
- [x] ProxyManager created (600 lines)
- [x] CaptchaSolver created (650 lines)
- [x] BaseScraper updated with proxy integration
- [x] Environment variables added
- [x] Test suite created (33 tests, all passing)
- [x] Documentation complete

**You're ready to scrape!** 🚀

---

**Version:** 1.0.0
**Date:** 2026-02-26
**Status:** Production Ready