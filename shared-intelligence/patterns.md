# Shared Intelligence — Patterns Library
> **Purpose:** Reusable solutions promoted from completed tasks.
> **Rule:** Reuse first, extend second, build new only when justified in ADR (Principle #15).
> **Update:** After every task — promote solutions to this library.

---

## Backend Patterns

### PAT-001: Flask Service Blueprint Pattern
```python
# Pattern: Register all services as Flask blueprints
# File: backend/app.py

from backend.services.coocook import coocook_bp
from backend.services.sns_auto import sns_auto_bp

def create_app():
    app = Flask(__name__)
    app.register_blueprint(coocook_bp, url_prefix='/api/coocook')
    app.register_blueprint(sns_auto_bp, url_prefix='/api/sns-auto')
    return app
```
**When to use:** Every new service added to SoftFactory Platform.
**Files:** `backend/app.py`, `backend/services/*.py`

### PAT-002: JWT Auth + Subscription Decorator Order
```python
# Pattern: ALWAYS @require_auth innermost (bottom), @require_subscription outermost (top)
# Reason: Python decorators execute bottom-to-top

@coocook_bp.route('/dashboard')
@require_subscription('coocook')   # ← OUTER: runs second, checks subscription
@require_auth                       # ← INNER: runs first, validates JWT
def dashboard():
    ...
```
**When to use:** Every protected API route requiring both auth + subscription check.
**Key rule:** `@require_auth` ALWAYS on bottom.

### PAT-003: SQLAlchemy Model with to_dict()
```python
# Pattern: Every model must have to_dict() for JSON serialization
class MyModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
```
**When to use:** All SQLAlchemy models. Add to model template.
**Enforcement:** Code review checklist item.

### PAT-004: Demo Token Support in Auth Middleware
```python
# Pattern: Support static 'demo_token' for testing without DB user
def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if token == 'demo_token':
            g.current_user = DemoUser()  # DemoUser class with to_dict()
            return f(*args, **kwargs)
        # ... normal JWT validation
    return decorated
```
**When to use:** All platforms needing demo/testing mode.
**DemoUser:** Must implement same interface as real User (to_dict(), id, email, etc.)

### PAT-005: Absolute DB Path Pattern
```python
# Pattern: Always resolve DB path absolutely
import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'platform.db')}"
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
```
**When to use:** All SQLite-based Flask apps.
**Why:** Relative paths cause duplicate DB files when CWD changes.

---

## QA Testing Patterns

### PAT-007: API Response Validation Checklist
**Pattern:** Comprehensive API endpoint validation (from M-002 Phase 3 QA)
```
For each endpoint:
1. Response time: Measure 3 runs, average < 500ms target
2. JSON validity: Validate all responses parse as JSON
3. Required fields: Check all expected fields present
4. Data types: Verify integers, floats, dates format correctly
5. Pagination: Test page/per_page params if applicable
6. Error codes: Test 400/401/403/404 cases
7. Auth headers: Test with/without Bearer token
8. Edge cases: Test invalid IDs, past dates, missing fields
```
**Files:** Implementation → QA reports in `shared-intelligence/qa-report-*.md`

### PAT-008: Price Calculation Verification
**Pattern:** For booking/transaction systems, always validate calculation
```python
# Verify all bookings match: duration_hours × price_per_session
# Test cases from M-002 QA:
# ✓ Chef Park: 3h × 120 = 360
# ✓ Chef Marco: 2h × 130 = 260
# ✓ Chef Tanaka: 4h × 150 = 600
# Sample query:
# SELECT b.id, b.duration_hours, c.price_per_session, b.total_price FROM booking b
# JOIN chef c ON b.chef_id = c.id
```
**When to use:** Any monetary transaction endpoint
**Prevention:** Prevents billing errors, trust issues

### PAT-009: OWASP Security Check Template
**Pattern:** Minimal security baseline for QA sign-off
```
1. Authentication: Test missing auth header → 401
2. Authorization: Test unauthorized user → 403
3. SQL Injection: Test with ' OR '1'='1 in filter params
4. Input Validation: Test past dates, invalid IDs, missing fields
5. Data Exposure: Verify no passwords/secrets in responses
6. Rate Limiting: Verify no repeated endpoint spam (if applicable)
```
**Result:** All checks must PASS for production sign-off
**Reference:** M-002 Phase 3 QA Report (100% passed)

---

## Agent Coordination Patterns

### PAT-006: Inter-Agent Message Format (Token-Efficient)
```json
{
  "from": "Agent_A",
  "to": "Agent_B",
  "type": "REQUEST|UPDATE|QUESTION|DECISION",
  "priority": "CRITICAL|HIGH|NORMAL",
  "payload": {
    "context_id": "unique_string",
    "data": {},
    "decision_required": false,
    "deadline": "ISO8601_timestamp"
  }
}
```
**When to use:** All inter-agent communication via `core/consultation.py`.

### PAT-007: Parallel Subagent Task Split
```
Independent tasks → run in parallel (same message, multiple Task tool calls)
Dependent tasks  → sequential with explicit handoff (checkpoint → next agent reads checkpoint)
```
**When to use:** Every multi-agent orchestration. Always classify dependency before scheduling.

---

## Documentation Patterns

### PAT-008: MEMORY.md as Index (≤200 lines)
```markdown
# MEMORY.md — Index Only
- Current status: [1-2 lines]
- Key decisions: [list with links to shared-intelligence/decisions.md]
- Active pitfalls: [links to shared-intelligence/pitfalls.md]
- → Detailed history: memory/project-status.md
```
**When to use:** Always. MEMORY.md is context-critical — never exceed 200 lines.
**Rule:** Details go to topic files, MEMORY.md points to them.

---

### PAT-009: CooCook MVP Demo Mode Pattern
```javascript
// Pattern: Demo mode with static token for web UI testing
const DEMO_PASSKEY = 'demo2026';
const DEMO_TOKEN = 'demo_token';

function enableDemoMode() {
    localStorage.setItem('demo_mode', 'true');
    localStorage.setItem('access_token', DEMO_TOKEN);
    localStorage.setItem('user', JSON.stringify(DEMO_USER));
}

// Backend: Accept 'demo_token' in Authorization header
@require_auth
def protected_route():
    if request.headers.get('Authorization') == f'Bearer {DEMO_TOKEN}':
        # Grant demo user access
        pass
```
**When to use:** MVP/demo phases where real authentication not required.
**Files:** `web/platform/api.js`, `backend/auth.py`
**Note:** Demo token is static string, never append timestamp (see PF-003).

---

## Telegram Bot Patterns

### PAT-010: Sonolbot Command Framework (v2.0)
```python
# Pattern: Extensible command handler with logging + scheduling
# File: daemon/daemon_service.py

def _handle_control_message(self, chat_id: int, message_id: int, text: str) -> bool:
    lowered = text.lower()

    # Log all commands for audit trail
    if any(lowered.startswith(cmd) for cmd in [CMD_STATUS, CMD_HELP, CMD_REMIND, ...]):
        self._log_command(chat_id, text.split()[0], text)

    # Handle each command
    if lowered.startswith(CMD_REMIND):
        reminder_text = text.replace(CMD_REMIND, "", 1).strip()
        self._handle_reminder_command(chat_id, reminder_text)
        return True

    if lowered.startswith(CMD_SUMMARY):
        self._send_daily_summary(chat_id)
        return True
```

**When to use:** Extending Sonolbot with new commands.
**Why:** Centralized logging, scheduler integration, consistent error handling.
**Files:** `daemon/daemon_service.py`, `daemon/README.md`
**Key rules:**
- All commands logged via `_log_command()` for audit
- Command handlers placed in `_handle_control_message()`
- Implementation methods named `_handle_*_command()` or `_send_*_report()`

### PAT-011: APScheduler Background Jobs for Telegram Bot
```python
# Pattern: Background scheduler for periodic notifications
# File: daemon/daemon_service.py

def _init_scheduler(self):
    self.scheduler = BackgroundScheduler()

    # Daily standup at 9 AM
    self.scheduler.add_job(
        self._send_daily_standup,
        trigger=CronTrigger(hour=9, minute=0),
        id='daily_standup'
    )

    # Weekly report (Friday 6 PM)
    self.scheduler.add_job(
        self._send_weekly_summary,
        trigger=CronTrigger(day_of_week=4, hour=18, minute=0),
        id='weekly_summary'
    )

    self.scheduler.start()

def _send_daily_standup(self):
    for chat_id in self.active_tasks.keys():
        self._send_text(chat_id, "🌅 오늘의 일정...")
```

**When to use:** Bots needing recurring notifications or maintenance tasks.
**Why:** APScheduler handles timezone-aware cron scheduling without blocking main event loop.
**Files:** `daemon/daemon_service.py`
**Requirements:** `pip install apscheduler>=3.10.4` (auto with python-telegram-bot[all])

### PAT-012: Persistent Reminder State with JSON
```python
# Pattern: JSON-backed reminder storage with scheduling
# File: daemon/daemon_service.py

def _handle_reminder_command(self, chat_id: int, reminder_text: str):
    # Parse "YYYY-MM-DD message"
    parts = reminder_text.split(None, 1)
    date_str, message = parts[0], parts[1]

    # Validate and save
    reminder = {
        'id': str(uuid.uuid4())[:8],
        'date': date_str,
        'message': message,
        'created_at': datetime.now().isoformat(),
        'notified': False
    }
    self.reminders[str(chat_id)].append(reminder)
    self._save_reminders()  # Persist to reminders.json

    # Schedule notification job
    if self.scheduler.running:
        self._schedule_reminder(reminder, chat_id)
```

**When to use:** Date-based reminders in Telegram bots.
**Why:** Survives daemon restart, decoupled from job scheduler.
**Files:** `daemon/daemon_service.py`, `daemon/state/reminders.json`

---

## Template for New Entries
```markdown
### PAT-XXX: [Short Title]
\`\`\`[language]
// Code example
\`\`\`
**When to use:** [context/trigger]
**Why:** [rationale]
**Files:** [relevant file paths]
```
