"""Naver Blog Scraper - Scrape experience campaigns from Naver blog"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict
from .base_scraper import BaseScraper

logger = logging.getLogger('review.scrapers')


class NaverScraper(BaseScraper):
    """Scraper for Naver blog - Experience and product review campaigns"""

    def __init__(self):
        super().__init__('naver', 'https://section.blog.naver.com')

    def parse_listings(self) -> List[Dict]:
        """Parse listings from Naver blog"""
        listings = []
        page = 1
        max_pages = 5

        logger.info(f"[{self.platform}] Starting to scrape listings...")

        while page <= max_pages:
            # Search for experience campaign related posts
            url = f"{self.base_url}/search"
            params = {
                'page': page,
                'keyword': '체험단 모집'  # "Experience recruitment"
            }

            logger.debug(f"[{self.platform}] Fetching page {page}")
            soup = self.fetch_page(url, params=params)

            if not soup:
                break

            # Naver blog search results
            items = soup.select('.post_item, .post-item, .article')

            if not items:
                break

            logger.debug(f"[{self.platform}] Found {len(items)} items on page {page}")

            for item in items:
                try:
                    listing = self._parse_item(item)
                    if listing and self.validate_listing(listing):
                        listings.append(listing)
                except Exception as e:
                    logger.error(f"[{self.platform}] Error parsing item: {e}")

            self.rate_limit()
            page += 1

        saved_count = self.save_listings(listings)
        logger.info(f"[{self.platform}] Completed: {saved_count} new listings saved")
        return listings

    def _parse_item(self, item) -> Dict:
        """Parse a single blog post about experience campaign"""
        try:
            title_elem = item.select_one('.post_title, .title, a[title]')
            title = title_elem.text.strip() if title_elem else 'Unknown'

            # Extract description/summary
            desc_elem = item.select_one('.post_desc, .description, .summary')
            description = desc_elem.text.strip() if desc_elem else ''

            # Try to extract brand from description or title
            brand = self._extract_brand(title, description)

            # Extract URL
            url_elem = item.select_one('a')
            url = url_elem.get('href', '') if url_elem else ''
            if url and not url.startswith('http'):
                url = 'https:' + url if url.startswith('//') else 'https://blog.naver.com' + url

            # Try to extract category keywords
            category = self._extract_category(title, description)

            # Parse reward information from description
            reward_type, reward_value = self._parse_reward(description)

            # Parse deadline
            deadline = self._parse_deadline(description)

            # Extract image
            image_elem = item.select_one('img')
            image_url = image_elem.get('src', '') if image_elem else ''

            # Generate external ID from URL
            external_id = url.split('/')[-1] if url else f"naver_{hash(title)}"

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
                'requirements': {'source': 'Naver Blog Post'}
            }

        except Exception as e:
            logger.error(f"[{self.platform}] Error parsing item: {e}")
            return None

    def _extract_brand(self, title: str, description: str) -> str:
        """Extract brand name from title or description"""
        try:
            text = (title + ' ' + description).lower()
            # Common Korean brands
            brands = ['삼성', '롯데', 'lg', '현대', 'sk', 'cj', '이마트', 'gs', '빙그레', '해태']
            for brand in brands:
                if brand in text:
                    return brand.upper()
            return 'Unknown'
        except:
            return 'Unknown'

    def _extract_category(self, title: str, description: str) -> str:
        """Extract product category from title or description"""
        try:
            text = (title + ' ' + description).lower()
            categories = ['식품', 'beauty', '뷰티', '의류', 'fashion', '전자', '가전', '생활용품', 'home']
            for category in categories:
                if category in text:
                    return category
            return 'general'
        except:
            return 'general'

    def _parse_reward(self, description: str) -> tuple:
        """Parse reward type and value from description"""
        try:
            if not description:
                return ('상품', 0)

            text = description.lower()
            reward_type = '상품'
            reward_value = 0

            # Check for monetary reward
            if '원' in text or 'won' in text:
                reward_type = '금전'
                # Try to extract numeric value
                import re
                matches = re.findall(r'(\d+,?\d*)\s*원', text)
                if matches:
                    reward_value = int(matches[0].replace(',', ''))

            # Check for product reward
            if '상품' in text:
                reward_type = '상품'

            return (reward_type, reward_value)

        except Exception as e:
            logger.warning(f"[{self.platform}] Error parsing reward: {e}")
            return ('상품', 0)

    def _parse_deadline(self, description: str) -> datetime:
        """Parse deadline from description"""
        try:
            if not description:
                return datetime.utcnow() + timedelta(days=14)

            text = description.lower()

            # Check for deadline indicators
            import re
            # Look for "~2026-03-01" or "까지" patterns
            date_patterns = [
                r'(\d{4}-\d{2}-\d{2})',  # YYYY-MM-DD
                r'(\d{1,2}월\s+\d{1,2})',  # Korean date format
            ]

            for pattern in date_patterns:
                matches = re.findall(pattern, text)
                if matches:
                    try:
                        if '-' in matches[0]:
                            return datetime.strptime(matches[0], '%Y-%m-%d')
                    except:
                        pass

            # Check for "D-X" format
            if 'd-' in text:
                match = re.search(r'd-(\d+)', text)
                if match:
                    days = int(match.group(1))
                    return datetime.utcnow() + timedelta(days=days)

            # Default: 14 days
            return datetime.utcnow() + timedelta(days=14)

        except Exception as e:
            logger.warning(f"[{self.platform}] Error parsing deadline: {e}")
            return datetime.utcnow() + timedelta(days=14)
