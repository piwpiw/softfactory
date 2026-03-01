# 📝 Lean Execution Protocol v1.0 — Fast Iterations, Minimal Overhead

> **Purpose**: ```
> **Status**: 🟢 ACTIVE (관리 중)
> **Impact**: [Engineering / Operations]

---

## ⚡ Executive Summary (핵심 요약)
- **주요 내용**: 본 문서는 Lean Execution Protocol v1.0 — Fast Iterations, Minimal Overhead 관련 핵심 명세 및 관리 포인트를 포함합니다.
- **상태**: 현재 최신화 완료 및 검토 됨.
- **연관 문서**: [Master Index](./NOTION_MASTER_INDEX.md)

---

> **Philosophy**: 빠른 반복 + 문서만 append + 중복 zero + context auto-compact
> **Mode**: Incremental-first, not full-rewrite
> **Status**: ACTIVE

---

## 🎯 **Core Principle: "Patch, Don't Rewrite"**

```
❌ OLD (Wasteful):
  Iteration 1: Document A (full)
  Iteration 2: Document A (rewrite full)
  Iteration 3: Document A (rewrite full again)
  = 반복 작업, context 낭비, 비효율

✅ NEW (Lean):
  Iteration 1: Document A v1
  Iteration 2: Document A v1 + PATCH (변경사항만)
  Iteration 3: Document A v1 + PATCH + PATCH
  = 변경만 추적, 빠름, token 절감
```

---

## 📝 **Document Pattern: "Append Only, Reference as Needed"**

### **Markdown Structure (아래로만 추가)**

```markdown
# Document Title

## Section 1: Stable Content (변경 X)
[초기 정의, 절대 변경 안 함]

## Section 2: Stable Content
[초기 정의, 절대 변경 안 함]

---

## PATCH LOG (변경사항 기록)

### Patch 1.1 (2026-02-25 14:05)
**Changes**: API endpoint added
- Added: POST /api/users/profile
- Modified: GET /api/users to include avatar
- Rationale: User profile feature required

**Previous version**: [Link to v1.0]
**Impact**: Frontend needs update ✓

### Patch 1.2 (2026-02-25 14:30)
**Changes**: Database schema update
- Added: users.avatar_url column
- Removed: users.profile_image (deprecated)
- Migration: auto_increment timestamp

**Previous version**: [Link to v1.1]
**Impact**: No frontend changes needed
```

### **WHY This Pattern?**

```
✓ Fast reads: Latest patch만 읽으면 됨
✓ History preserved: 모든 버전 추적 가능
✓ Diff-friendly: 뭐가 바뀌었는지 한눈에
✓ Reviewable: "이 패치가 correct한가?"만 검토
✓ Compact context: "v1.0은 생략, v1.5 patch부터만" 가능
✓ Revert-able: 이전 버전으로 돌리기 쉬움
```

---

## 🔄 **Context Auto-Compact: "Keep it Short"**

### **Level 1: Full Context (초회)**

```
당신: "프로젝트: 회원가입, ..."

Orchestrator:
  [전체 context 전달 — 1000 tokens]
  ├─ Phase -1: Research document
  ├─ Phase 0: Planning document
  ├─ Phase 1: Requirement spec
  └─ ... all details
```

### **Level 2: Incremental Context (Patch 이후)**

```
당신: "API endpoint 추가하고 싶어"

Orchestrator:
  [이전 document는 compress]

  Previous spec: [링크 to v1.0] ← 안 읽음, 참조만

  Current status:
    - Phase 1: COMPLETED v1.0
    - Phase 2: IN_PROGRESS → PATCH 1.1
    - Phase 3: READY

  New requirements:
    - Added endpoint: POST /api/users/profile
    - Modified: GET /api/users schema

  Action:
    Phase 1.1 → Review + approve (5 min)
    Phase 2: Auto-update spec
    Phase 3: Proceed

  [패치만 설명 — 200 tokens]
```

### **Level 3: Summary Only (많은 반복 후)**

```
당신: "상태 줄래"

Orchestrator:
  **Project: 회원가입 시스템**

  Phase 1: ✓ COMPLETE (v1.5, 5 patches)
  Phase 2: IN_PROGRESS (v2.3, 3 patches)
  Phase 3: READY (v3.0)

  Latest patch (2026-02-25 15:30):
    - Modified: Password validation regex
    - Impact: Test suite updated
    - Status: ✓ Approved

  Next: Phase 3 code generation

  [1줄 요약 — 50 tokens]
```

---

## 📋 **Document Type Strategy**

### **Type A: Static Documents (거의 변경 없음)**

**예**: API specification, Database schema, Architecture decision

```
✅ Append-only pattern 사용
  ├─ Core spec: 절대 변경 안 함
  ├─ Patch log: 추가/폐기된 항목만
  └─ Reference: v1.0 spec은 안 읽음

