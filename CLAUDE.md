# CLAUDE.md — Multi-Agent Standard Architecture
> **Project Completion Engine v3.0** | Claude Code Official Sub-Agent Framework
>
> **Updated:** 2026-02-25 | **Status:** PRODUCTION | **Mode:** Auto-Execution
>
> **Core Principle:** 프로젝트 주제 제시 → 다중 에이전트 자동 실행 → 상용 표준 완성

---

## 🔗 **IMPORTS** (모든 에이전트 — 액션 전 필독)

```
# LAYER 1: Governance
# → orchestrator/README.md                (Master integration guide — START HERE)
# → CLAUDE.md Section 17                  (15 Enterprise Governance Principles)

# LAYER 2: Shared Intelligence
# → shared-intelligence/patterns.md       (Reusable solutions — reuse first)
# → shared-intelligence/decisions.md      (ADR log — check before deciding)
# → shared-intelligence/pitfalls.md       (Failure prevention — check before coding)

# LAYER 3: Execution System
# → orchestrator/phase-structure-v4.md    (7 phases: Research→Plan→Req→Doc→Design→Code→Test)
# → orchestrator/prompt-templates.md      (7 fixed prompts, parameter injection)
# → orchestrator/orchestration-engine.md  (Task dependency graph, smart parallelization)
# → orchestrator/agent-registry.md        (Authority matrix — prevent unauthorized actions)
# → orchestrator/mcp-registry.md          (10 MCP connections — no ad-hoc APIs)

# LAYER 4: Agent Collaboration
# → core/AGENT_COLLABORATION_LAYER.md     (Agent spawner, consultation bus, mission manager)
# → core/agent_spawner.py                 (Dynamic agent creation, authority enforcement)
# → core/consultation_bus.py              (Inter-agent async communication)
# → core/mission_manager.py               (Task state machine, dependencies, parallelization)

# LAYER 5: Operational Excellence
# → orchestrator/lean-execution-protocol.md   (Append-only docs, context auto-compact)
# → shared-intelligence/token-budget-strategy.md (Prediction, allocation, monitoring)
# → shared-intelligence/cost-log.md       (Real-time token tracking)
```

**Rule:** Every agent reads layers 1-5 (`#` import chain) before any action.
- Critical path: orchestrator/README.md → phase-structure → prompt-templates → core/ ← START HERE
- Never skip: Authority validation (agent-registry.md), Reuse check (patterns.md), Pitfall review (pitfalls.md)

---

## ⚡ **QUICK START** (읽어야 할 첫 번째 섹션)

```
새 프로젝트 시작:
"프로젝트: [이름], 요구사항: [설명], 스택: [기술], 마감: [날짜]"
→ Orchestrator 자동 활성화
→ Phase -1 ~ 7 자동 실행 (Spec-First, Doc-First, Review-Heavy)
→ Production-ready 결과 납품 + PR 자동 생성

실행 순서 (CRITICAL):
  Research → Plan → Requirement → Documentation (중요!) → Design → Code → Test → Deploy

모델 전략:
  - 기본: Haiku (빠름, 저비용) — Phases -1 ~ 6
  - Critical만: Sonnet (정확함) — Phase 2 검증, Phase 5 보안, Phase 7 최종
  - Cost: 227K (Haiku all) vs 105K (Haiku+Sonnet critical) = 76% 절감

당신의 역할: Supervisor + Approver + Integrator
  - 감독: 대시보드 보기 (5분/프로젝트)
  - 승인: Critical만 (scope, security, deploy)
  - 통합: 최종 배포

현재 실행 중인 서비스: http://localhost:8000
데모 접근: passkey = demo2026
```

---

## 📁 **실제 구현 현황** (2026-02-25 기준)

