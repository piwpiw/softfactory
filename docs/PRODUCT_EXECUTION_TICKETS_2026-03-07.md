# Product Execution Tickets

Updated: 2026-03-07
Status: active
Owner: product + frontend + backend + QA

이 문서는 [MASTER_EXECUTION_BLUEPRINT_2026-03-07.md](/d:/Project/docs/MASTER_EXECUTION_BLUEPRINT_2026-03-07.md) 를 실제 작업 단위로 분해한 실행 티켓 문서다.

목표는 단순하다.

- 기능 부족을 빠르게 메운다
- 화면을 더 사용자 친화적으로 바꾼다
- 개발자가 바로 구현할 수 있는 수준까지 작업 범위를 고정한다

---

## 🎯 Priority Order

### P0

- SNS Automation 핵심 페이지 완성
- Review Platform 핵심 페이지 완성
- Growth Automation UX polish
- Telegram Scheduler 연결 완성
- CooCook 대표 흐름 완성

### P1

- 모바일 최적화 보강
- helper copy / empty state / error state 강화
- compare / trend / detail panel 설명력 강화

### P2

- 고급 분석
- saved views
- richer charts
- 운영 안정화 후속

---

## 1. SNS Automation

### 🎨 Product Intent

SNS Automation은 "콘텐츠 생성 도구"가 아니라 "콘텐츠 기획, 제작, 예약, 확산, 수익화까지 연결된 실행 콘솔"처럼 보여야 한다.

### 👤 Core User Questions

- 오늘 어떤 콘텐츠를 만들어야 하나?
- 어떤 형식이 성과가 좋았나?
- 링크 클릭과 수익화는 잘 이어지고 있나?
- 경쟁 계정과 비교해 무엇을 바꿔야 하나?

### 📄 Target Screens

- [create.html](/d:/Project/web/sns-auto/create.html)
- [link-in-bio.html](/d:/Project/web/sns-auto/link-in-bio.html)
- [monetize.html](/d:/Project/web/sns-auto/monetize.html)
- [viral.html](/d:/Project/web/sns-auto/viral.html)
- [competitor.html](/d:/Project/web/sns-auto/competitor.html)

### Ticket SNS-01. Create Screen Completion

목표:
사용자가 `직접 작성`, `AI 생성`, `자동화 생성`의 차이를 즉시 이해하고 콘텐츠를 바로 만들 수 있어야 한다.

기능:

- 생성 모드 3종을 카드형으로 분리
- 템플릿 선택
- 미리보기 패널
- 저장 / 예약 / 임시저장
- 최근 생성 기록

화면 UX:

- Hero에 `오늘의 추천 콘텐츠` 카드
- 생성 모드 카드에 `추천 상황` 문구 표시
- 빈 상태에 예시 게시물 3개 제공
- 결과 패널에 예상 채널별 활용안 표시

이미지/이모지:

- `🪄` AI 생성
- `✍️` 직접 작성
- `⚙️` 자동화 생성
- 추천 비주얼: 카드형 콘텐츠 목업

완료 기준:

- 사용자가 1회 클릭 흐름으로 생성 모드 선택 가능
- 생성 결과가 미리보기와 최근 기록에 반영됨
- 저장/예약 성공 및 실패 메시지가 친절하게 표시됨

### Ticket SNS-02. Link-in-Bio Screen Completion

목표:
사용자가 링크 인 바이오 페이지를 편집하고 성과를 이해할 수 있어야 한다.

기능:

- 링크 CRUD
- 테마 선택
- 클릭 수/인기 링크 요약
- 모바일 미리보기
- 발행 상태 표시

화면 UX:

- 좌측 편집, 우측 미리보기 구조
- 상단에 `이번 주 가장 많이 눌린 링크` 카드
- 링크 추가 시 즉시 반영
- 빈 상태에 starter template 제공

이미지/이모지:

- `🔗` 링크
- `📱` 모바일 미리보기
- `📈` 클릭 추세

완료 기준:

