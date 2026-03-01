"""CAPTCHA Solving for Anti-Bot Protection Bypass

Integrates with 2Captcha API to automatically solve CAPTCHA challenges
encountered during web scraping. Supports multiple CAPTCHA types.

Supported types:
- reCAPTCHA v2
- reCAPTCHA v3
- hCaptcha
- Image CAPTCHA

Token budget: ~300 per CAPTCHA solve (API calls + status checks)
"""

import os
import logging
import time
import requests
from typing import Optional, Dict
from enum import Enum

logger = logging.getLogger('scraper.captcha')


class CaptchaType(Enum):
    """Supported CAPTCHA types"""
    RECAPTCHA_V2 = 1          # reCAPTCHA v2 (I'm not a robot)
    RECAPTCHA_V3 = 4          # reCAPTCHA v3 (invisible)
    HCAPTCHA = 7              # hCaptcha
    IMAGE_CAPTCHA = 2         # Image-based CAPTCHA
    FUNCAPTCHA = 6            # FunCaptcha/Arkose
    GEETEST = 8               # GeeTest CAPTCHA


class CaptchaSolver:
    """
    Solves CAPTCHAs using 2Captcha service.

    2Captcha is a CAPTCHA solving service that can solve:
    - Text-based CAPTCHAs (image recognition)
    - reCAPTCHA v2 & v3
    - hCaptcha
    - Other anti-bot challenges

    Pricing: ~$0.0003 per CAPTCHA (very cheap bulk solving)

    Example:
        solver = CaptchaSolver(api_key='your_2captcha_key')
        solution = solver.solve_captcha(
            captcha_type='recaptcha_v2',
            image_url='https://...',  # OR
            site_key='...',           # for reCAPTCHA
            page_url='https://...'
        )
        print(solution['token'])  # Use token to bypass CAPTCHA
    """

    API_BASE = "http://2captcha.com"

    def __init__(self, api_key: str = None, timeout: int = 180, debug: bool = False):
        """
        Initialize CaptchaSolver.

        Args:
            api_key: 2Captcha API key (read from env if not provided)
            timeout: Maximum wait time for CAPTCHA solution in seconds (default: 3 min)
            debug: Enable debug logging
        """
        if api_key:
            self.api_key = api_key
        else:
            self.api_key = os.getenv('2CAPTCHA_KEY')

        if not self.api_key:
            logger.warning("2CAPTCHA_KEY not configured - CAPTCHA solving disabled")

        self.timeout = timeout
        self.debug = debug
        self.session = requests.Session()

        # Cost tracking
        self.total_solved = 0
        self.total_cost = 0.0  # in USD

        logger.info(f"CaptchaSolver initialized: api_key={'***' if self.api_key else 'None'}")

    def solve_captcha(
        self,
        captcha_type: str = "image",
        image_url: str = None,
        image_base64: str = None,
        site_key: str = None,
        page_url: str = None,
        max_retries: int = 3,
        retry_delay: int = 5
    ) -> Optional[Dict]:
        """
        Solve a CAPTCHA challenge.

        Args:
            captcha_type: Type of CAPTCHA ('image', 'recaptcha_v2', 'recaptcha_v3', 'hcaptcha')
            image_url: URL of CAPTCHA image (for image CAPTCHAs)
            image_base64: Base64-encoded image (alternative to image_url)
            site_key: reCAPTCHA site key (for reCAPTCHA)
            page_url: Page URL (required for reCAPTCHA, hCaptcha)
            max_retries: Maximum retries on temporary failures
            retry_delay: Delay between retries in seconds

        Returns:
            Dictionary with solution:
            {
                'success': bool,
                'captcha_id': str,     # 2Captcha ID for this request
                'token': str,          # Solution/token to use
                'type': str,           # CAPTCHA type solved
                'time_taken': float,   # Seconds to solve
                'cost': float,         # Cost in USD
                'error': str or None   # Error message if failed
            }

            Example response:
            {
                'success': True,
                'captcha_id': '12345678901234567890',
                'token': '0123456789abcdef...',  # Use in g-recaptcha-response
                'type': 'recaptcha_v2',
                'time_taken': 15.3,
                'cost': 0.0005,
                'error': None
            }
        """
        if not self.api_key:
            return {
                'success': False,
                'captcha_id': None,
                'token': None,
                'type': captcha_type,
                'time_taken': 0,
                'cost': 0,
                'error': '2CAPTCHA_KEY not configured'
            }

        start_time = time.time()

        # Validate inputs
        if captcha_type == "image" and not (image_url or image_base64):
            return {
                'success': False,
                'captcha_id': None,
                'token': None,
                'type': captcha_type,
                'time_taken': 0,
                'cost': 0,
                'error': 'image_url or image_base64 required for image CAPTCHA'
            }

        if captcha_type.startswith("recaptcha") and not (site_key and page_url):
            return {
                'success': False,
                'captcha_id': None,
                'token': None,
                'type': captcha_type,
                'time_taken': 0,
                'cost': 0,
                'error': 'site_key and page_url required for reCAPTCHA'
            }

        # Submit CAPTCHA for solving
        for attempt in range(max_retries):
            try:
                captcha_id = self._submit_captcha(
                    captcha_type, image_url, image_base64, site_key, page_url
                )

                if not captcha_id:
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                    continue

                # Poll for solution
                token = self._poll_solution(captcha_id, timeout=self.timeout)

                if token:
                    time_taken = time.time() - start_time
                    cost = self._estimate_cost(captcha_type)

                    self.total_solved += 1
                    self.total_cost += cost

                    logger.info(
                        f"CAPTCHA solved: id={captcha_id}, type={captcha_type}, "
                        f"time={time_taken:.1f}s, cost=${cost:.4f}"
                    )

                    return {
                        'success': True,
                        'captcha_id': captcha_id,
                        'token': token,
                        'type': captcha_type,
                        'time_taken': time_taken,
                        'cost': cost,
                        'error': None
                    }
                else:
                    logger.warning(f"Failed to get solution for CAPTCHA {captcha_id}")
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)

            except Exception as e:
                logger.error(f"CAPTCHA solving error (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)

        # All retries exhausted
        time_taken = time.time() - start_time
        return {
            'success': False,
            'captcha_id': None,
            'token': None,
            'type': captcha_type,
            'time_taken': time_taken,
            'cost': 0,
            'error': f'Failed to solve CAPTCHA after {max_retries} attempts'
        }

    def _submit_captcha(
        self,
        captcha_type: str,
        image_url: str = None,
        image_base64: str = None,
        site_key: str = None,
        page_url: str = None
    ) -> Optional[str]:
        """
        Submit CAPTCHA to 2Captcha for solving.

        Returns:
            Captcha ID (string) for polling, or None if submission failed
        """
        if captcha_type == "image":
            return self._submit_image_captcha(image_url, image_base64)
        elif captcha_type == "recaptcha_v2":
            return self._submit_recaptcha_v2(site_key, page_url)
        elif captcha_type == "recaptcha_v3":
            return self._submit_recaptcha_v3(site_key, page_url)
        elif captcha_type == "hcaptcha":
            return self._submit_hcaptcha(site_key, page_url)
        else:
            logger.error(f"Unknown CAPTCHA type: {captcha_type}")
            return None

    def _submit_image_captcha(self, image_url: str = None, image_base64: str = None) -> Optional[str]:
        """Submit image-based CAPTCHA"""
        url = f"{self.API_BASE}/api/upload"
        data = {'apikey': self.api_key}

        try:
            if image_base64:
                data['captchafile'] = image_base64
            elif image_url:
                # Download image first
                resp = requests.get(image_url, timeout=10)
                import base64
                data['captchafile'] = base64.b64encode(resp.content).decode()
            else:
                return None

            response = requests.post(url, data=data, timeout=10)
            result = response.text.strip()

            if result.startswith('OK|'):
                captcha_id = result.split('|')[1]
                logger.debug(f"Image CAPTCHA submitted: {captcha_id}")
                return captcha_id
            else:
                logger.error(f"Image CAPTCHA submission failed: {result}")
                return None

        except Exception as e:
            logger.error(f"Image CAPTCHA submission error: {e}")
            return None

    def _submit_recaptcha_v2(self, site_key: str, page_url: str) -> Optional[str]:
        """Submit reCAPTCHA v2 (I'm not a robot)"""
        url = f"{self.API_BASE}/api/upload"
        data = {
            'apikey': self.api_key,
            'method': 'userrecaptcha',
            'googlekey': site_key,
            'pageurl': page_url
        }

        try:
            response = requests.post(url, data=data, timeout=10)
            result = response.text.strip()

            if result.startswith('OK|'):
                captcha_id = result.split('|')[1]
                logger.debug(f"reCAPTCHA v2 submitted: {captcha_id}")
                return captcha_id
            else:
                logger.error(f"reCAPTCHA v2 submission failed: {result}")
                return None

        except Exception as e:
            logger.error(f"reCAPTCHA v2 submission error: {e}")
            return None

    def _submit_recaptcha_v3(self, site_key: str, page_url: str) -> Optional[str]:
        """Submit reCAPTCHA v3 (invisible)"""
        url = f"{self.API_BASE}/api/upload"
        data = {
            'apikey': self.api_key,
            'method': 'userrecaptcha',
            'googlekey': site_key,
            'pageurl': page_url,
            'version': 'v3'
        }

        try:
            response = requests.post(url, data=data, timeout=10)
            result = response.text.strip()

            if result.startswith('OK|'):
                captcha_id = result.split('|')[1]
                logger.debug(f"reCAPTCHA v3 submitted: {captcha_id}")
                return captcha_id
            else:
                logger.error(f"reCAPTCHA v3 submission failed: {result}")
                return None

        except Exception as e:
            logger.error(f"reCAPTCHA v3 submission error: {e}")
            return None

    def _submit_hcaptcha(self, site_key: str, page_url: str) -> Optional[str]:
        """Submit hCaptcha"""
        url = f"{self.API_BASE}/api/upload"
        data = {
            'apikey': self.api_key,
            'method': 'hcaptcha',
            'sitekey': site_key,
            'pageurl': page_url
        }

        try:
            response = requests.post(url, data=data, timeout=10)
            result = response.text.strip()

            if result.startswith('OK|'):
                captcha_id = result.split('|')[1]
                logger.debug(f"hCaptcha submitted: {captcha_id}")
                return captcha_id
            else:
                logger.error(f"hCaptcha submission failed: {result}")
                return None

        except Exception as e:
            logger.error(f"hCaptcha submission error: {e}")
            return None

    def _poll_solution(self, captcha_id: str, timeout: int = 180, poll_interval: int = 3) -> Optional[str]:
        """
        Poll 2Captcha for solution.

        Args:
            captcha_id: CAPTCHA ID from submission
            timeout: Maximum time to wait in seconds
            poll_interval: Seconds between polls

        Returns:
            Solution token/text, or None if not solved within timeout
        """
        url = f"{self.API_BASE}/api/res"
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                params = {
                    'apikey': self.api_key,
                    'action': 'get',
                    'id': captcha_id,
                    'json': 1
                }

                response = requests.get(url, params=params, timeout=10)
                result = response.json()

                if result.get('status') == 0:
                    # Not ready yet
                    if self.debug:
                        logger.debug(f"CAPTCHA {captcha_id} still processing...")
                    time.sleep(poll_interval)
                    continue

                elif result.get('status') == 1:
                    # Success
                    token = result.get('request')
                    logger.debug(f"CAPTCHA {captcha_id} solved: {token[:20]}...")
                    return token

                else:
                    # Error
                    error = result.get('error_text', 'Unknown error')
                    logger.error(f"CAPTCHA {captcha_id} error: {error}")
                    return None

            except Exception as e:
                logger.error(f"Polling error for {captcha_id}: {e}")
                time.sleep(poll_interval)

        logger.error(f"CAPTCHA {captcha_id} timeout after {timeout}s")
        return None

    def report_bad(self, captcha_id: str) -> bool:
        """
        Report unsolved/incorrect CAPTCHA to 2Captcha for refund.

        Args:
            captcha_id: CAPTCHA ID to report

        Returns:
            True if reported successfully
        """
        url = f"{self.API_BASE}/api/report"
        data = {
            'apikey': self.api_key,
            'id': captcha_id,
            'action': 'report'
        }

        try:
            response = requests.post(url, data=data, timeout=10)
            if 'OK' in response.text:
                logger.info(f"CAPTCHA {captcha_id} reported as bad (refunded)")
                return True
            else:
                logger.warning(f"Failed to report CAPTCHA {captcha_id}")
                return False
        except Exception as e:
            logger.error(f"Error reporting CAPTCHA {captcha_id}: {e}")
            return False

    def get_balance(self) -> Optional[float]:
        """
        Get 2Captcha account balance in USD.

        Returns:
            Account balance or None if error
        """
        url = f"{self.API_BASE}/api/user"
        params = {'apikey': self.api_key, 'action': 'getbalance'}

        try:
            response = requests.get(url, params=params, timeout=10)
            balance = float(response.text.strip())
            logger.info(f"2Captcha balance: ${balance:.2f}")
            return balance
        except Exception as e:
            logger.error(f"Error fetching balance: {e}")
            return None

    def _estimate_cost(self, captcha_type: str) -> float:
        """
        Estimate cost of solving CAPTCHA based on type.

        Costs are approximate and based on 2Captcha pricing (as of 2026).

        Args:
            captcha_type: Type of CAPTCHA

        Returns:
            Estimated cost in USD
        """
        costs = {
            'image': 0.0002,           # Image CAPTCHA: $0.0002
            'recaptcha_v2': 0.0003,    # reCAPTCHA v2: $0.0003
            'recaptcha_v3': 0.0003,    # reCAPTCHA v3: $0.0003
            'hcaptcha': 0.0003,        # hCaptcha: $0.0003
            'funcaptcha': 0.0005,      # FunCaptcha: $0.0005
            'geetest': 0.0005,         # GeeTest: $0.0005
        }

        return costs.get(captcha_type, 0.0003)

    def get_stats(self) -> Dict:
        """
        Get CAPTCHA solver statistics.

        Returns:
            Dictionary with solved count and total cost
        """
        return {
            'total_solved': self.total_solved,
            'total_cost_usd': round(self.total_cost, 4),
            'avg_cost_per_solve': round(self.total_cost / self.total_solved, 6) if self.total_solved > 0 else 0,
            'api_key_configured': bool(self.api_key),
        }
