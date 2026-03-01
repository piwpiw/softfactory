# 프로젝트 미완성 작업 전수 조사

**Date:** 2026-02-26
**Scan Status:** COMPLETE
**Priority:** Execute 8-Team Parallel

## 📋 미완성 작업 (15개)

### GROUP A: Frontend UI (2-3 tasks)

#### A1. SNS Automation v2.0 - Frontend Pages (5-7시간)
**Status:** 0% (Backend 70% DONE)
**Files:**
- `web/sns-auto/create.html` - 3가지 모드 구현 필요 (직접 작성/AI 생성/자동화)
- `web/sns-auto/link-in-bio.html` - 신규 페이지 (Link-in-Bio 빌더)
- `web/sns-auto/monetize.html` - 신규 페이지 (수익화 대시보드)
- `web/sns-auto/viral.html` - 신규 페이지 (바이럴 콘텐츠)
- `web/sns-auto/competitor.html` - 신규 페이지 (경쟁사 분석)

**Tasks per file:**
1. HTML 마크업 작성
2. API 함수 호출 (api.js)
3. 폼 밸리데이션
4. 실시간 카운터/통계
5. 에러 처리

#### A2. Review Platform - Frontend Pages (3-4시간)
**Status:** 50% (기본 페이지 있음, 고급 기능 부족)
**Files:**
- `web/review/aggregator.html` - 통합 수집 대시보드 개선
- `web/review/applications.html` - 신청 이력 트래킹 개선
- `web/review/auto-apply.html` - 자동신청 규칙 설정 고도화

---

### GROUP B: Backend API Endpoints (4-5 tasks)

#### B1. SNS Automation - 수익화 엔드포인트 (3-4시간)
**Status:** 50% (일부만 구현)
**Location:** `backend/services/sns_auto.py`
**Missing:**
- POST/GET/PUT/DELETE `/api/sns/linkinbio` (Link-in-Bio CRUD)
- GET `/api/sns/linkinbio/stats` (클릭통계)
- POST/GET/PUT/DELETE `/api/sns/automate` (자동화 작업)
- GET `/api/sns/trending` (트렌딩 데이터)
- POST/GET `/api/sns/competitor` (경쟁사 분석)
- POST `/api/sns/ai/repurpose` (콘텐츠 재활용)
- GET `/api/sns/roi` (ROI 계산)

#### B2. Review Platform - 스크래핑 통합 (4-5시간)
**Status:** 30% (기본 구조만 있음)
**Location:** `backend/services/review_scrapers/`
**Missing:**
- revu.net 스크래퍼 (2시간)
- reviewplace.co.kr 스크래퍼 (1시간)
- wible.co.kr 스크래퍼 (1시간)
- seoulouba.co.kr 스크래퍼 (1시간)
- naver 블로그 체험단 스크래퍼 (2시간)

#### B3. Telegram Bot - Scheduler 통합 (1-2시간)
**Status:** 80% (기본 구조 있음, 세부 기능 미완성)
**Location:** `backend/scheduler.py:167`
**TODO:** Get user's Telegram chat ID from SNSSettings

#### B4. CooCook API - Phase 2-3 구현 (6-8시간)
**Status:** 35% IN_PROGRESS
**Location:** `backend/services/coocook.py` (신규 또는 확장)
**Missing:**
- 레시피 검색/필터링 고도화
- 영양정보 계산
- 쇼핑리스트 생성/관리
- 사용자 피드 기능

---

### GROUP C: Database Models (1-2 tasks)

#### C1. SNS Models 확장 (1시간)
**Status:** 80% (기본 모델 있음)
**Models needed:**
- SNSLinkInBio (user_id, slug, title, links, theme, click_count)
- SNSAutomate (user_id, name, topic, platforms, frequency, next_run)
- SNSCompetitor (user_id, platform, username, last_analyzed, data)

#### C2. Review Models 확장 (1시간)
**Status:** 60% (일부 구현됨)
**Models needed (확인 필요):**
- ReviewAccount 확장 (follower_count, category_tags, success_rate)
- ReviewApplication 확장 (review_posted_at, review_url)

---

