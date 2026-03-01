# 🔌 SaaS OAuth & API 인증 설정 완료 ✅

> **Purpose**: **Date:** 2026-02-26
> **Status**: 🟢 ACTIVE (관리 중)
> **Impact**: [Engineering / Operations]

---

## ⚡ Executive Summary (핵심 요약)
- **주요 내용**: 본 문서는 SaaS OAuth & API 인증 설정 완료 ✅ 관련 핵심 명세 및 관리 포인트를 포함합니다.
- **상태**: 현재 최신화 완료 및 검토 됨.
- **연관 문서**: [Master Index](./NOTION_MASTER_INDEX.md)

---

**Date:** 2026-02-26
**Status:** 완전 설정됨 (Demo/Test Credentials)

## 📋 설정된 모든 SaaS 서비스

### 1. Google OAuth ✅
- **Client ID:** 847528942891-5h6v0j8t2k9n4m1p3q6r9s2t5u8v1w4x.apps.googleusercontent.com
- **Client Secret:** GOCSPX-8h6v0j8t2k9n4m1p3q6r9s2t5u
- **Redirect URI:** http://localhost:9000/api/auth/oauth/google/callback
- **Scopes:** openid, profile, email
- **Status:** Mock Mode (테스트용 Demo 키)

### 2. Facebook OAuth ✅
- **App ID:** 1234567890123456
- **App Secret:** a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
- **Redirect URI:** http://localhost:9000/api/auth/oauth/facebook/callback
- **Scopes:** public_profile, email
- **Status:** Mock Mode (테스트용 Demo 키)

### 3. Kakao OAuth ✅
- **REST API Key:** 1234567890abcdefghijklmnopqrstuv
- **Client Secret:** a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
- **Redirect URI:** http://localhost:9000/api/auth/oauth/kakao/callback
- **Scopes:** openid, profile, account_email
- **Status:** Mock Mode (테스트용 Demo 키)

### 4. Stripe Payment API ✅
- **Secret Key:** sk_test_51NxYzKL8h6v0j8t2k9n4m1p3q6r9s2t5u8v1w4x9y2z3a4b5c6d7e8f9g0h1i
- **Publishable Key:** pk_test_51NxYzKL8h6v0j8t2k9n4m1p3q6r9s2t5u8v1w4x9y2z3a4b5c6d7e8f9g0h1i
- **Webhook Secret:** whsec_1NxYzKL8h6v0j8t2k9n4m1p3q6r9s2t5u8v1w4x9y2z3a4b5c6d7e8f9g0h1i
- **Status:** Mock Mode (테스트용 Demo 키)

### 5. JWT Authentication ✅
- **JWT Secret:** softfactory-jwt-secret-2026
- **Token Expiry:** 1 hour (access), 30 days (refresh)
- **Algorithm:** HS256

### 6. Platform Security ✅
- **Platform Secret Key:** softfactory-dev-secret-key-2026
- **Database:** SQLite (D:/Project/platform.db)

### 7. Telegram Bot ✅
- **Bot Token:** 8461725251:AAELKRbZkpa3u6WK24q4k-RGkzedHxjTLiM
- **Chat ID:** 7910169750
- **Status:** 활성화 완료

## 🔌 API 엔드포인트

### OAuth Authorization URLs
```bash
# Google
GET http://localhost:9000/api/auth/oauth/google/url

# Facebook
GET http://localhost:9000/api/auth/oauth/facebook/url

# Kakao
GET http://localhost:9000/api/auth/oauth/kakao/url
```

### OAuth Callbacks
```bash
# All providers (POST)
POST http://localhost:9000/api/auth/oauth/{provider}/callback
Content-Type: application/json

{
  "code": "authorization_code_from_provider",
  "state": "state_token_from_url"
}
```

### Demo OAuth Flow
```bash
# Step 1: Get auth URL
curl http://localhost:9000/api/auth/oauth/google/url
# Returns: { "auth_url": "mock://google/auth?...", "state": "...", "mock_mode": true }

# Step 2: Exchange code for token (with demo credentials)
curl -X POST http://localhost:9000/api/auth/oauth/google/callback \
  -H "Content-Type: application/json" \
  -d '{
    "code": "demo_auth_code",
    "state": "demo_state"
  }'

# Returns: JWT access/refresh tokens + user info
```

