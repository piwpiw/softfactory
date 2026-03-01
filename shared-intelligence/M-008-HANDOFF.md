# M-008 Handoff: Telegram Bot Scheduler + CooCook API Enhancement
> **Prepared for:** Development Team | **Status:** READY TO IMPLEMENT
> **Date:** 2026-02-26 | **Estimated Duration:** 4 hours | **Budget:** 37K tokens

---

## What You're Getting

Three comprehensive planning documents to implement two major features:

### Documents Provided

1. **M-008-QUICK-START.md** — Start here. 5-min overview of requirements, API endpoints, and success criteria.

2. **M-008-TELEGRAM-COOCOOK-IMPLEMENTATION-PLAN.md** — Full technical specification with:
   - Complete code examples for every component
   - Task-by-task breakdown with time estimates
   - Database schema changes
   - API endpoint specifications
   - Test cases
   - Risk mitigation strategies

3. **M-008-ARCHITECTURE.md** — System design with:
   - Data flow diagrams (sequence diagrams, UML)
   - Database schema with relationships
   - Caching strategy
   - Error handling & validation
   - Monitoring & logging strategy

---

## Executive Summary

### PART A: Telegram Bot Scheduler Integration (1 hour)

**Problem:** SNS posts publish, but users don't get notified.

**Solution:** Integrate Telegram notifications into existing scheduler.

**What Changes:**
```
SNSSettings table:
  ADD: telegram_chat_id, telegram_enabled, timezone,
       notification_on_pending/complete/error

scheduler.py:
  REPLACE: send_telegram_notification() stub with real implementation
  ADD: notify_pending_jobs() background job (30-min interval)

New service:
  CREATE: backend/services/sns_notification.py
  - Format Telegram messages (HTML tags)
  - Handle timezone conversion
  - Integrate with daemon/telegram_notifier.py

New API endpoints:
  POST /api/sns-settings/telegram — Configure settings
  POST /api/sns-settings/telegram/test — Verify Telegram works
```

**How It Works:**
1. User schedules SNS post
2. Scheduler publishes post (60-sec job)
3. SNSNotificationService formats message
4. Telegram bot sends message to user's chat
5. User gets notification on phone ✓

**Testing:** 5 unit + integration tests
**No Breaking Changes:** Fully backward compatible

---

### PART B: CooCook API Enhancement (3 hours)

**Current State:** Chef listing + booking only (35% complete)

**What We're Adding:**
- Recipe management system (search, filter, sort)
- Nutrition calculator (macros, allergen detection)
- Shopping list management (add recipes, consolidate, export PDF/CSV)
- Social feed (following, sharing, trending recipes)

**New Models (7):**
```
Recipe (12 fields)
RecipeIngredient (8 fields)
RecipeReview (6 fields)
ShoppingList (6 fields)
UserFavorite (3 fields)
RecipeShare (9 fields)
UserFollowing (3 fields)
```

**New Services:**
```
NutritionCalculator (150 lines)
  - Calculate macros per serving
  - Detect allergens
  - 95%+ accuracy
```

**New API Endpoints (20):**
```
PART B1 (Recipes):
  GET    /api/coocook/recipes — Advanced search
  GET    /api/coocook/recipes/{id} — Recipe details
  POST   /api/coocook/recipes/{id}/reviews — Add review
  GET    /api/coocook/recipes/trending — Trending recipes

PART B2 (Shopping):
  GET    /api/coocook/shopping-lists — List user's lists
  POST   /api/coocook/shopping-lists — Create list
  POST   /api/coocook/shopping-lists/{id}/add-recipe — Add items
  GET    /api/coocook/shopping-lists/{id}/export?format=pdf|csv — Export

PART B2 (Social):
  POST   /api/coocook/recipes/{id}/share — Share recipe
  POST   /api/coocook/recipes/{id}/favorite — Add favorite
  POST   /api/coocook/users/{id}/follow — Follow user
  GET    /api/coocook/feed — Get personalized feed
  GET    /api/coocook/favorites — Get user's favorites
```

**Caching Strategy:**
- Recipe search: 15-min TTL (Redis)
- Feed generation: 5-min TTL (Redis)
- Nutrition calculations: In-memory (computed on-demand)

**Performance Targets:**
- Recipe search: < 1 second (with caching)
- Feed loading: < 500ms
- Nutrition calculation: < 100ms
- Shopping export (PDF): < 2 seconds

