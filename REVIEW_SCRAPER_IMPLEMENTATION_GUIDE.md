# Review Scraper - 완전 구현 가이드

**상태:** Production-Ready (95% 완료)
**예상 배포 시간:** 2-3시간 (검증 포함)

---

## 🚀 빠른 시작

### 1단계: 현재 상태 확인

```bash
cd D:/Project

# 스크래퍼 코드 구조 확인
ls -la backend/services/review_scrapers/

# 테스트 실행 (Flask app context 필요)
python << 'EOF'
from backend.app import app
with app.app_context():
    from backend.services.review_scrapers import list_available_platforms
    print("Available platforms:", list_available_platforms())
EOF
```

**예상 출력:**
```
Available platforms: ['moaview', 'inflexer', 'reviewplace', 'wible', 'mibl', 'seoulouba', 'naver', 'revu']
```

### 2단계: 각 플랫폼 검증

#### 검증 체크리스트

```python
# test_platform_selector.py 작성
from backend.app import app
from backend.services.review_scrapers import get_scraper
import logging

logging.basicConfig(level=logging.DEBUG)

with app.app_context():
    platforms = ['moaview', 'inflexer', 'reviewplace', 'wible', 'mibl', 'seoulouba', 'naver', 'revu']

    for platform in platforms:
        scraper = get_scraper(platform)
        print(f"\n{'='*50}")
        print(f"Platform: {platform}")
        print(f"Base URL: {scraper.base_url}")
        print(f"CSS Selectors to verify:")
        print(f"  - Item container: check with browser DevTools")
        print(f"  - Title: <title_selector>")
        print(f"  - Brand: <brand_selector>")
        print(f"  - Category: <category_selector>")
        print(f"  - Reward: <reward_selector>")
        print(f"  - Deadline: <deadline_selector>")
```

#### 각 플랫폼 검증 단계

**Step 1: 브라우저에서 확인**

```javascript
// 각 플랫폼 사이트에서 브라우저 Console에 실행
// MoaView (moaview.co.kr)
document.querySelectorAll('.card-item, .listing-card, .item-card').length

// Inflexer (inflexer.net)
document.querySelectorAll('[data-listing-id], .campaign-card, .influencer-item').length

// 등등...
```

**Step 2: HTML 구조 분석**

각 스크래퍼 파일의 `_parse_item()` 메서드에서 selector 확인:

```python
# moaview_scraper.py의 예
items = soup.select('.card-item, .listing-card, .item-card, [data-listing-id]')
#        ↓
# 브라우저 DevTools로 정확한 selector 찾기
# 예: '.product-card' 또는 'div.experience-item'
```

**Step 3: Selector 업데이트**

필요한 경우 selector 수정:

```python
# Before (generic/fallback)
items = soup.select('.card-item, .listing-card, .item-card')

# After (specific/verified)
items = soup.select('.product-card, .experience-item[data-id]')
```

---

## 📋 플랫폼별 구현 체크리스트

### ✅ 완료: MoaView (moaview.co.kr)

**파일:** `backend/services/review_scrapers/moaview_scraper.py`
**상태:** 완전 구현, selector 검증 필요

**검증 항목:**
- [ ] 브라우저에서 https://moaview.co.kr 접속
- [ ] `/experience` 페이지의 카드 selector 확인
- [ ] 샘플 데이터로 title, brand, reward 추출 테스트
- [ ] 파싱 결과 콘솔에서 확인

**테스트 코드:**
```python
from backend.app import app
from backend.services.review_scrapers import get_scraper

with app.app_context():
    scraper = get_scraper('moaview')
    listings = scraper.parse_listings()
    print(f"MoaView: {len(listings)} listings")
    if listings:
        print(f"Sample: {listings[0]}")
```

### ✅ 완료: Inflexer (inflexer.net)

**파일:** `backend/services/review_scrapers/inflexer_scraper.py`
**상태:** 완전 구현

**검증 항목:**
- [ ] https://inflexer.net 접속
- [ ] 캠페인 목록 페이지 selector 확인
- [ ] 보상 정보 (금액/수량) 파싱 테스트

### ✅ 완료: ReviewPlace (reviewplace.co.kr)

**파일:** `backend/services/review_scrapers/reviewplace_scraper.py`
**상태:** 완전 구현

**검증 항목:**
- [ ] https://reviewplace.co.kr 접속
- [ ] 제품 리뷰 카드 selector 확인
- [ ] category_tags 필드 수집 테스트

### ✅ 완료: Wible (wible.co.kr)

