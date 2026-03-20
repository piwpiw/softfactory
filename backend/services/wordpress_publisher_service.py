"""WordPress publishing orchestration endpoints for SNS Auto."""

from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

from flask import Blueprint, jsonify, g, request

from ..auth import require_auth, require_subscription
from ..models import db, SNSAccount, SNSPost
from .sns_platforms import get_client as get_platform_client

wordpress_bp = Blueprint("wordpress_publisher", __name__, url_prefix="/api/sns/wordpress")

ROOT_PILLARS = [
    "AI & Automation",
    "WordPress & Publishing",
    "Apps & Software",
    "Productivity & Workflows",
    "Creator Revenue & Growth",
    "Reviews & Comparisons",
]

WORDPRESS_TEMPLATES = [
    {
        "slug": "trend-brief",
        "name": "Trend Brief",
        "summary": "공식 출처 기반 변화 요약과 운영 의미 정리.",
        "best_for": ["AI & Automation", "WordPress & Publishing"],
    },
    {
        "slug": "field-guide",
        "name": "Field Guide",
        "summary": "실행 절차와 주의점을 단계별로 설명하는 가이드.",
        "best_for": ["WordPress & Publishing", "Productivity & Workflows"],
    },
    {
        "slug": "workflow-playbook",
        "name": "Workflow Playbook",
        "summary": "실무 흐름과 체크리스트 중심의 운영형 문서.",
        "best_for": ["AI & Automation", "Creator Revenue & Growth"],
    },
    {
        "slug": "comparison",
        "name": "Comparison",
        "summary": "도구와 선택지를 구조적으로 비교하는 템플릿.",
        "best_for": ["Apps & Software", "Reviews & Comparisons"],
    },
    {
        "slug": "review",
        "name": "Review",
        "summary": "체험, 장단점, 추천 대상, 대안까지 정리하는 리뷰.",
        "best_for": ["Apps & Software", "Reviews & Comparisons"],
    },
    {
        "slug": "tool-stack",
        "name": "Tool Stack",
        "summary": "추천 도구와 연계 흐름, 수익화 동선을 함께 설명.",
        "best_for": ["Creator Revenue & Growth", "Productivity & Workflows"],
    },
]

CADENCE_POLICY = {
    "candidate_interval_minutes": 10,
    "launch_public_limit_per_day": 12,
    "steady_public_limit_per_day": 6,
    "launch_window_hours": 72,
    "quality_threshold": 94,
    "hard_blockers": [
        "출처 부족",
        "중복도 초과",
        "얇은 본문",
        "과장형 제목",
        "광고 고지 누락",
        "이미지 alt 누락",
        "정책 리스크",
    ],
}

BRAND_SYSTEM = {
    "brand": "Bohemian Studio",
    "tagline": "팩트로 정리하고 실행으로 연결하는 디지털 매거진",
    "tokens": {
        "ink": "#0B1320",
        "paper": "#F6F1E8",
        "teal": "#0F766E",
        "amber": "#C58A2A",
        "moss": "#2F6B4F",
    },
    "fonts": {"body": "SUIT Variable", "headline": "MaruBuri"},
}


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _skill_root() -> Path:
    configured = os.getenv("WORDPRESS_PUBLISHER_SKILL_PATH", "").strip()
    if configured:
        return Path(configured)
    return Path.home() / ".codex" / "skills" / "wordpress-fact-publisher"


def _skill_script(script_name: str) -> Path:
    return _skill_root() / "scripts" / script_name