⏱️ Review time: 5분 (patch만)
💾 Storage: efficient (delta만 저장)
```

**Example**: API Spec

```markdown
# API Specification

## Core Endpoints (v1.0, stable)
- GET /api/users
- POST /api/users
- GET /api/users/{id}

---

## PATCHES

### v1.1 (2026-02-25 14:05)
Added: POST /api/users/{id}/profile
```

### **Type B: Living Documents (자주 변경)**

**예**: Progress tracking, Status report, Test results

```
✅ Version + delta pattern
  ├─ Latest version만 필요
  ├─ History는 archive
  └─ 이전 내용 참조 안 함

⏱️ Review time: 2-3분
💾 Storage: 최소 (latest만)
```

**Example**: Progress Report

```markdown
# M-007 Progress Report

## Latest Status (v2.5)
Phase 1: ✓ COMPLETE
Phase 2: IN_PROGRESS (75%)
Phase 3: READY

## Previous versions
- v2.4: [archive link]
- v2.3: [archive link]
```

### **Type C: Changing Documents (매번 patch)**

**예**: Test results, Code review comments, Performance metrics

```
✅ Log pattern
  ├─ Latest 10개만 display
  ├─ 나머지는 archive
  └─ Trend만 summary

⏱️ Review time: 1분
💾 Storage: 최소
```

**Example**: Test Results

```markdown
# Test Results

## Latest Run (v2.5 - 2026-02-25 15:30)
✓ 47/47 PASS
✓ Coverage: 89%
✓ Performance: 234ms avg

## Previous 10 runs
- v2.4: 45/47 (2 failures fixed)
- v2.3: 43/47 (4 failures)
- ...
```

---

## 🚫 **Anti-Patterns: What NOT To Do**

### **❌ Anti-Pattern 1: Full Document Rewrite**

```
❌ WRONG:
  Phase 1 v1.0: [전체 문서, 1000 lines]
  Phase 1 v1.1: [전체 문서 다시, 1050 lines] ← token 낭비

✅ RIGHT:
  Phase 1 v1.0: [1000 lines]
  Phase 1 v1.1: PATCH [50 lines] ← delta만
```

### **❌ Anti-Pattern 2: Full Context Every Time**

```
❌ WRONG:
  Agent A: [전체 문서 전달] → 1000 tokens
  Agent B: [전체 문서 전달 다시] → 1000 tokens
  Agent C: [전체 문서 전달 또 다시] → 1000 tokens
  Total: 3000 tokens (반복)

✅ RIGHT:
  Agent A: [전체 문서] → 1000 tokens
  Agent B: [참조 링크 + 변경사항만] → 200 tokens
  Agent C: [참조 링크 + 변경사항만] → 200 tokens
  Total: 1400 tokens (70% 절감)
```

### **❌ Anti-Pattern 3: Same Test Every Time**

```
❌ WRONG:
  Iteration 1: Full test suite run → 50 API calls
  Iteration 2: Full test suite run → 50 API calls (반복)
  Iteration 3: Full test suite run → 50 API calls (반복)
  Total: 150 calls (낭비)

✅ RIGHT:
  Iteration 1: Full test suite → 50 calls
  Iteration 2: Changed tests only → 5 calls (regression check)
  Iteration 3: Changed tests only → 3 calls (smoke test)
  Total: 58 calls (61% 절감)
```

### **❌ Anti-Pattern 4: Redundant Documentation**

```
❌ WRONG:
  research/market-analysis.md (초회)
  planning/market-considerations.md (다시 쓴 유사 내용)
  requirement/market-research.md (또 다시 쓴 유사 내용)
  = 중복, 유지보수 nightmare

✅ RIGHT:
  research/market-analysis.md (단 하나의 source of truth)
  planning/: [Links to research/] ← 참조
  requirement/: [Links to research/] ← 참조
  = 1개만 유지, 항상 최신
```

---

## 📐 **Standardization: One-time Setup, Forever Reuse**

### **Pattern Definition (한 번만)**

```markdown
# PATTERN: API Endpoint Design

## Template
```
**Endpoint**: [METHOD] /api/[resource]/[action]
**Auth**: [required/optional]
**Request**: [schema with example]
**Response**: [schema with example]
**Error cases**: [list]
**Notes**: [special considerations]
```

## Examples in codebase
- GET /api/users/profile (in project A)
- POST /api/payments (in project B)
- DELETE /api/sessions/{id} (in project C)
```

### **Application (계속 재사용)**

```
Iteration 1: Create pattern (30 min)
  → Document it in patterns.md

