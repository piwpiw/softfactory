"""WordPress REST API Client

Authentication: WordPress Application Passwords (WP 5.6+)
API: /wp-json/wp/v2/posts, /pages, /media, /categories, /tags

Setup on WordPress side:
  Users → Profile → Application Passwords → Add new
  Provide generated password as `access_token`, site URL as `site_url` in SNSAccount.
"""

import os
import base64
import logging
from typing import Optional, Dict, List, Any
from datetime import datetime

import requests

from .base_client import SNSPlatformClient

logger = logging.getLogger('sns.wordpress')


class WordPressClient(SNSPlatformClient):
    """WordPress REST API v2 client using Application Passwords."""

    def __init__(self, access_token: Optional[str] = None,
                 refresh_token: Optional[str] = None,
                 simulation_mode: bool = False,
                 site_url: Optional[str] = None,
                 wp_username: Optional[str] = None):
        super().__init__(access_token, refresh_token, simulation_mode)
        # site_url: e.g. "https://myblog.com"  (no trailing slash)
        self.site_url = (site_url or os.getenv('WP_SITE_URL', '')).rstrip('/')
        self.wp_username = wp_username or os.getenv('WP_USERNAME', 'admin')
        self.api_base = f"{self.site_url}/wp-json/wp/v2" if self.site_url else ''
        self.platform = 'wordpress'

    # ── auth helpers ──────────────────────────────────────────────────────────

    def _auth_header(self) -> Dict[str, str]:
        """Return Basic Auth header using username + Application Password."""
        credentials = f"{self.wp_username}:{self.access_token}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return {'Authorization': f'Basic {encoded}'}

    def _headers(self) -> Dict[str, str]:
        return {**self._auth_header(), 'Content-Type': 'application/json'}

    def _request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        url = f"{self.api_base}/{endpoint.lstrip('/')}"
        timeout = kwargs.pop('timeout', 20)
        resp = requests.request(method, url, headers=self._headers(),
                                timeout=timeout, **kwargs)
        resp.raise_for_status()
        return resp

    # ── SNSPlatformClient interface ───────────────────────────────────────────

    def get_auth_url(self) -> str:
        """WordPress uses Application Passwords — no OAuth redirect needed."""
        return f"{self.site_url}/wp-admin/profile.php#application-passwords-section"

    def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        """Not applicable for Application Password auth."""
        return {'note': 'WordPress uses Application Passwords, no code exchange needed.'}

    def refresh_token_if_expired(self, expires_at: datetime) -> Optional[Dict[str, Any]]:
        """Application Passwords do not expire."""
        return None

    def post_content(self, content: str, media_urls: Optional[List[str]] = None,
                     hashtags: Optional[List[str]] = None,
                     link_url: Optional[str] = None,
                     title: Optional[str] = None,
                     status: str = 'publish',
                     categories: Optional[List[int]] = None,
                     tags: Optional[List[int]] = None,
                     excerpt: Optional[str] = None) -> Dict[str, Any]:
        """
        Create or publish a WordPress post.

        Args:
            content: HTML or plain-text post body.
            media_urls: If provided, first URL is set as featured image (uploaded).
            hashtags: Converted to WordPress tags (by name).
            link_url: Appended as a "Read more" link at end of content.
            title: Post title (auto-generated from first line if omitted).
            status: 'publish' | 'draft' | 'future' | 'pending'
            categories: List of category IDs.
            tags: List of tag IDs. (hashtags are converted and merged)
            excerpt: Short excerpt / meta description.

        Returns:
            {'success': bool, 'external_post_id': str, 'url': str, ...}
        """
        if self.simulation_mode:
            return self._simulate_post(content)

        if not self.site_url or not self.access_token:
            return {'success': False, 'error': 'site_url and access_token required'}

        try:
            # Build post body
            body_content = content
            if link_url:
                body_content += f'\n\n<p><a href="{link_url}" target="_blank" rel="noopener">더 보기 →</a></p>'

            # Auto title from first line if not given
            post_title = title or content.split('\n')[0][:100].strip('#').strip()

            # Resolve hashtag names → tag IDs
            resolved_tag_ids = list(tags or [])
            if hashtags:
                resolved_tag_ids += self._resolve_tags(hashtags)

            payload: Dict[str, Any] = {
                'title': post_title,
                'content': body_content,
                'status': status,
            }
            if categories:
                payload['categories'] = categories
            if resolved_tag_ids:
                payload['tags'] = list(set(resolved_tag_ids))
            if excerpt:
                payload['excerpt'] = excerpt

            # Upload featured image if provided
            if media_urls:
                featured_id = self._upload_media_from_url(media_urls[0])
                if featured_id:
                    payload['featured_media'] = featured_id

            resp = self._request('POST', 'posts', json=payload)
            data = resp.json()

            return {
                'success': True,
                'external_post_id': str(data.get('id')),
                'platform': 'wordpress',
                'url': data.get('link', ''),
                'status': data.get('status'),
                'published_at': data.get('date', datetime.utcnow().isoformat()),
            }

        except requests.HTTPError as e:
            logger.error(f"[WordPress] post_content HTTP error: {e.response.text}")
            return {'success': False, 'error': str(e), 'detail': e.response.text}
        except Exception as e:
            logger.error(f"[WordPress] post_content error: {e}")
            return {'success': False, 'error': str(e)}

    def update_post(self, post_id: int, **kwargs) -> Dict[str, Any]:
        """Update an existing WordPress post."""
        if self.simulation_mode:
            return {'success': True, 'external_post_id': str(post_id)}
        try:
            resp = self._request('POST', f'posts/{post_id}', json=kwargs)
            data = resp.json()
            return {'success': True, 'external_post_id': str(data['id']), 'url': data.get('link', '')}
        except Exception as e:
            logger.error(f"[WordPress] update_post error: {e}")
            return {'success': False, 'error': str(e)}

    def get_analytics(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """WordPress does not expose analytics via REST API — returns basic post stats."""
        if self.simulation_mode:
            return self._simulate_analytics()
        try:
            resp = self._request('GET', 'posts', params={'per_page': 10, 'orderby': 'date', 'order': 'desc'})
            posts = resp.json()
            return {
                'platform': 'wordpress',
                'recent_posts': len(posts),
                'note': 'Full analytics require Jetpack Stats or Google Analytics integration.',
                'period': f"{start_date.date()} – {end_date.date()}",
            }
        except Exception as e:
            logger.error(f"[WordPress] get_analytics error: {e}")
            return {'error': str(e)}

    def get_inbox_messages(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Fetch recent pending comments as 'inbox'."""
        if self.simulation_mode:
            return self._simulate_messages()
        try:
            resp = self._request('GET', 'comments', params={'status': 'hold', 'per_page': min(limit, 100)})
            comments = resp.json()
            return [
                {
                    'id': str(c['id']),
                    'sender': c.get('author_name', 'Anonymous'),
                    'message': c.get('content', {}).get('rendered', ''),
                    'type': 'comment',
                    'post_id': c.get('post'),
                    'timestamp': c.get('date', ''),
                }
                for c in comments
            ]
        except Exception as e:
            logger.error(f"[WordPress] get_inbox_messages error: {e}")
            return []

    def reply_to_comment(self, comment_id: str, reply_text: str) -> Dict[str, Any]:
        """Reply to a WordPress comment."""
        if self.simulation_mode:
            return {'success': True, 'comment_id': comment_id}
        try:
            resp = self._request('POST', 'comments', json={
                'parent': int(comment_id),
                'content': reply_text,
                'status': 'approve',
            })
            data = resp.json()
            return {'success': True, 'comment_id': str(data['id'])}
        except Exception as e:
            logger.error(f"[WordPress] reply_to_comment error: {e}")
            return {'success': False, 'error': str(e)}

    # ── WordPress-specific helpers ────────────────────────────────────────────

    def get_categories(self) -> List[Dict[str, Any]]:
        """List all WordPress categories."""
        try:
            resp = self._request('GET', 'categories', params={'per_page': 100})
            return [{'id': c['id'], 'name': c['name'], 'slug': c['slug']} for c in resp.json()]
        except Exception as e:
            logger.error(f"[WordPress] get_categories error: {e}")
            return []

    def get_tags(self) -> List[Dict[str, Any]]:
        """List all WordPress tags."""
        try:
            resp = self._request('GET', 'tags', params={'per_page': 100})
            return [{'id': t['id'], 'name': t['name'], 'slug': t['slug']} for t in resp.json()]
        except Exception as e:
            logger.error(f"[WordPress] get_tags error: {e}")
            return []

    def _resolve_tags(self, hashtags: List[str]) -> List[int]:
        """
        Convert hashtag strings to WordPress tag IDs.
        Creates the tag if it doesn't exist.
        """
        tag_ids = []
        for tag_name in hashtags:
            clean = tag_name.lstrip('#').strip()
            if not clean:
                continue
            try:
                # Search existing
                resp = self._request('GET', 'tags', params={'search': clean, 'per_page': 5})
                existing = [t for t in resp.json() if t['name'].lower() == clean.lower()]
                if existing:
                    tag_ids.append(existing[0]['id'])
                else:
                    # Create new tag
                    create_resp = self._request('POST', 'tags', json={'name': clean})
                    tag_ids.append(create_resp.json()['id'])
            except Exception as e:
                logger.warning(f"[WordPress] _resolve_tags failed for '{clean}': {e}")
        return tag_ids

    def _upload_media_from_url(self, image_url: str) -> Optional[int]:
        """
        Download image from URL and upload to WordPress media library.
        Returns the media attachment ID or None on failure.
        """
        try:
            img_resp = requests.get(image_url, timeout=15)
            img_resp.raise_for_status()
            content_type = img_resp.headers.get('Content-Type', 'image/jpeg')
            filename = image_url.split('/')[-1].split('?')[0] or 'upload.jpg'

            upload_resp = requests.post(
                f"{self.api_base}/media",
                headers={
                    **self._auth_header(),
                    'Content-Disposition': f'attachment; filename="{filename}"',
                    'Content-Type': content_type,
                },
                data=img_resp.content,
                timeout=30,
            )
            upload_resp.raise_for_status()
            return upload_resp.json().get('id')
        except Exception as e:
            logger.warning(f"[WordPress] _upload_media_from_url failed: {e}")
            return None

    def verify_connection(self) -> Dict[str, Any]:
        """
        Test that credentials work. Returns site info or error.
        Call this when user links a WordPress account.
        """
        if self.simulation_mode:
            return {'success': True, 'site': 'Simulated WordPress Site', 'url': 'https://example.com'}
        try:
            resp = self._request('GET', '/', params={})  # /wp-json/wp/v2/
            # Try fetching current user to confirm auth
            me_resp = self._request('GET', 'users/me')
            me = me_resp.json()
            return {
                'success': True,
                'site_url': self.site_url,
                'wp_user_id': me.get('id'),
                'username': me.get('username', me.get('slug')),
                'display_name': me.get('name'),
            }
        except requests.HTTPError as e:
            status = e.response.status_code
            if status == 401:
                return {'success': False, 'error': 'Invalid credentials. Check username and Application Password.'}
            return {'success': False, 'error': f'HTTP {status}: {e.response.text}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
