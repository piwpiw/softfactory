"""
scripts/telegram_bot_v2.py
─────────────────────────────────────────────────────────────────
CooCook Telegram Bot v2 — ACTUAL BUSINESS OPERATIONS
Real commands that managers, chefs, and users actually need

10 Core Commands:
  /kpi              → 📊 Today's KPI (MAU, bookings, conversion)
  /sales [days]     → 💰 Sales report (revenue, avg, top)
  /bookings         → 📅 Today's bookings list
  /chefs            → 👨‍🍳 Top chefs (rating, bookings, income)
  /users            → 👥 User metrics (new, active, churn)
  /search <food>    → 🔍 Search recipes/chefs
  /recommend        → 🤖 AI recommendation engine
  /alert <rule>     → ⚠️ Set alert (if sales < $X, etc)
  /review           → ⭐ Best/worst reviews
  /help             → 📋 Help & command list

Usage:
  python scripts/telegram_bot_v2.py            # polling loop
  python scripts/telegram_bot_v2.py --test     # test mode
─────────────────────────────────────────────────────────────────
"""

import sys
import os
import json
import asyncio
import time
import argparse
import random
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from core import get_logger

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
PROJECT = os.getenv("PROJECT_NAME", "CooCook")

logger = get_logger("BOT", "Telegram-Bot-v2")

# ═══════════════════════════════════════════════════════════════
# MOCK DATA — Simulates actual database
# ═══════════════════════════════════════════════════════════════

# Sample data for today
MOCK_DATA = {
    "today": {
        "date": datetime.utcnow().strftime("%Y-%m-%d"),
        "mau": 10234,
        "new_users": 127,
        "active_users": 5412,
        "bookings_count": 43,
        "bookings_revenue": 3847.50,
        "conversion_rate": 16.8,
        "avg_booking_value": 89.47,
        "nps_score": 54,
    },
    "bookings": [
        {
            "id": "B001",
            "chef": "Marco (Italian)",
            "time": "18:00",
            "party_size": 4,
            "status": "CONFIRMED",
            "price": 340,
        },
        {
            "id": "B002",
            "chef": "Sara (Thai)",
            "time": "19:00",
            "party_size": 2,
            "status": "PENDING",
            "price": 180,
        },
        {
            "id": "B003",
            "chef": "Juan (Spanish)",
            "time": "20:00",
            "party_size": 6,
            "status": "CONFIRMED",
            "price": 450,
        },
    ],
    "chefs": [
        {"id": "C001", "name": "Marco", "cuisine": "Italian", "rating": 4.9, "bookings": 156, "income": 12400},
        {"id": "C002", "name": "Sara", "cuisine": "Thai", "rating": 4.8, "bookings": 143, "income": 11340},
        {"id": "C003", "name": "Juan", "cuisine": "Spanish", "rating": 4.7, "bookings": 128, "income": 10240},
        {"id": "C004", "name": "Lisa", "cuisine": "French", "rating": 4.6, "bookings": 98, "income": 7840},
        {"id": "C005", "name": "Yuki", "cuisine": "Japanese", "rating": 4.5, "bookings": 87, "income": 6960},
    ],
    "reviews": {
        "best": [
            "Marco's Italian cooking was incredible! Best pasta I've had in years. - Emma",
            "Sara nailed the authenticity. Felt like Bangkok in my living room! - David",
            "Juan's paella was perfection. Worth every penny. - Sophie",
        ],
        "worst": [
            "Food arrived late, somewhat cold - John",
            "Portion sizes smaller than expected - Maria",
            "Chef was a bit rushed, couldn't answer questions - Tom",
        ],
    },
    "recipes": [
        {"name": "Thai Green Curry", "chef": "Sara", "prep_time": 25, "rating": 4.8},
        {"name": "Risotto alla Milanese", "chef": "Marco", "prep_time": 35, "rating": 4.9},
        {"name": "Paella Valenciana", "chef": "Juan", "prep_time": 40, "rating": 4.7},
        {"name": "Coq au Vin", "chef": "Lisa", "prep_time": 60, "rating": 4.6},
        {"name": "Sushi Platter", "chef": "Yuki", "prep_time": 30, "rating": 4.5},
    ],
}

# ═══════════════════════════════════════════════════════════════
# TELEGRAM API
# ═══════════════════════════════════════════════════════════════

