# M-008 Implementation Index
> **Mission:** Telegram Bot Scheduler + CooCook API Enhancement
> **Start Date:** 2026-02-26 | **Target Completion:** 2026-02-26 (4 hours)
> **Status:** PLANNING COMPLETE ✅

---

## 📚 Complete Documentation Set

This mission is fully documented. Here's where to find each piece:

### For Quick Understanding (15 minutes)

**Start here if you have limited time:**

```
M-008-QUICK-START.md
├─ The Ask (summary)
├─ PART A: Telegram Notifications (1 hour)
│  └─ 3-step implementation + API reference
├─ PART B: CooCook Enhancement (3 hours)
│  ├─ Phase 1: Recipes (1.5 hours)
│  └─ Phase 2: Shopping & Feed (1.5 hours)
├─ File structure before/after
├─ Implementation checklist
├─ API reference (all 20+ endpoints)
├─ Key patterns & best practices
├─ Testing approach
├─ Success criteria
└─ Get started (step-by-step)
```

**Time:** 10-15 minutes to understand what you're building

---

### For Full Implementation (4-5 hours)

**This is your detailed reference while coding:**

```
M-008-TELEGRAM-COOCOOK-IMPLEMENTATION-PLAN.md
├─ Executive Summary
├─ PART A: Telegram Bot Scheduler (1 hour)
│  ├─ Current state & problem
│  ├─ Architecture diagram
│  ├─ Task A.1: Extend SNSSettings Model (code)
│  ├─ Task A.2: SNSNotificationService (code)
│  ├─ Task A.3: Update scheduler.py (code)
│  ├─ Task A.4: Telegram Settings API (code)
│  ├─ Task A.5: Update daemon/telegram_notifier.py
│  └─ Task A.6: Tests & Validation (code)
├─ PART B: CooCook API Enhancement (3 hours)
│  ├─ Current state & architecture
│  │
│  ├─ PHASE 1: Recipes & Nutrition (1.5 hours)
│  │  ├─ Task B1.1: Recipe Models (code)
│  │  ├─ Task B1.2: NutritionCalculator (code)
│  │  ├─ Task B1.3: Search API (code)
│  │  └─ Task B1.4: Tests
│  │
│  └─ PHASE 2: Shopping & Feed (1.5 hours)
│     ├─ Task B2.1: Shopping Models (code)
│     ├─ Task B2.2: Shopping Service (code)
│     ├─ Task B2.3: Social Feed (code)
│     └─ (tests included)
│
├─ Implementation Timeline (Gantt-style)
├─ Success Criteria Checklist
├─ Risk & Mitigation
├─ Dependencies & Packages
├─ Files to Create/Modify
├─ Token Budget Allocation
└─ Next Steps
```

**Time:** 3-4 hours to read + implement

**Recommendation:** Keep this open in one window while coding

---

### For Architecture & Design (30 minutes)

**If you need to understand system design or make decisions:**

```
M-008-ARCHITECTURE.md
├─ Overall System Architecture (diagram)
├─ PART A: Telegram Notification Flow
│  ├─ Sequence diagram (SNS publish → Telegram alert)
│  ├─ SNSSettings data model
│  ├─ SNSNotificationService class design
│  ├─ Background job: notify_pending_jobs()
│  └─ Notification flow diagram
├─ PART B1: Recipe Search Architecture
│  ├─ Data models (Recipe, RecipeIngredient, RecipeReview)
│  ├─ Search API request/response flow
│  ├─ Nutrition calculator algorithm (step-by-step)
│  └─ Cache strategy (keys, TTL, invalidation)
├─ PART B2: Shopping List & Social Feed
│  ├─ Shopping list consolidation logic
│  ├─ Export workflow (PDF generation)
│  ├─ Social network model (following + sharing)
│  ├─ Feed generation algorithm
│  └─ Data model relationships
├─ Database Schema (complete SQL view)
├─ Caching & Performance Strategy (table)
├─ Error Handling & Validation
└─ Monitoring & Logging
```

