# 👥 팀 디렉토리

> **마지막 업데이트:** 2026-02-23 | **소유자:** HR / Dispatcher | **상태:** ✅ ACTIVE

---

## 🎯 빠른 찾기

**"누한테 물어봐야 할까?"** 에이전트별로 찾아보세요.

| 질문 | 담당자 |
|------|--------|
| **"뭐 우선순위야?"** | 01-Chief Dispatcher |
| **"제품 방향이 뭐야?"** | 02-Product Manager |
| **"시장은 어떻게 봐?"** | 03-Market Analyst |
| **"기술 설계는?"** | 04-Solution Architect |
| **"백엔드 API는?"** | 05-Backend Developer |
| **"프론트엔드 UI는?"** | 06-Frontend Developer |
| **"테스트 어떻게 해?"** | 07-QA Engineer |
| **"보안은 안전해?"** | 08-Security Auditor |
| **"배포 준비됐나?"** | 09-DevOps Engineer |
| **"팀한테 알려줘."** | 10-Telegram Reporter |

---

## 📋 10개 에이전트 상세

### 01️⃣ Chief Dispatcher 🚦

**역할:** 최종 의사결정권자, 파이프라인 조율

**핵심 스킬:**
- WSJF 우선순위 지정
- 갈등 해결
- 파이프라인 오케스트레이션

**현재 프로젝트:**
- M-001 (완료)
- M-002 (모니터링)

**연락처:**
- Telegram: DM
- Escalation path: 최종 (이 사람이 최종)

**SLA:** < 2시간

**팀원:** 혼자

**참고:** 모든 갈등, 우선순위 문제, 모호한 결정은 여기로

---

### 02️⃣ Product Manager 📱

**역할:** 제품 비전, 요구사항 정의

**핵심 스킬:**
- RICE 우선순위 지정
- OKR 작성
- Story Map
- PRD 작성

**현재 프로젝트:**
- M-002 CooCook (PRD 작성 중)

**할당:** 60-70% (M-002 연구 중)

**연락처:**
- Slack: #product
- PRD 템플릿: `docs/standards/PRD_TEMPLATE.md`

**SLA:** < 4시간

**협력:** 03-Analyst와 일부 중복 (의도적 - 서로 다른 관점)

**참고:** 제품 방향, 기능 우선순위, 요구사항 정의는 여기로

---

### 03️⃣ Market Analyst 📊

**역할:** 시장 분석, 경쟁 분석

**핵심 스킬:**
- SWOT 분석
- PESTLE 분석
- Porter's 5 Forces
- TAM/SAM/SOM 계산

**현재 프로젝트:**
- M-002 CooCook (시장분석 완료 ✅)

**할당:** 60-70% (M-002 연구 중)

**연락처:**
- Slack: #product
- 산출물 위치: `docs/generated/market/`

**SLA:** < 4시간

**협력:** 02-PM과 일부 중복 (의도적)

**참고:** 시장 기회, 경쟁 현황, 위험 요인은 여기로

---

### 04️⃣ Solution Architect 🏗️

**역할:** 기술 설계, 아키텍처 결정

**핵심 스킬:**
- ADR (Architecture Decision Record)
- C4 Model
- Domain-Driven Design
- OpenAPI 3.1
- Clean Architecture

**현재 프로젝트:**
- M-002 CooCook (OpenAPI 60%, C4 90%)

**할당:** 60-70% (M-002 설계 중)

**연락처:**
- Slack: #architecture
- 템플릿: `docs/standards/ADR_TEMPLATE.md`
- 산출물: `docs/generated/adr/`, `docs/generated/c4/`

**SLA:** < 4시간

**협력:** 05-Backend, 06-Frontend와 깊은 협의

**참고:** 기술 설계, 마이크로서비스 vs 모놀리스, 데이터베이스 선택은 여기로

---

### 05️⃣ Backend Developer 🔧

**역할:** API 개발, 데이터베이스, 비즈니스 로직

**핵심 스킬:**
- TDD (Test-Driven Development)
- Clean Architecture 구현
- FastAPI / Flask
- PostgreSQL / SQLAlchemy
- RESTful API 설계

**현재 프로젝트:**
- M-002 CooCook (2026-02-24 시작)
- M-003 SoftFactory (완료 ✅)

**할당:** 75-80% (M-003 후 회복, M-002 준비)

**연락처:**
- Slack: #backend
- Code: `backend/`
- PR: GitHub 리뷰

**SLA:** < 2시간

**협력:** 04-Architect, 06-Frontend, 07-QA와 일일 동기화

**참고:** API 설계, 데이터베이스 스키마, 성능 최적화는 여기로