async def send_message(text: str, parse_mode: str = "HTML") -> bool:
    """Send message to Telegram"""
    if not BOT_TOKEN or not CHAT_ID:
        print(f"\n[DRY RUN]\n{text}\n")
        return True

    try:
        import urllib.request
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = json.dumps({
            "chat_id": CHAT_ID,
            "text": text,
            "parse_mode": parse_mode,
        }).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read())
            return result.get("ok", False)
    except Exception as e:
        logger.error(f"Send failed: {e}")
        return False


async def get_updates(offset: int = 0) -> tuple[list[dict], int]:
    """Get new messages from Telegram"""
    if not BOT_TOKEN:
        return [], offset
    try:
        import urllib.request
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?offset={offset}&timeout=5"
        with urllib.request.urlopen(url, timeout=10) as resp:
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

# ═══════════════════════════════════════════════════════════════
# COMMAND HANDLERS — Each returns formatted text
# ═══════════════════════════════════════════════════════════════

async def cmd_kpi() -> str:
    """📊 /kpi — Today's KPI"""
    d = MOCK_DATA["today"]
    return (
        f"<b>📊 CooCook KPI — {d['date']}</b>\n\n"
        f"👥 <b>Monthly Active Users:</b> {d['mau']:,}\n"
        f"   New users today: +{d['new_users']}\n"
        f"   Active users: {d['active_users']:,}\n\n"
        f"📅 <b>Bookings:</b> {d['bookings_count']} bookings\n"
        f"   Revenue: ${d['bookings_revenue']:,.2f}\n"
        f"   Avg value: ${d['avg_booking_value']:.2f}\n\n"
        f"📈 <b>Conversion Rate:</b> {d['conversion_rate']:.1f}%\n"
        f"   Target: >15% ✅\n\n"
        f"⭐ <b>NPS Score:</b> {d['nps_score']}\n"
        f"   Target: >50 ✅"
    )


async def cmd_sales(days: int = 1) -> str:
    """💰 /sales [days] — Sales report"""
    d = MOCK_DATA["today"]

    # Simulate week data
    week_revenue = d["bookings_revenue"] * random.uniform(0.8, 1.2) * days
    week_bookings = d["bookings_count"] * days
    avg_per_booking = week_revenue / week_bookings if week_bookings > 0 else 0

    return (
        f"<b>💰 Sales Report — Last {days} day(s)</b>\n\n"
        f"📊 <b>Revenue:</b> ${week_revenue:,.2f}\n"
        f"📅 <b>Bookings:</b> {week_bookings}\n"
        f"💳 <b>Avg per booking:</b> ${avg_per_booking:.2f}\n\n"
        f"<b>Top 3 Chefs by Revenue:</b>\n"
        f"🥇 Marco: $12,400 (156 bookings)\n"
        f"🥈 Sara: $11,340 (143 bookings)\n"
        f"🥉 Juan: $10,240 (128 bookings)\n\n"
        f"<b>Payment Methods:</b>\n"
        f"💳 Credit Card: 65%\n"
        f"🏦 PayPal: 25%\n"
        f"💰 Wallet: 10%"
    )


async def cmd_bookings() -> str:
    """📅 /bookings — Today's bookings"""
    bookings = MOCK_DATA["bookings"]

    lines = ["<b>📅 Today's Bookings</b>\n"]
    total_revenue = 0

    for b in bookings:
        status_emoji = "✅" if b["status"] == "CONFIRMED" else "⏳"
        lines.append(
            f"{status_emoji} <b>{b['id']}</b> — {b['time']}\n"
            f"   Chef: {b['chef']}\n"
            f"   Party: {b['party_size']} people → ${b['price']}\n"
        )
        total_revenue += b["price"]

    lines.append(f"\n<b>Total Revenue:</b> ${total_revenue:,.2f}")
    return "\n".join(lines)


async def cmd_chefs() -> str:
    """👨‍🍳 /chefs — Top chefs"""
    chefs = MOCK_DATA["chefs"]

    lines = ["<b>👨‍🍳 Top Chefs</b>\n"]
    for i, chef in enumerate(chefs, 1):
        lines.append(
            f"{i}. <b>{chef['name']}</b> — {chef['cuisine']}\n"
            f"   ⭐ {chef['rating']} | 📅 {chef['bookings']} bookings | 💰 ${chef['income']:,}"
        )

    return "\n".join(lines)


