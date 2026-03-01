# 📝 Review Scrapers - Multi-Platform Listing Aggregator

> **Purpose**: This package provides a comprehensive web scraping system for aggregating review and experience campaign listings from multiple Korean platforms.
> **Status**: 🟢 ACTIVE (관리 중)
> **Impact**: [Engineering / Operations]

---

## ⚡ Executive Summary (핵심 요약)
- **주요 내용**: 본 문서는 Review Scrapers - Multi-Platform Listing Aggregator 관련 핵심 명세 및 관리 포인트를 포함합니다.
- **상태**: 현재 최신화 완료 및 검토 됨.
- **연관 문서**: [Master Index](./NOTION_MASTER_INDEX.md)

---

This package provides a comprehensive web scraping system for aggregating review and experience campaign listings from multiple Korean platforms.

## Overview

The review scraper system automatically collects listings from various platforms where users can apply to become reviewers or test products in exchange for rewards. The system:

- Scrapes 8 major Korean review/experience platforms
- Stores listings in a centralized database
- Runs on a scheduled background job (every 4 hours)
- Can be manually triggered via API endpoint
- Handles errors with exponential backoff retry logic
- Respects rate limits with configurable delays

## Supported Platforms

| Platform | URL | Type |
|----------|-----|------|
| **MoaView** | moaview.co.kr | Experience & product reviews |
| **Inflexer** | inflexer.net | Influencer campaigns |
| **ReviewPlace** | reviewplace.co.kr | Product reviews |
| **Wible** | wible.co.kr | Influencer & product campaigns |
| **MiBL** | mibl.kr | Influencer collaboration |
| **SeoulOuba** | seoulouba.co.kr | Service listings |
| **Naver Blog** | section.blog.naver.com | Blog-based campaigns |
| **Revu** | revu.net | Template/Example implementation |

## Architecture

### Directory Structure

```
backend/services/review_scrapers/
├── __init__.py                 # Factory, aggregator, registry
├── base_scraper.py            # Abstract base class with common functionality
├── moaview_scraper.py         # MoaView platform scraper
├── inflexer_scraper.py        # Inflexer platform scraper
├── reviewplace_scraper.py     # ReviewPlace platform scraper
├── wible_scraper.py           # Wible platform scraper
├── mibl_scraper.py            # MiBL platform scraper
├── seoulouba_scraper.py       # SeoulOuba platform scraper
├── naver_scraper.py           # Naver Blog scraper
├── revu_scraper.py            # Revu (template/example)
├── test_scrapers.py           # Test suite
└── README.md                  # This file
```

### Class Hierarchy

```
BaseScraper (abstract)
├── MoaviewScraper
├── InflexerScraper
├── ReviewPlaceScraper
├── WibleScraper
├── MiblScraper
├── SeouloubaScraper
├── NaverScraper
└── RevuScraper (template)
```

## Core Components

### BaseScraper

Abstract base class providing common functionality:

- **`fetch_page(url, params, timeout)`** - Fetch page with retry logic (3 attempts, exponential backoff)
- **`rate_limit()`** - Add delay between requests (configurable, default: 2 seconds)
- **`parse_listings()`** - Abstract method, must be implemented by subclasses
- **`save_listings(listings)`** - Save listings to database, preventing duplicates
- **`validate_listing(listing)`** - Validate listing has all required fields

### Platform Scrapers

Each platform scraper implements:

- **`parse_listings()`** - Main method that orchestrates scraping
  - Iterates through pages (limited to 5 pages per platform)
  - Parses each item on the page
  - Validates and saves listings
  - Returns list of collected listings

- **`_parse_item(item)`** - Parse individual HTML element into listing dict
  - Extracts title, brand, category
  - Parses reward type (상품/금전/경험) and value
  - Extracts deadline and URL
  - Generates external_id from platform

- **`_parse_deadline(item)`** - Parse various deadline formats
  - Handles "D-7" format (days remaining)
  - Handles specific dates "YYYY-MM-DD"
  - Defaults to 7-14 days if parsing fails