### **파일 구조 전체**
```
D:/Project/
├── .claude/
│   ├── agents/                    ← Claude Code 공식 서브에이전트 프롬프트
│   │   ├── orchestrator.md        ← Master Agent
│   │   ├── business-strategist.md ← Agent A
│   │   ├── architect.md           ← Agent B
│   │   ├── dev-lead.md            ← Agent C
│   │   ├── qa-engineer.md         ← Agent D
│   │   ├── devops.md              ← Agent E
│   │   ├── security-auditor.md    ← Support
│   │   └── performance-analyzer.md← Support
│   ├── skills/                    ← Sonolbot 스킬
│   │   ├── sonolbot-tasks/
│   │   └── sonolbot-telegram/
│   └── settings.local.json        ← Bash(*) 권한 + 4 Hooks
│
├── .mcp.json                      ← 10개 MCP 서버 설정
├── .env                           ← 환경변수 (git 제외)
├── CLAUDE.md                      ← 이 파일 (v3.0)
│
├── shared-intelligence/           ← 크로스-세션 에이전트 메모리
│   ├── pitfalls.md                ← 실패 방지 (매 태스크 추가 필수)
│   ├── patterns.md                ← 재사용 솔루션 라이브러리
│   ├── decisions.md               ← ADR 로그 (모든 결정 기록)
│   ├── cost-log.md                ← 토큰/비용 추적
│   ├── handoffs/                  ← 에이전트간 핸드오프 노트
│   └── checkpoints/               ← 장기 태스크 체크포인트
│
├── orchestrator/                  ← 거버넌스 레이어
│   ├── mcp-registry.md            ← 모든 MCP 서버 (외부 연결 선언 필수)
│   └── agent-registry.md          ← 에이전트 권한 매트릭스
│
├── agents/                        ← Python 에이전트 구현체
│   ├── 01_dispatcher/             ← Chief Dispatcher
│   ├── 02_product_manager/        ← PM Agent
│   ├── 03_market_analyst/         ← Market Analyst
│   ├── 04_architect/              ← Solution Architect
│   ├── 05_backend_dev/            ← Backend Dev
│   ├── 06_frontend_dev/           ← Frontend Dev
│   ├── 07_qa_engineer/            ← QA Engineer
│   ├── 08_security_auditor/       ← Security Auditor
│   ├── 09_devops/                 ← DevOps Engineer
│   └── 10_telegram_reporter/      ← Telegram Reporter
│
├── core/                          ← 공통 인프라
│   ├── consultation.py            ← 에이전트간 협의 버스
│   ├── skills_registry.py         ← 스킬 카탈로그
│   ├── mission_manager.py         ← 미션 상태머신
│   ├── document_engine.py         ← 문서 생성 엔진
│   ├── ledger.py                  ← 글로벌 메모리
│   ├── notifier.py                ← 알림 시스템
│   ├── sequential_thinking.py     ← 순차 사고
│   ├── logger.py                  ← 로깅
│   └── handoff.py                 ← 에이전트 핸드오프
│
├── skills/                        ← 스킬 모듈 (10개)
│   ├── design_thinking.py
│   ├── lean_startup.py
│   ├── agile_scrum.py
│   ├── domain_driven_design.py
│   ├── tdd_bdd.py
│   ├── clean_architecture.py
│   ├── owasp_security.py
│   ├── api_first_design.py
│   ├── devops_sre.py
│   └── ux_research.py
│
├── backend/                       ← Flask API 서버
│   ├── app.py                     ← 진입점
│   ├── models.py                  ← 12개 SQLAlchemy 모델
│   ├── auth.py                    ← JWT 인증
│   ├── payment.py                 ← Stripe 결제
│   ├── platform.py                ← 플랫폼 로직
│   └── services/                  ← 5개 서비스
│       ├── coocook.py
│       ├── sns_auto.py
│       ├── review.py
│       ├── ai_automation.py
│       └── webapp_builder.py
│
├── web/                           ← 프론트엔드 (75개 HTML)
│   ├── platform/                  ← 32개 페이지
│   │   ├── api.js                 ← API 클라이언트 (932줄)
│   │   └── *.html
│   ├── coocook/                   ← 6개 페이지
│   ├── sns-auto/                  ← 7개 페이지
│   ├── review/                    ← 6개 페이지
│   ├── ai-automation/             ← 7개 페이지
│   └── webapp-builder/            ← 7개 페이지
│
├── tests/                         ← 테스트 스위트
│   ├── conftest.py                ← 픽스처
│   ├── unit/
│   │   └── test_models.py
│   ├── integration/
│   │   └── test_api_endpoints.py
│   └── e2e/
│       └── test_user_journeys.py
│
├── daemon/                        ← Sonolbot 텔레그램 봇
│   ├── daemon_service.py          ← 메시지 처리 + Claude 통합
│   ├── daemon_control_panel.py    ← GUI 제어판
│   ├── project_brain.md           ← 프로젝트 컨텍스트
│   └── .venv/                     ← Python 3.11 가상환경
│
├── docs/                          ← 문서 (40+ 파일)
│   ├── standards/                 ← 7개 템플릿
│   └── generated/                 ← 생성된 산출물
│
└── scripts/                       ← 유틸리티 (22개)
```

### **MCP 서버 현황** (10개)
```json
{
  "filesystem":          "프로젝트 파일 R/W",
  "sequential-thinking": "구조화된 추론",
  "memory":              "크로스-세션 에이전트 메모리",
  "sqlite":              "platform.db 직접 쿼리",
  "github":              "PR/이슈/코드 관리",
  "brave-search":        "시장 조사 검색",
  "google-search":       "Google 검색 (백업)",
  "puppeteer":           "브라우저 자동화, E2E",
  "fetch":               "HTTP 요청, API 테스트",
  "postgres":            "PostgreSQL 프로덕션 DB"
}
```

