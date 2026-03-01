"""Proxy Management & Rotation for Web Scraping

Handles proxy provider integration, health checks, and rotation strategies
to bypass IP blocking and rate limiting on Korean e-commerce platforms.

Supported providers:
- ScraperAPI: Built-in proxy rotation with CAPTCHA solving
- BrightData (Luminati): Premium proxy network with sticky sessions
- Direct HTTP proxies: Custom proxy lists with fallback

Token budget: ~500 per request (health check)
"""

import os
import logging
import time
from typing import Optional, List, Dict
from enum import Enum
import requests

logger = logging.getLogger('scraper.proxy')


class ProxyStrategy(Enum):
    """Proxy rotation strategies"""
    ROUND_ROBIN = "round-robin"      # Cycle through proxies
    RANDOM = "random"                # Random selection
    STICKY = "sticky"                # Keep session for duration
    LATENCY_BASED = "latency-based"  # Select lowest latency


class ProxyProvider(Enum):
    """Supported proxy providers"""
    SCRAPERAPI = "scraperapi"
    BRIGHTDATA = "brightdata"
    DIRECT = "direct"


class ProxyManager:
    """
    Manages proxy rotation and health checks for web scraping.

    Example:
        pm = ProxyManager(provider='scraperapi', api_key='key')
        proxy = pm.get_proxy()  # Returns proxy URL
        health = pm.test_proxy_health(proxy)  # Checks if working
    """

    def __init__(
        self,
        provider: str = "scraperapi",
        api_key: str = None,
        strategy: str = "round-robin",
        max_retries: int = 3,
        health_check_interval: int = 300  # 5 minutes
    ):
        """
        Initialize ProxyManager.

        Args:
            provider: Proxy provider ('scraperapi', 'brightdata', 'direct')
            api_key: API key for the provider (read from env if not provided)
            strategy: Rotation strategy (round-robin, random, sticky, latency-based)
            max_retries: Max retries on proxy failure
            health_check_interval: Seconds between health checks (default: 5 min)
        """
        self.provider = ProxyProvider(provider)
        self.strategy = ProxyStrategy(strategy)
        self.max_retries = max_retries
        self.health_check_interval = health_check_interval

        # Get API key from parameter or environment
        if api_key:
            self.api_key = api_key
        else:
            if self.provider == ProxyProvider.SCRAPERAPI:
                self.api_key = os.getenv('SCRAPERAPI_KEY')
            elif self.provider == ProxyProvider.BRIGHTDATA:
                self.api_key = os.getenv('BRIGHTDATA_KEY')
            else:
                self.api_key = None

        # State tracking
        self.current_index = 0
        self.proxy_list = []
        self.last_health_check = {}
        self.healthy_proxies = set()
        self.failed_attempts = {}
        self.session_start = time.time()

        # Load proxy list for direct proxies
        if self.provider == ProxyProvider.DIRECT:
            self._load_direct_proxies()

        logger.info(
            f"ProxyManager initialized: provider={self.provider.value}, "
            f"strategy={self.strategy.value}, api_key={'***' if self.api_key else 'None'}"
        )

    def get_proxy(self) -> Optional[str]:
        """
        Get a proxy URL for the next request.

        Returns:
            Proxy URL string or None if no proxies available

        Example:
            "http://proxy-user:pass@proxy.scraperapi.com:8001"
        """
        if self.provider == ProxyProvider.SCRAPERAPI:
            return self._get_scraperapi_proxy()
        elif self.provider == ProxyProvider.BRIGHTDATA:
            return self._get_brightdata_proxy()
        else:
            return self._get_direct_proxy()

    def _get_scraperapi_proxy(self) -> Optional[str]:
        """
        Get ScraperAPI proxy URL.

        ScraperAPI handles:
        - Automatic IP rotation
        - Built-in CAPTCHA solving
        - Geolocation selection

        Format: http://api_key@proxy.scraperapi.com:8001
        """
        if not self.api_key:
            logger.error("SCRAPERAPI_KEY not configured")
            return None

        return f"http://{self.api_key}@proxy.scraperapi.com:8001"

    def _get_brightdata_proxy(self) -> Optional[str]:
        """
        Get BrightData (Luminati) proxy URL.

        BrightData features:
        - Residential proxies (real IPs)
        - Sticky sessions for auth
        - Country-specific routing

        Format: http://lum-customer-xxxxxx-zone-xxxxxx:password@zproxy.lum-superproxy.io:22225
        """
        if not self.api_key:
            logger.error("BRIGHTDATA_KEY not configured")
            return None

        # Expected format: "customer_id:password"
        try:
            customer_id, password = self.api_key.split(':')
            return f"http://lum-customer-{customer_id}-zone-brightdata:{password}@zproxy.lum-superproxy.io:22225"
        except ValueError:
            logger.error("BRIGHTDATA_KEY format invalid. Expected: 'customer_id:password'")
            return None

    def _get_direct_proxy(self) -> Optional[str]:
        """
        Get proxy from direct proxy list with rotation.

        Supports round-robin, random, and latency-based selection.
        """
        if not self.proxy_list:
            logger.warning("No direct proxies configured")
            return None

        # Implement rotation strategy
        if self.strategy == ProxyStrategy.ROUND_ROBIN:
            proxy = self.proxy_list[self.current_index % len(self.proxy_list)]
            self.current_index += 1
        elif self.strategy == ProxyStrategy.RANDOM:
            import random
            proxy = random.choice(self.proxy_list)
        elif self.strategy == ProxyStrategy.LATENCY_BASED:
            # Select proxy with lowest latency
            proxy = self._select_lowest_latency_proxy()
        else:
            proxy = self.proxy_list[self.current_index % len(self.proxy_list)]

        return proxy

    def _load_direct_proxies(self):
        """
        Load direct proxy list from environment variable.

        Format (comma-separated):
        DIRECT_PROXIES=http://proxy1:port1,http://proxy2:port2,...
        """
        proxies_str = os.getenv('DIRECT_PROXIES', '')
        if proxies_str:
            self.proxy_list = [p.strip() for p in proxies_str.split(',') if p.strip()]
            logger.info(f"Loaded {len(self.proxy_list)} direct proxies")
        else:
            logger.warning("No DIRECT_PROXIES configured in environment")

    def _select_lowest_latency_proxy(self) -> Optional[str]:
        """
        Select proxy with lowest latency from health check results.

        Returns:
            Proxy URL with best latency, or None if no healthy proxies
        """
        if not self.healthy_proxies:
            return self.proxy_list[0] if self.proxy_list else None

        # Sort by latency from health check results
        sorted_proxies = sorted(
            self.healthy_proxies,
            key=lambda p: self.last_health_check.get(p, {}).get('latency', float('inf'))
        )

        return sorted_proxies[0] if sorted_proxies else None

    def test_proxy_health(self, proxy: Optional[str] = None, timeout: int = 5) -> Dict:
        """
        Test proxy health by making a test request.

        Args:
            proxy: Proxy URL to test (uses current if not specified)
            timeout: Request timeout in seconds

        Returns:
            Dictionary with health check results:
            {
                'healthy': bool,
                'latency': float,  # Response time in ms
                'status_code': int,
                'error': str or None,
                'timestamp': float
            }
        """
        if not proxy:
            proxy = self.get_proxy()

        if not proxy:
            return {
                'healthy': False,
                'latency': None,
                'status_code': None,
                'error': 'No proxy available',
                'timestamp': time.time()
            }

        # Check cache first
        if proxy in self.last_health_check:
            cached = self.last_health_check[proxy]
            if time.time() - cached['timestamp'] < self.health_check_interval:
                return cached

        test_url = "https://httpbin.org/ip"  # Simple test endpoint
        start_time = time.time()

        try:
            proxies = {'http': proxy, 'https': proxy}
            response = requests.get(test_url, proxies=proxies, timeout=timeout)
            latency = (time.time() - start_time) * 1000  # Convert to ms

            result = {
                'healthy': response.status_code == 200,
                'latency': latency,
                'status_code': response.status_code,
                'error': None,
                'timestamp': time.time()
            }

            # Cache result
            self.last_health_check[proxy] = result

            if result['healthy']:
                self.healthy_proxies.add(proxy)
                self.failed_attempts[proxy] = 0
                logger.debug(f"Proxy {proxy[:30]}... is healthy (latency: {latency:.1f}ms)")
            else:
                logger.warning(f"Proxy {proxy[:30]}... returned {response.status_code}")

            return result

        except requests.exceptions.Timeout:
            result = {
                'healthy': False,
                'latency': None,
                'status_code': None,
                'error': 'Request timeout',
                'timestamp': time.time()
            }
        except requests.exceptions.ProxyError:
            result = {
                'healthy': False,
                'latency': None,
                'status_code': None,
                'error': 'Proxy connection error',
                'timestamp': time.time()
            }
        except Exception as e:
            result = {
                'healthy': False,
                'latency': None,
                'status_code': None,
                'error': str(e),
                'timestamp': time.time()
            }

        # Cache failed result
        self.last_health_check[proxy] = result
        self.healthy_proxies.discard(proxy)
        self.failed_attempts[proxy] = self.failed_attempts.get(proxy, 0) + 1

        logger.warning(f"Proxy {proxy[:30]}... health check failed: {result['error']}")
        return result

    def mark_proxy_failed(self, proxy: str):
        """
        Mark proxy as failed and increment failure counter.

        Args:
            proxy: Proxy URL that failed
        """
        self.failed_attempts[proxy] = self.failed_attempts.get(proxy, 0) + 1
        self.healthy_proxies.discard(proxy)

        # If too many failures, mark as unhealthy
        if self.failed_attempts[proxy] >= self.max_retries:
            logger.error(f"Proxy {proxy[:30]}... marked as dead after {self.max_retries} failures")

    def mark_proxy_healthy(self, proxy: str):
        """
        Mark proxy as healthy and reset failure counter.

        Args:
            proxy: Proxy URL that succeeded
        """
        self.failed_attempts[proxy] = 0
        self.healthy_proxies.add(proxy)
        logger.debug(f"Proxy {proxy[:30]}... marked as healthy")

    def get_stats(self) -> Dict:
        """
        Get proxy manager statistics.

        Returns:
            Dictionary with current state and metrics
        """
        total_proxies = len(self.proxy_list) if self.provider == ProxyProvider.DIRECT else 1

        return {
            'provider': self.provider.value,
            'strategy': self.strategy.value,
            'total_proxies': total_proxies,
            'healthy_proxies': len(self.healthy_proxies),
            'failed_attempts': dict(self.failed_attempts),
            'session_duration_seconds': time.time() - self.session_start,
            'api_key_configured': bool(self.api_key),
        }
