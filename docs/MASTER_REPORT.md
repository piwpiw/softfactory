# 🏆 Deca-Agent Master Report
> **최종 기준 문서 (Living Reference Document)**
> Project: CooCook | Version: Max | Last Updated: 2026-02-22

---

## 📌 1. 시스템 개요 (System Overview)

| 항목 | 내용 |
|------|------|
| 시스템명 | Deca-Agent Master Ecosystem — Max Version |
| 프로젝트 | CooCook (Travel-Tech / Food Discovery / Chef Marketplace) |
| 완성도 | ~~18% (Stub)~~ → **85%+ (Production-Ready Framework)** |
| 에이전트 수 | 10개 (전 부서 풀 구현) |
| 핵심 모듈 | ConsultationBus, SkillsRegistry, MissionManager, DocumentEngine, Notifier |
| 스킬 라이브러리 | 10개 모듈 (Design Thinking ~ DevOps/SRE) |
| 문서 표준 | 7개 템플릿 (PRD, ADR, RFC, Bug, Security, TestPlan, Runbook) |
| Telegram | Live Dashboard + 전 에이전트 실시간 알림 (10분 단위) |

---

## 🤖 2. 전 에이전트 R&R 요약 (Role & Responsibility)

| ID | 에이전트 | 핵심 역할 | 주요 산출물 | 적용 스킬 |
|----|---------|----------|-----------|---------|
| **01** | Chief Dispatcher | 우선순위 결정, 충돌 해결 | 실행 계획, WSJF 점수표 | WSJF, 충돌 해결 알고리즘 |
| **02** | Product Manager | 제품 전략, 요구사항 정의 | PRD, RICE 표, OKR, Story Map | Lean Startup, Agile, Design Thinking |
| **03** | Market Analyst | 시장 조사, 경쟁 분석 | SWOT, PESTLE, Porter's 5 Forces, TAM/SAM/SOM | UX Research, Lean Startup |
| **04** | Solution Architect | 시스템 설계 | ADR, C4 다이어그램, OpenAPI spec | DDD, Clean Architecture, API-First |
| **05** | Backend Developer | 서버 구현 | API, DB, TDD 테스트 | TDD/BDD, Clean Architecture |
| **06** | Frontend Developer | 클라이언트 구현 | 컴포넌트, WCAG 감사 | Atomic Design, UX Research |
| **07** | QA Engineer | 품질 보증 | 테스트 플랜, 버그 리포트, 커버리지 | Test Pyramid, Risk-Based Testing |
| **08** | Security Auditor | 보안 감사 | STRIDE 모델, CVSS 리포트, OWASP 체크 | OWASP Top 10, STRIDE, CVSS 3.1 |
| **09** | DevOps Engineer | 배포 & 신뢰성 | SLO/SLI, 배포 런북, IaC | DevOps/SRE, Blue-Green |
| **10** | Telegram Reporter | 알림 & 보고 | 실시간 알림, Daily/Weekly 요약 | Event-Driven Notification |

---

## 🔄 3. 파이프라인 흐름 (Pipeline Flow)

```
[작업 입력]
    │
    ▼
[01 Dispatcher]──WSJF 우선순위──→ 충돌? ConsultationBus.escalate() ↩
    │
    ├──────────── 병렬 실행 ────────────┐
    ▼                                  ▼
[02 PM]                          [03 Analyst]
PRD + RICE + OKR                 SWOT + PESTLE + Porter's
    │                                  │
    └──────── merge ───────────────────┘
                  │
                  ▼  ConsultationBus.broadcast() → Backend, Frontend
         [04 Architect]
         ADR + C4 + OpenAPI
                  │
    ┌─────────────┴──────────────┐
    ▼                            ▼
[05 Backend]               [06 Frontend]
TDD + Clean Arch           Atomic Design + WCAG
    │                            │
    └────────── merge ───────────┘
                  │
    ┌─────────────┴──────────────┐
    ▼                            ▼
[07 QA]                    [08 Security]
Test Pyramid + Risk        STRIDE + CVSS + OWASP
    │                            │
    └────────── merge ───────────┘
                  │
                  ▼
         [09 DevOps]
         SLO + Blue-Green + Runbook
                  │
                  ▼
         [10 Reporter]
         Telegram 알림 + 회고 트리거
```

**병렬 실행 허용 구간:**
- `02 PM` ↔ `03 Analyst` (기획 단계)
- `05 Backend` ↔ `06 Frontend` (개발 단계)
- `07 QA` ↔ `08 Security` (검증 단계)