---

## Implementation Map

### PART A: Tasks (1 hour)

1. **T1:** Extend SNSSettings model (10 min)
   - 4 new columns: telegram_chat_id, telegram_enabled, timezone, notifications
   - SQLite/PostgreSQL migration

2. **T2:** Create SNSNotificationService (20 min)
   - Format messages with HTML tags
   - Handle timezone conversion
   - Integrate with Telegram API

3. **T3:** Update scheduler.py (15 min)
   - Replace send_telegram_notification() stub
   - Add notify_pending_jobs() (30-min interval job)
   - Add telemetry logging

4. **T4:** Create Telegram Settings API (10 min)
   - GET /api/sns-settings/telegram
   - POST /api/sns-settings/telegram
   - POST /api/sns-settings/telegram/test

5. **T5:** Tests & Validation (10 min)
   - Unit tests (notification formatting)
   - Integration tests (API endpoints)
   - Manual testing with Telegram bot

### PART B1: Tasks (1.5 hours)

1. **T1:** Create Recipe Models (15 min)
   - Recipe (12 fields)
   - RecipeIngredient (8 fields)
   - RecipeReview (6 fields)
   - Add indexes on title, category, difficulty, rating

2. **T2:** Implement NutritionCalculator (20 min)
   - Unit conversion logic (cup → grams)
   - Ingredient nutrient database
   - Per-serving calculations
   - Allergen detection

3. **T3:** Build Recipe Search API (25 min)
   - GET /api/coocook/recipes (advanced search)
   - Filters: keyword, ingredients, difficulty, time, category, rating
   - Sorting: popularity, rating, time, newest
   - Caching (15-min TTL)
   - Pagination

4. **T4:** Tests & Benchmarking (10 min)
   - Nutrition accuracy tests
   - Search performance tests
   - Cache validation

### PART B2: Tasks (1.5 hours)

1. **T1:** Create Shopping List Models (10 min)
   - ShoppingList (6 fields)
   - UserFavorite (3 fields)
   - Add consolidation logic (merge duplicates)

2. **T2:** Implement Shopping List Service (25 min)
   - CRUD operations
   - Add recipes to list
   - Auto-consolidation
   - Export (PDF, CSV)
   - Share with groups

3. **T3:** Build Social Features (20 min)
   - RecipeShare, UserFollowing models
   - Share recipes (public/private/group)
   - Follow users
   - Personalized feed
   - Trending recipes

4. **T4:** Tests & Integration (10 min)
   - Shopping list consolidation tests
   - Feed generation tests
   - Export format tests

---

## File Changes Summary

### Create (New Files)
```
backend/services/sns_notification.py        — 150 lines
backend/services/nutrition_calculator.py    — 100 lines
tests/integration/test_sns_notifications.py  — 80 lines
tests/integration/test_coocook_recipes.py    — 100 lines
```

### Modify (Existing Files)
```
backend/models.py                           — Add 7 new models, extend SNSSettings
backend/scheduler.py                        — Replace stub, add new job
backend/services/coocook.py                 — Extend from 50 to 400+ lines
backend/app.py                              — Register SNSNotificationService
```

### No Deletions

All changes are additive (no breaking changes to existing code).

---

## Dependencies & Prerequisites

### Python Packages (Already Installed)
```
Flask, SQLAlchemy, APScheduler — for scheduling
redis — for caching
requests — for Telegram API
reportlab or weasyprint — for PDF export (if not installed: pip install reportlab)
```

### External Services
```
Redis — localhost:6379 (for recipe search caching)
Telegram Bot API — bot token: 8461725251 (already configured)
SQLite/PostgreSQL — existing database
```

### Code You Already Have
```
daemon/telegram_notifier.py — existing Telegram bot integration
backend/auth.py — @require_auth decorator
backend/models.py — User, SNSPost, SNSAccount models
backend/scheduler.py — existing APScheduler setup
```

---

## Success Criteria Checklist

### PART A: Telegram Notifications
- [ ] SNSSettings has telegram_chat_id, telegram_enabled fields
- [ ] SNSNotificationService created and tested
- [ ] Notifications sent on job completion (with preview)
- [ ] Notifications sent on job failure (with retry count)
- [ ] 30-min pending job summary working
- [ ] Test endpoint verified (/api/sns-settings/telegram/test)
- [ ] All tests passing (unit + integration)
- [ ] No breaking changes to existing code
- [ ] Backward compatible (old code still works)

