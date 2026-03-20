# 5시간 자동 고도화 오토러너 실행 기록 (리뷰 작업리스트 우선)

- 시작 기준: 2026-03-04 (로컬 기준)
- 실행 스크립트: `scripts/agent_3h_loop.py` (5시간/300초/최대 12 worker로 실행)
- 출력 루트: `docs/plans/execution/2026-03-04/auto-5h/`
- 상태 파일: `status.json`, `status.md`
- 시간별 리포트: `hourly_report.md/json`
- 아침 브리프: `morning_check_brief.md/json`

## 실행 규칙
- 기간: `SOFTFACTORY_LOOP_HOURS` (기본 5)
- 간격: `SOFTFACTORY_LOOP_INTERVAL_SECONDS` (기본 300초)
- 동시 작업자: `SOFTFACTORY_LOOP_MAX_WORKERS` (기본: `max(CPU * 2, 12)`, 기본 값 미설정 시 자동)
- 모드: `SOFTFACTORY_LOOP_MODE` (`review` 기본, `work` 시 기존 구현/개발 워커 사용)
- 범위: P0~P4 전체, 부서별 최대 100개 작업

### 모드별 실행 커맨드 템플릿
- `review` (기본): `python scripts/department_review_list_worker.py ...`로 각 부서의 검토 작업리스트 산출
- `work` (기존): `python scripts/department_queue_worker.py ...`로 기존 작업 실행

## 백그라운드 실행
```powershell
$env:SOFTFACTORY_LOOP_HOURS='5'
$env:SOFTFACTORY_LOOP_INTERVAL_SECONDS='300'
$env:SOFTFACTORY_LOOP_MAX_WORKERS='12'
$env:SOFTFACTORY_LOOP_MODE='review'
Start-Process -FilePath python -ArgumentList 'scripts/agent_3h_loop.py' -WorkingDirectory 'D:\Project' -RedirectStandardOutput 'D:\Project\tmp_logs\agent_5h_loop_stdout.log' -RedirectStandardError 'D:\Project\tmp_logs\agent_5h_loop_stderr.log' -WindowStyle Hidden
```

## 상태 확인
- `Get-Content docs/plans/execution/$(Get-Date -Format yyyy-MM-dd)/auto-5h/status.md`
- `Get-Content docs/plans/execution/$(Get-Date -Format yyyy-MM-dd)/auto-5h/morning_check_brief.md` (아침 한줄 요약)
- `Get-Content docs/plans/execution/$(Get-Date -Format yyyy-MM-dd)/auto-5h/hourly_report.md` (매시간 집계 리포트)

## 중단 방법
```powershell
Get-Process python | Where-Object { $_.CommandLine -like '*scripts/agent_3h_loop.py*' } | Stop-Process
```
