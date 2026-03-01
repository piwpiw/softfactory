"""SeoulOuba Scraper - Scrape campaign listings from seoulouba.co.kr

SeoulOuba (서울오빠) is a Korean creator/influencer collaboration platform.
Campaign listings are at /campaign/ with filtering by category, channel, and region.

Structure (verified 2026-02-26):
  .campaign_wbox > li.campaign_content >
    div.load_campaign >
      a.load_blind_box[href]              — campaign detail link
        div.load_blind >
          div.load_blind_box              — image container (background-image or img)
      div.load_icon_box >
        div.icon_box                     — channel icons (blog, insta, youtube)
        p.i_like[idx]                    — campaign ID / favorite button
      div.load_info >
        div.com_icon >
          div.icon_tag                   — channel/category tags
        a[href] > strong.s_campaign_title — campaign title
        div.campaign_day_people >
          div.d_day > span               — deadline (D-day or date)
          div.recruit > span             — "신청 23 / 모집 5"

Pagination: /campaign/?page=2 or infinite scroll via AJAX
Categories: 맛집(378), 여행/숙박(379), 뷰티/패션(380), 문화/생활(381),
            테이크아웃(382), 배송형(383), 기자단(448), 구매평(449), 서비스(450)
Channels: 블로그(01), 인스타그램(03), 유튜브(04), 기타(06)
"""

import re
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlencode
from .base_scraper import BaseScraper

logger = logging.getLogger('review.scrapers')