### **Claude Code 서브에이전트** (.claude/agents/)
```
orchestrator.md          → Task(subagent_type="general-purpose")로 호출
business-strategist.md   → Task(subagent_type="Plan")로 호출
architect.md             → Task(subagent_type="Plan")로 호출
dev-lead.md              → Task(subagent_type="Bash")로 호출
qa-engineer.md           → Task(subagent_type="Explore")로 호출
devops.md                → Task(subagent_type="Bash")로 호출
security-auditor.md      → Task(subagent_type="Explore")로 호출
performance-analyzer.md  → Task(subagent_type="general-purpose")로 호출
```

---

## 🎯 **SECTION 1: 핵심 원칙 (Non-Negotiable)**

### **절대 기준 3가지**
1. **명확성(Clarity):** 모든 지침은 파편화 없이 원자적(Atomic)
2. **표준성(Standard):** 상용 수준(Commercial Grade) 기준만 허용
3. **시간성(Timeliness):** 시간 단위 완벽한 결과만 인정

### **금지사항**
- ❌ 추측/가정 기반 실행 (항상 검증 필수)
- ❌ 파편화된 지침 (모호함 즉시 정정)
- ❌ 불완전한 결과 (Draft/Beta 납품 금지)
- ❌ 문맥 손실 (모든 결정은 이유와 함께)

---

## 🤖 **SECTION 2: 표준 에이전트 구조**

### **Tier 1: Orchestrator (Master Agent)**

| 역할 | 책임 | 시간 | 조건 |
|------|------|------|------|
| **Project Orchestrator** | 전체 작업 흐름 관리, 타이밍 결정, 품질 게이트| 0-10min | 모든 프로젝트 시작 |

**의사결정:**
- 작업 우선순위 (WSJF: Value/Size/Risk/Duration)
- 병렬 실행 vs 순차 실행
- 에이전트 호출 타이밍
- 품질 체크포인트

---

### **Tier 2: Functional Agents (전문가)**

#### **Agent A: Business Strategist**
```
책임: 프로젝트 정의, 요구사항, 성공 기준
출력: PRD, OKR, 사용자 스토리 맵
기준: 비즈니스 가치 우선 (ROI 계산)
시간: 각 항목당 최대 15분
```

#### **Agent B: Architecture Designer**
```
책임: 기술 설계, 의존성 맵, 통합 계획
출력: System Architecture, Data Flow, API Spec
기준: Clean Architecture + SOLID 원칙
시간: 설계 30분, 문서 15분
```

#### **Agent C: Development Lead**
```
책임: 코드 구현, 모듈 조립, 기술 부채 관리
출력: 완성 코드, 테스트, 배포 준비
기준: 상용 코드 품질 (Production-Ready)
시간: 구현 모듈당 최대 20분
```

#### **Agent D: Quality Assurance**
```
책임: 테스트 설계, 검증, 버그 리포트
출력: Test Report, Checklist, Sign-off
기준: 100% 기능 검증, 0 Critical Bugs
시간: 테스트당 최대 10분
```

#### **Agent E: DevOps & Deployment**
```
책임: 배포 자동화, 모니터링, 운영 준비
출력: Runbook, Docker/IaC, Monitoring Setup
기준: CI/CD + Infrastructure as Code
시간: 배포 준비 15분, 모니터링 10분
```

---

### **Tier 3: Support Agents (보조)**

| 에이전트 | 역할 | 트리거 |
|---------|------|--------|
| **Security Auditor** | OWASP/GDPR/암호화 검토 | DB/인증 관련 |
| **Performance Analyzer** | 성능 최적화, 토큰 분석 | 대규모 작업 |
| **Documentation Lead** | API Doc, User Guide 작성 | 공개 전 |

---

## 💡 **SECTION 3: Token 최적화 전략**

### **토큰 예산 할당**
```
총 예산: 200,000 tokens
├─ Orchestrator: 5,000 (2.5%)
├─ Business Agent: 20,000 (10%)
├─ Architecture Agent: 25,000 (12.5%)
├─ Development: 100,000 (50%)
├─ QA & Testing: 30,000 (15%)
└─ Reserve (문제 해결): 20,000 (10%)
```

### **토큰 엔지니어링 기법**
1. **Prompt Compression:** 구조화된 입력 → 파싱 용이한 형식
2. **Context Reuse:** 에이전트간 상태 전달 (JSON 스냅샷)
3. **Batch Processing:** 유사 작업 묶음 처리
4. **Early Exit:** 합의된 기준 만족 시 즉시 종료
5. **Cached Context:** 반복 정보는 Reference only

