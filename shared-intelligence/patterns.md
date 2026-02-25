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
