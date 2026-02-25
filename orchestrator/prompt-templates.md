# Prompt Templates — Standard, Reusable, No Repetition
> **Philosophy**: Write once, use forever. Every phase has a fixed prompt.
> **Goal**: Zero repetitive long prompts. 1 issue = prevention in all future projects.
> **Status**: ACTIVE

---

## 🎯 **Core Principle: "Prompt is Data, Not Text"**

```
❌ OLD (Wasteful):
  Project 1: Long prompt → Execution
  Project 2: Long prompt again → Execution (repetition!)
  Project 3: Long prompt again → Execution (repetition!)
  = 3x token waste, 3x time waste

✅ NEW (Efficient):
  Template: Phase -1 RESEARCH PROMPT (write once)
  Project 1: Use template + inject {project_name, tech_stack}
  Project 2: Use template + inject {project_name, tech_stack}
  Project 3: Use template + inject {project_name, tech_stack}
  = 1 template, 3 projects, zero repetition
```

---

## 📋 **Phase -1: RESEARCH PROMPT (Template)**

```markdown
# TEMPLATE: Phase -1 RESEARCH

## Input Parameters
- {PROJECT_NAME}: string
- {TECH_STACK}: string (comma-separated)
- {USE_CASE}: string (what problem does it solve?)
- {SCALE}: string (small/medium/large)

## Fixed Prompt

You are a research agent. Conduct comprehensive research for {PROJECT_NAME}.

### Task 1: Market Research
Search for:
- Competing solutions in {USE_CASE} space
- Open-source libraries/frameworks for {TECH_STACK}
- Common pitfalls in {USE_CASE} implementations
- Industry standards for {TECH_STACK}

Output: `research/market-analysis.md`
Format: [Link | Key finding | Recommendation]

### Task 2: Architecture Research
Analyze:
- Existing codebase patterns (D:\Project\backend, D:\Project\web)
- Similar {TECH_STACK} implementations in the project
- Reusable architectural patterns
- Tech debt vs clean slate decision

Output: `research/architecture-baseline.md`
Format: [Pattern | Where used | Applicability]

### Task 3: Security Research
Check:
- Known vulnerabilities in {TECH_STACK}
- OWASP Top 10 risks for {USE_CASE}
- Authentication/authorization best practices
- Data security concerns

Output: `research/security-baseline.md`
Format: [Risk | Impact | Mitigation]

---

## Execution Notes
- Use shared-intelligence/patterns.md as reference
- Link to existing solutions if found
- Keep research output MINIMAL (80/20 rule)
- No speculation, only facts from docs/code/github
```

### **How to Use:**

```python
# Pseudo-code (how orchestrator uses this)

template = load_template("phase-1-research.md")

context = {
    "PROJECT_NAME": "Real-time Chat",
    "TECH_STACK": "WebSocket, Redis, FastAPI",
    "USE_CASE": "instant messaging",
    "SCALE": "medium"
}

prompt = template.format(**context)

# Result: Concrete prompt with specific project details
# No need to write 500 words every time!

agent = spawn_agent("market_analyst")
result = agent.execute(prompt)
```

---

## 📊 **All Phase Templates (Fixed Structure)**

### **Phase 0: PLANNING PROMPT**

```markdown
# TEMPLATE: Phase 0 PLANNING

## Inputs
- {PROJECT_NAME}
- {REQUIREMENTS}: string
- {RESEARCH_LINK}: link to Phase -1 results

## Fixed Prompt

Based on research at {RESEARCH_LINK}:

### Task 1: Business Planning
Create PRD addressing:
- Customer problems (from research)
- Features (MVP scope)
- Success metrics
- Constraints/assumptions

Output: `planning/prd.md`

### Task 2: Technical Planning
Create tech strategy for {TECH_STACK}:
- Architecture (why this pattern?)
- Tech choices (why these libraries?)
- Dependency analysis
- Risk assessment

Output: `planning/tech-strategy.md`

### Task 3: Feasibility Review
Assess from implementation perspective:
- Can we build this in {TIMELINE}?
- Resource needs
- Potential blockers
- Effort estimates per component

Output: `planning/implementation-feasibility.md`

---

## Execution Notes
- Reference Phase -1 findings
- Mark any contradictions with research
- Provide alternatives if scope too large
```

### **Phase 1: REQUIREMENT PROMPT**

```markdown
# TEMPLATE: Phase 1 REQUIREMENT

## Inputs
- {PROJECT_NAME}
- {PLANNING_LINK}: link to Phase 0 results
- {EXISTING_APIs}: optional (if extending)

## Fixed Prompt

Based on planning at {PLANNING_LINK}:

### Task 1: User Stories
Create 5-10 user stories from features:
- As [role], I want [action], so that [benefit]
- Acceptance criteria (testable)
- Dependencies marked

Output: `requirement/user-stories.md`

### Task 2: API Specification
Define APIs from user stories:
- Endpoints (REST/GraphQL)
- Request/response schemas
- Error codes
- Example payloads

Output: `requirement/api-spec.json`

### Task 3: QA Considerations
From user stories, define:
- Test scenarios per story
- Edge cases
- Security checks needed
- Performance requirements

Output: `requirement/qa-considerations.md`

---

## Execution Notes
- Each user story → at least 1 API endpoint
- Reference Phase 0 tech strategy for choices
- Flag any impossibilities
```