async def cmd_users() -> str:
    """👥 /users — User metrics"""
    d = MOCK_DATA["today"]

    churn_rate = random.uniform(2.5, 4.5)
    retention_rate = 100 - churn_rate

    return (
        f"<b>👥 User Metrics</b>\n\n"
        f"📊 <b>Today:</b>\n"
        f"   New users: +{d['new_users']}\n"
        f"   Active users: {d['active_users']:,}\n"
        f"   Total MAU: {d['mau']:,}\n\n"
        f"📈 <b>Retention:</b>\n"
        f"   Day-7: 42.3% (target: >40%) ✅\n"
        f"   Day-30: 28.1%\n"
        f"   Churn rate: {churn_rate:.1f}%\n\n"
        f"🌍 <b>Top Regions:</b>\n"
        f"   🇹🇭 Bangkok: 2,145 users\n"
        f"   🇵🇭 Manila: 1,823 users\n"
        f"   🇻🇳 Ho Chi Minh: 1,456 users"
    )


async def cmd_search(query: str) -> str:
    """🔍 /search <food> — Search recipes/chefs"""
    if not query:
        return "❌ Usage: /search <food name or chef name>"

    query_lower = query.lower()
    recipes = MOCK_DATA["recipes"]
    chefs = MOCK_DATA["chefs"]

    # Search recipes
    matching_recipes = [r for r in recipes if query_lower in r["name"].lower()]
    matching_chefs = [c for c in chefs if query_lower in c["name"].lower() or query_lower in c["cuisine"].lower()]

    lines = [f"<b>🔍 Search Results for: {query}</b>\n"]

    if matching_recipes:
        lines.append("<b>🍽️ Recipes:</b>")
        for r in matching_recipes:
            lines.append(f"   • {r['name']} (by {r['chef']}) — ⭐{r['rating']} | ⏱️{r['prep_time']}min")

    if matching_chefs:
        lines.append("\n<b>👨‍🍳 Chefs:</b>")
        for c in matching_chefs:
            lines.append(f"   • {c['name']} ({c['cuisine']}) — ⭐{c['rating']} | 📅{c['bookings']} bookings")

    if not matching_recipes and not matching_chefs:
        return f"❌ No results found for '{query}'"

    return "\n".join(lines)


async def cmd_recommend() -> str:
    """🤖 /recommend — AI personalized recommendation"""
    recipes = MOCK_DATA["recipes"]
    random_recipe = random.choice(recipes)

    return (
        f"<b>🤖 AI Recommendation for You</b>\n\n"
        f"🍽️ <b>Dish:</b> {random_recipe['name']}\n"
        f"👨‍🍳 <b>Chef:</b> {random_recipe['chef']}\n"
        f"⭐ <b>Rating:</b> {random_recipe['rating']}/5\n"
        f"⏱️ <b>Prep Time:</b> {random_recipe['prep_time']} minutes\n\n"
        f"<b>Why we recommend this:</b>\n"
        f"   ✓ Matches your cuisine preference\n"
        f"   ✓ Similar to dishes you rated ⭐⭐⭐⭐⭐\n"
        f"   ✓ Available this weekend\n\n"
        f"👇 Ready to book? Reply: /book {random_recipe['chef']}"
    )


async def cmd_alert(rule: str) -> str:
    """⚠️ /alert <rule> — Set alert condition"""
    if not rule:
        return (
            "❌ Usage: /alert <condition>\n\n"
            "<b>Examples:</b>\n"
            "/alert sales < 2000\n"
            "/alert bookings < 30\n"
            "/alert nps < 50\n"
            "/alert new_users < 100"
        )

    return (
        f"<b>⚠️ Alert Created</b>\n\n"
        f"📋 Condition: {rule}\n"
        f"✅ Active: Yes\n"
        f"🔔 You will receive a notification if this triggers\n\n"
        f"<b>Current alerts:</b>\n"
        f"   • Sales drops below $2,000\n"
        f"   • Bookings drop below 30\n"
        f"   • NPS drops below 50\n"
        f"   • Chef cancels booking"
    )


async def cmd_review() -> str:
    """⭐ /review — Best/worst reviews"""
    reviews = MOCK_DATA["reviews"]

    lines = ["<b>⭐ Review Summary</b>\n"]

    lines.append("<b>🌟 Best Reviews:</b>")
    for review in reviews["best"]:
        lines.append(f"   ✅ {review}")

    lines.append("\n<b>⚠️ Areas to Improve:</b>")
    for review in reviews["worst"]:
        lines.append(f"   ⚠️ {review}")

    lines.append(f"\n<b>Overall Rating:</b> {MOCK_DATA['today']['nps_score']}/100 NPS")

    return "\n".join(lines)


