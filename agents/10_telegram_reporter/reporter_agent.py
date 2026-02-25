"""
Agent 10 — Telegram Reporter (Sonol-Bot)
Event-driven notifications with priority routing, daily/weekly summaries.
Kept alive 24/7 by pm2. Requires TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env
"""

import sys
import os
import asyncio
import json
from datetime import datetime
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from core import ThoughtChain, ThinkingStep, TaskStatus, get_logger, log_to_ledger

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))
except ImportError:
    pass

AGENT_ID   = "10"
AGENT_NAME = "Telegram-Reporter"

logger = get_logger(AGENT_ID, AGENT_NAME)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID", "")

# ---------------------------------------------------------------------------
# Priority routing
# ---------------------------------------------------------------------------

PRIORITY_MAP = {
    "COMPLETE":    1,
    "DEPLOYMENT":  1,
    "BLOCKED":     0,    # Highest — always send immediately
    "ESCALATION":  0,
    "IN_PROGRESS": 3,
    "PENDING":     4,
    "DAILY":       2,
    "WEEKLY":      2,
}


def should_send(status: str, min_priority: int = 2) -> bool:
    """Only send if priority ≤ min_priority (lower number = higher urgency)."""
    return PRIORITY_MAP.get(status, 5) <= min_priority


# ---------------------------------------------------------------------------
# Message formatting
# ---------------------------------------------------------------------------

def format_message(event_type: str, mission_id: str, summary: str, status: str) -> str:
    icons = {
        "COMPLETE":    "✅",
        "BLOCKED":     "🚨",
        "IN_PROGRESS": "⚙️",
        "PENDING":     "⏳",
        "DEPLOYMENT":  "🚀",
        "ESCALATION":  "⚠️",
        "DAILY":       "📊",
        "WEEKLY":      "📈",
    }
    icon = icons.get(status, "📌")
    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    return (
        f"{icon} <b>Deca-Agent Report</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🎯 Mission: <code>{mission_id}</code>\n"
        f"📋 Event: {event_type}\n"
        f"📊 Status: <code>{status}</code>\n"
        f"📝 Summary: {summary}\n"
        f"🕐 Time: {ts}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"<i>CooCook Deca-Agent | Sonol-Bot</i>"
    )


def format_daily_summary(missions: list[dict]) -> str:
    lines = "\n".join(
        f"  • {m['id']} [{m['status']}] — {m['name']}" for m in missions
    )
    ts = datetime.utcnow().strftime("%Y-%m-%d")
    return (
        f"📊 <b>Daily Summary — {ts}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"Active Missions ({len(missions)}):\n{lines}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"<i>CooCook Deca-Agent | Sonol-Bot</i>"
    )


# ---------------------------------------------------------------------------
# Telegram API
# ---------------------------------------------------------------------------

async def send_telegram(message: str) -> bool:
    """Send message via Telegram Bot API."""
    if not BOT_TOKEN or not CHAT_ID:
        logger.warning("TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set. Message not sent.")
        logger.info(f"[DRY RUN] Would send:\n{message}")
        return False

    try:
        import urllib.request

        url     = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = json.dumps({
            "chat_id": CHAT_ID,
            "text": message,
            "parse_mode": "HTML",
        }).encode("utf-8")

        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read())
            if result.get("ok"):
                logger.info("Telegram message sent successfully.")
                return True
            else:
                logger.error(f"Telegram API error: {result}")
                return False
    except Exception as e:
        logger.error(f"Failed to send Telegram message: {e}")
        return False


# ---------------------------------------------------------------------------
# Report function (priority-aware)
# ---------------------------------------------------------------------------

def report(
    mission_id: str,
    event_type: str,
    summary: str,
    status: str,
    force: bool = False,
) -> bool:
    """
    Send a report notification.
    Only sends if status priority ≤ threshold (BLOCKED + COMPLETE always sent).
    force=True bypasses priority filter.
    """
    chain = (
        ThoughtChain(AGENT_ID, AGENT_NAME, f"Report {event_type}")
        .think(ThinkingStep.UNDERSTAND, f"Send {status} notification for mission {mission_id}")
        .think(ThinkingStep.DECOMPOSE, "1) Priority check 2) Format message 3) Send via Telegram API 4) Log")
        .think(ThinkingStep.EVALUATE, f"Priority level: {PRIORITY_MAP.get(status, 5)}. Min threshold: 2.")
        .think(ThinkingStep.DECIDE, f"{'Send' if force or should_send(status) else 'Skip'} — priority routing.")
        .think(ThinkingStep.EXECUTE, "Dispatching Telegram notification.")
        .think(ThinkingStep.HANDOFF, "No further agents. Pipeline complete.")
    )

    logger.info(chain.summary())

    if not force and not should_send(status):
        logger.info(f"Skipped low-priority notification: {status} for {mission_id}")
        return False

    message = format_message(event_type, mission_id, summary, status)
    sent    = asyncio.run(send_telegram(message))
    log_to_ledger(AGENT_NAME, f"Telegram notification sent for mission {mission_id} [{status}]")
    return sent


def send_daily_summary(missions: list[dict]) -> bool:
    """Send daily mission summary. Aggregates all active mission statuses."""
    message = format_daily_summary(missions)
    sent    = asyncio.run(send_telegram(message))
    log_to_ledger(AGENT_NAME, f"Daily summary sent — {len(missions)} missions")
    return sent


# ---------------------------------------------------------------------------
# Long-running listener mode (kept alive by pm2)
# ---------------------------------------------------------------------------

async def polling_loop():
    """Simple heartbeat loop. Replace with webhook in production."""
    logger.info("Sonol-Bot started. Polling for updates...")
    while True:
        logger.debug("Heartbeat — Sonol-Bot alive.")
        await asyncio.sleep(30)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--listen":
        asyncio.run(polling_loop())
    elif len(sys.argv) > 1 and sys.argv[1] == "--daily":
        send_daily_summary([
            {"id": "M-001", "status": "COMPLETE", "name": "Initial Infrastructure Setup"},
            {"id": "M-002", "status": "IN_PROGRESS", "name": "CooCook Market Analysis"},
        ])
    else:
        report("M-001", "INFRASTRUCTURE_SETUP", "Deca-Agent ecosystem initialized successfully.", "COMPLETE")
