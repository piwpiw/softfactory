# 📝 Phase Structure v4.0 — Spec-First, Doc-First, Review-Heavy

> **Purpose**: ```
> **Status**: 🟢 ACTIVE (관리 중)
> **Impact**: [Engineering / Operations]

---

## ⚡ Executive Summary (핵심 요약)
- **주요 내용**: 본 문서는 Phase Structure v4.0 — Spec-First, Doc-First, Review-Heavy 관련 핵심 명세 및 관리 포인트를 포함합니다.
- **상태**: 현재 최신화 완료 및 검토 됨.
- **연관 문서**: [Master Index](./NOTION_MASTER_INDEX.md)

---

> **New Approach**: Research → Plan → Requirement → Documentation → Implementation
> **Philosophy**: 에이전트 간 overlapping responsibility + document-driven development
> **Model Strategy**: Haiku default, Sonnet/Opus for critical validation only
> **Updated**: 2026-02-25

---

## 🎯 **Core Principle: Document-Driven Development**

```
Old Flow (Code-First, Fast but risky):
  Requirement → Design → Code → Test → Documentation
  ❌ Documentation 뒤늦게, often missing
  ❌ Code change 후 Document 수정 (painful)
  ❌ 단일 agent 책임 = bottleneck

New Flow (Doc-First, Safe and coordinated):
  Research → Plan → Requirement → Documentation → Code → Test
  ✅ Everything document-driven (source of truth)
  ✅ Multiple agents review each document
  ✅ Code = documentation translation
  ✅ Testing = specification verification
