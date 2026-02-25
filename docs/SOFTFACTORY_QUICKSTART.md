# 🚀 SoftFactory 빠른 시작

> **마지막 업데이트:** 2026-02-23 | **상태:** ✅ DEPLOYED | **라이브:** http://localhost:8000

---

## ⚡ 1분 시작 (복사+붙여넣기)

```bash
cd D:/Project
pip install -r requirements.txt
python start_platform.py
```

**결과:**
```
SoftFactory starting at http://localhost:8000
✅ Database: D:/Project/platform.db
✅ Demo: admin@softfactory.com / admin123
```

---

## 📝 15초 데모 로그인

```
이메일: admin@softfactory.com
비번:  admin123
```

→ 대시보드 접속 → 3개 서비스 구독 가능

---

## 🗂️ 파일 구조

```
D:/Project/
├── backend/                       ← Flask 앱
│   ├── app.py (포트 8000)
│   ├── models.py (10개 DB 모델)
│   ├── auth.py (JWT 토큰)
│   ├── payment.py (Stripe 결제)
│   ├── platform.py (허브 라우트)
│   └── services/ (3개 서비스)
├── web/ (15개 HTML 페이지)
├── start_platform.py (진입점)
├── requirements.txt (의존성)
├── .env (설정)
└── platform.db (DB, 자동 생성)
```

---

## 🔧 설정 (`.env`)

```env
PLATFORM_SECRET_KEY=PLATFORM_SECRET_KEY_REDACTED
STRIPE_SECRET_KEY=sk_test_your_key_here    # 선택사항
STRIPE_PUBLISHABLE_KEY=pk_test_your_key    # 선택사항
PLATFORM_URL=http://localhost:8000
```

결제 키 없어도 모든 기능 작동 ✅

---

## 🎯 3개 서비스

| 서비스 | 가격 | 설명 | 페이지 |
|--------|------|------|--------|
| **CooCook** | $29/월 | 셰프 예약 | `/web/coocook/` |
| **SNS Auto** | $49/월 | 소셜미디어 자동화 | `/web/sns-auto/` |
| **Review** | $39/월 | 체험단 캠페인 | `/web/review/` |

---

## 📊 API 엔드포인트 (전체)

### 인증
```
POST   /api/auth/register        # 회원가입
POST   /api/auth/login           # 로그인
POST   /api/auth/refresh         # 토큰 갱신
GET    /api/auth/me              # 현재 사용자
```

### 플랫폼
```
GET    /api/platform/products    # 서비스 목록 (공개)
GET    /api/platform/dashboard   # 대시보드 (인증)
GET    /api/platform/admin/users      # 사용자 목록 (관리자)
GET    /api/platform/admin/revenue    # MRR/ARR (관리자)
```

### CooCook
```
GET    /api/coocook/chefs                      # 셰프 목록
GET    /api/coocook/chefs/<id>                 # 셰프 상세
POST   /api/coocook/chefs                      # 셰프 등록
GET    /api/coocook/bookings                   # 내 예약
POST   /api/coocook/bookings                   # 예약 생성
```

### SNS Auto
```
GET    /api/sns/accounts              # 계정 목록
POST   /api/sns/accounts              # 계정 연동
DELETE /api/sns/accounts/<id>         # 계정 삭제
GET    /api/sns/posts                 # 포스트 목록
POST   /api/sns/posts                 # 포스트 생성
POST   /api/sns/posts/<id>/publish    # 발행/스케줄
DELETE /api/sns/posts/<id>            # 포스트 삭제
GET    /api/sns/templates             # 템플릿 목록
```

### Review Campaigns
```
GET    /api/review/campaigns                      # 캠페인 목록
POST   /api/review/campaigns                      # 캠페인 생성
GET    /api/review/campaigns/<id>                 # 캠페인 상세
POST   /api/review/campaigns/<id>/apply           # 신청
GET    /api/review/my-campaigns                   # 내 캠페인
GET    /api/review/my-applications                # 내 신청
GET    /api/review/campaigns/<id>/applications    # 신청 목록
PUT    /api/review/applications/<id>              # 승인/거절
```

---

## 🐛 자주하는 실수

| 실수 | 해결책 |
|------|--------|
| **포트 8000이 이미 사용됨** | `lsof -i :8000` → PID 죽이기, 또는 다른 포트 사용 |
| **`ModuleNotFoundError`** | `pip install -r requirements.txt --upgrade` |
| **DB 잠김** | `platform.db` 삭제 (자동 재생성) |
| **로그인 안 됨** | 토큰 localStorage 확인: F12 → Application → localStorage |
| **API 404 에러** | 포트 8000 확인, 라우트 경로 확인 (`/api/` 빠뜨림?) |
| **CORS 에러** | `.env`에서 `PLATFORM_URL` 확인 |

---

## 🔗 URLs

| 페이지 | URL |
|--------|-----|
| **홈** | http://localhost:8000 |
| **로그인** | http://localhost:8000/web/platform/login.html |
| **대시보드** | http://localhost:8000/web/platform/dashboard.html |
| **CooCook** | http://localhost:8000/web/coocook/index.html |
| **SNS Auto** | http://localhost:8000/web/sns-auto/index.html |
| **Review** | http://localhost:8000/web/review/index.html |

---

## 📦 샘플 데이터

자동 초기화됨:
- ✅ 3개 상품 (가격, 설명)
- ✅ Admin 계정 (관리자)
- ✅ Demo 계정 (테스트용)
- ✅ 5명 샘플 셰프
- ✅ 3개 샘플 캠페인

---

## 🚀 다음 단계

1. **로그인:** admin@softfactory.com / admin123
2. **서비스 구독:** Stripe 버튼 (선택)
3. **CooCook 사용:** 셰프 탐색 → 예약
4. **SNS Auto 사용:** 계정 연동 → 포스트 생성
5. **Review 사용:** 캠페인 보기 → 신청

---

## 🎯 새 서비스 추가 (10-30분)

```
1. backend/services/새서비스.py 생성
   - Blueprint 정의
   - 라우트 추가

2. backend/models.py에 모델 추가
   - DB 테이블 정의

3. web/새서비스/ 폴더 생성
   - HTML 페이지 3-5개

4. backend/app.py에 Blueprint 등록
   - app.register_blueprint(새서비스_bp)

5. backend/models.py init_db() 수정
   - Product 시드 데이터 추가

완료! 🎉
```

---

**더 자세한 정보:** [ARCHITECTURE.md](ARCHITECTURE.md) | [TEAM.md](TEAM.md) | [RULES.md](RULES.md)
