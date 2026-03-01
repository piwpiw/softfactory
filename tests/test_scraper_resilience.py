"""Test Suite for Scraper Resilience Features

Tests for proxy rotation, CAPTCHA solving, and retry logic.
Ensures scrapers can handle IP blocking, rate limiting, and anti-bot challenges.

Test Coverage:
- Proxy manager initialization and rotation
- CAPTCHA solver integration
- Fallback mechanisms on proxy failure
- Retry logic with exponential backoff
- Cost tracking for CAPTCHA solving
- Integration with existing scrapers
"""

import pytest
import logging
import time
from unittest.mock import Mock, patch, MagicMock
import requests

from backend.services.proxy_manager import ProxyManager, ProxyStrategy, ProxyProvider
from backend.services.captcha_solver import CaptchaSolver, CaptchaType
from backend.services.review_scrapers.base_scraper import BaseScraper

logger = logging.getLogger('test.scraper_resilience')


class TestProxyManager:
    """Test ProxyManager functionality"""

    def test_init_scraperapi(self):
        """Test ScraperAPI initialization"""
        pm = ProxyManager(provider='scraperapi', api_key='test_key_123')
        assert pm.provider == ProxyProvider.SCRAPERAPI
        assert pm.api_key == 'test_key_123'
        assert pm.strategy == ProxyStrategy.ROUND_ROBIN

    def test_init_brightdata(self):
        """Test BrightData initialization"""
        pm = ProxyManager(provider='brightdata', api_key='cust123:password456')
        assert pm.provider == ProxyProvider.BRIGHTDATA
        assert pm.api_key == 'cust123:password456'

    def test_init_direct(self):
        """Test direct proxy initialization"""
        pm = ProxyManager(provider='direct', strategy='round-robin')
        assert pm.provider == ProxyProvider.DIRECT
        assert pm.strategy == ProxyStrategy.ROUND_ROBIN

    def test_get_scraperapi_proxy(self):
        """Test ScraperAPI proxy URL generation"""
        pm = ProxyManager(provider='scraperapi', api_key='test_key_123')
        proxy = pm.get_proxy()
        assert proxy == 'http://test_key_123@proxy.scraperapi.com:8001'

    def test_get_brightdata_proxy(self):
        """Test BrightData proxy URL generation"""
        pm = ProxyManager(provider='brightdata', api_key='cust123:password456')
        proxy = pm.get_proxy()
        assert proxy == 'http://lum-customer-cust123-zone-brightdata:password456@zproxy.lum-superproxy.io:22225'

    def test_get_proxy_no_api_key(self):
        """Test get_proxy returns None when API key not configured"""
        pm = ProxyManager(provider='scraperapi', api_key=None)
        proxy = pm.get_proxy()
        assert proxy is None

    @patch.dict('os.environ', {'DIRECT_PROXIES': 'http://proxy1:8080,http://proxy2:8080'})
    def test_direct_proxy_round_robin(self):
        """Test round-robin proxy rotation"""
        pm = ProxyManager(provider='direct', strategy='round-robin')
        proxy1 = pm.get_proxy()
        proxy2 = pm.get_proxy()
        proxy3 = pm.get_proxy()

        assert proxy1 == 'http://proxy1:8080'
        assert proxy2 == 'http://proxy2:8080'
        assert proxy3 == 'http://proxy1:8080'  # Cycles back

    @patch('requests.get')
    def test_proxy_health_check_success(self, mock_get):
        """Test successful proxy health check"""
        pm = ProxyManager(provider='scraperapi', api_key='test_key')
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        health = pm.test_proxy_health('http://test-proxy:8001')

        assert health['healthy'] is True
        assert health['status_code'] == 200
        assert health['latency'] is not None
        assert health['error'] is None

    @patch('requests.get')
    def test_proxy_health_check_timeout(self, mock_get):
        """Test proxy health check timeout"""
        pm = ProxyManager(provider='scraperapi', api_key='test_key')
        mock_get.side_effect = requests.exceptions.Timeout()

        health = pm.test_proxy_health('http://test-proxy:8001', timeout=1)

        assert health['healthy'] is False
        assert 'timeout' in health['error'].lower()

    @patch('requests.get')
    def test_proxy_health_check_proxy_error(self, mock_get):
        """Test proxy health check with proxy error"""
        pm = ProxyManager(provider='scraperapi', api_key='test_key')
        mock_get.side_effect = requests.exceptions.ProxyError()

        health = pm.test_proxy_health('http://test-proxy:8001')

        assert health['healthy'] is False
        assert 'proxy' in health['error'].lower()

    def test_mark_proxy_failed(self):
        """Test marking proxy as failed"""
        pm = ProxyManager(provider='scraperapi', api_key='test_key', max_retries=3)
        proxy = pm.get_proxy()

        pm.mark_proxy_failed(proxy)
        assert pm.failed_attempts[proxy] == 1

        pm.mark_proxy_failed(proxy)
        assert pm.failed_attempts[proxy] == 2

    def test_mark_proxy_healthy(self):
        """Test marking proxy as healthy"""
        pm = ProxyManager(provider='scraperapi', api_key='test_key')
        proxy = pm.get_proxy()

        pm.mark_proxy_failed(proxy)
        assert pm.failed_attempts[proxy] == 1

        pm.mark_proxy_healthy(proxy)
        assert pm.failed_attempts[proxy] == 0
        assert proxy in pm.healthy_proxies

    def test_get_stats(self):
        """Test statistics reporting"""
        pm = ProxyManager(provider='scraperapi', api_key='test_key')
        stats = pm.get_stats()

        assert 'provider' in stats
        assert stats['provider'] == 'scraperapi'
        assert 'strategy' in stats
        assert 'api_key_configured' in stats
        assert stats['api_key_configured'] is True


