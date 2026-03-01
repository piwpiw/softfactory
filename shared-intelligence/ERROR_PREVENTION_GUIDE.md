# 📘 🛡️ Error Prevention & Root Cause Analysis Guide

> **Purpose**: **Version:** 2026-02-26
> **Status**: 🟢 ACTIVE (관리 중)
> **Impact**: [Engineering / Operations]

---

## ⚡ Executive Summary (핵심 요약)
- **주요 내용**: 본 문서는 🛡️ Error Prevention & Root Cause Analysis Guide 관련 핵심 명세 및 관리 포인트를 포함합니다.
- **상태**: 현재 최신화 완료 및 검토 됨.
- **연관 문서**: [Master Index](./NOTION_MASTER_INDEX.md)

---

**Version:** 2026-02-26
**Purpose:** 절대 반복되지 않도록 하는 근본 원인 차단 체계
**Status:** ACTIVE — 모든 개발자가 반드시 준수

---

## 🔴 발견된 주요 오류 클래스

### ERROR-001: API Blueprint 라우트 미등록
**발견:** 2026-02-26
**증상:** `/api/sns/*`, `/api/review/*` → 404
**근본원인:** Flask blueprint에 `@bp.route()` 데코레이터가 없거나 정의되지 않음

**방지 규칙:**
```
✓ RULE-001: 모든 Blueprint 라우트는 반드시 @blueprint.route() 데코레이터 필요
  위치: backend/services/*.py
  검증: grep -c "@sns_bp.route\|@review_bp.route\|@coocook_bp.route" backend/services/*.py
  최소: SNS(19), Review(26), CooCook(8) 이상

✗ 위반 사례:
  ❌ def get_campaigns(): ...  # 데코레이터 없음
  ❌ # @sns_bp.route('/campaigns')  # 주석 처리됨

✓ 올바른 사례:
  ✅ @sns_bp.route('/campaigns', methods=['GET'])
  ✅ def get_campaigns(): return jsonify(...)
```

**테스트:**
```bash
# 모든 blueprint 라우트 개수 검증 (최소값 충족 확인)
@pytest.mark.critical
def test_blueprint_route_registration():
    app = create_app()
    sns_routes = [r for r in app.url_map.iter_rules() if '/api/sns' in str(r)]
    assert len(sns_routes) >= 19, f"Expected 19+ SNS routes, got {len(sns_routes)}"

    review_routes = [r for r in app.url_map.iter_rules() if '/api/review' in str(r)]
    assert len(review_routes) >= 26, f"Expected 26+ Review routes, got {len(review_routes)}"
```

---

### ERROR-002: Blueprint 임포트 실패로 인한 라우트 미등록
**발견:** 2026-02-26
**증상:** 코드에 라우트가 있지만 실제로 등록 안 됨
**근본원인:** `backend/app.py`에서 blueprint 임포트 중 예외 발생 → 조용히 실패

**방지 규칙:**
```
✓ RULE-002: app.py의 모든 blueprint 임포트는 반드시 검증되어야 함
  위치: backend/app.py의 import 섹션

✓ 검증 체크리스트:
  1. 모든 import가 존재하고 올바른 경로인가?
  2. 순환 참조(circular import)는 없는가?
  3. import 시 에러가 발생하는가?
  4. 모든 blueprint 이름이 올바른가? (auth_bp vs authBp)

✗ 위반 사례:
  ❌ from .services import sns_auto  # sns_bp를 임포트하지 않음
  ❌ from .services.sns import sns_bp  # 잘못된 경로
  ❌ app.register_blueprint(sns_auto_bp)  # 틀린 변수명

✓ 올바른 사례:
  ✅ from .services.sns_auto import sns_bp  # 올바른 경로
  ✅ app.register_blueprint(sns_bp)  # 올바른 변수명
```

