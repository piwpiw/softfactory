"""
scripts/telegram_commander.py
─────────────────────────────────────────────────────────────────
Deca-Agent Telegram Commander — Accept commands, execute agents
polling-based (no webhook setup needed, runs immediately)

Supported commands:
  /help            → Show command list
  /status          → Send agent status + missions
  /dashboard       → Send live dashboard
  /mission <text>  → Create new mission + launch orchestrator
  /run <id>        → Run specific agent
  /cardnews <topic> → Generate card news (AI-powered)
  /trendlog <topic> → Generate AI trend blog (AI-powered)

Usage:
  python scripts/telegram_commander.py        # polling loop
  python scripts/telegram_commander.py --test # test mode (no actual polling)

pm2 registration:
  pm2 start scripts/telegram_commander.py --name coocook-commander --interpreter python
─────────────────────────────────────────────────────────────────
"""

import sys
import os
import json
import asyncio
import time
import argparse
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from core import get_logger
from core.ledger import LEDGER_PATH

try:
    from anthropic import Anthropic
    CLAUDE_CLIENT = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
except Exception:
    CLAUDE_CLIENT = None

# Reuse functions from live_dashboard.py
from scripts.live_dashboard import (
    collect_agent_status,
    collect_missions,
    collect_recent_consultations,
    collect_generated_docs,
    format_dashboard,
    AGENTS,
    AGENT_DISPLAY,
    STATUS_ICON,
)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID", "")
PROJECT   = os.getenv("PROJECT_NAME", "CooCook")
LOGS_DIR  = Path(__file__).parent.parent / "logs"
AGENTS_DIR = Path(__file__).parent.parent / "agents"

logger = get_logger("TCMD", "Telegram-Commander")


# ─── Telegram API ──────────────────────────────────────────────

async def send_message(text: str, parse_mode: str = "HTML") -> bool:
    """Send message to Telegram chat"""
    if not BOT_TOKEN or not CHAT_ID:
        print(f"[DRY RUN] {text[:100]}...")
        return False
    try:
        import urllib.request
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = json.dumps({
            "chat_id": CHAT_ID,
            "text": text,
            "parse_mode": parse_mode,
        }).encode("utf-8")
        req = urllib.request.Request(
            url, data=payload, headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read())
            return result.get("ok", False)
    except Exception as e:
        logger.error(f"Send failed: {e}")
        return False


async def get_updates(offset: int = 0) -> tuple[list[dict], int]:
    """Get new messages from Telegram (polling)"""
    if not BOT_TOKEN:
        return [], offset
    try:
        import urllib.request
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
        params = f"?offset={offset}&timeout=5"
        with urllib.request.urlopen(url + params, timeout=10) as resp:
            result = json.loads(resp.read())
            if result.get("ok"):
                updates = result.get("result", [])
                if updates:
                    offset = max(u.get("update_id", 0) for u in updates) + 1
                return updates, offset
        return [], offset
    except Exception as e:
        logger.warning(f"getUpdates failed: {e}")
        return [], offset


# ─── Command Handlers ──────────────────────────────────────────

async def handle_help() -> str:
    """Show command list"""
    return (
        "<b>🤖 CooCook Telegram Commander</b>\n\n"
        "<b>Core Commands:</b>\n"
        "/help          → Show this help\n"
        "/status        → Agent status + missions\n"
        "/dashboard     → Live dashboard (full report)\n"
        "/mission <txt> → Create new mission\n"
        "/run <id>      → Run specific agent\n\n"
        "<b>AI Content Generators:</b>\n"
        "/cardnews <topic>  → Generate card news (3-5 frames)\n"
        "/trendlog <topic>  → Generate AI trend blog post\n\n"
        "<i>Examples:</i>\n"
        "/cardnews Food trends 2026\n"
        "/trendlog Generative AI in hospitality\n"
        "/mission Analyze market trends\n"
    )