---

### 06️⃣ Frontend Developer 🎨

**역할:** UI/UX 개발, 프론트엔드 아키텍처

**핵심 스킬:**
- Atomic Design
- WCAG 2.1 (접근성)
- BDD Frontend
- React / Next.js
- Tailwind CSS

**현재 프로젝트:**
- M-002 CooCook (2026-02-24 시작)
- M-003 SoftFactory (완료 ✅)

**할당:** 75-80% (M-003 후 회복, M-002 준비)

**연락처:**
- Slack: #frontend
- Code: `web/`
- Design: Figma (TBD)

**SLA:** < 2시간

**협력:** 04-Architect, 05-Backend, 07-QA와 일일 동기화

**참고:** 페이지 레이아웃, 컴포넌트 설계, 사용자 경험은 여기로

---

### 07️⃣ QA Engineer 🧪

**역할:** 테스트 계획, QA 전략, 품질 관리

**핵심 스킬:**
- Test Pyramid (단위, 통합, E2E)
- 위험 기반 테스트
- 자동화 테스트
- 버그 추적

**현재 프로젝트:**
- M-002 CooCook (2026-02-27 시작)

**할당:** 40-50% (대기, 준비 완료)

**연락처:**
- Slack: #qa
- 템플릿: `docs/standards/TEST_PLAN_TEMPLATE.md`
- 산출물: `docs/generated/test_plans/`

**SLA:** < 4시간

**협력:** 05-Backend, 06-Frontend와 밀접한 협의

**참고:** 테스트 계획, 버그 발견, 품질 보증은 여기로

---

### 08️⃣ Security Auditor 🔒

**역할:** 보안 감시, 취약점 분석, GDPR 준수

**핵심 스킬:**
- STRIDE (위협 모델링)
- CVSS 3.1 (취약점 평가)
- OWASP Top 10
- GDPR / 데이터 개인정보
- 침투 테스트

**현재 프로젝트:**
- M-002 CooCook (2026-02-27 시작)

**할당:** 40-50% (대기, 준비 완료)

**연락처:**
- Slack: #security
- 템플릿: `docs/standards/SECURITY_REPORT_TEMPLATE.md`
- 산출물: `docs/generated/security/`

**SLA:** < 4시간

**협력:** 05-Backend, 06-Frontend, 09-DevOps와 협의

**참고:** 보안 취약점, 데이터 보호, 컴플라이언스는 여기로

---

### 09️⃣ DevOps Engineer ☁️

**역할:** 배포, 인프라, 모니터링

**핵심 스킬:**
- SLO / SLI (Service Level)
- GitOps
- Blue-Green 배포
- Infrastructure as Code
- AWS ECS / Docker
- Monitoring & Alerting

**현재 프로젝트:**
- M-002 CooCook (2026-03-01 Staging)
- M-004 JARVIS (운영 중)

**할당:** 50% (staging 배포 대기)

**연락처:**
- Slack: #devops
- 템플릿: `docs/standards/DEPLOYMENT_RUNBOOK_TEMPLATE.md`
- 산출물: `docs/generated/runbooks/`

**SLA:** < 4시간

**협력:** 04-Architect, 05-Backend, 06-Frontend와 협의

**참고:** 배포, 인프라 설계, 모니터링은 여기로

---

### 🔟 Telegram Reporter 📢

**역할:** 팀 알림, 이벤트 리포팅, 회고 자동화

**핵심 스킬:**
- 이벤트 기반 알림
- 일일 요약
- 회고 진행
- 대시보드 생성

**현재 프로젝트:**
- M-001 (완료)
- M-002 (모니터링)
- M-003 (배포 완료)
- M-004 JARVIS (24/7 운영)

**할당:** 100% (항상 활성)

**연락처:**
- Telegram: @jarvis_bot
- 명령어: `/help`
- 배포: https://jarvis-production.up.railway.app/

**SLA:** < 5분

**참고:** 팀 알림, 배포 알림, 일일 리포트는 여기로

---

## 📊 팀 할당 현황

```
현재 할당률: 62% (BALANCED)
기준일: 2026-02-23

┌──────────────────────────────────┐
│ 01-Dispatcher: 100% (항상 활성)  │
├──────────────────────────────────┤
│ 02-PM: 60-70% (M-002)            │
│ 03-Analyst: 60-70% (M-002)       │
│ 04-Architect: 60-70% (M-002)     │
├──────────────────────────────────┤
│ 05-Backend: 75-80% (M-003→M-002) │
│ 06-Frontend: 75-80% (M-003→M-002)│
├──────────────────────────────────┤
│ 07-QA: 40-50% (준비 중)          │
│ 08-Security: 40-50% (준비 중)    │
├──────────────────────────────────┤
│ 09-DevOps: 50% (staging 대기)    │
├──────────────────────────────────┤
│ 10-Reporter: 100% (항상 활성)    │
└──────────────────────────────────┘

요약: 전략팀 60%, 개발팀 75%, 품질팀 40%, DevOps 50%
→ 균형잡힌 할당 (현명한 하중 분산)
```

