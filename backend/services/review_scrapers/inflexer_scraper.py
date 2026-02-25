"""Inflexer Scraper - Scrape influencer campaigns from inflexer.net"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict
from .base_scraper import BaseScraper

logger = logging.getLogger('review.scrapers')


class InflexerScraper(BaseScraper):
    """Scraper for inflexer.net - Influencer marketing campaigns"""

    def __init__(self):
        super().__init__('inflexer', 'https://inflexer.net')

    def parse_listings(self) -> List[Dict]:
        """
        Parse campaign listings from Inflexer.

        Returns:
            List of listing dictionaries
        """
        listings = []
        page = 1
        max_pages = 5  # Scrape first 5 pages for performance

        logger.info(f"[{self.platform}] Starting to scrape listings...")

        while page <= max_pages:
            url = f"{self.base_url}/campaigns"
            params = {'page': page, 'type': 'active'}

            logger.debug(f"[{self.platform}] Fetching page {page}: {url}")
            soup = self.fetch_page(url, params=params)

            if not soup:
                logger.warning(f"[{self.platform}] Failed to fetch page {page}, stopping")
                break

            # Find campaign containers
            items = soup.select('.campaign-card, .campaign-item, .deal-card, [data-campaign-id]')

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
        Parse a single campaign item.

        Args:
            item: BeautifulSoup element for a single campaign

        Returns:
            Dictionary with campaign data
        """
        try:
            # Extract title
            title_elem = item.select_one('.campaign-title, .title, h3, [data-title]')
            title = title_elem.text.strip() if title_elem else 'Unknown Campaign'

            # Extract brand/company
            brand_elem = item.select_one('.company, .brand, .advertiser, [data-brand]')
            brand = brand_elem.text.strip() if brand_elem else 'Unknown'

            # Extract category
            category_elem = item.select_one('.category, .campaign-category, [data-category]')
            category = category_elem.text.strip() if category_elem else None

            # Extract compensation/reward
            compensation_elem = item.select_one('.compensation, .reward, .payment, [data-reward]')
            compensation_text = compensation_elem.text.strip() if compensation_elem else ''

            reward_type = '금전'  # Inflexer mostly has cash rewards
            reward_value = 0

            # Parse compensation value
            if compensation_text:
                try:
                    # Handle formats like "10,000원", "$100", "₩50,000"
                    numeric_str = compensation_text.replace('원', '').replace('$', '').replace('₩', '').replace(',', '').strip()
                    reward_value = int(numeric_str.split()[0])
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
            image_elem = item.select_one('img, [data-image], [data-src]')
            image_url = ''
            if image_elem:
                image_url = image_elem.get('src', '') or image_elem.get('data-src', '')
            if image_url and not image_url.startswith('http'):
                image_url = self.base_url + image_url

            # Extract external ID
            external_id = item.get('data-campaign-id', '')
            if not external_id and url:
                external_id = url.split('/')[-1]

            # Extract requirements (followers, engagement, etc.)
            requirements = self._parse_requirements(item)

            # Extract max applicants
            max_applicants_elem = item.select_one('.applicants, .max-spots, [data-slots]')
            max_applicants = None
            if max_applicants_elem:
                try:
                    max_applicants = int(max_applicants_elem.text.strip().split()[0])
                except (ValueError, AttributeError):
                    pass

            return {
                'external_id': external_id or f"inflexer_{hash(title)}",
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

    def _parse_requirements(self, item) -> Dict:
        """
        Parse campaign requirements (followers, engagement, etc.).

        Args:
            item: BeautifulSoup element

        Returns:
            Dictionary with requirements
        """
        requirements = {}

        try:
            # Follower requirements
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

            # Engagement rate
            engagement_elem = item.select_one('.engagement, [data-engagement]')
            if engagement_elem:
                try:
                    engagement_text = engagement_elem.text.strip()
                    requirements['engagement_min'] = float(engagement_text.replace('%', ''))
                except (ValueError, AttributeError):
                    pass

            # Platform/niche requirements
            niche_elem = item.select_one('.niche, .platform, [data-niche]')
            if niche_elem:
                requirements['niche'] = niche_elem.text.strip()

        except Exception as e:
            logger.warning(f"[{self.platform}] Error parsing requirements: {e}")

        return requirements

    def _parse_deadline(self, item) -> datetime:
        """
        Parse deadline from campaign item.

        Args:
            item: BeautifulSoup element

        Returns:
            Datetime object, default to 14 days from now
        """
        try:
            # Look for deadline/application deadline text
            deadline_elem = item.select_one('.deadline, .end-date, .closes, [data-deadline]')
            if not deadline_elem:
                return datetime.utcnow() + timedelta(days=14)

            deadline_text = deadline_elem.text.strip().lower()

            # Handle "D-X" or "In X days"
            if 'd-' in deadline_text:
                try:
                    days_left = int(deadline_text.replace('d-', '').split()[0])
                    return datetime.utcnow() + timedelta(days=days_left)
                except ValueError:
                    pass

            if 'in' in deadline_text and 'day' in deadline_text:
                try:
                    days_left = int(deadline_text.split()[1])
                    return datetime.utcnow() + timedelta(days=days_left)
                except (ValueError, IndexError):
                    pass

            # Handle specific date format
            try:
                return datetime.strptime(deadline_text.split()[0], '%Y-%m-%d')
            except ValueError:
                pass

            # Default: 14 days from now
            return datetime.utcnow() + timedelta(days=14)

        except Exception as e:
            logger.warning(f"[{self.platform}] Error parsing deadline: {e}")
            return datetime.utcnow() + timedelta(days=14)