- 링크 추가/수정/삭제가 화면에서 바로 반영됨
- 대표 클릭 지표가 summary 카드에 표시됨
- 모바일 미리보기가 실제 사용자 시점으로 읽힘

### Ticket SNS-03. Monetize Screen Completion

목표:
사용자가 수익화 기회를 이해하고 다음 액션을 결정할 수 있어야 한다.

기능:

- 수익화 카드 목록
- 채널별 성과 요약
- 추천 액션
- ROI 요약
- 최근 성과 변화

화면 UX:

- `지금 시도할 수 있는 수익화 액션`을 상단에 고정
- 단순 매출 대신 `무엇을 하면 늘어나는지` 설명
- 경고 상태는 `개선 포인트`와 함께 표기

이미지/이모지:

- `💸` 수익화
- `🎯` 추천 액션
- `📊` 성과 요약

완료 기준:

- 사용자가 상단 카드만 보고도 우선순위를 이해함
- ROI와 권장 액션이 한 화면에서 연결됨

### Ticket SNS-04. Viral Screen Completion

목표:
사용자가 바이럴 가능성이 높은 아이디어를 빠르게 고르고 실행할 수 있어야 한다.

기능:

- 트렌드 콘텐츠 목록
- 바이럴 점수 또는 신호
- 추천 포맷
- 저장/복제 CTA

화면 UX:

- 카드 리스트에 `왜 뜨는지` 설명
- 태그, 형식, 속도감 있는 랭킹 제공
- 클릭 시 상세 인사이트 패널 노출

이미지/이모지:

- `🔥` 상승 중
- `🚀` 빠르게 확산
- `📣` 확산 포맷

완료 기준:

- 트렌드 카드마다 설명과 CTA가 존재
- 상세 패널에서 재활용 액션이 가능

### Ticket SNS-05. Competitor Screen Completion

목표:
사용자가 경쟁 계정 비교 결과를 읽고 실행 가능한 인사이트를 얻어야 한다.

기능:

- 경쟁 계정 등록
- 비교 카드
- 게시 빈도/반응/포맷 비교
- 추천 액션 요약

화면 UX:

- 표보다 카드 우선
- `당장 바꿀 수 있는 점` 섹션 제공
- 비교 결과를 지나치게 수치 중심으로만 표현하지 않음

이미지/이모지:

- `🧭` 비교 방향
- `👀` 관찰 포인트
- `⚔️` 경쟁 비교

완료 기준:

- 경쟁 계정 추가 후 비교 요약이 즉시 렌더링됨
- 화면 하단에 실행 가능한 액션 3개 이상 제안됨

---

## 2. Review Platform

### 🎨 Product Intent

Review Platform은 "리스트 화면"이 아니라 "캠페인 발견 -> 신청 -> 자동화 -> 성과 확인"으로 이어지는 작업 콘솔처럼 보여야 한다.

### 👤 Core User Questions

- 지금 신청할 만한 캠페인이 무엇인가?
- 내 신청 상태는 어디까지 왔나?
- 자동 신청을 돌려도 안전한가?

### 📄 Target Screens

- [aggregator.html](/d:/Project/web/review/aggregator.html)
- [applications.html](/d:/Project/web/review/applications.html)
- [auto-apply.html](/d:/Project/web/review/auto-apply.html)

### Ticket REV-01. Aggregator Screen Upgrade

목표:
사용자가 가치 있는 캠페인을 빠르게 찾고 신청 판단을 내릴 수 있어야 한다.

기능:

- 필터/정렬
- 추천 캠페인
- 자격 상태 배지
- 마감 임박 표시
- 빠른 신청 CTA

화면 UX:

- 상단에 `오늘 추천 캠페인`
- 각 카드에 `추천 이유` 제공
- 자격 미달은 차단보다 가이드형 표시

이미지/이모지:

- `⭐` 추천
- `⏰` 마감 임박
- `📝` 바로 신청

완료 기준:

- 상단 추천 구역과 리스트 구역의 역할이 분리됨
- 추천 이유와 빠른 신청 버튼이 카드 내에 함께 존재

### Ticket REV-02. Applications Screen Upgrade

