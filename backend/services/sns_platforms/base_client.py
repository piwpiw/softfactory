"""Base SNS Platform Client with simulation mode"""

import os
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any


class SNSPlatformClient(ABC):
    """Abstract base class for SNS platform clients"""

    def __init__(self, access_token: Optional[str] = None,
                 refresh_token: Optional[str] = None,
                 simulation_mode: bool = False):
        """
        Initialize platform client.

        Args:
            access_token: OAuth access token (required unless simulation_mode=True)
            refresh_token: OAuth refresh token for renewal
            simulation_mode: If True, return mock data without API calls
        """
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.simulation_mode = simulation_mode or not access_token
        self.platform = self.__class__.__name__.replace('Client', '').lower()

    @abstractmethod
    def get_auth_url(self) -> str:
        """Generate OAuth authorization URL for user login"""
        pass

    @abstractmethod
    def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        """Exchange authorization code for access/refresh tokens"""
        pass

    @abstractmethod
    def refresh_token_if_expired(self, expires_at: datetime) -> Optional[Dict[str, Any]]:
        """Refresh token if expired. Returns new token data or None if not expired"""
        pass

    @abstractmethod
    def post_content(self, content: str, media_urls: Optional[List[str]] = None,
                     hashtags: Optional[List[str]] = None,
                     link_url: Optional[str] = None) -> Dict[str, Any]:
        """Publish content to platform"""
        pass

    @abstractmethod
    def get_analytics(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get analytics for account"""
        pass

    @abstractmethod
    def get_inbox_messages(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent DMs, comments, mentions"""
        pass

    @abstractmethod
    def reply_to_comment(self, comment_id: str, reply_text: str) -> Dict[str, Any]:
        """Reply to comment on platform"""
        pass

    # Simulation mode implementations (fallback)
    def _simulate_post(self, content: str) -> Dict[str, Any]:
        """Return mock post response"""
        import random
        post_id = f"sim_{self.platform}_{int(random.random() * 1000000)}"
        return {
            'success': True,
            'external_post_id': post_id,
            'platform': self.platform,
            'published_at': datetime.utcnow().isoformat(),
            'url': f"https://{self.platform}.com/posts/{post_id}",
        }

    def _simulate_analytics(self) -> Dict[str, Any]:
        """Return mock analytics"""
        import random
        return {
            'followers': random.randint(1000, 100000),
            'engagement': random.randint(50, 5000),
            'reach': random.randint(1000, 50000),
            'impressions': random.randint(5000, 100000),
            'period': 'last_7_days',
        }

    def _simulate_messages(self) -> List[Dict[str, Any]]:
        """Return mock inbox messages"""
        return [
            {
                'id': f'sim_msg_1',
                'sender': 'user_123',
                'message': 'Love your content!',
                'type': 'comment',
                'timestamp': datetime.utcnow().isoformat(),
            },
            {
                'id': f'sim_msg_2',
                'sender': 'user_456',
                'message': 'When is the next live stream?',
                'type': 'dm',
                'timestamp': (datetime.utcnow() - timedelta(hours=2)).isoformat(),
            },
        ]