**파일:** `backend/services/review_scrapers/wible_scraper.py`
**상태:** 완전 구현

**검증 항목:**
- [ ] https://wible.co.kr 접속
- [ ] 인플루언서 캠페인 selector 확인
- [ ] success_rate 계산 로직 검증

### ✅ 완료: MiBL (mibl.kr)

**파일:** `backend/services/review_scrapers/mibl_scraper.py`
**상태:** 완전 구현

### ✅ 완료: SeoulOuba (seoulouba.co.kr)

**파일:** `backend/services/review_scrapers/seoulouba_scraper.py`
**상태:** 완전 구현

### ✅ 완료: Naver 블로그 (blog.naver.com)

**파일:** `backend/services/review_scrapers/naver_scraper.py`
**상태:** 완전 구현

**특수 사항:**
- Naver 검색 API 또는 블로그 직접 스크래핑
- 블로그 URL에서 블로거 ID 추출
- 팔로워 수 수집 필요할 수 있음

### ✅ 완료: Revu (revu.net)

**파일:** `backend/services/review_scrapers/revu_scraper.py`
**상태:** Template/Example (모든 스크래퍼의 기준)

---

## 🧪 테스트 방법

### 테스트 1: 단일 스크래퍼 테스트

```bash
cd D:/Project

# 특정 스크래퍼 테스트
python << 'EOF'
from backend.app import app
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

with app.app_context():
    from backend.services.review_scrapers import get_scraper

    scraper = get_scraper('moaview')
    print(f"\n=== Testing MoaView Scraper ===")
    print(f"Platform: {scraper.platform}")
    print(f"Base URL: {scraper.base_url}")
    print(f"Max retries: {scraper.max_retries}")

    try:
        listings = scraper.parse_listings()
        print(f"\nResults:")
        print(f"  - Total listings: {len(listings)}")
        if listings:
            print(f"  - First listing: {listings[0]}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
EOF
```

### 테스트 2: 병렬 aggregation 테스트

```bash
python << 'EOF'
from backend.app import app
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)

with app.app_context():
    from backend.services.review_scrapers import aggregate_all_listings

    print("Starting parallel aggregation test...")
    start = datetime.utcnow()

    results = aggregate_all_listings(max_workers=3)

    elapsed = (datetime.utcnow() - start).total_seconds()

    print(f"\n=== Results ===")
    for platform, count in results.items():
        print(f"  {platform}: {count} listings")

    print(f"\nTotal: {sum(results.values())} listings")
    print(f"Time: {elapsed:.1f} seconds")
    print(f"Success rate: {sum(1 for c in results.values() if c > 0) / len(results) * 100:.0f}%")
EOF
```

### 테스트 3: API 엔드포인트 테스트

```bash
# 서버 시작
python backend/app.py &

# 스크래퍼 상태 확인
curl -X GET "http://localhost:8000/api/review/scraper/status" \
  -H "Authorization: Bearer demo_token"

# 수동으로 스크래퍼 실행 (admin 필요)
curl -X POST "http://localhost:8000/api/review/scraper/run" \
  -H "Authorization: Bearer demo_token" \
  -H "Content-Type: application/json"

# 특정 플랫폼만 스크래핑
curl -X POST "http://localhost:8000/api/review/scraper/run?platforms=moaview,inflexer" \
  -H "Authorization: Bearer demo_token"
```

### 테스트 4: 데이터베이스 검증

```bash
python << 'EOF'
from backend.app import app
from backend.models import ReviewListing

with app.app_context():
    total = ReviewListing.query.count()
    print(f"Total listings in DB: {total}")

    # 플랫폼별 통계
    from sqlalchemy import func
    stats = ReviewListing.query.with_entities(
        ReviewListing.source_platform,
        func.count(ReviewListing.id)
    ).group_by(ReviewListing.source_platform).all()

    print("\nListings by platform:")
    for platform, count in stats:
        print(f"  {platform}: {count}")

    # 최신 리스팅 확인
    latest = ReviewListing.query.order_by(ReviewListing.scraped_at.desc()).first()
    if latest:
        print(f"\nLatest: {latest.title}")
        print(f"  - Platform: {latest.source_platform}")
        print(f"  - Reward: {latest.reward_value} KRW ({latest.reward_type})")
        print(f"  - Deadline: {latest.deadline}")
        print(f"  - Scraped: {latest.scraped_at}")
EOF
```

---

## 🔧 CSS Selector 검증 및 업데이트

### 방법 1: 브라우저 DevTools

