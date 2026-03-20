# 장기 후속 백로그
<!-- doc-metadata
id: long-running-followups
type: status-backlog
owner: ops-engineering
status: active
updated: 2026-03-20
keywords: backlog, long running, parallel work, follow-up
scope: operations, qa, deployment, frontend
-->

지금 당장 처리하면 흐름이 끊기거나 외부 의존성이 큰 작업만 따로 분리한 목록이다.

## 분리 기준

- 외부 인증 또는 실제 계정 연결이 필요한 작업
- 브라우저에서 많은 화면을 반복 검증해야 하는 작업
- 대규모 데이터 조합 또는 성능 측정이 필요한 작업
- 배포 또는 인프라 복구가 먼저 필요한 작업

## 백로그

| 항목 | 오래 걸리는 이유 | 권장 처리 방식 |
| --- | --- | --- |
| 보호 페이지 포함 전체 사용자 플로우 브라우저 검증 | 로그인 상태, 리다이렉트, 권한 경로까지 확인해야 함 | Playwright 기반 병렬 검증 배치 |
| SNS 실제 계정 연동 검증 | Instagram, Threads, TikTok, YouTube, Naver 등 외부 인증과 토큰 상태 확인 필요 | 계정별 인증 점검 후 검증 |
| SNS 다채널 발행 결과 수집 | 발행 성공 여부, 결과 URL, 실패 원인, 재시도까지 확인 필요 | 발행 후 검증과 결과 수집 작업 분리 |
| [sns-auto/create.html](/d:/Project/web/sns-auto/create.html) 실제 `n8n` webhook 연결 | 실제 workflow endpoint와 payload 계약이 확정되어야 함 | `n8n` 및 운영 문서와 병렬 정리 |
| [instagram-cardnews/index.html](/d:/Project/web/instagram-cardnews/index.html) 계정별 자동 리서치 고도화 | 주제 추천, 템플릿 추천, 데이터 수집 규칙 정리가 필요 | 카드뉴스 2차 고도화로 분리 |
| `CooCook` 대규모 조합 성능 검증 | 국가, 메뉴, 식재료 카테고리 조합에 대한 캐시 및 비용 측정 필요 | 벤치마크와 샘플 데이터 확대 |
| AI 자동화 서비스 간 계약 정리 | `ai-automation`, `sns-auto`, `instagram-cardnews` 사이 공통 계약과 모델 정리가 필요 | 서비스 통합 설계 작업 |
| Docker/컨테이너 기반 로컬 배포 복구 | 현재 Docker 데몬과 이미지 조회 이슈가 남아 있음 | 인프라 후속 작업 |
| 인증 포함 배포 후 스모크 테스트 자동화 | 인증 흐름까지 포함한 자동화 스크립트와 테스트 계정 관리 필요 | nightly 또는 수동 확인용 CI |
| 대규모 문서 및 서비스 화면 UX 리패스 | 적용 범위가 넓고 수동 검토 시간이 큼 | 화면군 단위 병렬 개선 작업 |

## 우선순위 제안

1. 인증 포함 브라우저 스모크 자동화
2. SNS 실제 계정 연동 및 발행 검증
3. 카드뉴스 리서치 2차 고도화
4. `CooCook` 대규모 조합 성능 벤치마크
5. Docker 및 컨테이너 로컬 배포 복구
