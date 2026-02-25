# 🎯 CooCook Daily Operations Guide

**매일 새로운 프로젝트를 출시하기 위한 JARVIS v2 가이드**

**Status:** ✅ READY FOR PRODUCTION
**Release Date:** 2026-02-23
**Version:** JARVIS v2.0

---

## 🔑 10 CORE KEYWORDS (핵심 개념)

### 1. **MISSION** 🎯
큰 분기 목표 (1-3개월)
```
예: M-002 "CooCook Market Analysis & Launch"
```

### 2. **SPRINT** 📌
2주 개발 사이클 (40 story points)
```
예: S-001 "Auth System Sprint"
```

### 3. **TASK** ✓
개별 작업 (1-3일)
```
예: T-001 "JWT Authentication" (5 points)
```

### 4. **SKILL** 🛠️
팀/개인 능력
```
예: Team 05 - "Redis Caching" (블로킹 → 활성화)
```

### 5. **TEAM** 👥
담당 팀 (01-10)
```
Team 05: Backend Developer (⚙️)
```

### 6. **STATUS** 📈
작업 상태
```
BACKLOG → IN_PROGRESS → REVIEW → DONE
```

### 7. **PRIORITY** 🚨
긴급도
```
🚨 CRITICAL(P0) | 🔥 HIGH(P1) | ⚡ MEDIUM(P2) | 💤 LOW(P3)
```

### 8. **DEPLOY** 🚀
배포 (Dev → Staging → Prod)
```
/deploy staging v1.2.24
/deploy prod v1.2.24
```

### 9. **STANDUP** 🎙️
일일 회의 (5분)
```
어제 한 일 | 오늘 할 일 | 블로커
```

### 10. **RELEASE** 📦
버전 릴리스 (v1.2.24)
```
Daily release = 매일 새 버전 출시
```

---

## ⏰ DAILY RHYTHM (일일 리듬)

### **09:00 AM UTC — STANDUP** 🎙️
```
/standup
→ 모든 팀이 어제 한 일, 오늘 할 일, 블로커 공유
→ JARVIS가 블로커 요약
→ 예상: 5분
```

**예상 응답:**
```
🎙️ STANDUP 리포트

Team 05 (Backend):
  ✅ Yesterday: JWT auth 완성
  🔄 Today: User API 구현
  🚨 Blocker: None

Team 06 (Frontend):
  ✅ Yesterday: Login UI 50%
  🔄 Today: Dashboard UI
  🚨 Blocker: API 스펙 대기

Team 09 (DevOps):
  ✅ Yesterday: Staging 환경 준비
  🔄 Today: Blue-Green 설정
  🚨 Blocker: None
```

---

### **10:00 AM UTC — NEW PROJECT LAUNCH** 🚀
```
/mission create "새 프로젝트 이름"
→ 자동으로 팀 배정
→ 필요한 스킬 자동 감지
→ 부족한 스킬 설치 제안
→ 예상: 30분 준비
```

**자동 프로세스:**
```
✨ 새 MISSION 생성: "User Profile Feature"

🔄 자동 프로세스:
  1️⃣ Team 01 (Dispatcher) — WSJF 우선순위 (10초)
  2️⃣ Team 02 (PM) — PRD 작성 (5분)
  3️⃣ Team 03 (Analyst) — 시장 검증 (5분)
  4️⃣ Team 04 (Architect) — 설계 (10분)
  5️⃣ Teams 05-10 — 실행 준비

📍 Mission ID: M-005
⏱️ 예상: 30분 후 팀 준비 완료
```

---

### **1:00 PM UTC — SPRINT REVIEW** 📊
```
/sprint review
→ 현재 Sprint 진행 상황 확인
→ 팀별 속도 (velocity) 확인
→ 배포 가능 여부 확인
→ 예상: 10분
```

**응답 예시:**
```
📊 Sprint Report (S-001)

Sprint: Auth System Sprint
기간: 2026-02-23 → 2026-03-08
진행도: 12/40 points (30%)

팀별 상황:
  ⚙️ Team 05 (Backend): 5/12 points (42%)
  🎨 Team 06 (Frontend): 4/10 points (40%)
  🔍 Team 07 (QA): 2/8 points (25%)
  🚀 Team 09 (DevOps): 1/10 points (10%)

현재 Task:
  🔄 T-001: JWT Auth — 60% 진행중
  🔄 T-003: Login UI — 40% 진행중
  ⏳ T-004: API Tests — 준비중

💡 목표 달성 가능! 다음 단계: 스테이징 배포
```

