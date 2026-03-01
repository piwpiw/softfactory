# SoftFactory Deployment Guide

Last updated: 2026-03-01  
Purpose: 코드 변경 반영 속도를 높이기 위해 배포·로컬 검증·문서 정합성을 하나로 맞춘 실무 가이드

## 0) 현재 실행 기준 (Current Deployment Truth)

- 운영 배포: `.github/workflows/deploy.yml`
- 실행 브랜치: `main`
- 실행 조건: `workflow_dispatch`
- 로컬 즉시 검증: `docker-compose.dev.yml` + `run-dev.py` + `scripts/start-local.ps1`
- 최근 실행 이력: `run_id=22534340040` (실패)

## 1) 환경/명령 정리

### 1-1 운영 배포 1회 실행

```bash
# GitHub UI (권장)
# Actions > CI Build & Deploy (deploy.yml) > Run workflow > main
```

```bash
# GitHub API (자동화 스크립트에서 사용)
POST /repos/piwpiw/softfactory/actions/workflows/deploy.yml/dispatches
{
  "ref": "main",
  "inputs": {}
}
```

### 1-2 필수 시크릿 (deploy.yml)

```
REGISTRY
IMAGE_NAME
DOCKER_USERNAME
DOCKER_PASSWORD
SSH_HOST
SSH_USER
SSH_PRIVATE_KEY
DEPLOY_DIR
SSH_PORT
TELEGRAM_BOT_TOKEN
TELEGRAM_CHAT_ID
```

### 1-3 로컬 빠른 확인 루프 (개발 우선)

```bash
./scripts/start-local.ps1 -Rebuild
# 로그 확인
./scripts/start-local.ps1 -Rebuild -Tail
```

```bash
curl -f http://localhost:9000/health
curl -f http://localhost:9000/api/health
```

## 2) 단계별 실행 프로토콜 (실패 대비용)

### Phase A: 코드 변경 직후

1. `./scripts/start-local.ps1 -Rebuild`
2. `curl -f http://localhost:9000/health`
3. 핵심 API smoke test (필요 시 추가 엔드포인트 1~2개)
4. 문제가 없으면 커밋/푸시

### Phase B: 운영 배포

1. `main` 기준 브랜치 정합성 확인
2. GitHub Actions에서 `deploy.yml` 실행
3. 배포 run id 기록
4. Actions 로그에서 아래 우선순위 확인:
   - secrets 주입 실패
   - docker build/push 실패
   - SSH deploy 실패

### Phase C: 배포 후 점검

```bash
curl -f https://{prod-host}/health
curl -f https://{prod-host}/api/health
```

문제 발생 시:
1. run id 검색
2. 실패 스텝 로그만 추적
3. 동일 타입 실패 이력 있으면 비교(최근 1개 run 기준)

## 3) 핵심 문서 동기화 규칙

코드 수정 시 아래 3개 문서를 동시에 갱신합니다.

- `README_DEPLOY.md`: 실행 순서/명령 최신화
- `DEPLOYMENT_GUIDE.md`: Current Deployment Truth, 비상 대응 규칙
- `DEPLOYMENT_STATUS.md`: 최신 상태·실패 원인 기록

변경 기준:
- 배포 트리거가 바뀔 때
- 필수 시크릿이 바뀔 때
- 로컬 점검 포트/명령이 바뀔 때
- run failure가 반복 발생할 때

## 4) 바로 실행 가능한 상태 점검표

- [ ] 로컬에서 `curl -f http://localhost:9000/health` 통과
- [ ] `deploy.yml` 입력 Secret 누락 없음
- [ ] `main` 브랜치 푸시 상태 확인
- [ ] 배포 run id 확보
- [ ] 운영 health check 통과

## 5) 실패 모드 대응

- 로컬에서 실패:
  - `docker-compose.dev.yml` 컨테이너 상태 확인
  - 포트 충돌 확인
  - 코드 변경 없이 compose 재시작으로 원인 분리
- 운영 배포 실패:
  - run id 기반으로 실패 step만 확인
  - 기존 실패 유형 대비 템플릿 적용
  - 수정 후 같은 배포 루틴 재실행

## 6) 추천 다음 단계

1. 필요 시 `docs/standards/DEPLOYMENT_RUNBOOK_TEMPLATE.md`에 현재 기준 반영
2. 운영팀이 보는 `NOTION_MASTER_INDEX.md`에 본 가이드 업데이트 링크 등록
3. `DEPLOYMENT_STATUS.md`에 실패 run_id 및 조치 결과를 1회성으로 추가
