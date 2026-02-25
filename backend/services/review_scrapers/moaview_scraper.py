"""MoaView Scraper - Scrape experience listings from moaview.co.kr"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict
from .base_scraper import BaseScraper

logger = logging.getLogger('review.scrapers')


class MoaviewScraper(BaseScraper):
    """Scraper for moaview.co.kr - Experience and product review campaigns"""

    def __init__(self):
        super().__init__('moaview', 'https://moaview.co.kr')

    def parse_listings(self) -> List[Dict]:
        """
        Parse experience listings from MoaView.

        Returns:
            List of listing dictionaries
        """
        listings = []
        page = 1
        max_pages = 5  # Scrape first 5 pages for performance

        logger.info(f"[{self.platform}] Starting to scrape listings...")

        while page <= max_pages:
            url = f"{self.base_url}/experience"
            params = {'page': page}

            logger.debug(f"[{self.platform}] Fetching page {page}: {url}")
            soup = self.fetch_page(url, params=params)

            if not soup:
                logger.warning(f"[{self.platform}] Failed to fetch page {page}, stopping")
                break

            # Find listing containers (adjust selector based on actual HTML structure)
            # Common patterns: .item, .card, .listing-item, .experience-card
            items = soup.select('.card-item, .listing-card, .item-card, [data-listing-id]')

            if not items:
                logger.warning(f"[{self.platform}] No items found on page {page}, stopping")
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
            page += 1

        # Save to database
        saved_count = self.save_listings(listings)
        logger.info(f"[{self.platform}] Completed: {saved_count} new listings saved")

        return listings

    def _parse_item(self, item) -> Dict:
        """
        Parse a single listing item.

        Args:
            item: BeautifulSoup element for a single listing

        Returns:
            Dictionary with listing data
        """
        try:
            # Extract title
            title_elem = item.select_one('.title, .item-title, h3, .card-title')
            title = title_elem.text.strip() if title_elem else 'Unknown'

            # Extract brand
            brand_elem = item.select_one('.brand, .brand-name, [data-brand]')
            brand = brand_elem.text.strip() if brand_elem else 'Unknown'

            # Extract category
            category_elem = item.select_one('.category, .cat, [data-category]')
            category = category_elem.text.strip() if category_elem else None

            # Extract reward information
            reward_elem = item.select_one('.reward, .reward-text, [data-reward]')
            reward_text = reward_elem.text.strip() if reward_elem else ''

            reward_type = '상품'  # Default to product
            reward_value = 0

            if '원' in reward_text:
                # Extract numeric value (e.g., "50,000원" -> 50000)
                try:
                    reward_value = int(reward_text.replace('원', '').replace(',', '').split()[-1])
                    reward_type = '금전'
                except (ValueError, IndexError):
                    reward_value = 0

            # Extract deadline
            deadline = self._parse_deadline(item)

            # Extract URL
            url_elem = item.select_one('a')
            url = url_elem.get('href', '') if url_elem else ''
            if url and not url.startswith('http'):
                url = self.base_url + url

            # Extract image URL
            image_elem = item.select_one('img, [data-image]')
            image_url = image_elem.get('src', '') or image_elem.get('data-src', '') if image_elem else ''
            if image_url and not image_url.startswith('http'):
                image_url = self.base_url + image_url

            # Extract external ID from URL or data attribute
            external_id = item.get('data-listing-id', '')
            if not external_id and url:
                external_id = url.split('/')[-1]

            # Extract max applicants
            max_applicants_elem = item.select_one('.max-applicants, [data-max]')
            max_applicants = None
            if max_applicants_elem:
                try:
                    max_applicants = int(max_applicants_elem.text.strip().split()[0])
                except (ValueError, AttributeError):
                    pass

            return {
                'external_id': external_id or f"moaview_{hash(title)}",
                'title': title,
                'brand': brand,
                'category': category,
                'reward_type': reward_type,
                'reward_value': reward_value,
                'deadline': deadline,
                'url': url,
                'image_url': image_url,
                'max_applicants': max_applicants,
                'requirements': {}
            }

        except Exception as e:
            logger.error(f"[{self.platform}] Error parsing item: {e}")
            return None

    def _parse_deadline(self, item) -> datetime:
        """
        Parse deadline from listing item.

        Args:
            item: BeautifulSoup element

        Returns:
            Datetime object, default to 7 days from now
        """
        try:
            # Look for deadline text (e.g., "D-7", "2026-03-01", "종료")
            deadline_elem = item.select_one('.deadline, .date, [data-deadline]')
            if not deadline_elem:
                return datetime.utcnow() + timedelta(days=7)

            deadline_text = deadline_elem.text.strip().lower()

            # Handle "D-X" format
            if 'd-' in deadline_text:
                try:
                    days_left = int(deadline_text.replace('d-', '').split()[0])
                    return datetime.utcnow() + timedelta(days=days_left)
                except ValueError:
                    pass

            # Handle specific date format (e.g., "2026-03-01")
            try:
                return datetime.strptime(deadline_text.split()[0], '%Y-%m-%d')
            except ValueError:
                pass

            # Default: 7 days from now
            return datetime.utcnow() + timedelta(days=7)

        except Exception as e:
            logger.warning(f"[{self.platform}] Error parsing deadline: {e}")
            return datetime.utcnow() + timedelta(days=7)
