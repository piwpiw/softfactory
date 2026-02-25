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

### PAT-006: Service-Layer Dummy Data for MVP
```python
# Pattern: Use hardcoded DUMMY_DATA in service layer for fast MVP
# File: backend/services/experience.py

DUMMY_LISTINGS = {
    'site_name': [
        {'title': '...', 'url': '...', 'deadline': '...'},
    ]
}

@experience_bp.route('/listings')
def get_listings():
    site = request.args.get('site')
    if site:
        return jsonify(DUMMY_LISTINGS.get(site, []))
    # ... merge all sites
```

**When to use:** MVP phase when real data source (crawlers) not ready yet.
**Why:** 10-minute MVP delivery requires instant data; service layer decoupled from data source.
**Phase 5:** Replace DUMMY_DATA with `CrawlerClass.crawl()` — API unchanged.
**Files:** `backend/services/experience.py`, `scripts/crawlers/crawler_base.py`

### PAT-007: Abstract Crawler Base Class
```python
# Pattern: All crawlers inherit from ExperienceCrawler ABC
# File: scripts/crawlers/crawler_base.py

class ExperienceCrawler(ABC):
    def __init__(self, site_name):
        self.site_name = site_name
        self.listings = []

    @abstractmethod
    def crawl(self) -> list:
        """Override in subclass with real scraping logic"""
        pass

    def run(self, db=None):
        """Template method: crawl + validate + save + log"""
        self.listings = self.crawl()
        if db:
            self.save_to_db(db)
        return {'success': True, 'count': len(self.listings)}
```

**When to use:** Every new web scraper added (Coupang, Daangn, Soomgo, etc.).
**Why:** Ensures consistent interface, logging, error handling across all crawlers.
**Benefit:** Phase 5 can add real crawlers without changing service layer.
**Files:** `scripts/crawlers/crawler_base.py`, `scripts/crawlers/*_crawler.py`

### PAT-008: Deadline-Based Urgency Indicator (Frontend)
```javascript
// Pattern: Calculate days until deadline, show badge if < 3 days
const daysUntilDeadline = (deadline) => {
    const now = new Date();
    const deadlineDate = new Date(deadline);
    const diff = deadlineDate - now;
    return Math.ceil(diff / (1000 * 60 * 60 * 24));
};

const isUrgent = daysUntilDeadline(listing.deadline) <= 3;

// Render:
${isUrgent ? '<span class="text-red-600 font-bold">긴급</span>' : ''}
```

**When to use:** Any experience/deal listing with expiration dates.
**Why:** Highlights time-sensitive opportunities; improves engagement.
**Files:** `web/experience/index.html`, `web/review/index.html` (etc.)

### PAT-009: Responsive Dark Dashboard (Tailwind)
```html
<!-- Pattern: Dark theme grid dashboard with responsive columns -->
<body class="bg-gray-900 text-gray-100">
    <header class="bg-gradient-to-r from-purple-900 to-indigo-900">
        <h1 class="text-4xl font-bold">Title</h1>
    </header>

    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <!-- Cards auto-arrange: 1 col mobile, 2 col tablet, 3 col desktop -->
        <div class="bg-gray-800 rounded-lg shadow-lg hover:shadow-2xl transition">
            <!-- Card content -->
        </div>
    </div>
</body>
```

**When to use:** Any data-heavy dashboard (listings, campaigns, analytics).
**Why:** Dark mode reduces eye strain; responsive grid auto-adapts devices.
**CDN:** `<script src="https://cdn.tailwindcss.com"></script>` (no build needed).
**Files:** `web/experience/index.html`, `web/platform/*`

### PAT-010: Multi-Level Filter UI
```javascript
// Pattern: Site filter + Category filter + Action buttons
<div class="mb-6">
    <h2 class="text-sm font-semibold mb-3">Site Filter</h2>
    <div class="flex flex-wrap gap-2">
        <button onclick="filterBySite('all')">All</button>
        <button onclick="filterBySite('site1')">Site 1</button>
        <!-- ... -->
    </div>
</div>

<div class="mb-6">
    <h2 class="text-sm font-semibold mb-3">Category Filter</h2>
    <div id="categoryFilter"></div>
</div>

<script>
let currentSiteFilter = 'all';
let currentCategoryFilter = 'all';

function filterBySite(site) {
    currentSiteFilter = site;
    loadData();
}

function filterByCategory(cat) {
    currentCategoryFilter = cat;
    loadData();
}
</script>
```

**When to use:** Multi-dimensional filtering (site, category, status, etc.).
**Why:** Reduces API load; client-side filtering is instant.
**Advanced:** Can combine filters: `?site=${site}&category=${cat}`.
**Files:** `web/experience/index.html`

---

## Agent Collaboration Patterns

### PAT-007: Agent Communication via Consultation Bus

