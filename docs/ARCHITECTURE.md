# 📝 🏗️ 시스템 아키텍처

> **Purpose**: **10명의 에이전트가 4개 프로젝트를 동시 진행하는 조직**
> **Status**: 🟢 ACTIVE (관리 중)
> **Impact**: [Engineering / Operations]

---

## ⚡ Executive Summary (핵심 요약)
- **주요 내용**: 본 문서는 🏗️ 시스템 아키텍처 관련 핵심 명세 및 관리 포인트를 포함합니다.
- **상태**: 현재 최신화 완료 및 검토 됨.
- **연관 문서**: [Master Index](./NOTION_MASTER_INDEX.md)

---

> **마지막 업데이트:** 2026-02-23 | **소유자:** System Architecture | **상태:** ✅ ACTIVE

---

## 🎯 핵심 아이디어 (1분)

**10명의 에이전트가 4개 프로젝트를 동시 진행하는 조직**

- **단일 진실 공급원** (Single Source of Truth)
- **명확한 의사결정** (Clear Decision Authority)
- **병렬 작업** (Parallel Execution)
- **지속적 모니터링** (Real-time Visibility)

---

## 🧬 조직 구조

### 10개 에이전트 역할

```
01. Chief Dispatcher      ← 최종 의사결정권
02. Product Manager       ← 제품 방향
03. Market Analyst        ← 시장 분석
04. Solution Architect    ← 기술 설계
05. Backend Developer     ← 백엔드
06. Frontend Developer    ← 프론트엔드
07. QA Engineer          ← 테스트
08. Security Auditor     ← 보안
09. DevOps Engineer      ← 배포
10. Telegram Reporter    ← 알림 & 회고
```

| ID | 역할 | 주요 스킬 | 현재 프로젝트 | 상태 |
|----|----|---------|----------|------|
| **01** | Chief Dispatcher | WSJF, 갈등해결, 파이프라인 | M-001, M-002 | ✅ ACTIVE |
| **02** | Product Manager | RICE, OKR, PRD | M-002 (CooCook) | ✅ ACTIVE |
| **03** | Market Analyst | SWOT, PESTLE, Porter's | M-002 (CooCook) | ✅ ACTIVE |
| **04** | Solution Architect | ADR, C4, DDD, OpenAPI | M-002 (CooCook) | ✅ ACTIVE |
| **05** | Backend Developer | TDD, Clean Arch, FastAPI, Flask | M-002, M-003 | ✅ ACTIVE |
| **06** | Frontend Developer | Atomic Design, WCAG, React, HTML | M-002, M-003 | ✅ ACTIVE |
| **07** | QA Engineer | 테스트 피라미드, 위험기반테스트 | M-002 (준비) | ✅ ACTIVE |
| **08** | Security Auditor | STRIDE, CVSS, OWASP, GDPR | M-002 (준비) | ✅ ACTIVE |
| **09** | DevOps Engineer | SLO/SLI, GitOps, Blue-Green, IaC | M-002 (준비) | ✅ ACTIVE |
| **10** | Telegram Reporter | 알림, 회고, 대시보드 | M-001, M-002, M-003, M-004 | ✅ ACTIVE |

---

## 🔄 의사결정 파이프라인

```
[NEW TASK INPUT]
       ↓
01_DISPATCHER (WSJF 우선순위)
       ├─→ 갈등? → 요청자에게 되돌림 ↩️
       ↓
병렬 트랙:
    02_PM (RICE/OKR)  ←→ ConsultationBus ←→  03_ANALYST (SWOT/PESTLE)
       ↓
04_ARCHITECT (C4/ADR/DDD/OpenAPI)
       ↓
병렬 트랙:
    05_BACKEND (TDD/Clean)  ←→ ConsultationBus ←→  06_FRONTEND (Atomic/WCAG)
       ↓
병렬 트랙:
    07_QA (위험기반)  ←→ ConsultationBus ←→  08_SECURITY (STRIDE)
       ↓
09_DEVOPS (SLO/Blue-Green/IaC)
       ↓
10_REPORTER (알림 + 회고)
       ↓
[배포 + 모니터링]
```

### 파이프라인 규칙

1. **순차적 사고** (R1): 모든 에이전트는 손을 내밀기 전에 **순차적으로 생각**
2. **불확실성 > 70%** (R3): ConsultationBus 무조건 사용
3. **갈등 에스컬레이션** (R2): 즉시 01-Dispatcher 보고
4. **병렬 실행**: 같은 레벨 에이전트는 동시 진행