목표:
사용자가 신청 후 상태를 쉽게 추적하고 병목을 이해할 수 있어야 한다.

기능:

- 신청 상태 타임라인
- 상태별 필터
- 계정/플랫폼별 분류
- 상세 패널

화면 UX:

- `검토 중`, `승인`, `콘텐츠 제출 필요` 같은 사람이 읽기 쉬운 상태명 사용
- 각 신청 행에 다음 액션 문구 제공
- 타임라인 또는 스텝 배지 추가

이미지/이모지:

- `📬` 신청 현황
- `✅` 승인
- `🕒` 대기 중

완료 기준:

- 상태 변경 흐름이 타임라인 또는 배지로 읽힘
- 사용자가 다음 액션을 화면에서 바로 이해함

### Ticket REV-03. Auto-Apply Screen Upgrade

목표:
사용자가 자동 신청 규칙을 안심하고 설정할 수 있어야 한다.

기능:

- 규칙 생성/편집
- 제외 조건
- 위험 경고
- 예상 적용 결과
- 최근 자동 신청 로그

화면 UX:

- 규칙 편집 패널과 결과 미리보기 분리
- 위험 요소는 별도 색상/설명 박스
- 저장 전 `예상 영향` 카드 제공

이미지/이모지:

- `🤖` 자동화
- `🛡️` 안전 장치
- `📋` 규칙 미리보기

완료 기준:

- 사용자가 규칙 생성부터 저장까지 한 화면에서 완료
- 예상 결과와 위험 조건이 저장 전 노출됨

---

## 3. Growth Automation

### 🎨 Product Intent

Growth Automation은 단순 운영 도구가 아니라 "상황 판단 -> 액션 -> 증거 확인"이 자연스럽게 이어지는 운영 경험이어야 한다.

### 📄 Target Screens

- [index.html](/d:/Project/web/growth-automation/index.html)
- [contacts.html](/d:/Project/web/growth-automation/contacts.html)
- [journeys.html](/d:/Project/web/growth-automation/journeys.html)
- [ops.html](/d:/Project/web/growth-automation/ops.html)
- [app.js](/d:/Project/web/growth-automation/app.js)

### Ticket GRO-01. Hub Interpretation Upgrade

목표:
숫자 중심 화면을 판단 중심 화면으로 바꾼다.

기능/UX:

- 오늘의 할 일 패널
- 요약 카드에 변화 설명
- recommendation card 문구 개선
- evidence table 상단 컨텍스트 설명

이미지/이모지:

- `🧭` 오늘의 방향
- `📈` 변화 추세
- `⚡` 즉시 액션

완료 기준:

- 첫 화면 5초 안에 우선 행동이 보임
- 카드 수치마다 해석 문장이 붙음

### Ticket GRO-02. Contacts Friendly Console

목표:
운영자 화면을 보다 고객 중심 언어로 바꾼다.

기능/UX:

- segment 설명 문구 보강
- 리드 생성 성공/실패 피드백 개선
- 선택된 고객 detail panel에 `다음 액션` 영역 추가
- table empty state 일러스트 추가

완료 기준:

- 고객 상태가 기술 용어보다 행동 언어로 보임
- 신규 리드 생성 흐름이 더 짧고 명확함

### Ticket GRO-03. Journeys Narrative Upgrade

목표:
단계 이동이 숫자 나열이 아니라 사용자 여정으로 읽히게 한다.

기능/UX:

- stage card에 병목 설명
- progression action에 helper text
- recent event evidence를 서사형 라벨로 보강

완료 기준:

- 사용자가 어느 단계에서 막히는지 직관적으로 이해함

### Ticket GRO-04. Ops Recovery Clarity

목표:
복구 화면을 더 빠르고 덜 위협적으로 만든다.

기능/UX:

- 실패 이벤트와 복구 대기 항목의 구분 강화
- replay 설명 문구 개선
- 성공적인 복구 후 안심 메시지 제공

완료 기준:

- 실패와 복구 대상의 차이가 첫 시선에서 구분됨
- replay 후 상태 변화가 명확히 보임

