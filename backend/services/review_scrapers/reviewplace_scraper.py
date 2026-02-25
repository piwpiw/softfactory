"""ReviewPlace Scraper - Scrape listings from reviewplace.co.kr"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict
from .base_scraper import BaseScraper

logger = logging.getLogger('review.scrapers')


class ReviewPlaceScraper(BaseScraper):
    """Scraper for reviewplace.co.kr - Product review opportunities"""

    def __init__(self):
        super().__init__('reviewplace', 'https://reviewplace.co.kr')

    def parse_listings(self) -> List[Dict]:
        """Parse listings from ReviewPlace"""
        listings = []
        page = 1
        max_pages = 5

        logger.info(f"[{self.platform}] Starting to scrape listings...")

        while page <= max_pages:
            url = f"{self.base_url}/product"
            params = {'page': page}

            logger.debug(f"[{self.platform}] Fetching page {page}")
            soup = self.fetch_page(url, params=params)

            if not soup:
                break

            items = soup.select('.product-item, .review-card, .listing-item')

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
        """Parse a single product listing"""
        try:
            title_elem = item.select_one('.product-name, .title, h3')
            title = title_elem.text.strip() if title_elem else 'Unknown'

            brand_elem = item.select_one('.brand-name, .brand')
            brand = brand_elem.text.strip() if brand_elem else 'Unknown'

            category_elem = item.select_one('.category, .product-category')
            category = category_elem.text.strip() if category_elem else None

            reward_elem = item.select_one('.reward, .incentive')
            reward_text = reward_elem.text.strip() if reward_elem else ''

            reward_type = '상품'
            reward_value = 0
            if '원' in reward_text:
                try:
                    reward_value = int(reward_text.replace('원', '').replace(',', '').split()[-1])
                    reward_type = '금전'
                except (ValueError, IndexError):
                    pass

            deadline = self._parse_deadline(item)

            url_elem = item.select_one('a')
            url = url_elem.get('href', '') if url_elem else ''
            if url and not url.startswith('http'):
                url = self.base_url + url

            image_elem = item.select_one('img')
            image_url = image_elem.get('src', '') if image_elem else ''
            if image_url and not image_url.startswith('http'):
                image_url = self.base_url + image_url

            external_id = url.split('/')[-1] if url else f"reviewplace_{hash(title)}"

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
                'requirements': {}
            }

        except Exception as e:
            logger.error(f"[{self.platform}] Error parsing item: {e}")
            return None

    def _parse_deadline(self, item) -> datetime:
        """Parse deadline from listing"""
        try:
            deadline_elem = item.select_one('.deadline, .end-date')
            if not deadline_elem:
                return datetime.utcnow() + timedelta(days=7)

            deadline_text = deadline_elem.text.strip().lower()

            if 'd-' in deadline_text:
                try:
                    days_left = int(deadline_text.replace('d-', '').split()[0])
                    return datetime.utcnow() + timedelta(days=days_left)
                except ValueError:
                    pass

            return datetime.utcnow() + timedelta(days=7)

        except Exception as e:
            logger.warning(f"[{self.platform}] Error parsing deadline: {e}")
            return datetime.utcnow() + timedelta(days=7)
