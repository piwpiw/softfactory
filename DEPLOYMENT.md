# 🚀 JARVIS Heroku 배포 가이드

**목표:** 전 세계 어디서나 접근 가능한 CooCook JARVIS 운영 플랫폼

---

## 📋 사전 준비

### 1️⃣ Heroku 계정 생성 (무료)
```bash
# https://www.heroku.com 방문
# 회원가입 (이메일 인증)
```

### 2️⃣ Heroku CLI 설치
```bash
# Windows (PowerShell 관리자 모드)
choco install heroku-cli

# 또는 직접 다운로드
# https://devcenter.heroku.com/articles/heroku-cli

# 설치 확인
heroku --version
```

### 3️⃣ Heroku 로그인
```bash
heroku login
# 브라우저에서 로그인 수행
```

### 4️⃣ API 키 준비
- **ANTHROPIC_API_KEY**: Claude API 키 (필수)
- **TELEGRAM_BOT_TOKEN**: Telegram Bot Token (선택)
- **TELEGRAM_CHAT_ID**: Telegram Chat ID (선택)

---

## ⚡ 배포 방법 (선택 1: 자동 배포 - 추천)

**가장 쉬운 방법: Heroku 버튼 클릭**

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/coocook/jarvis)

1️⃣ 위 버튼 클릭
2️⃣ `ANTHROPIC_API_KEY` 입력
3️⃣ `Deploy app` 클릭
4️⃣ 5분 후 완료 ✅

---

## 🔧 배포 방법 (선택 2: 수동 배포)

### Step 1: 로컬 Git 저장소 준비
```bash
cd D:/Project

# Git 초기화 (이미 되어있으면 스킵)
git init
git add .
git commit -m "🚀 Initial Heroku deployment"
```

### Step 2: Heroku 앱 생성
```bash
# 앱 이름: coocook-jarvis (또는 자신의 이름)
heroku create coocook-jarvis

# 또는 이름 없이 (자동 생성)
heroku create
```

### Step 3: 환경 변수 설정
```bash
# API 키 설정
heroku config:set ANTHROPIC_API_KEY=YOUR_ANTHROPIC_API_KEY...

# Telegram 설정 (선택)
heroku config:set TELEGRAM_BOT_TOKEN=8461725251:AAE...
heroku config:set TELEGRAM_CHAT_ID=7910169750

# 현재 설정 확인
heroku config
```

### Step 4: PostgreSQL 추가 (선택)
```bash
# 무료 PostgreSQL 데이터베이스 추가
heroku addons:create heroku-postgresql:hobby-dev
```

### Step 5: 배포
```bash
# GitHub 연동 (권장)
# 1. GitHub에 리포지토리 생성
# 2. Heroku 대시보드에서 "Connect to GitHub" 선택
# 3. 리포지토리 검색 후 연동
# 4. "Enable Automatic Deploys" 활성화

# 또는 직접 배포
git push heroku main
# 또는
git push heroku master
```

### Step 6: 배포 상태 확인
```bash
# 로그 확인
heroku logs --tail

# 앱 열기
heroku open

# 또는 직접 URL 확인
heroku apps:info coocook-jarvis
```

---

## 🌐 배포 후 접근

### 웹 대시보드
```
https://coocook-jarvis.herokuapp.com/
```

### API 엔드포인트
```
https://coocook-jarvis.herokuapp.com/api/v1/status
https://coocook-jarvis.herokuapp.com/api/v1/teams
https://coocook-jarvis.herokuapp.com/api/v1/missions
```

### 웹 페이지들
```
Operations: https://coocook-jarvis.herokuapp.com/operations.html
Teams: https://coocook-jarvis.herokuapp.com/teams.html
Analytics: https://coocook-jarvis.herokuapp.com/analytics.html
Dashboard: https://coocook-jarvis.herokuapp.com/dashboard.html
```

---

## 🔐 보안 설정

### 1. HTTPS 자동 적용
```bash
# Heroku에서 자동으로 HTTPS 제공
# 추가 설정 필요 없음 ✅
```

### 2. 도메인 커스터마이징 (선택)
```bash
# 커스텀 도메인 추가
heroku domains:add jarvis.coocook.com

# DNS 설정 필요 (도메인 제공자에서)
# Type: CNAME
# Name: jarvis
# Value: coocook-jarvis.herokuapp.com
```