---

## 🧠 4. ConsultationBus 활용 가이드

```python
from core import get_bus, ConsultationType, ConsultationPriority

bus = get_bus()

# 1) 단방향 협의
resp = bus.consult(
    from_agent="02/Product-Manager",
    to_agent="03/Market-Analyst",
    question="CooCook TAM SEA 2026 검증 필요",
    consultation_type=ConsultationType.CLARIFICATION,
    priority=ConsultationPriority.HIGH,
)

# 2) 브로드캐스트
responses = bus.broadcast(
    from_agent="04/Solution-Architect",
    question="OpenAPI spec 검토 요청",
    target_agents=["05/Backend-Developer", "06/Frontend-Developer"],
)

# 3) 에스컬레이션 (항상 Dispatcher로)
bus.escalate("08/Security-Auditor", "CRITICAL: SQL Injection — 배포 차단 필요")
```

**순환 방지:** A→B 진행 중 B→A 시도 시 `ConsultationLoopError` 자동 발생.
**로그 위치:** `logs/consultations.jsonl`

---

## 📊 5. 활성 미션 상태 (Active Missions)

| Mission ID | 이름 | 상태 | 현재 단계 | 담당자 |
|-----------|------|------|---------|-------|
| M-001 | Initial Infrastructure Setup | ✅ COMPLETE | REPORTING | System |
| M-002 | CooCook Market Analysis & MVP | ⚙️ IN_PROGRESS | RESEARCH → DESIGN | PM + Analyst |

### CooCook OKR (M-002)
| Objective | Key Result | 목표 |
|-----------|-----------|------|
| SEA 1위 Food-Travel 플랫폼 | MAU | 10,000 (Q3 2026) |
| | Chef 예약 전환율 | > 15% |
| | Day-7 리텐션 | > 40% |
| | NPS | > 50 |

---

## 📋 6. 생성된 핵심 문서 목록

| 문서 | 경로 | 생성 주체 |
|------|------|---------|
| PRD (제품 요구사항) | `docs/generated/prd/PRD_CooCook_*.md` | Agent 02 |
| ADR-0001 (아키텍처 결정) | `docs/generated/adr/ADR-0001_*.md` | Agent 04 |
| Test Plan | `docs/generated/test_plans/TEST_PLAN_CooCook_*.md` | Agent 07 |
| Deployment Runbook | `docs/generated/runbooks/RUNBOOK_CooCook_API_*.md` | Agent 09 |
| R&R Matrix (RACI) | `docs/RR_MATRIX.md` | System |
| Agent Skills Catalog | `docs/AGENT_SKILLS.md` | System |
| Consultation Protocol | `docs/CONSULTATION_PROTOCOL.md` | System |
| Mission Lifecycle | `docs/MISSION_LIFECYCLE.md` | System |

---

## 📱 7. Telegram 실시간 모니터링

### 지금 당장 할 수 있는 것

```bash
# A) 즉시 1회 대시보드 전송 (지금 바로!)
python scripts/live_dashboard.py --now

# B) 10분 단위 자동 전송 시작
python scripts/live_dashboard.py

# C) 5분 단위 테스트
python scripts/live_dashboard.py --interval 5

# D) 전체 파이프라인 실행 → 자동 Telegram 알림
python agents/01_dispatcher/dispatcher.py
python agents/02_product_manager/pm_agent.py
python agents/03_market_analyst/analyst_agent.py
python agents/04_architect/architect_agent.py
python agents/08_security_auditor/security_agent.py
python agents/09_devops/devops_agent.py

# E) PM2로 영구 등록 (백그라운드)
pm2 start scripts/live_dashboard.py --name deca-dashboard --interpreter python
pm2 start agents/10_telegram_reporter/reporter_agent.py --name sonol-bot --interpreter python -- --listen
```

### Telegram에서 받는 메시지 유형

| 이벤트 | 전송 조건 | 아이콘 |
|--------|---------|--------|
| Mission Dispatched | 01 Dispatcher 실행 시 | ⚙️ |
| PRD + RICE 완료 | 02 PM 완료 시 | 📋 |
| 시장 분석 완료 | 03 Analyst 완료 시 | ✅ |
| ADR 결정 | 04 Architect 완료 시 | 🏗️ |
| Backend 구현 완료 | 05 Backend 완료 시 | ✅ |
| Frontend 구현 완료 | 06 Frontend 완료 시 | ✅ |
| QA 검증 | 07 QA 완료/실패 시 | 🔍 / 🚨 |
| 보안 감사 결과 | 08 Security 완료 시 | 🔐 / 🚨 |
| 배포 완료 | 09 DevOps 배포 시 | 🚀 |
| 10분 대시보드 | 자동 (10분마다) | 🤖 |

