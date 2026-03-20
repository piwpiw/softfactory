import pytest
from pathlib import Path

pytestmark = pytest.mark.e2e


def read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_platform_home_has_workspace_navigation_links():
    html = read("d:/Project/web/platform/index.html")
    assert "notifications.html" in html
    assert "security.html" in html
    assert "settings.html" in html
    assert "help.html" in html


def test_platform_workspace_pages_have_real_sections():
    notifications = read("d:/Project/web/platform/notifications.html")
    security = read("d:/Project/web/platform/security.html")
    settings = read("d:/Project/web/platform/settings.html")
    help_html = read("d:/Project/web/platform/help.html")

    assert "알림" in notifications
    assert "notification" in notifications.lower()
    assert "보안" in security
    assert "workspace" in settings.lower() or "워크스페이스" in settings
    assert "도움" in help_html or "help" in help_html.lower()
