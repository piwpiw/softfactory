"""
core/notifier.py
─────────────────────────────────────────────────────────────────
전 에이전트 공통 Telegram 알림 헬퍼.
모든 에이전트는 작업 완료/실패/블록 시 `notify()` 를 호출.
설정이 없으면 dry-run 로그로 폴백 (절대 크래시 없음).
─────────────────────────────────────────────────────────────────
"""

from __future__ import annotations

import json
import os
import urllib.request
from datetime import datetime
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")
except ImportError:
    pass

_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
_CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID", "")
_PROJECT   = os.getenv("PROJECT_NAME", "CooCook")


# ── Status → icon 매핑 ──────────────────────────────────────────

_ICONS = {
    "COMPLETE":    "✅",
    "BLOCKED":     "🚨",
    "IN_PROGRESS": "⚙️",
    "PENDING":     "⏳",
    "DEPLOYMENT":  "🚀",
    "ESCALATION":  "⚠️",
    "SECURITY":    "🔐",
    "QA":          "🔍",
    "ADR":         "🏗️",
    "PRD":         "📋",
    "ERROR":       "❌",
}


def _fmt(agent_id: str, agent_name: str, event: str,
         status: str, summary: str, outputs: list[str] = None) -> str:
    icon = _ICONS.get(status.upper(), "📌")
    ts   = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    out_lines = ""
    if outputs:
        out_lines = "\n" + "\n".join(f"  📄 {o}" for o in outputs[:4])

    return (
        f"{icon} <b>[{agent_id}] {agent_name}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🎯 Project: <code>{_PROJECT}</code>\n"
        f"📋 Event: {event}\n"
        f"📊 Status: <code>{status}</code>\n"
        f"📝 {summary[:200]}"
        f"{out_lines}\n"
        f"🕐 {ts}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"<i>Deca-Agent Max | Sonol-Bot</i>"
    )


def _send_sync(message: str) -> bool:
    """동기 전송 — asyncio 없이 어느 컨텍스트에서도 호출 가능."""
    if not _BOT_TOKEN or not _CHAT_ID:
        print(f"[Notifier DRY-RUN]\n{message}\n")
        return False
    try:
        url     = f"https://api.telegram.org/bot{_BOT_TOKEN}/sendMessage"
        payload = json.dumps({
            "chat_id": _CHAT_ID,
            "text": message,
            "parse_mode": "HTML",
        }).encode("utf-8")
        req = urllib.request.Request(
            url, data=payload, headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read())
            return bool(result.get("ok"))
    except Exception as e:
        print(f"[Notifier] Send failed (non-fatal): {e}")
        return False


def notify(
    agent_id: str,
    agent_name: str,
    event: str,
    status: str,
    summary: str,
    outputs: list[str] = None,
    mission_id: str = "",
    min_priority: str = "ALL",      # ALL | IMPORTANT | CRITICAL
) -> bool:
    """
    에이전트 어디서나 호출 가능한 Telegram 알림.

    min_priority:
      ALL       — 모든 이벤트 전송 (개발/테스트용)
      IMPORTANT — COMPLETE, BLOCKED, DEPLOYMENT만
      CRITICAL  — BLOCKED, ESCALATION, ERROR만

    Returns: True if sent, False if skipped/failed (절대 예외 없음)
    """
    try:
        _priority_map = {
            "ALL":       {"COMPLETE", "BLOCKED", "IN_PROGRESS", "DEPLOYMENT",
                          "ESCALATION", "SECURITY", "QA", "ADR", "PRD", "ERROR", "PENDING"},
            "IMPORTANT": {"COMPLETE", "BLOCKED", "DEPLOYMENT", "ESCALATION", "ERROR"},
            "CRITICAL":  {"BLOCKED", "ESCALATION", "ERROR"},
        }
        allowed = _priority_map.get(min_priority, _priority_map["ALL"])
        if status.upper() not in allowed:
            return False  # 우선순위 미달 → 무시

        mission_prefix = f"Mission <code>{mission_id}</code>\n" if mission_id else ""
        message = _fmt(agent_id, agent_name, event, status,
                       mission_prefix + summary, outputs)
        return _send_sync(message)
    except Exception as e:
        print(f"[Notifier] Unexpected error (non-fatal): {e}")
        return False