### **Phase 2: DOCUMENTATION PROMPT**

```markdown
# TEMPLATE: Phase 2 DOCUMENTATION

## Inputs
- {PROJECT_NAME}
- {PHASE_1_LINK}: link to requirements
- {ARCH_PATTERN}: (from Phase 0)

## Fixed Prompt

Create complete design documentation:

### Task 1: Architecture Document
Document (with diagrams):
- System components
- Data flow
- Integration points
- Deployment model

Output: `documentation/DESIGN.md`

### Task 2: API Documentation
Detailed specs:
- Each endpoint (request → response → error)
- Data models (with relationships)
- Authentication flow
- Rate limiting

Output: `documentation/API.md`

### Task 3: Database Design
Schema definition:
- Tables/collections
- Relationships
- Indexes
- Migration strategy

Output: `documentation/DATABASE.md`

### Task 4: Security & Configuration
Security implementation:
- Authentication mechanism
- Authorization rules
- Secret management
- Configuration defaults

Output: `documentation/SECURITY.md`

---

## Execution Notes
- Everything in Phase 1 must be documentable here
- If can't document it, design is incomplete
- Use text-based diagrams (ASCII or Mermaid)
- Flag any mismatches with Phase 1
```

### **Phase 3: DESIGN PROMPT**

```markdown
# TEMPLATE: Phase 3 DESIGN

## Inputs
- {PROJECT_NAME}
- {DOCUMENTATION_LINK}: link to Phase 2 docs

## Fixed Prompt

Validate and detail design:

### Task 1: Code Structure
Define structure (without implementation):
- Directory layout
- Module organization
- Class/function signatures (empty bodies)
- Dependency injection points

Output: `design/code-structure.py`

### Task 2: Database Migrations
Plan migrations:
- Initial schema creation
- Future schema changes
- Rollback strategy
- Data migration scripts

Output: `design/migrations.sql`

### Task 3: Security Review
Pre-implementation security check:
- Authentication flow (correct?)
- Authorization rules (enforced?)
- Secret handling (secure?)
- Input validation (complete?)

Output: `design/security-review.md`

---

## Execution Notes
- Code structure = signatures only (no logic)
- All from Phase 2 documentation
- If issues found, go back to Phase 2
```

### **Phase 4: DEVELOPMENT PROMPT**

```markdown
# TEMPLATE: Phase 4 DEVELOPMENT

## Inputs
- {MODULE_NAME}: backend/frontend/tests
- {DESIGN_LINK}: link to Phase 3 design
- {LANGUAGE}: python/javascript/etc

## Fixed Prompt

Implement {MODULE_NAME} following design:

### Task: Implement Module
Requirements:
- Follow code structure in {DESIGN_LINK}
- Match API spec from Phase 1
- Include inline comments (why, not what)
- Error handling per Phase 1 spec

Output: `{MODULE_NAME}/` (complete, working code)

Quality gate:
- Code compiles/runs without errors
- Imports resolve
- No hardcoded values
- Follows language conventions

---

## Execution Notes
- Code is specification translation, not interpretation
- If spec incomplete, ask Architect (don't guess)
- Keep functions small (<30 lines)
- One function = one responsibility
```

### **Phase 5: TESTING PROMPT**

```markdown
# TEMPLATE: Phase 5 TESTING

## Inputs
- {PROJECT_NAME}
- {CODE_LINK}: link to Phase 4 code
- {TEST_PLAN_LINK}: from Phase 1

## Fixed Prompt

Test implementation against spec:

### Task 1: Functional Testing
Verify each endpoint/feature:
- Test cases from Phase 1 test plan
- Happy path + error cases
- Edge cases from Phase 1
- Actual vs expected behavior

Output: `tests/functional-tests.py`

### Task 2: Security Testing
Verify security from Phase 2:
- Authentication required?
- Authorization enforced?
- Input validation working?
- Secrets not exposed?

Output: `tests/security-tests.py`

### Task 3: Test Report
Summary:
- Total tests: X
- Passed: Y
- Failed: Z (with details)
- Coverage: X%

Output: `tests/TEST-REPORT.md`

---

## Execution Notes
- Tests verify spec (Phase 1), not implementation
- Every test is traceable to requirement
- Red test before green (TDD)
- Coverage target: 80%+
```

### **Phase 6: FINALIZATION PROMPT**