**Time:** 20-30 minutes to understand data flows

**Recommendation:** Review this if:
- You're not sure how pieces fit together
- You need to make architectural decisions
- You want to understand performance strategy

---

### For Handoff & Project Overview (10 minutes)

**High-level summary for stakeholders:**

```
M-008-HANDOFF.md
├─ What You're Getting (3 documents)
├─ Executive Summary
│  ├─ PART A (1 hour) — Telegram notifications
│  └─ PART B (3 hours) — CooCook enhancement
├─ Implementation Map (13 tasks)
├─ File Changes Summary
├─ Dependencies & Prerequisites
├─ Success Criteria Checklist
├─ Timeline & Estimates
├─ Risk Assessment
├─ Recommended Execution Order
├─ Testing Strategy
├─ Monitoring After Deployment
├─ Known Limitations & Future Work
├─ Questions & Support
├─ Commit Strategy
├─ Project Completion Steps
└─ Ready to Begin?
```

**Time:** 5-10 minutes to understand what's being delivered

**Recommendation:** Share this with project manager / stakeholders

---

### Index & Navigation (You are here)

```
M-008-INDEX.md
├─ 📚 Complete Documentation Set (this section)
├─ 🎯 Quick Navigation by Role
├─ ⏱️ Time Investment Guide
├─ 📋 Document Summary Table
├─ 🔍 Quick Reference Links
├─ ✅ Checklist for Getting Started
└─ 📞 Common Questions
```

---

## 🎯 Quick Navigation by Role

### I'm a Developer

**Goal:** Implement features quickly with minimal ramp-up time

**Reading order:**
1. **M-008-QUICK-START.md** (15 min) — Understand what to build
2. **M-008-TELEGRAM-COOCOOK-IMPLEMENTATION-PLAN.md** (keep open) — Reference while coding
3. **M-008-ARCHITECTURE.md** (as needed) — For design questions

**Recommended workflow:**
```
1. Read QUICK-START to understand requirements
2. Pick a task (e.g., "Task A.1: Extend SNSSettings")
3. Find it in IMPLEMENTATION-PLAN.md
4. Copy code examples, adapt to your codebase
5. Implement tests (examples provided)
6. Run tests, commit, move to next task
7. Reference ARCHITECTURE.md if you have design questions
```

**Time:** 4-5 hours total (includes implementation)

---

### I'm a Tech Lead / Architect

**Goal:** Ensure quality and fit within existing system

**Reading order:**
1. **M-008-HANDOFF.md** (5 min) — Overview
2. **M-008-ARCHITECTURE.md** (30 min) — System design
3. **M-008-TELEGRAM-COOCOOK-IMPLEMENTATION-PLAN.md** (1 hour) — Detailed spec
4. **M-008-QUICK-START.md** (optional) — For double-checking

**Key sections to review:**
- Architecture diagrams (data flows)
- Database schema changes
- Caching strategy (performance)
- Error handling & validation
- Risk assessment & mitigation

**Time:** 1.5-2 hours (review only, no implementation)

---

### I'm a Project Manager

**Goal:** Track progress and understand scope