def _skill_available() -> tuple[bool, str | None]:
    required = [
        _skill_script("run_post_pipeline.py"),
        _skill_script("run_research_publish_pipeline.py"),
        _skill_script("publish_wordpress_post.py"),
        _skill_script("validate_brief_contract.py"),
        _skill_script("build_post_package.py"),
        _skill_script("validate_post_quality.py"),
        _skill_script("autofix_post_brief.py"),
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        return False, f"Missing WordPress skill assets: {', '.join(missing)}"
    return True, None


def _serialize_site(account: SNSAccount) -> dict[str, Any]:
    return {
        "id": account.id,
        "account_name": account.account_name,
        "platform": account.platform,
        "site_url": account.site_url,
        "wp_username": account.wp_username,
        "is_active": bool(account.is_active),
        "created_at": account.created_at.isoformat() if account.created_at else None,
    }


def _serialize_post(post: SNSPost) -> dict[str, Any]:
    return {
        "id": post.id,
        "account_id": post.account_id,
        "platform": post.platform,
        "status": post.status,
        "template_type": post.template_type,
        "content": post.content,
        "scheduled_at": post.scheduled_at.isoformat() if post.scheduled_at else None,
        "published_at": post.published_at.isoformat() if post.published_at else None,
        "link_url": post.link_url,
        "media_urls": post.media_urls or [],
        "error_message": post.error_message,
        "created_at": post.created_at.isoformat() if post.created_at else None,
    }


def _wordpress_account_query():
    return SNSAccount.query.filter(
        SNSAccount.user_id == g.user_id,
        SNSAccount.platform.in_(["wordpress", "blog"]),
    )


def _get_site_or_404(site_id: int) -> SNSAccount:
    account = _wordpress_account_query().filter(SNSAccount.id == site_id).first()
    if not account:
        raise ValueError("WordPress site not found")
    return account


def _slugify(value: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9가-힣]+", "-", value.lower()).strip("-")
    return normalized or f"run-{int(datetime.utcnow().timestamp())}"


def _output_root() -> Path:
    root = _repo_root() / "output" / "wordpress-publisher"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _pipeline_env(account: SNSAccount) -> dict[str, str]:
    env = os.environ.copy()
    env["WP_BASE_URL"] = (account.site_url or "").rstrip("/")
    env["WP_USERNAME"] = account.wp_username or ""
    env["WP_APP_PASSWORD"] = account.access_token or ""
    return env


def _run_command(command: list[str], env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )


def _parse_json_output(stdout: str) -> dict[str, Any] | list[Any] | None:
    payload = (stdout or "").strip()
    if not payload:
        return None
    try:
        return json.loads(payload)
    except json.JSONDecodeError:
        return None


def _read_json(path: Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def _artifacts_for(workdir: Path) -> dict[str, str]:
    pipeline_dir = workdir / "pipeline"
    return {
        "workdir": str(workdir),
        "generated_brief": str(workdir / "generated-brief.json"),
        "source_notes": str(workdir / "source-notes.json"),
        "brief": str(pipeline_dir / "brief-fixed.json"),
        "payload": str(pipeline_dir / "post-payload.json"),
        "quality_report": str(pipeline_dir / "quality-report.json"),
        "contract_report": str(pipeline_dir / "contract-report.json"),
        "stage_report": str(pipeline_dir / "stage-report.json"),
        "featured_image": str(pipeline_dir / "featured-image.png"),
    }


def _persist_wordpress_post(
    account: SNSAccount,
    payload: dict[str, Any],
    template_type: str,
    publish_result: dict[str, Any] | None,
    artifacts: dict[str, str],
) -> SNSPost:
    excerpt = payload.get("excerpt", "")
    content = f"{payload.get('title', 'WordPress Post')}\n\n{excerpt}".strip()
    status = payload.get("status", "draft")
    published_at = None
    link_url = None
    if publish_result:
        status = "published" if publish_result.get("status") == "publish" else publish_result.get("status", status)
        link_url = publish_result.get("link") or publish_result.get("url")
        published_at_raw = publish_result.get("date") or publish_result.get("published_at")
        if published_at_raw:
            try:
                published_at = datetime.fromisoformat(str(published_at_raw).replace("Z", "+00:00"))
            except ValueError:
                published_at = datetime.utcnow()

    post = SNSPost(
        user_id=account.user_id,
        account_id=account.id,
        content=content[:5000],
        platform="wordpress",
        status=status,
        published_at=published_at,
        template_type=template_type,
        media_urls=[artifacts["featured_image"]],
        link_url=link_url,
        hashtags=payload.get("tags", []),
    )
    db.session.add(post)
    db.session.commit()
    return post


def _run_quality_audit(brief: dict[str, Any]) -> dict[str, Any]:
    skill_ok, error = _skill_available()
    if not skill_ok:
        raise RuntimeError(error)

    with tempfile.TemporaryDirectory(prefix="wp-audit-") as tmp:
        tmp_path = Path(tmp)
        brief_path = tmp_path / "brief.json"
        fixed_brief_path = tmp_path / "brief-fixed.json"
        payload_path = tmp_path / "payload.json"
        contract_report_path = tmp_path / "contract-report.json"
        quality_report_path = tmp_path / "quality-report.json"
        with open(brief_path, "w", encoding="utf-8") as handle:
            json.dump(brief, handle, ensure_ascii=False, indent=2)

        _run_command(
            [
                os.sys.executable,
                str(_skill_script("autofix_post_brief.py")),
                "--input",
                str(brief_path),
                "--output",
                str(fixed_brief_path),
            ]
        )
        _run_command(
            [
                os.sys.executable,
                str(_skill_script("validate_brief_contract.py")),
                "--brief",
                str(fixed_brief_path),
                "--report",
                str(contract_report_path),
            ]
        )
        _run_command(
            [
                os.sys.executable,
                str(_skill_script("build_post_package.py")),
                "--input",
                str(fixed_brief_path),
                "--output",
                str(payload_path),
            ]
        )
        _run_command(
            [
                os.sys.executable,
                str(_skill_script("validate_post_quality.py")),
                "--brief",
                str(fixed_brief_path),
                "--payload",
                str(payload_path),
                "--report",
                str(quality_report_path),
            ]
        )

        return {
            "fixed_brief": _read_json(fixed_brief_path),
            "contract_report": _read_json(contract_report_path),
            "quality_report": _read_json(quality_report_path),
            "payload": _read_json(payload_path),
        }


def _verify_wordpress_credentials(site_url: str, wp_username: str, access_token: str) -> dict[str, Any]:
    client = get_platform_client(
        "wordpress",
        access_token=access_token,
        simulation_mode=False,
        site_url=site_url,
        wp_username=wp_username,
    )
    return client.verify_connection()


@wordpress_bp.route("/sites", methods=["GET"])
@require_auth
@require_subscription("sns-auto")
def list_wordpress_sites():
    sites = _wordpress_account_query().order_by(SNSAccount.created_at.desc()).all()
    return jsonify({"sites": [_serialize_site(site) for site in sites], "count": len(sites)}), 200


@wordpress_bp.route("/sites", methods=["POST"])
@require_auth
@require_subscription("sns-auto")
def upsert_wordpress_site():
    data = request.get_json() or {}
    site_url = (data.get("site_url") or "").strip().rstrip("/")
    wp_username = (data.get("wp_username") or "").strip()
    access_token = (data.get("access_token") or "").strip()
    account_name = (data.get("account_name") or BRAND_SYSTEM["brand"]).strip()

    if not site_url or not wp_username or not access_token:
        return jsonify({"error": "site_url, wp_username, access_token are required"}), 400

    verify = _verify_wordpress_credentials(site_url, wp_username, access_token)
    if not verify.get("success"):
        return jsonify({"error": "WordPress connection failed", "detail": verify.get("error")}), 400

    account = _wordpress_account_query().filter(SNSAccount.site_url == site_url).first()
    if account is None:
        account = SNSAccount(
            user_id=g.user_id,
            platform="wordpress",
            account_name=account_name,
            site_url=site_url,
            wp_username=wp_username,
            access_token=access_token,
            is_active=True,
        )
        db.session.add(account)
    else:
        account.account_name = account_name
        account.wp_username = wp_username
        account.access_token = access_token
        account.is_active = True

    db.session.commit()
    return jsonify({"message": "WordPress site saved", "site": _serialize_site(account), "verify": verify}), 201


@wordpress_bp.route("/sites/<int:site_id>/test", methods=["POST"])
@require_auth
@require_subscription("sns-auto")
def test_wordpress_site(site_id: int):
    try:
        account = _get_site_or_404(site_id)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 404

    result = _verify_wordpress_credentials(account.site_url or "", account.wp_username or "", account.access_token or "")
    status_code = 200 if result.get("success") else 400
    return jsonify(result), status_code


@wordpress_bp.route("/templates", methods=["GET"])
@require_auth
@require_subscription("sns-auto")
def get_wordpress_templates():
    return jsonify(
        {
            "brand_system": BRAND_SYSTEM,
            "pillars": ROOT_PILLARS,
            "templates": WORDPRESS_TEMPLATES,
            "cadence_policy": CADENCE_POLICY,
        }
    ), 200


@wordpress_bp.route("/runs", methods=["GET"])
@require_auth
@require_subscription("sns-auto")
def get_wordpress_runs():
    limit = min(request.args.get("limit", 20, type=int), 100)
    posts = (
        SNSPost.query.join(SNSAccount, SNSPost.account_id == SNSAccount.id)
        .filter(SNSPost.user_id == g.user_id, SNSPost.platform == "wordpress")
        .order_by(SNSPost.created_at.desc())
        .limit(limit)
        .all()
    )
    return jsonify({"runs": [_serialize_post(post) for post in posts], "count": len(posts)}), 200


@wordpress_bp.route("/content-audit", methods=["POST"])
@require_auth
@require_subscription("sns-auto")
def audit_wordpress_content():
    data = request.get_json() or {}
    brief = data.get("brief")
    if not isinstance(brief, dict):
        return jsonify({"error": "brief object is required"}), 400

    try:
        audit = _run_quality_audit(brief)
    except subprocess.CalledProcessError as exc:
        return jsonify({"error": "Audit failed", "detail": exc.stderr or exc.stdout}), 500
    except RuntimeError as exc:
        return jsonify({"error": str(exc)}), 503

    return jsonify(audit), 200


@wordpress_bp.route("/posts", methods=["GET"])
@require_auth
@require_subscription("sns-auto")
def get_wordpress_posts():
    posts = (
        SNSPost.query.join(SNSAccount, SNSPost.account_id == SNSAccount.id)
        .filter(SNSPost.user_id == g.user_id, SNSPost.platform == "wordpress")
        .order_by(SNSPost.created_at.desc())
        .all()
    )
    return jsonify({"posts": [_serialize_post(post) for post in posts], "count": len(posts)}), 200


@wordpress_bp.route("/posts", methods=["POST"])
@require_auth
@require_subscription("sns-auto")
def create_wordpress_post():
    data = request.get_json() or {}
    site_id = data.get("account_id") or data.get("site_id")
    if not site_id:
        return jsonify({"error": "account_id is required"}), 400

    try:
        account = _get_site_or_404(int(site_id))
    except (TypeError, ValueError) as exc:
        return jsonify({"error": str(exc)}), 404

    skill_ok, error = _skill_available()
    if not skill_ok:
        return jsonify({"error": error}), 503

    template_type = (data.get("template_type") or "trend-brief").strip().lower()
    title = (data.get("title") or "").strip()
    status = (data.get("status") or "draft").strip().lower()
    category_label = (data.get("category_label") or "AI & Automation").strip()
    category_slug = (data.get("category_slug") or _slugify(category_label)).strip()
    provider = (data.get("provider") or "deterministic").strip()
    push_to_wordpress = bool(data.get("push_to_wordpress", True))

    timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    run_slug = _slugify(title or f"{template_type}-{timestamp}")
    workdir = _output_root() / f"{timestamp}-{run_slug}"
    workdir.mkdir(parents=True, exist_ok=True)

    env = _pipeline_env(account)
    command: list[str]

    try:
        if isinstance(data.get("brief"), dict):
            brief = dict(data["brief"])
            if title:
                brief["title"] = title
            brief["status"] = status
            if category_label:
                brief["category_label"] = category_label
            brief_path = workdir / "brief.json"
            with open(brief_path, "w", encoding="utf-8") as handle:
                json.dump(brief, handle, ensure_ascii=False, indent=2)
            command = [
                os.sys.executable,
                str(_skill_script("run_post_pipeline.py")),
                "--brief",
                str(brief_path),
                "--workdir",
                str(workdir / "pipeline"),
            ]
            _run_command(command, env=env)
        elif isinstance(data.get("sources"), list):
            if not title:
                return jsonify({"error": "title is required when sources are provided"}), 400
            sources_path = workdir / "source-list.json"
            with open(sources_path, "w", encoding="utf-8") as handle:
                json.dump(data["sources"], handle, ensure_ascii=False, indent=2)
            command = [
                os.sys.executable,
                str(_skill_script("run_research_publish_pipeline.py")),
                "--sources",
                str(sources_path),
                "--title",
                title,
                "--updated-at",
                data.get("updated_at") or datetime.utcnow().strftime("%Y-%m-%d"),
                "--category-label",
                category_label,
                "--category-slug",
                category_slug,
                "--site-url",
                account.site_url or "",
                "--workdir",
                str(workdir),
                "--status",
                status,
                "--provider",
                provider,
            ]
            for category_id in data.get("category_ids", []) or []:
                command.extend(["--category-id", str(category_id)])
            for tag_id in data.get("tag_ids", []) or []:
                command.extend(["--tag-id", str(tag_id)])
            _run_command(command, env=env)
        else:
            return jsonify({"error": "brief object or sources list is required"}), 400
    except subprocess.CalledProcessError as exc:
        return jsonify({"error": "WordPress pipeline failed", "detail": exc.stderr or exc.stdout}), 500

    artifacts = _artifacts_for(workdir)
    payload = _read_json(Path(artifacts["payload"]))
    quality_report = _read_json(Path(artifacts["quality_report"]))
    contract_report = _read_json(Path(artifacts["contract_report"]))
    publish_result = None

    if push_to_wordpress:
        publish_cmd = [
            os.sys.executable,
            str(_skill_script("publish_wordpress_post.py")),
            "--payload",
            artifacts["payload"],
        ]
        try:
            publish_process = _run_command(publish_cmd, env=env)
            publish_result = _parse_json_output(publish_process.stdout)
        except subprocess.CalledProcessError as exc:
            return jsonify({"error": "WordPress publish failed", "detail": exc.stderr or exc.stdout}), 500

    post = _persist_wordpress_post(account, payload, template_type, publish_result if isinstance(publish_result, dict) else None, artifacts)

    return jsonify(
        {
            "message": "WordPress pipeline completed",
            "site": _serialize_site(account),
            "post": _serialize_post(post),
            "artifacts": artifacts,
            "contract_report": contract_report,
            "quality_report": quality_report,
            "publish_result": publish_result,
        }
    ), 201
