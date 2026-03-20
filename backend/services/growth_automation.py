"""Growth automation operations API."""
from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone

from flask import Blueprint, jsonify, request
from sqlalchemy import func, or_

from ..auth import require_admin, require_auth
from ..models import (
    db,
    MarketingConsent,
    MarketingContact,
    MarketingDLQ,
    MarketingEvent,
    MarketingJourneyState,
    MarketingMessageLog,
)

growth_automation_bp = Blueprint("growth_automation", __name__, url_prefix="/api/v1/growth")


def _utc_now() -> datetime:
    return datetime.utcnow()


def _parse_iso_datetime(raw: str | None) -> datetime | None:
    if not raw:
        return None
    try:
        parsed = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo:
        return parsed.astimezone(timezone.utc).replace(tzinfo=None)
    return parsed


def _extract_bearer_token(header_value: str | None) -> str | None:
    if not header_value:
        return None
    parts = header_value.split(" ", 1)
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1].strip()
    return None


def _check_queue_token():
    expected = os.getenv("GROWTH_QUEUE_TOKEN") or os.getenv("N8N_JWT_SECRET") or ""
    if not expected:
        return jsonify({"ok": False, "error": "queue token not configured"}), 503

    provided = request.headers.get("X-Queue-Token") or _extract_bearer_token(request.headers.get("Authorization"))
    if provided != expected:
        return jsonify({"ok": False, "error": "unauthorized queue token"}), 401
    return None


def _pagination():
    page = max(request.args.get("page", 1, type=int), 1)
    per_page = request.args.get("per_page", 20, type=int)
    per_page = min(max(per_page, 1), 100)
    return page, per_page


def _apply_window(query, column, from_dt: datetime | None, to_dt: datetime | None):
    if from_dt:
        query = query.filter(column >= from_dt)
    if to_dt:
        query = query.filter(column <= to_dt)
    return query


def _build_summary_payload(from_dt: datetime | None = None, to_dt: datetime | None = None):
    contact_q = _apply_window(MarketingContact.query, MarketingContact.created_at, from_dt, to_dt)
    event_q = _apply_window(MarketingEvent.query, MarketingEvent.event_ts, from_dt, to_dt)
    message_q = _apply_window(MarketingMessageLog.query, MarketingMessageLog.created_at, from_dt, to_dt)
    dlq_q = _apply_window(MarketingDLQ.query, MarketingDLQ.created_at, from_dt, to_dt)
    journey_q = MarketingJourneyState.query
    if from_dt:
        journey_q = journey_q.filter(
            or_(MarketingJourneyState.entered_at >= from_dt, MarketingJourneyState.last_action_at >= from_dt)
        )
    if to_dt:
        journey_q = journey_q.filter(
            or_(MarketingJourneyState.entered_at <= to_dt, MarketingJourneyState.last_action_at <= to_dt)
        )

    contact_total = contact_q.count()
    event_total = event_q.count()
    failed_events = event_q.filter(MarketingEvent.processing_status == "failed").count()
    queue = {
        row.processing_status: row.total
        for row in db.session.query(
            MarketingEvent.processing_status,
            func.count(MarketingEvent.id).label("total"),
        ).group_by(MarketingEvent.processing_status).all()
    }
    journey_counts = {
        row.state: row.total
        for row in journey_q.with_entities(
            MarketingJourneyState.state,
            func.count(MarketingJourneyState.id).label("total"),
        ).group_by(MarketingJourneyState.state).all()
    }
    delivery = {
        row.status: row.total
        for row in message_q.with_entities(
            MarketingMessageLog.status,
            func.count(MarketingMessageLog.id).label("total"),
        ).group_by(MarketingMessageLog.status).all()
    }
    lifecycle_counts = {
        row.lifecycle_stage: row.total
        for row in contact_q.with_entities(
            MarketingContact.lifecycle_stage,
            func.count(MarketingContact.id).label("total"),
        ).group_by(MarketingContact.lifecycle_stage).all()
    }
    return {
        "contacts": {"total": contact_total, "lifecycle_counts": lifecycle_counts},
        "events": {"total": event_total, "failed": failed_events},
        "journey_counts": journey_counts,
        "delivery": delivery,
        "queue": queue,
        "errors": {"dlq_open": dlq_q.filter(MarketingDLQ.status == "open").count()},
    }