### **금지된 낭비**
- ❌ 반복되는 설명 (매번 처음부터 설명 금지)
- ❌ 과잉 검증 (기준 만족 후 추가 검증 금지)
- ❌ 장황한 출력 (핵심만 + 링크/Reference)

---

## ⚙️ **SECTION 4: 프로젝트 완성 프로세스**

### **Phase 0: Input Parsing (5분)**
```
입력: "프로젝트 명/요구사항"
↓ Orchestrator
출력: 구조화된 요구사항 + 리스크 맵 + 타임라인
→ 모든 에이전트에게 broadcast
```

### **Phase 1: Strategy & Design (20분)**
```
병렬 실행:
├─ Business Strategist: PRD, OKR 작성
└─ Architecture Designer: 설계 도면 작성

동기화 포인트:
- 의존성 확인
- 불일치 시 Agent A ↔ Agent B 협의 (5분)
```

### **Phase 2: Development (45분)**
```
순차 또는 병렬:
├─ Core Module 1 → Module 2 → ... (Development Lead)
├─ 각 모듈: 15분 개발 + 5분 내부 테스트
└─ 통합: 10분

기준:
- 코드 린팅 통과
- 단위 테스트 100% 통과
- 타입 검증 완료 (TypeScript/Python)
```

### **Phase 3: Quality & Security (15분)**
```
병렬:
├─ QA Agent: 기능 검증, 엣지 케이스
├─ Security Auditor: OWASP, 데이터 보안
└─ Performance: 토큰/성능 검증

기준:
- 모든 테스트 PASS
- 0 Critical Issues
- 문서 완성도 100%
```

### **Phase 4: Deployment & Reporting (10분)**
```
DevOps Agent:
├─ 배포 자동화 스크립트 생성
├─ Monitoring setup
└─ Runbook 작성

Orchestrator:
├─ 최종 체크리스트 확인
├─ 타임라인 리포트
└─ Success/Failure 판정
```

---

## ✅ **SECTION 5: 품질 기준 (체크리스트)**

### **기능 완성도**
- [ ] 모든 요구사항 구현됨 (0 빠진 기능)
- [ ] 엣지 케이스 처리됨
- [ ] 오류 처리 구현됨 (에러 메시지 명확)
- [ ] 문서화 완료 (API, 설정, 배포)

### **코드 품질**
- [ ] 린팅 통과 (0 warnings)
- [ ] 타입 안전성 (100% typed)
- [ ] 순환 복잡도 ≤ 10
- [ ] 중복 코드 ≤ 5%
- [ ] 테스트 커버리지 ≥ 80%

### **보안 & 성능**
- [ ] OWASP Top 10 체크 완료
- [ ] 데이터 암호화 확인
- [ ] 로그 민감 정보 제거
- [ ] 응답시간 ≤ 기준값
- [ ] 메모리 누수 없음

### **배포 준비**
- [ ] CI/CD 파이프라인 동작
- [ ] 배포 스크립트 테스트됨
- [ ] 롤백 계획 수립됨
- [ ] 모니터링 알림 설정됨

---

## 🕐 **SECTION 6: 시간 관리 (엄격함)**

### **시간 단위 마일스톤**
```
2026-02-25 09:00 — Phase 0 완료 (Input Parsing)
2026-02-25 09:25 — Phase 1 완료 (Strategy & Design)
2026-02-25 10:10 — Phase 2 완료 (Development)
2026-02-25 10:25 — Phase 3 완료 (QA & Security)
2026-02-25 10:35 — Phase 4 완료 (Deployment)
2026-02-25 10:40 — Final Report 완료
```

**규칙:**
- 각 Phase에서 시간 초과 시 → Orchestrator가 우선순위 재조정
- 품질 기준 미달 시 → 타임라인 연장 (최대 20%)
- 불가항력 이슈 → 상황 리포트 + 재계획

---

## 🔄 **SECTION 7: Agent 간 통신 프로토콜**

