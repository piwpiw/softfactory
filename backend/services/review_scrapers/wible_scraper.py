"""Wible Scraper - Scrape listings from wible.co.kr (체험단/인플루언서 캠페인)

NOTE: As of 2026-02-26, wible.co.kr is unreachable (connection timeout).
The domain may be defunct, rebranded, or temporarily down.

Revu.net (revu.net) was previously known as "Weble" (위블) — their mobile app
is still called "weble" in the Play Store. This scraper handles two scenarios:

1. If wible.co.kr comes back online: Uses best-effort selectors based on common
   Korean 체험단 platform patterns (GnuBoard/XpressEngine CMS templates)
2. Fallback: Searches Naver for indexed wible.co.kr pages

Common Korean 체험단 CMS structure (GnuBoard5):
  - Board listings: /bbs/board.php?bo_table=campaign
  - Gallery view: .gall_li > .gall_con > .gall_text_href
  - List view: .bo_tit > a
"""

import re
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from urllib.parse import urljoin
from .base_scraper import BaseScraper

logger = logging.getLogger('review.scrapers')


class WibleScraper(BaseScraper):
    """
    Scraper for wible.co.kr - Influencer and product review campaigns.

    Currently unreachable. Uses Naver search fallback to find any
    indexed wible.co.kr content.
    """

    # Common board paths for Korean 체험단 CMS platforms
    BOARD_PATHS = [
        '/campaign/',
        '/bbs/board.php?bo_table=campaign',
        '/bbs/board.php?bo_table=experience',
        '/bbs/board.php?bo_table=review',
    ]

    def __init__(self):
        super().__init__('wible', 'https://wible.co.kr')
        self.session.headers.update({
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        })
        # Reduce retries since site may be down
        self.max_retries = 2

    def parse_listings(self) -> List[Dict]:
        """
        Parse campaign listings from Wible.

        Strategy:
        1. Try direct site access with multiple board paths
        2. If unreachable, fall back to Naver search index

        Returns:
            List of listing dictionaries
        """
        listings = []
        max_pages = 3

        logger.info(f"[{self.platform}] Starting to scrape listings...")

        # Strategy 1: Direct site access
        site_reachable = False
        for path in self.BOARD_PATHS:
            url = f"{self.base_url}{path}"
            logger.debug(f"[{self.platform}] Trying direct access: {url}")
            soup = self.fetch_page(url)

            if soup:
                site_reachable = True
                items = self._find_listing_items(soup)
                if items:
                    logger.info(f"[{self.platform}] Found {len(items)} items at {path}")
                    for item_elem in items:
                        try:
                            listing = self._parse_cms_item(item_elem, url)
                            if listing and self.validate_listing(listing):
                                listings.append(listing)
                        except Exception as e:
                            logger.error(f"[{self.platform}] Error parsing item: {e}")
                    break  # Found working path
            self.rate_limit()

        # Paginate if site is reachable and we found a working path
        if site_reachable and listings:
            working_path = self.BOARD_PATHS[0]  # Use first successful path
            for page in range(2, max_pages + 1):
                url = f"{self.base_url}{working_path}"
                params = {'page': page}
                soup = self.fetch_page(url, params=params)
                if not soup:
                    break
                items = self._find_listing_items(soup)
                if not items:
                    break
                for item_elem in items:
                    try:
                        listing = self._parse_cms_item(item_elem, url)
                        if listing and self.validate_listing(listing):
                            listings.append(listing)
                    except Exception as e:
                        logger.error(f"[{self.platform}] Error parsing item: {e}")
                self.rate_limit()

        # Strategy 2: Naver search fallback
        if not listings:
            logger.info(f"[{self.platform}] Site unreachable or no items, using Naver search fallback")
            listings = self._naver_search_fallback(max_pages)

        saved_count = self.save_listings(listings)
        logger.info(f"[{self.platform}] Completed: {saved_count} new listings saved (total found: {len(listings)})")
        return listings

    def _find_listing_items(self, soup) -> list:
        """
        Find listing items using common Korean CMS selectors.

        Tries multiple common patterns used by GnuBoard5, XpressEngine,
        and custom Korean 체험단 platforms.

        Args:
            soup: BeautifulSoup object

        Returns:
            List of BeautifulSoup elements
        """
        # Try various common Korean CMS listing selectors (most specific first)
        selector_options = [
            'li.campaign_content',           # SeoulOuba-style
            'div.item',                       # ReviewPlace-style
            '.campaign_list .item',           # Generic campaign list
            '.gall_li',                       # GnuBoard gallery view
            '.bo_tit',                        # GnuBoard list view title
            'li.list-item',                   # Generic list item
            '.board-list-body tr',            # Table-based board
            '[class*="campaign"] [class*="item"]',  # Fuzzy campaign item
            '.card, .listing-card',           # Card layout
        ]

        for selector in selector_options:
            items = soup.select(selector)
            if items and len(items) > 1:  # Need at least 2 to be a real listing
                return items

        return []

    def _parse_cms_item(self, item, base_url: str) -> Optional[Dict]:
        """
        Parse a listing item using common Korean CMS patterns.

        Args:
            item: BeautifulSoup element
            base_url: Base URL for resolving relative links

        Returns:
            Dictionary with listing data or None
        """
        try:
            # --- URL ---
            link_elem = item.select_one('a[href]')
            if not link_elem:
                return None

            raw_url = link_elem.get('href', '')
            url = urljoin(self.base_url, raw_url) if raw_url else ''

            # --- Title ---
            title_candidates = [
                item.select_one('.s_campaign_title, .tit, .title, .bo_tit a, .gall_text_href'),
                item.select_one('strong, h3, h4'),
                link_elem,
            ]
            title = ''
            for elem in title_candidates:
                if elem:
                    title = elem.get_text(strip=True)
                    if title and len(title) > 3:
                        break

            if not title:
                return None

            # --- External ID ---
            id_match = re.search(r'[?&](c|wr_id|id|no)=(\d+)', raw_url)
            external_id = f"wible_{id_match.group(2)}" if id_match else f"wible_{abs(hash(url)) % 10**8}"

            # --- Image ---
            img_elem = item.select_one('img')
            image_url = ''
            if img_elem:
                image_url = img_elem.get('src', '') or img_elem.get('data-src', '')
                if image_url and not image_url.startswith('http'):
                    image_url = urljoin(self.base_url, image_url)

            # --- Deadline ---
            deadline = self._parse_deadline_from_item(item)

            # --- Recruitment ---
            max_applicants = self._parse_max_applicants(item)

            # --- Category & Brand ---
            category = self._extract_category(title)
            brand = self._extract_brand(title)

            # --- Reward ---
            reward_type, reward_value = self._parse_reward(title)

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
                'max_applicants': max_applicants,
                'requirements': {'source': 'wible.co.kr'}
            }

        except Exception as e:
            logger.error(f"[{self.platform}] Error parsing CMS item: {e}")
            return None

    def _naver_search_fallback(self, max_pages: int) -> List[Dict]:
        """
        Search Naver for indexed wible.co.kr pages.

        Args:
            max_pages: Maximum search pages

        Returns:
            List of listing dictionaries
        """
        listings = []
        search_url = 'https://search.naver.com/search.naver'

        for page in range(1, max_pages + 1):
            start = (page - 1) * 10 + 1
            params = {
                'where': 'webkr',
                'query': 'site:wible.co.kr 체험단',
                'start': start,
            }

            soup = self.fetch_page(search_url, params=params)
            if not soup:
                break

            # Parse Naver web search results
            items = soup.select('li.bx, li.lst')
            if not items:
                break

            for item in items:
                try:
                    link = item.select_one('a[href*="wible.co.kr"]')
                    if not link:
                        link = item.select_one('a.lnk_tit, a[href]')
                    if not link:
                        continue

                    url = link.get('href', '')
                    if 'wible.co.kr' not in url:
                        continue

                    title = link.get_text(strip=True)
                    if not title:
                        continue

                    id_match = re.search(r'[?&](c|id|no)=(\d+)', url)
                    external_id = f"wible_n_{id_match.group(2)}" if id_match else f"wible_n_{abs(hash(url)) % 10**8}"

                    desc_elem = item.select_one('.dsc_txt, .link_desc, .desc')
                    description = desc_elem.get_text(strip=True) if desc_elem else ''

                    combined = f"{title} {description}"

                    listings.append({
                        'external_id': external_id,
                        'title': title,
                        'brand': self._extract_brand(title),
                        'category': self._extract_category(title),
                        'reward_type': '상품',
                        'reward_value': 0,
                        'deadline': datetime.utcnow() + timedelta(days=7),
                        'url': url,
                        'image_url': '',
                        'requirements': {'source': 'wible.co.kr (via Naver)'}
                    })
                except Exception as e:
                    logger.error(f"[{self.platform}] Naver fallback parse error: {e}")

            self.rate_limit()

        return listings

    def _parse_deadline_from_item(self, item) -> datetime:
        """Parse deadline from item using various selector patterns."""
        try:
            # Try common deadline selectors
            for selector in ['.d_day', '.deadline', '.end-date', '.date', '[class*="day"]']:
                elem = item.select_one(selector)
                if elem:
                    text = elem.get_text(strip=True)
                    dday_match = re.search(r'[Dd]\s*[-]\s*(\d+)', text)
                    if dday_match:
                        return datetime.utcnow() + timedelta(days=int(dday_match.group(1)))

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

            return datetime.utcnow() + timedelta(days=7)
        except Exception:
            return datetime.utcnow() + timedelta(days=7)

    def _parse_max_applicants(self, item) -> Optional[int]:
        """Parse max applicant count from item."""
        try:
            for selector in ['.recruit', '.applicants', '[class*="recruit"]', '[class*="모집"]']:
                elem = item.select_one(selector)
                if elem:
                    text = elem.get_text(strip=True)
                    total_match = re.search(r'모집\s*(\d+)', text)
                    if total_match:
                        return int(total_match.group(1))
                    num_match = re.search(r'/\s*(\d+)\s*명?', text)
                    if num_match:
                        return int(num_match.group(1))
            return None
        except Exception:
            return None

    def _extract_category(self, title: str) -> str:
        """Extract category from title text."""
        text = title.lower()
        categories = {
            '맛집': ['맛집', '음식', '식당', '카페', '커피', '고기', '치킨'],
            '뷰티': ['뷰티', '화장품', '스킨케어', '크림', '세럼'],
            '패션': ['패션', '의류', '옷', '신발'],
            '식품': ['식품', '건강식품', '영양제', '밀키트'],
            '생활': ['생활', '인테리어', '가구'],
        }
        for cat, keywords in categories.items():
            if any(kw in text for kw in keywords):
                return cat
        return '기타'

    def _extract_brand(self, title: str) -> str:
        """Extract brand name from title."""
        clean = re.sub(r'\[[^\]]*\]', '', title).strip()
        return clean if clean else 'Unknown'

    def _parse_reward(self, title: str) -> tuple:
        """Parse reward from title text."""
        won_match = re.search(r'([\d,]+)\s*원', title)
        if won_match:
            try:
                return ('금전', int(won_match.group(1).replace(',', '')))
            except ValueError:
                pass
        man_match = re.search(r'(\d+)\s*만\s*원', title)
        if man_match:
            try:
                return ('금전', int(man_match.group(1)) * 10000)
            except ValueError:
                pass
        return ('상품', 0)
