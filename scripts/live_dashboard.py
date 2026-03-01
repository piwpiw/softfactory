"""
scripts/live_dashboard.py
─────────────────────────────────────────────────────────────────
Deca-Agent Live Dashboard — 10분 단위 Telegram 상태 보고
Every 10 minutes: collects ALL agent status + mission + consultations
and sends a rich HTML summary to Telegram.

Usage:
  python scripts/live_dashboard.py            # 10분 루프 실행
  python scripts/live_dashboard.py --now      # 지금 즉시 1회 전송
  python scripts/live_dashboard.py --interval 5  # 5분 간격 (테스트용)

pm2 등록:
  pm2 start scripts/live_dashboard.py --name deca-dashboard --interpreter python
─────────────────────────────────────────────────────────────────
"""

import sys
import os
import json
import asyncio
import time
import argparse
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from core import get_manager, get_logger
from core.ledger import LEDGER_PATH

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID", "")
PROJECT   = os.getenv("PROJECT_NAME", "CooCook")
LOGS_DIR  = Path(__file__).parent.parent / "logs"
DOCS_DIR  = Path(__file__).parent.parent / "docs" / "generated"

logger = get_logger("00", "Dashboard")

# ─── Agent 정의 ────────────────────────────────────────────────

AGENTS = [
    ("01", "Chief-Dispatcher",   "🧭"),
    ("02", "Product-Manager",    "📋"),
    ("03", "Market-Analyst",     "📊"),
    ("04", "Solution-Architect", "🏗️"),
    ("05", "Backend-Developer",  "⚙️"),
    ("06", "Frontend-Developer", "🎨"),
    ("07", "QA-Engineer",        "🔍"),
    ("08", "Security-Auditor",   "🔐"),
    ("09", "DevOps-Engineer",    "🚀"),
    ("10", "Telegram-Reporter",  "📣"),
]

# 표시 이름 (Telegram 메시지에서 짧게)
AGENT_DISPLAY = {
    "01": "Dispatcher",   "02": "PM",       "03": "Analyst",
    "04": "Architect",    "05": "Backend",  "06": "Frontend",
    "07": "QA",           "08": "Security", "09": "DevOps",
    "10": "Reporter",
}

# ─── 데이터 수집 ────────────────────────────────────────────────

def collect_missions() -> list[dict]:
    log_path = LOGS_DIR / "missions.jsonl"
    if not log_path.exists():
        return []
    missions: dict[str, dict] = {}
    with open(log_path, encoding="utf-8") as f:
        for line in f:
            try:
                entry = json.loads(line)
                mid = entry.get("mission_id")
                if mid:
                    missions[mid] = entry
            except Exception:
                pass
    return list(missions.values())


def collect_recent_consultations(minutes: int = 10) -> list[dict]:
    log_path = LOGS_DIR / "consultations.jsonl"
    if not log_path.exists():
        return []
    cutoff = (datetime.utcnow() - timedelta(minutes=minutes)).isoformat()
    recent = []
    with open(log_path, encoding="utf-8") as f:
        for line in f:
            try:
                entry = json.loads(line)
                if entry.get("timestamp", "") >= cutoff and entry.get("type") == "REQUEST":
                    recent.append(entry)
            except Exception:
                pass
    return recent


def collect_generated_docs() -> list[str]:
    if not DOCS_DIR.exists():
        return []
    docs = []
    for root, dirs, files in os.walk(DOCS_DIR):
        for f in files:
            if f.endswith(".md"):
                docs.append(f)
    return docs


def get_agent_last_activity(agent_id: str, agent_name: str) -> tuple[str, str]:
    """
    Returns (status, last_action) from the agent's log file.
    파일명 패턴: {id}_{Name}.log  예) 02_Product-Manager.log
    """
    candidate = LOGS_DIR / f"{agent_id}_{agent_name}.log"
    if candidate.exists():
        try:
            lines = candidate.read_text(encoding="utf-8", errors="ignore").strip().splitlines()
            # 의미있는 마지막 줄 찾기 (INFO 이상)
            for line in reversed(lines):
                if not line.strip():
                    continue
                low = line.lower()
                if "error" in low:
                    return "ERROR",   _clip(line)
                if "blocked" in low or "warning" in low:
                    return "BLOCKED", _clip(line)
                if any(k in low for k in ("complete", "generated", "deployed", "passed", "sent")):
                    return "COMPLETE", _clip(line)
                if "info" in low or any(k in low for k in ("starting", "running", "analyzing")):
                    return "ACTIVE",  _clip(line)
        except Exception:
            pass
    return "IDLE", "No recent activity"


def _clip(s: str, n: int = 55) -> str:
    # log line 형식: "[02][Product-Manager] INFO - message" → message 부분만 추출
    import re
    m = re.search(r"(?:INFO|WARNING|ERROR)\s*[-–]\s*(.+)", s)
    text = m.group(1) if m else s
    return text[:n] + ("…" if len(text) > n else "")


def collect_agent_status() -> list[dict]:
    statuses = []
    for agent_id, name, icon in AGENTS:
        status, last = get_agent_last_activity(agent_id, name)
        statuses.append({
            "id": agent_id, "name": name, "icon": icon,
            "status": status, "last": last,
        })
    return statuses


# ─── 메시지 포매팅 ────────────────────────────────────────────

STATUS_ICON = {
    "COMPLETE":    "✅",
    "IN_PROGRESS": "⚙️",
    "BLOCKED":     "🚨",
    "PENDING":     "⏳",
    "ARCHIVED":    "🗄️",
    "ACTIVE":      "🔄",
    "IDLE":        "💤",
    "ERROR":       "❌",
}


