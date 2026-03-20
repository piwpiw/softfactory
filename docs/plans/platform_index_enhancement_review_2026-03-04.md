# Platform 사용자 대시보드 고도화 검토서 (2026-03-04)

## 1. 체크 결과 (문서-코드 정합성)

- 대상 페이지: `web/platform/index.html`
- 확인 경로:
  - `web/platform/index.html`
  - `web/platform/api.js`
  - `backend/platform_routes.py`
  - `docs/plans/enterprise_upgrade_day_plan_2026-03-03.md`
  - `STATUS.md`
- 실행 상태(배포 런타임 9000 기준):
  - `GET /health` → `200`
  - `GET /web/platform/index.html` → `200`
  - `GET /web/platform/dashboard-enhanced.js` → `404`
  - `GET /api/platform/dashboard` → `401` (인증 필요)
- 핵심 결함:
  - `index.html`은 `dashboard-enhanced.js`를 `defer` 로드하도록 작성되어 있지만, 실제 파일이 존재하지 않음.
  - 페이지는 KPI/차트/서비스/알림/내보내기 동작을 의도하고 있으나 실질 로직 바인딩이 불완전.
  - `/api/platform/dashboard`는 인증이 필요하고 응답 스키마(`user`, `products`, `subscription_count`)가 페이지 KPI 필드 기대치와 정합성 검토가 필요.

## 2. 기존 페이지 고도화(필수) 방향

1. **대시보드 동작 복구**
   - `dashboard-enhanced.js` 신설 또는 대체 번들 적용.
   - 페이지 진입 시 `DOM` 준비, 조회 버튼, 새로고침, 내보내기, 모달 닫기 핸들러 일괄 바인딩.

2. **데이터 계약 정합화**
   - `index.html` KPI 카드가 요구하는 지표: 월매출/활성서비스/누적지출/평균ROI를 API 스키마와 1:1 매핑.
   - 현재 `/api/platform/dashboard` 또는 전용 집계 API를 기준으로 UI 계약 문서화.

3. **안정성 강화**
   - 로딩/빈 데이터/에러/오프라인 4가지 상태 UI 명시.
   - 실패 재시도, 마지막 동기화 시각, fallback 메시지 표준화.

4. **운영성 개선**
   - `index.html` 내비게이션 라벨/접근성/키보드 포커스 일관성 정리.
   - 이벤트 트래킹: `api_fail`, `api_timeout`, `api_fallback`, `refresh_error`.

## 3. 신규 기능 추가 제안(우선순위)

1. 기간 비교 내비게이션(7d/30d/90d/1y) 유지 + 전환율 라벨 표시.
2. 구독/요금제 상태 액션(재결제 유도, 결제 수단 관리, 상태 변경 안내).
3. 내보내기 확장: CSV, JSON, PDF(요약 뷰) 멀티 포맷 + 선택 기간 반영.
4. 위젯 커스터마이징: 즐겨찾기 위젯 고정/비활성 토글.
5. 감사/운영 탭: 최근 20건 이벤트 로그(요금 결제, 구독 변경, 알림, 상태 전환).

## 4. 개발 분류(문서 기반 우선순위)

- **T6 Frontend**
  - `dashboard-enhanced.js` 생성 및 바인딩
  - 로딩/오류/빈 상태 패턴 도입
  - 접근성 보완(모달 포커스, 버튼 라벨, aria 상태)

- **T5 Backend**
  - `/api/platform/dashboard` 응답 정합성 문서 확정
  - `index` 전용 축약뷰가 필요한 경우 전용 엔드포인트 신설 검토

- **T4/T8**
- KPI 정의/허용 오차/감사로그 보존 규칙 정리
- 민감 동작(내보내기, 결제 액션)에 대한 보안/권한 규칙 정리

- **T7**
  - 인증/비인증/오프라인/401/500 시나리오 E2E 검증 케이스

## 5. 2026-03-04 기준 즉시 실행 체크리스트 (D1)

1. `dashboard-enhanced.js` 복구(1st) → 완료 (`web/platform/dashboard-enhanced.js` 추가).
2. `index.html` 요소 바인딩 점검(새로고침/내보내기/기간버튼/모달).
3. 대시보드 API 계약 문서화 후 화면 필드 매핑 갱신.
4. 404 미존재 파일/401 차단 케이스의 사용자 메시지 확정.
2. `dashboard-enhanced.js`에서 KPI, 차트, 서비스그리드, 청구표, 알림, 내보내기, 새로고침, 조회기간 버튼을 한 번에 바인딩.
3. `/api/platform/dashboard` 응답 및 결제내역을 보조 소스로 사용해 KPI/차트 계산 폴백 적용.
4. 401/네트워크 오류/빈 데이터 상태에 대한 사용자 메시지 및 재시도 가능 경로 적용.
5. 검증 로그를 `docs`와 `STATUS.md`에 반영.

## 6) 2026-03-04 실행 완료 요약

- `web/platform/dashboard-enhanced.js` 추가 완료 (404 치명 오류 해소).
- `web/platform/index.html`는 동일 참조 유지.
- 핵심 렌더 루프(대시보드 데이터 fetch → KPI 렌더링 → 차트 렌더링 → 모듈별 섹션 갱신)를 구현.
- 내보내기(CSV/JSON/PDF) 및 모달 접근성(ESC/백드롭 닫기) 핸들링 추가.

## 6. 성공 기준

- 플랫폼 대시보드 접속 시 KPI 4개와 4개 차트 영역이 렌더링되어야 함.
- 차트/표/알림/내보내기 기능이 인증 여부에 따라 명확히 동작하고 오류 메시지가 일관되어야 함.
- 기능 갱신 내용이 문서와 동일하게 추적 가능해야 함.