def _build_recommendations(summary: dict):
    recs = []
    contact_total = summary.get("contacts", {}).get("total", 0)
    event_total = summary.get("events", {}).get("total", 0)
    activated = summary.get("journey_counts", {}).get("activated", 0)
    dlq_open = summary.get("errors", {}).get("dlq_open", 0)
    queue_pending = summary.get("queue", {}).get("pending", 0)

    if contact_total == 0:
        recs.append({
            "title": "첫 리드를 만들어보세요",
            "description": "Hub 또는 Contacts에서 lead 이벤트를 생성하면 연락처와 여정이 자동으로 시작됩니다.",
            "action_label": "리드 생성",
            "action": "seed-lead",
        })
    if contact_total > 0 and activated == 0:
        recs.append({
            "title": "활성화 전환을 만드세요",
            "description": "signup_completed 또는 key_action_completed 이벤트를 생성해 온보딩 흐름을 확인하세요.",
            "action_label": "활성화 실행",
            "action": "seed-activation",
        })
    if dlq_open > 0:
        recs.append({
            "title": "실패 복구가 필요합니다",
            "description": f"현재 열린 DLQ가 {dlq_open}건 있습니다. Ops 메뉴에서 재처리하세요.",
            "action_label": "Ops 열기",
            "action": "open-ops",
        })
    if queue_pending > 0:
        recs.append({
            "title": "처리 대기 이벤트가 있습니다",
            "description": f"현재 pending 이벤트가 {queue_pending}건입니다. 워크플로 소비 상태를 확인하세요.",
            "action_label": "큐 확인",
            "action": "open-ops",
        })
    if event_total < 5:
        recs.append({
            "title": "샘플 시나리오를 더 생성하세요",
            "description": "리드, 가입, 활성화, 결제 실패 이벤트를 순서대로 만들어 전체 흐름을 점검하세요.",
            "action_label": "시나리오 실행",
            "action": "seed-sequence",
        })
    if not recs:
        recs.append({
            "title": "다음 실험을 설계하세요",
            "description": "현재 흐름은 작동 중입니다. 전환 손실 구간을 기준으로 세그먼트 실험을 시작하세요.",
            "action_label": "Journeys 보기",
            "action": "open-journeys",
        })
    return recs[:4]


def _serialize_event_for_queue(event_row: MarketingEvent):
    contact = event_row.contact
    return {
        "event_id": event_row.event_id,
        "event_name": event_row.event_name,
        "ts": event_row.event_ts.isoformat() if event_row.event_ts else None,
        "idempotency_key": event_row.idempotency_key,
        "correlation_id": event_row.idempotency_key,
        "identity": {
            "contact_id": contact.contact_uid if contact else None,
            "anonymous_id": event_row.anonymous_id,
            "email": contact.email if contact else None,
            "phone": contact.phone if contact else None,
        },
        "context": event_row.context_json or {},
        "props": event_row.props_json or {},
    }


@growth_automation_bp.route("/dashboard/summary", methods=["GET"])
@require_auth
@require_admin
def growth_dashboard_summary():
    from_dt = _parse_iso_datetime(request.args.get("from"))
    to_dt = _parse_iso_datetime(request.args.get("to"))
    return jsonify(_build_summary_payload(from_dt, to_dt)), 200


@growth_automation_bp.route("/public/bootstrap", methods=["GET"])
def public_bootstrap():
    summary = _build_summary_payload()
    latest_contacts = (
        MarketingContact.query
        .order_by(MarketingContact.created_at.desc())
        .limit(12)
        .all()
    )
    latest_journeys = (
        MarketingJourneyState.query
        .order_by(MarketingJourneyState.entered_at.desc())
        .limit(12)
        .all()
    )
    latest_events = (
        MarketingEvent.query
        .order_by(MarketingEvent.event_ts.desc())
        .limit(16)
        .all()
    )
    latest_dlq = (
        MarketingDLQ.query
        .order_by(MarketingDLQ.created_at.desc())
        .limit(12)
        .all()
    )
    return jsonify(
        {
            "mode": "public",
            "summary": summary,
            "contacts": [row.to_dict() for row in latest_contacts],
            "journeys": [row.to_dict() for row in latest_journeys],
            "events": [row.to_dict() for row in latest_events],
            "dlq": [row.to_dict() for row in latest_dlq],
            "recommendations": _build_recommendations(summary),
        }
    ), 200