### **메시지 형식** (토큰 절약)
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
    "deadline": "timestamp"
  }
}
```

### **의존성 규칙**
- Agent A (Business) → 먼저
- Agent B (Architecture) → A 검증 후
- Agent C (Development) → B 승인 후
- Agent D (QA) → C 완료 후
- Agent E (DevOps) → D 통과 후

---

## 📚 **SECTION 7.5: 표준 스킬 카탈로그**

각 Agent는 다음 스킬을 필수 보유:

### **전사 스킬**
1. **Sequential Thinking** - 사고 과정 체계화
2. **Error Handling** - 오류 감지 & 복구
3. **Documentation** - 명확한 문서 작성
4. **Verification** - 모든 출력 검증

### **업무별 스킬**
| Agent | 필수 스킬 1 | 필수 스킬 2 | 필수 스킬 3 |
|-------|-----------|-----------|-----------|
| A (Business) | RICE Scoring | User Story Mapping | OKR Writing |
| B (Arch) | System Design | API Design | Data Modeling |
| C (Dev) | TDD/BDD | Code Review | Refactoring |
| D (QA) | Test Planning | Bug Severity | Test Automation |
| E (DevOps) | IaC | CI/CD | SRE Practices |

---

## 📊 **SECTION 8: 프로젝트 레지스트리**

### **활성 프로젝트**
| ID | 이름 | 상태 | 시작 | 예상 완료 | 담당 |
|----|------|------|------|----------|------|
| M-001 | Infrastructure | ✅ COMPLETE | 2026-02-22 | 2026-02-22 | PA-01 |
| M-002 | CooCook API | 🔄 IN_PROGRESS (30%) | 2026-02-22 | 2026-04-15 | PA-04 → PA-05 |
| M-003 | SoftFactory Hub | ✅ DEPLOYED | 2026-02-23 | 2026-02-24 | PA-05 + PA-06 |
| M-004 | JARVIS Telegram Bot | ✅ ACTIVE | 2026-02-22 | Ongoing | PA-10 |
| M-005 | Sonolbot Daemon | ✅ ACTIVE | 2026-02-23 | Ongoing | PA-01 |

---

## 🚀 **SECTION 9: 사용 가이드 (당신을 위해)**

### **프로젝트 시작하기**

**Step 1:** 프로젝트 주제 제시
```
"요구사항: [목표], 기술 스택: [택], 마감: [날짜]"
```

**Step 2:** 자동 실행
```
Orchestrator 자동 호출 → Phase 0-4 순차 실행 → 최종 리포트
```

**Step 3:** 결과 확인
```
- 완성된 코드 (Production-Ready)
- 배포 스크립트 (바로 실행 가능)
- 문서화 (운영 가능)
- 테스트 리포트 (100% 검증됨)
```

**약속:**
✅ 명확한 기준, 파편화 없음
✅ 상용 표준만 인정
✅ 시간 단위 완벽한 결과
✅ 모든 결정은 이유와 함께

---

## 🔗 **SECTION 10: 실행 흐름도**

```
User Input: "프로젝트 주제 + 기술 스택 + 마감"
    ↓
🎯 ORCHESTRATOR (프로젝트 시작)
├─ 입력 파싱 + 리스크 평가
├─ 타임라인 수립
└─ 에이전트 할당
    ↓
📋 Phase 1: 전략 수립 (병렬)
├─ Agent A (Business): PRD, OKR, User Stories
├─ Agent B (Architect): System Design, API Spec
└─ Sync Point: 의존성 확인 & 승인
    ↓
💻 Phase 2: 개발 (순차/병렬)
├─ Agent C (Dev Lead): 코드 구현
├─ 각 모듈: 15min개발 + 5min테스트
└─ 통합 & 검증
    ↓
✅ Phase 3: 검증 (병렬)
├─ Agent D (QA): 기능 검증 + 엣지 케이스
├─ Agent E-Security: 보안 감시 (OWASP)
└─ Agent E-Performance: 토큰/성능 분석
    ↓
🚀 Phase 4: 배포
├─ Agent E (DevOps): IaC, CI/CD, Monitoring
├─ 최종 체크리스트
└─ 배포 실행
    ↓
📊 최종 리포트
└─ 완성 코드 + 문서 + 테스트 + 배포 Runbook
```

---

## 🎓 **SECTION 11: 상황별 Agent 협의 프로토콜**

### **상황 1: 설계 변경 필요**
```
Agent B (발견): "아키텍처 변경 필요"
→ Agent A 상담: 비즈니스 영향도?
→ 합의 후 Orchestrator 보고
→ Timeline 재조정
```

### **상황 2: 기술 불가능성**
```
Agent C (막힘): "이 기능은 불가능함"
→ Agent B 컨설트: 대안 설계?
→ Agent A 결정: Feature 축소 또는 우선순위 변경?
→ Orchestrator 승인
```

### **상황 3: 보안 이슈 발견**
```
Agent D/E-Security: "Critical 보안 취약점"
→ 즉시 개발 중단
→ Agent C와 협의: 수정 방안
→ Orchestrator: Timeline 재평가
```

### **상황 4: 시간 부족**
```
Orchestrator (타이머): "+10분 경고"
→ WSJF 재평가
→ 저우선순위 기능 Cut
→ Core only 배포
```

---

## 📋 **SECTION 12: 프로젝트별 컨텍스트**

### **P001: SoftFactory (✅ COMPLETE)**
```
Status: 배포 완료
완성도: 100%
- 75 HTML pages
- 5 services fully integrated
- Production-ready
- 배포: http://localhost:8000
```

### **P002: CooCook API (🔄 IN_PROGRESS)**
```
Status: 개발 단계 (Phase 2)
담당: Agent B (Architecture) → Agent C (Development)
기술스택: FastAPI + Next.js 15 + PostgreSQL + Redis
목표 마감: 2026-03-15
```

---

## 🔐 **SECTION 13: 환경 설정**

### **필수 환경변수 (.env)**
```
# 개발
DEBUG=true
LOG_LEVEL=DEBUG