async def handle_status() -> str:
    """Send agent status"""
    agents = collect_agent_status()
    missions = collect_missions()

    lines = [
        f"<b>📊 Agent Status — {datetime.utcnow().strftime('%H:%M UTC')}</b>\n"
    ]

    for agent in agents:
        icon = agent["icon"]
        display = AGENT_DISPLAY.get(agent["id"], agent["name"])
        status_icon = STATUS_ICON.get(agent["status"], "❓")
        lines.append(
            f"{icon} <b>{agent['id']}/{display}</b> {status_icon}\n"
            f"   └ {agent['last']}"
        )

    lines.append(f"\n<b>📋 Missions ({len(missions)})</b>")
    for m in missions[-3:]:
        status_icon = STATUS_ICON.get(m.get("status", ""), "📌")
        lines.append(
            f"{status_icon} {m['mission_id']} [{m.get('status','?')}]\n"
            f"   └ {m.get('name','')[:40]}"
        )

    return "\n".join(lines)


async def handle_dashboard() -> str:
    """Send full dashboard"""
    missions = collect_missions()
    agents = collect_agent_status()
    consultations = collect_recent_consultations(10)
    docs = collect_generated_docs()
    return format_dashboard(missions, agents, consultations, docs, 10)


async def handle_mission(text: str) -> str:
    """Create new mission and launch dispatcher"""
    if not text.strip():
        return "❌ Usage: /mission <description>"

    mission_text = text.strip()
    logger.info(f"New mission: {mission_text}")

    # Create mission entry in ledger
    mission_id = f"M-{int(time.time()) % 100000:05d}"
    mission_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "mission_id": mission_id,
        "name": mission_text,
        "status": "PENDING",
        "phase": "DISPATCH",
    }

    try:
        logs_dir = LOGS_DIR
        logs_dir.mkdir(parents=True, exist_ok=True)
        with open(logs_dir / "missions.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(mission_entry) + "\n")
    except Exception as e:
        logger.error(f"Failed to log mission: {e}")

    # Launch dispatcher subprocess
    try:
        dispatcher_path = AGENTS_DIR / "01_dispatcher" / "dispatcher.py"
        proc = subprocess.Popen(
            [sys.executable, str(dispatcher_path), mission_id, mission_text],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        logger.info(f"Dispatcher launched for {mission_id}")
    except Exception as e:
        logger.error(f"Failed to launch dispatcher: {e}")
        return f"❌ Failed to create mission: {e}"

    return (
        f"✅ <b>Mission Created</b>\n"
        f"ID: <code>{mission_id}</code>\n"
        f"Task: {mission_text}\n\n"
        f"🚀 Dispatcher launched. Check /status for updates."
    )


async def handle_run(agent_id: str) -> str:
    """Run specific agent"""
    if not agent_id or len(agent_id) != 2:
        return "❌ Usage: /run <id>  (e.g., /run 02)"

    agent_id = agent_id.zfill(2)

    # Find agent
    agent_name = None
    for aid, aname, _ in AGENTS:
        if aid == agent_id:
            agent_name = aname
            break

    if not agent_name:
        return f"❌ Agent {agent_id} not found"

    logger.info(f"Running agent {agent_id}/{agent_name}")

    try:
        agent_path = AGENTS_DIR / f"{agent_id}_dispatcher" if agent_id == "01" else AGENTS_DIR / f"{agent_id}_{agent_name.replace('-', '_')}" / f"{agent_name.lower().replace('-', '_')}_agent.py"

        # Fallback: search for the agent file
        agent_dir = AGENTS_DIR / f"{agent_id}_{agent_name.replace('-', '_')}"
        if not agent_dir.exists():
            return f"❌ Agent directory not found: {agent_dir}"

        py_files = list(agent_dir.glob("*.py"))
        agent_file = next((f for f in py_files if f.name != "__init__.py"), None)

        if not agent_file:
            return f"❌ No agent script found in {agent_dir}"

        proc = subprocess.Popen(
            [sys.executable, str(agent_file)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        logger.info(f"Agent {agent_id} subprocess started")
        return (
            f"✅ <b>Agent Started</b>\n"
            f"{agent_id} - {agent_name}\n\n"
            f"Check /status for progress."
        )
    except Exception as e:
        logger.error(f"Failed to run agent {agent_id}: {e}")
        return f"❌ Failed to start agent: {e}"


async def handle_cardnews(topic: str) -> str:
    """Generate card news (3-5 social media frames)"""
    if not topic.strip():
        return "❌ Usage: /cardnews <topic>"

    if not CLAUDE_CLIENT:
        return "❌ Claude API not configured"

    logger.info(f"Generating card news for: {topic}")

    try:
        msg = CLAUDE_CLIENT.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=500,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Create 3-4 short card news frames about: {topic}\n"
                        f"Format: Frame 1: [title]\n[1-line summary]\n\n"
                        f"Use emojis, max 150 chars per frame."
                    ),
                }
            ],
        )
        content = msg.content[0].text
        logger.info(f"Card news generated ({len(content)} chars)")
        return f"📰 <b>Card News: {topic}</b>\n\n{content}"
    except Exception as e:
        logger.error(f"Card news generation failed: {e}")
        return f"❌ Generation failed: {str(e)[:100]}"