---

### **3:00 PM UTC — STAGING DEPLOY** 🧪
```
/deploy staging v1.2.24
→ 스테이징 환경에 배포
→ 자동 테스트 실행
→ 예상: 5분
```

**배포 진행:**
```
🧪 STAGING 배포 시작
Version: v1.2.24

배포 진행도:
  ✅ Build 완료 — 100% ▓▓▓▓▓
  ⏳ Deploy 중... — 50% ▓▓▓░░
  ⏳ Tests 실행 중...

🚀 Team 09 (DevOps) 담당
📊 약 2분 소요...

[2분 후]

✅ Staging 배포 완료!
- Build: PASS
- Unit tests: 234/234 PASS
- Integration tests: 45/45 PASS
- Load test: OK (5K req/s)

💡 다음 단계: 프로덕션 배포
```

---

### **4:30 PM UTC — PRODUCTION DEPLOY** 🌍
```
/deploy prod v1.2.24
→ 프로덕션에 배포
→ Blue-Green 자동 전환
→ 24시간 모니터링
→ 예상: 10분 (+ 모니터링)
```

**프로덕션 배포:**
```
🌍 PRODUCTION 배포 시작
⚠️ 주의: 라이브 배포 (10.2K 사용자)

배포 프로세스:
  1️⃣ Blue-Green 전환 준비
  2️⃣ 헬스 체크
  3️⃣ 모니터링 (24시간)
  4️⃣ 문제 시 자동 롤백

확인 필요: `/deploy prod v1.2.24 confirm`

[승인 후]

🚀 Blue-Green 전환 진행...
  → Green environment 활성화 (100%)
  → 트래픽 전환 (완료)
  → 모니터링 시작

✅ 배포 완료!
- 영향받은 사용자: 10,234
- 에러율: 0.02% (정상)
- 응답시간: 145ms (정상)
- 자동 롤백: OFF

🎉 새 버전 v1.2.24 라이브!
```

---

### **6:00 PM UTC — DAILY SUMMARY** 📝
```
/summary
→ 하루 일과 정리
→ KPI 리포트
→ 내일 계획 제시
→ 예상: 5분
```

**일일 요약:**
```
📝 Daily Summary — 2026-02-23

✅ 배포 완료:
  - 1개 feature 배포 (v1.2.24)
  - 영향받은 사용자: 10,234
  - 버그 수정: 3개
  - 성능 개선: +8%

📊 메트릭:
  - New PRs: 12개
  - Merged: 8개
  - Code reviews: 15개
  - Test coverage: 89%
  - Incident: 0개

🎯 팀 성과:
  - Team 05 (Backend): 8 points (목표: 8) ✅
  - Team 06 (Frontend): 5 points (목표: 6) ⚠️
  - Team 07 (QA): 3 points (목표: 3) ✅
  - Team 09 (DevOps): 2 points (목표: 2) ✅

🌟 NPS 영향:
  - 어제: 54
  - 오늘: 56
  - 변화: +2점 ⬆️

📅 내일 계획:
  - 새 프로젝트 1개 시작 예정
  - Sprint 진행도: 40% 목표
  - 배포: v1.2.25 준비

💡 다음 STANDUP: 내일 09:00 UTC
```

---

## 🚨 CRITICAL vs HIGH vs MEDIUM vs LOW

### 🔴 CRITICAL (P0) — 즉시 대응
```
상황: 프로덕션 장애
예: 보안 취약점, 데이터 손실, 서비스 전체 다운
응답: < 1시간 배포
팀: 모든 팀 동원
```

### 🟠 HIGH (P1) — 이번 Sprint 내 배포
```
상황: 주요 기능 버그
예: 사용자 30% 이상 영향, 매출 손실
응답: < 1일 배포
팀: Team 05, 06, 07
```

### 🟡 MEDIUM (P2) — 이번 달 내 배포
```
상황: 부분적 기능 버그
예: UI 오류, 성능 저하
응답: < 1주 배포
팀: 관련 팀
```

### 🟢 LOW (P3) — Backlog
```
상황: 미래 개선 사항
예: 문서화, 리팩토링
응답: 우선순위 낮음
팀: 여유 있을 때
```

