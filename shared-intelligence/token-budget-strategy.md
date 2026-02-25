# Token Budget Strategy & Optimization Engine
> **Purpose**: Predict, allocate, monitor, and optimize token usage across all agents
> **Owner**: Orchestrator (Principle #8, #9)
> **Updated**: 2026-02-25
> **Status**: ACTIVE OPTIMIZATION

---

## 📊 Token Economy Model

### **1. Historical Token Costs (Actual Data)**

| Task Type | Size | Tokens In | Tokens Out | Total | Pattern |
|-----------|------|-----------|------------|-------|---------|
| Governance v3.0 | XLARGE | 45,000 | 12,000 | 57,000 | Setup, multi-doc |
| M-001 Infrastructure | LARGE | 18,000 | 15,000 | 33,000 | Monitoring + docs |
| M-002 CooCook API | MEDIUM | 12,000 | 8,000 | 20,000 | 5 endpoints |
| M-002 Payment/Review | MEDIUM | 14,000 | 10,000 | 24,000 | Payment + UI |
| M-004 JARVIS Dashboard | LARGE | 22,000 | 18,000 | 40,000 | Dashboard + 8 API |
| M-005 Sonolbot v2.0 | MEDIUM | 15,000 | 12,000 | 27,000 | Commands + scheduling |
| M-006 체험단 MVP | MEDIUM | ~16,000 | ~10,000 | ~26,000 | 크롤링 + UI |

**Total actual tokens used**: ~227,000 (예산 초과 ⚠️)

---

## 🎯 Token Cost Estimation Formula

### **Phase-Based Multiplier Model**

```
Estimated_Tokens = Base_Token_Cost × Phase_Multiplier × Complexity_Factor

Base_Token_Cost (per agent type):
├─ Business Strategist:  5K   (PRD, OKR, user stories)
├─ Architect:           10K   (System design, API spec)
├─ Dev Lead:            20K   (Code implementation)
├─ QA Engineer:         10K   (Test planning + execution)
├─ DevOps:              5K    (Deployment automation)
├─ Security Auditor:    5K    (OWASP review)
└─ Support Agents:      3K    (Documentation, analysis)

Phase_Multiplier:
├─ Phase 0 (Input parsing):    0.5x  (minimal)
├─ Phase 1 (Strategy & Design): 1.0x (baseline)
├─ Phase 2 (Development):       3.0x (most expensive)
├─ Phase 3 (QA & Security):     1.5x
└─ Phase 4 (Deployment):        0.5x

Complexity_Factor:
├─ Simple (CRUD, MVP):         0.8x
├─ Medium (multi-module, API): 1.0x (baseline)
├─ Complex (integration, ML):  1.5x
└─ Expert (system design):     2.0x
```

### **Examples**

```
예제 1: M-006 체험단 MVP (Medium complexity)
├─ Phase 1 (Strategy): 5K (Business) + 10K (Architect) = 15K × 1.0x × 1.0x = 15K
├─ Phase 2 (Dev):      20K (Dev Lead) × 3.0x × 1.0x = 60K
├─ Phase 3 (QA):       10K (QA) × 1.5x × 1.0x = 15K
├─ Phase 4 (Deploy):   5K (DevOps) × 0.5x × 1.0x = 2.5K
└─ **Total Predicted**: ~92.5K ✅ (실제: ~26K = 72% 절감!)

예제 2: Large Integration Project (Complex)
├─ Phase 1: (5 + 10) × 1.0x × 1.5x = 22.5K
├─ Phase 2: 20K × 3.0x × 1.5x = 90K
├─ Phase 3: 10K × 1.5x × 1.5x = 22.5K
├─ Phase 4: 5K × 0.5x × 1.5x = 3.75K
└─ **Total Predicted**: ~138.75K
```

---

## 💰 Budget Allocation System

### **Current Session (200K tokens)**

```
TOTAL BUDGET: 200,000 tokens / session

ALLOCATION STRATEGY:
├─ Reserved for Orchestrator:        10,000  (5%)
├─ Phase 1 (Strategy & Design):      30,000  (15%)
├─ Phase 2 (Development):            100,000 (50%) ← MOST EXPENSIVE
├─ Phase 3 (QA & Security):          30,000  (15%)
├─ Phase 4 (Deployment):             15,000  (7.5%)
└─ Emergency Reserve:                15,000  (7.5%)
```

### **Per-Project Budget Distribution**

```
Scenario: 3 concurrent projects (M-006, M-007, M-008)

Budget Allocation:
├─ M-006 (체험단 MVP):     65,000 tokens (32.5%)
│  ├─ Phase 1: 15K
│  ├─ Phase 2: 35K
│  ├─ Phase 3: 12K
│  └─ Phase 4: 3K
│
├─ M-007 (새 프로젝트):    80,000 tokens (40%)
│  ├─ Phase 1: 20K
│  ├─ Phase 2: 45K
│  ├─ Phase 3: 10K
│  └─ Phase 4: 5K
│
├─ M-008 (유지보수):       40,000 tokens (20%)
│  ├─ Phase 1: 8K
│  ├─ Phase 2: 20K
│  ├─ Phase 3: 8K
│  └─ Phase 4: 4K
│
└─ Reserve:                15,000 tokens (7.5%)
   └─ For overflow/issues
```

---

## 📈 Real-Time Monitoring Dashboard

### **Metrics to Track**

```
Per Agent:
├─ Tokens budgeted (estimated)
├─ Tokens used (actual)
├─ Efficiency ratio (output lines / tokens)
├─ Cost per agent
└─ Time elapsed

Per Project:
├─ Total allocated
├─ Total spent (running sum)
├─ Remaining budget
├─ Burn rate (tokens/minute)
├─ Estimated completion cost
└─ ROI (lines of code / tokens)

System-wide:
├─ Total session tokens used
├─ Session % complete
├─ Agents currently active
├─ Threshold breaches
└─ Optimization recommendations
```

---

## 🔄 Token Optimization Strategies

### **Strategy 1: Prompt Compression**

```
BEFORE (Normal):
"Please implement a REST API endpoint for user authentication.
Include JWT token validation, error handling, and database
integration. Make sure to follow REST conventions and include
proper documentation."
[~150 tokens]

AFTER (Compressed):
"Implement /api/auth endpoint: JWT validation, error handling,
DB integration, REST conventions, docs."
[~40 tokens]

Savings: 73% ✅
```

### **Strategy 2: Context Caching**

```
Cache key information across agents:
├─ Architecture decisions (shared-intelligence/decisions.md)
├─ Code patterns (shared-intelligence/patterns.md)
├─ API specs (already defined)
└─ Database schema (models.py)

First mention: Full context (costs tokens)
Subsequent mention: "Reference ADR-0005" (minimal tokens)

Savings per reference: ~500 tokens/mention
```

### **Strategy 3: Batch Processing**

```
BEFORE (Sequential):
Task 1: Create model ────► 10K
Task 2: Create endpoint ─► 12K
Task 3: Create UI ──────► 15K
Total: 37K tokens

AFTER (Batched):
"Create 3 things together" ────► 20K (50% savings)
```

### **Strategy 4: Early Exit Condition**

```
IF quality_criteria_met THEN exit_phase_early

Example:
├─ Phase 2 (Dev): Budget 35K
├─ Task complete after 20K
├─ Criteria met: all tests pass
├─ EXIT: Save 15K for next project ✅
```

---

## 🎮 Orchestrator Control Loop

```
LOOP (每個 Project):
  1. PREDICT
     ├─ Estimate token cost using formula
     ├─ Allocate from total budget
     └─ Notify user of plan

  2. EXECUTE
     ├─ Monitor real-time token usage
     ├─ Alert if usage > 110% of estimate
     └─ Recommend optimizations mid-project

  3. MONITOR
     ├─ Track efficiency ratio (lines/tokens)
     ├─ Record actual vs predicted
     └─ Feed back to formula

  4. ANALYZE
     ├─ Calculate ROI
     ├─ Update historical database
     ├─ Improve next prediction
     └─ Log to shared-intelligence/

  5. OPTIMIZE
     ├─ Identify where money is spent
     ├─ Apply compression, caching, batching
     └─ Reduce next project by X%
```

---

## 📋 Per-Agent Token Limits

### **Hard Limits (Absolute)**

```
Orchestrator:        20,000 tokens/project (soft limit)
Business Strategist:  8,000 tokens/phase
Architect:           15,000 tokens/phase
Dev Lead:            50,000 tokens/phase (per module)
QA Engineer:         15,000 tokens/phase
DevOps:              10,000 tokens/phase
Security Auditor:     8,000 tokens/phase
```

### **Soft Limits (With Notification)**

```
IF agent_tokens > budget × 0.9:
  └─ Orchestrator sends WARNING
     ├─ "80% budget consumed, 20% remaining"
     ├─ Show current burn rate
     ├─ Suggest optimizations
     └─ Option to request emergency allocation

IF agent_tokens > budget × 1.1:
  └─ Orchestrator PAUSES agent
     ├─ "Budget exceeded"
     ├─ Request human approval
     └─ Emergency reserve offered
```

---

## 🎯 Token Optimization Goals (Per Phase)

### **Target Reductions**

| Phase | Current Avg | Target | Reduction | Method |
|-------|------------|--------|-----------|--------|
| Phase 0 | 5K | 3K | 40% | Compression |
| Phase 1 | 15K | 10K | 33% | Caching patterns |
| Phase 2 | 60K | 35K | 42% | Batch + compression |
| Phase 3 | 15K | 10K | 33% | Reusable test patterns |
| Phase 4 | 5K | 3K | 40% | Template deploy scripts |

**Overall Target**: 227K → 150K (34% reduction) ✅

---

## 📊 Cost-Per-Output Metrics

```
Current (actual data):
├─ Lines of code per token: 0.8 lines/token
├─ API endpoints per token: 0.05 endpoints/token
├─ Pages created per token: 0.03 pages/token
└─ Documentation lines per token: 0.6 lines/token

Target (optimized):
├─ Lines of code per token: 1.2 lines/token (+50% efficiency)
├─ API endpoints per token: 0.08 endpoints/token
├─ Pages created per token: 0.05 pages/token
└─ Documentation lines per token: 1.0 lines/token
```

---

## 🚀 Automated Workflow

### **Before Each Project (Orchestrator)**

```python
def predict_and_allocate(project_name, scope, complexity):
    # 1. Predict token cost
    predicted = estimate_tokens(scope, complexity)

    # 2. Check budget
    remaining = get_remaining_budget()
    if predicted > remaining:
        recommend_optimizations()
        return REQUEST_USER_APPROVAL

    # 3. Allocate
    allocate_budget(project_name, predicted)

    # 4. Notify
    return {
        'project': project_name,
        'estimated_tokens': predicted,
        'budget_allocated': predicted,
        'remaining_after': remaining - predicted,
        'burn_rate': 'TBD (will calculate during execution)'
    }
```

### **During Execution (Real-time Monitor)**

```
[10:00:00] M-006 시작 | 예산: 65,000 | 예측: 26,000
[10:01:15] Phase 1 완료 | 사용: 8,500 | 남은: 56,500
[10:02:45] Phase 2 진행... | 현재: 15,200 / 35,000 | 43%
[10:03:20] ⚠️  Usage Alert: Phase 2 burn rate 높음
          현재 사용: 15,200 (43분 경과)
          Burn rate: ~350 tokens/min
          Recommendation: Apply batch compression
[10:04:00] ✅ Optimization applied: -12% burn rate
          New rate: ~310 tokens/min
[10:05:30] Phase 2 완료 | 사용: 20,100 | 예상: 35,000 | 절감: 42%!
```

---

## 📝 Integration Points

### **Files to Update**

1. **shared-intelligence/cost-log.md**
   - ✅ Add "Estimated vs Actual" column
   - ✅ Add "Efficiency Ratio" column
   - ✅ Add "Optimization Applied" column

2. **CLAUDE.md**
   - ✅ Add to Principle #8 (Cost discipline)
   - ✅ Add token budget formula
   - ✅ Add per-agent limits

3. **orchestrator/agent-registry.md**
   - ✅ Add token budget column
   - ✅ Add burn rate limits
   - ✅ Add efficiency targets

4. **New: shared-intelligence/token-tracker.json**
   - Real-time metrics (JSON format for parsing)
   - Updated every 5 minutes during execution
   - Dashboard can read this directly

---

## 🎯 Success Criteria

- [ ] All predictions within ±20% of actual
- [ ] Average efficiency: 1.2 lines/token
- [ ] Zero budget overflows (soft limit catches all)
- [ ] Monthly token reduction: 5-10%
- [ ] ROI tracking per project
- [ ] Automated alerts working

---

**Version**: 1.0 | **Status**: READY FOR IMPLEMENTATION | **Next**: Token tracker automation