### PART B1: Recipe System
- [ ] Recipe, RecipeIngredient, RecipeReview models created
- [ ] Recipe search API with filters working
- [ ] Nutrition calculator with 95%+ accuracy
- [ ] Caching layer (Redis) in place
- [ ] Pagination working (20 items per page)
- [ ] Tests passing (nutrition, search, cache)
- [ ] Performance targets met (search < 1s)

### PART B2: Shopping & Social
- [ ] ShoppingList model with consolidation logic
- [ ] Add/remove recipes from shopping list
- [ ] Export to PDF and CSV formats
- [ ] Social features (following, sharing, feed)
- [ ] Trending recipes algorithm
- [ ] User favorites & history
- [ ] Tests passing (consolidation, export, feed)
- [ ] All 20+ new endpoints working

### Overall
- [ ] Total code: ~1,500 lines (models + services + tests)
- [ ] Token usage: ~37K / 200K budget
- [ ] All tests passing (30+ test cases)
- [ ] No security vulnerabilities
- [ ] Error handling & logging complete
- [ ] Production-ready code quality

---

## Timeline & Estimates

| Phase | Duration | Tasks | Status |
|-------|----------|-------|--------|
| A: Telegram | 1 hour | 5 tasks | 🔄 Ready to start |
| B1: Recipes | 1.5 hours | 4 tasks | 🔄 Ready to start |
| B2: Shopping | 1.5 hours | 4 tasks | 🔄 Ready to start |
| **Total** | **4 hours** | **13 tasks** | **Ready** |

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|-----------|
| Telegram API rate limits | Medium | Notifications dropped | Queue + exponential backoff |
| Nutrition DB incomplete | Medium | Inaccurate values | Start with 50 common ingredients |
| Search performance slow | Low | User experience | Redis caching (indexed queries) |
| Model migration issues | Low | Data loss | Test migrations in dev first |
| Token budget overflow | Low | Work incomplete | Stop at 80% (160K), cut features |

---

## Recommended Execution Order

1. **Start with PART A** (simpler, 1 hour)
   - Gets Telegram notifications working
   - Foundation for further development
   - Clear success metrics

2. **Then PART B1** (recipes, 1.5 hours)
   - Core feature for CooCook
   - Search is critical
   - Nutrition calculator can be iteratively improved

3. **Finally PART B2** (social, 1.5 hours)
   - Builds on recipes
   - Most complex feature (but well-documented)
   - Can be extended later (comments, ratings, etc.)

**Total: 4 hours end-to-end**

---

## Testing Strategy

### Unit Tests (No DB)
```python
test_nutrition_calculator()          — 95% accuracy
test_recipe_consolidation()          — Merge duplicates
test_telegram_message_formatting()   — HTML escaping
test_timezone_conversion()           — User TZ handling
```

### Integration Tests (Real DB)
```python
test_recipe_search_with_filters()    — Full query
test_recipe_search_caching()         — Cache hit/miss
test_shopping_list_export()          — PDF/CSV generation
test_feed_generation()               — Following + trending
test_sns_notification_api()          — Full flow
```

### Manual Testing
```
1. Configure Telegram chat ID in API
2. Create SNS post, schedule for 5 min
3. Verify notification arrives on Telegram ✓
4. Search for recipe, verify results < 1s ✓
5. Add recipe to shopping list, verify consolidation ✓
6. Export shopping list as PDF, verify formatting ✓
7. Follow user, verify feed appears ✓
```

---

## Monitoring After Deployment

### Metrics to Track
```
Telegram notifications:
  - Delivery rate (% successfully sent)
  - Average delivery latency
  - Failed notifications (with error)

Recipe service:
  - Search query count (popularity)
  - Cache hit rate (should be > 80%)
  - Query latency (should be < 1s)
  - Nutrition calculation errors

Shopping lists:
  - Lists created per day
  - Average items per list
  - Export usage (PDF vs CSV)
  - Consolidation rate (% with duplicates)

Social features:
  - Users following others
  - Recipe shares per day
  - Feed engagement rate
```

