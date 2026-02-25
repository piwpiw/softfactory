# 🎁 체험단 통합 플랫폼 (Experience Platform) - M-006

## Overview

**Project:** Korean Experience Platform Integration
**Code:** M-006
**Status:** MVP v1.0 (Complete)
**Launch Date:** 2026-02-25
**Timeline:** 10-minute delivery

Unified dashboard to browse experience listings from Korea's major platforms:
- 쿠팡이츠 (Coupang Eats)
- 당근마켓 (Daangn Market)
- 숨고 (Soomgo)
- 오늘의딜 (Today's Deal)

## Features

### Phase 1 (MVP - Complete)
- [x] Unified dashboard with responsive design
- [x] Real-time filtering by site and category
- [x] 8+ sample experience listings
- [x] API endpoints for all data
- [x] Mobile-friendly UI (Tailwind CSS)
- [x] Auto-refresh every 5 minutes
- [x] Search and filter capabilities
- [x] Deadline-based sorting and urgency indicators

### Phase 2 (QA Ready)
- [ ] Real crawlers with BeautifulSoup/Selenium
- [ ] Database persistence
- [ ] Scheduled crawling (APScheduler)
- [ ] Advanced filtering and search

### Phase 3+ (Future)
- [ ] User accounts and saved preferences
- [ ] Push notifications for new listings
- [ ] Category-based subscriptions
- [ ] Mobile app
- [ ] Integration with user's SNS accounts

## Architecture

### Backend Structure
```
backend/
├── services/
│   └── experience.py          # Experience service blueprint (7 endpoints)
├── models.py                  # ExperienceListing, CrawlerLog models
└── app.py                     # Flask app with experience_bp registered
```

### Frontend Structure
```
web/experience/
├── index.html                 # Main dashboard (responsive, dark theme)
└── README.md                  # This file
```

### Crawler Structure
```
scripts/crawlers/
├── crawler_base.py            # Base class for all crawlers
├── coupang_eats_crawler.py    # Coupang Eats crawler (MVP: dummy data)
├── danggeun_crawler.py        # Daangn Market crawler (MVP: dummy data)
├── soomgo_crawler.py          # Soomgo crawler (MVP: dummy data)
└── __init__.py                # Package init
```

## API Endpoints

### GET `/api/experience/listings`
Get all or filtered experience listings.

**Parameters:**
- `site` (optional): Filter by site (coupang_eats, danggeun, soomgo, today_deal)
- `category` (optional): Filter by category (음식, 카페, 뷰티, etc.)
- `page` (optional): Page number (default: 1)
- `per_page` (optional): Items per page (default: 12)

**Response:**
```json
{
  "total": 8,
  "page": 1,
  "per_page": 12,
  "pages": 1,
  "data": [
    {
      "id": "hash",
      "site": "coupang_eats",
      "title": "[쿠팡이츠] 맛집 배달 리뷰 체험단",
      "url": "https://www.coupangeats.com",
      "deadline": "2026-03-02T...",
      "category": "음식",
      "reward": "무료 음식 + 현금 2만원",
      "description": "신규 맛집의 배달 음식을 먹고 솔직한 리뷰를 남겨주세요",
      "image_url": "https://..."
    }
  ]
}
```

### GET `/api/experience/listings/<id>`
Get single listing detail.

**Response:**
```json
{
  "id": 1,
  "site": "coupang_eats",
  "title": "...",
  "url": "...",
  "deadline": "...",
  "category": "...",
  "reward": "...",
  "description": "...",
  "image_url": "..."
}
```

### GET `/api/experience/stats`
Get platform statistics.

**Response:**
```json
{
  "total_listings": 8,
  "total_sites": 4,
  "sites": {
    "coupang_eats": {
      "count": 2,
      "categories": ["음식"]
    },
    "danggeun": {
      "count": 3,
      "categories": ["카페", "편의점", "음식"]
    },
    "soomgo": {
      "count": 2,
      "categories": ["생활서비스", "인테리어"]
    },
    "today_deal": {
      "count": 1,
      "categories": ["뷰티"]
    }
  },
  "categories": {
    "음식": 3,
    "카페": 1,
    "뷰티": 1,
    "생활서비스": 1,
    "인테리어": 1,
    "편의점": 1
  },
  "last_updated": "2026-02-25T..."
}
```

### GET `/api/experience/categories`
Get all available categories.

**Response:**
```json
{
  "categories": ["뷰티", "생활서비스", "음식", "카페", "인테리어", "편의점"]
}
```

### GET `/api/experience/sites`
Get all available sites with counts.

**Response:**
```json
{
  "sites": {
    "coupang_eats": {
      "name": "Coupang Eats",
      "count": 2
    },
    "danggeun": {
      "name": "Danggeun",
      "count": 3
    },
    "soomgo": {
      "name": "Soomgo",
      "count": 2
    },
    "today_deal": {
      "name": "Today Deal",
      "count": 1
    }
  }
}
```

### POST `/api/experience/crawl`
Trigger crawler to refresh listings.

**Request Body:**
```json
{
  "site": "coupang_eats"  // optional
}
```

**Response:**
```json
{
  "status": "success",
  "total_listings_found": 8,
  "sites_crawled": ["coupang_eats", "danggeun", "soomgo", "today_deal"],
  "timestamp": "2026-02-25T..."
}
```

## Database Models

### ExperienceListing
```python
class ExperienceListing(db.Model):
    id: Integer (Primary Key)
    site: String (coupang_eats, danggeun, soomgo, today_deal)
    title: String (max 300 chars)
    url: String (max 500 chars)
    deadline: DateTime
    image_url: String (max 500 chars)
    category: String (max 100 chars)
    description: Text
    reward: String (max 200 chars)
    created_at: DateTime
    updated_at: DateTime
```

### CrawlerLog
```python
class CrawlerLog(db.Model):
    id: Integer (Primary Key)
    site: String
    listing_count: Integer
    last_crawl_time: DateTime
    status: String (success, error)
    error_message: Text
    created_at: DateTime
```

## Frontend Features

### Dashboard
- Dark theme with purple/indigo gradient header
- Real-time statistics (total listings count)
- Responsive grid layout (1 column mobile, 2 columns tablet, 3 columns desktop)

### Filtering
- **Site Filter:** All, Coupang Eats, Daangn, Soomgo, Today's Deal
- **Category Filter:** Dynamic based on available categories
- Real-time filter application

### Listing Cards
- Site badge with unique colors
- Urgency indicator (red "긴급" badge if deadline < 3 days)
- Deadline countdown (days until deadline)
- Reward information
- Call-to-action button linking to original site
- Placeholder images with error handling

### User Actions
- **New Listings Refresh:** Manually trigger data refresh
- **Crawl Trigger:** Start crawler to fetch new data
- **Auto-Refresh:** Every 5 minutes
- **Loading State:** Skeleton loaders while fetching

## Running the Platform

### 1. Start Backend
```bash
cd D:/Project
python start_platform.py
```

Server runs on `http://localhost:8000`

### 2. Access Dashboard
```
http://localhost:8000/web/experience/index.html
```

### 3. Test APIs
```bash
# Get all listings
curl http://localhost:8000/api/experience/listings

# Get stats
curl http://localhost:8000/api/experience/stats

# Get categories
curl http://localhost:8000/api/experience/categories

# Trigger crawl
curl -X POST http://localhost:8000/api/experience/crawl
```

## Tech Stack

### Backend
- **Framework:** Flask 2.0+
- **Database:** SQLite (MVP) → PostgreSQL (production)
- **ORM:** SQLAlchemy
- **API:** RESTful JSON endpoints

### Frontend
- **HTML5 / CSS3 / Vanilla JavaScript**
- **Styling:** Tailwind CSS (CDN)
- **Icons:** Unicode emojis
- **Responsive:** Mobile-first design
- **State Management:** Client-side localStorage-ready

### Crawlers
- **Base Framework:** Python 3.11
- **Phase 5 Tech:** BeautifulSoup4, Selenium (planned)
- **Scheduling:** APScheduler (planned)

## Deployment

### Development
```bash
python start_platform.py
```

### Production (Planned)
```bash
# Docker setup
docker build -t experience-platform .
docker run -p 8000:8000 experience-platform

# Gunicorn + Nginx
gunicorn -w 4 -b 0.0.0.0:8000 backend.app:create_app()
```

## Future Enhancements

### Phase 2: Advanced Crawling
- [ ] BeautifulSoup web scraping
- [ ] Selenium for JavaScript-heavy sites
- [ ] Proxy rotation for rate limiting
- [ ] User-Agent rotation

### Phase 3: User Features
- [ ] User registration and authentication
- [ ] Saved listings and favorites
- [ ] Email notifications
- [ ] Custom alerts for deadline-based filtering

### Phase 4: Platform Expansion
- [ ] More Korean platforms (Wadiz, Toss, Kakao etc.)
- [ ] International platforms
- [ ] AI-based recommendation engine
- [ ] Sentiment analysis of rewards

### Phase 5: Mobile & Social
- [ ] React Native mobile app
- [ ] Integration with user's SNS accounts
- [ ] Auto-posting reviews to social media
- [ ] Collaborative reviewing features

## Known Limitations (MVP)

1. **Data is Dummy:** Phase 5 implements real crawlers
2. **No Persistence:** Each restart resets data (will add DB persistence)
3. **No Scheduling:** Manual refresh only (will add APScheduler)
4. **No Authentication:** Public access (will add auth in Phase 2)
5. **No Rate Limiting:** Can be called unlimited times (will add limits)

## Testing

### Unit Tests
```bash
pytest tests/unit/test_models.py
pytest tests/unit/test_experience_api.py
```

### Integration Tests
```bash
pytest tests/integration/test_experience_endpoints.py
```

### Manual Testing
```bash
# Test all endpoints
bash scripts/test_experience_api.sh
```

## Troubleshooting

### API returns 404
- Ensure Flask app is running: `python start_platform.py`
- Check URL format: `http://localhost:8000/api/experience/...`

### Dashboard shows no listings
- Open browser console (F12) to check for errors
- Verify API is accessible
- Try refreshing the page

### Crawl button shows loading forever
- Check network tab in DevTools
- Verify backend is responding to `/api/experience/crawl`

## Support

For issues or questions:
1. Check error messages in browser console (F12)
2. Check Flask server logs
3. Review this README
4. Check `/api/experience/stats` for platform health

## Credits

Created: 2026-02-25
Project: M-006 Korean Experience Platform
Team: SoftFactory Multi-Agent System
Version: 1.0 MVP