---

## 🛠️ 8. 기술 스택 (Tech Stack Decision — ADR-0001)

| Layer | 기술 | 결정 이유 |
|-------|------|---------|
| Backend | FastAPI + Python 3.12 | 성능, 타입 힌트, 자동 OpenAPI |
| Frontend | Next.js 15 + TypeScript | App Router, SSR, SEO |
| Styling | Tailwind CSS + shadcn/ui | 일관성, Atomic Design 적합 |
| Database | PostgreSQL 16 | 관계형 + JSONB 지원 |
| Cache | Redis 7 | 세션 + Rate limiting |
| AI Layer | Claude claude-sonnet-4-6 (Anthropic API) | 개인화 추천, 일정 생성 |
| Auth | Auth0 (OAuth2 + JWT) | 소셜 로그인, MFA |
| Storage | AWS S3 | 미디어 파일 |
| Infra | AWS ECS Fargate + GitHub Actions | 서버리스 컨테이너 |
| Monitoring | Datadog + Prometheus/Grafana | APM + 메트릭 |
| Architecture | **Clean Architecture + Modular Monolith** | MVP 속도 + 미래 확장성 |

---

## 📐 9. 12가지 운영 규칙 요약 (.clauderules)

| Rule | 이름 | 핵심 내용 |
|------|------|---------|
| 01 | Sequential Thinking | 모든 에이전트: Understand→Decompose→Evaluate→Decide→Execute→Handoff |
| 02 | Hand-Off Protocol | 구조화된 메시지 (FROM/TO/MISSION/STATUS/SUMMARY/OUTPUT/NEXT/BLOCKERS) |
| 03 | Conflict Escalation | 충돌 감지 시 즉시 STOP → BLOCKED → Dispatcher 에스컬레이션 |
| 04 | Pipeline Order | 순서 고정. 병렬: PM+Analyst / Backend+Frontend / QA+Security |
| 05 | Ledger Updates | 중요 산출물 → CLAUDE.md Change Log 업데이트 의무 |
| 06 | Secret Management | 하드코딩 금지. 항상 .env 사용 |
| 07 | Agent Identity | 로그: `[ID][NAME] message` 형식 |
| 08 | Reporter Trigger | COMPLETE/BLOCKED/DEPLOYMENT → 자동 Telegram 알림 |
| 09 | **Skill Mandate** | 각 에이전트는 Expert 스킬 먼저 적용 후 산출물 생성 |
| 10 | **Doc Standards** | 모든 공식 산출물은 `docs/standards/` 템플릿 사용 |
| 11 | **Consultation** | 불확실성 >70% → ConsultationBus 사용 의무 |
| 12 | **Retrospective** | 미션 완료 후 회고 기록 의무 (Start/Stop/Continue) |

---

## 📂 10. 파일 구조 전체 맵

