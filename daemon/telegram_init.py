#!/usr/bin/env python3
"""Initialize Telegram bot polling and message I/O"""

import sys
import os
import json
from pathlib import Path

# Add project root and daemon to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "daemon"))

# Load environment
from dotenv import load_dotenv
load_dotenv()

# Use skill_bridge to load telegram module
from daemon.skill_bridge import get_telegram_skill

telegram_module = get_telegram_skill()

def init_telegram_bot():
    """Initialize Telegram bot with polling"""

    # Bot credentials from config
    bot_token = "8461725251:AAELKRbZkpa3u6WK24q4k-RGkzedHxjTLiM"
    allowed_users = [7910169750]
    bot_user_id = 7910169750

    print("[Telegram] Initializing bot: piwpiwtelegrambot")
    print(f"[Telegram] Token: {bot_token[:15]}...")
    print(f"[Telegram] Allowed users: {allowed_users}")

    # Build runtime configuration using skill module
    runtime = telegram_module.build_runtime_vars({
        "telegram_bot_token": bot_token,
        "telegram_allowed_users": [bot_user_id],  # List format
        "telegram_user_id": bot_user_id,
        "telegram_include_24h_context": True,
        "work_dir": str(project_root / "daemon"),
        "message_retention_days": 7,
    })

    print("[Telegram] Runtime configured")

    # Load or initialize message store
    try:
        store = telegram_module.load_message_store(str(project_root / "daemon" / "telegram_messages.json"))
        last_update_id = store.get("last_update_id", 0)
        print(f"[Telegram] Loaded message store (last_update_id: {last_update_id})")
    except FileNotFoundError:
        last_update_id = 0
        print("[Telegram] Creating new message store")

    # Test polling
    print("[Telegram] Starting message polling...")
    try:
        new_messages, new_last_update_id = telegram_module.receive_once(runtime, last_update_id=last_update_id)
        print(f"[Telegram] Received {len(new_messages)} message(s)")

        if new_messages:
            # Store messages
            telegram_module.append_messages_to_store(
                str(project_root / "daemon" / "telegram_messages.json"),
                new_messages,
                new_last_update_id
            )

            # Echo first message back
            for msg in new_messages:
                print(f"[Telegram] Message from {msg['chat_id']}: {msg.get('text', '[attachment]')}")

                # Send confirmation back
                if msg.get('text'):
                    response = f"Received: {msg['text'][:50]}"
                    telegram_module.send_text_retry(runtime, chat_id=msg['chat_id'], text=response)
                    print(f"[Telegram] Sent confirmation")
        else:
            print("[Telegram] No new messages")

            # Send test message to verify connectivity
            test_msg = "SoftFactory v2.0 - Telegram bot is now active and monitoring messages"
            telegram_module.send_text_retry(runtime, chat_id=bot_user_id, text=test_msg)
            print("[Telegram] Sent activation confirmation")

    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False

    print("[Telegram] Bot initialization complete!")
    print("[Telegram] Bot is ready to send/receive messages")
    return True

if __name__ == "__main__":
    success = init_telegram_bot()
    sys.exit(0 if success else 1)
