# 📊 Agent 10 — Telegram Reporter (Sonol-Bot)

> **Purpose**: **Role:** Real-time mission notifications via Telegram. Kept alive 24/7 by pm2.
> **Status**: 🟢 ACTIVE (관리 중)
> **Impact**: [Engineering / Operations]

---

## ⚡ Executive Summary (핵심 요약)
- **주요 내용**: 본 문서는 Agent 10 — Telegram Reporter (Sonol-Bot) 관련 핵심 명세 및 관리 포인트를 포함합니다.
- **상태**: 현재 최신화 완료 및 검토 됨.
- **연관 문서**: [Master Index](./NOTION_MASTER_INDEX.md)

---

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