```

---

## 📋 **Extended Phase Structure (6 phases → 7 sub-phases)**

### **Phase -1: RESEARCH (병렬, 3-5 min)**

**Agents**: Market Analyst (lead), Architect, Security Auditor (parallel)

**Market Analyst does**:
- Web research: 경쟁사 분석, 오픈소스 조사, 기술 트렌드
- Output: `research/market-analysis.md`

**Architect does** (동시):
- Code research: 기존 코드 분석, 패턴 식별
- Output: `research/architecture-baseline.md`

**Security Auditor does** (동시):
- Security research: 유사 프로젝트 보안 이슈, threat model
- Output: `research/security-baseline.md`

**Sync Point**:
```
모든 research 결과 → shared-intelligence/research/{project}.md에 통합
```

---

### **Phase 0: PLANNING (순차, 5-8 min)**

**Agents**: Business Strategist (lead), Architect (co-lead), Dev Lead (review)

**1. Business Strategist**:
- Research 읽음
- PRD 작성 (고객 관점): features, use cases, acceptance criteria
- Output: `planning/prd.md`

**2. Architect** (동시):
- Research 읽음
- Technical planning (기술자 관점): architecture, tech stack, dependencies
- Output: `planning/tech-strategy.md`

**3. Dev Lead** (Review capacity):
- 구현 관점에서 feasibility 검토
- 문제점 flag: "이건 30분에 못 한다", "이건 불가능하다"
- Output: `planning/implementation-feasibility.md`

**Sync Point**:
```
3개 문서 검토 → Business + Architect 합의
Dev Lead의 feasibility issue 해결 또는 scope cut
→ 모두 동의 시 다음 phase
```

---

### **Phase 1: REQUIREMENT (순차, 8-12 min)**

**Agents**: Business Strategist (lead), Architect (co-lead), QA Engineer (review)

**1. Business Strategist**:
- PRD를 상세 요구사항으로 확장
- User stories (5-10개) 작성
- Acceptance criteria 명확화
- Output: `requirement/user-stories.md`

**2. Architect** (동시):
- API specification 작성 (OpenAPI/JSON)
- Data model specification (JSON schema)
- System architecture diagram (text-based)
- Output: `requirement/api-spec.json`, `requirement/data-model.json`

**3. QA Engineer** (Review):
- 요구사항 완전성 검토: "이건 어떻게 test할 거야?"
- Edge cases 식별
- Output: `requirement/qa-considerations.md`

**Sync Point**:
```
API spec + User stories + QA considerations
→ Architect + Business 최종 검토
→ QA: "이거 test 가능한가?" 확인
→ 모두 동의 시 Phase 2
```

---

### **Phase 2: DOCUMENTATION (병렬, 8-15 min)**

**Agents**: Documentation Lead (lead), Architect (co-author), QA (test-spec)

**이 phase가 중요**: 코드 작성 전에 모든 문서 완성

**1. Documentation Lead**:
- Research + Planning + Requirement 모두 읽음
- 완성된 설계 문서 작성
  - System architecture (with diagrams)
  - Data flow (with sequences)
  - API documentation (with examples)
  - Database schema (with relationships)
  - Configuration guide
- Output: `documentation/DESIGN.md`

**2. Architect** (Co-author):
- Deep technical details
- Trade-off analysis
- Alternative approaches considered
- Output: `documentation/ARCHITECTURE-DECISIONS.md`

**3. QA Engineer** (Test Specification):
- Test plan (unit, integration, E2E)
- Test cases (from user stories)
- Test data requirements
- Output: `documentation/TEST-PLAN.md`

**4. Security Auditor** (Security spec):
- Threat model details
- Security requirements (per endpoint)
- Authentication/Authorization spec
- Output: `documentation/SECURITY-SPEC.md`

**Sync Point**:
```
모든 문서 완성 & 리뷰됨
→ Documentation consistency check
→ Coverage check: 모든 requirement이 document되었는가?
→ Pass → Phase 3
```

---

### **Phase 3: DESIGN (순차, 10-15 min)**

**Agents**: Architect (lead), Security Auditor (review)

**실제로는 Phase 2에서 이미 모든 design이 done**
**Phase 3 = Design 문서의 최종 validation & 상세화**

**Architect**:
- Code skeleton 작성 (structure만, no logic)
- Database migration 계획
- Deployment diagram
- Output: `design/code-skeleton.py` (empty functions), `design/deployment.md`

**Security Auditor**:
- Security design review
- 구현 전 잠재 vulnerabilities 식별
- Output: `design/security-review.md`

**Sync Point**:
```
Security review passed → Dev Lead에게 green light
```

---

### **Phase 4: DEVELOPMENT (병렬 모듈, 30-60 min)**

**Agents**: Dev Lead (backend), Frontend Dev (frontend), QA (test cases)

**각 module은 documentation 따라 구현**

**Backend Dev**:
- API implementation (spec 따라)
- Database implementation (schema 따라)
- Output: `backend/` (완성 코드)

**Frontend Dev** (동시):
- UI implementation (spec 따라)
- API client (API spec 따라)
- Output: `frontend/` (완성 코드)

**QA** (동시):
- Test code 작성 (test plan 따라)
- Mock/stub 준비
- Output: `tests/` (완성 테스트)

**Sync Point** (Module 완성마다):
```
Code review (by peer agent):
├─ Dev Lead reviews Frontend (feasibility)
├─ Frontend Dev reviews Backend (integration points)
└─ QA reviews both (testability)
```

---

### **Phase 5: TESTING & VALIDATION (병렬, 15-30 min)**

**Agents**: QA Engineer (lead), Security Auditor (security), Dev Lead (integration)

**QA**:
- Run all tests (unit, integration, E2E)
- Coverage report
- Regression testing
- Output: `tests/test-report.md`

**Security Auditor** (동시):
- OWASP scan
- Dependency check
- Secret scan
- Output: `security/security-scan.md`

**Dev Lead** (동시):
- Code quality check (lint, type)
- Performance check
- Integration test
- Output: `tests/integration-report.md`

**Sync Point**:
```
All reports pass → Phase 6
Any critical issue → Escalate to Dev
```

---

### **Phase 6: FINALIZATION (순차, 10-15 min)**

**Agents**: Dev Lead (lead), Documentation (update), DevOps (deployment)

**Dev Lead**:
- Final code review
- Tech debt assessment
- Output: `READY_FOR_DEPLOY.md`

**Documentation**:
- Update docs with actual implementation details
- User guide finalization
- Output: `documentation/FINAL-DOCS.md`

**DevOps**:
- Deployment script preparation
- Runbook creation
- Monitoring setup
- Output: `deployment/RUNBOOK.md`

**Sync Point**:
```
All artifacts ready → Create PR
```

---

### **Phase 7: DELIVERY (순차, 5-10 min)**

**Agents**: Git automation, Orchestrator (final sign-off)

**Git Automation**:
- Commit all changes
- Create feature branch
- Auto-generate PR description (from documents!)
- Create PR
- Output: PR #XXX

**Orchestrator**:
- Final quality gate
- You (supervisor) final approval for deploy
- Merge PR
- Trigger deployment
- Output: ✅ Deployed

---

## 🔄 **Overlapping Responsibility (에이전트 간 겹침)**

핵심: **단일 agent 책임 → 여러 agent 검토**

### **Example: API Design**

```
PRIMARY: Architect
├─ 초안 작성: API spec