**테스트:**
```bash
# 모든 blueprint 임포트 검증
@pytest.mark.critical
def test_all_blueprints_imported():
    from backend.app import create_app
    app = create_app()

    expected_blueprints = [
        'auth', 'payment', 'platform',
        'coocook', 'sns', 'review',
        'ai_automation', 'webapp_builder',
        'dashboard', 'analytics', 'performance', 'settings'
    ]

    registered = [bp.name for bp in app.blueprints.values()]
    for expected in expected_blueprints:
        assert expected in registered, f"Blueprint '{expected}' not registered"
```

---

### ERROR-003: API 엔드포인트 응답 테스트 부재
**발견:** 2026-02-26
**증상:** 단위 테스트 통과 → 실제 API는 404
**근본원인:** E2E 테스트 없음, API 엔드포인트 실제 동작 검증 안 함

**방지 규칙:**
```
✓ RULE-003: 모든 새 API 엔드포인트는 반드시 E2E 테스트 필요
  파일: tests/integration/test_endpoints_live.py

  필수 테스트:
  - GET/POST/PUT/DELETE 메서드 각각 테스트
  - 200, 400, 401, 404, 500 상태 코드 검증
  - 응답 JSON 스키마 검증
  - 실제 데이터베이스와의 상호작용 검증

✗ 위반 사례:
  ❌ 단위 테스트만 있음: test_oauth_social_login.py (라우트 테스트 없음)
  ❌ Mock 데이터로만 테스트
  ❌ 라이브 API 엔드포인트 테스트 없음

✓ 올바른 사례:
  ✅ test_oauth_endpoint_live():  # 실제 라우트 호출
       response = client.get('/api/auth/oauth/google/url')
       assert response.status_code == 200
       assert 'auth_url' in response.json
```

**테스트:**
```bash
# 모든 API 엔드포인트 실제 동작 검증
@pytest.mark.critical
def test_all_api_endpoints_live():
    client = app.test_client()

    endpoints = [
        ('GET', '/api/auth/me', 401),  # Demo token invalid
        ('GET', '/api/sns/campaigns', 200),  # Should work
        ('GET', '/api/review/aggregated', 200),
        ('POST', '/api/review/scrape/now', 200),
    ]

    for method, path, expected_status in endpoints:
        if method == 'GET':
            response = client.get(path, headers={'Authorization': 'Bearer demo_token'})
        else:
            response = client.post(path, headers={'Authorization': 'Bearer demo_token'})

        assert response.status_code == expected_status, \
            f"Expected {expected_status} for {method} {path}, got {response.status_code}"
```

---

## 📋 체크리스트: 새 기능 배포 전

**모든 새 API 추가 시 반드시 실행:**

```markdown
## 새 API 엔드포인트 배포 체크리스트

### 1. Blueprint 정의
- [ ] blueprint.py 파일에 `@blueprint.route()` 데코레이터 있는가?
- [ ] url_prefix 올바른가? (예: '/api/sns')
- [ ] Blueprint 객체명 올바른가? (예: sns_bp)

### 2. Blueprint 등록
- [ ] backend/app.py에 정확한 import 있는가?
- [ ] `app.register_blueprint(blueprint)` 호출 있는가?
- [ ] 변수명이 정확한가?

### 3. 라우트 검증
- [ ] HTTP 메서드 올바른가? (GET/POST/PUT/DELETE)
- [ ] URL 경로 올바른가?
- [ ] @require_auth 데코레이터 필요한가?
- [ ] 요청/응답 JSON 스키마 문서화?

### 4. 테스트
- [ ] 단위 테스트 작성? (>= 3개 케이스)
- [ ] E2E 테스트 작성? (실제 라우트 호출)
- [ ] 모든 테스트 통과?
- [ ] curl로 수동 테스트?

### 5. 배포 전 검증
- [ ] curl로 엔드포인트 직접 호출 → 200 OK?
- [ ] 브라우저에서 페이지 로드 → API 호출 성공?
- [ ] 로그에 에러 없는가?
- [ ] 데이터베이스 상태 정상?

### 6. 문서화
- [ ] API 엔드포인트 문서화 (docs/API_REFERENCE.md)?
- [ ] 예제 cURL 명령 포함?
- [ ] 응답 스키마 명시?

### 배포 가능 (모두 ✓)
```

