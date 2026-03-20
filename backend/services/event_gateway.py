"""Event ingestion API for growth automation."""
from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone

from flask import Blueprint, jsonify, request
from sqlalchemy import or_

from ..models import db, MarketingContact, MarketingEvent, MarketingJourneyState

event_gateway_bp = Blueprint("event_gateway", __name__, url_prefix="/api/v1")


EVENT_JOURNEY_MAP = {
    "lead_captured": ("growth_main", "lead_captured", "lead"),
    "signup_completed": ("growth_main", "signup_completed", "signed_up"),
    "key_action_completed": ("growth_main", "activated", "active"),
    "trial_expiring": ("revenue_recovery", "trial_expiring", "trial"),
    "payment_failed": ("revenue_recovery", "payment_failed", "at_risk"),
    "reengagement_eligible": ("retention_recovery", "reengagement", "inactive"),
    "churn_risk_detected": ("retention_recovery", "churn_risk", "at_risk"),
}


def _utc_now() -> datetime:
    return datetime.utcnow()


def _extract_bearer_token(header_value: str | None) -> str | None:
    if not header_value:
        return None
    parts = header_value.split(" ", 1)
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1].strip()
    return None


def _parse_event_ts(raw: str | None) -> datetime:
    if not raw:
        return _utc_now()
    try:
        parsed = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
    except ValueError:
        return _utc_now()
    if parsed.tzinfo:
        return parsed.astimezone(timezone.utc).replace(tzinfo=None)
    return parsed


def _resolve_contact(identity: dict) -> MarketingContact | None:
    contact_id = identity.get("contact_id")
    email = (identity.get("email") or "").strip() or None
    phone = (identity.get("phone") or "").strip() or None

    contact = None
    if contact_id:
        contact = MarketingContact.query.filter_by(contact_uid=str(contact_id)).first()
        if not contact and str(contact_id).isdigit():
            contact = MarketingContact.query.get(int(contact_id))

    if not contact and email:
        contact = MarketingContact.query.filter(MarketingContact.email == email).first()
    if not contact and phone:
        contact = MarketingContact.query.filter(MarketingContact.phone == phone).first()

    if contact:
        return contact

    if not email and not phone:
        return None

    now = _utc_now()
    contact = MarketingContact(
        contact_uid=str(uuid.uuid4()),
        email=email,
        phone=phone,
        status="active",
        lifecycle_stage="lead",
        locale="ko-KR",
        timezone="Asia/Seoul",
        created_at=now,
        updated_at=now,
    )
    db.session.add(contact)
    db.session.flush()
    return contact


def _apply_contact_progress(contact: MarketingContact, event_name: str, event_ts: datetime) -> None:
    mapping = EVENT_JOURNEY_MAP.get(event_name)
    if not contact or not mapping:
        return

    journey_id, next_state, lifecycle_stage = mapping
    contact.lifecycle_stage = lifecycle_stage
    contact.updated_at = event_ts

    journey = MarketingJourneyState.query.filter_by(
        contact_id=contact.id,
        journey_id=journey_id,
    ).first()
    if not journey:
        journey = MarketingJourneyState(
            contact_id=contact.id,
            journey_id=journey_id,
            state=next_state,
            entered_at=event_ts,
            last_action_at=event_ts,
            cooldown_until=None,
            version=1,
        )
        db.session.add(journey)
        return

    if journey.state != next_state:
        journey.state = next_state
        journey.entered_at = event_ts
        journey.version += 1
    journey.last_action_at = event_ts


@event_gateway_bp.route("/events", methods=["POST"])
def ingest_event():
    ingest_token = os.getenv("EVENT_INGEST_TOKEN") or ""
    if ingest_token:
        provided = request.headers.get("X-Event-Token") or _extract_bearer_token(request.headers.get("Authorization"))
        if provided != ingest_token:
            return jsonify({"accepted": False, "error": "unauthorized ingest token"}), 401

    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"accepted": False, "error": "invalid JSON body"}), 400

    event_name = (payload.get("event_name") or "").strip()
    if not event_name:
        return jsonify({"accepted": False, "error": "event_name is required"}), 400

    event_id = str(payload.get("event_id") or uuid.uuid4())
    event_ts = _parse_event_ts(payload.get("ts"))
    identity = payload.get("identity") if isinstance(payload.get("identity"), dict) else {}
    context = payload.get("context") if isinstance(payload.get("context"), dict) else {}
    props = payload.get("props") if isinstance(payload.get("props"), dict) else {}

    idempotency_key = str(payload.get("idempotency_key") or event_id)
    duplicate = MarketingEvent.query.filter(
        or_(
            MarketingEvent.event_id == event_id,
            MarketingEvent.idempotency_key == idempotency_key,
        )
    ).first()
    if duplicate:
        return jsonify(
            {
                "accepted": True,
                "duplicate": True,
                "event_id": duplicate.event_id,
                "idempotency_key": duplicate.idempotency_key,
            }
        ), 200

    try:
        contact = _resolve_contact(identity)
        if contact:
            _apply_contact_progress(contact, event_name, event_ts)
        event = MarketingEvent(
            event_id=event_id,
            event_name=event_name,
            event_ts=event_ts,
            contact_id=contact.id if contact else None,
            anonymous_id=identity.get("anonymous_id"),
            context_json=context,
            props_json=props,
            idempotency_key=idempotency_key,
            processing_status="pending",
            processing_updated_at=_utc_now(),
            created_at=_utc_now(),
        )
        db.session.add(event)
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({"accepted": False, "error": "event persistence failed"}), 500

    return jsonify(
        {
            "accepted": True,
            "duplicate": False,
            "event_id": event.event_id,
            "idempotency_key": event.idempotency_key,
        }
    ), 201