REVIEW 1: Dev Lead
├─ "이거 구현 가능한가?"
├─ 구현 어려운 부분 flag
└─ 대체 design 제안

REVIEW 2: QA Engineer
├─ "이거 test 가능한가?"
├─ Edge cases 찾기
└─ Test strategy 제안

REVIEW 3: Security Auditor
├─ "이거 secure한가?"
├─ 보안 요구사항 추가
└─ 인증/인가 spec 제안

→ Architect가 모든 feedback 통합 & 최종화
→ 모두 동의할 때까지 iterate
```

### **Example: Implementation**

```
PRIMARY: Dev Lead (backend)
├─ API 구현

CO-REVIEW 1: Frontend Dev
├─ "이 API로 UI 만들 수 있나?"
├─ Response format 피드백
└─ Missing fields 요청

CO-REVIEW 2: QA Engineer
├─ "이거 test하려면 뭐 필요한가?"
├─ Mock data 구조 확인
└─ Error response format 검증

CO-REVIEW 3: Security Auditor
├─ "이거 secure하게 구현되었나?"
├─ Input validation 확인
└─ Secret handling 검증

→ Dev Lead가 feedback 통합
→ Merge 전 모두 sign-off 필요
```

---

## 🤖 **Model Strategy**

### **Default: Haiku 4.5 (Fast, Cost-Effective)**

```
Phase -1 (Research): Haiku ✓
Phase 0 (Planning): Haiku ✓
Phase 1 (Requirement): Haiku ✓
Phase 2 (Documentation): Haiku ✓
Phase 3 (Design): Haiku ✓
Phase 4 (Development): Haiku ✓
Phase 5 (Testing): Haiku ✓
Phase 6 (Finalization): Haiku ✓
```

**Cost: 227K tokens → ~$0.68 (전체 6 프로젝트)**

### **Critical Phase Only: Sonnet 4.6 (Accurate, Comprehensive)**

**When Upgrade to Sonnet?**

```
✓ CRITICAL ONLY:
├─ Phase 1 Requirement (spec이 source of truth)
├─ Phase 2 Documentation (everyone relies on this)
├─ Phase 5 Security validation (security-critical)
├─ Phase 7 Final sign-off (before production)

❌ NEVER use for:
├─ Routine development
├─ Common documentation
├─ Unit testing
├─ Standard design review
```

**Sonnet Usage Example**:

```
프로젝트: "Payment Processing (중요)"

Phases -1 to 4: Haiku (비용 절감)
Phase 5 (Security): Sonnet (보안 critical)
Phase 6: Haiku
Phase 7 (Deploy): Sonnet (최종 검증)