**Reading order:**
1. **M-008-HANDOFF.md** (10 min) — Executive summary
2. **M-008-QUICK-START.md** (5 min) — High-level understanding
3. Track 3 tasks (#22, #23, #24) in task manager

**Key info to track:**
- Timeline: 4 hours total
- Budget: 37K tokens / 200K available
- Success criteria: All tests passing + no breaking changes
- Risk level: LOW (well-documented, clear requirements)

**Time:** 15 minutes to understand; then monitor progress

---

### I'm a QA / Tester

**Goal:** Understand what to test and success criteria

**Reading order:**
1. **M-008-QUICK-START.md** (15 min) — Success criteria
2. **M-008-TELEGRAM-COOCOOK-IMPLEMENTATION-PLAN.md** (sections on tests) — Test cases
3. **M-008-ARCHITECTURE.md** (error handling section) — Edge cases

**Key sections:**
- Success Criteria Checklist (30+ items)
- Test cases (provided for each feature)
- Error handling & validation rules
- Performance targets (search < 1s, etc.)

**Time:** 30 minutes to understand scope; 1-2 hours to create test plan

---

## ⏱️ Time Investment Guide

```
Role              Document           Time    Purpose
─────────────────────────────────────────────────────────────
Developer         QUICK-START         15m    Understand requirements
(coding)          PLAN                240m    Reference while coding
                  ARCHITECTURE         15m    Design questions
                  ─────────────────────────
                  TOTAL               ~4.5 hours

Tech Lead         HANDOFF             10m     Overview
(review)          ARCHITECTURE         45m     System design
                  PLAN (skim)          20m     Detailed review
                  ─────────────────────────
                  TOTAL               ~1.5 hours

PM                HANDOFF             10m     Executive summary
(tracking)        QUICK-START          5m     High-level
                  Ongoing             20m     Monitor 3 tasks
                  ─────────────────────────
                  TOTAL               ~35 minutes

QA                QUICK-START         15m     Success criteria
(testing)         PLAN (test sections) 30m    Test cases
                  ARCHITECTURE        15m     Edge cases
                  ─────────────────────────
                  TOTAL               ~1 hour
```

---

## 📋 Document Summary Table

| Document | Purpose | Audience | Length | Time |
|----------|---------|----------|--------|------|
| **QUICK-START** | Get started fast | Developers | 7 pages | 15m |
| **IMPLEMENTATION-PLAN** | Step-by-step instructions | Developers | 25 pages | 4h |
| **ARCHITECTURE** | System design details | Tech leads | 15 pages | 30m |
| **HANDOFF** | Executive summary | Everyone | 10 pages | 10m |
| **INDEX** | Navigation guide | Everyone | 5 pages | 10m |

**Total documentation:** ~62 pages | **Total reading:** 1-2 hours

---

## 🔍 Quick Reference Links

### By Feature

**Telegram Notifications (PART A)**
- Implementation: See `M-008-TELEGRAM-COOCOOK-IMPLEMENTATION-PLAN.md` → PART A
- Architecture: See `M-008-ARCHITECTURE.md` → PART A section
- API: See `M-008-QUICK-START.md` → "Telegram Settings"
- Tasks: #22 in task manager

**Recipe Search (PART B1)**
- Implementation: See `M-008-TELEGRAM-COOCOOK-IMPLEMENTATION-PLAN.md` → PHASE 1
- Architecture: See `M-008-ARCHITECTURE.md` → PART B1 section
- API: See `M-008-QUICK-START.md` → "Recipes"
- Tasks: #23 in task manager

**Shopping & Feed (PART B2)**
- Implementation: See `M-008-TELEGRAM-COOCOOK-IMPLEMENTATION-PLAN.md` → PHASE 2
- Architecture: See `M-008-ARCHITECTURE.md` → PART B2 section
- API: See `M-008-QUICK-START.md` → "Shopping" & "Social"
- Tasks: #24 in task manager

---

### By Topic

**Database Models**
- Complete schema: `M-008-ARCHITECTURE.md` → Database Schema section
- Telegram: `M-008-TELEGRAM-COOCOOK-IMPLEMENTATION-PLAN.md` → Task A.1
- Recipes: `M-008-TELEGRAM-COOCOOK-IMPLEMENTATION-PLAN.md` → Task B1.1
- Shopping: `M-008-TELEGRAM-COOCOOK-IMPLEMENTATION-PLAN.md` → Task B2.1

**API Endpoints**
- All 20+ endpoints: `M-008-QUICK-START.md` → API Reference
- Telegram API: `M-008-QUICK-START.md` → PART A section
- Recipes API: `M-008-TELEGRAM-COOCOOK-IMPLEMENTATION-PLAN.md` → Task B1.3
- Shopping/Feed API: `M-008-TELEGRAM-COOCOOK-IMPLEMENTATION-PLAN.md` → Tasks B2.2/B2.3

**Testing**
- Test cases: `M-008-TELEGRAM-COOCOOK-IMPLEMENTATION-PLAN.md` → Each task (A.6, B1.4, B2.x)
- Testing strategy: `M-008-HANDOFF.md` → Testing Strategy section
- Performance targets: `M-008-QUICK-START.md` → Performance Targets

**Performance & Caching**
- Strategy: `M-008-ARCHITECTURE.md` → Caching & Performance Strategy
- Implementation: `M-008-TELEGRAM-COOCOOK-IMPLEMENTATION-PLAN.md` → B1.3 (Redis)
- Targets: `M-008-QUICK-START.md` → Performance Targets

---

## ✅ Checklist for Getting Started

### Before You Start
- [ ] Read `M-008-QUICK-START.md` (15 minutes)
- [ ] Skim `M-008-ARCHITECTURE.md` (10 minutes)
- [ ] Have `M-008-TELEGRAM-COOCOOK-IMPLEMENTATION-PLAN.md` open
- [ ] Clone/pull latest code from main branch
- [ ] Set up Python environment (if needed)

### Day 1: PART A (Telegram Notifications)
- [ ] Complete Task A.1: Extend SNSSettings model
- [ ] Complete Task A.2: Implement SNSNotificationService
- [ ] Complete Task A.3: Update scheduler.py
- [ ] Complete Task A.4: Create Telegram Settings API
- [ ] Complete Task A.5: Update daemon integration
- [ ] Complete Task A.6: Write & run tests
- [ ] Verify: Test Telegram notification endpoint
- [ ] Commit: 5 commits (one per task)
- [ ] Review: Check against success criteria

### Day 1-2: PART B1 (Recipes)
- [ ] Complete Task B1.1: Create Recipe models
- [ ] Complete Task B1.2: Implement NutritionCalculator
- [ ] Complete Task B1.3: Build Search API + caching
- [ ] Complete Task B1.4: Write & run tests
- [ ] Verify: Search recipe, check cache hit, verify results
- [ ] Commit: 3 commits (models, service, API)

### Day 2: PART B2 (Shopping & Social)
- [ ] Complete Task B2.1: Create Shopping List models
- [ ] Complete Task B2.2: Implement Shopping Service
- [ ] Complete Task B2.3: Build Social Features
- [ ] Complete Task B2.4: Write & run tests
- [ ] Verify: Add recipe to list, export PDF, share recipe
- [ ] Commit: 3 commits

### Final Steps
- [ ] Run full test suite (30+ tests)
- [ ] Check code quality (lint, type hints)
- [ ] Update cost-log.md with token usage
- [ ] Create pull request with handoff as description
- [ ] Request code review
- [ ] Merge to main branch
- [ ] Deploy to production
- [ ] Monitor metrics for 24 hours

---

## 📞 Common Questions

### Q: Where do I start?

**A:** Read `M-008-QUICK-START.md` first (15 minutes). It tells you:
- What you're building
- Why it's important
- The 3 major pieces
- Success criteria

Then pick a task and reference the IMPLEMENTATION-PLAN document while coding.

---

### Q: How long will this take?

**A:** Estimated 4 hours total:
- PART A (Telegram): 1 hour
- PART B1 (Recipes): 1.5 hours
- PART B2 (Shopping): 1.5 hours

**Your mileage may vary based on:**
- Familiarity with the codebase
- Experience with Flask/SQLAlchemy
- Testing thoroughness

---

### Q: What if I get stuck?

**A:** Steps:
1. Re-read the relevant task in IMPLEMENTATION-PLAN.md
2. Check code examples (they're complete, copy-paste ready)
3. Review ARCHITECTURE.md for design questions
4. Look at existing code (`backend/services/coocook.py` for patterns)
5. Run tests to see what's expected

All docs are designed to be self-explanatory.

---

### Q: Do I need to break changes?

**A:** No. All changes are additive:
- New tables/models only (no deletions)
- Existing code untouched
- New API endpoints (no breaking existing ones)
- Backward compatible with existing clients

---

### Q: What about database migrations?

**A:** Use Flask-Migrate:
```bash
flask db init  # (if first time)
flask db migrate -m "Add Telegram, Recipe, Shopping, Social models"
flask db upgrade
```

See IMPLEMENTATION-PLAN.md for schema details.

---

### Q: How do I verify my implementation?

**A:** Use the Success Criteria Checklist in `M-008-QUICK-START.md`:
- 30+ checklist items
- Clear pass/fail criteria
- Verification steps included

---

### Q: What's the token budget?

**A:** 37K tokens out of 200K (18.5%)
- PART A: 12K
- PART B1: 13K
- PART B2: 12K
- Buffer: 163K remaining (81.5%)

Low risk of overflow. You have room.

---

### Q: Who reviews the code?

**A:** Tech lead or architect should:
1. Review database schema changes
2. Check caching strategy (Redis)
3. Verify error handling
4. Validate performance targets
5. Approve before merge

See ARCHITECTURE.md for what to look for.

---

## 📌 Key Files in Your Codebase

**Existing files you'll modify:**
- `backend/models.py` — Add 7 new models, extend SNSSettings
- `backend/scheduler.py` — Replace stub, add new job
- `backend/services/coocook.py` — Extend with 12+ endpoints
- `backend/app.py` — Register new services

**Existing files you'll reference (don't modify):**
- `daemon/telegram_notifier.py` — Telegram bot (integration only)
- `backend/auth.py` — @require_auth decorator (usage)
- `backend/models.py` — User, SNSPost (relationships)

**New files you'll create:**
- `backend/services/sns_notification.py` — 150 lines
- `backend/services/nutrition_calculator.py` — 100 lines
- `tests/integration/test_sns_notifications.py` — 80 lines
- `tests/integration/test_coocook_recipes.py` — 100 lines

---

## 🚀 You're Ready!

All documentation is complete and ready for implementation.

**Next step:** Open `M-008-QUICK-START.md` and begin! 📖

---

## Document Structure Summary

```
M-008-INDEX.md (YOU ARE HERE)
├─ Explains what docs exist
├─ Who should read what
├─ Time investment per role
├─ Quick navigation links
├─ Common questions answered
└─ Ready to begin checklist

M-008-QUICK-START.md (READ FIRST - 15 min)
├─ Quick summary of requirements
├─ 3-step implementation for each part
├─ All API endpoints
├─ Success criteria
└─ Get started guide

M-008-TELEGRAM-COOCOOK-IMPLEMENTATION-PLAN.md (DETAILED SPEC - keep open)
├─ Full technical specification
├─ Code examples for every component
├─ Task-by-task breakdown
├─ Database schemas
├─ Test cases
└─ Risk mitigation

M-008-ARCHITECTURE.md (REFERENCE - as needed)
├─ System design diagrams
├─ Data flow sequences
├─ Database relationships
├─ Caching strategy
├─ Error handling
└─ Monitoring approach

M-008-HANDOFF.md (SUMMARY - for stakeholders)
├─ Executive overview
├─ Timeline & estimates
├─ Success criteria
├─ Risk assessment
├─ Testing strategy
└─ Deployment plan
```

---

**Status:** ✅ ALL DOCUMENTS COMPLETE AND READY FOR IMPLEMENTATION

**Questions?** Check the section above or refer to specific document.

**Ready to code?** Start with `M-008-QUICK-START.md` →

---

**Prepared by:** Claude Code v2.1.55 | **Governance:** CLAUDE.md v3.0 | **Date:** 2026-02-26