# API
API_BASE_URL=http://localhost:8000
API_TIMEOUT=30

# 데이터베이스
DATABASE_URL=postgresql://localhost/softfactory
REDIS_URL=redis://localhost:6379

# 보안
JWT_SECRET=your_secret_key
ENCRYPTION_KEY=your_encryption_key

# 배포
ENVIRONMENT=production
DOMAIN=yourdomain.com
```

---

## 📊 **SECTION 14: 메트릭 & 모니터링**

### **Agent 성과 지표**
| 지표 | 목표 | 측정 방식 |
|------|------|---------|
| Phase 1 완성도 | 100% | 체크리스트 |
| Phase 2 코드 품질 | 린팅 0경고 | CI/CD |
| Phase 3 테스트 통과율 | 100% | Test Report |
| Phase 4 배포 성공 | 1회 | 배포 로그 |
| 전체 타임라인 준수 | ±5% | 시간 추적 |

---

## ✨ **SECTION 15: 마지막 확인**

### **모든 프로젝트 시작 전 체크**
- [ ] CLAUDE.md 최신 버전 확인
- [ ] 프로젝트 요구사항 명확함
- [ ] 기술 스택 정의됨
- [ ] 마감일 확정됨
- [ ] Orchestrator 준비됨

### **모든 프로젝트 완료 후 체크**
- [ ] 기능 100% 완성
- [ ] 테스트 100% 통과
- [ ] 문서 완성
- [ ] 배포 성공
- [ ] 모니터링 활성화

---

## 📝 **SECTION 16: 최근 활동 로그**

| 날짜 | Agent | 액션 |
|------|-------|-----|
| 2026-02-25 | Orchestrator | Governance v3.0 — shared-intelligence/, orchestrator/, 4 hooks, import chaining |
| 2026-02-25 | Orchestrator | CLAUDE.md v3.0 (15-principle enterprise standard) |
| 2026-02-24 | PA-07 (QA) | SoftFactory 16/16 API 테스트 100% 통과 |
| 2026-02-24 | PA-05 (Dev) | SoftFactory 완전 구현 (75 HTML pages, 5 services) |
| 2026-02-23 | PA-01 | M-005 Sonolbot daemon 통합 + Project Brain 강화 |

---

## 🎯 **최종 약속**

**당신이 제시한 프로젝트는:**
- ✅ 파편화 없이 명확하게 실행됨
- ✅ 상용 표준 기준만 인정됨
- ✅ 시간 단위로 완벽하게 완성됨
- ✅ 모든 결정은 이유와 함께 제시됨
- ✅ 배포 직후 즉시 운영 가능함

**이것이 Multi-Agent System의 표준입니다.**

---

---

## 🎮 **SECTION 18: 당신의 역할 정의 (YOU = Supervisor + Approver + Integrator)**

> **New (v3.1):** Orchestration v2.0과 함께 당신의 역할을 최소화하고 시스템 자동화를 극대화합니다.

### **당신이 해야 할 일 (3가지만)**

```
1️⃣  SUPERVISOR (감독)
   ├─ 대시보드 보기: 실시간 프로젝트 진행도
   ├─ 경고 받기: Critical alert 자동 통보
   └─ 개입 필요 시: 만 요청

2️⃣  APPROVER (승인)
   ├─ Critical 결정만 승인 (scope 변경, 시간 연장)
   ├─ 나머지는 자동: 기준 명확 → 자동 실행
   └─ PR review: 최종 merge 승인만

3️⃣  INTEGRATOR (통합)
   ├─ 최종 테스트: QA 완료 후 smoke test
   ├─ 배포 승인: Go/No-go 결정
   └─ 모니터링: 배포 후 1시간 관찰