```python
# Pattern: All inter-agent communication goes through async message bus
# File: core/consultation_bus.py

from core.consultation_bus import get_bus, MessageType, MessagePriority

bus = get_bus()

# Agent A asks Agent B a question
msg_id = bus.request(
    from_agent="dev-lead-1",
    to_agent="qa-engineer-2",
    subject="Code ready for testing?",
    payload={"modules": ["auth", "api"]}
)

# Agent B responds
bus.reply(
    to_message_id=msg_id,
    from_agent="qa-engineer-2",
    payload={"ready": True, "test_count": 47},
    is_decision=False
)

# Agent C escalates to orchestrator
bus.ask_question(
    from_agent="backend-dev-1",
    subject="Token budget exceeded?",
    payload={"used": 28000, "budget": 25000},
    requires_decision=True
)
```

**When to use:** Any agent-to-agent communication, questions, alerts
**Why:** Decouples agents, enables async execution, audit trail maintained
**Files:** core/consultation_bus.py, core/agent_spawner.py, core/mission_manager.py
**Trade-off:** Message overhead ~50-100 tokens per communication (acceptable for coordination)

### PAT-008: Dynamic Agent Spawning with Authority Matrix

```python
# Pattern: Orchestrator spawns agents with defined authority boundaries
# File: core/agent_spawner.py

from core.agent_spawner import get_spawner, AgentRole, AgentCapability, AgentAuthority

spawner = get_spawner()

# Spawn backend dev with limited authority
dev = spawner.spawn(
    role=AgentRole.DEVELOPER,
    capabilities=[...],
    token_budget=10000,
    parent_id="orchestrator-1"
)

# Spawn sub-agent (if needed)
specialist = spawner.spawn(
    role=AgentRole.SPECIALIST,
    capabilities=[...],
    parent_id=dev.id,  # Dev can now spawn this
    token_budget=2000
)

# Check authority
if dev.authority.can_spawn_agents:
    # Can create sub-agents
    pass

# Enforce authority
if "delete_database" in dev.authority.forbidden_actions:
    # Prevent this action
    pass
```

**When to use:** Project startup, workload scaling, dynamic team formation
**Why:** Agents are first-class resources (like team members), authority prevents mistakes
**Files:** core/agent_spawner.py, orchestrator/agent-registry.md
**Limit:** Max 20 concurrent agents (depends on token budget)

### PAT-009: Mission Dependency Graph for Parallelization

```python
# Pattern: Auto-detect parallel groups via dependency resolution
# File: core/mission_manager.py

from core.mission_manager import get_mission_manager, MissionPhase

manager = get_mission_manager()

# Create missions
m1 = manager.create_mission("Research", MissionPhase.RESEARCH, agent_id="analyst-1")
m2 = manager.create_mission("Planning", MissionPhase.PLANNING, agent_id="strategist-1")
m3 = manager.create_mission("Design", MissionPhase.DESIGN, agent_id="architect-1")

# Define dependencies
manager.add_dependency(m2.id, m1.id)  # Planning blocks on Research
manager.add_dependency(m3.id, m2.id)  # Design blocks on Planning

# Get parallelizable groups
groups = manager.get_parallelizable_missions()
# Result: [[m1], [m2], [m3]] — sequential
# But if m2 & m3 had no dependency: [[m1], [m2, m3]] — parallel

# Check readiness
if manager.check_ready(m3.id):
    # All dependencies met, assign to agent
    pass
```

**When to use:** Multi-phase projects (Research→Plan→Code→Test)
**Why:** Eliminates manual sequencing, auto-parallelizes safe tasks
**Files:** core/mission_manager.py, orchestrator/orchestration-engine.md
**Benefit:** 50-70% time savings through parallelization

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

## PAT-010: Query Optimization Patterns (2026-02-25)

### Pattern: Aggregate with JOIN
**Use:** Count related records without N+1
```python
from sqlalchemy import func
from sqlalchemy.orm import joinedload

# Get items with related counts in single query
items = db.session.query(
    Item,
    func.count(RelatedItem.id).label('count')
).outerjoin(RelatedItem,
           Item.id == RelatedItem.item_id)\
.group_by(Item.id)\
.all()

for item, count in items:
    # Use count directly, no additional queries
```

### Pattern: Eager Load Relationships
**Use:** Prevent N+1 when accessing relationships
```python
# Instead of: for item in items: print(item.related.name)  [N+1]
# Use:
items = Item.query.options(joinedload(Item.related)).all()
for item in items:
    print(item.related.name)  # No new query
```

### Pattern: Batch Counts
**Use:** Multiple COUNT queries in one request
```python
# Instead of: [User.query.count(), Post.query.count(), ...]  [6 queries]
# Use:
stats = db.session.query(
    func.count(User.id),
    func.count(Post.id),
    func.count(Comment.id),
).first()
```

### Pattern: Partial Indexes
**Use:** Index only active records (PostgreSQL)
```sql
CREATE INDEX idx_posts_active
ON posts(created_at DESC)
WHERE status IN ('draft', 'published');
```

### Performance Impact
- N+1 fix: 40-80% faster
- Eager load: 5-10x faster
- Batch counts: 83% faster (6→1 query)
- Indexes: 20-50% faster