- **Platform-specific methods** - Additional parsing for requirements, engagement rates, etc.

### Aggregator Functions

**`aggregate_all_listings(max_workers=3)`**
- Scrape all 7 active platforms concurrently
- Uses ThreadPoolExecutor for parallelization
- Returns dict with platform names and listing counts
- Respects rate limiting within each scraper

**`aggregate_specific_platforms(platforms, max_workers=3)`**
- Scrape only specified platforms
- Useful for testing or focusing on specific sources
- Returns dict with results

**`get_scraper(platform)`**
- Get scraper instance for specific platform
- Returns None if not found

**`list_available_platforms()`**
- Get list of all available platform identifiers

## Listing Data Structure

Each listing stored in database has:

```python
{
    'external_id': str,           # Unique ID from platform
    'title': str,                 # Listing title
    'brand': str,                 # Brand/company name
    'category': str,              # Product category
    'reward_type': str,           # '상품' (product) | '금전' (cash) | '경험' (experience)
    'reward_value': int,          # Reward in KRW
    'deadline': datetime,         # Application deadline
    'url': str,                   # Link to listing
    'image_url': str,             # Optional product image
    'max_applicants': int,        # Optional max number of applicants
    'requirements': dict,         # Optional requirements (followers, engagement, etc.)
    'status': str,                # 'active' | 'closed' | 'ended'
    'source_platform': str,       # Platform identifier
    'scraped_at': datetime        # When it was scraped
}
```

## Scheduled Execution

### Background Job

Configured in `backend/scheduler.py`:

- **Job ID:** `scrape_review_listings`
- **Trigger:** Every 4 hours
- **Function:** `scrape_review_listings(app)`
- **Max workers:** 3 concurrent scrapers
- **Timeout:** Handled by individual scraper timeouts (10 seconds per request)

### Manual Triggering

Via API endpoint:

```bash
# Scrape all platforms
POST /api/review/scraper/run
Authorization: Bearer {token}

# Scrape specific platforms
POST /api/review/scraper/run?platforms=moaview,inflexer
Authorization: Bearer {token}
```

## API Endpoints

### GET `/api/review/scraper/status`

Get scraper status and statistics.

**Response:**
```json
{
    "success": true,
    "data": {
        "available_platforms": ["moaview", "inflexer", ...],
        "platform_statistics": {
            "moaview": {
                "total_listings": 42,
                "last_scraped": "2026-02-26T10:30:00"
            }
        },
        "total_listings": 245,
        "scheduler_status": "active"
    }
}
```

### POST `/api/review/scraper/run`

Manually trigger scraping (requires authentication).

**Parameters:**
- `platforms` (optional): Comma-separated list (e.g., `moaview,inflexer`)

**Response:**
```json
{
    "success": true,
    "data": {
        "message": "Scraper job started in background",
        "platforms": "all",
        "started_at": "2026-02-26T10:35:00"
    }
}
```

### GET `/api/review/listings/by-platform/{platform}`

Get listings from specific platform.

**Parameters:**
- `limit`: Number to return (default: 20, max: 100)
- `offset`: Pagination offset (default: 0)
- `sort`: 'deadline' or 'reward' (default: 'deadline')

**Response:**
```json
{
    "success": true,
    "data": {
        "listings": [...],
        "total": 245,
        "offset": 0,
        "limit": 20,
        "platform": "moaview"
    }
}
```

## Testing

### Test Script

```bash
# Test all scrapers
python -m backend.services.review_scrapers.test_scrapers

# Test specific scraper
python -m backend.services.review_scrapers.test_scrapers moaview

# Test with Flask app context
cd /d/Project && python << 'EOF'
from backend.app import app
app.app_context().push()
from backend.services.review_scrapers import aggregate_all_listings
results = aggregate_all_listings()
print(f"Results: {results}")
EOF
```

### Test Functions

In `test_scrapers.py`:

- **`test_scraper(name)`** - Test single scraper
- **`test_all()`** - Test all scrapers sequentially
- **`test_aggregation()`** - Test concurrent aggregation
- **`test_listing_validation(listings)`** - Validate listing structure

## Error Handling

### Retry Logic

- **Max retries:** 3 attempts per request
- **Backoff strategy:** Exponential (1s, 2s, 4s)
- **Timeout:** 10 seconds per request
- **Handled exceptions:**
  - `requests.exceptions.Timeout`
  - `requests.exceptions.ConnectionError`
  - `requests.exceptions.RequestException`

### Logging

- **Logger:** `review.scrapers` (main)
- **Sub-loggers:**
  - `review.scrapers.base`
  - `review.scrapers.{platform}`
  - `review.scraper.manual` (API-triggered)

**Log levels:**
- INFO: Major operations (scrape start/complete, listings saved)
- DEBUG: Page fetching, item parsing
- WARNING: Non-critical errors, timeouts
- ERROR: Critical errors, parsing failures

## Performance Considerations

### Concurrency

- **Max workers:** 3 concurrent platform scrapers
- **Rate limiting:** 2-second delay between requests per platform
- **Estimated run time:** 5-7 minutes per full aggregation

### Resource Usage

- **Memory:** ~5MB per scraper thread
- **Network:** ~1-2 MB per platform (compressed HTML)
- **Database:** ~100-200 new listings per run

### Optimization

- **Page limit:** 5 pages per platform (prevents excessive scraping)
- **Duplicate detection:** Checks external_id before saving
- **Concurrent execution:** ThreadPoolExecutor with controlled max_workers
- **Batch database commits:** One commit per scraper

## Adding a New Platform

### Step 1: Create Scraper Class

Create `new_platform_scraper.py`:

```python
from .base_scraper import BaseScraper
from typing import List, Dict
import logging

logger = logging.getLogger('review.scrapers')

class NewPlatformScraper(BaseScraper):
    def __init__(self):
        super().__init__('newplatform', 'https://example.com')

    def parse_listings(self) -> List[Dict]:
        # Implement scraping logic
        pass

    def _parse_item(self, item) -> Dict:
        # Implement item parsing
        pass

    def _parse_deadline(self, item):
        # Implement deadline parsing
        pass
```

### Step 2: Register Scraper

Add to `__init__.py`:

```python
from .new_platform_scraper import NewPlatformScraper

SCRAPERS = [
    ...,
    NewPlatformScraper(),
]
```

### Step 3: Test

```bash
python -m backend.services.review_scrapers.test_scrapers newplatform
```

## Troubleshooting

### Listings not saving

1. Check if ReviewListing model exists in models.py
2. Verify database connection in app context
3. Check logs for duplicate external_id errors

### Scraper timing out

1. Check platform website availability
2. Increase timeout value in BaseScraper.__init__
3. Reduce max_pages limit in parse_listings()

### Missing fields

1. Verify CSS selectors match current HTML structure
2. Add fallback selectors for alternate formats
3. Use `_parse_deadline()` helper for deadline parsing

### Rate limiting issues

1. Increase delay in BaseScraper (currently 2 seconds)
2. Reduce max_workers in aggregation (currently 3)
3. Add platform-specific delay if needed

## Future Enhancements

- [ ] Selenium/Puppeteer for JavaScript-heavy sites
- [ ] Proxy rotation for large-scale scraping
- [ ] ML-based content classification
- [ ] User preference matching and notifications
- [ ] Scraper performance metrics dashboard
- [ ] A/B testing platform variations
- [ ] Real-time listing updates (webhook support)
- [ ] Platform-specific APIs instead of scraping where available

## Dependencies

- `requests` - HTTP requests
- `beautifulsoup4` - HTML parsing
- `sqlalchemy` - Database ORM
- `flask` - Web framework
- `apscheduler` - Task scheduling
- `python 3.8+`

## License

Internal use only - SoftFactory platform