@growth_automation_bp.route("/contacts", methods=["GET"])
@require_auth
@require_admin
def list_contacts():
    page, per_page = _pagination()
    q = MarketingContact.query

    status = request.args.get("status")
    lifecycle = request.args.get("lifecycle_stage")
    keyword = (request.args.get("q") or "").strip()
    sort_by = request.args.get("sort_by", "created_at")
    sort_order = request.args.get("sort_order", "desc").lower()

    if status:
        q = q.filter(MarketingContact.status == status)
    if lifecycle:
        q = q.filter(MarketingContact.lifecycle_stage == lifecycle)
    if keyword:
        like_value = f"%{keyword}%"
        q = q.filter(
            or_(
                MarketingContact.email.ilike(like_value),
                MarketingContact.phone.ilike(like_value),
                MarketingContact.contact_uid.ilike(like_value),
            )
        )

    sort_map = {
        "created_at": MarketingContact.created_at,
        "updated_at": MarketingContact.updated_at,
        "email": MarketingContact.email,
        "status": MarketingContact.status,
    }
    sort_column = sort_map.get(sort_by, MarketingContact.created_at)
    q = q.order_by(sort_column.asc() if sort_order == "asc" else sort_column.desc())

    rows = q.paginate(page=page, per_page=per_page, error_out=False)
    return jsonify(
        {
            "items": [row.to_dict() for row in rows.items],
            "total": rows.total,
            "page": page,
            "per_page": per_page,
            "pages": rows.pages,
        }
    ), 200


@growth_automation_bp.route("/contacts/upsert", methods=["POST"])
@require_auth
@require_admin
def upsert_contact():
    payload = request.get_json(silent=True) or {}
    email = (payload.get("email") or "").strip() or None
    phone = (payload.get("phone") or "").strip() or None
    if not email and not phone:
        return jsonify({"error": "email or phone is required"}), 400

    q = MarketingContact.query
    if email and phone:
        contact = q.filter(or_(MarketingContact.email == email, MarketingContact.phone == phone)).first()
    elif email:
        contact = q.filter(MarketingContact.email == email).first()
    else:
        contact = q.filter(MarketingContact.phone == phone).first()

    created = False
    now = _utc_now()
    if not contact:
        contact = MarketingContact(
            contact_uid=str(uuid.uuid4()),
            email=email,
            phone=phone,
            status=payload.get("status") or "active",
            lifecycle_stage=payload.get("lifecycle_stage") or "lead",
            locale=payload.get("locale") or "ko-KR",
            timezone=payload.get("timezone") or "Asia/Seoul",
            created_at=now,
            updated_at=now,
        )
        db.session.add(contact)
        created = True
    else:
        if email:
            contact.email = email
        if phone:
            contact.phone = phone
        if payload.get("status"):
            contact.status = payload["status"]
        if payload.get("lifecycle_stage"):
            contact.lifecycle_stage = payload["lifecycle_stage"]
        if payload.get("locale"):
            contact.locale = payload["locale"]
        if payload.get("timezone"):
            contact.timezone = payload["timezone"]
        contact.updated_at = now

    db.session.flush()
    for consent_payload in payload.get("consents", []):
        channel = (consent_payload.get("channel") or "").strip().lower()
        if not channel:
            continue
        policy_version = consent_payload.get("policy_version") or "v1"
        consent = MarketingConsent.query.filter_by(
            contact_id=contact.id,
            channel=channel,
            policy_version=policy_version,
        ).first()
        if not consent:
            consent = MarketingConsent(
                contact_id=contact.id,
                channel=channel,
                policy_version=policy_version,
                source=consent_payload.get("source"),
                created_at=now,
            )
            db.session.add(consent)

        opt_in = bool(consent_payload.get("opt_in", True))
        consent.opt_in = opt_in
        consent.source = consent_payload.get("source") or consent.source
        consent.updated_at = now
        if opt_in:
            consent.granted_at = now
            consent.revoked_at = None
        else:
            consent.revoked_at = now

    db.session.commit()
    return jsonify({"contact_id": contact.contact_uid, "status": "created" if created else "updated"}), 200


