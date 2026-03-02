# AI 비용 전략 & 효율화 분석

> **작성일:** 2026-03-02
> **출처:** 사용자-에이전트 전략 세션 (직접 대화 기반)
> **상태:** ACTIVE — 의사결정 기준 문서
> **중요도:** 🔴 HIGH — 모든 신규 AI 기능 개발 시 반드시 참조

---

## 1. 핵심 진단 (2026-03-02 기준)

### 현재 비용 구조

| 레이어 | 내용 | 현황 |
|--------|------|------|
| **Dev Layer** | Claude Code CLI로 개발하는 비용 | 부분 추적 (수동) |
| **Runtime Layer** | 배포된 플랫폼이 유저 요청으로 쓰는 Claude API | `AIUsageTracker` 구현됨, 미가동 |

### 누적 Dev 비용 (2026-02-25 기준)

| 프로젝트 | 실제 토큰 | 비용 (Haiku 환산) |
|---------|---------|-----------------|
| Governance v3.0 Setup | 45,000 | $0.136 |
| M-001 Infrastructure | 33,000 | $0.099 |
| M-002 CooCook MVP | 44,000 | $0.132 |
| M-002 Payment/Review | 24,000 | $0.072 |
| M-004 JARVIS | 40,000 | $0.120 |
| M-005 Sonolbot v2.0 | 27,000 | $0.081 |
| M-006 체험단 | 26,000 | $0.078 |
| **합계** | **239,000** | **~$0.718** |

> **주의:** 예산 200K 대비 113.5% 초과 (⚠️ OVER BUDGET 기록 있음)

---

## 2. 근본 문제 진단

### 문제 1: 단일 벤더 전면 의존
```
Dev     → Claude Code
Runtime → Claude API (해시태그, 분석, 생성 등)
Agents  → Claude API (오케스트레이터)
Daemon  → Claude API (Sonolbot)

→ 가격 인상·장애 시 대안 없음
→ 계정별 분산 비용 집계 불가
```

### 문제 2: LLM이 필요 없는 곳에 LLM 사용 중

| 기능 | 현재 | LLM 필요? | 판정 |
|------|------|-----------|------|
| 해시태그 생성 | Claude Haiku | ❌ | 키워드 DB + 트렌딩 API로 대체 가능 |
| 최적 게시 시간 | Claude Haiku | ❌ | 통계 룩업 테이블로 대체 가능 |
| 트렌딩 토픽 | Claude Haiku | ❌ | 플랫폼 공식 API (무료) |
| 영양 분석 | Claude Haiku | ⚠️ | USDA API 무료로 대체 가능 |
| 레시피 추천 | Claude Haiku | ⚠️ | Spoonacular API로 대체 가능 |
| SNS 콘텐츠 생성 | Claude Sonnet | ✅ | LLM 필수 — 유지 |
| 경쟁사 분석 | Claude Sonnet | ✅ | LLM 필수 — 유지 |
| 콘텐츠 리퍼포징 | Claude Sonnet | ✅ | LLM 필수 — 유지 |
| 성과 분석 | Claude Sonnet | ✅ | LLM 필수 — 유지 |

**결론: Runtime 호출의 약 40-50%는 LLM 불필요**

### 문제 3: 거버넌스 오버헤드
```
매 세션마다 고정 로드되는 컨텍스트:
CLAUDE.md + .agent/*(5개) + MEMORY.md ≈ 860줄

→ 시스템이 정교할수록 세션 기본 토큰 소모 증가
→ 현재 프로젝트 규모 대비 오버엔지니어링 판정
```

### 문제 4: 다중 계정 통합 집계 없음
```
계정 A → 플랫폼 Runtime API
계정 B → Claude Code 개발
계정 C → 기타

→ 실제 월간 총 비용 파악 불가
```

---

## 3. 모델별 실제 가격표 (2026-03 기준)

| 모델 | Input /1M tokens | Output /1M tokens | 용도 |
|------|-----------------|------------------|------|
| Claude Haiku 4.5 | $0.25 | $1.25 | 단순 작업 기본값 |
| Claude Sonnet 4.6 | $3.00 | $15.00 | 창의·분석 |
| Claude Opus 4.6 | $15.00 | $75.00 | 비상용 (자동 라우팅 금지) |
| **Gemini Flash 2.0** | **$0.075** | **$0.30** | Haiku 대비 3-4배 저렴 |
| GPT-4o-mini | $0.15 | $0.60 | 안정적 JSON 출력 |
| Gemini Pro 1.5 | $1.25 | $5.00 | Sonnet 대비 3배 저렴 |

> **핵심 인사이트:** Dev 세션에서 Haiku → Sonnet 전환 시 **동일 작업에 5배 비용 발생**

---

## 4. 50% 비용 절감 로드맵

### Phase 1: 즉시 적용 — 0 코드 변경 (예상 절감 ~30%)

- [ ] **Claude Code 세션 모델 고정**: 항상 Haiku 사용, Sonnet/Opus 전환 금지
- [ ] **Anthropic Console 계정별 사용량 확인**: 어떤 API 키가 가장 많이 소모하는지 파악
- [ ] **월간 총 비용 수동 집계**: 모든 계정 합산 → `cost-log.md` 업데이트

### Phase 2: 단순 기능 AI 제거 — 2-3시간 (예상 절감 ~20%)