---

## 🔄 협력 관계

### 코어 협력 (매일)
- **04-Architect** ↔ **05-Backend** (API 설계)
- **04-Architect** ↔ **06-Frontend** (UI 아키텍처)
- **05-Backend** ↔ **06-Frontend** (API-UI 통합)
- **05-Backend** ↔ **07-QA** (테스트 케이스)
- **06-Frontend** ↔ **07-QA** (E2E 테스트)

### 중간 협력 (주 3회)
- **02-PM** ↔ **03-Analyst** (시장 vs 제품)
- **07-QA** ↔ **08-Security** (테스트 vs 보안)
- **09-DevOps** ↔ **04-Architect** (인프라 설계)

### 주간 협력 (주 1회)
- **01-Dispatcher** ↔ **모든 에이전트** (상태 동기화)
- **10-Reporter** ↔ **모든 에이전트** (회고, 리포팅)

---

## 🔒 백업 및 교차 훈련

| 주 역할 | 백업 1순위 | 백업 2순위 | 교차훈련 상태 |
|--------|-----------|----------|------------|
| **01-Dispatcher** | 02-PM | 04-Architect | 대기 |
| **02-PM** | 04-Architect | 01-Dispatcher | 진행 중 |
| **03-Analyst** | 02-PM | 04-Architect | 진행 중 |
| **04-Architect** | 05-Backend | 09-DevOps | 진행 중 |
| **05-Backend** | 06-Frontend | 07-QA | 진행 중 |
| **06-Frontend** | 05-Backend | 07-QA | 진행 중 |
| **07-QA** | 05-Backend | 08-Security | 진행 중 |
| **08-Security** | 07-QA | 04-Architect | 진행 중 |
| **09-DevOps** | 04-Architect | 05-Backend | 진행 중 |
| **10-Reporter** | 01-Dispatcher | 02-PM | 대기 |

---

## 📞 일반적인 질문과 답변

| 질문 | 답변 | 담당 |
|------|------|------|
| 이 기능은 우선순위가 뭐야? | WSJF 점수 확인 | 01-Dispatcher |
| 이 기능이 필요한가? | 시장/제품 분석 필요 | 02 + 03 |
| 어떻게 구현하지? | 기술 설계 필요 | 04-Architect |
| API 설계는? | OpenAPI 스펙 확인 | 04-Architect |
| DB 스키마는? | ERD 확인 또는 04/05 협의 | 05-Backend |
| 페이지 레이아웃은? | 와이어프레임/목업 | 06-Frontend |
| 테스트 계획은? | 테스트 피라미드 | 07-QA |
| 보안 위험은? | STRIDE 분석 | 08-Security |
| 배포 준비는? | 인프라 체크리스트 | 09-DevOps |
| 팀한테 공지해줘 | Telegram 알림 | 10-Reporter |

---

## 🎯 SLA (Service Level Agreement)

| 카테고리 | SLA | 담당자들 |
|---------|-----|---------|
| **Blocker (🔴)** | < 2h | 01, 05, 06, 09 |
| **Critical (🟠)** | < 4h | 02, 03, 04, 07, 08 |
| **Normal (🟡)** | < 1d | 모든 에이전트 |
| **FYI (🟢)** | < 3d | 10-Reporter |

---

## 📞 연락처 요약

| 이름 | Slack | Telegram | 이메일 | 시간대 |
|------|-------|----------|--------|--------|
| 01-Dispatcher | #general | DM | TBD | KST |
| 02-PM | #product | DM | TBD | KST |
| 03-Analyst | #product | DM | TBD | KST |
| 04-Architect | #architecture | DM | TBD | KST |
| 05-Backend | #backend | DM | TBD | KST |
| 06-Frontend | #frontend | DM | TBD | KST |
| 07-QA | #qa | DM | TBD | KST |
| 08-Security | #security | DM | TBD | KST |
| 09-DevOps | #devops | DM | TBD | KST |
| 10-Reporter | @jarvis_bot | Telegram | N/A | Always |

---

**마지막 업데이트:** 2026-02-23
**다음 업데이트:** 2026-02-28 (M-002 개발 중간 리뷰)
