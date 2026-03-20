# Master Execution Blueprint

Updated: 2026-03-07
Status: active
Owner: product + engineering + design + ops

## 🎯 Why This Document Exists

이 문서는 현재 프로젝트의 잔여 작업을 개발자, 기획자, 작업자가 같은 기준으로 이해하고 실행할 수 있도록 다시 구조화한 실행 기준 문서다.

기존 문서들은 목적별로 흩어져 있고 일부는 인코딩 손상, 완료 시점 차이, 범위 중복이 있어 다음 문제가 있었다.

- 무엇이 이미 끝났는지와 무엇이 실제 잔여 작업인지 구분이 어려움
- 화면 구현 목표와 운영 안정화 목표가 섞여 있음
- 배포 전 필수 작업과 향후 고도화 작업의 우선순위가 혼재됨

이 문서의 목적은 세 가지다.

1. 현재 상태를 현실 기준으로 다시 잠금한다.
2. 남은 작업을 실행 가능한 워크스트림으로 재편한다.
3. 특히 화면 구현을 사용자 친화적으로 다시 정의한다.

---

## 🧭 Canonical Sources Reviewed

이 문서는 아래 문서들을 교차 검토해 재구성했다.

- [PRD.md](/d:/Project/docs/PRD.md)
- [IA.md](/d:/Project/docs/IA.md)
- [DoD.md](/d:/Project/docs/DoD.md)
- [RELEASE_SAFE_CHANGE_CHECKLIST.md](/d:/Project/docs/RELEASE_SAFE_CHANGE_CHECKLIST.md)
- [GROWTH_AUTOMATION_PARALLEL_UPDATE_2026-03-07.md](/d:/Project/docs/GROWTH_AUTOMATION_PARALLEL_UPDATE_2026-03-07.md)
- [RUNBOOK_GROWTH_AUTOMATION.md](/d:/Project/docs/RUNBOOK_GROWTH_AUTOMATION.md)
- [STATUS.md](/d:/Project/STATUS.md)
- [INCOMPLETE_TASKS_SCAN.md](/d:/Project/INCOMPLETE_TASKS_SCAN.md)

---

## ✅ Verified Current State

### 1. Growth Automation

현재 Growth Automation의 P0 기능 바인딩과 주요 P1 보강은 완료된 상태다.

- Hub, Contacts, Journeys, Ops의 핵심 화면은 구현됨
- 기존 백엔드 엔드포인트를 재사용해 UI 연동이 완료됨
- 회귀 검증은 2026-03-07 기준 `11 passed`까지 확인됨
- 브라우저 정적 스모크도 통과함

결론:
Growth Automation은 "미구현 영역"이 아니라 "운영 안정화 + 사용자 경험 고도화 단계"로 봐야 한다.

### 2. Platform / Deployment / Runtime

운영 안정화 측면의 잔여 리스크는 아직 남아 있다.

- `/api/health` 500 원인 미정리
- Flask 런타임 바인딩 로그 가시성 부족
- Docker 데몬 접근/이미지 조회 이슈로 컨테이너 검증 미완료
- 수정 파일이 매우 많아 배포 단위가 흐려져 있음

결론:
현재 가장 위험한 지점은 "새 기능 부족"보다 "검증되지 않은 배포 묶음"이다.

### 3. Historical Backlog

기존 미완료 스캔 문서에는 여전히 유효한 잔여 작업이 있다.

- SNS Automation 일부 프론트/백엔드 고도화
- Review 플랫폼 일부 프론트/스크래퍼 고도화
- Telegram scheduler 연결 TODO
- CooCook Phase 2-3 잔여 기능
- 테스트, 문서, 배포 자동화 마감

결론:
백로그는 존재하지만, 모든 항목을 동등 우선순위로 보면 안 된다.

---

## 🧱 Execution Structure

전체 잔여 작업은 아래 4개 워크스트림으로 관리한다.

### A. 🛟 Runtime Stabilization

목표:
로컬/배포 환경에서 핵심 서비스가 예측 가능하게 뜨고, 장애 원인과 복구 경로가 명확해야 한다.

포함 작업:

- `/api/health` 500 원인 분석 및 수정
- 앱 시작 로그, 포트 바인딩 로그, 실패 로그 표준화
- Docker Compose 기반 기동 재검증
- 배포 경로별 canonical workflow 고정
- 롤백 기준과 검증 절차 정리

완료 기준:

- health 응답이 일관되게 200 또는 의도된 auth status를 반환
- 로컬/컨테이너 기동 로그에 포트와 서비스 상태가 명확히 출력
- 핵심 진입 페이지와 API 헬스체크가 다시 검증됨

### B. 🧩 Product Completion

목표:
각 제품 영역에서 "기획 문서에는 있는데 실사용 흐름에는 아직 약한 부분"을 마감한다.

포함 작업:

- SNS Automation 잔여 화면/엔드포인트
- Review 플랫폼 고도화
- Telegram scheduler chat ID 연동
- CooCook Phase 2-3 구현
- 관련 모델, 마이그레이션, API 문서 보완

완료 기준:

- 각 제품 흐름에서 핵심 액션 1개 이상이 end-to-end로 검증됨
- 백엔드 계약과 화면 텍스트가 일치함
- 테스트가 기능 단위로 최소 smoke 이상 확보됨

### C. 🖥️ User-Friendly Screen Upgrade

목표:
화면이 "구현되어 보이는 수준"이 아니라 "처음 보는 사용자도 이해하고 행동할 수 있는 수준"이 되어야 한다.

핵심 원칙:

- 첫 화면 5초 안에 목적을 이해하게 한다
- 숫자만 보여주지 말고 의미와 다음 행동을 함께 제시한다
- 테이블은 증거 영역이고, 액션은 상단에서 바로 수행 가능해야 한다
- 빈 상태와 오류 상태도 친절해야 한다
- 모바일에서도 핵심 CTA가 접히지 않아야 한다

완료 기준:

- Hero, summary, action, evidence, feedback 구조가 모든 핵심 화면에 일관됨
- 각 화면의 primary CTA가 1개로 선명함
- empty, loading, error, success 상태 메시지가 사용자 언어로 제공됨

### D. 🧪 Validation and Release Control

목표:
변경이 많아도 배포와 검증을 작은 단위로 통제할 수 있어야 한다.

포함 작업:

- 기능별 smoke 시나리오 표준화
- 공통 모듈 변경 시 회귀 범위 명시
- preview -> smoke -> monitor -> release 절차 고정
- 변경 묶음 기준으로 릴리스 노트 작성

완료 기준:

- 핵심 사용자 경로별 smoke checklist 존재
- 롤백 대상 커밋/배포 URL이 명시됨
- 배포 후 30분 관찰 규칙이 실제로 운영됨

---

## 🔥 Priority Model

이번 우선순위는 운영 리스크보다 기능 부족과 화면 부족을 먼저 해소하는 방향으로 재정렬한다.

### P0: 기능 완성 + 화면 완성

이 단계는 "사용자가 실제로 체감하는 미완성과 불친절함"을 먼저 줄이는 단계다.

- SNS Automation 핵심 화면 완성
- Review Platform 핵심 화면 완성
- Growth Automation 화면을 더 직관적이고 친화적으로 보강
- Telegram scheduler 실사용 연결
- CooCook 주요 사용자 흐름 완성

### P1: 경험 고도화

- richer empty/loading/error states
- 더 강한 onboarding / helper copy
- 모바일 우선 CTA 정리
- inline charts / saved filters / compare UX 강화
- 상세 패널과 evidence 영역의 설명력 강화

### P2: 운영 안정화 및 배포 통제

- `/api/health` 500 해결
- 시작/바인딩/장애 로그 정리
- Docker/배포 검증 재실행
- smoke / rollback 체계 정리
- release monitoring 체계 고정

---

## 👥 Role-Based Responsibility Map

### Product / Planner

산출물:

- 각 기능의 한 줄 acceptance criteria
- 비목표 명시
- 각 화면의 primary CTA 정의
- 이벤트명, 상태명, 사용자 용어 통일

체크포인트:

- 사용자 질문이 화면에서 바로 해소되는가
- 같은 개념이 문서마다 다른 이름으로 쓰이지 않는가

### Frontend

산출물:

- Hero + summary + action + evidence + feedback 레이아웃 정렬
- empty/loading/error/success state UX 보강
- 모바일 CTA 유지
- shared runtime 영향 범위 명시

체크포인트:

- "무엇을 해야 하는지"가 화면에서 바로 보이는가
- 숫자와 행동 버튼이 분리되지 않았는가

### Backend

산출물:

- health / readiness / diagnostics 정리
- payload shape 안정화
- optional field fallback 규칙 유지
- 로그와 에러 응답 일관화

체크포인트:

- UI가 기대하는 최소 필드를 계속 제공하는가
- 실패 시 화면이 설명 가능한 형태로 떨어지는가

### QA / Ops

산출물:

- 기능별 smoke 시나리오
- 오류경로 점검표
- 배포 후 30분 모니터링 체크리스트
- rollback trigger 기준

체크포인트:

- 로그인부터 핵심 액션까지 한 번에 재현 가능한가
- 실패 시 복구 절차가 runbook에 있는가

---

## 🖼️ Screen UX Upgrade Guide

이 섹션은 "화면을 더 사용자 친화적으로 구현"하기 위한 기준이다.

### 1. Shared UX Rules

모든 핵심 화면에 공통 적용:

- Hero에는 한 줄 설명 + 현재 상태 + 대표 CTA를 넣는다
- KPI 카드에는 수치와 함께 해석 문장을 붙인다
- 테이블 위에는 "왜 이 리스트를 보고 있는지"를 설명한다
- 실패 상태에는 복구 버튼 또는 다음 행동을 같이 둔다
- 빈 상태에는 삽화, 짧은 설명, 시작 버튼을 같이 제공한다

권장 UI 카피 톤:

- 짧고 명령형보다 안내형
- 기술 용어보다 사용자 목적 중심
- 예: `DLQ open 12건` 대신 `복구가 필요한 실패 작업 12건`

공통 시각 자산 방향:

- 배경은 단색보다 부드러운 gradient 또는 pattern을 사용한다
- 상태 표현은 badge + icon + 짧은 문장을 함께 쓴다
- 숫자 카드에는 작은 보조 그래프나 변화 표시를 붙인다
- 설명 블록에는 아이콘을 적극 사용해 스캔 속도를 높인다

공통 이모지 세트:

- `✨` 새 기능
- `📌` 핵심 포인트
- `👀` 확인 필요
- `✅` 완료/정상
- `⚠️` 주의
- `🚀` 빠른 시작
- `🧩` 연결 기능
- `🎯` 주요 목표

공통 이미지 스타일 가이드:

- 지나치게 추상적인 스톡 이미지보다 제품 맥락이 읽히는 일러스트 선호
- 대시보드형 화면은 data visualization motif 사용
- CRM/contacts 화면은 사람, 카드, 연결 흐름 중심
- ops 화면은 경고만이 아니라 복구/정상화가 함께 느껴지는 그래픽 사용

### 2. Hub

사용자 질문:
"오늘 무엇을 먼저 봐야 하나?"

개선 포인트:

- Hero에 오늘의 운영 상태 요약 배치
- 추천 카드에 우선순위 배지 표시
- summary 카드는 숫자보다 변화 방향을 강조
- 최근 이벤트 테이블은 "방금 일어난 일"이라는 맥락을 붙임

추천 이미지 방향:

- 📈 라인 차트형 일러스트
- 🧭 대시보드 나침반 또는 신호등형 상태 그래픽

추천 이모지:

- `🟢` 안정
- `🟡` 주의
- `🔴` 대응 필요
- `⚡` 즉시 조치

### 3. Contacts

사용자 질문:
"리드가 잘 들어오고 있고, 누구를 먼저 봐야 하나?"

개선 포인트:

- 리드 생성 composer를 화면 상단 CTA 영역에 고정
- segment chip은 설명형 라벨 사용
- detail panel은 "선택한 고객의 다음 액션" 중심으로 구성
- 테이블 첫 열에 상태 배지와 신뢰 신호를 같이 표시

추천 이미지 방향:

- 👥 사람/그룹 기반 일러스트
- ✉️ 연락처 카드 또는 인입 파이프라인 그래픽

추천 UX 카피:

- `Lead 24명` 대신 `새로 유입된 잠재 고객 24명`
- `At Risk` 대신 `이탈 가능성이 높은 고객`

### 4. Journeys

사용자 질문:
"사용자가 어느 단계에서 막히고 있나?"

개선 포인트:

- progression 버튼은 단계 흐름과 함께 보여준다
- stage card에는 현재 수치 + 병목 설명 + 다음 버튼을 함께 둔다
- recent evidence는 이벤트명보다 사용자 행동 서사 중심으로 표시한다

추천 이미지 방향:

- 🛤️ 단계형 여정 지도
- 🔄 전환 흐름 다이어그램

추천 UX 카피:

- `signup_completed` 대신 `회원가입 완료`
- `key_action_completed` 대신 `핵심 행동 완료`

### 5. Ops

사용자 질문:
"무엇이 실패했고, 무엇부터 복구해야 하나?"

개선 포인트:

- 실패 이벤트와 DLQ를 시각적으로 분리
- severity 배지는 색상만이 아니라 텍스트도 포함
- replay 버튼은 영향 범위와 최근 실패 시간 표시와 함께 배치
- empty state는 `현재 복구할 항목이 없습니다` 식으로 안심 메시지 제공

추천 이미지 방향:

- 🛠️ 수리/복구 아이콘
- 🚨 경고와 해결을 함께 보여주는 운영 일러스트

추천 UX 카피:

- `DLQ open` 대신 `복구 대기 중`
- `replay` 대신 `다시 처리`

---

## 🧠 Feature Completion Blueprint

이 섹션은 기능 부족을 우선 해소하기 위한 제품 중심 실행표다.

### 1. SNS Automation

현재 판단:

- 페이지 수는 있으나 실제 사용 흐름이 덜 살아 있음
- "무엇을 할 수 있는 제품인지"는 보이지만 "지금 당장 어떻게 쓰는지"는 약함

우선 구현 대상:

- `create.html`
- `link-in-bio.html`
- `monetize.html`
- `viral.html`
- `competitor.html`

사용자 관점 핵심 시나리오:

1. 콘텐츠를 만들고 예약한다
2. 링크 인 바이오를 편집하고 클릭 반응을 본다
3. 수익화 포인트를 확인하고 다음 액션을 결정한다
4. 경쟁 계정을 비교해 개선 아이디어를 얻는다

필수 기능 기준:

- 명확한 생성 CTA
- 결과 미리보기
- 저장/실행 이후 피드백
- 성과 요약 카드
- 최근 활동 리스트

화면 친화성 기준:

- 첫 화면에 "오늘 할 일" 카드 제공
- AI 추천/자동화/직접 편집의 차이를 카드형으로 설명
- 빈 상태에 예시 템플릿과 추천 시작 버튼 제공

추천 이미지:

- `🪄` 생성 마법봉형 일러스트
- `🔗` 링크 카드 목업
- `📣` 캠페인/바이럴 확산형 그래픽

### 2. Review Platform

현재 판단:

- 기본 화면은 존재하지만 제품 서사가 약하고, 자동화 가치가 직관적으로 드러나지 않음

우선 구현 대상:

- `aggregator.html`
- `applications.html`
- `auto-apply.html`

사용자 관점 핵심 시나리오:

1. 진행 가능한 캠페인을 빠르게 찾는다
2. 신청 현황과 성공 가능성을 확인한다
3. 자동 신청 조건을 설정하고 결과를 검토한다

필수 기능 기준:

- 캠페인 필터
- 신청 상태 추적
- 자동 신청 규칙 편집
- 계정/자격 상태 표시
- 추천 캠페인 근거 표시

화면 친화성 기준:

- 카드 제목만 보지 않아도 "왜 추천되는지" 설명
- 신청 내역에 단계별 진행 배지 표시
- 자동 신청 화면에 위험/제외 조건을 명확히 구분

추천 이미지:

- `📝` 지원서/검토 문서형 그래픽
- `⭐` 평점/리뷰 강조 그래픽
- `🤖` 자동 신청 플로우 일러스트

### 3. Growth Automation

현재 판단:

- 기능은 살아 있으나 운영 도구 냄새가 강해 일반 사용자 입장에서 다소 건조함

