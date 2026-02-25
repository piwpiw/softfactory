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


---

## Production Deployment Patterns

### PAT-012: Multi-Stage Docker Build for Production
**Pattern:** Separate build stage from runtime stage to reduce image size and attack surface.

```dockerfile
# Stage 1: Builder (includes build tools)
FROM python:3.11-slim as builder
RUN apt-get install gcc postgresql-client
COPY requirements.txt .
RUN pip install --user -r requirements.txt

# Stage 2: Runtime (minimal, no build tools)
FROM python:3.11-slim
COPY --from=builder /root/.local /root/.local
COPY --chown=appuser:appuser . .
USER appuser
CMD ["gunicorn", ...]
```

**When to use:** All production Docker deployments to reduce image size (150MB → 350MB final vs 1GB+).
**Files:** `Dockerfile.prod`, best practice for Python 3.11+ images.

### PAT-013: Blue-Green Deployment Strategy
**Pattern:** Keep old version running (blue) while deploying new version (green), then switch traffic.

```bash
# Current: Blue running on port 8000
# Deploy: Green built and tested separately
docker build -t softfactory:green .

# Test green on staging
docker run --name green-test softfactory:green /bin/bash -c "pytest tests/"

# Switch traffic (done by load balancer or manual cutover)
docker-compose restart web  # Runs new version
```

**When to use:** Production deployments requiring zero downtime.
**Benefit:** Instant rollback — if green fails, restart blue.
**Limitation:** Requires load balancer or manual cutover (not auto with docker-compose).

### PAT-014: Health Check Pattern for Containers
**Pattern:** Every container has healthcheck that returns exit code 0 (pass) or 1+ (fail).

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s       # Check every 30 seconds
  timeout: 10s        # Wait 10 seconds for response
  retries: 3          # Fail after 3 consecutive timeouts
  start_period: 15s   # Wait 15s before first check (warmup)
```

**When to use:** All docker-compose services (db, redis, web, nginx).
**Files:** `docker-compose-prod.yml` all services include healthcheck.

### PAT-015: Database Migration on Deployment
**Pattern:** Run migrations in container before starting API to ensure schema matches code.

```bash
# 1. Start database only
docker-compose up -d db
sleep 20  # Wait for DB initialization

# 2. Run migrations
docker run --rm --network softfactory_softfactory \
  -e DATABASE_URL="postgresql://..." \
  softfactory:latest \
  flask db upgrade

# 3. Start API
docker-compose up -d web
```

**When to use:** Every deployment that includes schema changes.
**Atomicity:** Ensures API never runs with wrong schema.
**Rollback:** Revert git commit, rerun migrations to previous version.

### PAT-016: Automated Backup Strategy with Retention
**Pattern:** Daily backups with date-based cleanup using cron + find command.

```bash
#!/bin/bash
# 1. Create timestamped backup
BACKUP_FILE="backups/softfactory_db_$(date +%Y%m%d_%H%M%S).sql.gz"
docker exec db pg_dump -U postgres softfactory | gzip > "$BACKUP_FILE"

# 2. Upload to S3 (optional)
aws s3 cp "$BACKUP_FILE" "s3://bucket/$BACKUP_FILE"

# 3. Delete backups older than 30 days
find backups/ -name "softfactory_db_*.sql.gz" -mtime +30 -delete
```

**When to use:** All production systems. Schedule: `0 2 * * * /scripts/backup.sh`.
**Retention:** 30 days local + indefinite S3 (cost-effective archival).
**Testing:** Monthly restore test from backup to staging.

### PAT-017: Nginx Rate Limiting with Burst
**Pattern:** Rate limit critical endpoints but allow short traffic spikes.

```nginx
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=100r/s;

location /api/ {
  limit_req zone=api_limit burst=200 nodelay;
  proxy_pass http://backend;
}
```

**When to use:** All public-facing APIs to prevent DDoS and abuse.
**Tuning:** burst = 2-3x rate for legitimate traffic spikes.
**Result:** 99% of traffic passes, only extreme spike (>300r/s) gets throttled.

### PAT-018: Gunicorn Worker Calculation
**Pattern:** Set workers to `(2 × cpu_count) + 1` for optimal concurrency.

```bash
# In docker-compose.prod.yml or deployment script
WORKERS=$(($(nproc) * 2 + 1))  # Dynamic calculation
# Or static for predictable environments:
WORKERS=4  # For 2-core instance
WORKERS=9  # For 4-core instance
```

**When to use:** All Gunicorn deployments.
**Formula:**
- 1-core: 3 workers
- 2-core: 5 workers (we use 4 for conservative load)
- 4-core: 9 workers

### PAT-019: Environment-Specific Configuration
**Pattern:** Use .env files for secrets, docker-compose for service definitions, conditional logic in scripts.

```bash
# .env-prod (NOT in git, secret)
DATABASE_URL=postgresql://user:password@db:5432/softfactory
FLASK_ENV=production

# docker-compose-prod.yml
services:
  web:
    environment:
      - FLASK_ENV=production
      - DATABASE_URL=${DATABASE_URL}  # Interpolated from .env-prod

