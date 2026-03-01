#!/bin/bash
# 30분 지속적 개선 작업 스크립트

echo "=== 지속적 개선 작업 시작 ==="
echo "시작시간: $(date)"
echo ""

# 1. 코드 정적 분석
echo "[1/8] 코드 품질 분석..."
python -m pylint backend/ --disable=all --enable=C,E,F --exit-zero > code-quality.txt 2>&1 || true

# 2. 보안 의존성 확인
echo "[2/8] 보안 업데이트 확인..."
pip list --outdated | grep -i flask || echo "Flask 최신버전"
pip list --outdated | grep -i sqlalchemy || echo "SQLAlchemy 최신버전"

# 3. 파일 크기 분석
echo "[3/8] 프로젝트 크기 분석..."
du -sh backend/ web/ scripts/ docs/ 2>/dev/null | head -10

# 4. 데이터베이스 통계
echo "[4/8] 데이터베이스 통계..."
sqlite3 platform.db "SELECT name, COUNT(*) as count FROM (
  SELECT 'users' as name FROM users UNION ALL
  SELECT 'chefs' FROM chefs UNION ALL
  SELECT 'bookings' FROM bookings UNION ALL
  SELECT 'products' FROM products
) GROUP BY name;" 2>/dev/null || echo "DB 접근 불가"

# 5. API 응답시간 기록
echo "[5/8] API 응답시간 측정..."
for endpoint in "health" "chefs" "bookings"; do
  time curl -s http://localhost:8000/api/$endpoint -w "\nStatus: %{http_code}\n" > /dev/null 2>&1 || echo "엔드포인트 테스트 불가"
done

# 6. 로그 분석
echo "[6/8] 오류 로그 분석..."
grep -r "ERROR\|CRITICAL" /tmp/*.log 2>/dev/null | head -5 || echo "주요 오류 없음"

# 7. 테스트 실행 (빠른 버전)
echo "[7/8] 고속 테스트 실행..."
python -m pytest tests/e2e/ -q --tb=no 2>/dev/null || echo "테스트 실행"

# 8. 배포 준비 상태
echo "[8/8] 배포 준비 상태..."
echo "- Docker: $(docker --version 2>/dev/null || echo 'Not running')"
echo "- Git: $(git log --oneline -1 2>/dev/null)"
echo "- Python: $(python --version)"

echo ""
echo "완료시간: $(date)"
echo "=== 지속적 개선 작업 완료 ==="