### Logging Setup
```
backend/services/sns_notification.py:
  logger = logging.getLogger('sns.notifications')
  logger.info('[TELEGRAM] To chat {chat_id}: ...')

backend/services/nutrition_calculator.py:
  logger = logging.getLogger('coocook.nutrition')
  logger.info('[NUTRITION] Calculated {calories} cal/serving in {time}ms')

backend/services/coocook.py:
  logger = logging.getLogger('coocook.api')
  logger.info('[RECIPE-SEARCH] Query: ...')
  logger.info('[FEED-CACHE-HIT] User {user_id}')
```

---

## Known Limitations & Future Work

### Current Implementation
- Recipe nutrition DB: 50 common ingredients (can be expanded)
- Telegram notifications: User-configured only (no system defaults)
- Shopping list: Basic consolidation (no price comparison yet)
- Feed: Pagination (no infinite scroll yet)

### Future Enhancements (Not in Scope)
- Advanced nutrition: Allergen warnings, dietary restrictions
- Smart shopping: Price comparison, store locator
- AI-powered feed: Recommendation algorithm
- Community features: Comments, likes, ratings
- Mobile app integration: Deep links, push notifications

---

## Questions & Support

If implementation team has questions:

1. **Check PART A or B sections** of the implementation plan
2. **Review architecture diagrams** for data flow clarity
3. **Look at code examples** in the plan (copy-paste ready)
4. **Reference test cases** for expected behavior
5. **Check existing code** in `/backend/services/coocook.py` (pattern examples)

**Key Contact Points:**
- SNSSettings model: See `backend/models.py:484`
- Existing Telegram bot: See `daemon/telegram_notifier.py`
- Existing scheduler: See `backend/scheduler.py:1-50`
- Existing CooCook API: See `backend/services/coocook.py`

---

## Commit Strategy

Recommended commit sequence:

```bash
# PART A
git commit -m "feat(telegram): Extend SNSSettings model with Telegram fields"
git commit -m "feat(telegram): Add SNSNotificationService for Telegram alerts"
git commit -m "feat(telegram): Update scheduler with notification triggers"
git commit -m "feat(telegram): Add Telegram settings API endpoints"
git commit -m "test(telegram): Add notification tests and validation"

# PART B1
git commit -m "feat(coocook): Add Recipe and RecipeIngredient models"
git commit -m "feat(coocook): Add NutritionCalculator service"
git commit -m "feat(coocook): Add advanced recipe search API with caching"
git commit -m "test(coocook): Add recipe search and nutrition tests"

# PART B2
git commit -m "feat(coocook): Add ShoppingList and social models"
git commit -m "feat(coocook): Add shopping list service with consolidation"
git commit -m "feat(coocook): Add social feed and sharing features"
git commit -m "test(coocook): Add shopping and social feature tests"

# Final
git commit -m "docs: Update API documentation with new endpoints"
git commit -m "docs: Add CooCook API integration guide"
```

---

## Project Completion

**When all tasks done:**

1. ✅ Push to feature branch
2. ✅ Run full test suite
3. ✅ Create pull request with this handoff as description
4. ✅ Request code review
5. ✅ Merge to main branch
6. ✅ Deploy to production
7. ✅ Monitor metrics for 24 hours
8. ✅ Update cost-log with final token count

---

## Files Reference

**Read First:**
- `M-008-QUICK-START.md` — 5-min overview

**Detailed Implementation:**
- `M-008-TELEGRAM-COOCOOK-IMPLEMENTATION-PLAN.md` — Full spec with code

**Architecture & Design:**
- `M-008-ARCHITECTURE.md` — Data flows, diagrams, schemas

**This File:**
- `M-008-HANDOFF.md` — You are here (executive summary)

---

## Ready to Begin?

1. ✅ Read `M-008-QUICK-START.md`
2. ✅ Review `M-008-TELEGRAM-COOCOOK-IMPLEMENTATION-PLAN.md` for your task
3. ✅ Reference `M-008-ARCHITECTURE.md` for design questions
4. ✅ Start Task #22: Telegram Bot Scheduler Integration
5. ✅ Follow checklist in QUICK-START
6. ✅ Update task status as you progress
7. ✅ Update `shared-intelligence/cost-log.md` with token usage

---

**Status:** ✅ READY FOR IMPLEMENTATION
**Token Budget:** 37K / 200K (18.5%)
**Expected Duration:** 4 hours
**Difficulty Level:** MEDIUM (documented, clear requirements)

Good luck! 🚀

---

**Prepared by:** Claude Code v2.1.55 | **Governance:** CLAUDE.md v3.0 | **Date:** 2026-02-26
