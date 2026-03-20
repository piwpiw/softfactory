#!/usr/bin/env python
"""
Telegram 엔드포인트 smoke test — Step 3 검증
JWT 토큰 생성 후 /api/telegram/status 호출
"""
import sys
import os
import requests
from datetime import datetime

# 프로젝트 루트 추가
sys.path.insert(0, 'd:/Project')

# Flask app 초기화 (데이터베이스 포함)
# CRITICAL: Set TESTING=true BEFORE importing backend modules to ensure
# consistent SECRET_KEY across test process and Flask app process.
# This prevents ephemeral key generation mismatch.
os.environ['TESTING'] = 'true'
os.environ['ENVIRONMENT'] = 'development'

from backend.auth import create_jwt_token
from backend.app import create_app
from backend.models import db, User

# Flask app 생성
app = create_app()

with app.app_context():
    # 테스트용 사용자 확인 또는 생성
    test_user = User.query.filter_by(email='test@example.com').first()
    if not test_user:
        test_user = User(
            email='test@example.com',
            name='testuser',
            password_hash='dummy'
        )
        db.session.add(test_user)
        db.session.commit()
        print(f"[OK] 테스트 사용자 생성: {test_user.id}")
    else:
        print(f"[OK] 기존 테스트 사용자 사용: {test_user.id}")

    # JWT 토큰 생성
    token = create_jwt_token(user_id=test_user.id, user_role='user')
    print(f"[OK] JWT 토큰 생성 완료")
    print(f"  - User ID: {test_user.id}")
    print(f"  - Token preview: {token[:20]}...")

# Flask 앱 실행 중이어야 함
print("\n======================================")
print("Telegram 엔드포인트 테스트 시작")
print("======================================")
print(f"시간: {datetime.now().isoformat()}")
print()

# HTTP 요청 수행
headers = {
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json'
}

try:
    # 포트 9000 (Flask 메인 엔드포인트)으로 요청
    response = requests.get(
        'http://localhost:9000/api/telegram/status',
        headers=headers,
        timeout=5
    )

    print(f"[OK] HTTP 요청 완료")
    print(f"  - URL: http://localhost:9000/api/telegram/status")
    print(f"  - 상태 코드: {response.status_code}")
    print()

    if response.status_code == 200:
        data = response.json()
        print("[OK] 응답 데이터 (HTTP 200):")
        for key, value in data.items():
            if key == 'masked_chat_id' or key == 'telegram_chat_id':
                print(f"  - {key}: {value} (마스킹됨)")
            else:
                print(f"  - {key}: {value}")
        print()
        print("======================================")
        print("[OK] Telegram 통합 정상 작동 확인!")
        print("======================================")
    else:
        print(f"[FAIL] 예상치 못한 상태 코드: {response.status_code}")
        print(f"  응답: {response.text}")

except requests.exceptions.ConnectionError:
    print("[FAIL] 연결 실패: Flask 앱이 http://localhost:9000 에서 실행 중이어야 합니다")
    print("  다음 명령어로 Flask 앱 시작:")
    print("  python d:/Project/start_platform.py")
except Exception as e:
    print(f"[FAIL] 에러: {e}")
