# 🎯 의사결정 트리

> **마지막 업데이트:** 2026-02-23 | **권한:** Chief Dispatcher | **상태:** ✅ ACTIVE

---

## ❓ "누가 이 결정을 내리나요?"

**상황에 맞는 담당자를 찾아보세요.**

---

## 🔴 BLOCKER (즉시)

**"앱이 안 켜져요 / 배포 실패 / 데이터 손실"**

```
→ 09-DevOps (배포 문제)
  또는 05-Backend (런타임 에러)
  또는 01-Dispatcher (즉시 에스컬레이션)

SLA: < 2시간
```

---

## 🟠 CRITICAL (4시간 내)

### 우선순위 결정
**"어떤 기능을 먼저 할까?"**

```
1. 기능이 명확한가?
   → YES: 01-Dispatcher (WSJF 우선순위)
   → NO: 02-PM + 03-Analyst (정의 필요)

결정: 01-Dispatcher
SLA: < 4시간
```

### 기술 설계
**"어떤 기술을 써야 할까?"**

```
1. 프레임워크 선택 (FastAPI vs Flask)
   → 04-Architect (기술 설계 전권)

2. 데이터베이스 (SQL vs NoSQL)
   → 04-Architect + 05-Backend

3. 배포 전략 (Blue-Green vs Canary)
   → 04-Architect + 09-DevOps

결정: 04-Solution Architect
SLA: < 4시간
```

### 제품 방향
**"이 기능을 정말 빌드해야 할까?"**

```
1. 시장 요구가 있나?
   → 03-Analyst (시장 분석)

2. 제품 로드맵에 맞나?
   → 02-PM (제품 전략)

최종 결정: 02-PM (with 03 input)
SLA: < 4시간
```

### 보안 / 규정
**"GDPR 준수 하나요? 보안은?"**

```
1. 개인정보 처리
   → 08-Security (GDPR, 데이터 보호)

2. 취약점 발견
   → 08-Security (CVSS 평가)

3. 보안 감시
   → 08-Security (STRIDE, OWASP)

결정: 08-Security Auditor
SLA: < 4시간
```

### QA / 테스트
**"테스트 전략은? 버그는?"**

```
1. 테스트 계획
   → 07-QA (테스트 피라미드)

2. 버그 심각도
   → 07-QA (우선순위 지정)

3. 자동화 전략
   → 07-QA (CI/CD 테스트)

결정: 07-QA Engineer
SLA: < 4시간
```

### 배포
**"언제 배포할까? 어디로?"**

```
1. 배포 일정
   → 09-DevOps + 01-Dispatcher (조율)

2. 인프라 요구
   → 09-DevOps (AWS 설정)

3. 롤백 계획
   → 09-DevOps (Blue-Green)

결정: 09-DevOps Engineer
SLA: < 4시간
```

---

## 🟡 NORMAL (1일 내)

### API 설계
**"엔드포인트 이름이 뭐야? 응답 포맷은?"**

```
기본: 04-Architect (OpenAPI 정의)
구현: 05-Backend (실제 코드)
테스트: 07-QA (E2E 테스트)
```

### 데이터베이스 스키마
**"테이블 구조는? 정규화는?"**

```
설계: 04-Architect + 05-Backend
리뷰: 04-Architect
구현: 05-Backend
```

### UI/UX
**"버튼은 어디에? 색상은?"**

```
설계: 06-Frontend (Atomic Design)
접근성: 06-Frontend (WCAG)
리뷰: 02-PM (사용자 관점)
```

### 코드 품질
**"테스트 커버리지는? 코드 리뷰?"**

```
목표: 80% 커버리지 (R9)
리뷰: 07-QA
결정: 05-Backend (backend) 또는 06-Frontend (frontend)
```

---

## 🟢 ROUTINE (3일 내)

### 문서 작성
**"문서는 어디에? 어떤 형식?"**

```
필수: docs/standards/ 템플릿 사용 (R4)
리뷰: 10-Reporter
```

### 일일 스탠드업
**"오늘 뭐 했어?"**

```
진행: 각 팀 자체
리포팅: 10-Reporter (대시보드)
```

### 스킬 공유
**"이거 어떻게 했어?"**

```
진행: 개별 에이전트
공유: 주간 (R6)
기록: 10-Reporter
```

---

## 🎯 의사결정 매트릭스

