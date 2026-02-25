# Sonolbot — Telegram-Based Claude Integration Daemon

**Version:** 2.0 (Enhanced with Scheduling & Logging)
**Updated:** 2026-02-25

---

## Overview

Sonolbot is an advanced Telegram bot daemon that integrates Claude AI sessions with project task management. It enables developers to request code implementation, bug fixes, analysis, and deployment tasks directly through Telegram, with full session context and scheduling capabilities.

**Key Features:**
- ✅ 5 Core Commands (task management, status, help)
- ✅ 4 New Extended Commands (reminders, summaries, exports, logs)
- ✅ Background Scheduler (APScheduler integration)
- ✅ Automated Daily Standup (9 AM)
- ✅ Automated Weekly Summary (Friday 6 PM)
- ✅ Command Logging & Audit Trail
- ✅ Data Export (JSON, CSV)
- ✅ Intelligent Log Cleanup (7-day retention)

---

## Quick Start

### Prerequisites

```bash
Python 3.11+
Telegram Bot Token (from BotFather)
D:/Project/ structure with backend/frontend/scripts
APScheduler (auto-installed with python-telegram-bot)
```

### Installation

```bash
cd D:/Project/daemon
python -m venv .venv
source .venv/Scripts/activate  # Windows
pip install -r requirements.txt  # Create if needed
```

### Running Sonolbot

**Via Control Panel (GUI):**
```bash
pythonw.exe daemon_control_panel.py
```

**Via Command Line:**
```bash
python daemon_service.py
```

**For Development:**
```bash
python daemon_service.py --debug
```

---

## Command Reference

### Core Commands (Original 5)

| Command | Usage | Description |
|---------|-------|-------------|
| `/task-new [description]` | `/task-new Fix login bug` | Start a new Claude session task |
| `/task-list` | `/task-list` | View recent tasks (max 20) |
| `/task-activate [id]` | `/task-activate abc123` | Switch to existing task |
| `/s` | `/s` | Quick project status overview |
| `/h` | `/h` | Show help menu |

### New Extended Commands (v2.0)

| Command | Usage | Description |
|---------|-------|-------------|
| `/remind [date] [msg]` | `/remind 2026-02-28 배포 검토` | Set a date-based reminder |
| `/summary` | `/summary` | Get daily activity report |
| `/export [format]` | `/export json` or `/export csv` | Export task/log data |
| `/logs [lines]` | `/logs 50` | View recent command history |

### Examples

```
User: /remind 2026-03-01 CooCook API review
Bot: ✅ 알림을 설정했습니다.
     📅 2026-03-01
     💬 CooCook API review

User: /summary
Bot: 📊 일간 요약 리포트
     📅 2026-02-25 14:23
     📈 활성 TASK: 5개
     ⏳ 대기 중: 2개 메시지

User: /export csv
Bot: ✅ 데이터를 CSV 형식으로 내보냈습니다.
     sonolbot_export_20260225_142300.csv

User: /logs 30
Bot: 📝 최근 30개 명령어
     [2026-02-25 14:20:15] chat_id=7910169750 cmd=/task-new Fix auth
     [2026-02-25 14:15:42] chat_id=7910169750 cmd=/s
     ...
```

---

## Architecture

```
daemon_service.py
├── ClaudeDaemonService (Main daemon class)
├── Message Processing Pipeline
│   ├── _ingest_pending_messages()
│   ├── _handle_control_message() [NEW: logging]
│   └── _process_telegram_message()
├── Command Handlers (NEW in v2.0)
│   ├── _send_command_logs()
│   ├── _send_daily_summary()
│   ├── _export_data()
│   ├── _handle_reminder_command()
│   └── Logging: _log_command()
├── Scheduler (NEW in v2.0)
│   ├── _init_scheduler()
│   ├── _send_daily_standup() (9 AM)
│   ├── _send_weekly_summary() (Fri 6 PM)
│   ├── _cleanup_old_logs() (3 AM)
│   └── _schedule_reminder()
└── Persistence
    ├── reminders.json (scheduled reminders)
    ├── command_history.log (audit trail)
    └── tasks/ (Claude session workspaces)
```

---

## Files & Directories

