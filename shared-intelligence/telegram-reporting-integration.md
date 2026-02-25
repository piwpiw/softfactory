# Telegram Auto-Reporting Integration Plan
> **Objective**: All project progress → Telegram summaries (auto-daily + on-demand)
> **User**: Sonolbot (daemon) reads token-tracker.json + generates reports
> **Status**: READY FOR INTEGRATION

---

## 📱 Telegram Commands (Coming Soon)

### **New Commands for Sonolbot**

```
/report summary     — Executive summary (5 min update)
/report detailed    — Full project breakdown
/report alerts      — Critical alerts & recommendations
/report recovery    — Token optimization plan
/report optimizations — Opportunities list
/report all         — All reports stacked

/schedule-daily     — Auto-report every day at 9 AM KST
/schedule-weekly    — Weekly digest (Friday 6 PM KST)
```

---

## 🔄 Implementation Steps

### **Step 1: Modify daemon_service.py** (5 min)

Add to command handlers:

```python
from scripts.project_reporter import ProjectReporter

CMD_REPORT = "/report"

async def handle_report_command(report_type: str):
    """Generate and send project report"""
    reporter = ProjectReporter()

    if report_type == "all":
        for rtype in ["summary", "detailed", "alerts", "recovery"]:
            text = reporter.format_for_telegram(rtype)
            await send_telegram_message(chat_id, text)
            await asyncio.sleep(0.5)  # Rate limiting
    else:
        text = reporter.format_for_telegram(report_type)
        await send_telegram_message(chat_id, text)
```

### **Step 2: Add Auto-Scheduling** (APScheduler)

```python
from apscheduler.schedulers.background import BackgroundScheduler

def schedule_daily_report():
    """Schedule 9 AM daily report"""
    if HAS_APSCHEDULER:
        scheduler = BackgroundScheduler()
        scheduler.add_job(
            send_daily_report,
            'cron',
            hour=9, minute=0,
            timezone='Asia/Seoul'
        )
        scheduler.start()

async def send_daily_report():
    """Sent at 9:00 AM daily"""
    reporter = ProjectReporter()
    text = reporter.format_for_telegram("summary")
    await send_telegram_message(ALLOWED_CHAT_ID, text)
```

### **Step 3: Wire Up Handler**

In message handler, detect `/report` command:

```python
if message.text.startswith("/report"):
    parts = message.text.split()
    report_type = parts[1] if len(parts) > 1 else "summary"
    await handle_report_command(report_type)
```

---

## 📊 Current Dashboard

Once integrated, Sonolbot will send:

```
📊 PROJECT STATUS SUMMARY
========================================

Budget Status: 113.5% (OVER)
Total Used: 227,000 tokens
Remaining: -27,000 tokens
Session Status: ⚠️ OVER BUDGET

PROJECT BREAKDOWN:
----------------------------------------
✓ M-001 Infrastructure
  Status: COMPLETED
  Efficiency: 110% (ACCEPTABLE)
  Tokens: 33,000/30,000

✓ M-002 CooCook MVP
  Status: COMPLETED (Phase 3 QA approved!)
  Efficiency: 68% (EXCELLENT)
  Tokens: 44,000/65,000

● M-006 체험단 MVP
  Status: IN_PROGRESS (Phase 2)
  Efficiency: 40% used (60% remaining)
  Tokens: 26,000/65,000

[More projects...]
```

---

## 🎯 Automated Reports Timeline

```
DAILY (9:00 AM KST):
├─ Project summary
├─ Budget status
├─ Critical alerts (if any)
└─ Top optimization opportunity

WEEKLY (Friday 6:00 PM KST):
├─ Full project breakdown
├─ Token analysis
├─ Performance metrics
└─ Next week forecast

ON-DEMAND (/report command):
├─ Real-time status
├─ Any requested format
├─ Historical comparison (if tracking enabled)
```

---

## 🔌 Integration Checklist

- [ ] Add `/report` command to daemon_service.py
- [ ] Test with `/report summary`
- [ ] Add APScheduler daily job (9 AM)
- [ ] Test daily auto-report
- [ ] Add `/report detailed` endpoint
- [ ] Verify token-tracker.json parsing
- [ ] Format HTML properly for Telegram
- [ ] Set up error handling (file not found, invalid JSON)
- [ ] Test all 5 report types
- [ ] Deploy to Sonolbot

---

## 💾 Data Sources

**Real-time sources:**
1. `shared-intelligence/token-tracker.json` — Live token/budget data
2. `shared-intelligence/cost-log.md` — Historical costs
3. `shared-intelligence/decisions.md` — ADR history
4. `shared-intelligence/patterns.md` — Pattern library status

**Computation:**
- Efficiency calculation: tokens_actual / tokens_budgeted
- ROI calculation: lines_of_code / tokens_used
- Burn rate: tokens_per_minute
- Forecast: (remaining_budget / burn_rate) = eta_hours

---

## 🎨 Telegram Message Format

**Summary Report Example:**

```
Generated: 2026-02-25 13:45:00

📊 PROJECT STATUS SUMMARY
========================================

Budget Status: 108.5% (over by 17K)
Total Used: 217,000 tokens
Remaining: -17,000 tokens
Session Status: ⚠️ RECOVER

PROJECT BREAKDOWN:
---
✓ M-001 Infrastructure [COMPLETE]
  ✓ Efficiency: 110%
  ✓ Tokens: 33K/30K

✓ M-002 CooCook [COMPLETE - QA SIGNED OFF!]
  ✓ Efficiency: 68%
  ✓ Tokens: 44K/65K

✓ M-004 JARVIS [COMPLETE]
  ✓ Efficiency: 89%
  ✓ Tokens: 40K/45K

● M-006 체험단 [IN_PROGRESS]
  ● Efficiency: 40% used
  ● Tokens: 26K/65K (60% remaining)
  ● ETA: ~90 min to completion

Next: Monitor Phase 2 compression
```

---

## 🚀 Example Telegram Interaction

```
You: /report summary

Bot:
📊 PROJECT STATUS SUMMARY
[sends summary as above]

You: /report alerts

Bot:
⚠️ ALERTS & RECOMMENDATIONS
========================================

🔴 CRITICAL
Session OVER BUDGET by 27,000 tokens
→ Implement aggressive optimization for M-006

🟡 WARNING
M-006 Phase 2 burn rate elevated (295 tokens/min)
→ Continue template-based development

🟢 INFO
M-002 QA phase consuming only 77% of budget
→ Can proceed to Phase 4 with confidence
```

---

## 🔐 Security & Privacy

- ✅ Reports only show aggregated metrics (no sensitive code)
- ✅ Token counts are visible (internal use only)
- ✅ No user data exposed
- ✅ No API keys in reports
- ✅ Telegram bot token secured in env

---

## 🎯 Success Criteria

Once implemented:
- [ ] `/report` command responds within 2 seconds
- [ ] Daily report sent at 9:00 AM reliably
- [ ] All 5 report types working
- [ ] HTML formatting correct in Telegram
- [ ] No errors when tracker.json updated
- [ ] User receives up-to-date project info 24/7

---

**Next Action:** Run `/report summary` and share Sonolbot's response ✅
