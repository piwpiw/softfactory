"""ReviewPlace Scraper - Scrape campaign listings from reviewplace.co.kr

ReviewPlace is a Korean review/experience campaign platform. The campaign listing
page is at /pr/ (or /bbs/board.php?bo_table=product). Each campaign item has:

Structure (verified 2026-02-26):
  #cmp_list > div.item > a[href] >
    div.img > img.thumbimg
    div.item_info >
      div.sns_icon > (blog_icon, insta_icon, youtube_icon, etc.)
      div.txt_wrap >
        p.tit       — campaign title
        p.txt       — reward/product description
      div.date_wrap >
        p.date > em.d_ico + text  — "D - 11" (days remaining)
        div.num > p > span        — "신청 2 / 30명" (applied/total)
      div.tag_wrap >
        div.txt_tag                — point/price tag "10,000P", "32,700P"

Pagination: /pr/?page=2
"""

import re
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from urllib.parse import urljoin
from .base_scraper import BaseScraper

logger = logging.getLogger('review.scrapers')


class ReviewPlaceScraper(BaseScraper):
    """Scraper for reviewplace.co.kr - Product review and experience campaigns."""

    def __init__(self):
        super().__init__('reviewplace', 'https://reviewplace.co.kr')
        self.session.headers.update({
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
            'Referer': 'https://reviewplace.co.kr/',
        })

    def parse_listings(self) -> List[Dict]:
        """
        Parse campaign listings from ReviewPlace.

        Iterates through pages of the /pr/ listing page and extracts
        campaign details using verified CSS selectors.

        Returns:
            List of listing dictionaries
        """
        listings = []
        max_pages = 3

        logger.info(f"[{self.platform}] Starting to scrape listings from reviewplace.co.kr/pr/ ...")

        for page in range(1, max_pages + 1):
            url = f"{self.base_url}/pr/"
            params = {'page': page}

            logger.debug(f"[{self.platform}] Fetching page {page}: {url}")
            soup = self.fetch_page(url, params=params)

            if not soup:
                logger.warning(f"[{self.platform}] Failed to fetch page {page}, stopping")
                break

            # Campaign items: #cmp_list > div.item
            cmp_list = soup.select_one('#cmp_list')
            if not cmp_list:
                # Fallback: try direct .campaign_list selector
                cmp_list = soup.select_one('.campaign_list.c_list')

            if not cmp_list:
                logger.warning(f"[{self.platform}] Campaign list container not found on page {page}")
                break

            items = cmp_list.select('div.item')

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
        Parse a single campaign item from the ReviewPlace listing.

        Args:
            item: BeautifulSoup element (div.item)

        Returns:
            Dictionary with listing data or None if parsing fails
        """
        try:
            # --- URL and external ID ---
            link_elem = item.select_one('a[href]')
            if not link_elem:
                return None

            raw_url = link_elem.get('href', '')
            url = urljoin(self.base_url, raw_url) if raw_url else ''

            # Extract ID from URL: /pr/?id=272302 -> 272302
            id_match = re.search(r'[?&]id=(\d+)', raw_url)
            external_id = f"rp_{id_match.group(1)}" if id_match else f"rp_{abs(hash(url)) % 10**8}"

            # --- Title ---
            title_elem = item.select_one('p.tit')
            title = title_elem.get_text(strip=True) if title_elem else ''

            if not title:
                return None

            # --- Product/reward description ---
            desc_elem = item.select_one('p.txt')
            description = desc_elem.get_text(strip=True) if desc_elem else ''

            # --- Image ---
            img_elem = item.select_one('img.thumbimg')
            image_url = ''
            if img_elem:
                image_url = img_elem.get('src', '') or img_elem.get('data-src', '')
                if image_url and not image_url.startswith('http'):
                    image_url = urljoin(self.base_url, image_url)

            # --- Deadline (D-day) ---
            deadline = self._parse_deadline(item)

            # --- Applicant count ---
            max_applicants = self._parse_applicants(item)

            # --- Reward/Point value ---
            reward_type, reward_value = self._parse_reward(item, description)

            # --- Category (extracted from title) ---
            category = self._extract_category(title, description)

            # --- Brand (extracted from description or title) ---
            brand = self._extract_brand(title, description)

            # --- SNS platform type ---
            platform_type = self._detect_sns_type(item, title)

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
                    'description': description,
                    'platform_type': platform_type,
                    'source': 'reviewplace.co.kr',
                }
            }

        except Exception as e:
            logger.error(f"[{self.platform}] Error parsing item: {e}")
            return None

    def _parse_deadline(self, item) -> datetime:
        """
        Parse deadline from the D-day element.

        Format: <p class="date"><em class="d_ico">D</em> - 11</p>

        Args:
            item: BeautifulSoup element

        Returns:
            datetime of deadline
        """
        try:
            date_elem = item.select_one('p.date')
            if not date_elem:
                date_elem = item.select_one('.date_wrap .date')

            if date_elem:
                date_text = date_elem.get_text(strip=True)
                # Extract number from "D - 11" or "D-7"
                dday_match = re.search(r'[Dd]\s*[-]\s*(\d+)', date_text)
                if dday_match:
                    days = int(dday_match.group(1))
                    return datetime.utcnow() + timedelta(days=days)

                # Check for "마감" (closed)
                if '마감' in date_text:
                    return datetime.utcnow()  # Already expired

            return datetime.utcnow() + timedelta(days=7)

        except Exception as e:
            logger.warning(f"[{self.platform}] Error parsing deadline: {e}")
            return datetime.utcnow() + timedelta(days=7)

    def _parse_applicants(self, item) -> Optional[int]:
        """
        Parse max applicant count from the recruitment info.

        Format: <div class="num"><p>신청 2<span> / 30명</span></p></div>

        Args:
            item: BeautifulSoup element

        Returns:
            Max applicants or None
        """
        try:
            num_elem = item.select_one('div.num p')
            if not num_elem:
                num_elem = item.select_one('.date_wrap .num p')

            if num_elem:
                text = num_elem.get_text(strip=True)
                # Extract total from "신청 2 / 30명"
                total_match = re.search(r'/\s*(\d+)\s*명?', text)
                if total_match:
                    return int(total_match.group(1))

            return None

        except Exception:
            return None

    def _parse_reward(self, item, description: str) -> tuple:
        """
        Parse reward type and value.

        Tag format: <div class="txt_tag">+ 10,000P</div> or <div class="txt_tag"> 32,700P</div>

        Args:
            item: BeautifulSoup element
            description: Text description of the reward

        Returns:
            Tuple of (reward_type, reward_value)
        """
        reward_type = '상품'
        reward_value = 0

        try:
            # Check tag for point/price value
            tag_elem = item.select_one('div.txt_tag')
            if tag_elem:
                tag_text = tag_elem.get_text(strip=True)

                # Extract point value: "+ 10,000P" or "32,700P"
                point_match = re.search(r'[\+]?\s*([\d,]+)\s*[Pp포]', tag_text)
                if point_match:
                    reward_value = int(point_match.group(1).replace(',', ''))
                    reward_type = '포인트'
                    return (reward_type, reward_value)

                # Extract KRW value
                won_match = re.search(r'([\d,]+)\s*원', tag_text)
                if won_match:
                    reward_value = int(won_match.group(1).replace(',', ''))
                    reward_type = '금전'
                    return (reward_type, reward_value)

            # Parse from description text
            combined = description
            won_match = re.search(r'([\d,]+)\s*원', combined)
            if won_match:
                val = int(won_match.group(1).replace(',', ''))
                if val >= 1000:  # Filter noise
                    reward_value = val
                    reward_type = '금전'

            man_match = re.search(r'(\d+)\s*만\s*원', combined)
            if man_match:
                reward_value = int(man_match.group(1)) * 10000
                reward_type = '금전'

        except Exception as e:
            logger.debug(f"[{self.platform}] Reward parse error: {e}")

        return (reward_type, reward_value)

    def _extract_brand(self, title: str, description: str) -> str:
        """Extract brand name from title or description."""
        # Pattern: [Brand] in title brackets (not location/platform/price)
        for text in [title, description]:
            bracket_match = re.search(r'\[([^\]]{2,30})\]', text)
            if bracket_match:
                candidate = bracket_match.group(1)
                # Skip locations, platforms, and price indicators
                skip_patterns = [
                    '서울', '부산', '대구', '인천', '광주', '대전', '울산', '세종',
                    '경기', '강원', '충북', '충남', '전북', '전남', '경북', '경남', '제주',
                    '블로그', '인스타', '유튜브', '틱톡', '기자단', '스마트스토어',
                    '마켓컬리', '올리브영', '쿠팡', '스스',
                    '만원', '상당', '원 ', '인분',
                ]
                # Also skip if candidate looks like a price/quantity
                if re.match(r'^[\d,]+', candidate):
                    continue
                if not any(skip in candidate for skip in skip_patterns):
                    return candidate

        # Platform names as brand source (check both title and description)
        platform_brands = {
            '스마트스토어': '스마트스토어',
            '마켓컬리': '마켓컬리',
            '올리브영': '올리브영',
            '쿠팡': '쿠팡',
        }
        combined = f"{title} {description}"
        for key, brand in platform_brands.items():
            if key in combined:
                return brand

        # Try to extract brand from description (first noun phrase before space/special char)
        if description:
            # Description often starts with the brand/product name
            desc_brand = re.match(r'^([가-힣A-Za-z][가-힣A-Za-z0-9]+)', description)
            if desc_brand and len(desc_brand.group(1)) >= 2:
                candidate = desc_brand.group(1)
                # Skip price/quantity patterns and common non-brand words
                skip_words = ['만원', '상당', '이용', '인분', '무료', '리뷰플레이스', '헬스']
                if not any(sw in candidate for sw in skip_words) and not re.match(r'^\d', candidate):
                    return candidate

        return 'Unknown'

    def _extract_category(self, title: str, description: str) -> str:
        """Extract category from text content."""
        text = f"{title} {description}".lower()

        categories = {
            '맛집': ['맛집', '음식', '식당', '레스토랑', '카페', '커피', '디저트', '고기', '삼겹살', '곱창',
                     '갈치', '초밥', '치킨', '파스타', '피자', '국밥', '맥주'],
            '뷰티': ['뷰티', '화장품', '스킨케어', '메이크업', '향수', '네일', '패치', '크림', '세럼', '앰플',
                     '쿠션', '마스크팩', '탈모', '샴푸', '립밤', '클렌징', '선크림', '선스크린', '토너',
                     '에센스', '아이크림', '필링', '각질', '보습'],
            '패션': ['패션', '의류', '옷', '신발', '가방', '액세서리', '바람막이', '스타일링', '주얼리'],
            '식품': ['식품', '건강식품', '영양제', '밀키트', '간식', '비니거', '효소', '프로틴', '유산균', '비타민'],
            '생활': ['생활용품', '인테리어', '가구', '디퓨저', '방향제', '주방', '세탁', '청소'],
            '육아': ['육아', '유아', '아이', '키즈', '기저귀', '분유'],
            '운동': ['필라테스', '요가', '헬스', '피트니스', '운동', '다이어트'],
            '반려동물': ['반려견', '반려묘', '강아지', '고양이', '펫'],
        }

        for cat, keywords in categories.items():
            if any(kw in text for kw in keywords):
                return cat

        return '기타'

    def _detect_sns_type(self, item, title: str) -> str:
        """
        Detect SNS platform type from the icon or title.

        The item contains div.sns_icon with sub-elements like:
        - blog_icon
        - insta_icon
        - youtube_icon

        Args:
            item: BeautifulSoup element
            title: Campaign title

        Returns:
            SNS platform type string
        """
        sns_icon = item.select_one('div.sns_icon')
        if sns_icon:
            if sns_icon.select_one('.insta_icon, [class*="insta"]'):
                return '인스타그램'
            if sns_icon.select_one('.youtube_icon, [class*="youtube"]'):
                return '유튜브'
            if sns_icon.select_one('.tiktok_icon, [class*="tiktok"]'):
                return '틱톡'
            if sns_icon.select_one('.blog_icon, [class*="blog"]'):
                return '블로그'

        # Fallback: detect from title
        title_lower = title.lower()
        if '인스타' in title_lower or '릴스' in title_lower:
            return '인스타그램'
        if '유튜브' in title_lower:
            return '유튜브'
        if '틱톡' in title_lower:
            return '틱톡'
        if '블로그' in title_lower or '블' == title_lower[:1]:
            return '블로그'

        return '블로그'