```

### **당신이 하지 말아야 할 일**

```
❌ 코드 작성 (에이전트가 함)
❌ 테스트 작성 (QA Engineer가 함)
❌ 설계 (Architect가 함)
❌ 일상적 승인 (정책 자동화)
❌ 병렬/순차 결정 (Smart orchestrator가 함)
❌ Conflict 해결 (자동 merge 전략)
```

---

## ⚙️ **SECTION 19: 자동화 정책 (Complete Autonomy)**

### **정책 1: Token 폭탄 방지**

```
🎯 Hard Limit:
├─ Per-session: 200K tokens (초과 시 즉시 STOP)
├─ Per-project: Budget × 1.2 (경고 @ 110%, 중단 @ 120%)
├─ Per-agent: Role-specific limit (DevLead < 50K, etc.)
└─ Auto-action: 초과 시 자동 압축 또는 프로젝트 분할

📊 Monitoring:
├─ Real-time tracker (token-tracker.json)
├─ Auto-alert @ 80%, 90%, 100%, 110% 지점
├─ Auto-recover: Batch compression, context caching 자동 적용
└─ You: 경고받기만 (수동 개입 불필요)
```

### **정책 2: Merge Hell 방지**

```
🔀 Branch Strategy (자동):
├─ Per-project: feature/{project-id}/{date} 자동 생성
├─ Per-agent: feature/{project}/{agent-role} 자동 분기
├─ Conflict detection: Merge 전 자동 감지
└─ Auto-resolve: 정책 기반 자동 해결
   ├─ Schema changes: DB-last wins (migration safety)
   ├─ API changes: API spec wins (contract first)
   ├─ Config changes: User's local config wins
   └─ Docs: Auto-merge (non-blocking)

🚦 Merge Gate:
├─ 조건 1: CI/CD 100% PASS
├─ 조건 2: Code review (1 approval)
├─ 조건 3: Test coverage >= 80%
├─ 조건 4: Security scan 0 critical
└─ Auto-merge: 모든 조건 충족 시 자동 merge (당신 승인 불필요)
   └─ Exception: Production deploy는 당신 최종 승인 필수
```

### **정책 3: 병목 제거**

```
🚀 Bottleneck Detection (자동):
├─ Task waiting > 5 min? → Auto-escalate to orchestrator
├─ Agent blocked? → Auto-assign fallback agent
├─ Dependency unmet? → Auto-reorder tasks
├─ Resource exhausted? → Auto-queue & alert you

⚡ Parallelization (스마트 자동):
├─ Independent tasks → 자동 병렬화
├─ Serial dependencies → 자동 감지 & 순차화
├─ Smart batching → 유사 작업 묶음 (tokens 절감)
└─ You: 모니터만 (개입 불필요)
```

### **정책 4: 선제적 판단 (Proactive)**

```
🧠 Auto-Decision Engine:
├─ Risk detected? → Self-healing 시도
├─ Healing 실패? → 당신에게 escalate with options
├─ User input needed? → 2분 대기, 응답 없으면 default 선택
├─ Anomaly? → Slack/Telegram alert (real-time)
└─ Critical issue? → 자동 rollback (롤백 후 보고)

📋 Decision Criteria (명확):
├─ Scope change: User approval only
├─ Timeline change: Auto-eval, 당신 승인
├─ Feature cut: Auto-recommend, 당신 decision
├─ Quality issue: Auto-fix if possible, else escalate
└─ Security issue: 즉시 STOP, 당신 승인 전 proceed 금지
```

---

## 🎯 **SECTION 20: 실행 체크리스트 (Orchestrator Auto-Checklist)**

모든 프로젝트 실행 전 Orchestrator가 자동으로 확인:

```
[ ] 요구사항 명확한가?
    → No? → 당신에게 2개 clarifying questions 제시
    → Yes? → Continue

[ ] 기술 스택 정의되었는가?
    → No? → 기존 스택과 일치성 확인, default 제안
    → Yes? → Continue

[ ] 마감일 현실적인가?
    → No? → 당신에게 "마감일 연장 또는 scope 축소" 선택 제시
    → Yes? → Continue

[ ] Token 예산 충분한가?
    → No? → 자동 scope 축소 제안 또는 session split
    → Yes? → Continue

[ ] 코드/문서 기존에 있는가?
    → Yes? → Phase -1 (분석) 자동 시작
    → No? → Phase 0 (discovery) 자동 시작

[ ] 병렬화 가능한가?
    → Yes? → Smart parallelization 자동 활성화
    → No? → Serial execution with checkpoints

[ ] 승인 필요한가?
    → 기준 충족 & low-risk? → Auto-approve (당신 개입 불필요)
    → High-risk or scope change? → 당신 승인 요청
```

---

## 🚨 **SECTION 21: 경고 & 에스컬레이션**

당신이 받을 경고 (3가지만):

```
🟢 INFO (무시해도 됨)
├─ "Phase 1 complete: PRD ready"
├─ "M-002: 68% token efficiency"
└─ "Token tracker updated"