### 3. 환경 변수 보호
```bash
# .env 파일은 절대 Git에 커밋하지 말 것
echo ".env" >> .gitignore

# Heroku 대시보드에서만 환경 변수 관리
```

---

## 📊 모니터링

### Heroku 대시보드
```
https://dashboard.heroku.com/apps/coocook-jarvis
```

### 실시간 로그 보기
```bash
heroku logs --tail
```

### 성능 메트릭
```bash
heroku ps
heroku status
```

### 데이터베이스 상태
```bash
heroku pg:info
```

---

## 🔄 업데이트 배포

### GitHub 연동 시 (자동)
```bash
# 로컬에서 변경 후
git add .
git commit -m "업데이트: 새 기능 추가"
git push origin main

# Heroku가 자동으로 감지하고 배포 ✅
```

### 수동 배포
```bash
# 로컬 변경 후
git add .
git commit -m "업데이트"
git push heroku main
```

---

## 💰 비용

| 항목 | 무료 | 유료 |
|------|------|------|
| **Web Dyno** | ✅ (550시간/월) | $7/월 (무제한) |
| **Worker Dyno** | ✅ (550시간/월) | $7/월 (무제한) |
| **PostgreSQL** | ✅ (hobby-dev) | $9/월 (standard) |
| **HTTPS** | ✅ | ✅ |
| **총 비용** | **무료** | **~$16/월** |

### 비용 절감 팁
- 무료 Dyno 사용 (550시간/월 = 약 23일)
- 3개월 이상 사용 시 자동 가동 중지 (무료 기간 종료 후)
- 유료 전환 시 신용카드 필수

---

## ⚙️ 고급 설정

### 스케일링
```bash
# 웹 인스턴스 추가
heroku ps:scale web=2 worker=1

# 현재 상태 확인
heroku ps
```

### 커스텀 빌드팩
```bash
# 이미 Python 빌드팩 설정됨 (app.json에서)
# 추가 필요 없음 ✅
```

### 정기 작업 (Scheduler)
```bash
# Heroku Scheduler 추가
heroku addons:create scheduler:standard

# 작업 설정
heroku addons:open scheduler
```

---

## 🆘 트러블슈팅

### 배포 실패
```bash
# 로그 확인
heroku logs --tail

# 재시작
heroku restart

# 롤백 (이전 버전으로)
heroku releases
heroku rollback v123
```

### 포트 에러
```bash
# Procfile에서 PORT 환경 변수 사용 확인
# ✅ 이미 적용됨 (api_server.py 수정)
```

### 메모리 부족
```bash
# Dyno 업그레이드
heroku ps:type web=standard-2x
```

---

## 📱 Telegram 통합

### Heroku Worker에서 실행
```bash
# Procfile에 이미 설정됨
worker: python scripts/jarvis_v2.py

# 확인
heroku ps
```

### Telegram 알림 테스트
```bash
# Telegram Bot에 메시지 전송
/status

# Heroku 로그 확인
heroku logs --tail
```

---

## ✅ 배포 체크리스트

- [ ] Heroku 계정 생성
- [ ] Heroku CLI 설치
- [ ] `heroku login` 실행
- [ ] `ANTHROPIC_API_KEY` 준비
- [ ] `heroku create coocook-jarvis` 실행
- [ ] 환경 변수 설정 완료
- [ ] `git push heroku main` 배포
- [ ] 로그 확인 (`heroku logs --tail`)
- [ ] 웹 대시보드 접근 테스트 (`heroku open`)
- [ ] API 엔드포인트 테스트
- [ ] Telegram 명령 테스트 (선택)

---

## 🎉 배포 완료!

**축하합니다! JARVIS가 전 세계에 배포되었습니다!**

### 공유 가능한 URL
```
🌍 웹: https://coocook-jarvis.herokuapp.com/
📚 API: https://coocook-jarvis.herokuapp.com/api/v1/status
👥 팀: https://coocook-jarvis.herokuapp.com/teams.html
📊 분석: https://coocook-jarvis.herokuapp.com/analytics.html
```

### 다음 단계
1. 커스텀 도메인 추가 (선택)
2. 모니터링 대시보드 설정
3. 백업 설정
4. CI/CD 파이프라인 개선

---

**기술 지원이 필요하면 저에게 알려주세요!** 🚀