---

## 4. CooCook

### 🎨 Product Intent

CooCook은 기능 모음이 아니라 "탐색 -> 선택 -> 장보기 -> 예약/공유"로 이어지는 생활형 푸드 경험이어야 한다.

### 📄 Candidate Screens

- [index.html](/d:/Project/web/coocook/index.html)
- [recipes.html](/d:/Project/web/coocook/recipes.html)
- [shopping-list.html](/d:/Project/web/coocook/shopping-list.html)
- [feed.html](/d:/Project/web/coocook/feed.html)
- [my-bookings.html](/d:/Project/web/coocook/my-bookings.html)

### Ticket COO-01. Recipe Discovery Completion

목표:
사용자가 빠르게 먹고 싶은 것 또는 만들 수 있는 것을 찾게 한다.

기능:

- 검색
- 필터
- 추천 레시피
- 상세 정보
- 저장 CTA

화면 UX:

- `지금 바로 만들 수 있어요` 카드
- 재료 기반 추천 진입점
- 조리시간/난이도/후기 시각 강화

이미지/이모지:

- `🍳` 레시피
- `🥕` 재료
- `⭐` 추천

완료 기준:

- 사용자가 검색 또는 추천 중 하나로 바로 진입 가능
- 레시피 카드의 판단 정보가 충분히 보임

### Ticket COO-02. Shopping List Flow Completion

목표:
레시피에서 장보기까지 이어지는 흐름을 완성한다.

기능:

- 재료 추가
- 체크리스트
- 레시피에서 자동 가져오기
- 공유/내보내기

화면 UX:

- 장보기 진행률 표시
- 필요한 재료와 보유 재료를 구분
- 빈 상태에 추천 레시피 연결

이미지/이모지:

- `🛒` 장보기
- `✅` 체크 완료
- `📦` 준비물

완료 기준:

- 레시피에서 쇼핑리스트 생성까지 이어짐
- 리스트 상태가 즉시 업데이트됨

---

## 5. Telegram Scheduler

### Ticket TEL-01. Chat ID Connection Completion

목표:
설정만 보면 연결 여부와 다음 행동을 이해할 수 있어야 한다.

기능:

- chat ID 연결
- 연결 상태 표시
- 테스트 발송
- 실패 원인 메시지

화면 UX:

- `연결됨 / 미연결 / 확인 필요` 배지
- 테스트 발송 버튼
- 실패 시 해결 안내

이미지/이모지:

- `📨` 테스트 발송
- `🔔` 알림 연결
- `⚠️` 설정 필요

완료 기준:

- 사용자가 설정 후 연결 상태를 즉시 확인 가능
- 테스트 발송 성공/실패가 명확히 보임

---

## 🧪 Shared Acceptance Checklist

모든 티켓은 아래 기준을 공통으로 만족해야 한다.

- Hero에 화면 목적이 한 줄로 보인다
- Primary CTA가 첫 화면에서 보인다
- Empty state가 친절하다
- Error state가 사용자 언어다
- Success feedback이 즉시 노출된다
- 모바일에서도 CTA가 유지된다
- 테이블은 증거, 카드는 방향 역할을 한다

---

## 📌 Recommended Implementation Sequence

1. SNS-01, SNS-02
2. REV-01, REV-02
3. GRO-01, GRO-02
4. TEL-01
5. COO-01, COO-02
6. SNS-03, SNS-04, SNS-05
7. REV-03
8. GRO-03, GRO-04

---

## ✨ Final Guidance

지금 단계에서 중요한 것은 많은 페이지를 건드리는 것이 아니라, 대표 화면 몇 개를 확실히 제품답게 바꾸는 것이다.

우선 성공 기준은 아래와 같다.

- 사용자가 각 제품에서 "지금 뭘 해야 하는지" 바로 안다
- 한 화면 안에서 핵심 작업 1개를 끝낼 수 있다
- 결과가 수치와 설명으로 바로 확인된다

이 기준을 통과한 뒤에 나머지 운영 안정화와 배포 통제를 이어가는 것이 맞다.