## 📁 설정 파일

**Updated Files:**
- `.env` - 모든 OAuth, Stripe, JWT 키 설정
- `backend/auth.py` - Provider별 redirect_uri 지원 추가
- `backend/oauth.py` - Mock mode 포함 완전 구현

**Key Features:**
- ✅ Mock Mode: 실제 credentials 없어도 테스트 가능
- ✅ Provider Abstraction: Google, Facebook, Kakao 지원
- ✅ CSRF Protection: State token 기반 검증
- ✅ User Auto-Creation: OAuth 사용자 자동 등록
- ✅ JWT Integration: OAuth 로그인 후 JWT 토큰 발급

## 🧪 테스트 방법

### 1. Mock Mode Test (즉시 사용 가능)
```bash
# Flask 시작
cd /d/Project
python start_platform.py

# OAuth URL 요청 (mock mode)
curl http://localhost:9000/api/auth/oauth/google/url

# 응답
{
  "auth_url": "mock://google/auth?state=...",
  "state": "...",
  "mock_mode": true
}
```

### 2. 실제 OAuth 사용 (credentials 교체 후)
1. Google Cloud Console에서 credentials 생성
2. Facebook Developer에서 앱 등록
3. Kakao Developers에서 앱 등록
4. 각 credentials를 .env에 교체
5. Flask 재시작

## 🔐 보안 기능

- [x] CSRF Protection (State Token)
- [x] JWT Token Signing
- [x] Secure OAuth Code Exchange
- [x] User Password Hashing (OAuth users get random passwords)
- [x] Token Expiration (1 hour access, 30 days refresh)
- [x] OAuth Provider Validation
- [x] Error Handling

## 📊 Demo 사용자 인증

### 기본 인증
```bash
# Email/Password 로그인
curl -X POST http://localhost:9000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "demo@softfactory.com",
    "password": "demo123"
  }'

# Response: JWT access token + refresh token
```

### OAuth 로그인
```bash
# Google OAuth 로그인 (mock mode)
curl -X POST http://localhost:9000/api/auth/oauth/google/callback \
  -H "Content-Type: application/json" \
  -d '{
    "code": "demo_code",
    "state": "demo_state"
  }'

# Response: JWT access token + 자동 등록된 사용자 정보
```

## 🎯 다음 단계 (프로덕션 배포)

1. **실제 OAuth Credentials 등록**
   - Google Cloud Console
   - Facebook App Center
   - Kakao Developers

2. **Stripe 실제 계정 설정**
   - Stripe Dashboard에서 API keys 획득
   - Webhook 설정

3. **환경변수 업데이트**
   - .env 파일의 mock 키들을 실제 키로 교체
   - 환경별로 다른 .env 사용 (dev, staging, prod)

4. **HTTPS 설정**
   - OAuth2에서는 HTTPS 필수 (프로덕션)
   - Localhost는 HTTP 허용

5. **Security Headers**
   - Secure cookies
   - HSTS (HTTP Strict Transport Security)
   - Content Security Policy

## ✨ 현재 상태

```
✅ JWT Authentication
✅ OAuth 2.0 Social Login (Google, Facebook, Kakao)
✅ Demo/Test Credentials
✅ Mock Mode Support
✅ User Auto-Registration
✅ Token Management
✅ Stripe API Integration
✅ Telegram Bot Integration
✅ Port 9000 설정 완료
```

## 📞 지원되는 OAuth Providers

| Provider | Status | Mode |
|----------|--------|------|
| Google   | ✅ 설정됨 | Mock/Real |
| Facebook | ✅ 설정됨 | Mock/Real |
| Kakao    | ✅ 설정됨 | Mock/Real |

모든 서비스가 데모 모드로 즉시 사용 가능하며, 실제 credentials로 업그레이드 가능합니다!