---

## 📋 4개 활성 프로젝트

### M-001: Infrastructure Setup
**상태:** ✅ COMPLETE | **기간:** 2026-02-22 | **팀:** 01-Dispatcher

**배경:** Deca-Agent 생태계의 기본 인프라 구축

**결과:**
- ✅ 10개 에이전트 역할 정의
- ✅ ConsultationBus, SkillsRegistry, MissionManager 모듈
- ✅ 7개 문서 템플릿
- ✅ 10개 스킬 모듈
- ✅ RACI 매트릭스
- ✅ 43 파일 생성/업데이트

**상태:** 기본 생태계 가동. M-002, M-003, M-004 동시 지원 준비 완료.

---

### M-002: CooCook (Chef Marketplace)
**상태:** 🔄 IN_PROGRESS | **진행률:** 30% | **팀:** 02-PM + 03-Analyst + 04-Architect + 05-Backend + 06-Frontend + 07-QA + 08-Security + 09-DevOps

**배경:** "에어비앤비 for 로컬 음식 경험"

**스택:**
- Backend: FastAPI + PostgreSQL 16 + Redis
- Frontend: Next.js 15 + Tailwind CSS
- DevOps: AWS ECS + Blue-Green
- AI: Claude API (claude-sonnet-4-6)

**진행 상황:**
- ✅ **시장 분석:** SWOT, PESTLE, Porter's 완료
- ✅ **ADR-0001:** Clean Architecture + Modular Monolith 승인
- 🔄 **OpenAPI:** 60% (완료 2026-02-24)
- 🔄 **C4 다이어그램:** 90% (완료 2026-02-24)
- 📋 **개발 시작:** 2026-02-24
- 🎯 **런칭:** 2026-04-15
- 📊 **목표:** 10K MAU by Q3 2026

---

### M-003: SoftFactory Hub (Multi-SaaS Platform)
**상태:** ✅ COMPLETE | **진행률:** 100% | **팀:** 05-Backend + 06-Frontend

**배경:** 하나의 플랫폼 위에 여러 SaaS 서비스를 제공하는 구조

**스택:**
- Backend: Flask + SQLAlchemy + SQLite
- Frontend: HTML + Tailwind CSS
- Auth: JWT (1시간 access, 30일 refresh)
- Payment: Stripe Checkout (선택)

**서비스 (3개):**
1. **CooCook** - 셰프 예약 플랫폼 ($29/월)
2. **SNS Auto** - 소셜미디어 자동화 ($49/월)
3. **Review Campaigns** - 브랜드 체험단 모집 ($39/월)

**완료 항목:**
- ✅ 10개 DB 모델 + 자동 초기화
- ✅ JWT 인증 + @require_auth, @require_subscription 데코레이터
- ✅ Stripe 결제 통합 (dev 모드 작동)
- ✅ 3개 서비스 API (15개 엔드포인트)
- ✅ 15개 프론트엔드 페이지
- ✅ 모든 테스트 통과 ✅

**라이브:** http://localhost:8000
**데모:** admin@softfactory.com / admin123

---

### M-004: JARVIS Telegram Bot
**상태:** ✅ ACTIVE | **진행률:** 100% | **팀:** 10-Reporter

**배경:** 팀 알림, 배포 트리거, 회고 자동화

**배포:** Railway (production)
**토큰:** 8461725251:AAELKRbZkpa3u6WK24q4k-RGkzedHxjTLiM
**URL:** https://jarvis-production.up.railway.app/

**명령어:**
- `/pages` - 모든 웹페이지
- `/status` - 시스템 상태
- `/deploy env version` - 배포
- `/mission name` - 새 프로젝트
- `/report` - 모니터링
- `/help` - 도움말

**가동률:** 100% (2026-02-22부터)

---

## 🛠️ 공유 인프라

### Core Modules

| 모듈 | 경로 | 목적 | 사용처 |
|------|------|------|--------|
| **ConsultationBus** | `core/consultation.py` | 에이전트 간 양방향 협의 | 모든 에이전트 |
| **SkillsRegistry** | `core/skills_registry.py` | 스킬 카탈로그 + 작업 매칭 | Dispatcher |
| **MissionManager** | `core/mission_manager.py` | 미션 생명주기 상태 머신 | Dispatcher |
| **DocumentEngine** | `core/document_engine.py` | 템플릿 기반 문서 생성 | 모든 에이전트 |

### Reusable Skills Library

