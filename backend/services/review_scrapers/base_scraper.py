"""Base Scraper Class - Common functionality for all review platform scrapers"""

import requests
from bs4 import BeautifulSoup
import time
import logging
import os
from datetime import datetime
from typing import List, Dict, Optional
from abc import ABC, abstractmethod

logger = logging.getLogger('review.scrapers')


class BaseScraper(ABC):
    """Abstract base class for all review platform scrapers"""

    def __init__(self, platform_name: str, base_url: str = None, use_proxy: bool = True, use_captcha_solver: bool = True):
        """
        Initialize the scraper.

        Args:
            platform_name: Identifier for the platform (e.g., 'revu', 'reviewplace')
            base_url: Base URL for the platform
            use_proxy: Enable proxy rotation (default: True)
            use_captcha_solver: Enable CAPTCHA solving (default: True)
        """
        self.platform = platform_name
        self.base_url = base_url
        self.delay = 2  # Delay between requests in seconds
        self.max_retries = int(os.getenv('RETRY_MAX_ATTEMPTS', '3'))
        self.initial_retry_delay = 1

        # Setup session with proper headers
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

        # Initialize proxy manager and CAPTCHA solver
        self.use_proxy = use_proxy
        self.use_captcha_solver = use_captcha_solver
        self.proxy_manager = None
        self.captcha_solver = None
        self.captcha_cost_tracker = 0.0

        if self.use_proxy:
            self._init_proxy_manager()

        if self.use_captcha_solver:
            self._init_captcha_solver()

    def _init_proxy_manager(self):
        """Initialize proxy manager for request rotation"""
        try:
            from backend.services.proxy_manager import ProxyManager
            proxy_strategy = os.getenv('PROXY_ROTATION_STRATEGY', 'round-robin')
            self.proxy_manager = ProxyManager(
                provider='scraperapi',
                strategy=proxy_strategy
            )
            logger.debug(f"[{self.platform}] Proxy manager initialized with strategy: {proxy_strategy}")
        except Exception as e:
            logger.warning(f"[{self.platform}] Failed to initialize proxy manager: {e}")
            self.proxy_manager = None

    def _init_captcha_solver(self):
        """Initialize CAPTCHA solver for anti-bot challenges"""
        try:
            from backend.services.captcha_solver import CaptchaSolver
            self.captcha_solver = CaptchaSolver()
            logger.debug(f"[{self.platform}] CAPTCHA solver initialized")
        except Exception as e:
            logger.warning(f"[{self.platform}] Failed to initialize CAPTCHA solver: {e}")
            self.captcha_solver = None

    def fetch_page(self, url: str, params: Dict = None, timeout: int = 10) -> Optional[BeautifulSoup]:
        """
        Fetch a page with error handling, proxy rotation, and retry logic.

        Implements exponential backoff for retries and automatic proxy rotation
        to bypass IP blocking and rate limiting.

        Args:
            url: URL to fetch
            params: Optional query parameters
            timeout: Request timeout in seconds

        Returns:
            BeautifulSoup object or None if failed
        """
        for attempt in range(self.max_retries):
            proxy = None
            if self.proxy_manager:
                proxy = self.proxy_manager.get_proxy()

            try:
                proxies = None
                if proxy:
                    proxies = {'http': proxy, 'https': proxy}
                    logger.debug(f"[{self.platform}] Using proxy: {proxy[:40]}...")

                resp = self.session.get(
                    url,
                    params=params,
                    timeout=timeout,
                    proxies=proxies
                )
                resp.raise_for_status()

                # Mark proxy as healthy if request succeeded
                if self.proxy_manager and proxy:
                    self.proxy_manager.mark_proxy_healthy(proxy)

                return BeautifulSoup(resp.content, 'html.parser')

            except requests.exceptions.Timeout:
                logger.warning(f"[{self.platform}] Timeout fetching {url} (attempt {attempt + 1}/{self.max_retries})")
                if self.proxy_manager and proxy:
                    self.proxy_manager.mark_proxy_failed(proxy)
                if attempt < self.max_retries - 1:
                    wait = self.initial_retry_delay * (2 ** attempt)
                    time.sleep(wait)

            except requests.exceptions.ConnectionError:
                logger.warning(f"[{self.platform}] Connection error fetching {url} (attempt {attempt + 1}/{self.max_retries})")
                if self.proxy_manager and proxy:
                    self.proxy_manager.mark_proxy_failed(proxy)
                if attempt < self.max_retries - 1:
                    wait = self.initial_retry_delay * (2 ** attempt)
                    time.sleep(wait)

            except requests.exceptions.RequestException as e:
                logger.error(f"[{self.platform}] Error fetching {url}: {e}")
                if self.proxy_manager and proxy:
                    self.proxy_manager.mark_proxy_failed(proxy)
                if attempt < self.max_retries - 1:
                    wait = self.initial_retry_delay * (2 ** attempt)
                    time.sleep(wait)

        logger.error(f"[{self.platform}] Failed to fetch {url} after {self.max_retries} attempts")
        return None

    def rate_limit(self):
        """Apply rate limiting between requests"""
        time.sleep(self.delay)

    @abstractmethod
    def parse_listings(self) -> List[Dict]:
        """
        Parse listings from the platform.

        Subclasses must implement this method.

        Returns:
            List of listing dictionaries with keys:
            - external_id: Unique ID from the platform
            - title: Listing title
            - brand: Brand name
            - category: Product category
            - reward_type: Type of reward ('상품', '금전', '경험')
            - reward_value: Reward value in KRW
            - deadline: Deadline as datetime
            - url: URL to the listing
            - image_url: Image URL (optional)
            - max_applicants: Max number of applicants (optional)
            - requirements: JSON object with requirements
        """
        raise NotImplementedError

    def save_listings(self, listings: List[Dict]) -> int:
        """
        Save listings to database, avoiding duplicates.

        Args:
            listings: List of listing dictionaries

        Returns:
            Number of listings saved
        """
        from backend.models import db, ReviewListing

        saved_count = 0
        for listing_data in listings:
            try:
                # Check if already exists
                existing = ReviewListing.query.filter_by(
                    source_platform=self.platform,
                    external_id=listing_data['external_id']
                ).first()

                if existing:
                    logger.debug(f"[{self.platform}] Listing {listing_data['external_id']} already exists, skipping")
                    continue

                # Create new listing
                listing = ReviewListing(
                    source_platform=self.platform,
                    external_id=listing_data['external_id'],
                    title=listing_data.get('title', ''),
                    brand=listing_data.get('brand'),
                    category=listing_data.get('category'),
                    reward_type=listing_data.get('reward_type'),
                    reward_value=listing_data.get('reward_value', 0),
                    deadline=listing_data.get('deadline'),
                    max_applicants=listing_data.get('max_applicants'),
                    url=listing_data.get('url'),
                    image_url=listing_data.get('image_url'),
                    requirements=listing_data.get('requirements', {}),
                    status='active'
                )
                db.session.add(listing)
                saved_count += 1

            except Exception as e:
                logger.error(f"[{self.platform}] Error saving listing {listing_data.get('external_id')}: {e}")
                continue

        try:
            db.session.commit()
            logger.info(f"[{self.platform}] Saved {saved_count} new listings")
        except Exception as e:
            logger.error(f"[{self.platform}] Error committing listings: {e}")
            db.session.rollback()
            return 0

        return saved_count

    def validate_listing(self, listing: Dict) -> bool:
        """
        Validate listing has required fields.

        Args:
            listing: Listing dictionary

        Returns:
            True if valid, False otherwise
        """
        required_fields = ['external_id', 'title', 'url']
        for field in required_fields:
            if field not in listing or not listing[field]:
                logger.warning(f"[{self.platform}] Missing required field: {field}")
                return False
        return True
