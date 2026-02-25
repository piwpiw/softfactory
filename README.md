# 🏭 SoftFactory — Multi-Agent B2B SaaS Platform

> **Production-Ready** | Multi-Agent System v2.1 | Claude Code Sub-Agent Framework

[![Python](https://img.shields.io/badge/Python-3.11-blue)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0-green)](https://flask.palletsprojects.com)
[![Status](https://img.shields.io/badge/Status-Production-brightgreen)](http://localhost:8000)

---

## 🚀 Quick Start

```bash
# 1. 의존성 설치
pip install -r requirements.txt

# 2. 서버 시작
python start_platform.py

# 3. 브라우저에서 열기
# http://localhost:8000/web/platform/login.html
# 패스키: demo2026
```

---

## 📦 What's Inside

### 5개 핵심 서비스

| 서비스 | 설명 | 가격 |
|--------|------|------|
| 📱 **SNS Auto** | 소셜 미디어 자동화 + AI 콘텐츠 | ₩49,000~₩199,000/월 |
| ⭐ **Review Campaign** | 브랜드 체험단 캠페인 관리 | ₩99,000~₩299,000/월 |
| 🍳 **CooCook** | 셰프 마켓플레이스 & 예약 | ₩39,000~₩299,000/월 |
| 🤖 **AI Automation** | 24/7 AI 직원 생성 & 배포 | ₩89,000~₩490,000/월 |
| 💻 **WebApp Builder** | 8주 부트캠프 | ₩590,000 (1회) |

### 플랫폼 규모
- **75개** HTML 페이지 (프론트엔드)
- **16개** API 엔드포인트 (100% 테스트 통과)
- **12개** SQLAlchemy 데이터 모델
- **10개** Python 에이전트
- **10개** 스킬 모듈

---

## 🤖 Multi-Agent Architecture

```
User Input → Orchestrator
              ├─ Agent A: Business Strategist  (PRD, OKR, RICE)
              ├─ Agent B: Architect            (C4, Clean Arch, OpenAPI)
              ├─ Agent C: Dev Lead             (TDD, Code Standards)
              ├─ Agent D: QA Engineer          (Test Pyramid, Coverage)
              └─ Agent E: DevOps               (IaC, CI/CD, SLO)
                         + Security Auditor    (OWASP Top 10)
                         + Performance Analyzer (Token Budget)
```

**서브에이전트 프롬프트:** `.claude/agents/` (8개 파일)
**MCP 서버:** `.mcp.json` (10개: filesystem, memory, sqlite, github, puppeteer...)

---

## 🗂️ Project Structure

```
D:/Project/
├── .claude/agents/        ← Claude Code 서브에이전트 (8개)
├── .mcp.json              ← MCP 서버 10개
├── .clauderules           ← 14개 에이전트 규칙
├── CLAUDE.md              ← 마스터 지침서 v2.1
│
├── backend/               ← Flask API
│   ├── app.py             ← 진입점
│   ├── models.py          ← 12개 모델
│   └── services/          ← 5개 서비스
│
├── agents/                ← Python 에이전트 (10개)
├── core/                  ← 공통 인프라 (9개 모듈)
├── skills/                ← 스킬 라이브러리 (10개)
│
├── web/                   ← 프론트엔드 (75개 HTML)
│   ├── platform/          ← 32개 플랫폼 페이지
│   ├── sns-auto/          ← 7개 페이지
│   ├── review/            ← 6개 페이지
│   ├── coocook/           ← 6개 페이지
│   ├── ai-automation/     ← 7개 페이지
│   └── webapp-builder/    ← 7개 페이지
│
├── tests/                 ← 테스트 스위트 (unit/integration/e2e)
├── daemon/                ← Sonolbot Telegram Bot
├── docs/                  ← 문서 40+
│
├── docker-compose.yml     ← 전체 스택 (api+db+redis+nginx)
├── Makefile               ← 표준 명령어
└── pytest.ini             ← 테스트 설정
```

---

## ⚙️ Commands

```bash
make help          # 전체 명령어 목록
make run           # 로컬 서버 시작
make test          # 전체 테스트
make test-unit     # 단위 테스트
make coverage      # 커버리지 리포트 (목표 ≥80%)
make lint          # 코드 품질 체크
make docker-up     # Docker 전체 스택
make agents        # 서브에이전트 목록
make clean         # 캐시 정리
```

---

## 🧪 Testing

```bash
pytest tests/                           # 전체
pytest tests/unit/                      # 단위
pytest tests/integration/              # API 통합
pytest tests/e2e/                       # E2E (서버 필요)
pytest tests/ --cov=backend --cov-report=term-missing
```

---

## 🔧 MCP Servers (10개)

| 서버 | 용도 |
|------|------|
| `filesystem` | 프로젝트 파일 전체 R/W |
| `sequential-thinking` | 구조화 추론 |
| `memory` | 크로스-세션 메모리 |
| `sqlite` | platform.db 직접 쿼리 |
| `github` | PR/이슈/코드 관리 |
| `brave-search` | 시장 조사 검색 |
| `puppeteer` | E2E 브라우저 자동화 |
| `fetch` | HTTP/API 테스트 |
| `postgres` | 프로덕션 DB |

---

## 🔐 Environment Variables

```bash
cp .env.example .env  # 필수 값 채우기
```

| 변수 | 용도 |
|------|------|
| `ANTHROPIC_API_KEY` | Claude API |
| `TELEGRAM_BOT_TOKEN` | Sonolbot |
| `JWT_SECRET` | 인증 토큰 |
| `DATABASE_URL` | DB 연결 |
| `STRIPE_SECRET_KEY` | 결제 (선택) |

---

## 🚢 Deployment

```bash
make docker-up   # Docker (권장)
railway up       # Railway 클라우드
make run         # 로컬 개발
```

---

## 📊 Current Status

| 항목 | 상태 |
|------|------|
| API Endpoints | ✅ 16/16 PASSING |
| Frontend Pages | ✅ 75/75 HTTP 200 |
| Demo Mode | ✅ passkey: `demo2026` |
| CI/CD | ✅ GitHub Actions → Railway |
| Docker | ✅ docker-compose.yml |
| Tests | ✅ unit / integration / e2e |

---

**Built with [Claude Code](https://claude.ai/code) Multi-Agent System v2.1**