### GROUP D: Testing & QA (2-3 tasks)

#### D1. SNS v2.0 엔드포인트 테스트 (2시간)
**Status:** 0% (Backend 구현 후)
**Files:** `tests/integration/test_sns_monetize.py` (신규)
**Coverage:** 모든 수익화 엔드포인트

#### D2. Review Scraper 통합 테스트 (2시간)
**Status:** 0% (Scraper 구현 후)
**Files:** `tests/integration/test_review_scrapers.py` (신규)
**Coverage:** 모든 스크래퍼 + aggregator

#### D3. E2E 사용자 여정 확장 (1시간)
**Status:** 50% (기본만 있음)
**Files:** `tests/e2e/test_user_journeys.py` (확장)
**New flows:**
- SNS 수익화 플로우
- Review 자동신청 플로우
- CooCook 쇼핑리스트 플로우

---

### GROUP E: Documentation & DevOps (1-2 tasks)

#### E1. API 문서화 완성 (2시간)
**Status:** 70% (기본 문서만 있음)
**Missing:**
- SNS v2.0 엔드포인트 상세 문서
- Review 스크래퍼 API 문서
- OAuth 플로우 상세 가이드

#### E2. 배포 자동화 개선 (1-2시간)
**Status:** 80% (기본 스크립트 있음)
**Missing:**
- CI/CD 파이프라인 최적화
- 자동 테스트 트리거
- 배포 후 헬스 체크 개선

---

## 🎯 병렬 실행 전략 (8팀)

### Team Assignment (추천)

| Team | Agent Type | Tasks | Est. Time |
|------|-----------|-------|-----------|
| **Team 1** | Frontend Dev | A1 (create.html) | 3h |
| **Team 2** | Frontend Dev | A1 (나머지 페이지) | 4h |
| **Team 3** | Backend Dev | B1 (SNS 엔드포인트) | 4h |
| **Team 4** | Backend Dev | B2 (Review 스크래퍼) | 5h |
| **Team 5** | Backend Dev | B3 + B4 (Telegram + CooCook) | 3h |
| **Team 6** | Data Engineer | C1 + C2 (Models) | 2h |
| **Team 7** | QA Engineer | D1 + D2 + D3 (Tests) | 5h |
| **Team 8** | DevOps/Doc | E1 + E2 (Docs + Deployment) | 3h |

**Total Parallel Time:** ~5시간 (순차 개발 시 22시간 vs 병렬 5시간)

---

## 📊 의존성 그래프

```
Frontend (A1, A2)
    ↓
API Endpoints (B1, B2, B3, B4)
    ↓
Database Models (C1, C2)
    ↓
Testing (D1, D2, D3)
    ↓
Documentation (E1, E2)
```

**병렬 가능:** A1 / A2 (독립적)
**병렬 가능:** B1 / B2 / B3 / B4 (독립적)
**병렬 가능:** C1 / C2 (독립적, B와 동시 가능)
**직렬 필수:** D는 B, C 완료 후

---

## 🔥 실행 순서

### Phase 1 (동시 시작, ~3시간)
- Team 1: A1 Frontend
- Team 3: B1 SNS API
- Team 4: B2 Review Scraper
- Team 6: C Models

### Phase 2 (Phase 1 + 2시간, 동시 진행)
- Team 2: A2 더 많은 Frontend
- Team 5: B3 + B4 추가 API
- Team 7: D1 + D2 테스트 설계 (B 진행 중 병렬)

### Phase 3 (Phase 2 + 3시간, 동시)
- Team 7: D1 + D2 + D3 테스트 실행
- Team 8: E1 + E2 문서화 + 배포

---

## ✅ 완료 기준

- [ ] 모든 HTML 페이지 100% 완성
- [ ] 모든 API 엔드포인트 구현 및 테스트
- [ ] 모든 데이터베이스 모델 마이그레이션
- [ ] 테스트 커버리지 80%+ 유지
- [ ] API 문서 완성
- [ ] 배포 자동화 개선
- [ ] 최종 통합 테스트 PASS

**Estimated Total Duration:** 4-6시간 (모든 팀 병렬 실행 기준)
