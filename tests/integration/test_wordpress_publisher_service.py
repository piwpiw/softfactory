import json
from datetime import datetime
from pathlib import Path

from backend.models import db, SNSAccount, SNSPost, User


def _ensure_user():
    user = User.query.filter_by(email="wp-test@example.com").first()
    if user is None:
        user = User(email="wp-test@example.com", name="WP Test User", email_verified=True)
        user.set_password("StrongPassword123!")
        db.session.add(user)
        db.session.commit()
    return user


def test_save_wordpress_site(client, app, auth_headers, monkeypatch):
    with app.app_context():
        _ensure_user()

    from backend.services import wordpress_publisher_service as service

    monkeypatch.setattr(
        service,
        "_verify_wordpress_credentials",
        lambda site_url, wp_username, access_token: {
            "success": True,
            "site_url": site_url,
            "username": wp_username,
            "display_name": "Bohemian Studio",
        },
    )

    response = client.post(
        "/api/sns/wordpress/sites",
        headers=auth_headers,
        json={
            "account_name": "Bohemian Studio",
            "site_url": "https://example.com",
            "wp_username": "admin",
            "access_token": "app-password",
        },
    )
    assert response.status_code == 201
    data = response.get_json()
    assert data["site"]["site_url"] == "https://example.com"


def test_get_wordpress_templates(client, auth_headers):
    response = client.get("/api/sns/wordpress/templates", headers=auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert data["brand_system"]["brand"] == "Bohemian Studio"
    assert len(data["templates"]) >= 6


def test_create_wordpress_post_pipeline(client, app, auth_headers, monkeypatch):
    with app.app_context():
        user = _ensure_user()
        account = SNSAccount(
            user_id=user.id,
            platform="wordpress",
            account_name="Bohemian Studio",
            site_url="https://example.com",
            wp_username="admin",
            access_token="app-password",
            is_active=True,
        )
        db.session.add(account)
        db.session.commit()
        account_id = account.id

    from backend.services import wordpress_publisher_service as service

    monkeypatch.setattr(service, "_skill_available", lambda: (True, None))

    def fake_run_command(command, env=None):
        command_text = " ".join(command)
        if "publish_wordpress_post.py" in command_text:
            return type("Result", (), {"stdout": json.dumps({"status": "publish", "link": "https://example.com/post", "date": datetime.utcnow().isoformat()}), "stderr": ""})()
        return type("Result", (), {"stdout": str(Path("output") / "wordpress-publisher" / "fake"), "stderr": ""})()

    monkeypatch.setattr(service, "_run_command", fake_run_command)

    fake_payload = {
        "title": "테스트 포스트",
        "excerpt": "요약",
        "status": "publish",
        "tags": [1, 2],
    }
    monkeypatch.setattr(service, "_read_json", lambda path: {"score": 97} if "quality-report" in str(path) else {"passed": True} if "contract-report" in str(path) else fake_payload)

    response = client.post(
        "/api/sns/wordpress/posts",
        headers=auth_headers,
        json={
            "account_id": account_id,
            "title": "테스트 포스트",
            "template_type": "trend-brief",
            "status": "publish",
            "category_label": "AI & Automation",
            "category_slug": "ai-automation",
            "push_to_wordpress": True,
            "sources": [{"url": "https://developers.google.com/search/docs/fundamentals/creating-helpful-content"}],
        },
    )
    assert response.status_code == 201
    data = response.get_json()
    assert data["post"]["status"] == "published"

    with app.app_context():
        saved_posts = SNSPost.query.filter_by(platform="wordpress").all()
        assert len(saved_posts) == 1
