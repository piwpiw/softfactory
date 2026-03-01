# ⚡ 5분 안에 배포하기 (Heroku 무료)

## 🎯 목표
JARVIS를 **전 세계 어디서나 접근 가능**하게 배포

---

## ✅ 배포 단계

### 1️⃣ Heroku CLI 설치 (1분)
**Windows (PowerShell 관리자 모드):**
```powershell
choco install heroku-cli -y
```

아니면 직접 다운로드:
```
https://devcenter.heroku.com/articles/heroku-cli
```

설치 확인:
```bash
heroku --version
```

---

### 2️⃣ Heroku 로그인 (1분)
```bash
heroku login
```
→ 브라우저에서 로그인

---

### 3️⃣ 앱 생성 및 배포 (2분)
```bash
cd D:/Project

# Heroku 앱 생성
heroku create

# 예: Created https://xxxxxx.herokuapp.com/
# 이 URL을 기억하세요!
```

---

### 4️⃣ API 키 설정 (1분)
```bash
# Anthropic API 키 설정
heroku config:set ANTHROPIC_API_KEY=sk-ant-api03-[YOUR_KEY_HERE]

# Telegram (선택)
heroku config:set TELEGRAM_BOT_TOKEN=8461725251:AAE...
heroku config:set TELEGRAM_CHAT_ID=7910169750
```

---

### 5️⃣ 배포 (자동)
```bash
# Git 준비
git add .
git commit -m "🚀 Deploy JARVIS to Heroku"

# 배포
git push heroku main
# 또는
git push heroku master
```

---

## 🎉 완료!

**배포 URL:**
```
https://[your-app-name].herokuapp.com/
```

**테스트:**
```bash
# 앱 열기
heroku open

# 로그 확인
heroku logs --tail
```

---

## 📍 접근 가능한 URL들

| 페이지 | URL |
|------|-----|
| 🎛️ 제어판 | https://[app].herokuapp.com/operations.html |
| 👥 팀 관리 | https://[app].herokuapp.com/teams.html |
| 📊 분석 | https://[app].herokuapp.com/analytics.html |
| 📈 대시보드 | https://[app].herokuapp.com/dashboard.html |
| 🏠 홈페이지 | https://[app].herokuapp.com/index.html |
| 🔌 API | https://[app].herokuapp.com/api/v1/status |

---

## ❓ 문제 해결

### Git 초기화 안 되어있으면?
```bash
cd D:/Project
git init
git config user.name "Your Name"
git config user.email "your@email.com"
git add .
git commit -m "Initial commit"
git push heroku main
```

### Heroku CLI 못 찾음?
```bash
# 다시 설치
choco uninstall heroku-cli -y
choco install heroku-cli -y

# PowerShell 재시작
```

### 배포 실패?
```bash
# 로그 확인
heroku logs --tail

# 재시작
heroku restart

# 상태 확인
heroku ps
```

---

## 💡 팁

- **무료 사용:** 첫 3개월 무료 (550시간/월)
- **자동 배포:** GitHub 연동하면 push 시 자동 배포
- **모니터링:** `heroku logs --tail` 로 실시간 로그
- **스케일링:** `heroku ps:scale web=2` 로 인스턴스 추가

---

**준비됐나요? 지금 배포하세요!** 🚀
