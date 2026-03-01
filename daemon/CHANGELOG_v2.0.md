# 📝 Sonolbot v2.0 Changelog

> **Purpose**: **Released:** 2026-02-25
> **Status**: 🟢 ACTIVE (관리 중)
> **Impact**: [Engineering / Operations]

---

## ⚡ Executive Summary (핵심 요약)
- **주요 내용**: 본 문서는 Sonolbot v2.0 Changelog 관련 핵심 명세 및 관리 포인트를 포함합니다.
- **상태**: 현재 최신화 완료 및 검토 됨.
- **연관 문서**: [Master Index](./NOTION_MASTER_INDEX.md)

---

**Released:** 2026-02-25
**Upgrade Path:** v1.0 → v2.0 (backward compatible)

---

## What's New

### New Commands (4)

#### `/remind [date] [message]`
Schedule date-based reminders that trigger at 9 AM on specified date.

**Usage:**
```
/remind 2026-03-01 배포 완료 검증
/remind 2026-02-28 CooCook API review
```

**Features:**
- Past dates rejected
- Reminders persist in `state/reminders.json`
- Scheduled via APScheduler
- Survives daemon restart

---

#### `/summary`
Get daily activity summary report.

**Output includes:**
- Total active TASK count
- Current chat TASK count
- Messages in queue
- Daemon status

---

#### `/export [json|csv]`
Export task and command data in specified format.

**Usage:**
```
/export json  # → sonolbot_export_20260225_143000.json
/export csv   # → sonolbot_export_20260225_143000.csv
```

**Export contents:**
- Task list (max 50)
- Queue status
- Metadata (timestamps, counts)

---

#### `/logs [lines]`
View recent command history (default: 20 lines).

**Usage:**
```
/logs         # Last 20 commands
/logs 50      # Last 50 commands
```

**Sample output:**
```
[2026-02-25 14:20:15] chat_id=7910169750 cmd=/task-new text=Fix login bug
[2026-02-25 14:15:42] chat_id=7910169750 cmd=/s text=/s
[2026-02-25 14:10:00] chat_id=7910169750 cmd=/remind text=/remind 2026-02-28 배포
```

---

## Background Jobs (Scheduler)

### Daily Standup (9 AM)
Automatically sends "Good morning" status to all active chats.

**Message includes:**
- Date/time
- Current projects
- Daemon status

---

### Weekly Summary (Friday 6 PM)
Triggers full summary report to all active chats.

---

### Log Cleanup (3 AM)
Automatically removes logs older than 7 days (configurable).

---

## Enhanced Logging

### Command Audit Trail
**File:** `logs/command_history.log`

Every command is logged with:
- ISO timestamp
- User chat_id
- Command name
- Full command text (truncated at 100 chars)

**Example:**
```
[2026-02-25 14:20:15] chat_id=7910169750 cmd=/task-new text=Fix login page bug in SoftFactory
[2026-02-25 14:15:42] chat_id=7910169750 cmd=/s text=/s
```

**Retention:** Automatic cleanup (7 days by default, configurable via `LOG_RETENTION_DAYS`)

---

## Architecture Changes

### New Files
- `daemon/README.md` — Comprehensive usage guide
- `state/reminders.json` — Persistent reminder storage (auto-created)
- `logs/command_history.log` — Audit trail (auto-created)

### Modified Files
- `daemon/daemon_service.py` — Core enhancement (+1200 lines)
  - APScheduler integration
  - 4 new command handlers
  - 13 new methods
  - Graceful scheduler shutdown

### Documentation Updates
- `shared-intelligence/patterns.md` — Added PAT-010, PAT-011, PAT-012
- `shared-intelligence/pitfalls.md` — Added PF-007, PF-008
- `shared-intelligence/decisions.md` — Added ADR-0007

---

## Breaking Changes

**None.** v2.0 is fully backward compatible with v1.0.

All existing commands work exactly as before:
- `/task-new`, `/task-list`, `/task-activate` — unchanged
- `/s` (status) — unchanged  
- `/h` (help) — updated to show new commands

---

## Migration Guide

### For Existing Users
No migration needed. Simply start the updated daemon.

```bash
pythonw.exe daemon_control_panel.py
```

New directories will be created automatically:
- `daemon/logs/command_history.log`
- `daemon/state/reminders.json`

### For Developers
Review the new patterns and pitfalls in shared-intelligence:

```
shared-intelligence/patterns.md
  ├─ PAT-010: Sonolbot Command Framework
  ├─ PAT-011: APScheduler Background Jobs
  └─ PAT-012: Persistent Reminder State

shared-intelligence/pitfalls.md
  ├─ PF-007: Missing Scheduler Shutdown
  └─ PF-008: Command Logging Directory Validation
```

---

## Performance Impact

- **Memory:** +30-50 MB (scheduler + reminders dict)
- **CPU:** Minimal (APScheduler runs in background thread)
- **Disk:** ~100 KB per 1000 command entries (logs auto-cleanup)

---

## Known Issues

None. Tested and validated.

---

## Dependencies

All dependencies were already in `python-telegram-bot[all]`:
- ✅ `apscheduler >= 3.10.4` (already available)
- ✅ `python-telegram-bot >= 22.6` (already available)

No new dependencies to install.

---

## Rollback

To rollback to v1.0, restore the previous `daemon_service.py` file. New command will not work, but old commands are unaffected.

---

## Support

See `daemon/README.md` for:
- Detailed usage guide
- Troubleshooting section
- Development guide
- Configuration options

---

**Version:** 2.0
**Release Date:** 2026-02-25
**Status:** Production Ready
**Tested:** ✅ Yes
**Documented:** ✅ Yes