@growth_automation_bp.route("/events", methods=["GET"])
@require_auth
@require_admin
def list_events():
    page, per_page = _pagination()
    q = MarketingEvent.query

    event_name = request.args.get("event_name")
    status = request.args.get("status")
    from_dt = _parse_iso_datetime(request.args.get("from"))
    to_dt = _parse_iso_datetime(request.args.get("to"))

    if event_name:
        q = q.filter(MarketingEvent.event_name == event_name)
    if status:
        q = q.filter(MarketingEvent.processing_status == status)
    if from_dt:
        q = q.filter(MarketingEvent.event_ts >= from_dt)
    if to_dt:
        q = q.filter(MarketingEvent.event_ts <= to_dt)

    rows = q.order_by(MarketingEvent.event_ts.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return jsonify(
        {
            "items": [row.to_dict() for row in rows.items],
            "total": rows.total,
            "page": page,
            "per_page": per_page,
            "pages": rows.pages,
        }
    ), 200


@growth_automation_bp.route("/journeys", methods=["GET"])
@require_auth
@require_admin
def list_journeys():
    page, per_page = _pagination()
    q = MarketingJourneyState.query

    state = request.args.get("state")
    journey_id = request.args.get("journey_id")
    if state:
        q = q.filter(MarketingJourneyState.state == state)
    if journey_id:
        q = q.filter(MarketingJourneyState.journey_id == journey_id)

    rows = q.order_by(MarketingJourneyState.entered_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return jsonify(
        {
            "items": [row.to_dict() for row in rows.items],
            "total": rows.total,
            "page": page,
            "per_page": per_page,
            "pages": rows.pages,
        }
    ), 200


@growth_automation_bp.route("/messages/log", methods=["POST"])
@require_auth
@require_admin
def log_message():
    payload = request.get_json(silent=True) or {}
    contact_id_value = payload.get("contact_id")
    contact_id = None
    if contact_id_value:
        contact = MarketingContact.query.filter_by(contact_uid=str(contact_id_value)).first()
        if not contact and str(contact_id_value).isdigit():
            contact = MarketingContact.query.get(int(contact_id_value))
        if contact:
            contact_id = contact.id

    channel = (payload.get("channel") or "").strip().lower()
    status = (payload.get("status") or "").strip().lower()
    if not channel or not status:
        return jsonify({"error": "channel and status are required"}), 400

    sent_at = _parse_iso_datetime(payload.get("sent_at"))
    row = MarketingMessageLog(
        message_uid=payload.get("message_uid") or str(uuid.uuid4()),
        contact_id=contact_id,
        channel=channel,
        template_id=payload.get("template_id"),
        campaign_id=payload.get("campaign_id"),
        variant_id=payload.get("variant_id"),
        status=status,
        provider_msg_id=payload.get("provider_msg_id"),
        error_code=payload.get("error_code"),
        sent_at=sent_at,
        created_at=_utc_now(),
    )
    db.session.add(row)
    db.session.commit()
    return jsonify({"message_id": row.message_uid, "status": row.status}), 201


@growth_automation_bp.route("/dlq", methods=["GET"])
@require_auth
@require_admin
def list_dlq():
    page, per_page = _pagination()
    q = MarketingDLQ.query

    status = request.args.get("status")
    workflow = request.args.get("workflow")
    from_dt = _parse_iso_datetime(request.args.get("from"))
    to_dt = _parse_iso_datetime(request.args.get("to"))

    if status:
        q = q.filter(MarketingDLQ.status == status)
    if workflow:
        q = q.filter(MarketingDLQ.workflow_name == workflow)
    if from_dt:
        q = q.filter(MarketingDLQ.created_at >= from_dt)
    if to_dt:
        q = q.filter(MarketingDLQ.created_at <= to_dt)

    rows = q.order_by(MarketingDLQ.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return jsonify(
        {
            "items": [row.to_dict() for row in rows.items],
            "total": rows.total,
            "page": page,
            "per_page": per_page,
            "pages": rows.pages,
        }
    ), 200


@growth_automation_bp.route("/dlq/<int:dlq_id>/replay", methods=["POST"])
@require_auth
@require_admin
def replay_dlq(dlq_id: int):
    row = db.session.get(MarketingDLQ, dlq_id)
    if not row:
        return jsonify({"error": "DLQ entry not found"}), 404

    payload = request.get_json(silent=True) or {}
    reason = payload.get("reason") or "manual replay"
    now = _utc_now()
    row.status = "resolved"
    row.resolved_at = now
    row.resolved_reason = reason
    row.retry_count += 1

    event = MarketingEvent.query.filter_by(event_id=row.event_id).first()
    if event:
        event.processing_status = "pending"
        event.processing_updated_at = now
        event.error_code = None

    db.session.commit()
    return jsonify({"replayed": True, "status": row.status}), 200


@growth_automation_bp.route("/queue/pending", methods=["GET"])
def queue_pending():
    auth_error = _check_queue_token()
    if auth_error:
        return auth_error

    now = _utc_now()
    stale_at = now.timestamp() - 300
    stale_rows = (
        MarketingEvent.query
        .filter(MarketingEvent.processing_status == "processing")
        .all()
    )
    for row in stale_rows:
        if row.processing_updated_at and row.processing_updated_at.timestamp() < stale_at:
            row.processing_status = "pending"
            row.processing_updated_at = now

    limit = min(max(request.args.get("limit", 50, type=int), 1), 200)
    rows = (
        MarketingEvent.query
        .filter(MarketingEvent.processing_status == "pending")
        .order_by(MarketingEvent.created_at.asc())
        .limit(limit)
        .all()
    )
    for row in rows:
        row.processing_status = "processing"
        row.processing_updated_at = now
    db.session.commit()
    return jsonify({"events": [_serialize_event_for_queue(row) for row in rows]}), 200


@growth_automation_bp.route("/queue/ack", methods=["POST"])
def queue_ack():
    auth_error = _check_queue_token()
    if auth_error:
        return auth_error

    payload = request.get_json(silent=True) or {}
    event_id = payload.get("event_id")
    if not event_id:
        return jsonify({"ok": False, "error": "event_id is required"}), 400

    row = MarketingEvent.query.filter_by(event_id=str(event_id)).first()
    if not row:
        return jsonify({"ok": False, "error": "event not found"}), 404

    row.processing_status = "processed"
    row.processing_updated_at = _utc_now()
    row.workflow_run_id = payload.get("workflow_run_id")
    db.session.commit()
    return jsonify({"ok": True}), 200


@growth_automation_bp.route("/queue/fail", methods=["POST"])
def queue_fail():
    auth_error = _check_queue_token()
    if auth_error:
        return auth_error

    payload = request.get_json(silent=True) or {}
    event_id = payload.get("event_id")
    if not event_id:
        return jsonify({"ok": False, "error": "event_id is required"}), 400

    row = MarketingEvent.query.filter_by(event_id=str(event_id)).first()
    if not row:
        return jsonify({"ok": False, "error": "event not found"}), 404

    now = _utc_now()
    error_summary = payload.get("error") or "workflow failed"
    row.processing_status = "failed"
    row.processing_updated_at = now
    row.error_code = error_summary[:120]
    row.workflow_run_id = payload.get("workflow_run_id")

    dlq = MarketingDLQ(
        event_id=row.event_id,
        workflow_name=payload.get("workflow_name") or "unknown-workflow",
        step_name=payload.get("step"),
        error_summary=error_summary,
        payload_json={
            "event": row.to_dict(),
            "workflow_run_id": payload.get("workflow_run_id"),
        },
        retry_count=0,
        status="open",
        created_at=now,
    )
    db.session.add(dlq)
    db.session.commit()
    return jsonify({"ok": True, "dlq_id": dlq.id}), 200
