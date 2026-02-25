# 📖 문서 시작 가이드

> **마지막 업데이트:** 2026-02-25 | **상태:** ✅ ACTIVE | **Governance:** v3.0 (15 principles)

---

## 🎯 빠른 시작 (30초)

**당신은 지금 뭘 해야 하나요?**

| 상황 | 읽을 문서 |
|------|----------|
| **처음 온 사람** | [ARCHITECTURE.md](#architecture) (10분) |
| **누한테 물어봐야 하나?** | [TEAM.md](#team) |
| **지금 뭐하고 있나?** | [PROJECTS.md](#projects) (실시간) |
| **뭘 지켜야 하나?** | [RULES.md](#rules) |
| **누가 이 결정을 내리나?** | [DECISIONS.md](#decisions) |
| **SoftFactory 빨리 시작** | [SOFTFACTORY_QUICKSTART.md](#quickstart) |
| **문제 해결** | [TROUBLESHOOTING.md](#troubleshooting) |
| **새 서비스 추가** | [ADD_NEW_SERVICE.md](#newservice) |
| **문서 템플릿?** | `docs/standards/` |
| **과거 실수 확인** | [`shared-intelligence/pitfalls.md`](../shared-intelligence/pitfalls.md) |
| **재사용 패턴 찾기** | [`shared-intelligence/patterns.md`](../shared-intelligence/patterns.md) |
| **MCP 서버 목록** | [`orchestrator/mcp-registry.md`](../orchestrator/mcp-registry.md) |

---

## 📚 핵심 문서 (4개)

### 1️⃣ ARCHITECTURE.md {#architecture}
**이 조직의 구조는?** (10분 읽음)

- 10명의 에이전트 역할
- **5개의 활성 프로젝트** (M-001~M-005)
- 의사결정 파이프라인
- 통신 방식
- **거버넌스 레이어 v3.0** (shared-intelligence, orchestrator, 15 principles)

👉 **처음 읽을 문서**

### 2️⃣ PROJECTS.md {#projects}
**현재 각 프로젝트는?** (실시간 대시보드)

| 프로젝트 | 상태 | 진행률 | 담당 |
|---------|------|--------|------|
| **M-001** | ✅ COMPLETE | 100% | 01-Dispatcher |
| **M-002** | 🔄 IN_PROGRESS | 35% | 02-PM |
| **M-003** | ✅ DEPLOYED | 100% | 05+06-Dev |
| **M-004** | ✅ ACTIVE | 100% | 10-Reporter |
| **M-005** | ✅ ACTIVE | 100% | 01-Dispatcher |

👉 **실시간 현황판**

### 3️⃣ TEAM.md {#team}
**누가 뭘 잘하나?** (팀 디렉토리)

- 10개 에이전트 + 역할
- 핵심 스킬
- 현재 프로젝트
- 연락처

👉 **"누한테 물어봐야 할까?"** 할 때

### 4️⃣ DECISIONS.md {#decisions}
**누가 이 결정을 내리나?** (의사결정 트리)

- 문제 타입별 결정권자
- 갈등 해결
- 에스컬레이션 경로

👉 **"누가 최종 결정을 하나?"** 할 때

---

## 🔒 규칙 & 표준

### RULES.md
**뭘 지켜야 하나?** (10개 규칙)

- R1: 순차적 사고 (모든 에이전트)
- R2: 갈등 에스컬레이션
- R3: 불확실성 > 70% → 협의
- R4: 템플릿 준수
- R5: 비밀정보는 .env만
- R6: 주간 지식 공유
- R7: RACI 명확성
- R8: 스킬 우선 매칭
- R9: 코드 품질 게이트 (80% 커버, 0C/0H 보안)
- R10: 완료 후 회고

### standards/
**문서 템플릿** (7가지)

- `PRD_TEMPLATE.md` — 제품 요구사항
- `ADR_TEMPLATE.md` — 아키텍처 결정
- `RFC_TEMPLATE.md` — 의견 요청
- `TEST_PLAN_TEMPLATE.md` — QA 전략
- `BUG_REPORT_TEMPLATE.md` — 이슈
- `SECURITY_REPORT_TEMPLATE.md` — 보안
- `DEPLOYMENT_RUNBOOK_TEMPLATE.md` — 배포

👉 **공식 문서 작성 시 반드시 이 템플릿 사용**

---

## 🗂️ 문서 구조

```
docs/
├── README.md                    ← 당신은 여기입니다 🔴
├── ARCHITECTURE.md              ← 핵심 #1 (시스템 그림)
├── PROJECTS.md                  ← 핵심 #2 (현황판)
├── TEAM.md                      ← 핵심 #3 (팀 디렉토리)
├── DECISIONS.md                 ← 핵심 #4 (의사결정)
├── RULES.md                     ← 핵심 #5 (10개 규칙)
├── standards/                   ← 템플릿 7개
├── generated/                   ← 생성된 문서들
│   ├── prd/
│   ├── adr/
│   ├── test_plans/
│   └── runbooks/
└── archive/                     ← 이전 버전들
    └── INDEX.md (old, obsolete)
```

---

## 🚀 다음 단계

### 1단계: 5분 안에 이해하기
1. **이 README.md** ← 지금 읽는 중
2. **ARCHITECTURE.md** ← 다음 (10분)

### 2단계: 당신의 역할 찾기
- **개발자?** → [TEAM.md](#team) 에서 05 또는 06 찾기
- **매니저?** → [TEAM.md](#team) 에서 01, 02, 03 찾기
- **새로온 사람?** → [ARCHITECTURE.md](#architecture) 먼저

### 3단계: 필요한 정보 찾기
- **"누한테 물어봐야 할까?"** → [TEAM.md](#team)
- **"누가 최종 결정하나?"** → [DECISIONS.md](#decisions)
- **"뭘 지켜야 하나?"** → [RULES.md](#rules)
- **"문서 어떻게 쓰나?"** → `docs/standards/`

---

## 📊 시스템 건강도

```
🟢 ECOSYSTEM HEALTH: GREEN

Projects:
├── M-001 Infrastructure ✅ COMPLETE
├── M-002 CooCook 🔄 30% (dev starts 2026-02-24)
├── M-003 SoftFactory ✅ DEPLOYED (http://localhost:8000)
└── M-004 JARVIS ✅ ACTIVE (24/7)

Team: 10 agents, 62% utilized, BALANCED
Security: 100% passed (0C/0H)
Uptime: 99.9%+
```

---

## ❓ FAQ

**Q: CLAUDE.md는 뭐예요?**
A: 원본 생태계 문서입니다. 역사적 기록용으로 유지하고 있습니다. 현재 정보는 여기 **docs/** 폴더에 있습니다.

**Q: 왜 이렇게 많은 문서가 있어요?**
A: 각 문서는 **다른 목적**을 가집니다:
- ARCHITECTURE = "이 조직의 구조는?"
- PROJECTS = "현황판"
- TEAM = "팀 디렉토리"
- DECISIONS = "의사결정"
- RULES = "규칙"

**Q: 문서가 오래되면 어떻게 하나요?**
A: [PROJECTS.md](#projects)는 실시간으로 업데이트합니다. 변경 사항이 있으면 거기 먼저 반영하세요.

**Q: 새 프로젝트를 어떻게 추가하나요?**
A: [PROJECTS.md](#projects)에 새 M-00X 항목을 추가하고, 담당 에이전트를 [TEAM.md](#team)에 업데이트하세요.

---

## 📞 빠른 도움말

| 상황 | 액션 |
|------|------|
| **앱이 안 켜짐** | [PROJECTS.md](#projects) → M-003 섹션 → "Getting Started" |
| **누가 이 기능을 하나?** | [TEAM.md](#team) → 스킬 찾기 |
| **의사결정이 필요함** | [DECISIONS.md](#decisions) → 문제 타입 찾기 |
| **새 문서 작성** | `docs/standards/` → 템플릿 고르기 |
| **버그 발견** | [TEAM.md](#team) → 07-QA 연락 또는 `standards/BUG_REPORT_TEMPLATE.md` |

---

**마지막 업데이트:** 2026-02-23
**다음 업데이트:** 2026-02-24 (M-002 개발 시작)
**질문?** → TEAM.md 의 적절한 담당자 찾기
