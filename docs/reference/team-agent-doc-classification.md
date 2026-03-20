# 팀·에이전트 문서 분류표

<!-- doc-metadata
id: team-agent-doc-classification
type: reference-classification
owner: ops-engineering
status: active
updated: 2026-03-10
keywords: team docs, agent docs, classification, archive, active, reference
scope: documentation, repository-structure, governance
-->

이 문서는 팀별·에이전트별 문서를 "지금 운영에 직접 쓰는가" 기준으로 다시 분류한 표입니다.
핵심 원칙은 간단합니다.

- 지금 바로 따라야 하는 문서만 `Active`로 둡니다.
- 설명 가치나 배경 가치가 남아 있으면 `Reference`로 둡니다.
- 과거 산출물, 완료 보고, 실행 로그는 `Archive`로 둡니다.

## 이 문서를 보는 방법

| 분류 | 의미 | 운영 판단 |
| --- | --- | --- |
| Active | 지금 상태 확인이나 운영 판단에 직접 쓰는 문서 | 최신성 유지 필요 |
| Reference | 지금의 정식 기준은 아니지만 참고 가치가 있는 문서 | 필요 시만 조회 |
| Archive | 과거 기록 보존용 문서 | 현재 업무 기준으로 사용하지 않음 |

## 핵심 판단

- 팀·에이전트 문서는 기본적으로 정식 운영 기준 문서가 아닙니다.
- 정식 기준 문서는 `README.md`, `STATUS.md`, `docs/INDEX.md`, `docs/reference/*`, `docs/runbooks/*`, `docs/checklists/*`가 우선입니다.
- 팀·에이전트 문서에 유용한 내용이 있으면 새 문서를 늘리기보다 정식 기준 문서로 흡수하는 것이 맞습니다.
- "누가 만들었는가"보다 "지금 무엇을 따라야 하는가"를 우선합니다.

## Active

| 파일 | 유지 이유 | 비고 |
| --- | --- | --- |
| `docs/status/TEAM_WORK_STATUS.md` | 현재 팀 진행 상태를 직접 보여주는 상태 문서 | `team_work_manager.py`가 생성/사용 |

## Reference

| 파일 | 유지 이유 | 현재 해석 |
| --- | --- | --- |
| `docs/TEAM_SKILLS.md` | 런북에서 아직 직접 참조하는 팀 스킬 참고 문서 | 운영 기준 문서 아님 |
| `docs/PERFORMANCE_AGENT_HANDOFF.md` | 체크리스트에서 참조하는 handoff 참고 문서 | 절차 보조 문서 |
| `docs/reference/legacy-root/TEAM_CHARTER_REFERENCE.md` | 과거 팀 운영 기준의 배경을 설명하는 참조 문서 | 역사적 기준 |
| `docs/TEAM_K_CI_CD_PIPELINE.md` | CI/CD 설계 배경과 세부 구성을 담은 기술 참고 문서 | 현행 정책 문서 아님 |
| `docs/TEAM_K_PERFORMANCE_MONITORING.md` | 성능/모니터링 관련 상세 배경 참고 문서 | 현행 운영 지침 아님 |
| `docs/TEAM_K_SECURITY_AUDIT_HARDENING.md` | 보안 강화 작업의 상세 배경 참고 문서 | 현행 보안 정책 문서 아님 |
| `docs/M-007_TEAM_E_IMPLEMENTATION_SUMMARY.md` | 특정 구현 배경과 맥락을 남기는 참고 문서 | 구현 히스토리 |
| `docs/archive/TEAM_STRUCTURE.md` | 현재 기준 문서는 아니지만 팀 구조 히스토리 확인용 | archive 안의 reference 성격 |

## Archive

| 파일 | 분류 이유 |
| --- | --- |
| `docs/status/TEAM_VALIDATION_SUMMARY.json` | 현재 라이브 운영 기준으로 직접 소비되는 흔적이 약함. 상태 데이터이지만 참고/보존 성격이 더 강함 |
| `docs/AGENT_SKILLS.md` | 현재 active 흐름보다 과거 체계 설명에 가까움 |
| `docs/TEAM_K_COMPLETION_REPORT.md` | 완료 보고서 성격이 강하고 현재 운영 기준으로 쓰이지 않음 |
| `docs/archive/root-legacy/8TEAM_VALIDATION_FINAL_REPORT.md` | 과거 병렬 검증 결과 |
| `docs/archive/root-legacy/TEAM_D_GOVERNANCE_CHECKPOINTS.md` | 과거 팀 산출물 |
| `docs/archive/root-legacy/TEAM_E_COMPLETION.md` | 과거 완료 보고 |
| `docs/archive/root-legacy/TEAM_E_IMPLEMENTATION_SUMMARY.md` | 과거 구현 요약 |
| `docs/archive/root-legacy/TEAM_E_REVIEW_SERVICE_COMPLETION.md` | 과거 완료 보고 |
| `docs/archive/root-legacy/TEAM_G_FINAL_DELIVERY.txt` | 과거 납품 기록 |
| `docs/archive/root-legacy/TEAM_H_TASK_21_COMPLETION.md` | 과거 작업 완료 기록 |
| `docs/archive/root-legacy/TEAM_I_FINAL_DELIVERY.md` | 과거 납품 기록 |
| `docs/archive/root-legacy/TEAM_I_INTEGRATION_TESTS_SUMMARY.md` | 과거 통합 테스트 요약 |
| `docs/archive/root-legacy/TEAM_I_WORK_COMPLETE.md` | 과거 작업 완료 기록 |
| `docs/archive/root-legacy/TEAM_K_DELIVERY_SUMMARY.md` | 과거 납품 요약 |
| `docs/plans/execution/2026-03-03/agent_3h_cycle.ps1` | 실행 로그성 계획 산출물 |
| `docs/plans/execution/2026-03-03/agent_3h_loop.log` | 실행 로그 |
| `docs/plans/execution/2026-03-04/auto-5h/agent_5h_loop.log` | 실행 로그 |

## 실무 해석 규칙

- 새 팀 문서나 에이전트 문서를 기준 문서처럼 늘리지 않습니다.
- 실제 운영 기준이 필요하면 `docs/reference/`, `docs/runbooks/`, `docs/checklists/`, `docs/status/`로 흡수합니다.
- `Reference` 문서는 유지하되 우선순위는 낮게 둡니다.
- `Archive` 문서는 링크가 남아 있어도 현재 업무 절차의 출발점으로 쓰지 않습니다.

## 다음 정리 후보

- `Reference` 문서 중 실제 조회 흔적이 더 약해지면 다음 배치에서 `Archive`로 내립니다.
- `TEAM_K_*` 계열은 내용이 정책 문서로 승격되지 않는 한 장기적으로는 archive 후보입니다.
- `TEAM_SKILLS.md`와 `PERFORMANCE_AGENT_HANDOFF.md`도 정식 기준 문서로 흡수되면 archive 후보로 전환할 수 있습니다.
