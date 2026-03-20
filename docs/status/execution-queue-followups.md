# 후속 실행 큐
<!-- doc-metadata
id: execution-queue-followups
type: status-execution-queue
owner: ops-engineering
status: active
updated: 2026-03-20
keywords: execution queue, ui first, follow-up, backlog
scope: frontend, qa, deployment, operations
-->

이 문서는 지금부터의 기본 작업 원칙을 정리한다.
목표는 테스트 과잉보다 실제 화면 검증과 사용자 체감 개선을 먼저 진행하는 것이다.

## 기본 원칙

- 기본 라인은 `화면 감사 -> 수정 -> 배포 -> 브라우저 검증` 순서다.
- `pytest -q`는 기본 안전망으로만 사용한다.
- `slow`, `e2e`, 대규모 검증은 별도 백로그로 관리한다.
- 모든 화면을 한 번에 고치기보다 사용자가 바로 체감하는 화면부터 순차적으로 개선한다.

## 즉시 실행

| 우선순위 | 항목 | 기준 | 기대 결과 |
| --- | --- | --- | --- |
| 1 | UI 화면 스프린트 감사 | `scripts/ui-screen-sprint-audit.py` 실행 | 공개/보호 페이지의 실제 화면 상태, 콘솔 오류, 스크린샷 증적 확보 |
| 2 | 서비스별 화면 개선 배치 | `sns-auto`, `instagram-cardnews`, `ai-automation`, `coocook` 우선 | 사용자가 바로 이해하는 UI/UX 개선 축적 |
| 3 | 화면 기반 기능 보강 | 빈 상태, 버튼 라벨, CTA, 우선순위 문구 보강 | 화면과 기능이 같이 좋아지는 작은 반복 |
| 4 | 링크 및 라우트 검증 | `scripts/check-deployed-web-links.py` | 배포 후 404, 잘못된 이동 경로 조기 차단 |

## 병렬 가능 작업

| 우선순위 | 항목 | 병렬 처리 이유 | 기대 결과 |
| --- | --- | --- | --- |
| 1 | 서비스별 문안 및 카피 개선 | 화면 구현과 독립적으로 진행 가능 | 페이지 이해도 향상 |
| 2 | 공통 컴포넌트 스켈레톤 및 테마 보강 | 기능 흐름과 충돌이 적음 | 시각 일관성 개선 |
| 3 | 페이지별 미세 UX 개선 | 로딩, 빈 상태, 실패 메시지 보강 | 사용자 체감 향상 |
| 4 | 배포 smoke 검증 | 수정 배치와 병렬 실행 가능 | 배포 리스크 축소 |

## 후순위 백로그

| 우선순위 | 항목 | 후순위인 이유 |
| --- | --- | --- |
| 1 | 전체 `pytest -m slow` 실행 | 현재 화면 개선 속도를 직접 올리지는 않음 |
| 2 | 대규모 통합 테스트 환경 복구 | 사용자 화면보다 비용이 큼 |
| 3 | Docker 전체 복구 | 중요하지만 현재 UI 개선 사이클과 직접 연결되지는 않음 |
| 4 | 외부 계정 연동 검증 | 계정과 권한 확인이 선행되어야 함 |

## 실행 도구

- 빠른 화면 감사: [scripts/ui-screen-sprint-audit.py](../../scripts/ui-screen-sprint-audit.py)
- PowerShell 래퍼: [scripts/run-ui-screen-sprint-audit.ps1](../../scripts/run-ui-screen-sprint-audit.ps1)
- 링크 점검: [scripts/check-deployed-web-links.py](../../scripts/check-deployed-web-links.py)
- 보호 페이지 회귀: [scripts/auth-browser-regression.py](../../scripts/auth-browser-regression.py)

## 권장 반복 사이클

1. `python scripts/ui-screen-sprint-audit.py --base https://softfactory-platform.vercel.app`
2. 스크린샷과 콘솔 오류 기준으로 1~3개 서비스 화면만 묶어서 수정
3. 배포 후 링크 점검 재실행
4. 필요한 경우에만 좁은 범위 테스트 추가

## 연결 문서

- 장기 백로그: [long-running-followups.md](long-running-followups.md)
- 관리 대시보드: [repo-structure-management-dashboard.md](repo-structure-management-dashboard.md)
- 현재 상태: [TEAM_WORK_STATUS.md](TEAM_WORK_STATUS.md)