---

## 🚨 긴급 Validation Script

모든 배포 전 실행할 스크립트:

```bash
#!/bin/bash
# validate_before_deploy.sh

echo "🔍 API 엔드포인트 검증..."

# 1. Blueprint 라우트 개수 검증
echo "Step 1: Blueprint 라우트 개수"
python3 << 'EOF'
import re
from pathlib import Path

services = {
    'sns_auto.py': 19,
    'review.py': 26,
    'coocook.py': 8,
}

for service, min_routes in services.items():
    file = Path(f"backend/services/{service}")
    if file.exists():
        content = file.read_text()
        routes = len(re.findall(r'@\w+_bp\.route\(', content))
        status = "✅" if routes >= min_routes else "❌"
        print(f"{status} {service}: {routes} routes (min: {min_routes})")
    else:
        print(f"❌ {service}: NOT FOUND")
EOF

# 2. Blueprint 등록 검증
echo ""
echo "Step 2: Blueprint 등록 (app.py)"
grep -c "register_blueprint" backend/app.py && echo "✅ $(grep -c 'register_blueprint' backend/app.py) blueprints registered"

# 3. API 엔드포인트 라이브 테스트
echo ""
echo "Step 3: API 엔드포인트 라이브 테스트"
ENDPOINTS=(
    "http://localhost:8000/api/auth/me"
    "http://localhost:8000/api/sns/campaigns"
    "http://localhost:8000/api/review/aggregated"
)

for endpoint in "${ENDPOINTS[@]}"; do
    status=$(curl -s -w "%{http_code}" -o /dev/null -H "Authorization: Bearer demo_token" "$endpoint")
    [ "$status" != "404" ] && echo "✅ $endpoint: $status" || echo "❌ $endpoint: $status (404 - NOT FOUND)"
done

# 4. 테스트 실행
echo ""
echo "Step 4: 테스트 실행"
pytest tests/ -v --tb=short -k "critical" 2>&1 | tail -20

echo ""
echo "✅ 모든 검증 완료. 배포 준비 상태."
```

---

## 📊 회귀 테스트 전략

**주간 자동화 검증:**

```yaml
# .github/workflows/regression-tests.yml
name: Weekly Regression Tests

on:
  schedule:
    - cron: '0 9 * * MON'  # 매주 월요일 9시

jobs:
  regression:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Check API Endpoints
        run: |
          pytest tests/integration/test_endpoints_live.py -v
      - name: Check Blueprint Registration
        run: |
          pytest tests/integration/test_blueprint_registration.py -v
      - name: Health Check
        run: |
          curl -f http://localhost:8000/health || exit 1
```

---

## 📝 개발자 서명

**이 문서를 읽고 준수하겠습니다:**

| 팀 | 개발자 | 서명 | 날짜 |
|----|--------|------|------|
| A | OAuth Team | ___ | ___ |
| B | Frontend Team | ___ | ___ |
| C | Monetization | ___ | ___ |
| D | Scrapers | ___ | ___ |
| E | API | ___ | ___ |
| F | Review UI | ___ | ___ |
| G | SNS API | ___ | ___ |
| H | API Client | ___ | ___ |

---

## 🔗 관련 문서

- `ACTUAL_STATUS_REPORT.md` — 현재 오류 상태
- `CLAUDE.md Section 17` — 15 거버넌스 원칙
- `shared-intelligence/pitfalls.md` — 발견된 함정
- `shared-intelligence/patterns.md` — 재사용 가능한 패턴

---

**마지막 업데이트:** 2026-02-26 05:30 UTC
**담당:** Governance & Quality Assurance Team