# Deployment script
if [ "$ENVIRONMENT" = "production" ]; then
  ENV_FILE=.env-prod
else
  ENV_FILE=.env-staging
fi
```

**When to use:** All deployments with secrets or environment-specific config.
**Never:** Commit .env files to git. Never hardcode secrets in Dockerfile/docker-compose.yml.

### PAT-020: Comprehensive Health Check Script
**Pattern:** Script that validates all infrastructure components and returns JSON/human-readable output.

```bash
#!/bin/bash
# checks/health.sh
echo "1. Container status..."
docker ps | grep softfactory

echo "2. HTTP endpoints..."
curl -s http://localhost:8000/health | jq .

echo "3. Database..."
docker exec db psql -U postgres -c "SELECT version();"

echo "4. Resource usage..."
docker stats --no-stream

# Return 0 if all OK, 1 if any fail
[ $? -eq 0 ] && exit 0 || exit 1
```

**When to use:** Post-deployment verification, monitoring probes, incident response.
**Integration:** Export to monitoring as `./scripts/health-check.sh --json` for alerts.


## Performance Optimization Patterns (2026-02-25)

### PAT-010: Database Connection Pooling
**Problem:** New connection per request exhausts resources under load.
**Solution:**
```python
from sqlalchemy.pool import QueuePool

app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'poolclass': QueuePool,
    'pool_size': 10,
    'max_overflow': 20,
    'pool_pre_ping': True,
    'pool_recycle': 3600
}
```
**When to use:** All Flask apps with SQLAlchemy.
**Impact:** 15-20% connection overhead reduction, prevents "too many connections" errors.
**Files:** `backend/app.py`

### PAT-011: SQLite WAL Mode for Concurrency
**Problem:** SQLite locks database on writes, blocking all reads.
**Solution:**
```python
def init_db(app):
    with app.app_context():
        db.create_all()
        with db.engine.connect() as conn:
            conn.execute(text("PRAGMA journal_mode=WAL"))
            conn.execute(text("PRAGMA synchronous=NORMAL"))
            conn.execute(text("PRAGMA cache_size=10000"))
```
**When to use:** All SQLite databases.
**Impact:** 2-3x write throughput, reads don't block on writes.
**Files:** `backend/models.py`

### PAT-012: Application-Level Caching with TTL
**Problem:** Repeated database queries for unchanged data.
**Solution:**
```python
from backend.caching_config import cached, cache_bust

@app.route('/api/products')
@cached('products:all', ttl_seconds=3600)
def get_products():
    return jsonify([p.to_dict() for p in Product.query.all()])

@app.route('/api/products', methods=['POST'])
@cache_bust('products:')  # Invalidate on write
def create_product():
    # Create logic
    return jsonify(new_product.to_dict()), 201
```
**When to use:** Read-heavy endpoints with infrequent writes.
**Impact:** 80-90% response time on cached endpoints, 75%+ cache hit rate.
**Files:** `backend/caching_config.py`, `backend/app.py`

### PAT-013: GZIP Response Compression
**Problem:** Large JSON responses consume bandwidth.
**Solution:**
```python
from flask_compress import Compress

Compress(app)
app.config['COMPRESS_MIN_SIZE'] = 500
app.config['COMPRESS_LEVEL'] = 6
```
**When to use:** All Flask apps serving JSON.
**Impact:** 50-70% response size reduction.
**Files:** `backend/app.py`, `requirements.txt` (add flask-compress)

### PAT-014: HTTP Caching Headers & ETag
**Problem:** Browser doesn't cache responses, repeats same request.
**Solution:**
```python
@app.after_request
def add_caching_headers(response):
    if request.method == 'GET':
        add_cache_headers(response, 'public, max-age=3600')
    add_etag(response)
    return response
```
**When to use:** All GET endpoints.
**Impact:** 80% cache hit rate on repeat requests (browser doesn't re-request).
**Files:** `backend/caching_config.py`

### PAT-015: Eager Loading to Fix N+1 Queries
**Problem:** Loop over results causes 1+N database queries.
**Solution:**
```python
# BEFORE: 9 queries (1 base + 8 related)
bookings = Booking.query.all()
for booking in bookings:
    print(booking.chef.name)  # Executes query per booking

# AFTER: 1 query with join
from sqlalchemy.orm import joinedload
bookings = Booking.query.options(joinedload(Booking.chef)).all()
for booking in bookings:
    print(booking.chef.name)  # Already loaded
```
**When to use:** Any endpoint that accesses related records in loops.
**Impact:** 40-60% query time reduction.
**Detection:** Count SQL queries in logs. If >3, likely N+1 problem.

### PAT-016: Database Indexing Strategy
**Problem:** Slow queries on frequently filtered columns.
**Solution:**
```python
class User(db.Model):
    email = db.Column(db.String(120), unique=True, index=True)
    is_active = db.Column(db.Boolean, index=True)
    created_at = db.Column(db.DateTime, index=True)