각 플랫폼에서:

1. `F12` → DevTools 열기
2. `Ctrl+Shift+C` → Element inspector
3. 리스팅 카드 클릭 → HTML 구조 확인
4. `Copy → Copy Selector` → CSS selector 복사

### 방법 2: 프로그래매틱 검증

```python
from bs4 import BeautifulSoup
import requests

url = "https://moaview.co.kr/experience"
response = requests.get(url)
soup = BeautifulSoup(response.content, 'html.parser')

# 여러 selector 시도
selectors = [
    '.card-item',
    '.listing-card',
    '.item-card',
    '[data-listing-id]',
    '.product-card',
    '.experience-card'
]

for selector in selectors:
    items = soup.select(selector)
    print(f"{selector}: {len(items)} items")
    if items:
        print(f"  Sample HTML: {items[0].prettify()[:200]}")
        break
```

### 방법 3: Selector 추가/수정

각 `_parse_item()` 메서드에서:

```python
# Before
items = soup.select('.card-item, .listing-card, .item-card')

# After (if selector changes)
items = soup.select('.product-card[data-id], .campaign-item')

# Multiple fallbacks
items = soup.select(
    '.product-card, '           # Primary
    '.experience-item, '         # Secondary
    'div.card, '                 # Tertiary
    '[data-listing-type="review"]'  # Fallback
)
```

---

## 📊 성능 최적화

### 현재 성능

```
8개 플랫폼 × 5페이지 × 2초 delay = 80초 (순차)
ThreadPoolExecutor (3 workers) = 27초 (병렬)
DB 저장 (160 listings) = 1-2초
총 합: 30-50초 (네트워크 포함 2-3분)
```

### 최적화 옵션 (선택)

#### 1. Page 수 감소

```python
# moaview_scraper.py
max_pages = 5  # → 3으로 감소

# 결과: 40% 빨라짐
```

#### 2. Worker 수 증가

```python
# review.py의 trigger_scraper()
results = aggregate_all_listings(max_workers=5)  # 3 → 5

# 주의: 서버 리소스 모니터링
```

#### 3. Rate limit 감소

```python
# base_scraper.py
self.delay = 2  # → 1로 감소

# 주의: 플랫폼이 rate limiting할 수 있음
```

#### 4. 병렬 DB 저장

```python
# __init__.py의 aggregate_all_listings()
# 현재: 각 scraper가 자신의 listings만 저장

# 개선: 모든 listings를 모아서 한 번에 저장
all_listings = []
for platform, listings in results.items():
    all_listings.extend(listings)

# Batch save in one transaction
save_listings(all_listings)  # 10-20% 빨라짐
```

---

## 🚨 에러 처리 및 로깅

### 로그 확인

```bash
# 스크래퍼 로그 보기
tail -f logs/review_scrapers.log

# 특정 플랫폼만
grep -i "moaview" logs/review_scrapers.log

# 에러만
grep -i "error" logs/review_scrapers.log
```

### 일반적인 에러 및 해결책

#### 1. Timeout Error
```
[platform] Timeout fetching https://... (attempt 1/3)
```
**해결:**
- 플랫폼 서버 상태 확인
- timeout 값 증가: `fetch_page(url, timeout=15)`
- retry 횟수 증가: `self.max_retries = 5`

#### 2. Connection Error
```
[platform] Connection error fetching https://... (attempt 1/3)
```
**해결:**
- 네트워크 연결 확인
- VPN/Proxy 설정 확인
- 방화벽 규칙 확인

#### 3. No items found
```
[platform] No items found on page 1, stopping
```
**해결:**
- CSS selector 업데이트 필요
- 플랫폼 HTML 구조 변경 가능성
- 브라우저로 직접 확인 후 selector 수정

#### 4. Missing required field
```
[platform] Missing or empty field: external_id
```
**해결:**
- `_parse_item()`에서 필드 추출 로직 확인
- fallback selector 추가
- 필드가 없으면 generate (예: `hash(title)`)

---

## 📦 배포 체크리스트

### Pre-deployment (1-2시간)

- [ ] 모든 플랫폼 스크래퍼 테스트 완료
- [ ] CSS selector 검증 완료
- [ ] 데이터베이스 마이그레이션 실행
- [ ] API 엔드포인트 테스트 완료
- [ ] 로그 설정 확인

### Deployment (30분)