def format_dashboard(
    missions: list[dict],
    agents: list[dict],
    consultations: list[dict],
    docs: list[str],
    interval_min: int = 10,
) -> str:
    now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    next_str = (datetime.utcnow() + timedelta(minutes=interval_min)).strftime("%H:%M UTC")

    # ── HEADER ──────────────────────────────────────────
    lines = [
        f"🤖 <b>Deca-Agent Live Dashboard</b>",
        f"📌 Project: <code>{PROJECT}</code>",
        f"🕐 {now_str}  |  Next: {next_str}",
        "━━━━━━━━━━━━━━━━━━━━",
        "",
    ]

    # ── MISSIONS ────────────────────────────────────────
    lines.append("📋 <b>ACTIVE MISSIONS</b>")
    if missions:
        for m in missions[-5:]:  # 최근 5개
            s_icon = STATUS_ICON.get(m.get("status", ""), "📌")
            phase  = m.get("phase", "—")
            lines.append(
                f"  {s_icon} <code>{m['mission_id']}</code> [{m.get('status','')}]"
                f"  Phase: {phase}"
                f"\n     └ {m.get('name','')[:40]}"
            )
    else:
        lines.append("  (미션 없음)")
    lines.append("")

    # ── ALL 10 AGENTS ────────────────────────────────────
    lines.append("🤖 <b>AGENT STATUS</b>")
    for agent in agents:
        s_icon = STATUS_ICON.get(agent["status"], "❓")
        display = AGENT_DISPLAY.get(agent["id"], agent["name"])
        lines.append(
            f"  {agent['icon']} <b>{agent['id']}/{display}</b> {s_icon}"
            f"\n     └ {agent['last']}"
        )
    lines.append("")

    # ── CONSULTATIONS (최근 N분) ──────────────────────────
    lines.append(f"💬 <b>CONSULTATIONS (last {interval_min}min)</b>")
    if consultations:
        for c in consultations[-5:]:  # 최근 5개
            c_type = c.get("consultation_type", "")
            lines.append(
                f"  🔗 {c['from_agent'][:20]} → {c['to_agent'][:20]}"
                f"  [{c_type}]"
            )
    else:
        lines.append(f"  (최근 {interval_min}분간 상호협의 없음)")
    lines.append("")

    # ── GENERATED DOCS ─────────────────────────────────────
    lines.append("📄 <b>GENERATED DOCUMENTS</b>")
    if docs:
        for d in docs[-4:]:
            lines.append(f"  📝 {d}")
    else:
        lines.append("  (생성된 문서 없음)")
    lines.append("")

    # ── FOOTER ─────────────────────────────────────────────
    lines.append("━━━━━━━━━━━━━━━━━━━━")
    lines.append(
        f"<i>Deca-Agent Max | Sonol-Bot | "
        f"Consultations: {len(consultations)} | Docs: {len(docs)}</i>"
    )

    return "\n".join(lines)


# ─── Telegram 전송 ──────────────────────────────────────────────

async def send_telegram(message: str) -> bool:
    if not BOT_TOKEN or not CHAT_ID:
        print("[DRY RUN] Telegram credentials not set. Message preview:")
        print(message)
        return False
    try:
        import urllib.request
        url     = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = json.dumps({
            "chat_id": CHAT_ID,
            "text": message,
            "parse_mode": "HTML",
        }).encode("utf-8")
        req = urllib.request.Request(
            url, data=payload, headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read())
            if result.get("ok"):
                logger.info("Dashboard sent to Telegram ✓")
                return True
            else:
                logger.error(f"Telegram API error: {result}")
                return False
    except Exception as e:
        logger.error(f"Send failed: {e}")
        return False


# ─── 메인 루프 ──────────────────────────────────────────────────

async def run_once(interval_min: int = 10) -> bool:
    logger.info("Collecting dashboard data...")
    missions      = collect_missions()
    agents        = collect_agent_status()
    consultations = collect_recent_consultations(interval_min)
    docs          = collect_generated_docs()

    message = format_dashboard(missions, agents, consultations, docs, interval_min)
    print("\n" + "="*50)
    print(f"Dashboard Preview ({datetime.utcnow().strftime('%H:%M:%S UTC')}):")
    print("="*50)
    # 터미널에도 plain-text 버전 출력
    import re
    plain = re.sub(r"<[^>]+>", "", message)
    print(plain)
    print("="*50 + "\n")
    return await send_telegram(message)


async def run_loop(interval_min: int = 10):
    logger.info(f"Deca-Agent Live Dashboard started. Interval: {interval_min}min")
    print(f"[Dashboard] 시작됨. {interval_min}분 간격 Telegram 전송.")
    print(f"[Dashboard] 중지: Ctrl+C\n")

    while True:
        try:
            ok = await run_once(interval_min)
            status_str = "✓ Sent" if ok else "✗ Dry-run/failed"
            print(f"[{datetime.utcnow().strftime('%H:%M:%S')}] {status_str} — next in {interval_min}min")
        except Exception as e:
            logger.error(f"Dashboard error: {e}")
            print(f"[ERROR] {e}")

        await asyncio.sleep(interval_min * 60)


# ─── Entry Point ────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Deca-Agent Live Dashboard")
    parser.add_argument("--now",      action="store_true", help="지금 즉시 1회 전송")
    parser.add_argument("--interval", type=int, default=10, help="전송 간격(분), 기본 10")
    args = parser.parse_args()

    if args.now:
        asyncio.run(run_once(args.interval))
    else:
        asyncio.run(run_loop(args.interval))