async def handle_trendlog(topic: str) -> str:
    """Generate AI trend blog post"""
    if not topic.strip():
        return "❌ Usage: /trendlog <topic>"

    if not CLAUDE_CLIENT:
        return "❌ Claude API not configured"

    logger.info(f"Generating trend log for: {topic}")

    try:
        msg = CLAUDE_CLIENT.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=600,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Write a brief AI/Tech trend blog post (200-300 words) about: {topic}\n"
                        f"Format: [Title]\n[3-4 short paragraphs]\n[3 key takeaways]\n"
                        f"Tone: Professional, insights-focused, for tech newsletter."
                    ),
                }
            ],
        )
        content = msg.content[0].text
        logger.info(f"Trend log generated ({len(content)} chars)")
        return f"📝 <b>Trend Log: {topic}</b>\n\n{content}"
    except Exception as e:
        logger.error(f"Trend log generation failed: {e}")
        return f"❌ Generation failed: {str(e)[:100]}"


# ─── Command Parser ────────────────────────────────────────────

async def process_command(text: str) -> str:
    """Parse and execute command"""
    if not text.startswith("/"):
        return None

    parts = text.split(maxsplit=1)
    cmd = parts[0].lower()
    arg = parts[1] if len(parts) > 1 else ""

    if cmd == "/help":
        return await handle_help()
    elif cmd == "/status":
        return await handle_status()
    elif cmd == "/dashboard":
        return await handle_dashboard()
    elif cmd == "/mission":
        return await handle_mission(arg)
    elif cmd == "/run":
        return await handle_run(arg)
    elif cmd == "/cardnews":
        return await handle_cardnews(arg)
    elif cmd == "/trendlog":
        return await handle_trendlog(arg)
    else:
        return f"❓ Unknown command: {cmd}\nTry /help"


# ─── Polling Loop ──────────────────────────────────────────────

async def polling_loop():
    """Main polling loop"""
    logger.info("Telegram Commander started (polling mode)")
    print("[Telegram Commander] Started. Send /help to begin.")

    offset = 0
    while True:
        try:
            updates, offset = await get_updates(offset)

            for update in updates:
                msg = update.get("message", {})
                chat_id = msg.get("chat", {}).get("id")
                user = msg.get("from", {}).get("first_name", "User")
                text = msg.get("text", "").strip()

                if not text:
                    continue

                logger.info(f"[{user}] {text[:50]}")

                # Process command
                response = await process_command(text)

                if response:
                    await send_message(response)
                    logger.info(f"Response sent ({len(response)} chars)")

            # Polling interval
            await asyncio.sleep(1)

        except KeyboardInterrupt:
            logger.info("Telegram Commander stopped (Ctrl+C)")
            break
        except Exception as e:
            logger.error(f"Polling error: {e}")
            await asyncio.sleep(5)


async def test_mode():
    """Test mode — send /help to verify setup"""
    logger.info("TEST MODE: Verifying Telegram connection...")

    msg = await handle_help()
    ok = await send_message(msg)

    if ok:
        print("✅ Telegram connection OK")
        print("📨 /help message sent to chat")
    else:
        print("❌ Telegram send failed (dry-run mode or invalid credentials)")
        print(f"BOT_TOKEN: {'***' if BOT_TOKEN else '(empty)'}")
        print(f"CHAT_ID: {CHAT_ID if CHAT_ID else '(empty)'}")


# ─── Entry Point ──────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CooCook Telegram Commander")
    parser.add_argument("--test", action="store_true", help="Test Telegram connection and exit")
    args = parser.parse_args()

    if args.test:
        asyncio.run(test_mode())
    else:
        asyncio.run(polling_loop())
