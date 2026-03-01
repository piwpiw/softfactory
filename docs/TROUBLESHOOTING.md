# 🔧 트러블슈팅 & FAQ

> **마지막 업데이트:** 2026-02-23 | **상태:** ✅ ACTIVE

---

## 🚨 앱이 안 켜져요

### ❌ "ModuleNotFoundError: No module named 'flask'"

**원인:** 의존성 미설치

**해결:**
```bash
pip install -r requirements.txt --upgrade
python start_platform.py
```

---

### ❌ "Address already in use" (포트 8000)

**원인:** 포트 8000이 이미 사용 중

**해결 1 (프로세스 죽이기):**
```bash
lsof -i :8000  # PID 확인
kill -9 <PID>  # 프로세스 종료
python start_platform.py
```

**해결 2 (다른 포트 사용):**
```python
# backend/app.py 마지막 줄 수정
app.run(host='0.0.0.0', port=9000)  # 8000 → 9000
```

---

### ❌ "FileNotFoundError: platform.db not found"

**원인:** DB 파일 손상 또는 경로 문제

**해결:**
```bash
# 손상된 DB 삭제 (안전, 자동 재생성됨)
rm D:/Project/platform.db

# 다시 시작
python start_platform.py
```

---

## 🔐 로그인이 안 돼요

### ❌ "Invalid credentials"

**원인 1:** 아이디/비번 오타

**해결:**
```
이메일: admin@softfactory.com  (정확히!)
비번: admin123
```

**원인 2:** DB 초기화 실패

**해결:**
```bash
rm D:/Project/platform.db
python start_platform.py
# 자동으로 admin 계정 생성됨
```

---

### ❌ "Token expired"

**원인:** 접근 토큰 만료 (1시간)

**해결:** 자동 갱신됨 (api.js에서 처리)

수동 갱신 필요 시:
```javascript
// 브라우저 콘솔에서
const refresh_token = localStorage.getItem('refresh_token');
fetch('http://localhost:8000/api/auth/refresh', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({refresh_token})
})
```

---

## 🌐 API가 응답 안 해요

### ❌ "404 Not Found"

**원인 1:** 잘못된 URL

**확인:**
```
❌ /api/coocook/chefs
✅ /api/coocook/chefs    (정확히)
```

**원인 2:** 포트 번호 잘못됨

**확인:**
```
❌ http://localhost:5000/api/...  (JARVIS Bot)
✅ http://localhost:8000/api/...  (SoftFactory)
```

---

### ❌ "CORS error"

**원인:** CORS 설정 문제

**확인:**
- 브라우저 콘솔 확인 (F12 → Console)
- 정확한 URL 확인

**해결:**
```python
# backend/app.py 확인
CORS(app, resources={r"/api/*": {
    "origins": ["http://localhost:8000", "http://localhost:5000", "null"]
}})
```

---

### ❌ "401 Unauthorized"

**원인:** 토큰 없음 또는 만료

**해결:**
1. 로그인 다시 하기
2. localStorage 토큰 확인:
```javascript
localStorage.getItem('access_token')
```

3. API 헤더 확인:
```javascript
headers: {
  'Authorization': `Bearer ${token}`
}
```

---

## 💾 DB 문제

### ❌ "database is locked"

**원인:** DB 파일이 다른 프로세스에 의해 잠김

**해결:**
```bash
# DB 삭제 (안전)
rm D:/Project/platform.db

# 재시작 (자동 재생성)
python start_platform.py
```

---

### ❌ "Integrity constraint violation"

**원인:** 중복 데이터 또는 FK 위반

**해결:** DB 초기화
```bash
rm D:/Project/platform.db
python start_platform.py
```

---

## 🧪 테스트 문제

### ❌ "모든 API를 테스트하고 싶어요"

**방법 1: curl 사용**
```bash
# 헬스 체크
curl http://localhost:8000/health

# 상품 조회
curl http://localhost:8000/api/platform/products

# 로그인
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@softfactory.com","password":"admin123"}'
```

