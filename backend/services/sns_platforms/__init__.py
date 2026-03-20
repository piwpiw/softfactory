"""SNS Platform Clients Factory"""

from .instagram_client import InstagramClient
from .facebook_client import FacebookClient
from .twitter_client import TwitterClient
from .linkedin_client import LinkedInClient
from .tiktok_client import TikTokClient
from .youtube_client import YouTubeClient
from .pinterest_client import PinterestClient
from .threads_client import ThreadsClient
from .youtube_shorts_client import YouTubeShortsClient
from .wordpress_client import WordPressClient

PLATFORM_CLIENTS = {
    'instagram': InstagramClient,
    'facebook': FacebookClient,
    'twitter': TwitterClient,
    'linkedin': LinkedInClient,
    'tiktok': TikTokClient,
    'youtube': YouTubeClient,
    'pinterest': PinterestClient,
    'threads': ThreadsClient,
    'youtube_shorts': YouTubeShortsClient,
    'blog': WordPressClient,
    'wordpress': WordPressClient,
}

def get_client(platform, access_token=None, refresh_token=None, simulation_mode=False,
               site_url=None, wp_username=None):
    """
    Get platform client instance.

    Args:
        platform: 'instagram', 'facebook', 'blog', 'wordpress', etc.
        access_token: OAuth access token (WordPress: Application Password)
        refresh_token: OAuth refresh token
        simulation_mode: If True, return mock data without calling platform API
        site_url: WordPress site URL (e.g. 'https://myblog.com') — blog/wordpress only
        wp_username: WordPress username — blog/wordpress only

    Returns:
        Platform client instance or None if invalid platform
    """
    if platform not in PLATFORM_CLIENTS:
        return None

    client_class = PLATFORM_CLIENTS[platform]

    if platform in ('blog', 'wordpress'):
        return client_class(access_token, refresh_token, simulation_mode,
                            site_url=site_url, wp_username=wp_username)

    return client_class(access_token, refresh_token, simulation_mode)


__all__ = [
    'get_client',
    'PLATFORM_CLIENTS',
    'InstagramClient',
    'FacebookClient',
    'TwitterClient',
    'LinkedInClient',
    'TikTokClient',
    'YouTubeClient',
    'PinterestClient',
    'ThreadsClient',
    'YouTubeShortsClient',
    'WordPressClient',
]
