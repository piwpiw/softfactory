"""Revu Scraper - Scrape experience campaigns from revu.net

Revu.net is a Single Page Application (AngularJS) with an authenticated API
at api.revu.net / api.weble.net. Since the API requires login, this scraper
uses two strategies:
1. Primary: Scrape the mobile web version which may render server-side
2. Fallback: Parse the sitemap or use Naver search indexed pages for revu.net

The scraper extracts campaign listings including title, brand, category,
reward details, deadline, and URL.
"""

import re
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlencode
from .base_scraper import BaseScraper

logger = logging.getLogger('review.scrapers')


class RevuScraper(BaseScraper):
    """
    Scraper for revu.net - Korea's largest experience/influencer campaign platform.

    Since revu.net is a full SPA (AngularJS), direct HTML scraping yields no content.
    Strategy:
    - Use Naver search to find indexed revu.net campaign pages
    - Parse the indexed content which contains campaign details
    - Extract structured data from search result snippets and cached pages
    """

    NAVER_SEARCH_URL = 'https://search.naver.com/search.naver'
    REVU_CAMPAIGN_PATTERN = re.compile(r'revu\.net/campaign/(\d+)')

    def __init__(self):
        super().__init__('revu', 'https://www.revu.net')
        # Update headers for Korean content
        self.session.headers.update({
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        })

    def parse_listings(self) -> List[Dict]:
        """
        Parse experience listings from Revu via Naver search index.

        Searches Naver for recently indexed revu.net campaign pages and
        extracts structured campaign data from search results.

        Returns:
            List of listing dictionaries
        """
        listings = []
        max_pages = 3

        logger.info(f"[{self.platform}] Starting to scrape listings via Naver search index...")

        # Search queries targeting different campaign types on revu.net
        search_queries = [
            'site:revu.net 체험단 모집',
            'site:revu.net 블로그 체험단',
            'site:revu.net 인스타 체험단',
        ]

        for query in search_queries:
            for page in range(1, max_pages + 1):
                start = (page - 1) * 10 + 1
                params = {
                    'where': 'webkr',
                    'query': query,
                    'start': start,
                }

                logger.debug(f"[{self.platform}] Searching: {query} (page {page})")
                soup = self.fetch_page(self.NAVER_SEARCH_URL, params=params)

                if not soup:
                    logger.warning(f"[{self.platform}] Failed to fetch search page {page}")
                    break

                # Naver web search results use .lst class items
                items = soup.select('li.bx')
                if not items:
                    # Fallback to older Naver search layout
                    items = soup.select('.lst')

                if not items:
                    logger.debug(f"[{self.platform}] No results for query: {query} page {page}")
                    break

                logger.debug(f"[{self.platform}] Found {len(items)} search results")

                for item in items:
                    try:
                        listing = self._parse_search_result(item)
                        if listing and self.validate_listing(listing):
                            # Deduplicate by external_id
                            if not any(l['external_id'] == listing['external_id'] for l in listings):
                                listings.append(listing)
                    except Exception as e:
                        logger.error(f"[{self.platform}] Error parsing search result: {e}")
                        continue

                self.rate_limit()

        # Also try direct campaign page scraping (mobile version)
        mobile_listings = self._try_mobile_scrape()
        for listing in mobile_listings:
            if not any(l['external_id'] == listing['external_id'] for l in listings):
                listings.append(listing)

        saved_count = self.save_listings(listings)
        logger.info(f"[{self.platform}] Completed: {saved_count} new listings saved (total found: {len(listings)})")

        return listings

    def _parse_search_result(self, item) -> Optional[Dict]:
        """
        Parse a single Naver search result for a revu.net campaign.

        Args:
            item: BeautifulSoup element representing a search result

        Returns:
            Dictionary with listing data or None if not a valid revu campaign
        """
        try:
            # Extract URL from search result link
            link_elem = item.select_one('a[href*="revu.net"]')
            if not link_elem:
                # Try any link in the result
                link_elem = item.select_one('a.link_tit, a.lnk_tit, a[href]')
            if not link_elem:
                return None

            url = link_elem.get('href', '')

            # Only process revu.net URLs
            if 'revu.net' not in url:
                return None

            # Extract campaign ID from URL
            match = self.REVU_CAMPAIGN_PATTERN.search(url)
            if match:
                external_id = f"revu_{match.group(1)}"
            else:
                external_id = f"revu_{abs(hash(url)) % 10**8}"

            # Extract title from search result
            title_elem = item.select_one('.lnk_tit, .link_tit, a.title_link, .tit, a[href]')
            title = title_elem.get_text(strip=True) if title_elem else ''

            if not title:
                title = link_elem.get_text(strip=True)

            # Clean up title - remove "레뷰" prefix if present
            title = re.sub(r'^레뷰\s*[-|:]\s*', '', title).strip()

            # Extract description/snippet
            desc_elem = item.select_one('.dsc_txt, .link_desc, .desc, .txt')
            description = desc_elem.get_text(strip=True) if desc_elem else ''

            # Try to extract brand from title or description
            brand = self._extract_brand(title, description)

            # Try to extract category
            category = self._extract_category(title, description)

            # Parse reward from description
            reward_type, reward_value = self._parse_reward(title + ' ' + description)

            # Parse deadline
            deadline = self._parse_deadline_text(title + ' ' + description)

            # Extract image if available
            img_elem = item.select_one('img.img_thumb, img[src*="revu"], img')
            image_url = ''
            if img_elem:
                image_url = img_elem.get('src', '') or img_elem.get('data-lazysrc', '')

            return {
                'external_id': external_id,
                'title': title,
                'brand': brand,
                'category': category,
                'reward_type': reward_type,
                'reward_value': reward_value,
                'deadline': deadline,
                'url': url,
                'image_url': image_url,
                'requirements': {
                    'source': 'revu.net (via Naver index)',
                    'platform_type': self._detect_platform_type(title),
                }
            }

        except Exception as e:
            logger.error(f"[{self.platform}] Error parsing search result: {e}")
            return None

    def _try_mobile_scrape(self) -> List[Dict]:
        """
        Attempt to scrape revu.net mobile version which may have
        server-side rendered content.

        Returns:
            List of listing dictionaries
        """
        listings = []
        try:
            # Try mobile user agent
            mobile_headers = {
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) '
                              'AppleWebKit/605.1.15 (KHTML, like Gecko) '
                              'Version/16.0 Mobile/15E148 Safari/604.1',
                'Accept-Language': 'ko-KR,ko;q=0.9',
            }
            self.session.headers.update(mobile_headers)

            # Try common campaign listing URLs
            for path in ['/campaign', '/campaigns', '/experience', '/']:
                url = f"https://m.revu.net{path}" if path != '/' else 'https://m.revu.net/'
                soup = self.fetch_page(url)

                if not soup:
                    continue

                # Look for any campaign-like content
                # Revu mobile may use different selectors
                items = soup.select(
                    '[class*="campaign"], [class*="item"], [class*="card"], '
                    '[data-campaign-id], .list-item, .campaign-item'
                )

                for item in items:
                    try:
                        listing = self._parse_mobile_item(item)
                        if listing and self.validate_listing(listing):
                            listings.append(listing)
                    except Exception as e:
                        logger.debug(f"[{self.platform}] Mobile parse error: {e}")

                if listings:
                    break

                self.rate_limit()

        except Exception as e:
            logger.debug(f"[{self.platform}] Mobile scrape failed: {e}")
        finally:
            # Restore desktop headers
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                              '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            })

        return listings

    def _parse_mobile_item(self, item) -> Optional[Dict]:
        """Parse a campaign item from mobile version."""
        try:
            link = item.select_one('a[href]')
            if not link:
                return None

            url = link.get('href', '')
            if url and not url.startswith('http'):
                url = urljoin('https://m.revu.net', url)

            title_elem = item.select_one('h3, .title, .name, [class*="title"]')
            title = title_elem.get_text(strip=True) if title_elem else item.get_text(strip=True)[:100]

            if not title or len(title) < 3:
                return None

            match = self.REVU_CAMPAIGN_PATTERN.search(url)
            external_id = f"revu_{match.group(1)}" if match else f"revu_m_{abs(hash(url)) % 10**8}"

            img_elem = item.select_one('img')
            image_url = img_elem.get('src', '') if img_elem else ''

            return {
                'external_id': external_id,
                'title': title,
                'brand': 'Unknown',
                'category': self._extract_category(title, ''),
                'reward_type': '상품',
                'reward_value': 0,
                'deadline': datetime.utcnow() + timedelta(days=7),
                'url': url,
                'image_url': image_url,
                'requirements': {'source': 'revu.net (mobile)'},
            }
        except Exception:
            return None

    def _extract_brand(self, title: str, description: str) -> str:
        """Extract brand name from title or description text."""
        text = f"{title} {description}"

        # Common patterns: [Brand] Title or Brand - Title
        bracket_match = re.search(r'\[([^\]]{2,20})\]', text)
        if bracket_match:
            candidate = bracket_match.group(1)
            # Filter out location/platform markers
            if not re.match(r'^(서울|부산|대구|인천|광주|대전|울산|경기|강원|충북|충남|전북|전남|경북|경남|제주|블로그|인스타|유튜브|틱톡)', candidate):
                return candidate

        return 'Unknown'

    def _extract_category(self, title: str, description: str) -> str:
        """Extract product category from text."""
        text = f"{title} {description}".lower()

        category_map = {
            '맛집': ['맛집', '음식', '식당', '레스토랑', '카페', '커피', '디저트', '베이커리', '고기', '삼겹살', '치킨'],
            '뷰티': ['뷰티', '화장품', '스킨케어', '메이크업', '향수', '네일', '헤어', '미용실', '에스테틱'],
            '패션': ['패션', '의류', '옷', '신발', '가방', '액세서리', '주얼리'],
            '여행': ['여행', '호텔', '숙박', '펜션', '리조트', '관광', '투어'],
            '식품': ['식품', '건강식품', '영양제', '다이어트', '밀키트', '간식'],
            '생활': ['생활용품', '인테리어', '가구', '주방', '세제', '청소'],
            '전자': ['전자', '가전', '스마트폰', 'IT', '앱', '가전제품'],
            '육아': ['육아', '유아', '아이', '키즈', '아기'],
        }

        for category, keywords in category_map.items():
            if any(kw in text for kw in keywords):
                return category

        return '기타'

    def _parse_reward(self, text: str) -> tuple:
        """Parse reward type and value from text."""
        reward_type = '상품'
        reward_value = 0

        if not text:
            return (reward_type, reward_value)

        # Check for monetary values (e.g., "50,000원", "5만원")
        won_match = re.search(r'(\d[\d,]*)\s*원', text)
        if won_match:
            try:
                reward_value = int(won_match.group(1).replace(',', ''))
                reward_type = '금전'
            except ValueError:
                pass

        man_match = re.search(r'(\d+)\s*만\s*원', text)
        if man_match:
            try:
                reward_value = int(man_match.group(1)) * 10000
                reward_type = '금전'
            except ValueError:
                pass

        # Check for point values (e.g., "10,000P")
        point_match = re.search(r'(\d[\d,]*)\s*[Pp포]', text)
        if point_match and reward_value == 0:
            try:
                reward_value = int(point_match.group(1).replace(',', ''))
                reward_type = '포인트'
            except ValueError:
                pass

        # If contains "상품" or "제공" without monetary value, it's a product
        if reward_value == 0 and ('상품' in text or '제공' in text or '무료' in text):
            reward_type = '상품'

        return (reward_type, reward_value)

    def _parse_deadline_text(self, text: str) -> datetime:
        """Parse deadline from text content."""
        if not text:
            return datetime.utcnow() + timedelta(days=7)

        # D-day format: "D-7", "D - 11"
        dday_match = re.search(r'[Dd]\s*[-]\s*(\d+)', text)
        if dday_match:
            try:
                days = int(dday_match.group(1))
                return datetime.utcnow() + timedelta(days=days)
            except ValueError:
                pass

        # Date format: "2026-03-01", "2026.03.01"
        date_match = re.search(r'(\d{4})[-./ ](\d{1,2})[-./ ](\d{1,2})', text)
        if date_match:
            try:
                return datetime(
                    int(date_match.group(1)),
                    int(date_match.group(2)),
                    int(date_match.group(3))
                )
            except ValueError:
                pass

        # Korean date: "3월 15일"
        kr_date_match = re.search(r'(\d{1,2})월\s*(\d{1,2})일', text)
        if kr_date_match:
            try:
                now = datetime.utcnow()
                month = int(kr_date_match.group(1))
                day = int(kr_date_match.group(2))
                year = now.year if month >= now.month else now.year + 1
                return datetime(year, month, day)
            except ValueError:
                pass

        # "~3.7까지" format
        until_match = re.search(r'~?\s*(\d{1,2})\.(\d{1,2})', text)
        if until_match:
            try:
                now = datetime.utcnow()
                month = int(until_match.group(1))
                day = int(until_match.group(2))
                year = now.year if month >= now.month else now.year + 1
                return datetime(year, month, day)
            except ValueError:
                pass

        return datetime.utcnow() + timedelta(days=7)

    def _detect_platform_type(self, title: str) -> str:
        """Detect which SNS platform the campaign targets."""
        title_lower = title.lower()

        if '인스타' in title_lower or 'instagram' in title_lower or '릴스' in title_lower:
            return '인스타그램'
        elif '유튜브' in title_lower or 'youtube' in title_lower:
            return '유튜브'
        elif '틱톡' in title_lower or 'tiktok' in title_lower:
            return '틱톡'
        elif '블로그' in title_lower or 'blog' in title_lower:
            return '블로그'
        elif '숏폼' in title_lower:
            return '숏폼'

        return '블로그'  # Default - most common on revu