```markdown
# TEMPLATE: Phase 6 FINALIZATION

## Inputs
- {PROJECT_NAME}
- {CODE_LINK}: link to Phase 4 code
- {TEST_REPORT_LINK}: from Phase 5

## Fixed Prompt

Final review and documentation:

### Task 1: Code Review
Check:
- Quality (lint, style, complexity)
- Maintainability (clear names, structure)
- Performance (no obvious bottlenecks)
- Tech debt assessment

Output: `final/CODE-REVIEW.md`

### Task 2: Final Documentation
Complete docs:
- README (how to run)
- Configuration guide
- Troubleshooting
- API documentation

Output: `final/README.md`, `final/CONFIG.md`, `final/API.md`

### Task 3: Deployment Preparation
Ready to deploy:
- Deployment checklist (all items?)
- Runbook (step-by-step deployment)
- Monitoring setup
- Rollback procedure

Output: `final/DEPLOYMENT.md`

---

## Execution Notes
- Everything from Phase 1-5 covered?
- All tests passing?
- All docs complete?
- Ready for production?
```

### **Phase 7: DELIVERY PROMPT**

```markdown
# TEMPLATE: Phase 7 DELIVERY

## Inputs
- {PROJECT_NAME}
- {FINAL_ARTIFACTS}: link to Phase 6 output
- {QUALITY_GATES}: all passed?

## Fixed Prompt

Orchestrator final validation:

### Task: Final Sign-Off
Verify:
- All phases complete?
- All tests pass?
- All docs present?
- Security validated?
- Performance acceptable?
- Ready for production?

Output: `final/READY-FOR-PRODUCTION.md` (yes/no)

If YES:
- Auto-create PR (summary from Phase 1)
- Auto-merge (if all checks pass)
- Auto-deploy to staging
- Notify supervisor

If NO:
- List blockers
- Suggest fixes
- Request re-work on specific phase

---

## Execution Notes
- Final gate before production
- No surprises (everything already validated)
- Supervisor final approval still required
```

---

## 🔄 **Template Usage Flow**

```
New Project Starts:
  ↓
Orchestrator loads all 7 templates
  ↓
Injects project parameters:
  - {PROJECT_NAME}: "Real-time Chat"
  - {TECH_STACK}: "WebSocket, Redis, FastAPI"
  - {TIMELINE}: "3 days"
  - {SCALE}: "medium"
  ↓
Phase -1 Agent executes template (not custom prompt)
  ↓
Phase 0 Agent loads template + links Phase -1 output
  ↓
Phase 1 Agent loads template + links Phase 0 output
  ↓
... (same pattern for all 7 phases)
  ↓
Phase 7 Agent validates + delivers

Result:
  ✓ No long custom prompts
  ✓ Consistent execution across projects
  ✓ 95% automation in prompt generation
  ✓ Future projects inherit all improvements
```

---

## 💾 **Template Maintenance**

### **When to Update a Template:**

1. **Issue Found in Execution**
   - Example: Phase 1 missed a requirement
   - Action: Add "Verify phase -1 findings are covered" to template
   - Applied to: ALL future projects automatically

2. **New Pattern Discovered**
   - Example: Redis pattern for caching
   - Action: Add to Phase 0 tech strategy template
   - Applied to: ALL future projects automatically

3. **Quality Improvement**
   - Example: Test coverage should be 90% not 80%
   - Action: Update Phase 5 testing template
   - Applied to: ALL future projects automatically

### **Template Versioning**

```markdown
# Phase 1 REQUIREMENT PROMPT

## Version 2.3 (2026-02-26)
Changes from v2.2:
- Added: "Verify API endpoints are testable" check
- Reason: Issue PF-008 (untestable API design)
- Impact: All Phase 1 from now on includes testability check

## Version 2.2 (2026-02-25)
Changes from v2.1:
- Added: "Check for conflicting user story requirements"
- Reason: Issue PF-005 (contradictory stories)
```

---

## 🚫 **Anti-Patterns (Eliminated)**

```
❌ WRONG: Writing custom prompt for Phase 1 every time
✅ RIGHT: Use Phase 1 template, inject {project_params}

❌ WRONG: "That issue happened before, we should fix it"
✅ RIGHT: Update template so it NEVER happens again

❌ WRONG: Repeating 500-word prompts for 10 projects
✅ RIGHT: 1 template, 10 projects, zero repetition

❌ WRONG: "We should remember to check X in Phase 2"
✅ RIGHT: Add to Phase 2 template (automatic for all future)

❌ WRONG: Learning same lesson across projects
✅ RIGHT: Lesson learned once → applied to all future projects
```

---

## 📊 **Impact: Templates Eliminate Repetition**

| Aspect | Without Templates | With Templates |
|--------|------------------|----------------|
| **Per-phase prompt length** | 500 words | 200 words (template) + 50 words (params) |
| **Prompt creation time** | 15 min | 2 min (parameter injection) |
| **Consistency** | 60% (human variation) | 100% (fixed template) |
| **Issue recurrence** | 80% (same problems repeat) | 5% (template prevents 95%) |
| **Knowledge transfer** | Verbal (fragile) | Template (permanent) |
| **Future projects** | "Remember to..." (forgot) | Template (automatic) |

---

**Version**: v1.0 | **Status**: Production | **Impact**: 95% repetition eliminated
