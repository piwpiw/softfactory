# Bohemian Marketing Parallel Implementation Plan

This plan is migrated to the existing orchestrator model.

## Execution Mode
- Queue source: `orchestrator/task-queue.json`
- Runner: `python run_all_agents.py`
- Policy: existing `orchestrator/agent-registry.md` authority boundaries

## 10 Agents x 10 Tasks
- Agent A (coordination): BM-A01 ... BM-A10
- Agent B (frontend): BM-B01 ... BM-B10
- Agent C (backend): BM-C01 ... BM-C10
- Agent D (architecture): BM-D01 ... BM-D10
- Agent E (security): BM-E01 ... BM-E10
- Agent F (product): BM-F01 ... BM-F10
- Agent G (devops): BM-G01 ... BM-G10
- Agent H (frontend advanced): BM-H01 ... BM-H10
- Agent I (qa): BM-I01 ... BM-I10
- Agent J (ops communication): BM-J01 ... BM-J10

---

## Structured Execution Metadata

<!-- doc-metadata
id: bohemian-marketing-parallel-plan
type: execution-plan
owner: bohemian-marketing-ops
updated: 2026-03-03
status: active
indexing-tags:
  - bohemian-marketing
  - autopilot
  - parallel
  - api
  - deployment-readiness
-->

- Execution target: `web/bohemian-marketing/index.html` advanced orchestration rollout
- Primary evidence files: `web/bohemian-marketing/index.html`, `web/platform/api.js`
- Update contract: any task touching behavior must update `README.md` and this plan file in same PR

## Status Tracking
- Source of truth: `orchestrator/task-queue.json`
- Runtime evidence: `agent_workspaces/*/run_*.json`
- Governance: `orchestrator/README.md`, `orchestrator/agent-registry.md`

### Work Stream Index

| Stream | 목적 | 입력산출물 | 검색 키워드 |
|---|---|---|---|
| BM-A01~BM-A10 | 조정/우선순위/리스크 | `task-queue`, 런북 링크 | coordination, priority, recovery |
| BM-B01~BM-B10 | UI/UX | `index.html`, 스타일/컴포넌트 | ui, dashboard, cards |
| BM-C01~BM-C10 | API 연동 | `platform/api.js`, `/api/sns/*` | api, sns, publish |
| BM-D01~BM-D10 | 아키텍처 | 실행 플로우 다이어그램, 상태전이 | state machine, autopilot |
| BM-E01~BM-E10 | 보안/접근성 | 입력 검증, 로컬스토리지 정책 | security, xss, csp |
| BM-F01~BM-F10 | 제품 완성도 | 문안/톤/템플릿 정합성 | product, draft quality |
| BM-G01~BM-G10 | 운영/배포 | CI/CD, Render, Vercel | deploy, render, vercel |
| BM-H01~BM-H10 | 고도화 실험 | 성능/애니메이션/반응형 | enhancement, polish |
| BM-I01~BM-I10 | 품질 및 테스트 | 기능 점검 체크리스트 | test, qa, manual checks |
| BM-J01~BM-J10 | 문서/커뮤니케이션 | README, 운영 가이드 | docs, changelog |

### Acceptance Matrix

| 조건 | 검증 항목 | 확인 방식 |
|---|---|---|
| 기본 운영 | 페이지가 200 응답 및 핵심 버튼 활성 | HTTP + 화면 조작 테스트 |
| API/데모 전환 | 토큰 미보유 시 데모 모드 전환 | 콘솔 로그 및 UI 표시값 |
| 동시 실행 제어 | 중복 버튼 연타 방지 | actionBusy 토글 상태 |
| 자동 발행 루프 | 생성→검토→발행 흐름 완료 | run history 및 로그 출력 |
| 장애 대응 | API 실패 시 오류 메시지/복구 안내 | 수동 시나리오 재현 |

### 7일 후 리뷰 기준

- 실행 속도: 로컬 smoke test 소요시간 30초 내
- 실패율: 핵심 액션(run/publish/refresh) 1% 미만
- 문서 동기화: 핵심 문서 1건 변경 시 24시간 내 README 반영

## Maintenance Integration Addendum

- 문서 메인 진입: README와 본 문서는 독립 운영이 아닌 상호 참조 구조
- 문서 표준: `docs/documentation-maintenance-template.md`
- 중앙 인덱스: `docs/doc-index.json`
- 점검 루틴: `pwsh scripts/check-doc-metadata.ps1`

### 현재 적용 상태

- 고도화 항목이 변경될 때마다 이 문서와 README에 동기 업데이트
- 변경 증적은 런북-계획-실행의 3중 구조로 관리