```
D:/Project/daemon/
├── daemon_service.py          Main daemon (1000+ lines, v2.0 enhanced)
├── daemon_control_panel.py    GUI control panel
├── skill_bridge.py            Claude/Telegram skill integration
├── project_brain.md           Project context injected into Claude
├── README.md                  This file (NEW)
├── logs/                      Runtime logs & exports (auto-created)
│   ├── claude-runner.log     Claude execution logs
│   ├── sonolbot-daemon.log   Daemon lifecycle logs
│   ├── command_history.log   User command audit trail (NEW)
│   └── sonolbot_export_*.{json,csv}  Data exports (NEW)
├── state/                     Daemon state (auto-created)
│   ├── reminders.json        Scheduled reminders (NEW)
│   ├── active_task_by_chat.json
│   ├── task_queue.json
│   └── .daemon_service.pid
├── tasks/                     Claude session workspaces (auto-created)
│   └── chat_{id}/            Per-chat task directories
├── .venv/                     Python 3.11 virtual environment
├── requirements.txt           Python dependencies (optional)
└── .control_panel_telegram_bots.json  Bot config

```

---

## Configuration

### Environment Variables

```bash
# Daemon
DAEMON_POLL_INTERVAL_SEC=1           # Message polling frequency
LOG_RETENTION_DAYS=7                  # Log cleanup threshold (NEW)

# Claude
SONOLBOT_CLAUDE_MODEL=sonnet          # Claude model version
SONOLBOT_CLAUDE_EFFORT=high           # Reasoning effort level

# Telegram
SONOLBOT_BOT_ID=8461725251            # Bot ID from BotFather
SONOLBOT_ALLOWED_CHATS=7910169750     # Comma-separated chat IDs

# Scheduler (NEW in v2.0)
# Controlled via APScheduler built-in cron triggers
# Daily standup: 9:00 AM
# Weekly summary: Friday 6:00 PM
# Log cleanup: 3:00 AM
```

### .env File (Do Not Commit)

```env
TELEGRAM_BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
SONOLBOT_BOT_ID=8461725251
SONOLBOT_ALLOWED_CHATS=7910169750
DEBUG=true
```

---

## Logging

### Command History (`logs/command_history.log`)

```
[2026-02-25 14:20:15] chat_id=7910169750 cmd=/task-new text=Fix login page bug in SoftFactory
[2026-02-25 14:15:42] chat_id=7910169750 cmd=/s text=/s
[2026-02-25 14:10:00] chat_id=7910169750 cmd=/remind text=/remind 2026-02-28 배포 검토
```

**Automatic Cleanup:** Old logs are deleted at 3 AM daily (configurable via `LOG_RETENTION_DAYS`)

### Daemon Logs (`logs/sonolbot-daemon.log`)

```
[daemon] Daemon started
[daemon] Scheduler initialized and started
[daemon] Task created: task_id=thread_abc123 chat_id=7910169750
[daemon] Cleaned up old log: logs/sonolbot-daemon.20260218.log
```

---

## Data Export Formats

### JSON Export
```json
{
  "export_time": "2026-02-25T14:23:00.123456",
  "chat_id": 7910169750,
  "task_count": 5,
  "tasks": [
    {
      "task_id": "thread_abc123",
      "instruction": "Fix login page bug",
      "timestamp": "2026-02-25 10:00:00",
      "task_dir": "D:/Project/daemon/tasks/chat_7910169750/thread_abc123"
    },
    ...
  ],
  "queue_count": 0,
  "active_tasks": 5
}
```

### CSV Export
```csv
task_id,instruction,timestamp,task_dir
thread_abc123,Fix login page bug,2026-02-25 10:00:00,D:/Project/daemon/tasks/chat_7910169750/thread_abc123
thread_def456,Add CooCook API,2026-02-25 11:30:00,D:/Project/daemon/tasks/chat_7910169750/thread_def456
...
```

---

## Reminders

### Setting Reminders

```
User: /remind 2026-03-01 배포 완료 검증
```

**Reminder Data** (`state/reminders.json`):
```json
{
  "7910169750": [
    {
      "id": "a1b2c3d4",
      "date": "2026-03-01",
      "message": "배포 완료 검증",
      "created_at": "2026-02-25T14:23:00.123456",
      "notified": false
    }
  ]
}
```

**Behavior:**
- Reminders are scheduled to trigger at **9 AM** on the specified date
- Past dates are rejected
- All reminders are persisted to `state/reminders.json`
- Daily cleanup removes notified reminders (automatic)