---

## 💬 JARVIS와 자연스럽게 대화하기

### ✅ GOOD (자연스러움)
```
"새 프로젝트를 시작하고 싶어"
→ JARVIS: 자동으로 `/mission create` 프로세스 제시

"지금 상황이 어떻게 돼?"
→ JARVIS: Sprint report 제시

"스테이징에 배포해줄래?"
→ JARVIS: Deploy staging 프로세스 진행

"블로커가 있는데 도움이 필요해"
→ JARVIS: 관련 팀 자동 호출
```

### ❌ BAD (딱딱함)
```
"deploy"
→ 뭘 배포? Staging? Prod? Version?

"/deploy"
→ 필수 파라미터 누락

"배포해"
→ 너무 모호함
```

---

## 📊 DAILY DEPLOYMENT CHECKLIST

매일 배포할 때 확인 사항:

```
배포 전:
  ☐ Sprint review 완료
  ☐ 모든 테스트 통과 (98% 이상)
  ☐ Code review 완료
  ☐ Security 검증 완료
  ☐ Staging 테스트 완료

배포:
  ☐ /deploy staging v1.2.X 실행
  ☐ Staging 테스트 최종 확인
  ☐ /deploy prod v1.2.X 실행
  ☐ Blue-Green 전환 확인
  ☐ 헬스 체크 통과

배포 후:
  ☐ 24시간 모니터링
  ☐ 에러 로그 확인 (0.1% 미만)
  ☐ 성능 메트릭 확인
  ☐ 사용자 피드백 수집
  ☐ Daily summary 생성
```

---

## 🎯 WEEKLY GOALS

| 항목 | 목표 | 현재 | 상태 |
|------|------|------|------|
| 배포 횟수 | 5개 | 2개 | ⏳ |
| 새 피처 | 7개 | 3개 | ⏳ |
| 버그 수정 | 10개 | 6개 | ⏳ |
| 스킬 활성화 | 42/70 | 29/70 | ⏳ |
| NPS 변화 | +5점 | +2점 | ⏳ |
| 배포 성공률 | 100% | 100% | ✅ |

---

## 🤖 JARVIS Commands Quick Ref

| 명령어 | 용도 | 예시 |
|--------|------|------|
| `/mission create` | 새 프로젝트 시작 | `/mission create "사용자 프로필"` |
| `/sprint review` | Sprint 진행도 확인 | `/sprint review` |
| `/task create` | 작업 추가 | `/task create "JWT 인증"` |
| `/deploy staging` | Staging 배포 | `/deploy staging v1.2.24` |
| `/deploy prod` | Production 배포 | `/deploy prod v1.2.24` |
| `/standup` | 일일 리포트 | `/standup` |
| `/status` | 전체 상황 | `/status` |
| `/summary` | 일일 요약 | `/summary` |
| `/priority` | 우선순위 변경 | `/priority T-001 CRITICAL` |
| `/help` | 도움말 | `/help` |

---

## 📈 SUCCESS METRICS

### 회사 운영 성공 기준

| 메트릭 | 목표 | 현재 | Track |
|--------|------|------|-------|
| **배포 자동화** | 99% | 95% | 📈 |
| **일일 배포** | 1 feature | 0.4 | 📈 |
| **버그 재발** | 0% | 2% | 📉 |
| **NPS 성장** | +5/월 | +2/월 | 📈 |
| **팀 속도** | 40pts/sprint | 30pts/sprint | 📈 |
| **배포 시간** | < 10min | 15min | 📉 |

---

## ✨ JARVIS v2 핵심 특징

✅ **자연스러운 대화** — 딱딱한 명령어 불필요
✅ **자동 라우팅** — 옳은 팀으로 자동 할당
✅ **스킬 감지** — 부족한 능력 자동 감지
✅ **진행도 표시** — 실시간 ▓▓▓░░ 진행률
✅ **일일 리듬** — 09:00 ~ 18:00 정해진 흐름
✅ **배포 자동화** — 스테이징 → Prod 자동 관리
✅ **모니터링** — 배포 후 24시간 감시
✅ **블로커 감지** — 막힌 부분 자동 대응

---

**Status: 🟢 READY FOR DAILY OPERATIONS**

**매일 새로운 프로젝트를 Telegram으로 지시하고 JARVIS가 자동으로 구현합니다!**