| 스킬 | 경로 | 사용 에이전트 |
|-----|------|----------|
| Design Thinking | `skills/design_thinking.py` | 02, 06 |
| Lean Startup | `skills/lean_startup.py` | 02, 03 |
| Agile Scrum | `skills/agile_scrum.py` | 01, 02, 07 |
| Domain-Driven Design | `skills/domain_driven_design.py` | 04, 05 |
| TDD/BDD | `skills/tdd_bdd.py` | 05, 06, 07 |
| Clean Architecture | `skills/clean_architecture.py` | 04, 05 |
| OWASP Security | `skills/owasp_security.py` | 08 |
| API-First Design | `skills/api_first_design.py` | 04, 05, 06 |
| DevOps/SRE | `skills/devops_sre.py` | 09 |
| UX Research | `skills/ux_research.py` | 02, 06 |

---

## 📊 현재 팀 활용률

```
┌─────────────────────────────────┐
│ Team Utilization: 62% (BALANCED)│
├─────────────────────────────────┤
│ 05-Backend + 06-Frontend: 75-80%│  (M-003 복구 중)
│ 02-PM + 03-Analyst + 04-Arch:60%│  (M-002 연구 중)
│ 07-QA + 08-Security: 40-50%     │  (대기 중, 준비)
│ 09-DevOps: 50%                  │  (staging 배포 대기)
│ 01-Dispatcher + 10-Reporter:100%│  (항상 활성)
└─────────────────────────────────┘
```

**해석:**
- 개발팀은 M-003 후 회복 중
- 전략팀은 M-002 초기 연구 중
- QA/보안 팀은 준비 완료, 대기 중
- DevOps는 신호 대기 중

---

## 🗂️ 파일 구조

```
D:/Project/
├── CLAUDE.md                      ← 원본 생태계 문서 (역사)
├── docs/
│   ├── README.md                  ← START HERE (30초)
│   ├── ARCHITECTURE.md            ← 이 파일 (10분)
│   ├── PROJECTS.md                ← 현황판 (실시간)
│   ├── TEAM.md                    ← 팀 디렉토리
│   ├── DECISIONS.md               ← 의사결정 트리
│   ├── RULES.md                   ← 10개 규칙
│   ├── standards/                 ← 템플릿 7개
│   ├── generated/                 ← 생성 문서들
│   └── archive/                   ← 이전 버전
├── backend/                       ← Flask 앱 (M-003)
├── web/                           ← HTML 페이지들 (M-003)
├── scripts/                       ← JARVIS Bot (M-004)
├── agents/                        ← 10개 에이전트 폴더 (준비)
└── memory/
    └── MEMORY.md                  ← 지속 메모리
```

---

## 🎯 다음 단계

**2026-02-24 (내일):**
- M-002 개발 시작 (05 Backend + 06 Frontend)
- OpenAPI 스펙 최종화 (04 Architect)
- C4 다이어그램 완성 (04 Architect)

**2026-02-27:**
- QA 리뷰 시작 (07 QA)
- 보안 감사 시작 (08 Security)

**2026-03-01:**
- Staging 배포 (09 DevOps)

**2026-04-15:**
- M-002 CooCook 정식 런칭 🚀

---

## 🔐 핵심 규칙 (요약)

| 규칙 | 내용 |
|------|------|
| **R1** | 순차적 사고 (모든 에이전트, 손을 내밀기 전) |
| **R2** | 갈등 에스컬레이션 (01-Dispatcher) |
| **R3** | 불확실성 > 70% → ConsultationBus |
| **R4** | 템플릿 준수 (공식 문서는 standards/ 템플릿만) |
| **R5** | 비밀정보는 .env만 (코드에 절대금지) |
| **R6** | 주간 지식 공유 |
| **R7** | RACI 명확성 |
| **R8** | 스킬 우선 매칭 |
| **R9** | 코드 품질 게이트 (80% 커버, 0C/0H 보안) |
| **R10** | 완료 후 회고 |

---

## ✨ 시스템의 장점

✅ **단일 진실 공급원** - 중복 제거
✅ **명확한 의사결정** - 01-Dispatcher가 최종 권한
✅ **병렬 작업** - 동시 진행으로 빠른 속도
✅ **실시간 추적** - PROJECTS.md 대시보드
✅ **재사용 가능한 스킬** - 10개 모듈
✅ **표준 템플릿** - 일관된 품질
✅ **협의 프로토콜** - ConsultationBus
✅ **크로스트레이닝** - TEAM.md 백업

---

**다음:** [PROJECTS.md](PROJECTS.md) 또는 [TEAM.md](TEAM.md)