class SeouloubaScraper(BaseScraper):
    """Scraper for seoulouba.co.kr - Korean creator collaboration platform."""

    # Category IDs for targeted scraping
    CATEGORIES = {
        'all': 'all',
        '맛집': '378',
        '여행/숙박': '379',
        '뷰티/패션': '380',
        '문화/생활': '381',
        '테이크아웃': '382',
        '배송형': '383',
        '기자단': '448',
        '구매평': '449',
        '서비스': '450',
    }

    def __init__(self):
        super().__init__('seoulouba', 'https://seoulouba.co.kr')
        self.session.headers.update({
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
            'Referer': 'https://seoulouba.co.kr/',
        })

    def parse_listings(self) -> List[Dict]:
        """
        Parse campaign listings from SeoulOuba.

        Iterates through pages of the /campaign/ listing and extracts
        campaign details using real CSS selectors.

        Returns:
            List of listing dictionaries
        """
        listings = []
        max_pages = 3

        logger.info(f"[{self.platform}] Starting to scrape listings from seoulouba.co.kr/campaign/ ...")

        for page in range(1, max_pages + 1):
            url = f"{self.base_url}/campaign/"
            params = {'page': page}

            logger.debug(f"[{self.platform}] Fetching page {page}: {url}")
            soup = self.fetch_page(url, params=params)

            if not soup:
                logger.warning(f"[{self.platform}] Failed to fetch page {page}, stopping")
                break

            # Campaign items: li.campaign_content
            items = soup.select('li.campaign_content')

            if not items:
                logger.info(f"[{self.platform}] No items found on page {page}, stopping pagination")
                break

            logger.debug(f"[{self.platform}] Found {len(items)} items on page {page}")

            for item in items:
                try:
                    listing = self._parse_item(item)
                    if listing and self.validate_listing(listing):
                        listings.append(listing)
                except Exception as e:
                    logger.error(f"[{self.platform}] Error parsing item: {e}")
                    continue

            self.rate_limit()

        saved_count = self.save_listings(listings)
        logger.info(f"[{self.platform}] Completed: {saved_count} new listings saved (total found: {len(listings)})")
        return listings

    def _parse_item(self, item) -> Optional[Dict]:
        """
        Parse a single campaign item from SeoulOuba listing.

        Args:
            item: BeautifulSoup element (li.campaign_content)

        Returns:
            Dictionary with listing data or None if parsing fails
        """
        try:
            # --- URL and external ID ---
            # Primary link: a.load_blind_box or the title link
            link_elem = item.select_one('a.load_blind_box')
            if not link_elem:
                link_elem = item.select_one('a[href*="/campaign/"]')
            if not link_elem:
                link_elem = item.select_one('a[href]')

            if not link_elem:
                return None

            raw_url = link_elem.get('href', '')
            url = urljoin(self.base_url, raw_url) if raw_url else ''

            # Extract campaign ID from URL: /campaign/?c=397125 -> 397125
            id_match = re.search(r'[?&]c=(\d+)', raw_url)
            external_id = ''

            if id_match:
                external_id = f"souba_{id_match.group(1)}"
            else:
                # Try from i_like element idx attribute
                like_elem = item.select_one('p.i_like[idx]')
                if like_elem:
                    idx = like_elem.get('idx', '')
                    if idx:
                        external_id = f"souba_{idx}"

            if not external_id:
                external_id = f"souba_{abs(hash(url)) % 10**8}"

            # --- Title ---
            title_elem = item.select_one('strong.s_campaign_title')
            if not title_elem:
                title_elem = item.select_one('.load_info a strong, .load_info a')

            title = title_elem.get_text(strip=True) if title_elem else ''

            if not title:
                return None

            # --- Image ---
            image_url = self._extract_image(item)

            # --- Deadline ---
            deadline = self._parse_deadline(item)

            # --- Recruitment numbers ---
            max_applicants, current_applicants = self._parse_recruit(item)

            # --- Category ---
            category = self._extract_category_from_title(title)

            # --- Brand ---
            brand = self._extract_brand(title)

            # --- Channel type ---
            channel_type = self._detect_channel(item, title)

            # --- Reward ---
            reward_type = '상품'  # SeoulOuba campaigns are typically product/service
            reward_value = 0

            # Check if title contains reward info
            reward_type, reward_value = self._parse_reward_from_title(title)

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
                'requirements': {
                    'current_applicants': current_applicants,
                    'channel_type': channel_type,
                    'source': 'seoulouba.co.kr',
                }
            }

        except Exception as e:
            logger.error(f"[{self.platform}] Error parsing item: {e}")
            return None

    def _extract_image(self, item) -> str:
        """
        Extract campaign image URL.

        SeoulOuba uses either <img> tags inside .load_blind_box
        or CSS background-image on the element.

        Args:
            item: BeautifulSoup element

        Returns:
            Image URL string
        """
        # Try img tag first
        img_elem = item.select_one('.load_blind img, .load_blind_box img, .load_campaign img')
        if img_elem:
            src = img_elem.get('src', '') or img_elem.get('data-src', '')
            if src:
                return urljoin(self.base_url, src) if not src.startswith('http') else src

        # Try background-image style
        blind_box = item.select_one('.load_blind_box, .load_blind')
        if blind_box:
            style = blind_box.get('style', '')
            bg_match = re.search(r"background-image\s*:\s*url\(['\"]?([^'\")\s]+)['\"]?\)", style)
            if bg_match:
                src = bg_match.group(1)
                return urljoin(self.base_url, src) if not src.startswith('http') else src

        return ''

    def _parse_deadline(self, item) -> datetime:
        """
        Parse deadline from the D-day element.

        Format: <div class="d_day"><span>D-5</span></div>
                or specific date text

        Args:
            item: BeautifulSoup element

        Returns:
            datetime of deadline
        """
        try:
            dday_elem = item.select_one('div.d_day')
            if not dday_elem:
                dday_elem = item.select_one('.campaign_day_people .d_day')

            if dday_elem:
                dday_text = dday_elem.get_text(strip=True)

                # D-day format: "D-5", "D - 3"
                dday_match = re.search(r'[Dd]\s*[-]\s*(\d+)', dday_text)
                if dday_match:
                    days = int(dday_match.group(1))
                    return datetime.utcnow() + timedelta(days=days)

                # "마감" (closed) or "마감임박" (closing soon)
                if '마감' in dday_text:
                    if '임박' in dday_text:
                        return datetime.utcnow() + timedelta(days=1)
                    return datetime.utcnow()

                # Date format: "2026-03-01" or "2026.03.01"
                date_match = re.search(r'(\d{4})[-./ ](\d{1,2})[-./ ](\d{1,2})', dday_text)
                if date_match:
                    try:
                        return datetime(
                            int(date_match.group(1)),
                            int(date_match.group(2)),
                            int(date_match.group(3))
                        )
                    except ValueError:
                        pass

                # Short date: "03.15" or "3/15"
                short_match = re.search(r'(\d{1,2})[./](\d{1,2})', dday_text)
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

            return datetime.utcnow() + timedelta(days=7)

        except Exception as e:
            logger.warning(f"[{self.platform}] Error parsing deadline: {e}")
            return datetime.utcnow() + timedelta(days=7)

    def _parse_recruit(self, item) -> tuple:
        """
        Parse recruitment numbers from item.

        Format: <div class="recruit"><span>신청 23 <span class="span_gray">/ 모집 5</span></span></div>

        Args:
            item: BeautifulSoup element

        Returns:
            Tuple of (max_applicants, current_applicants)
        """
        max_applicants = None
        current_applicants = None

        try:
            recruit_elem = item.select_one('div.recruit')
            if not recruit_elem:
                recruit_elem = item.select_one('.campaign_day_people .recruit')

            if recruit_elem:
                text = recruit_elem.get_text(strip=True)

                # Parse "신청 23 / 모집 5"
                applied_match = re.search(r'신청\s*(\d+)', text)
                if applied_match:
                    current_applicants = int(applied_match.group(1))

                total_match = re.search(r'모집\s*(\d+)', text)
                if total_match:
                    max_applicants = int(total_match.group(1))

        except Exception as e:
            logger.debug(f"[{self.platform}] Recruit parse error: {e}")

        return (max_applicants, current_applicants)

    def _extract_category_from_title(self, title: str) -> str:
        """
        Extract category from campaign title.

        SeoulOuba titles often follow the pattern:
        [Channel][Region] Store/Brand Name

        Args:
            title: Campaign title

        Returns:
            Category string
        """
        title_lower = title.lower()

        categories = {
            '맛집': ['맛집', '음식', '식당', '레스토랑', '카페', '커피', '디저트',
                     '고기', '삼겹살', '치킨', '곱창', '초밥', '맥주', '포차', '주점',
                     '파스타', '피자', '국밥', '갈비'],
            '뷰티': ['뷰티', '화장품', '스킨케어', '메이크업', '향수', '네일', '헤어',
                     '미용실', '에스테틱', '속눈썹', '왁싱'],
            '패션': ['패션', '의류', '옷', '신발', '가방', '액세서리', '주얼리', '스포츠'],
            '여행': ['여행', '호텔', '숙박', '펜션', '리조트', '관광', '투어', '글램핑'],
            '배송형': ['배송', '택배', '온라인', '제품'],
            '서비스': ['서비스', '앱', '어플', '웹사이트', '플랫폼'],
            '문화/생활': ['문화', '생활', '인테리어', '운동', '헬스', '요가', '필라테스', '레저'],
        }

        for cat, keywords in categories.items():
            if any(kw in title_lower for kw in keywords):
                return cat

        # Default: try to guess from location mentions (implies 맛집/visit type)
        location_pattern = re.search(r'\[(서울|부산|대구|인천|광주|대전|울산|경기|강남|홍대|이태원|신촌|강원|제주)', title)
        if location_pattern:
            return '맛집'  # Location-based campaigns are often restaurants

        return '기타'

    def _extract_brand(self, title: str) -> str:
        """
        Extract brand/store name from title.

        SeoulOuba titles: [Channel][Region] StoreName
        E.g.: "[블로그+릴스][부산] 광안어썸" -> "광안어썸"
              "[강남] 더막창스 강남본점" -> "더막창스 강남본점"

        Args:
            title: Campaign title

        Returns:
            Brand/store name
        """
        # Remove all bracketed content
        clean_title = re.sub(r'\[[^\]]*\]', '', title).strip()

        if clean_title:
            return clean_title

        return 'Unknown'

    def _detect_channel(self, item, title: str) -> str:
        """
        Detect the SNS channel type from icon or title.

        Args:
            item: BeautifulSoup element
            title: Campaign title

        Returns:
            Channel type string
        """
        # Check icon_tag for channel info
        icon_tag = item.select_one('div.icon_tag')
        if icon_tag:
            tag_text = icon_tag.get_text(strip=True).lower()
            if '인스타' in tag_text or 'instagram' in tag_text:
                return '인스타그램'
            if '유튜브' in tag_text or 'youtube' in tag_text:
                return '유튜브'
            if '블로그' in tag_text or 'blog' in tag_text:
                return '블로그'
            if '구매평' in tag_text:
                return '구매평'

        # Check icon_box for channel icons
        icon_box = item.select_one('div.icon_box')
        if icon_box:
            icon_img = icon_box.select_one('img')
            if icon_img:
                alt = (icon_img.get('alt', '') + icon_img.get('src', '')).lower()
                if 'insta' in alt:
                    return '인스타그램'
                if 'youtube' in alt:
                    return '유튜브'
                if 'blog' in alt:
                    return '블로그'

        # Fallback: detect from title
        title_lower = title.lower()
        if '인스타' in title_lower or '릴스' in title_lower:
            return '인스타그램'
        if '유튜브' in title_lower:
            return '유튜브'
        if '블로그' in title_lower:
            return '블로그'
        if '구매평' in title_lower:
            return '구매평'

        return '블로그'  # Default

    def _parse_reward_from_title(self, title: str) -> tuple:
        """
        Parse reward info from the title text.

        Args:
            title: Campaign title

        Returns:
            Tuple of (reward_type, reward_value)
        """
        reward_type = '상품'
        reward_value = 0

        # Check for monetary mentions
        won_match = re.search(r'([\d,]+)\s*원', title)
        if won_match:
            try:
                reward_value = int(won_match.group(1).replace(',', ''))
                reward_type = '금전'
            except ValueError:
                pass

        man_match = re.search(r'(\d+)\s*만\s*원', title)
        if man_match:
            try:
                reward_value = int(man_match.group(1)) * 10000
                reward_type = '금전'
            except ValueError:
                pass

        return (reward_type, reward_value)
