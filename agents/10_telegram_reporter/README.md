# Agent 10 — Telegram Reporter (Sonol-Bot)

**Role:** Real-time mission notifications via Telegram. Kept alive 24/7 by pm2.

## Setup
1. Create a Telegram bot via [@BotFather](https://t.me/BotFather) → get `BOT_TOKEN`
2. Get your `CHAT_ID` (send a message to your bot, then call `getUpdates`)
3. Copy `.env.example` → `.env`, fill in credentials
4. Install pm2: `npm install -g pm2`
5. Start: `cd agents/10_telegram_reporter && pm2 start ecosystem.config.js`
6. Save: `pm2 save && pm2 startup`

## Triggers (per .clauderules Rule 8)
- Mission COMPLETE
- BLOCKED escalation
- DevOps deployment confirmation

## Message Format
```
✅ Deca-Agent Report
━━━━━━━━━━━━━━━━━━━━
🎯 Mission: M-002
📋 Event: DEPLOYMENT
📊 Status: COMPLETE
📝 Summary: CooCook API v0.1 deployed to staging
━━━━━━━━━━━━━━━━━━━━
CooCook Deca-Agent | Sonol-Bot
```
