# 야간 화면 작업 큐
<!-- doc-metadata
id: overnight-screen-work-queue
type: status
owner: ops-engineering
status: active
updated: 2026-03-20
keywords: overnight, ui, queue, audit
scope: frontend, operations
-->

## 기준

- 기본 흐름은 `화면 감사 -> 수정 -> preview 배포 -> 브라우저 검증`이다.
- 전체 테스트 확장보다 실제 페이지 체감과 콘솔 오류 감소를 우선한다.
- 작업은 `공개 화면`, `전환 화면`, `반복 사용 화면` 순서로 좁혀서 진행한다.

## 현재 완료 기준

- 운영 콘솔 기본 진입 정상
- CooCook 공개 진입 정상
- SNS 자동화 생성 화면 정상
- AI 자동화 대시보드 정상
- 인스타 카드뉴스 화면 정상
- 브라우저 감사 통과
- 링크 점검 통과

## 즉시 다음 작업

1. CooCook 페이지의 공통 404 자산 2건을 정확히 확인
2. `coocook/explore`, `coocook/recipes`, `coocook/feed`의 콘솔 경고를 0건까지 축소
3. SNS Auto 생성 흐름을 3단계 이하로 단순화
4. Instagram Cardnews 입력 화면을 더 짧은 흐름으로 재정리
5. AI Automation 대시보드의 카드 밀도를 줄여 가독성 확보

## 병렬 작업 후보

1. `/platform/dashboard.html` 운영 카드 정보 구조 정리
2. `/sns-auto/templates.html` 템플릿 탐색 UI 단순화
3. `/sns-auto/accounts.html` 계정 연결 상태 시각화 개선
4. `/instagram-cardnews/index.html` 계정별 주제 추천 카드 정리
5. `/coocook/shopping-list.html` 장보기 체크 흐름 단순화

## 반복 검증 루프

1. `python scripts/ui-screen-sprint-audit.py --base <preview-url> --headless true --timeout 20000`
2. `python scripts/check-deployed-web-links.py --base-url <preview-url>`
3. 통과 이후에만 production 승격 검토

## 최종 확인 포인트

- 브라우저 감사 리포트 최신본 확인
- preview 링크 체감 확인
- 다음 production 승격 후보만 좁혀서 관리