Cost: 227K (Haiku 6개) → 60K (Haiku 5) + 45K (Sonnet 2) = 105K 추가
= 총 $0.91 (vs 무조건 Sonnet: $3.87 - 76% 절감)
```

---

## 📊 **Example: M-007 "회원가입 + OAuth"**

### **실행 흐름**

```
[14:00] Phase -1 START: Research
  Market Analyst (Haiku): OAuth provider 조사, 경쟁사 분석
  Architect (Haiku): 기존 auth 코드 분석
  Security (Haiku): OAuth security vulns 조사
  → [14:05] Complete: 3개 research doc

[14:05] Phase 0 START: Planning
  Business (Haiku): PRD 작성
  Architect (Haiku): Tech strategy 작성
  Dev Lead (Haiku): Feasibility review
  → [14:15] Complete: 3개 planning doc

[14:15] Phase 1 START: Requirement
  Business (Haiku): User stories (6개)
  Architect (Haiku): API spec 작성
  QA (Haiku): Test considerations
  → [14:30] Complete: 3개 requirement doc

[14:30] Phase 2 START: Documentation
  Doc Lead (Haiku): Design document 작성
  Architect (Haiku): Architecture decisions
  QA (Haiku): Test plan 작성
  Security (Haiku): Security spec
  → [14:50] Complete: 4개 doc artifact
  → [14:50] *CRITICAL PHASE* → Sonnet 검증 (1분)
    Sonnet: Spec completeness, consistency check
    → Approve or request revision

[14:50] Phase 3-4: Design + Development
  Dev Lead (Haiku): Backend implementation
  Frontend (Haiku): UI implementation
  QA (Haiku): Test code
  → [15:45] Complete: Working code

[15:45] Phase 5: Testing
  QA (Haiku): Run tests (all pass ✓)
  Security (Sonnet): OWASP validation (critical)
    → Check OAuth impl, token handling
    → Approve or request fix
  Dev (Haiku): Integration test ✓
  → [16:10] Complete: All tests pass

[16:10] Phase 6: Finalization
  Dev (Haiku): Final review
  Doc (Haiku): Final docs
  DevOps (Haiku): Deployment prep
  → [16:25] Ready for deploy

[16:25] Phase 7: Delivery
  Git: PR auto-created
  You: Review PR (5 min) → Approve
  Orchestrator (Sonnet): Final validation before deploy
    → Double-check critical logic
    → Approve deploy
  → [16:30] Deployed ✓

Total time: 90 min (vs 3-4 hours manual)
Token cost: 45K (Haiku) + 30K (Sonnet) = 75K
Quality: 100% (multiple reviews)
```

---

## 🎯 **Success Criteria**

| Metric | Target | Method |
|--------|--------|--------|
| **Documentation completeness** | 100% | Coverage check |
| **Agent reviews per artifact** | 2-3 | Review log |
| **Spec compliance** | 100% | Code = spec translation |
| **Test coverage** | 80%+ | Coverage report |
| **Security scan** | 0 critical | Automated scan |
| **Model efficiency** | 75% Haiku, 25% Sonnet | Token tracking |
| **Overlap catch rate** | 95% | Issue detection |

---

## 💡 **Key Benefits**

```
✓ Spec-First:
  ├─ Source of truth = documentation
  ├─ Code changes = doc changes
  └─ No surprise re-work

✓ Doc-First:
  ├─ Architecture clear before coding
  ├─ APIs frozen early
  └─ Testing starts parallel to dev

✓ Review-Heavy:
  ├─ 2-3 agents review each artifact
  ├─ Bugs caught early
  └─ Knowledge shared

✓ Cost-Effective:
  ├─ Haiku default (75% of time)
  ├─ Sonnet only critical (25%)
  └─ 76% cost reduction vs all-Sonnet

✓ Speed:
  ├─ Parallel phases where possible
  ├─ No rework from missed requirements
  └─ 50-60% faster than sequential
```

---

**Version**: v4.0 | **Status**: Ready for implementation | **Mode**: Spec-First, Doc-First, Review-Heavy