| 문제 타입 | 1차 담당 | 2차 협의 | 최종 결정자 | SLA |
|----------|---------|---------|-----------|-----|
| **우선순위** | 01-Dispatcher | 02/03 | 01 | 4h |
| **기술 설계** | 04-Architect | 05/06 | 04 | 4h |
| **제품 방향** | 02-PM | 03-Analyst | 02 | 4h |
| **구현 방식** | 05 or 06 | 04-Architect | 해당 팀 | 2h |
| **테스트 전략** | 07-QA | 05/06 | 07 | 4h |
| **보안** | 08-Security | 04/05/06 | 08 | 4h |
| **배포** | 09-DevOps | 04/05/06 | 09 | 4h |
| **갈등** | 해당 팀들 | ConsultationBus | 01-Dispatcher | < 2h |

---

## ⚡ 빠른 결정 (< 30분)

**명확한 기술 기준이 있으면 즉시 결정**

| 상황 | 결정자 | 근거 |
|------|--------|------|
| **리팩토링** | 해당 팀 리드 | 코드 품질 목표 (R9) |
| **변수명 변경** | 개발자 스스로 | 코드 리뷰로 사후 검증 |
| **테스트 추가** | 07-QA | 커버리지 80% 목표 (R9) |
| **문서 업데이트** | 해당 작성자 | 템플릿 이미 정의됨 (R4) |
| **Slack 메시지** | 개인 판단 | 긴급 시에만 에스컬레이션 |

---

## 🔗 갈등 해결 (Conflict Resolution)

### 단계별 프로세스

```
[Conflict Detected]
       ↓
Step 1: 당사자끼리 대화 (1시간)
       ↓
       성공? → End ✅
       실패? ↓
Step 2: 관련 에이전트 회의 (2시간)
       (예: 기술 갈등 → 04, 05, 06)
       ↓
       성공? → End ✅
       실패? ↓
Step 3: 01-Dispatcher 중재 (< 2시간)
       (최종 결정)
       ↓
[Decision Made & Documented]
```

### 예시

**갈등:** "FastAPI 쓸까 Flask 쓸까?"

```
Step 1 실패: 05-Backend와 04-Architect 의견 다름
Step 2: 둘이 pros/cons 정리해서 회의
Step 2 실패: 이해는 하되 여전히 다른 의견
Step 3: 01-Dispatcher가 "FastAPI (이유: ORM 통합)"로 결정
→ 결정사항 ADR로 기록
```

---

## 📋 의사결정 기록

**모든 주요 결정은 다음 위치에 기록:**

| 결정 타입 | 기록 위치 |
|----------|---------|
| **아키텍처** | `docs/generated/adr/` (ADR-00X) |
| **제품** | `docs/generated/prd/` |
| **테스트** | `docs/generated/test_plans/` |
| **보안** | `docs/generated/security/` |
| **배포** | `docs/generated/runbooks/` |
| **기타** | `docs/generated/rfc/` (RFC) |

**템플릿:** `docs/standards/`

---

## 🎓 의사결정 권한 (RACI)

### R = Responsible (실행)
### A = Accountable (최종 책임)
### C = Consulted (협의)
### I = Informed (보고)

예시: "CooCook API 설계"

| 역할 | Status |
|------|--------|
| 04-Architect | **A** (최종 책임) |
| 05-Backend | **R** (구현) |
| 06-Frontend | **C** (API 사용) |
| 07-QA | **C** (테스트 전략) |
| 09-DevOps | **I** (배포 고려사항) |
| 01-Dispatcher | **I** (우선순위만 정의) |

완전한 RACI는 `docs/RACI_MATRIX.md` 참조

---

## 🚨 에스컬레이션 경로

```
일반 질문
    ↓
해당 에이전트 (< 1d)
    ↓
   Success? → End
    ↓
   No (분쟁/불확실)
    ↓
ConsultationBus (< 4h)
    ↓
   Success? → End
    ↓
   No (여전히 불명확)
    ↓
01-Dispatcher (< 2h)
    ↓
[FINAL DECISION]
```

---

## ✅ 의사결정 체크리스트

새로운 결정을 내릴 때:

- [ ] 담당자가 명확한가? (RACI에서 찾기)
- [ ] SLA가 명확한가? (위 매트릭스 참조)
- [ ] 협의 필요한가? (불확실성 > 70%?)
- [ ] 갈등이 있나? (01-Dispatcher 호출)
- [ ] 결정을 기록했나? (ADR/RFC/문서화)
- [ ] 팀에 알렸나? (10-Reporter)

---

**참고:** 모든 결정 권한은 다음 규칙 아래 작동합니다:
- R1: 순차적 사고 (먼저 생각하고 결정)
- R2: 갈등 에스컬레이션 (분쟁은 즉시 보고)
- R3: 협의 (불확실성 > 70%)
- R10: 회고 (결정 후 되돌아보기)

---

**마지막 업데이트:** 2026-02-23
**다음 업데이트:** 2026-02-24 (M-002 기술 결정 후)