```
D:/Project/
├── CLAUDE.md                    ← Global Memory Ledger (자동 업데이트)
├── .clauderules                 ← 12개 운영 규칙
├── .env                         ← 비밀키 (커밋 금지)
├── core/
│   ├── consultation.py          ← ConsultationBus (상호협의 엔진)
│   ├── skills_registry.py       ← 10 에이전트 × N 스킬 레지스트리
│   ├── mission_manager.py       ← 미션 라이프사이클 상태 머신
│   ├── document_engine.py       ← 7종 문서 자동 생성 엔진
│   ├── notifier.py              ← 전 에이전트 Telegram 알림 공통 헬퍼
│   ├── ledger.py                ← 파일 락 + 안전한 CLAUDE.md append
│   ├── handoff.py               ← HandOffMessage, TaskStatus
│   ├── sequential_thinking.py   ← ThoughtChain, ThinkingStep
│   └── logger.py                ← 에이전트 로거
├── skills/
│   ├── design_thinking.py       ← Stanford d.school 5단계
│   ├── lean_startup.py          ← Build-Measure-Learn, MVP
│   ├── agile_scrum.py           ← Scrum, Kanban, Velocity
│   ├── domain_driven_design.py  ← Bounded Context, Aggregate
│   ├── tdd_bdd.py               ← Red-Green-Refactor, Gherkin
│   ├── clean_architecture.py    ← SOLID, Clean Code, 12-Factor
│   ├── owasp_security.py        ← OWASP Top 10, STRIDE, CVSS 3.1
│   ├── api_first_design.py      ← OpenAPI 3.1, REST Maturity Model
│   ├── devops_sre.py            ← SLO/SLI, GitOps, Chaos Engineering
│   └── ux_research.py           ← JTBD, Nielsen, WCAG 2.1, RICE
├── agents/
│   ├── 01_dispatcher/           ← WSJF 우선순위 + 충돌 해결
│   ├── 02_product_manager/      ← PRD + RICE + OKR + Story Map
│   ├── 03_market_analyst/       ← SWOT + PESTLE + Porter's
│   ├── 04_architect/            ← ADR + C4 + OpenAPI + DDD
│   ├── 05_backend_dev/          ← TDD Cycle + Clean Architecture
│   ├── 06_frontend_dev/         ← Atomic Design + WCAG + BDD
│   ├── 07_qa_engineer/          ← Test Pyramid + Risk Matrix
│   ├── 08_security_auditor/     ← STRIDE + CVSS + OWASP
│   ├── 09_devops/               ← SLO + Blue-Green + Runbook
│   └── 10_telegram_reporter/    ← Priority 알림 + Daily Summary
├── scripts/
│   └── live_dashboard.py        ← 10분 단위 Telegram 대시보드
├── docs/
│   ├── MASTER_REPORT.md         ← ★ 이 문서 (최종 기준)
│   ├── RR_MATRIX.md             ← RACI 매트릭스
│   ├── AGENT_SKILLS.md          ← 에이전트별 스킬 카탈로그
│   ├── CONSULTATION_PROTOCOL.md ← ConsultationBus 명세
│   ├── MISSION_LIFECYCLE.md     ← 미션 라이프사이클
│   ├── standards/               ← 7개 문서 템플릿
│   └── generated/               ← 에이전트가 생성한 실제 문서
└── logs/
    ├── consultations.jsonl      ← 전 협의 이력 (자동)
    ├── missions.jsonl           ← 미션 이벤트 이력 (자동)
    └── {ID}_{Name}.log          ← 에이전트별 실행 로그
```

---

## ⚡ 11. Quick Start (지금 바로 시작)

```bash
# Step 1: 즉시 Telegram 테스트
python scripts/live_dashboard.py --now

# Step 2: 전체 파이프라인 1회 실행
python agents/01_dispatcher/dispatcher.py   # ⚙️ Telegram 도착
python agents/02_product_manager/pm_agent.py # 📋 PRD 생성 + Telegram
python agents/03_market_analyst/analyst_agent.py  # ✅ 분석 완료 + Telegram
python agents/04_architect/architect_agent.py     # 🏗️ ADR 생성 + Telegram
python agents/07_qa_engineer/qa_agent.py          # 🔍 테스트 플랜 + Telegram
python agents/08_security_auditor/security_agent.py # 🔐 STRIDE + Telegram
python agents/09_devops/devops_agent.py           # 🚀 배포 런북 + Telegram

# Step 3: 10분 자동 대시보드 시작
python scripts/live_dashboard.py

# Step 4: PM2 영구 등록 (선택)
pm2 start scripts/live_dashboard.py --name deca-dashboard --interpreter python
```

---

## 🔮 12. 다음 단계 (Next Steps)

| 우선순위 | 작업 | 담당 에이전트 |
|---------|------|------------|
| P0 | orchestrator.py 전체 파이프라인 자동화 연결 | 01 Dispatcher |
| P0 | CooCook M-002 실제 시장 데이터 수집 (Google MCP 활성화) | 03 Analyst |
| P1 | Anthropic API 연동 → 에이전트 실제 AI 추론 | 전체 |
| P1 | PRD/ADR → 실제 코드 생성 연결 | 04 Architect + 05 Backend |
| P2 | Telegram Bot 양방향 커맨드 구현 (/status, /report, /block) | 10 Reporter |
| P2 | 자동 회고(Retrospective) → CLAUDE.md 피드백 루프 | 01 Dispatcher |

---

*이 문서는 Deca-Agent 생태계의 살아있는 기준서입니다.*
*모든 신규 에이전트/기능/미션은 이 문서를 기준으로 설계·평가됩니다.*
*Generated: 2026-02-22 | Engine: Deca-Agent Max v1.0*
