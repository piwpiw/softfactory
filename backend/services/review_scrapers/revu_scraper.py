"""Revu Scraper - Template/Example implementation for review platform scraping"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict
from .base_scraper import BaseScraper

logger = logging.getLogger('review.scrapers')


class RevuScraper(BaseScraper):
    """
    Scraper for revu.net - Template/Example scraper showing full implementation pattern.

    This scraper demonstrates the complete implementation pattern for any review platform.
    To add a new platform:
    1. Create a new file (e.g., newplatform_scraper.py)
    2. Extend BaseScraper
    3. Implement parse_listings() method
    4. Implement _parse_item() for individual items
    5. Add to SCRAPERS list in __init__.py
    """

    def __init__(self):
        super().__init__('revu', 'https://revu.net')

    def parse_listings(self) -> List[Dict]:
        """
        Parse experience listings from Revu.

        Returns:
            List of listing dictionaries with the following structure:
            {
                'external_id': 'unique_id_from_platform',
                'title': 'Listing title',
                'brand': 'Brand name',
                'category': 'Product category',
                'reward_type': '상품|금전|경험',  # Product, Cash, Experience
                'reward_value': 50000,  # KRW value
                'deadline': datetime,
                'url': 'https://...',
                'image_url': 'https://...',
                'max_applicants': 50,  # Optional
                'requirements': {}  # Optional JSON requirements
            }
        """
        listings = []
        page = 1
        max_pages = 5  # Limit to first 5 pages for performance

        logger.info(f"[{self.platform}] Starting to scrape listings...")

        while page <= max_pages:
            # Construct URL with pagination
            url = f"{self.base_url}/experience"
            params = {'page': page}

            # Fetch the page
            logger.debug(f"[{self.platform}] Fetching page {page}: {url}")
            soup = self.fetch_page(url, params=params)

            if not soup:
                logger.warning(f"[{self.platform}] Failed to fetch page {page}, stopping")
                break

            # Find all listing items on the page
            # CSS selectors vary by website - adjust based on actual HTML structure
            items = soup.select(
                '.listing-card, .item-card, .experience-item, .card-item, [data-listing-id]'
            )

            if not items:
                logger.warning(f"[{self.platform}] No items found on page {page}, stopping")
                break

            logger.debug(f"[{self.platform}] Found {len(items)} items on page {page}")

            # Parse each item
            for item in items:
                try:
                    listing = self._parse_item(item)
                    if listing and self.validate_listing(listing):
                        listings.append(listing)
                except Exception as e:
                    logger.error(f"[{self.platform}] Error parsing item: {e}")
                    continue

            # Rate limiting between requests
            self.rate_limit()
            page += 1

        # Save all collected listings to database
        saved_count = self.save_listings(listings)
        logger.info(f"[{self.platform}] Completed: {saved_count} new listings saved")

        return listings

    def _parse_item(self, item) -> Dict:
        """
        Parse a single listing item from HTML element.

        Args:
            item: BeautifulSoup element representing a single listing

        Returns:
            Dictionary with listing data or None if parsing fails
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

            # Parse reward type and value
            reward_type = '상품'  # Default to product
            reward_value = 0

            if '원' in reward_text:
                # Extract numeric value (e.g., "50,000원" -> 50000)
                try:
                    numeric_str = reward_text.replace('원', '').replace(',', '').strip()
                    reward_value = int(numeric_str.split()[-1])
                    reward_type = '금전'  # Mark as cash if numeric
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
            image_url = ''
            if image_elem:
                image_url = image_elem.get('src', '') or image_elem.get('data-src', '')
            if image_url and not image_url.startswith('http'):
                image_url = self.base_url + image_url

            # Extract external ID from URL or data attribute
            external_id = item.get('data-listing-id', '')
            if not external_id and url:
                external_id = url.split('/')[-1]
            if not external_id:
                external_id = f"revu_{hash(title)}"

            # Extract max applicants (optional)
            max_applicants_elem = item.select_one('.max-applicants, [data-max]')
            max_applicants = None
            if max_applicants_elem:
                try:
                    max_applicants = int(max_applicants_elem.text.strip().split()[0])
                except (ValueError, AttributeError):
                    pass

            # Extract requirements (optional)
            requirements = self._parse_requirements(item)

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
                'requirements': requirements
            }

        except Exception as e:
            logger.error(f"[{self.platform}] Error parsing item: {e}")
            return None

    def _parse_deadline(self, item) -> datetime:
        """
        Parse deadline from listing item.

        Handles various deadline formats:
        - "D-7" (7 days remaining)
        - "2026-03-01" (specific date)
        - "종료" (ended, in Korean)

        Args:
            item: BeautifulSoup element

        Returns:
            Datetime object, defaults to 7 days from now if parsing fails
        """
        try:
            deadline_elem = item.select_one('.deadline, .date, [data-deadline]')
            if not deadline_elem:
                return datetime.utcnow() + timedelta(days=7)

            deadline_text = deadline_elem.text.strip().lower()

            # Handle "D-X" format (e.g., "D-7")
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

    def _parse_requirements(self, item) -> Dict:
        """
        Parse campaign requirements (follower count, engagement rate, etc.).

        Args:
            item: BeautifulSoup element

        Returns:
            Dictionary with requirements
        """
        requirements = {}

        try:
            # Parse follower requirements
            followers_elem = item.select_one('.followers, [data-followers]')
            if followers_elem:
                try:
                    followers_text = followers_elem.text.strip()
                    # Handle formats like "1K+", "10,000+", "500K+"
                    if 'k' in followers_text.lower():
                        followers_text = followers_text.replace('K', '000').replace('k', '000')
                    requirements['follower_min'] = int(followers_text.replace('+', '').replace(',', '').split()[0])
                except (ValueError, AttributeError):
                    pass

            # Parse engagement rate
            engagement_elem = item.select_one('.engagement, [data-engagement]')
            if engagement_elem:
                try:
                    engagement_text = engagement_elem.text.strip()
                    requirements['engagement_min'] = float(engagement_text.replace('%', ''))
                except (ValueError, AttributeError):
                    pass

            # Parse category/niche
            niche_elem = item.select_one('.niche, .platform, [data-niche]')
            if niche_elem:
                requirements['niche'] = niche_elem.text.strip()

        except Exception as e:
            logger.warning(f"[{self.platform}] Error parsing requirements: {e}")

        return requirements