**방법 2: Postman 사용**
- Import → Raw JSON:
```json
{
  "info": {"name": "SoftFactory"},
  "item": [
    {
      "name": "Health",
      "request": {"url": "http://localhost:8000/health"}
    }
  ]
}
```

---

## 🎨 프론트엔드 문제

### ❌ "페이지가 안 로드돼요"

**원인 1:** 포트 8000 확인

**원인 2:** 정적 파일 경로 문제

**확인:**
```
✅ http://localhost:8000/web/platform/login.html
❌ http://localhost:8000/login.html
```

---

### ❌ "CSS / 스타일이 안 보여요"

**원인:** Tailwind CSS 스타일 미적용

**확인:** HTML head에 있는지
```html
<link href="https://cdn.tailwindcss.com" rel="stylesheet">
```

---

### ❌ "JavaScript 에러"

**원인:** api.js 경로 오류

**확인:**
```html
<script src="../../platform/api.js"></script>  <!-- 경로 맞나? -->
```

---

## 🔑 설정 문제

### ❌ "SECRET_KEY가 없어요"

**원인:** .env 파일 누락

**해결:**
```bash
# .env 생성
echo "PLATFORM_SECRET_KEY=softfactory-dev-secret-key-2026" > .env
```

---

### ❌ "Stripe 결제가 안 돼요"

**원인:** Stripe 키 미설정 (정상)

**상태:** 개발 모드에서는 결제 버튼만 비활성 → 그 외 모든 기능 정상 작동 ✅

**설정 원할 때:**
```env
STRIPE_SECRET_KEY=sk_test_your_key
STRIPE_PUBLISHABLE_KEY=pk_test_your_key
```

---

## 🔄 데이터 초기화

### ✅ "깨끗한 상태로 다시 시작하고 싶어요"

```bash
# 1. 앱 종료
# Ctrl+C

# 2. DB 삭제
rm D:/Project/platform.db

# 3. 재시작
python start_platform.py

# 결과: 깨끗한 상태, 샘플 데이터 자동 생성
```

---

## 📊 성능 문제

### ❌ "앱이 느려요"

**확인:**
```bash
# Python 메모리/CPU 사용량
top  # Mac/Linux
tasklist | grep python  # Windows
```

**해결:**
```bash
# 캐시 삭제
rm -rf __pycache__
pip cache purge

# 재시작
python start_platform.py
```

---

## 📈 배포 관련

### ❌ "GitHub에 푸시하고 싶은데 자격증명 에러"

**원인:** Git 인증 실패

**해결:**
```bash
git config --global user.email "you@example.com"
git config --global user.name "Your Name"

# 토큰 기반 인증 사용
git remote set-url origin https://<token>@github.com/user/repo.git
```

---

### ❌ "Merge conflict가 생겼어요"

**해결:**
```bash
# 1. 상태 확인
git status

# 2. 충돌 파일 해결
# 편집기에서 <<<<<<< ======= >>>>>>> 처리

# 3. 다시 커밋
git add .
git commit -m "Resolve merge conflicts"
```

---

## ❓ 자주 묻는 질문

| Q | A |
|----|---|
| **데이터가 저장돼요?** | ✅ SQLite에 저장됨. 앱 종료해도 유지. |
| **여러 서비스를 동시에 쓸 수 있어요?** | ✅ 3개 서비스 모두 독립적으로 작동. |
| **새 서비스를 추가할 수 있어요?** | ✅ 10-30분 소요. [SOFTFACTORY_QUICKSTART.md](SOFTFACTORY_QUICKSTART.md) 참조. |
| **사용자를 추가할 수 있어요?** | ✅ `/api/auth/register` 엔드포인트로 회원가입. |
| **가격을 바꿀 수 있어요?** | ✅ `backend/models.py` → Product 모델 수정. |
| **외부에서 접속할 수 있어요?** | ⚠️ 현재는 localhost만. 배포 필요. |

---

**도움이 안 됐나요?** → [TEAM.md](TEAM.md)에서 담당자 찾기

**마지막 업데이트:** 2026-02-23