class TestCaptchaSolver:
    """Test CaptchaSolver functionality"""

    def test_init_with_api_key(self):
        """Test initialization with API key"""
        solver = CaptchaSolver(api_key='test_key_123')
        assert solver.api_key == 'test_key_123'
        assert solver.timeout == 180

    def test_init_without_api_key(self):
        """Test initialization without API key (reads from env)"""
        solver = CaptchaSolver(api_key=None)
        # Should succeed but api_key will be None if env not set
        assert solver is not None

    @patch('requests.post')
    def test_submit_image_captcha(self, mock_post):
        """Test image CAPTCHA submission"""
        solver = CaptchaSolver(api_key='test_key')
        mock_response = Mock()
        mock_response.text = 'OK|12345678901234567890'
        mock_post.return_value = mock_response

        captcha_id = solver._submit_image_captcha(image_base64='base64_encoded_image')

        assert captcha_id == '12345678901234567890'

    @patch('requests.post')
    def test_submit_recaptcha_v2(self, mock_post):
        """Test reCAPTCHA v2 submission"""
        solver = CaptchaSolver(api_key='test_key')
        mock_response = Mock()
        mock_response.text = 'OK|87654321098765432100'
        mock_post.return_value = mock_response

        captcha_id = solver._submit_recaptcha_v2(
            site_key='test_site_key',
            page_url='https://example.com'
        )

        assert captcha_id == '87654321098765432100'

    @patch('requests.post')
    def test_submit_hcaptcha(self, mock_post):
        """Test hCaptcha submission"""
        solver = CaptchaSolver(api_key='test_key')
        mock_response = Mock()
        mock_response.text = 'OK|hcaptcha_id_123'
        mock_post.return_value = mock_response

        captcha_id = solver._submit_hcaptcha(
            site_key='test_site_key',
            page_url='https://example.com'
        )

        assert captcha_id == 'hcaptcha_id_123'

    @patch.object(CaptchaSolver, '_poll_solution')
    @patch.object(CaptchaSolver, '_submit_captcha')
    def test_solve_captcha_success(self, mock_submit, mock_poll):
        """Test successful CAPTCHA solving"""
        solver = CaptchaSolver(api_key='test_key')
        mock_submit.return_value = 'captcha_123'
        mock_poll.return_value = 'solution_token_xyz'

        result = solver.solve_captcha(
            captcha_type='image',
            image_url='https://example.com/image.png'
        )

        assert result['success'] is True
        assert result['captcha_id'] == 'captcha_123'
        assert result['token'] == 'solution_token_xyz'
        assert result['type'] == 'image'
        assert result['error'] is None

    @patch.object(CaptchaSolver, '_poll_solution')
    @patch.object(CaptchaSolver, '_submit_captcha')
    def test_solve_captcha_failure(self, mock_submit, mock_poll):
        """Test failed CAPTCHA solving"""
        solver = CaptchaSolver(api_key='test_key')
        mock_submit.return_value = 'captcha_123'
        mock_poll.return_value = None  # Solution not obtained

        result = solver.solve_captcha(
            captcha_type='image',
            image_url='https://example.com/image.png',
            max_retries=1
        )

        assert result['success'] is False
        assert result['token'] is None
        assert 'Failed to solve CAPTCHA' in result['error']

    def test_solve_captcha_missing_required_fields(self):
        """Test CAPTCHA solving with missing required fields"""
        solver = CaptchaSolver(api_key='test_key')

        # Image CAPTCHA without image
        result = solver.solve_captcha(captcha_type='image')
        assert result['success'] is False
        assert 'image_url or image_base64' in result['error']

        # reCAPTCHA without site_key
        result = solver.solve_captcha(captcha_type='recaptcha_v2', page_url='https://example.com')
        assert result['success'] is False
        assert 'site_key and page_url' in result['error']

    @patch('requests.get')
    def test_poll_solution_success(self, mock_get):
        """Test successful CAPTCHA solution polling"""
        solver = CaptchaSolver(api_key='test_key')
        mock_response = Mock()
        mock_response.json.return_value = {'status': 1, 'request': 'solution_token_123'}
        mock_get.return_value = mock_response

        solution = solver._poll_solution('captcha_123', timeout=30)

        assert solution == 'solution_token_123'

    @patch('requests.get')
    def test_poll_solution_timeout(self, mock_get):
        """Test CAPTCHA polling timeout"""
        solver = CaptchaSolver(api_key='test_key', timeout=1)
        mock_response = Mock()
        mock_response.json.return_value = {'status': 0}  # Still processing
        mock_get.return_value = mock_response

        solution = solver._poll_solution('captcha_123', timeout=1, poll_interval=0.5)

        assert solution is None

    @patch('requests.post')
    def test_report_bad_captcha(self, mock_post):
        """Test bad CAPTCHA reporting"""
        solver = CaptchaSolver(api_key='test_key')
        mock_response = Mock()
        mock_response.text = 'OK'
        mock_post.return_value = mock_response

        result = solver.report_bad('captcha_123')

        assert result is True

    @patch('requests.get')
    def test_get_balance(self, mock_get):
        """Test account balance checking"""
        solver = CaptchaSolver(api_key='test_key')
        mock_response = Mock()
        mock_response.text = '25.50'
        mock_get.return_value = mock_response

        balance = solver.get_balance()

        assert balance == 25.50

    def test_estimate_cost(self):
        """Test CAPTCHA cost estimation"""
        solver = CaptchaSolver(api_key='test_key')

        assert solver._estimate_cost('image') == 0.0002
        assert solver._estimate_cost('recaptcha_v2') == 0.0003
        assert solver._estimate_cost('hcaptcha') == 0.0003
        assert solver._estimate_cost('funcaptcha') == 0.0005

    def test_get_stats(self):
        """Test statistics reporting"""
        solver = CaptchaSolver(api_key='test_key')
        solver.total_solved = 100
        solver.total_cost = 0.025

        stats = solver.get_stats()

        assert stats['total_solved'] == 100
        assert stats['total_cost_usd'] == 0.025
        assert stats['api_key_configured'] is True


