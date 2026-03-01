"""Naver Blog Scraper - Scrape experience campaign posts from Naver Blog Section

Naver Blog Section (section.blog.naver.com) provides a search interface for
blog posts. We search for "체험단 모집" (experience campaign recruitment) to find
campaign announcement posts.

Structure (verified 2026-02-26 from section.blog.naver.com/Search/Post.naver):
  .post_list_wrap > .list > div.item >
    a[href]                — link to blog post
    div.img_area > img     — thumbnail image
    div.text_area >
      .title               — post title (with search keyword highlighting)
      .desc                — post description/snippet
    .blogname              — blog author name
    .category              — post category (if available)
    .pagination_area       — pagination links

Alternative: Naver search API (search.naver.com) returns blog results with:
  li.lst > .lnk_tit (title), .dsc_area (description), .lnk_thumb > img

This scraper uses both approaches for maximum coverage.
"""

import re
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from urllib.parse import urljoin, quote, urlencode
from .base_scraper import BaseScraper

logger = logging.getLogger('review.scrapers')


class NaverScraper(BaseScraper):
    """
    Scraper for Naver Blog - Experience and product review campaign posts.

    Uses two data sources:
    1. section.blog.naver.com - Blog section search (primary)
    2. search.naver.com - Naver web search blog tab (fallback)
    """

    BLOG_SECTION_URL = 'https://section.blog.naver.com/Search/Post.naver'
    NAVER_SEARCH_URL = 'https://search.naver.com/search.naver'

    # Search queries for different campaign types
    SEARCH_QUERIES = [
        '체험단 모집',
        '블로그 체험단 신청',
        '인스타 체험단 모집중',
    ]

    def __init__(self):
        super().__init__('naver', 'https://section.blog.naver.com')
        self.session.headers.update({
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        })

    def parse_listings(self) -> List[Dict]:
        """
        Parse experience campaign blog posts from Naver.

        Searches Naver Blog Section for campaign recruitment posts
        and extracts relevant data.

        Returns:
            List of listing dictionaries
        """
        listings = []
        max_pages = 3

        logger.info(f"[{self.platform}] Starting to scrape Naver blog campaign posts...")

        # Strategy 1: Blog Section search
        for query in self.SEARCH_QUERIES:
            section_listings = self._scrape_blog_section(query, max_pages)
            for listing in section_listings:
                if not any(l['external_id'] == listing['external_id'] for l in listings):
                    listings.append(listing)

        # Strategy 2: Naver web search (blog tab) as fallback
        if len(listings) < 10:
            search_listings = self._scrape_naver_search(max_pages)
            for listing in search_listings:
                if not any(l['external_id'] == listing['external_id'] for l in listings):
                    listings.append(listing)

        saved_count = self.save_listings(listings)
        logger.info(f"[{self.platform}] Completed: {saved_count} new listings saved (total found: {len(listings)})")
        return listings

    def _scrape_blog_section(self, query: str, max_pages: int) -> List[Dict]:
        """
        Scrape blog posts from section.blog.naver.com search.

        Args:
            query: Search keyword
            max_pages: Maximum pages to scrape

        Returns:
            List of listing dictionaries
        """
        listings = []

        for page in range(1, max_pages + 1):
            params = {
                'pageNo': page,
                'rangeType': 'ALL',
                'orderBy': 'sim',  # similarity (relevance)
                'keyword': query,
            }

            logger.debug(f"[{self.platform}] Blog Section search: '{query}' page {page}")

            # Set referer for CSRF protection
            self.session.headers['Referer'] = (
                f'{self.BLOG_SECTION_URL}?{urlencode(params)}'
            )

            soup = self.fetch_page(self.BLOG_SECTION_URL, params=params)

            if not soup:
                logger.warning(f"[{self.platform}] Failed to fetch blog section page {page}")
                break

            # Find post list container
            post_list = soup.select_one('.post_list_wrap .list')
            if not post_list:
                post_list = soup.select_one('.post_list_wrap')

            if not post_list:
                logger.debug(f"[{self.platform}] No post list found on page {page}")
                break

            # Select individual post items
            items = post_list.select('div.item, li.item')

            if not items:
                logger.debug(f"[{self.platform}] No items found on page {page}")
                break

            logger.debug(f"[{self.platform}] Found {len(items)} blog posts on page {page}")

            for item in items:
                try:
                    listing = self._parse_blog_section_item(item)
                    if listing and self.validate_listing(listing):
                        listings.append(listing)
                except Exception as e:
                    logger.error(f"[{self.platform}] Error parsing blog item: {e}")
                    continue

            self.rate_limit()

        return listings

    def _parse_blog_section_item(self, item) -> Optional[Dict]:
        """
        Parse a single blog post from section.blog.naver.com search results.

        Args:
            item: BeautifulSoup element (div.item)

        Returns:
            Dictionary with listing data or None
        """
        try:
            # --- URL ---
            link_elem = item.select_one('a[href]')
            if not link_elem:
                return None

            url = link_elem.get('href', '')
            if url and not url.startswith('http'):
                url = urljoin(self.base_url, url)

            if not url:
                return None

            # --- Title ---
            title_elem = item.select_one('.title')
            if not title_elem:
                title_elem = item.select_one('a .tit, .text_area .title')
            title = title_elem.get_text(strip=True) if title_elem else ''

            if not title:
                title = link_elem.get_text(strip=True)

            # Filter: only include posts that look like campaign announcements
            if not self._is_campaign_post(title):
                return None

            # --- Description ---
            desc_elem = item.select_one('.desc')
            if not desc_elem:
                desc_elem = item.select_one('.text_area .desc, .desc_area')
            description = desc_elem.get_text(strip=True) if desc_elem else ''

            # --- Blog author ---
            blog_name_elem = item.select_one('.blogname')
            if not blog_name_elem:
                blog_name_elem = item.select_one('.nickname, .name')
            blog_name = blog_name_elem.get_text(strip=True) if blog_name_elem else 'Unknown'

            # --- Image ---
            img_elem = item.select_one('.img_area img, img')
            image_url = ''
            if img_elem:
                image_url = (
                    img_elem.get('src', '') or
                    img_elem.get('data-src', '') or
                    img_elem.get('data-lazysrc', '')
                )

            # --- External ID ---
            # Extract blog post ID from URL
            # URL formats: https://blog.naver.com/user/12345 or https://m.blog.naver.com/user/12345
            post_id_match = re.search(r'blog\.naver\.com/([^/]+)/(\d+)', url)
            if post_id_match:
                external_id = f"naver_{post_id_match.group(1)}_{post_id_match.group(2)}"
            else:
                external_id = f"naver_{abs(hash(url)) % 10**8}"

            # --- Extract campaign details from title + description ---
            combined_text = f"{title} {description}"
            brand = self._extract_brand(combined_text)
            category = self._extract_category(combined_text)
            reward_type, reward_value = self._parse_reward(combined_text)
            deadline = self._parse_deadline(combined_text)

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
                    'blog_author': blog_name,
                    'source': 'Naver Blog Section',
                }
            }

        except Exception as e:
            logger.error(f"[{self.platform}] Error parsing blog section item: {e}")
            return None

    def _scrape_naver_search(self, max_pages: int) -> List[Dict]:
        """
        Fallback: Scrape blog results from Naver web search.

        Args:
            max_pages: Maximum pages to scrape

        Returns:
            List of listing dictionaries
        """
        listings = []

        for page in range(1, max_pages + 1):
            start = (page - 1) * 10 + 1
            params = {
                'where': 'blog',
                'query': '체험단 모집 블로그',
                'start': start,
            }

            logger.debug(f"[{self.platform}] Naver web search page {page}")
            soup = self.fetch_page(self.NAVER_SEARCH_URL, params=params)

            if not soup:
                break

            # Naver blog search results: .fds-ugc-single-intention-item-list or fallback
            items = soup.select('.fds-ugc-single-intention-item-list > div')
            if not items:
                items = soup.select('li.lst')
            if not items:
                # Try the newer FDS structure
                items = soup.select('.lst_item')

            if not items:
                logger.debug(f"[{self.platform}] No search results on page {page}")
                break

            for item in items:
                try:
                    listing = self._parse_naver_search_item(item)
                    if listing and self.validate_listing(listing):
                        listings.append(listing)
                except Exception as e:
                    logger.error(f"[{self.platform}] Error parsing search item: {e}")

            self.rate_limit()

        return listings

    def _parse_naver_search_item(self, item) -> Optional[Dict]:
        """
        Parse a single blog search result from Naver web search.

        Naver search results use various class names including:
        - .lnk_tit / .link_tit — title link
        - .dsc_area / .desc_area — description
        - .lnk_thumb — thumbnail link
        - img.img_thumb — thumbnail image

        Args:
            item: BeautifulSoup element

        Returns:
            Dictionary with listing data or None
        """
        try:
            # --- URL ---
            link_elem = item.select_one(
                'a.lnk_tit, a.link_tit, a[href*="blog.naver.com"], a[href]'
            )
            if not link_elem:
                return None

            url = link_elem.get('href', '')
            if not url or 'blog.naver.com' not in url:
                # Skip non-blog results
                return None

            # --- Title ---
            title = link_elem.get_text(strip=True)
            if not title:
                return None

            # Filter out non-campaign posts
            if not self._is_campaign_post(title):
                return None

            # --- Description ---
            desc_elem = item.select_one('.dsc_area, .desc_area, .link_desc')
            description = desc_elem.get_text(strip=True) if desc_elem else ''

            # --- Image ---
            img_elem = item.select_one('img.img_thumb, .lnk_thumb img, img')
            image_url = ''
            if img_elem:
                image_url = (
                    img_elem.get('src', '') or
                    img_elem.get('data-lazysrc', '')
                )

            # --- External ID ---
            post_id_match = re.search(r'blog\.naver\.com/([^/?&]+)/(\d+)', url)
            if post_id_match:
                external_id = f"naver_{post_id_match.group(1)}_{post_id_match.group(2)}"
            else:
                external_id = f"naver_s_{abs(hash(url)) % 10**8}"

            # --- Extract structured data ---
            combined_text = f"{title} {description}"
            brand = self._extract_brand(combined_text)
            category = self._extract_category(combined_text)
            reward_type, reward_value = self._parse_reward(combined_text)
            deadline = self._parse_deadline(combined_text)

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
                'requirements': {'source': 'Naver Blog Search'}
            }

        except Exception as e:
            logger.error(f"[{self.platform}] Error parsing search item: {e}")
            return None

    def _is_campaign_post(self, title: str) -> bool:
        """
        Check if a blog post title indicates a campaign announcement.

        Filters out general reviews, personal blogs, etc.

        Args:
            title: Post title

        Returns:
            True if likely a campaign/recruitment post
        """
        title_lower = title.lower()

        # Must contain campaign-related keywords
        campaign_keywords = [
            '체험단', '모집', '신청', '리뷰어', '서포터즈',
            '인플루언서', '블로거', '캠페인', '원정대',
            '무료체험', '리뷰단', '체험', '협찬',
        ]

        return any(kw in title_lower for kw in campaign_keywords)

    def _extract_brand(self, text: str) -> str:
        """Extract brand name from text."""
        # Pattern: [Brand] in brackets
        bracket_match = re.search(r'\[([^\]]{2,20})\]', text)
        if bracket_match:
            candidate = bracket_match.group(1)
            skip = ['블로그', '인스타', '유튜브', '틱톡', '체험단', '모집', '서울', '부산',
                     '대구', '인천', '광주', '대전', '울산', '경기', '강원']
            if not any(s in candidate for s in skip):
                return candidate

        # Well-known Korean brands
        brands = {
            '삼성': '삼성', 'samsung': '삼성',
            '롯데': '롯데', 'LG': 'LG', 'lg': 'LG',
            '현대': '현대', 'SK': 'SK', 'CJ': 'CJ', 'cj': 'CJ',
            '이마트': '이마트', 'GS': 'GS',
            '올리브영': '올리브영', '쿠팡': '쿠팡',
        }
        for keyword, brand in brands.items():
            if keyword in text:
                return brand

        return 'Unknown'

    def _extract_category(self, text: str) -> str:
        """Extract product category from text."""
        text_lower = text.lower()

        categories = {
            '맛집': ['맛집', '음식', '식당', '레스토랑', '카페', '커피', '디저트', '베이커리', '치킨', '고기'],
            '뷰티': ['뷰티', '화장품', '스킨케어', '메이크업', '향수', '네일', '헤어', '미용', '패치', '크림'],
            '패션': ['패션', '의류', '옷', '신발', '가방', '주얼리', '스타일'],
            '여행': ['여행', '호텔', '숙박', '펜션', '리조트', '투어'],
            '식품': ['식품', '건강식품', '영양제', '다이어트', '밀키트', '간식', '음료'],
            '생활': ['생활용품', '인테리어', '가구', '주방', '세제', '청소', '디퓨저'],
            '전자': ['전자', '가전', '스마트폰', 'IT', '앱', '가전제품'],
            '육아': ['육아', '유아', '아이', '키즈', '아기'],
        }

        for cat, keywords in categories.items():
            if any(kw in text_lower for kw in keywords):
                return cat

        return '기타'

    def _parse_reward(self, text: str) -> tuple:
        """Parse reward information from text."""
        reward_type = '상품'
        reward_value = 0

        if not text:
            return (reward_type, reward_value)

        # Monetary value
        won_match = re.search(r'([\d,]+)\s*원', text)
        if won_match:
            try:
                val = int(won_match.group(1).replace(',', ''))
                if val >= 1000:
                    reward_value = val
                    reward_type = '금전'
            except ValueError:
                pass

        # "X만원" format
        man_match = re.search(r'(\d+)\s*만\s*원', text)
        if man_match:
            try:
                reward_value = int(man_match.group(1)) * 10000
                reward_type = '금전'
            except ValueError:
                pass

        # Point value
        if reward_value == 0:
            point_match = re.search(r'([\d,]+)\s*[Pp포]', text)
            if point_match:
                try:
                    reward_value = int(point_match.group(1).replace(',', ''))
                    reward_type = '포인트'
                except ValueError:
                    pass

        if reward_value == 0 and ('상품' in text or '제공' in text or '무료' in text):
            reward_type = '상품'

        return (reward_type, reward_value)

    def _parse_deadline(self, text: str) -> datetime:
        """Parse deadline from text content."""
        if not text:
            return datetime.utcnow() + timedelta(days=14)

        # D-day format
        dday_match = re.search(r'[Dd]\s*[-]\s*(\d+)', text)
        if dday_match:
            try:
                return datetime.utcnow() + timedelta(days=int(dday_match.group(1)))
            except ValueError:
                pass

        # Full date: 2026-03-01, 2026.03.01
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

        # Korean date: "3월 15일까지"
        kr_match = re.search(r'(\d{1,2})월\s*(\d{1,2})일', text)
        if kr_match:
            try:
                now = datetime.utcnow()
                month = int(kr_match.group(1))
                day = int(kr_match.group(2))
                year = now.year if month >= now.month else now.year + 1
                return datetime(year, month, day)
            except ValueError:
                pass

        # Short date: ~3.7
        short_match = re.search(r'~?\s*(\d{1,2})\.(\d{1,2})', text)
        if short_match:
            try:
                now = datetime.utcnow()
                month = int(short_match.group(1))
                day = int(short_match.group(2))
                if 1 <= month <= 12 and 1 <= day <= 31:
                    year = now.year if month >= now.month else now.year + 1
                    return datetime(year, month, day)
            except ValueError:
                pass

        return datetime.utcnow() + timedelta(days=14)