고도화 방향:

- summary를 해석형 문장으로 전환
- recommendation을 행동 중심으로 재작성
- detail panel에 "이 항목을 왜 보고 있는지" 설명 추가
- evidence 테이블 위에 컨텍스트 문장 배치

추가 고도화 항목:

- 오늘의 할 일 패널
- 상태별 quick action strip
- 성공/실패 이후 다음 행동 제안
- 모바일용 compact card mode

추천 이미지:

- `📈` 퍼널/추세 그래픽
- `🧭` 운영 내비게이션형 그래픽
- `🛠️` 복구/자동화 결합 그래픽

### 4. CooCook

현재 판단:

- 기능 범위는 넓지만 사용자 가치가 즉시 보이는 대표 흐름이 부족함

우선 사용자 흐름:

1. 레시피 탐색
2. 재료 기반 추천
3. 쇼핑리스트 생성
4. 예약/피드/리뷰 연결

필수 기능 기준:

- 검색과 필터의 명확한 시작점
- 레시피 상세의 신뢰 정보
- 쇼핑리스트 생성 CTA
- 저장/공유/재방문 흐름

추천 이미지:

- `🍳` 조리/레시피 카드형 비주얼
- `🛒` 장보기 체크리스트형 비주얼
- `👩‍🍳` 셰프/커뮤니티형 이미지

### 5. Telegram Scheduler

현재 판단:

- 구조는 거의 있으나 실제 사용자 연결 고리가 미완성

우선 해결:

- 사용자 chat ID 연결
- 설정 화면에서 상태 확인
- 테스트 메시지 발송
- 실패 시 안내 메시지

친화성 기준:

- 설정 완료 여부를 한 줄로 보여준다
- 연결 실패 원인을 사람이 이해할 수 있게 보여준다

추천 이미지:

- `📨` 메시지 발송 상태 그래픽
- `🔔` 알림 연결형 아이콘

---

## 🎨 User-Friendly Screen Implementation Rules

화면 구현은 아래 규칙을 만족해야 한다.

### Rule 1. 페이지마다 대표 행동을 1개로 압축한다

한 화면에서 가장 중요한 행동은 1개만 hero 근처에 강하게 노출한다.

예시:

- SNS Create: `콘텐츠 만들기`
- Review Auto Apply: `자동 신청 규칙 설정`
- Contacts: `새 리드 등록`
- Ops: `실패 작업 다시 처리`

### Rule 2. 수치만 두지 말고 해석을 붙인다

나쁜 예:

- `Conversion 12.4%`

좋은 예:

- `전환율 12.4%`
- `지난주보다 상승 중입니다`

### Rule 3. 빈 화면도 제품처럼 보이게 만든다

빈 상태에는 아래 3개가 있어야 한다.

- 설명 문장
- 시작 버튼
- 예시 또는 템플릿

### Rule 4. 에러는 개발자 언어가 아니라 사용자 언어로 쓴다

나쁜 예:

- `Fetch failed`

좋은 예:

- `데이터를 불러오지 못했습니다`
- `잠시 후 다시 시도하거나 연결 상태를 확인해 주세요`

### Rule 5. 테이블은 증거, 카드는 방향이다

- 카드는 지금 판단해야 할 것을 보여준다
- 테이블은 그 판단의 근거를 보여준다

### Rule 6. 모바일에서 의미가 사라지지 않게 한다

- 긴 비교표는 카드 뷰 대체 수단 제공
- CTA는 sticky 또는 상단 고정 고려
- 상태 배지는 2줄 이상 깨지지 않게 설계

---

## 🧪 Definition of Better Screens

화면은 아래 조건을 만족해야 "친화적 구현"으로 인정한다.

### Readability

- 5초 안에 화면 목적이 이해된다
- 첫 시선에서 primary CTA가 보인다
- 경고/오류/정상 상태가 색과 텍스트로 모두 구분된다

### Operability

- 한 화면 안에서 최소 1개의 핵심 작업을 끝낼 수 있다
- 액션 후 결과가 즉시 요약 카드나 리스트에 반영된다
- 실패해도 다음 행동이 제시된다

### Mobile Fit

