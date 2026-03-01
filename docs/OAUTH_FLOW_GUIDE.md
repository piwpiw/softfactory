# OAuth 2.0 Social Login Flow - Complete Guide

**Version:** 2.0.0
**Last Updated:** 2026-02-26
**Platform:** SoftFactory Multi-Service

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Supported Providers](#supported-providers)
3. [Google OAuth Flow](#google-oauth-flow)
4. [Facebook OAuth Flow](#facebook-oauth-flow)
5. [Kakao OAuth Flow](#kakao-oauth-flow)
6. [Security Best Practices](#security-best-practices)
7. [Error Handling](#error-handling)
8. [Testing & Debugging](#testing--debugging)

---

## Overview

OAuth 2.0 allows users to securely authenticate using their existing social media accounts without sharing passwords. SoftFactory supports multiple providers for maximum user convenience.

**Key Benefits:**
- ✅ Secure authentication (no password sharing)
- ✅ Faster sign-up process
- ✅ Access to user profile data (with consent)
- ✅ Multiple provider options
- ✅ Automatic account linking

**Flow Diagram:**
```
User → SoftFactory → OAuth Provider → User Authorization → SoftFactory → Create/Update Account → JWT Token
```

---

## Supported Providers

| Provider | Provider ID | Country | Status | Scope |
|----------|------------|---------|--------|-------|
| Google | `google` | Global | ✅ Active | Profile, Email |
| Facebook | `facebook` | Global | ✅ Active | Profile, Email, Public |
| Kakao | `kakao` | Korea | ✅ Active | Profile, Email, Friends |
| Naver | `naver` | Korea | 🔄 Coming Soon | Profile, Email |
| GitHub | `github` | Developers | 🔄 Coming Soon | User, Email |

---

## Google OAuth Flow

### Prerequisites

1. **Google Cloud Console Setup:**
   - Create project at https://console.cloud.google.com
   - Enable Google+ API
   - Create OAuth 2.0 credentials (Web application)
   - Set Authorized Redirect URIs:
     ```
     http://localhost:8000/api/auth/oauth/google/callback (dev)
     https://api.softfactory.com/api/auth/oauth/google/callback (prod)
     ```

2. **Environment Variables:**
   ```bash
   GOOGLE_CLIENT_ID=your_client_id.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=your_client_secret
   ```

### Step 1: Get Authorization URL

**Endpoint:** `GET /api/auth/oauth/google/url`

**Query Parameters:**
```
?redirect_uri=https://app.softfactory.com/auth/callback
&state=random_state_token
&response_type=code
```

**Example Request:**
```bash
curl -X GET "http://localhost:8000/api/auth/oauth/google/url" \
  -H "Content-Type: application/json"
```

**Response (200 OK):**
```json
{
  "auth_url": "https://accounts.google.com/o/oauth2/v2/auth?client_id=YOUR_CLIENT_ID&redirect_uri=http://localhost:8000/api/auth/oauth/google/callback&response_type=code&scope=openid+email+profile&state=random_state_token",
  "state": "random_state_token",
  "expires_in": 600
}
```

**What Happens:**
1. User is redirected to Google login page
2. User signs in with their Google account
3. User grants permission to access profile data
4. Google redirects back to your app with authorization code

---

### Step 2: Redirect User to Auth URL

**Frontend Code (JavaScript):**
```javascript
// Get the authorization URL
const response = await fetch('/api/auth/oauth/google/url');
const { auth_url } = await response.json();

// Redirect user to Google
window.location.href = auth_url;
```

**User Experience:**
1. Click "Sign in with Google"
2. Redirected to Google login page
3. Sign in or select existing account
4. Grant permission to "SoftFactory" app
5. Redirected back to app

---

### Step 3: Handle Callback & Exchange Code

**What Happens Automatically:**
When user is redirected back to your callback URL, the browser will receive:
```
https://app.softfactory.com/auth/callback?code=4/0AY0e-g...&state=random_state_token
```

**Backend Endpoint:** `POST /api/auth/oauth/google/callback`

**Request Body:**
```json
{
  "code": "4/0AY0e-g...",
  "state": "random_state_token",
  "redirect_uri": "https://app.softfactory.com/auth/callback"
}
```

**Example cURL:**
```bash
curl -X POST "http://localhost:8000/api/auth/oauth/google/callback" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "4/0AY0e-g...",
    "state": "random_state_token"
  }'
```

**Response (200 OK):**
```json
{
  "success": true,
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 86400,
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 123,
    "email": "user@example.com",
    "name": "John Doe",
    "picture": "https://lh3.googleusercontent.com/...",
    "is_new_user": true
  }
}
```

---

### Step 4: Use JWT Token

**Store JWT in localStorage/sessionStorage:**
```javascript
const { access_token, user } = response.json();
localStorage.setItem('auth_token', access_token);
localStorage.setItem('user', JSON.stringify(user));
```

**Use in Subsequent API Calls:**
```javascript
const headers = {
  'Authorization': `Bearer ${localStorage.getItem('auth_token')}`,
  'Content-Type': 'application/json'
};

const response = await fetch('/api/user/profile', { headers });
```

**or with curl:**
```bash
curl -X GET "http://localhost:8000/api/user/profile" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json"
```

---

### Step 5: Refresh Token

**When JWT Expires:**
```bash
curl -X POST "http://localhost:8000/api/auth/refresh" \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }'
```

**Response (200 OK):**
```json
{
  "access_token": "new_jwt_token",
  "expires_in": 86400
}
```

---

## Facebook OAuth Flow

### Prerequisites

1. **Facebook App Setup:**
   - Create app at https://developers.facebook.com
   - Add "Facebook Login" product
   - Set Valid OAuth Redirect URIs:
     ```
     http://localhost:8000/api/auth/oauth/facebook/callback (dev)
     https://api.softfactory.com/api/auth/oauth/facebook/callback (prod)
     ```

2. **Environment Variables:**
   ```bash
   FACEBOOK_APP_ID=your_app_id
   FACEBOOK_APP_SECRET=your_app_secret
   ```

### Flow

**Get Authorization URL:**
```bash
GET /api/auth/oauth/facebook/url
```

**Response:**
```json
{
  "auth_url": "https://www.facebook.com/v18.0/dialog/oauth?client_id=YOUR_APP_ID&redirect_uri=http://localhost:8000/api/auth/oauth/facebook/callback&scope=public_profile,email&state=random_state_token",
  "state": "random_state_token"
}
```

**Exchange Code:**
```bash
POST /api/auth/oauth/facebook/callback
{
  "code": "facebook_code",
  "state": "random_state_token"
}
```

**Response:**
```json
{
  "access_token": "jwt_token",
  "user": {
    "id": 123,
    "email": "user@facebook.com",
    "name": "John Doe",
    "picture": "https://platform-lookaside.fbsbx.com/..."
  }
}
```

---

## Kakao OAuth Flow

### Prerequisites

1. **Kakao Developer Setup:**
   - Register app at https://developers.kakao.com
   - Add "Kakao Login" API
   - Set Redirect URI:
     ```
     http://localhost:8000/api/auth/oauth/kakao/callback (dev)
     https://api.softfactory.com/api/auth/oauth/kakao/callback (prod)
     ```

2. **Environment Variables:**
   ```bash
   KAKAO_REST_API_KEY=your_rest_api_key
   KAKAO_CLIENT_SECRET=your_client_secret
   ```

### Flow

**Get Authorization URL:**
```bash
GET /api/auth/oauth/kakao/url
```

**Response:**
```json
{
  "auth_url": "https://kauth.kakao.com/oauth/authorize?client_id=YOUR_REST_API_KEY&redirect_uri=http://localhost:8000/api/auth/oauth/kakao/callback&response_type=code&state=random_state_token",
  "state": "random_state_token"
}
```

**Exchange Code:**
```bash
POST /api/auth/oauth/kakao/callback
{
  "code": "kakao_code",
  "state": "random_state_token"
}
```

**Response:**
```json
{
  "access_token": "jwt_token",
  "user": {
    "id": 123,
    "email": "user@kakao.com",
    "name": "John Doe",
    "picture": "https://k.kakaocdn.net/..."
  }
}
```

---

## Account Linking

### Link OAuth Account to Existing User

If user is already logged in and wants to link a new OAuth provider:

```bash
POST /api/auth/oauth/link/{provider}
Authorization: Bearer YOUR_JWT_TOKEN
{
  "code": "oauth_code"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Google account linked successfully",
  "providers": ["google", "facebook", "kakao"]
}
```

---

## Security Best Practices

### 1. State Token Validation ✅
Always validate state token to prevent CSRF attacks:

```python
# Backend
def verify_state(request_state, stored_state):
    if request_state != stored_state:
        raise SecurityError("Invalid state token")
```

**Your app automatically validates this.**

### 2. PKCE (Proof Key for Code Exchange)
For mobile/SPA apps, use PKCE:

```javascript
// Generate code verifier and challenge
const codeVerifier = generateRandomString(128);
const codeChallenge = base64UrlEncode(sha256(codeVerifier));

// Request with code_challenge
// Exchange with code_verifier
```

### 3. Token Storage
```javascript
// ✅ DO: Store in memory or secure HTTP-only cookie
localStorage.setItem('auth_token', token); // OK for demo

// ❌ DON'T: Log or expose tokens
console.log(token); // NEVER

// ✅ DO: Use HTTPS in production
// ❌ DON'T: Use HTTP with tokens
```

### 4. Scope Minimization
```python
# Request only needed scopes
scopes = ["openid", "email", "profile"]  # ✅ Minimal
# NOT: ["openid", "email", "profile", "phone", "address"]
```

### 5. Token Refresh
```javascript
// Automatically refresh before expiry
if (isTokenExpiring()) {
  refreshToken();
}
```

---

## Error Handling

### Authorization Error
```json
{
  "error": "invalid_request",
  "error_description": "The request is invalid",
  "state": "random_state_token"
}
```

### Token Exchange Error
```json
{
  "error": "OAUTH_EXCHANGE_FAILED",
  "message": "Failed to exchange code for token",
  "provider": "google",
  "details": "Invalid authorization code"
}
```

### Account Linking Error
```json
{
  "error": "ACCOUNT_ALREADY_LINKED",
  "message": "This Google account is already linked to another SoftFactory account",
  "existing_user_id": 456
}
```

---

## Testing & Debugging

### Test Google OAuth Locally

**1. Create OAuth Credentials:**
- Go to https://console.cloud.google.com
- Create "Web application" credential
- Add `http://localhost:8000/api/auth/oauth/google/callback` as redirect URI

**2. Test with cURL:**
```bash
# Get auth URL
curl http://localhost:8000/api/auth/oauth/google/url

# Manually open URL in browser
# Complete login and get code from redirect

# Exchange code
curl -X POST http://localhost:8000/api/auth/oauth/google/callback \
  -H "Content-Type: application/json" \
  -d '{
    "code": "code_from_redirect",
    "state": "state_from_url"
  }'
```

**3. Test with Postman:**
- Create new POST request to `/api/auth/oauth/google/callback`
- Set Body to:
  ```json
  {
    "code": "test_code",
    "state": "test_state"
  }
  ```
- Send request and inspect response

### Debugging Tips

**Check Logs:**
```bash
docker logs softfactory-api | grep oauth
tail -f logs/app.log | grep oauth
```

**Enable Debug Mode:**
```python
# In app.py
app.debug = True
app.logger.setLevel(logging.DEBUG)
```

**Common Issues:**

1. **"Redirect URI mismatch"**
   - Verify redirect URI matches exactly in OAuth provider settings
   - Check for trailing slashes and protocol (http vs https)

2. **"Invalid client ID"**
   - Verify `GOOGLE_CLIENT_ID` environment variable is set correctly
   - Ensure credentials are not expired

3. **"Code exchange failed"**
   - Code may have expired (valid for ~10 minutes)
   - State token may not match
   - Check backend logs for details

---

## Complete Integration Example

### Frontend (HTML + JavaScript)

```html
<!DOCTYPE html>
<html>
<head>
    <title>SoftFactory Login</title>
</head>
<body>
    <button onclick="loginWithGoogle()">Sign in with Google</button>
    <button onclick="loginWithFacebook()">Sign in with Facebook</button>

    <script>
        async function loginWithGoogle() {
            try {
                // Get authorization URL
                const response = await fetch('/api/auth/oauth/google/url');
                const { auth_url } = await response.json();

                // Redirect to Google
                window.location.href = auth_url;
            } catch (error) {
                console.error('Login error:', error);
            }
        }

        async function loginWithFacebook() {
            try {
                // Get authorization URL
                const response = await fetch('/api/auth/oauth/facebook/url');
                const { auth_url } = await response.json();

                // Redirect to Facebook
                window.location.href = auth_url;
            } catch (error) {
                console.error('Login error:', error);
            }
        }

        // Handle callback
        async function handleCallback() {
            const params = new URLSearchParams(window.location.search);
            const code = params.get('code');
            const state = params.get('state');
            const provider = params.get('provider') || 'google';

            if (!code) return;

            try {
                // Exchange code for JWT
                const response = await fetch(
                    `/api/auth/oauth/${provider}/callback`,
                    {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ code, state })
                    }
                );

                const { access_token, user } = await response.json();

                // Store token
                localStorage.setItem('auth_token', access_token);
                localStorage.setItem('user', JSON.stringify(user));

                // Redirect to dashboard
                window.location.href = '/dashboard';
            } catch (error) {
                console.error('Callback error:', error);
            }
        }

        // Run on page load
        handleCallback();
    </script>
</body>
</html>
```

### Backend (Python Flask)

Already implemented in `/backend/auth.py` and `/backend/oauth.py`.

---

## API Reference Summary

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/auth/oauth/{provider}/url` | GET | Get authorization URL |
| `/api/auth/oauth/{provider}/callback` | POST | Exchange code for token |
| `/api/auth/oauth/link/{provider}` | POST | Link OAuth account |
| `/api/auth/logout` | POST | Logout and revoke token |
| `/api/auth/profile` | GET | Get current user profile |
| `/api/auth/refresh` | POST | Refresh JWT token |

---

**Last Updated:** 2026-02-26
**Status:** Production Ready ✅
**Support:** support@softfactory.com