제거 대상 (Claude API → 정적 로직/외부 API):

```python
# 현재: Claude Haiku 호출 (비용 발생)
def analyze_best_posting_time(platform, timezone):
    return self._call_claude(...)

# 개선: 정적 룩업 테이블 (비용 0)
BEST_TIMES = {
    'instagram': {'weekday': ['06:00', '12:00', '19:00']},
    'tiktok':    {'weekday': ['07:00', '15:00', '21:00']},
}
```

| 제거 대상 함수 | 대체 방법 | 파일 위치 |
|-------------|---------|---------|
| `analyze_best_posting_time` | 정적 시간대 테이블 | `backend/services/claude_ai.py` |
| `generate_hashtags` | 카테고리 키워드 사전 + 트렌딩 API | `backend/services/claude_ai.py` |
| `get_trending_topics` | Twitter/TikTok Trends API | `backend/services/claude_ai.py` |
| `analyze_nutrition` | USDA FoodData API (무료) | `backend/services/claude_ai.py` |
| `recommend_recipes` | Spoonacular API (무료 플랜 있음) | `backend/services/claude_ai.py` |

### Phase 3: 모델 다양화 — 1일 (예상 절감 ~15%)

```python
# 현재: 모든 것 Claude
MODELS = {
    'fast':     'claude-haiku-4-5-20251001',
    'balanced': 'claude-sonnet-4-6',
}

# 개선: 용도별 최적 모델
MODELS = {
    'hashtag':    'gemini/gemini-2.0-flash',   # 3-4배 저렴
    'calendar':   'gpt-4o-mini',               # 안정적 JSON
    'content':    'claude-sonnet-4-6',          # 창의 강점 유지
    'analysis':   'claude-sonnet-4-6',          # 분석 강점 유지
    'coding':     'claude-haiku-4-5-20251001',  # 개발 작업
}
```

### Phase 4: 멀티 계정 통합 모니터링 — 반나절 (구조 개선)

**도구: LiteLLM Proxy**

```bash
pip install litellm
litellm --model claude-haiku,gemini-flash,gpt-4o-mini --port 4000
```

```
모든 AI 호출 → LiteLLM Proxy (localhost:4000) → 실제 API
                        ↓
            - 통합 비용 대시보드
            - 계정 자동 로드밸런싱
            - 모델 fallback 자동화
            - GET /metrics → 전체 비용 집계
```

### 합산 절감 예상

| Phase | 조치 | 절감 |
|-------|------|------|
| 1 | Dev Haiku 고정 | ~30% |
| 2 | 단순 기능 AI 제거 | ~20% |
| 3 | Gemini Flash 혼합 | ~15% |
| **합계** | | **~50-65%** |

---

## 5. 신규 기능 개발 시 의사결정 프레임워크

```
새 AI 기능 추가 전 반드시 아래 질문에 답할 것:

Q1. 이 기능이 정말 LLM이 필요한가?
    └─ 규칙/통계/외부 API로 해결 가능? → LLM 쓰지 말 것

Q2. LLM이 필요하다면, 어떤 모델이 최소 요건을 충족하는가?
    └─ 단순 → Gemini Flash
    └─ 창의/분석 → Claude Sonnet
    └─ Opus는 자동 라우팅 금지

Q3. 응답을 캐싱할 수 있는가?
    └─ 캐싱 가능 → TTL 설정 필수
    └─ 항상 새로운 답 필요 → max_tokens 반드시 최소화

Q4. 이 기능의 예상 호출량은?
    └─ 고빈도(일 1000회+) → 반드시 비 LLM 대안 검토
    └─ 저빈도(일 10회 이하) → LLM 허용
```

---

## 6. 현재 구현 적합성 종합 평가

| 관점 | 평가 | 이유 |
|------|------|------|
| Claude Code로 개발 | ✅ 적합 | 복잡한 코드베이스 관리에 적합 |
| Runtime 단순 기능 (해시태그 등) | ❌ 과잉 | LLM 불필요, 즉시 교체 권고 |
| Runtime 창의·분석 기능 | ✅ 적합 | 콘텐츠 생성·분석은 LLM이 맞음 |
| 멀티 에이전트 거버넌스 구조 | ⚠️ 과잉 | 현재 규모 대비 오버엔지니어링 |
| 단일 Claude 벤더 의존 | ❌ 리스크 | 가격 인상·장애 시 대안 없음 |
| 다중 계정 비용 추적 | ❌ 미구현 | 실제 총 비용 파악 불가 |

---

## 7. 즉시 실행 액션 (우선순위 순)

1. **이번 주** — Phase 1: Dev 세션 Haiku 고정 규칙 전 팀 공유
2. **이번 주** — 모든 Anthropic 계정 Console에서 사용량 스크린샷 → `cost-log.md` 업데이트
3. **다음 주** — Phase 2: 5개 함수 AI 제거 (2-3시간 작업)
4. **다음 달** — Phase 3+4: Gemini 혼합 + LiteLLM 도입

---

> **이 문서는 AI 기능 관련 모든 기획·개발·리뷰 시 반드시 참조한다.**
> **업데이트 주기:** 월 1회 또는 신규 모델 출시 시
> **관리자:** 프로젝트 오너 (전략 결정 문서 — 에이전트가 임의 수정 불가)
