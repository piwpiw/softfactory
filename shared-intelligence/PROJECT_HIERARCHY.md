# 📝 Project Hierarchy & Governance Structure

> **Purpose**: ```
> **Status**: 🟢 ACTIVE (관리 중)
> **Impact**: [Engineering / Operations]

---

## ⚡ Executive Summary (핵심 요약)
- **주요 내용**: 본 문서는 Project Hierarchy & Governance Structure 관련 핵심 명세 및 관리 포인트를 포함합니다.
- **상태**: 현재 최신화 완료 및 검토 됨.
- **연관 문서**: [Master Index](./NOTION_MASTER_INDEX.md)

---

> **메인 플랫폼 + 7개 하위 프로젝트 구조**
> **Updated**: 2026-02-25 | **Status**: ACTIVE

---

## 🏗️ **Project Tree (트리 구조)**

```
SoftFactory Platform (M-003) — 메인 프로젝트 🏢
│
├─ M-001: Infrastructure ⚙️ (Support layer)
│   └─ 역할: 플랫폼 기반, 모니터링, API 서버 운영
│
├─ M-002: CooCook API 👨‍🍳 (Product MVP #1)
│   └─ 역할: 쉐프-사용자 매칭, 예약, 결제, 리뷰
│
├─ M-003: SoftFactory Core 🎯 (Main Platform)
│   └─ 역할: 통합 대시보드, 다중 서비스 호스팅
│   ├─ Includes: 5 services (CooCook, SNS-Auto, Review, AI-Auto, WebApp)
│   └─ Live: http://localhost:8000
│
├─ M-004: JARVIS Dashboard 📊 (Analytics)
│   └─ 역할: 프로젝트 진행률, 토큰 소비, 실시간 모니터링
│
├─ M-005: Sonolbot Daemon 🤖 (Operations)
│   └─ 역할: Telegram 통합, 태스크 관리, 자동 리포팅
│
├─ M-006: 체험단 Platform 🔍 (Product MVP #2)
│   └─ 역할: 국내 체험단 통합 (쿠팡, 당근, 숨고 크롤링)
│
└─ M-007: Agent Team Monitor 👥 (Platform Infrastructure v2.0)
    └─ 역할: 에이전트 협력 시각화, 토큰 추적, 실시간 대시보드
```

---

## 📊 **각 프로젝트 역할 (명확한 정의)**

### **M-001: Infrastructure (기반층) ⚙️**

| 항목 | 정보 |
|------|------|
| **Status** | ✅ COMPLETE |
| **역할** | 플랫폼 모니터링, API 기본 운영 |
| **담당** | DevOps + Monitoring |
| **산출물** | Health check endpoints, Monitoring dashboard |
| **의존도** | 가장 기반 (모든 프로젝트가 의존) |
| **크기** | Small (기반 설정만) |

---

### **M-002: CooCook API (쉐프 매칭) 👨‍🍳**

| 항목 | 정보 |
|------|------|
| **Status** | 🔄 IN_PROGRESS (Phase 3 QA 승인 완료) |
| **역할** | 쉐프-사용자 매칭, 예약 관리, 결제 처리, 리뷰 시스템 |
| **담당** | Business + Backend + Frontend + QA |
| **산출물** | FastAPI 백엔드 + React 프론트엔드 + PostgreSQL |
| **의존도** | M-001 (기반 인프라) |
| **크기** | Large (MVP 프로젝트) |
| **마감** | 2026-04-15 (Staging → Production) |

**하위 기능:**
- 쉐프 프로필 및 등록
- 예약 시스템 (달력, 시간대)
- 결제 처리 (Stripe)
- 리뷰 및 평점

---

### **M-003: SoftFactory Core (메인 플랫폼) 🎯**

| 항목 | 정보 |
|------|------|
| **Status** | ✅ DEPLOYED |
| **역할** | 통합 플랫폼, 다중 서비스 호스팅, 사용자 관리 |
| **담당** | Full-stack (모든 팀) |
| **산출물** | Flask API + SQLite + 75 HTML 페이지 |
| **의존도** | M-001 (기반), M-002 (CooCook 통합) |
| **크기** | Extra Large (포괄적 플랫폼) |
| **생성일** | 2026-02-24 |
| **라이브** | http://localhost:8000 (demo: demo2026) |

**5개 통합 서비스:**
1. **CooCook** — 쉐프 매칭 (위 참조)
2. **SNS Auto** — 자동 포스팅 (Instagram, Twitter)
3. **Review System** — 통합 리뷰 (평점, 이미지)
4. **AI Automation** — 자동화 도구 (API 자동화)
5. **WebApp Builder** — No-code 웹앱 빌더

---

### **M-004: JARVIS Dashboard (분석) 📊**

| 항목 | 정보 |
|------|------|
| **Status** | ✅ COMPLETE |
| **역할** | 프로젝트 진행률, 에이전트 성능, 토큰 소비 실시간 모니터링 |
| **담당** | 데이터 분석 + 대시보드 엔지니어 |
| **산출물** | HTML 대시보드 + 8개 API 엔드포인트 |
| **의존도** | M-001 (모니터링 데이터), M-003 (플랫폼) |
| **크기** | Medium |
| **라이브** | http://localhost:8000/dashboard |

**모니터링 항목:**
- Agent health status
- Token consumption per agent
- Mission dependency graph
- Message latency
- Decision history

---

### **M-005: Sonolbot Daemon (자동화) 🤖**

| 항목 | 정보 |
|------|------|
| **Status** | ✅ ACTIVE |
| **역할** | Telegram 메시지 처리, 태스크 관리, 자동 리포팅 |
| **담당** | DevOps + Automation |
| **산출물** | Python 데몬 (Telegram API 통합) |
| **의존도** | M-003 (플랫폼), M-004 (리포팅 데이터) |
| **크기** | Small |
| **실행** | `pythonw daemon_control_panel.py` |

**기능:**
- `/task-new` — 새 태스크 생성
- `/task-list` — 태스크 목록
- `/report summary` — 프로젝트 요약 (자동)
- `/report detailed` — 상세 리포트

---

### **M-006: 체험단 Platform (상품 MVP #2) 🔍**

| 항목 | 정보 |
|------|------|
| **Status** | ✅ COMPLETE MVP |
| **역할** | 국내 체험단 통합 (쿠팡 이츠, 당근마켓, 숨고) |
| **담당** | 크롤링 + 데이터 파이프라인 + 프론트엔드 |
| **산출물** | 6개 API 엔드포인트 + 크롤러 (3개 사이트) + 대시보드 |
| **의존도** | M-003 (플랫폼) |
| **크기** | Medium |
| **커버리지** | 8개 실제 데이터 검증 완료 |

**크롤링 대상:**
1. Coupang Eats (배달 체험)
2. Danggeun Market (마켓 상품)
3. Soomgo (서비스 체험)

---

### **M-007: Agent Team Monitor (인프라 v2.0) 👥**

| 항목 | 정보 |
|------|------|
| **Status** | ✅ VALIDATED (방금 완료) |
| **역할** | Agent Collaboration 시각화, 토큰 추적, 실시간 협력 모니터링 |
| **담당** | 에이전트 시스템 + 인프라 |
| **산출물** | Agent Spawner + Consultation Bus + Mission Manager |
| **의존도** | M-001 (기반), M-003 (플랫폼), M-005 (리포팅) |
| **크기** | Medium |
| **기술** | 3-pillar architecture (spawner, bus, manager) |

**기능:**
- Real-time agent status
- Message latency tracking
- Token consumption per agent
- Mission dependency graph
- Decision log visualization
- Parallel group detection

---

## 🔄 **의존성 & 협력 구조**

```
M-001 (Infrastructure)
  ↑ (기반)
  ├── M-003 (SoftFactory Core) ← 메인 플랫폼
  │    ├── M-002 (CooCook) ← 상품 #1
  │    └── M-006 (체험단) ← 상품 #2
  │
  ├── M-004 (JARVIS) ← 분석 대시보드
  │
  ├── M-005 (Sonolbot) ← 자동화
  │
  └── M-007 (Agent Monitor) ← 에이전트 모니터링

의존성 관계:
M-007: 모든 프로젝트의 상태 모니터링 (상위 위치)
M-004: M-003, M-002, M-006 데이터 분석
M-005: M-003, M-004 정보 리포팅
M-003: M-001 위에서 작동 (메인)
M-002, M-006: M-003에 통합 (상품)
```

---

## 📈 **프로젝트 성숙도 & 다음 단계**

| 프로젝트 | 상태 | 진행도 | 다음 단계 |
|---------|------|--------|----------|
| M-001 | ✅ Complete | 100% | → 모니터링만 진행 |
| M-002 | 🔄 In Progress | 80% | → Phase 4 DevOps → Staging 배포 |
| M-003 | ✅ Deployed | 100% | → 라이브 운영, 버그 픽스 |
| M-004 | ✅ Complete | 100% | → M-007 통합 (Agent Monitor) |
| M-005 | ✅ Active | 100% | → 자동화 명령어 확대 |
| M-006 | ✅ Complete | 100% | → 더 많은 크롤러 추가 |
| M-007 | ✅ Validated | 100% | → M-008+ 프로젝트 적용 |

---

## 🎯 **역할 명확화 (팀 관점)**

### **Business Strategist**
- 담당: M-002 (CooCook), M-006 (체험단) — 상품 기획
- 역할: PRD 작성, 사용자 스토리, 성공 지표

### **Architect**
- 담당: M-003 (메인 플랫폼), M-007 (에이전트 시스템)
- 역할: 시스템 설계, 기술 스택, 통합 전략

### **Backend Developer**
- 담당: M-002 (CooCook API), M-003 (API 엔드포인트), M-006 (크롤러)
- 역할: FastAPI/Flask 구현, 데이터 모델, 통합

### **Frontend Developer**
- 담당: M-002 (UI), M-003 (웹 페이지), M-004 (대시보드), M-006 (UI)
- 역할: React/HTML 구현, UX 최적화

### **QA Engineer**
- 담당: 모든 프로젝트 테스트
- 역할: 테스트 계획, 버그 리포트, 품질 게이트

### **DevOps/SRE**
- 담당: M-001 (기반), M-005 (자동화), M-007 (모니터링)
- 역할: 배포, 모니터링, 자동화

### **Security Auditor**
- 담당: 모든 프로젝트 보안 검증
- 역할: 취약점 검사, 보안 스펙, 컴플라이언스

---

## 💰 **토큰 예산 & 효율**

| 프로젝트 | 예산 | 사용 | 효율 | 상태 |
|---------|------|------|------|------|
| M-001 | 30K | 33K | 110% | ⚠️ Over (acceptable) |
| M-002 | 65K | 44K | 68% | ✅ Excellent |
| M-003 | 50K | 45K | 90% | ✅ Good |
| M-004 | 45K | 40K | 89% | ✅ Good |
| M-005 | 35K | 27K | 77% | ✅ Good |
| M-006 | 65K | 26K | 40% | ✅ Excellent |
| M-007 | 40K | 8K | 20% | ✅ Excellent |
| **합계** | **330K** | **223K** | **68%** | ✅ **On Budget** |

---

## 🚀 **M-008+ 계획**

새로운 프로젝트는 이 7개를 기반으로 빌드:
- M-008: 결제 시스템 강화 (M-002 확장)
- M-009: 추천 엔진 (M-006 확장)
- M-010: 모바일 앱 (M-003 크로스 플랫폼)

모두 M-007 (Agent Monitor)로 모니터링됨.

---

**Version**: 1.0 | **Updated**: 2026-02-25 | **Status**: GOVERNANCE DEFINED