- 핵심 CTA가 fold 아래로 완전히 숨지 않는다
- 긴 테이블은 카드 요약 또는 수평 스크롤 대안이 있다
- 상태 배지와 숫자가 뭉개지지 않는다

---

## 📦 Work Breakdown by Deliverable

### Deliverable 1. User-Friendly Screen Pack

- SNS Automation 화면 재설계
- Review Platform 주요 화면 정리
- 공통 UX 카피 정비
- 이미지/아이콘/상태배지 체계화

### Deliverable 2. Growth Automation Hardening Pack

- 인증 포함 브라우저 smoke
- richer error-path handling
- empty/loading state polish
- 운영 runbook 보강

### Deliverable 3. Product Backlog Closure Pack

- Telegram scheduler TODO 해소
- CooCook Phase 2-3 잔여 기능
- 관련 모델/마이그레이션/문서/테스트 정리

### Deliverable 4. Runtime Safety Pack

- health 오류 수정
- 시작 로그 표준화
- Docker 기동 재검증
- release smoke checklist 갱신

---

## 🗓️ Recommended Execution Order

### Phase 1. 핵심 화면 완성

- SNS / Review 핵심 화면 UX 개선
- 공통 hero / summary / action / evidence / feedback 구조 통일
- empty/error/success state 일괄 보강

### Phase 2. 핵심 기능 완성

- Telegram / CooCook / 잔여 API 및 모델 작업
- 각 제품의 대표 사용자 흐름 1개 이상 완성
- 문서와 acceptance criteria 동기화

### Phase 3. Growth Automation polish

- recommendation / evidence / action UX 강화
- 인증 포함 실동작 smoke
- 상세 패널, quick action, helper copy 개선

### Phase 4. 운영 안정화

- preview 배포
- smoke
- health/log/runtime 검증
- release sign-off

---

## 📝 Team Working Rules

작업자는 아래 규칙을 지켜야 한다.

1. 작업 시작 전에 변경 파일 목록을 먼저 적는다.
2. 각 기능은 acceptance criteria 한 줄로 잠근다.
3. 공통 모듈 변경 시 영향 화면을 같이 기록한다.
4. UI는 fallback이 없는 상태로 배포하지 않는다.
5. 문서와 코드의 용어가 다르면 문서를 먼저 맞춘다.
6. 배포 전에는 `핵심 액션 1회 + 오류경로 1회`를 반드시 확인한다.

---

## 🚦Immediate Next Actions

가장 먼저 실행할 권장 순서는 아래와 같다.

1. SNS Automation, Review Platform, CooCook, Telegram을 기능 기준으로 다시 티켓화한다.
2. 모든 핵심 화면에 대해 Hero, CTA, evidence, feedback 구조 점검표를 만든다.
3. Growth Automation은 추가 구현보다 UX polish 대상으로 관리한다.
4. 각 화면에 맞는 이미지/아이콘/상태 배지 체계를 먼저 확정한다.
5. 운영 안정화는 별도 후속 묶음으로 분리한다.

---

## ✨ Final Direction

이 프로젝트의 다음 단계는 아래 순서로 가야 한다.

- 먼저 기능 부족을 메운다
- 그다음 화면을 더 쉽게 이해되고 쓰기 좋게 만든다
- 운영 안정화는 그 다음 묶음으로 처리한다

즉, 지금 가장 중요한 기준은 아래 세 가지다.

- 사용자가 실제로 할 수 있는 일이 늘어나는가
- 화면이 더 친절하고 명확해지는가
- 제품별 대표 흐름이 끝까지 이어지는가

이 기준으로 움직이면 개발자, 기획자, 작업자 모두 같은 목표를 보고 기능과 화면 품질을 빠르게 끌어올릴 수 있다.
# 2026-03-10 Validation Update

- `GET /api/health` is now verified at `200` on the current codebase. Older notes calling out a `500` should be treated as historical.
- The login deep-link flow now honors `next`, including demo login. Direct entry to `/web/coocook/index.html` returns the user to CooCook after authentication.
- The core `CooCook` browser flow was revalidated end-to-end: `hub -> shopping list -> item check`.
- Remaining `CooCook` backlog should be treated as phase expansion and performance work, not basic flow recovery.