Iteration 2-100: Apply pattern
  → Copy template (30 sec)
  → Fill in details (2 min)
  → Done (no reinvention)

Total: 30 min + (99 × 2.5 min) = 4.5 hours
vs Old: 100 × 30 min = 50 hours
= 91% time savings!
```

### **System-Wide Standardization**

```
shared-intelligence/patterns.md
├─ API Endpoint Design
├─ Database Migration
├─ Test Case Structure
├─ Security Review Checklist
├─ Error Handling Pattern
├─ Configuration Management
└─ Deployment Checklist

Every project uses these patterns:
  ✓ No reinvention
  ✓ Consistency across projects
  ✓ New team members learn from patterns
  ✓ Best practices baked in
```

---

## ⚡ **Execution Flow: Patch-Based Iterations**

### **Iteration 1 (Full)**

```
[14:00] Phase 1: REQUIREMENT
  Orchestrator: "Phase 1 시작"

  Agents:
    Business: User stories 작성 → v1.0
    Architect: API spec 작성 → v1.0
    QA: Test plan 작성 → v1.0

  Context: Full (1000 tokens)
  Time: 15 min
  Output: 3개 document v1.0
```

### **Iteration 2 (Patch)**

```
[14:15] Phase 2: API IMPLEMENTATION
  Orchestrator: "Phase 2 시작, Phase 1 status: v1.0"

  Dev: Phase 1.0 읽음 (full)
       "API endpoint 어떻게 하지?"
       → Architect에게 질문

  Architect: Phase 1.0은 안 읽음 (이미 봤음)
             변경사항만: "POST /users/profile 추가"
             Context: Patch (200 tokens) ← 70% 절감
             Time: 2 min

  Output: Phase 1.1 PATCH (변경사항만)
```

### **Iteration 3 (Patch)**

```
[14:30] REQUIREMENT UPDATE (비즈니스 변경)
  PM: "User avatar 지원해야 함"

  Business: Phase 1.0 기반
            PATCH 1.1 추가: "User.avatar field"
            Time: 2 min
            Context: 50 tokens

  Architect: Phase 1.0 기반
             PATCH 1.1 읽음 (user stories 변경)
             PATCH 1.2 추가: "GET /api/users response에 avatar"
             Time: 2 min
             Context: 80 tokens

  Dev: Phase 1.0+1.1+1.2 통합 (3 min read)
       구현에 착수

  Total: 7 min (vs 15 min if full rewrite)
```

---

## 🎯 **Review Strategy: "Just the Delta"**

### **Full Review (초회)**

```
Reviewer: Phase 1.0 전체 검토
Time: 15 min
Context: Full spec
Approval: "✓ All good"
```

### **Patch Review (이후)**

```
Reviewer: PATCH 1.1만 검토
  "Added POST /users/profile"
  "Modified GET /users response"
  "Is this consistent with v1.0?" ← 빠른 check

Time: 3 min (vs 15 min if full)
Context: Delta only (200 tokens vs 1000)
Approval: "✓ Patch approved"
```

### **Summary Review (많은 패치 후)**

```
Reviewer: PATCH SUMMARY
  "Total 5 patches to Phase 1
   - 3 added endpoints
   - 2 schema updates
   - 0 breaking changes

   All consistent? ✓
   All approved? ✓"

Time: 2 min (vs 15 min)
Context: Summary only (100 tokens vs 1000)
Approval: "✓ Ready for code generation"
```

---

## 📊 **Metrics: Lean Execution Impact**

| Metric | Old (Full) | New (Lean) | Savings |
|--------|-----------|-----------|---------|
| **Per-iteration time** | 15 min | 3 min | 80% |
| **Context per iteration** | 1000 tok | 200 tok | 80% |
| **Full project time** | 3 hours | 1.5 hours | 50% |
| **Total tokens/project** | 65K | 35K | 46% |
| **Review cycles** | 1 | 7 (incremental) | parallel |
| **Rework due to missed feedback** | 20% | 3% | 85% |

---

## 🔧 **Implementation Checklist**

```
[ ] Document Pattern: Append-only structure implemented
[ ] Archive System: Old versions archived, latest + patches only
[ ] Reference Links: All documents use cross-references
[ ] Auto-Compact: Context compression per iteration
[ ] Patch Logging: PATCH LOG section in all documents
[ ] Pattern Library: shared-intelligence/patterns.md standardized
[ ] Delta Review: Review process adjusted for patches
[ ] Summary System: Auto-summary for large patch logs
[ ] Context Caching: Previous context → 1-line reference
[ ] Dedup Check: shared-intelligence/pitfalls.md updated with "no duplicate docs"
```

---

**Version**: v1.0 | **Status**: Ready for adoption | **Impact**: 50-80% time + token savings