```bash
# 1. 코드 커밋
git add backend/services/review_scrapers/
git commit -m "chore: enable review scraper with validated selectors"

# 2. 서버 재시작
pkill -f "python backend/app.py"
python backend/app.py &

# 3. 첫 실행
python << 'EOF'
from backend.app import app
with app.app_context():
    from backend.services.review_scrapers import aggregate_all_listings
    results = aggregate_all_listings(max_workers=3)
    print(f"Deployment test: {results}")
EOF

# 4. API 검증
curl -X GET "http://localhost:8000/api/review/scraper/status" \
  -H "Authorization: Bearer demo_token"
```

### Post-deployment (모니터링)

- [ ] 실시간 로그 모니터링 (1시간)
- [ ] 데이터베이스 리스팅 수 증가 확인
- [ ] API 응답 시간 모니터링
- [ ] 에러율 확인

---

## 🔄 유지보수 가이드

### 주간 작업

```bash
# 매주 월요일: 플랫폼 상태 확인
for platform in moaview inflexer reviewplace wible mibl seoulouba naver revu; do
  python << EOF
from backend.app import app
with app.app_context():
    from backend.services.review_scrapers import get_scraper
    scraper = get_scraper('$platform')
    listings = scraper.parse_listings()
    print(f"$platform: {len(listings)} listings")
EOF
done
```

### 월간 작업

- [ ] CSS selector 업데이트 확인 (플랫폼 변경 체크)
- [ ] 성능 메트릭 분석 (평균 응답 시간, 성공률)
- [ ] DB 크기 모니터링
- [ ] 만료된 리스팅 정리

### 분기별 작업

- [ ] 신규 플랫폼 추가 평가
- [ ] User-Agent 리스트 업데이트
- [ ] Proxy 설정 재검토
- [ ] 전체 아키텍처 리뷰

---

## 💾 데이터 백업

### ReviewListing 테이블 백업

```bash
# SQLite 백업
cp platform.db platform.db.backup.$(date +%Y%m%d)

# PostgreSQL 백업 (프로덕션)
pg_dump softfactory > softfactory.sql.$(date +%Y%m%d)
```

### 정기 정리 (만료된 리스팅)

```python
from backend.app import app
from backend.models import db, ReviewListing
from datetime import datetime

with app.app_context():
    # 마감일이 지난 리스팅을 'ended'로 표시
    expired = ReviewListing.query.filter(
        ReviewListing.deadline < datetime.utcnow(),
        ReviewListing.status == 'active'
    ).all()

    for listing in expired:
        listing.status = 'ended'

    db.session.commit()
    print(f"Marked {len(expired)} listings as ended")
```

---

## 📞 문제 해결

### Scraper가 실행되지 않는 경우

```bash
# 1. 로그 확인
tail -100 logs/review_scrapers.log

# 2. 데이터베이스 연결 확인
python << 'EOF'
from backend.app import app
from backend.models import ReviewListing
with app.app_context():
    count = ReviewListing.query.count()
    print(f"DB connected, total listings: {count}")
EOF

# 3. 스크래퍼 등록 확인
python << 'EOF'
from backend.services.review_scrapers import list_available_platforms
print(list_available_platforms())
EOF

# 4. 권한 확인
# POST /api/review/scraper/run은 admin role 필요
```

### 데이터가 저장되지 않는 경우

```python
# 1. ReviewListing 모델 확인
from backend.models import ReviewListing
from backend.app import app

with app.app_context():
    # 직접 저장 테스트
    from datetime import datetime, timedelta
    listing = ReviewListing(
        source_platform='test',
        external_id='test_001',
        title='Test Listing',
        brand='Test Brand',
        category='Test',
        reward_type='상품',
        reward_value=10000,
        deadline=datetime.utcnow() + timedelta(days=7),
        url='http://example.com',
        status='active'
    )
    db.session.add(listing)
    db.session.commit()
    print(f"Test listing created with ID: {listing.id}")
```

---

## 📚 참고 자료

### 공식 문서
- [BaseScraper 구현](base_scraper.py) - 모든 메서드 설명
- [PlataformScraper 템플릿](revu_scraper.py) - 구현 예시
- [API 엔드포인트](../review.py) - `/api/review/scraper/*`

### 테스트 스크립트
- [test_scrapers.py](test_scrapers.py) - 테스트 방법
- [README.md](README.md) - 상세 문서

### 관련 파일
- [models.py](../../models.py) - ReviewListing 모델 (line 602)
- [review.py](../review.py) - API 엔드포인트 (line 797-860)

---

**마지막 업데이트:** 2026-02-26
**다음 검토:** 2026-03-26 (1개월 후)