class TestBaseScraperWithProxy:
    """Test BaseScraper with proxy integration"""

    def test_scraper_init_with_proxy(self):
        """Test scraper initialization with proxy enabled"""
        class TestScraper(BaseScraper):
            def parse_listings(self):
                return []

        scraper = TestScraper('test_platform', use_proxy=True)
        assert scraper.use_proxy is True
        # Note: proxy_manager might be None if env vars not set

    def test_scraper_init_without_proxy(self):
        """Test scraper initialization with proxy disabled"""
        class TestScraper(BaseScraper):
            def parse_listings(self):
                return []

        scraper = TestScraper('test_platform', use_proxy=False)
        assert scraper.use_proxy is False
        assert scraper.proxy_manager is None

    @patch('requests.Session.get')
    def test_fetch_page_with_proxy(self, mock_get):
        """Test fetch_page uses proxy when available"""
        class TestScraper(BaseScraper):
            def parse_listings(self):
                return []

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b'<html><body>Test</body></html>'
        mock_get.return_value = mock_response

        with patch.object(ProxyManager, 'get_proxy', return_value='http://test:8001'):
            scraper = TestScraper('test', use_proxy=True)
            scraper.proxy_manager = ProxyManager(provider='scraperapi', api_key='test')

            result = scraper.fetch_page('https://example.com')

            assert result is not None
            # Verify proxy was used in request
            call_kwargs = mock_get.call_args[1]
            assert 'proxies' in call_kwargs

    @patch('requests.Session.get')
    def test_fetch_page_retry_with_backoff(self, mock_get):
        """Test fetch_page retries with exponential backoff"""
        class TestScraper(BaseScraper):
            def parse_listings(self):
                return []

        scraper = TestScraper('test', use_proxy=False)
        scraper.max_retries = 3

        # Fail first 2 times, succeed on 3rd
        mock_get.side_effect = [
            requests.exceptions.ConnectionError(),
            requests.exceptions.Timeout(),
            Mock(status_code=200, content=b'<html>Success</html>')
        ]

        start = time.time()
        result = scraper.fetch_page('https://example.com')
        elapsed = time.time() - start

        # Should succeed on 3rd attempt
        assert result is not None
        # Should have waited with exponential backoff (1 + 2 = 3 seconds minimum)
        assert elapsed >= 3

    @patch('requests.Session.get')
    def test_fetch_page_marks_proxy_failed(self, mock_get):
        """Test that failed requests mark proxy as failed"""
        class TestScraper(BaseScraper):
            def parse_listings(self):
                return []

        mock_get.side_effect = requests.exceptions.ConnectionError()

        with patch.object(ProxyManager, 'get_proxy', return_value='http://test:8001'):
            scraper = TestScraper('test', use_proxy=True)
            scraper.proxy_manager = ProxyManager(provider='scraperapi', api_key='test')

            # Stub mark_proxy_failed to track calls
            scraper.proxy_manager.mark_proxy_failed = Mock()

            scraper.fetch_page('https://example.com')

            # Verify mark_proxy_failed was called
            scraper.proxy_manager.mark_proxy_failed.assert_called()


class TestIntegration:
    """Integration tests for resilience features"""

    @patch('backend.services.proxy_manager.requests.get')
    @patch('requests.Session.get')
    def test_scraper_with_all_features(self, mock_session_get, mock_proxy_check):
        """Test scraper with both proxy and CAPTCHA features enabled"""
        class TestScraper(BaseScraper):
            def parse_listings(self):
                self.fetch_page('https://example.com')
                return []

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b'<html><body>Test</body></html>'
        mock_session_get.return_value = mock_response

        mock_health = Mock()
        mock_health.status_code = 200
        mock_proxy_check.return_value = mock_health

        scraper = TestScraper('test_platform', use_proxy=True, use_captcha_solver=True)

        # Should initialize without error
        assert scraper is not None
        assert scraper.use_proxy is True
        assert scraper.use_captcha_solver is True


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