---

## Scheduled Jobs

### Built-in Scheduler Jobs

| Job ID | Schedule | Action |
|--------|----------|--------|
| `daily_standup` | 9:00 AM daily | Send "Good morning" + project status |
| `weekly_summary` | Friday 6:00 PM | Send weekly report to all active chats |
| `log_cleanup` | 3:00 AM daily | Delete logs older than 7 days |

**View Active Jobs:**
```python
# In daemon_service.py
if self.scheduler:
    for job in self.scheduler.get_jobs():
        print(f"Job: {job.id} | Next run: {job.next_run_time}")
```

---

## Troubleshooting

### Scheduler Not Running?

**Error:** `APScheduler not available, scheduling disabled`

**Solution:** APScheduler comes with `python-telegram-bot[all]`. Install if missing:
```bash
pip install "apscheduler>=3.10.4"
```

### Command History Log Not Created?

**Cause:** Directory permissions or first run

**Solution:** Check logs directory exists and is writable:
```bash
ls -la D:/Project/daemon/logs/
chmod 700 D:/Project/daemon/logs/  # Unix/WSL
```

### Reminders Not Firing?

**Cause:** Scheduler not started or APScheduler missing

**Check:**
```bash
# In logs, look for:
# "Scheduler initialized and started"
tail -f D:/Project/daemon/logs/sonolbot-daemon.log | grep -i scheduler
```

### Memory/CPU Usage High?

**Cause:** Large log files or too many reminders

**Solution:**
1. Manually clean logs: `rm D:/Project/daemon/logs/*.log`
2. Reduce `LOG_RETENTION_DAYS` to 3 or 5
3. Archive old reminders in `state/reminders.json`

---

## Version History

### v2.0 (2026-02-25) — CURRENT
✅ Added 4 new commands (/remind, /summary, /export, /logs)
✅ APScheduler integration for background jobs
✅ Command audit logging (command_history.log)
✅ Automatic log cleanup (7-day retention)
✅ Daily standup at 9 AM
✅ Weekly summary reports
✅ JSON/CSV data export

### v1.0 (2026-02-23)
- Original 5 core commands
- Basic Telegram integration
- Claude session management

---

## Development

### Adding New Commands

1. **Define constant** in top section:
   ```python
   CMD_MYCMD = "/mycmd"
   ```

2. **Add to help text** in `_send_help()`:
   ```python
   "  /mycmd — Description here",
   ```

3. **Add handler** in `_handle_control_message()`:
   ```python
   if lowered.startswith(CMD_MYCMD):
       arg = lowered.replace(CMD_MYCMD, "", 1).strip()
       self._my_command(chat_id, arg)
       return True
   ```

4. **Implement method** (after `_send_task_list`):
   ```python
   def _my_command(self, chat_id: int, arg: str) -> None:
       """My command implementation."""
       msg = f"Processing: {arg}"
       self._send_text(chat_id, msg)
   ```

5. **Add logging** (optional):
   ```python
   self._log_command(chat_id, CMD_MYCMD, arg)
   ```

### Testing Commands Locally

```bash
# 1. Run daemon
python daemon_service.py

# 2. In another terminal, check logs
tail -f D:/Project/daemon/logs/sonolbot-daemon.log

# 3. Send Telegram message to bot
# @8461725251 or direct chat

# 4. Monitor command log
tail -f D:/Project/daemon/logs/command_history.log
```

---

## Performance Notes

- **Polling interval:** 1 second (configurable)
- **Log retention:** 7 days (configurable)
- **Scheduler threads:** 1 background thread
- **Memory footprint:** ~50-100 MB (baseline)
- **Max reminders per chat:** Unlimited (recommend <1000)

---

## Security

- ✅ All state files: mode 0o600 (read/write owner only)
- ✅ All state dirs: mode 0o700 (rwx owner only)
- ✅ Telegram token: **Must be in `.env` (not committed)**
- ✅ Chat IDs: Whitelist-based access control
- ✅ Exported data: Saved to logs directory (secure path)

---

## Support & Contribution

**Issues?** Check logs first:
```bash
tail -100 D:/Project/daemon/logs/sonolbot-daemon.log
```

**Want to extend?** See Development section above.

**Questions?** Refer to `project_brain.md` for project context.

---

**Built with ❤️ for D:/Project Multi-Agent System**