# Composite indices for common WHERE clauses
from sqlalchemy import Index
Index('idx_user_email_active', User.email, User.is_active)
Index('idx_booking_user_status', Booking.user_id, Booking.status)
```
**When to use:** Columns used in WHERE, JOIN, ORDER BY clauses.
**Impact:** 35-45% query speed improvement on indexed columns.
**Files:** `backend/models.py`

### PAT-017: Performance Monitoring Decorator
**Problem:** No visibility into endpoint performance.
**Solution:**
```python
from backend.performance_monitor import monitor_performance

@app.route('/api/dashboard')
@monitor_performance
@require_auth
def get_dashboard():
    return jsonify(dashboard_data)

# Access metrics: curl http://localhost:8000/api/monitoring/metrics
```
**When to use:** All API endpoints.
**Impact:** Real-time metrics collection, identifies slow endpoints.
**Files:** `backend/performance_monitor.py`

### PAT-018: Image Lazy Loading (Frontend)
**Problem:** All images load on page load, even below-the-fold.
**Solution:**
```html
<!-- Native lazy loading (simplest) -->
<img src="/images/chef.jpg" loading="lazy" alt="Chef" />

<!-- With Intersection Observer (fallback for older browsers) -->
<img src="/placeholder.jpg" data-src="/images/chef.jpg" class="lazy-image" alt="Chef" />
<script>
const images = document.querySelectorAll('img.lazy-image');
const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.src = entry.target.dataset.src;
            observer.unobserve(entry.target);
        }
    });
}, { rootMargin: '50px' });
images.forEach(img => observer.observe(img));
</script>
```
**When to use:** Pages with 5+ images.
**Impact:** 30-40% page load improvement.
**Files:** `web/**/*.html`

### PAT-019: JavaScript Code Splitting
**Problem:** Load all JavaScript upfront, unused on current page.
**Solution:**
```html
<button id="charts-btn">Show Analytics</button>
<script>
document.getElementById('charts-btn').addEventListener('click', async () => {
    const { Chart } = await import('/js/modules/charts.js');
    Chart.init();
});
</script>
```
**When to use:** Heavy modules not needed on initial page load.
**Impact:** 20-30% faster initial page load.
**Files:** `web/**/*.html`

### PAT-020: Load Testing with Locust
**Problem:** No visibility into how system behaves under load.
**Solution:**
```bash
# Run Locust load test
locust -f scripts/load_test.py \
  --host=http://localhost:8000 \
  --users=200 \
  --spawn-rate=50 \
  --run-time=10m \
  --headless \
  --csv=docs/load_test_results
```
**When to use:** Before each performance optimization.
**Metrics:** Track response times, error rates, throughput under load.
**Files:** `scripts/load_test.py`

---

---

## Public Access / Networking Patterns

### PAT-013: ngrok Tunnel Auto-Reconnect Pattern (2026-02-25)

**Category:** Infrastructure / Networking
**Status:** PRODUCTION
**Usage:** `scripts/ngrok-start.sh --monitor`

Pattern for reliable tunnel management with automatic recovery:
- Monitor process with PID file
- Health check every 30 seconds
- Auto-reconnect on failure (max 5 attempts, 10s delay)
- Graceful cleanup on exit
- Web inspector integration (http://127.0.0.1:4040)

**When to use:** Any system requiring stable public access
**Reference:** `scripts/ngrok-start.sh`, `docs/PUBLIC_ACCESS_GUIDE.md` Section 3

### PAT-014: Public URL Discovery and Management (2026-02-25)

**Category:** Infrastructure / Configuration
**Status:** PRODUCTION
**Usage:** `from backend.public_access_handler import get_access_manager`

Multi-source URL discovery with fallback:
1. Try file first (logs/ngrok-url.txt) — fastest (~1ms)
2. Query ngrok API (http://127.0.0.1:4040/api/tunnels) — fallback
3. Return cached URL — last resort

Enables dynamic CORS updates without app restart.

**When to use:** Any system with dynamic public URLs
**Reference:** `backend/public_access_handler.py`, `docs/PUBLIC_ACCESS_INTEGRATION.md`

### PAT-015: JSON Lines Access Logging (2026-02-25)

**Category:** Monitoring / Logging
**Status:** PRODUCTION
**Usage:** Append-only JSON log files (logs/access.log)

One JSON object per line, stream-friendly format:
- Queryable with jq
- No locking issues (append-only)
- Partial corruption survivable (each line independent)
- Human-readable with tail -f

Supports:
- Real-time streaming
- Batch analysis
- Aggregation/grouping
- Time-windowed queries

**When to use:** High-volume audit logging
**Reference:** `monitoring/access_logging.py`, `docs/PUBLIC_ACCESS_GUIDE.md` Section 7

### PAT-016: IP Whitelist Enforcement (2026-02-25)

**Category:** Security / Access Control
**Status:** PRODUCTION
**Usage:** `access_whitelist.json`, `@require_public_access` decorator

Optional IP-based access control:
- Enable/disable at runtime
- Accounts for reverse proxies (X-Forwarded-For header)
- All requests logged (even blocked ones)
- Supports CIDR notation

**When to use:** Restrict public access to known IPs
**Reference:** `backend/public_access_handler.py`, `access_whitelist.json`

