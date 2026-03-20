# 저장소 구조 관리 장표

<!-- doc-metadata
id: repo-structure-management-dashboard
type: management-dashboard
owner: ops-engineering
status: active
updated: 2026-03-10
keywords: repo structure, management dashboard, documentation, operations, layout
scope: repository-structure, management, operations
-->

이 문서는 저장소 구조를 관리 관점에서 빠르게 이해하기 위한 요약 장표입니다.
목표는 세 가지입니다.

- 어디를 먼저 봐야 하는지 바로 알기
- 어떤 경로가 정식 위치인지 헷갈리지 않기
- 팀·에이전트 문서를 과대평가하지 않기

## 현재 구조 상태

| 항목 | 현재 상태 | 의미 |
| --- | --- | --- |
| 루트 불필요 문서 | 0건 | 루트는 진입점 중심으로 정리됨 |
| 루트 임시/로그 파일 | 0건 | 실행 산출물이 루트에 쌓이지 않음 |
| deprecated 경로 | 0건 | 정식 경로가 하나로 정리됨 |
| 문서 단일 입구 | `docs/INDEX.md` | 문서는 여기서 시작 |
| 운영 상태 입구 | `STATUS.md` | 현재 상태는 여기서 확인 |

## 구조를 보는 기준

| 축 | 정식 위치 | 해석 |
| --- | --- | --- |
| Product | `backend/`, `web/`, `tests/`, `api/` | 제품 코드와 테스트 |
| Automation | `agents/`, `daemon/`, `orchestrator/`, `shared-intelligence/`, `n8n/` | 자동화 런타임과 운영 보조 |
| Operations | `scripts/`, `monitoring/`, `nginx/`, `infrastructure/`, `.github/` | 배포, 검증, 운영 제어 |
| Documentation | `docs/` | 사람이 보는 정식 문서 |
| Workspace | `.workspace/`와 생성물 디렉터리 | 로그, 임시 결과, 로컬 산출물 |

## 어디를 먼저 봐야 하나

| 목적 | 먼저 볼 문서 | 설명 |
| --- | --- | --- |
| 전체 시작점 | `README.md` | 실행과 루트 진입 안내 |
| 현재 상태 | `STATUS.md` | 지금 상태와 진행 현황 |
| 문서 탐색 | `docs/INDEX.md` | 문서의 정식 시작점 |
| 경로 규칙 | `docs/reference/repo-layout.md` | 어디에 무엇을 둬야 하는지 |
| 정식 경로 확인 | `docs/reference/active-paths.md` | canonical path 기준 |
| 구조 기준선 | `docs/status/repo-layout-baseline.md` | 구조 정리 결과 요약 |

## 문서 배치 원칙

| 문서 종류 | 정식 위치 | 원칙 |
| --- | --- | --- |
| 기준/정책 | `docs/reference/` | 오래 유지할 규칙 문서 |
| 실행 가이드 | `docs/runbooks/` | 바로 실행할 때 쓰는 문서 |
| 점검표 | `docs/checklists/` | 검증과 납품 체크 |
| 상태 요약 | `docs/status/` | 현재 상태와 관리 보고 |
| 과거 기록 | `docs/archive/` | 보존은 하되 현재 기준으로 쓰지 않음 |

## 팀·에이전트 문서는 어떻게 봐야 하나

팀·에이전트 문서는 대부분 "현재 정답"이 아니라 "배경 자료"입니다.
따라서 아래처럼 해석하는 것이 안전합니다.

| 구분 | 의미 | 관리 원칙 |
| --- | --- | --- |
| Active | 지금 상태나 운영 판단에 직접 쓰는 문서 | 아주 제한적으로만 유지 |
| Reference | 참고 가치가 있는 배경 문서 | 필요할 때만 조회 |
| Archive | 과거 산출물, 완료 보고, 실행 로그 | 현재 기준 문서로 사용하지 않음 |

현재 기준 해석:

- 실제로 `Active`로 볼 문서는 거의 `docs/status/TEAM_WORK_STATUS.md` 수준만 남습니다.
- 팀 스킬, handoff, 구현 요약 같은 문서는 `Reference`가 맞습니다.
- 완료 보고, 팀별 납품 요약, 병렬 실행 로그는 `Archive`로 봐야 합니다.
- 상세 분류표는 `docs/reference/team-agent-doc-classification.md`를 따릅니다.

## 책임 구분

| 영역 | 1차 책임 | 관리 포인트 |
| --- | --- | --- |
| 루트 구조와 경로 규칙 | ops-engineering | 루트 오염 방지, canonical path 유지 |
| 제품 코드 구조 | engineering | 기능 구조와 테스트 유지 |
| 자동화/운영 구조 | ops-engineering | 런타임 경로 안정성 유지 |
| 문서 품질 | ops-engineering | 시작 문서 중복 방지, 링크 무결성 유지 |
| archive 보존 | ops-engineering | 현재 문서와 과거 문서 분리 |

## 검증 기준

다음 상태가 유지되어야 구조가 안정적이라고 봅니다.

- 루트 불필요 문서 0건
- 루트 임시/로그 파일 0건
- missing link targets 0건
- deprecated paths 0건
- 새 문서는 루트가 아니라 `docs/` 하위 정식 카테고리에만 추가

## 관리자용 체크포인트

- 새 문서가 생기면 먼저 `docs/INDEX.md` 기준으로 위치가 맞는지 확인합니다.
- 새 팀 문서나 에이전트 문서를 만들기 전에 기존 기준 문서에 흡수할 수 있는지 먼저 봅니다.
- 실행 결과물은 `.workspace/`나 생성물 디렉터리로 보내고 루트에는 두지 않습니다.
- 루트 wrapper는 호환성 목적일 뿐이며, 실제 구현은 `scripts/`가 정식 위치입니다.

## 현재 검증 스냅샷

2026-03-10 기준 `python scripts/check-repo-layout.py` 결과:

- `root files present: 46`
- `disallowed root files present: 0`
- `legacy root documents present: 0`
- `temp root files present: 0`
- `missing link targets: 0`
- `deprecated paths present: 0`

## 다음 관리 액션

- 팀·에이전트 문서에서 가치가 약해진 `Reference` 항목은 주기적으로 `Archive`로 내립니다.
- 필요한 배경 내용은 새 문서를 늘리기보다 `docs/reference/`, `docs/runbooks/`, `docs/checklists/`로 흡수합니다.
- 구조 변경이 생기면 `docs/INDEX.md`, `docs/reference/active-paths.md`, 이 장표를 같이 갱신합니다.