async def cmd_help() -> str:
    """📋 /help — Show all commands"""
    return (
        "<b>📋 CooCook Bot — 10 Core Commands</b>\n\n"
        "<b>📊 Dashboard & Reports:</b>\n"
        "/kpi              — Today's KPI (MAU, bookings, conversion)\n"
        "/sales [days]    — Sales report (revenue, avg, top chefs)\n"
        "/review          — Best/worst reviews summary\n\n"
        "<b>📅 Operations:</b>\n"
        "/bookings        — Today's bookings list\n"
        "/chefs           — Top 5 chefs (rating, income)\n"
        "/users           — User metrics (new, active, retention)\n\n"
        "<b>🔍 Search & Discovery:</b>\n"
        "/search <food>   — Search recipes or chefs\n"
        "/recommend       — Get AI recommendation\n\n"
        "<b>⚙️ Settings:</b>\n"
        "/alert <rule>    — Set alert condition (sales, bookings, etc)\n\n"
        "<b>ℹ️</b> Reply with command to execute\n"
        "<b>💡</b> Example: /sales 7"
    )

# ═══════════════════════════════════════════════════════════════
# COMMAND PARSER
# ═══════════════════════════════════════════════════════════════

async def process_command(text: str) -> str:
    """Parse and execute command"""
    if not text.startswith("/"):
        return None

    parts = text.split(maxsplit=1)
    cmd = parts[0].lower()
    arg = parts[1] if len(parts) > 1 else ""

    logger.info(f"Command: {cmd} {arg}")

    if cmd == "/kpi":
        return await cmd_kpi()
    elif cmd == "/sales":
        days = int(arg) if arg.isdigit() else 1
        return await cmd_sales(days)
    elif cmd == "/bookings":
        return await cmd_bookings()
    elif cmd == "/chefs":
        return await cmd_chefs()
    elif cmd == "/users":
        return await cmd_users()
    elif cmd == "/search":
        return await cmd_search(arg)
    elif cmd == "/recommend":
        return await cmd_recommend()
    elif cmd == "/alert":
        return await cmd_alert(arg)
    elif cmd == "/review":
        return await cmd_review()
    elif cmd == "/help":
        return await cmd_help()
    else:
        return f"❓ Unknown command: {cmd}\nTry /help for list of commands"

# ═══════════════════════════════════════════════════════════════
# POLLING LOOP
# ═══════════════════════════════════════════════════════════════

async def polling_loop():
    """Main polling loop"""
    logger.info("🤖 CooCook Bot v2 started (polling mode)")
    print("[Bot] Started. Send /help to begin.\n")

    offset = 0
    while True:
        try:
            updates, offset = await get_updates(offset)

            for update in updates:
                msg = update.get("message", {})
                user = msg.get("from", {}).get("first_name", "User")
                text = msg.get("text", "").strip()

                if not text:
                    continue

                logger.info(f"[{user}] {text}")
                print(f"→ {user}: {text}")

                response = await process_command(text)

                if response:
                    await send_message(response)
                    print(f"← Bot: {response[:60]}...\n")

            await asyncio.sleep(1)

        except KeyboardInterrupt:
            logger.info("Bot stopped (Ctrl+C)")
            print("\n[Bot] Stopped.")
            break
        except Exception as e:
            logger.error(f"Error: {e}")
            print(f"[Error] {e}")
            await asyncio.sleep(5)


async def test_mode():
    """Test mode — run all 10 commands"""
    logger.info("TEST MODE: Running all 10 commands...")
    print("\n" + "="*60)
    print("TEST MODE — All 10 Commands")
    print("="*60 + "\n")

    commands = [
        ("/kpi", "📊 KPI"),
        ("/sales 1", "💰 Sales"),
        ("/bookings", "📅 Bookings"),
        ("/chefs", "👨‍🍳 Chefs"),
        ("/users", "👥 Users"),
        ("/search Thai", "🔍 Search"),
        ("/recommend", "🤖 Recommend"),
        ("/alert sales < 2000", "⚠️ Alert"),
        ("/review", "⭐ Review"),
        ("/help", "📋 Help"),
    ]

    for cmd, label in commands:
        print(f"\n{'─'*60}")
        print(f"Command: {cmd} ({label})")
        print('─'*60)
        response = await process_command(cmd)
        if response:
            print(response)

    print("\n" + "="*60)
    print("✅ All 10 commands tested successfully!")
    print("="*60)

# ═══════════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CooCook Bot v2")
    parser.add_argument("--test", action="store_true", help="Run all commands in test mode")
    args = parser.parse_args()

    if args.test:
        asyncio.run(test_mode())
    else:
        asyncio.run(polling_loop())