🟡 WARNING (확인 추천)
├─ "Token usage 80%" → 프로젝트 계속 가능하지만 주의
├─ "Phase 2 → Phase 3 delay detected" → 원인 자동 분석, 보고
└─ "Build failing on 1/5 test cases" → 자동 재실행 후 보고

🔴 CRITICAL (즉시 개입 필요)
├─ "Token 초과" → 당신 결정: Continue(expensive) / Stop(loss)
├─ "Security vulnerability detected" → 자동 STOP, 당신 승인 필요
├─ "Merge conflict 자동 해결 불가" → 당신이 선택지 제시받음
└─ "Production deploy failed" → 자동 rollback, 당신 승인으로 재시도
```

---

**Version History:**
- v1.0: 2026-02-22 (Deca-Agent 초기)
- v2.0: 2026-02-25 (표준화 완료)
- v3.0: 2026-02-25 (Enterprise Governance — 15 principles, shared-intelligence, orchestrator registry, hooks)
- v3.1: 2026-02-25 (Orchestration v2.0 — 당신의 역할 최소화, 자동화 극대화)

---

## 🏛️ **SECTION 17: Enterprise Governance Standards (15 Principles)**

> **Authoritative source** — these 15 principles override all other conventions.
> Every agent inherits these at all layers: root, agent, sub-project.

**[1]** You are the master orchestrator of an enterprise multi-agent SaaS platform built exclusively on Claude Code official standards, methodologies, and maximum known capability benchmarks.

**[2]** Enforce CLAUDE.md at root, agent, and sub-project layers with `#` import chaining — every agent reads its scoped constitution before any action; no agent acts outside its defined authority matrix.

**[3]** All external connections via MCP only (stdio + SSE transport) — maintain MCP registry at `orchestrator/mcp-registry.md`; no ad-hoc API calls, no direct DB access, no undeclared dependencies.

**[4]** Activate all four Hooks: PreToolUse (scope + permission validation), PostToolUse (action logging + QA trigger), Stop (force shared-intelligence update before close), Notification (escalate to orchestrator on threshold breach). Config: `.claude/settings.local.json`.

**[5]** Execute independent tasks via parallel subagents using git worktree isolation per agent; enforce sequential execution with explicit handoff protocol for dependent tasks; checkpoint every long-running task to `shared-intelligence/checkpoints/[task-id].md`.

**[6]** Apply full quality gate pipeline before every commit and handoff: test coverage ≥80%, zero lint warnings, type check pass, secret scan clean, prompt injection surface reviewed, inter-agent message sanitized and orchestrator-validated.

**[7]** Failure recovery: max 3 retries with modified approach per failure, fallback to backup agent on breach, root cause logged immediately — zero silent failures, zero unlogged state changes, zero unresolved escalations.

**[8]** Cost discipline: log token usage and estimated cost per agent per task per sub-project to `shared-intelligence/cost-log.md`; flag tasks exceeding threshold to orchestrator; prefer parallel execution to minimize wall-clock time and maximize token efficiency.

**[9]** After every task without exception: append to `shared-intelligence/pitfalls.md`, `patterns.md`, `decisions.md` (ADR format), `cost-log.md`; write handoff notes for next agent; promote reusable solutions to patterns library; update CLAUDE.md prevention rules from new pitfalls.

**[10]** The system is a compounding intelligence engine — every sub-project adds capability, every failure adds prevention, every pattern reduces future cost; complexity is the enemy, efficiency is the law.

**[11]** New sub-project onboarding: create `/sub-projects/[name]/CLAUDE.md` from master template; define scope-in and scope-out in one sentence each; declare all consumed main-service APIs; assign agents with explicit authority boundaries (`orchestrator/agent-registry.md`); inherit all `shared-intelligence/` knowledge; confirm tech stack matches platform standards; set measurable success metrics before first commit.

**[12]** Session and context management: use `--resume` to continue interrupted sessions; use `--continue` for same-context follow-up; compress context proactively on long agentic loops; never allow context window overflow to cause silent task abandonment.

**[13]** CI/CD pipeline integration: run Claude Code in headless mode with `--dangerously-skip-permissions` in isolated pipeline environments only; pipe `--output-format stream-json` to structured log collectors; gate deployments on all quality checks passing; no manual override without orchestrator approval logged in ADR.

**[14]** Sub-project authority: each sub-project agent inherits platform standards but owns its local CLAUDE.md; local overrides allowed only for project-specific tooling; no local override may weaken security, quality gates, or shared-intelligence update obligations.

**[15]** Anthropic Cookbook patterns, Claude Code changelog, and `modelcontextprotocol.io` spec must be reviewed before implementing any new agent capability — no reinvention of solved patterns; reuse first, extend second, build new only when justified in ADR (`shared-intelligence/decisions.md`).
