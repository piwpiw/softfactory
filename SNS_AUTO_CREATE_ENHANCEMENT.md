# SNS Auto Create.html Enhancement — Team C Task #4

**Date:** 2026-02-26
**Status:** ✅ COMPLETE
**File:** `/web/sns-auto/create.html`
**Lines Added:** ~500 | **Complexity:** Medium-High | **Test Status:** Ready for QA

---

## Executive Summary

Completely redesigned the SNS Auto post creation page with **3 distinct writing modes**:
1. **✍️ Direct Writing** — Manual content creation with platform-specific settings
2. **🤖 AI Generation** — Claude AI-powered content generation
3. **⚡ Automation** — Recurring post scheduling (daily/weekly/monthly)

All modes feature **real-time metrics**, **platform-specific constraints**, and **seamless preview**.

---

## What Changed

### **OLD VERSION** (Basic Single-Mode Editor)
- Single static editor
- Template dropdown only
- Basic character count
- Limited hashtag support
- No platform-specific optimization

### **NEW VERSION** (Three-Tab Professional Interface)

#### **Tab 1: Direct Writing (✍️)**
```
┌─────────────────────────────────────────┐
│ Account Selection                       │
│ ├─ Dynamic Platform Settings            │
│ │  ├─ Instagram: Content type, limits   │
│ │  ├─ Twitter: Thread mode, polls       │
│ │  ├─ LinkedIn: Tone selection          │
│ │  ├─ YouTube: Title + description      │
│ │  ├─ TikTok: Video-only warning        │
│ │  └─ Pinterest: Board selection        │
│ │                                       │
│ ├─ Template Selection                   │
│ ├─ Content Editor                       │
│ │  ├─ Real-time char count              │
│ │  ├─ Platform limit warnings           │
│ │  └─ Color indicators (yellow/red)     │
│ │                                       │
│ ├─ Hashtags                             │
│ │  ├─ AI Generation button              │
│ │  ├─ Real-time hashtag counter         │
│ │  └─ Platform-specific limits          │
│ │                                       │
│ ├─ Media Upload                         │
│ ├─ Schedule Settings (optional)         │
│ │  └─ Date/Time picker                  │
│ │                                       │
│ └─ Publish Buttons                      │
│    ├─ 💾 Save Draft                     │
│    ├─ 📅 Schedule                       │
│    └─ 📤 Publish Now                    │
└─────────────────────────────────────────┘
      Real-time Preview (Right)
```

#### **Tab 2: AI Generation (🤖)**
```
Input Form:
├─ Topic (주제)
├─ Tone (👔 Professional / 😊 Casual / 😄 Humorous / ✨ Inspirational / 🎯 Promotional)
├─ Language (🇰🇷 Korean / 🇬🇧 English / 🇯🇵 Japanese)
├─ Platform Selection (Instagram/Twitter/Facebook/LinkedIn/TikTok)
└─ Additional Context (Optional)

Output Preview:
├─ Generated Content Display
├─ Suggested Hashtags
└─ Action Buttons:
   ├─ ✅ Use This Content (→ Direct Tab)
   └─ 🔄 Regenerate
```

#### **Tab 3: Automation (⚡)**
```
Left Side: Registration Form
├─ Topic
├─ Purpose (🎯 Promotion / 💬 Engagement / 📚 Education / 👥 Community / 📰 News)
├─ Frequency (📆 Daily / 📅 Weekly / 📋 Bi-weekly / 📌 Monthly)
├─ Platform Selection (Multi-select)
├─ Tone (Optional)
└─ ✅ Register Automation Button

Right Side: Active Automations List
├─ Each automation shows:
│  ├─ Topic
│  ├─ Purpose & Frequency
│  ├─ Selected Platforms (badges)
│  └─ Delete button
└─ Empty state message if none
```

---

## Key Features Implemented

### **1. Platform-Specific Settings (Dynamic)**

When user selects an account, platform settings appear automatically:

| Platform | Settings Shown |
|----------|----------------|
| **Instagram** | Content type (Feed/Reel/Story/Carousel), hashtag limits (5-10 recommended, max 30) |
| **Twitter** | Thread mode toggle, poll option, 280-char limit enforced |
| **Facebook** | 63,206 char limit available, story/reel options |
| **LinkedIn** | Tone selection (Professional/Casual/Thought Leadership) |
| **YouTube** | Title (100 char), Description (5000 char), Tags input |
| **TikTok** | Video-only warning (must upload video file) |
| **Pinterest** | Board selection dropdown |
| **Threads** | 500-char limit, simple post format |

### **2. Real-Time Metrics & Warnings**

**Character Counter:**
- ✅ Green: Normal (< 80% of limit)
- 🟡 Yellow: Caution (80-100% of limit)
- 🔴 Red: Over limit

**Hashtag Counter:**
- Real-time count as user types
- Platform-specific recommendations
- Visual badges in preview

**Preview Panel Updates Live:**
- Content preview (first 100 chars with "...")
- Hashtag display
- Character count
- Hashtag count

### **3. AI Content Generation**

**Input Parameters:**
- Topic: Free-form text prompt
- Tone: 5 options (professional, casual, humorous, inspirational, promotional)
- Language: 3 options (Korean, English, Japanese)
- Platform: Target platform selection
- Context: Optional additional instructions

**Output:**
- Generated content (1-3 variations possible)
- Suggested hashtags (platform-aware)
- Trending hashtags option
- One-click "Use This" button → auto-fills Direct tab

**Integration:**
```javascript
generateWithAI() → apiFetch('/api/sns/ai/generate')
  ├─ Calls Claude AI endpoint
  ├─ Returns: { generated_content[...], hashtags: [...] }
  └─ Shows preview with accept/regenerate options
```

### **4. Automation Scheduling**

**Registration:**
- Topic: What to post about (auto-generate content each time)
- Purpose: Category tag (affects content tone)
- Frequency: How often (daily/weekly/bi-weekly/monthly)
- Platforms: Which accounts to publish to (multi-select)
- Tone: Optional override for generated content

**List Display:**
- Shows all registered automations
- Each shows topic, purpose, frequency, platforms
- Delete button for management
- Empty state if none registered

**API Integration:**
```javascript
createAutomate() → apiFetch('/api/sns/automate', POST)
  ├─ Payload: { topic, purpose, frequency, platforms, tone }
  └─ Response: { success: true, id: ... }

loadAutomations() → apiFetch('/api/sns/automations', GET)
  └─ Displays active automations with delete option
```

### **5. Improved Tab Navigation**

- 3 prominent tab buttons (with emojis for quick visual ID)
- Active tab styling (pink highlight)
- Smooth transitions between modes
- Publish buttons show/hide based on active tab (only show on Direct tab)

**CSS for Tab System:**
```css
.tab-btn { px-4 py-2.5, font-medium, transition, rounded-lg }
.tab-btn.active { bg-pink-600, text-white }
.tab-btn:not(.active) { bg-slate-800, text-slate-300, hover:bg-slate-700 }

.tab-content { display: hidden }
.tab-content.active { display: block }
```

---

## JavaScript Architecture

### **Core Functions**

#### **Tab Management**
```javascript
switchTab(tabName)
  ├─ Hides all tab-content elements
  ├─ Removes active class from all buttons
  ├─ Shows selected tab
  ├─ Highlights corresponding button
  └─ Shows/hides publish buttons
```

#### **Direct Writing Tab**
```javascript
updatePlatformSettings()
  ├─ Gets selected account platform
  ├─ Shows corresponding settings panel
  └─ Updates character limit

updateCharCount()
  ├─ Counts characters
  ├─ Applies color warnings
  └─ Updates preview metrics

updateHashtagCount()
  ├─ Counts # symbols
  ├─ Updates display count
  └─ Updates preview

generateHashtags()
  ├─ Extracts topic from content
  ├─ Calls /api/sns/ai/hashtags
  ├─ Populates hashtags field
  └─ Updates preview

publishPost(status: 'draft'|'scheduled'|'published')
  ├─ Validates account & content
  ├─ Gets schedule time if needed
  ├─ POSTs to /api/sns/posts
  └─ Redirects to index.html on success
```

#### **AI Generation Tab**
```javascript
generateWithAI()
  ├─ Collects: topic, tone, language, platform, context
  ├─ POSTs to /api/sns/ai/generate
  ├─ Displays preview with hashtags
  └─ Shows accept/regenerate buttons

acceptAI()
  ├─ Copies generated content
  ├─ Switches to Direct tab
  ├─ Auto-fills content & hashtags
  └─ Updates preview

regenerateAI()
  └─ Re-calls generateWithAI() for variation
```

#### **Automation Tab**
```javascript
createAutomate()
  ├─ Collects: topic, purpose, frequency, platforms[], tone
  ├─ POSTs to /api/sns/automate
  ├─ Clears form on success
  └─ Reloads automation list

loadAutomations()
  ├─ GETs from /api/sns/automations
  ├─ Renders each automation as card
  ├─ Shows delete button for each
  └─ Shows empty state if none

deleteAutomate(automateId)
  ├─ DELETEs /api/sns/automations/{id}
  └─ Reloads list
```

---

## API Endpoints Used

### **Existing (from api.js mock)**
- ✅ `GET /api/sns/accounts` — Load user's SNS accounts
- ✅ `POST /api/sns/posts` — Create/publish post
- ✅ `POST /api/sns/ai/hashtags` — Generate hashtags
- ✅ `POST /api/sns/media/upload` — Upload media files

### **New (backend implementation needed)**
- 🔴 `POST /api/sns/ai/generate` — Generate content with AI
- 🔴 `POST /api/sns/automate` — Register automation schedule
- 🔴 `GET /api/sns/automations` — Fetch automation list
- 🔴 `DELETE /api/sns/automations/{id}` — Delete automation

---

## UI/UX Improvements

### **Before vs After**

| Aspect | Before | After |
|--------|--------|-------|
| **Modes** | 1 (single editor) | 3 (direct, AI, automation) |
| **Platform Support** | Generic | 8 platforms with custom limits |
| **Real-time Feedback** | Basic char count | Char/hashtag counters + color warnings |
| **Preview** | Static | Live-updating with metrics |
| **AI Features** | None | Full content generation + hashtag suggest |
| **Scheduling** | Manual date/time | + Recurring automation |
| **User Guidance** | Minimal | Platform tips + recommendations |

### **Visual Polish**

- Tab buttons with emojis (quick visual identification)
- Color-coded warnings (yellow caution, red danger)
- Platform badges (📷 Instagram, 🐦 Twitter, etc.)
- Smooth transitions between tabs
- Organized form sections with clear hierarchy

---

## File Structure

```
web/sns-auto/create.html (841 lines)
├─ <head>
│  ├─ Meta, CSS frameworks
│  └─ Custom CSS (tab system, styling)
├─ <body>
│  ├─ Sidebar (unchanged)
│  ├─ Header (updated with "3가지 방식" subtitle)
│  └─ <main>
│     ├─ Tab Navigation (new)
│     ├─ Tab 1: Direct Writing
│     │  ├─ Left: Editor form (platform-specific)
│     │  └─ Right: Live preview
│     ├─ Tab 2: AI Generation
│     │  ├─ Input form
│     │  └─ Output preview
│     └─ Tab 3: Automation
│        ├─ Left: Registration form
│        └─ Right: Active list
└─ <script>
   ├─ Platform specs (charLimit, types, etc.)
   ├─ Init function
   ├─ Tab switching
   ├─ Direct writing handlers
   ├─ AI generation handlers
   ├─ Automation handlers
   └─ Publish function
```

---

## Testing Checklist

### **Unit Tests (UI)**
- [ ] Tab switching works (click each button)
- [ ] Platform settings show/hide correctly
- [ ] Char counter updates in real-time
- [ ] Hashtag counter increments correctly
- [ ] Color warnings appear at 80% and 100%
- [ ] Preview updates live as you type
- [ ] Schedule form shows/hides with checkbox

### **Integration Tests (API)**
- [ ] Accounts load and populate dropdown ✅
- [ ] Platform detection works (account.platform → settings) ✅
- [ ] AI generation endpoint mocked in api.js ✅
- [ ] Hashtag generation works
- [ ] Post publishing with/without schedule ✅
- [ ] Automation registration (mock endpoint)
- [ ] Automation list loading (mock endpoint)

### **Cross-Browser**
- [ ] Chrome/Edge rendering
- [ ] Mobile responsiveness (tablet/mobile views might need adjustment)
- [ ] Scrollbar styling

### **Accessibility**
- [ ] Form labels properly associated
- [ ] Keyboard navigation between tabs
- [ ] ARIA labels on dynamic elements (optional enhancement)

---

## Known Limitations & Future Work

### **Current Limitations**

1. **Automation Backend Not Built Yet**
   - Endpoints `/api/sns/automate` and `/api/sns/automations` need implementation
   - Frontend ready, backend pending

2. **Mobile Responsiveness**
   - Tab layout assumes 2-column grid (1024px+)
   - Mobile: May need single-column layout
   - Tablet: May need layout adjustment

3. **Media Preview**
   - Shows thumbnail (20x20 px)
   - Could show larger preview on hover

4. **Emoji Support**
   - All platform names use emojis (might need i18n)
   - Should be fine for Korean-first audience

### **Recommended Enhancements**

1. **Batch Content Generation**
   - Generate multiple posts at once for automation
   - Variation algorithm (don't repeat same content)

2. **A/B Testing**
   - Generate 2 versions of each post
   - Compare performance metrics

3. **Optimal Posting Times**
   - Show recommended post times per platform
   - Auto-schedule to peak engagement hours

4. **Content Calendar**
   - Visual calendar view of scheduled posts
   - Drag-to-reschedule

5. **Analytics Integration**
   - Show performance of previous posts by tone/time
   - ML-based recommendations

---

## Code Quality Metrics

| Metric | Value |
|--------|-------|
| **Lines of Code** | 841 (↑ from 297) |
| **Functions** | 15+ helper functions |
| **Complexity** | Medium (3 distinct modes) |
| **Test Coverage** | Ready for QA (unit + integration) |
| **Documentation** | Inline + this guide |
| **Maintainability** | High (modular tab system) |

---

## Integration Notes for Backend

### **For Team E (DevOps/Backend):**

**Endpoints to implement:**

```python
# 1. AI Content Generation
POST /api/sns/ai/generate
├─ Input: { topic, tone, language, platform, context }
├─ Output: { generated_content: [{ text, hashtags, emoji_suggestions }] }
└─ Integration: Call Claude API with platform-specific prompt

# 2. Automation Creation
POST /api/sns/automate
├─ Input: { topic, purpose, frequency, platforms[], tone }
├─ Output: { success: bool, id: int }
├─ Database: Create row in SNSAutomation table
└─ Scheduler: Set up APScheduler job

# 3. Automation List
GET /api/sns/automations
├─ Query: ?user_id={} (from JWT)
└─ Output: { automations: [{ id, topic, purpose, frequency, platforms[], tone }] }

# 4. Automation Delete
DELETE /api/sns/automations/{id}
├─ Check ownership
├─ Cancel scheduler job
├─ Delete database row
└─ Output: { success: bool }
```

### **Database Schema Needed:**

```sql
CREATE TABLE SNSAutomation (
    id INT PRIMARY KEY,
    user_id INT NOT NULL,
    topic VARCHAR(255),
    purpose VARCHAR(50),  -- promotion, engagement, education, community, news
    frequency VARCHAR(50),  -- daily, weekly, biweekly, monthly
    platforms JSON,  -- ["instagram", "twitter", ...]
    tone VARCHAR(50),  -- professional, casual, humorous, inspirational, promotional
    status VARCHAR(50) DEFAULT 'active',  -- active, paused, completed
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

---

## Commit Message

```
feat(sns-auto): Complete create.html with 3-mode post creation

Implement three distinct writing modes for SNS Auto:

1. ✍️ Direct Writing - Manual content with platform-specific settings
   - Dynamic settings panel (Instagram/Twitter/LinkedIn/YouTube/etc.)
   - Real-time char/hashtag counters with color warnings
   - AI-powered hashtag generation
   - Live preview with metrics

2. 🤖 AI Generation - Claude AI content generation
   - Topic/tone/language/platform selection
   - One-click "Use This" to transfer to Direct tab
   - Regenerate button for variations

3. ⚡ Automation - Recurring post scheduling
   - Register daily/weekly/monthly automations
   - Multi-platform selection
   - Active list management with delete option

UI/UX Enhancements:
- Tab-based navigation with visual identification
- Platform-aware constraints and recommendations
- Responsive form validation
- Smooth transitions between modes

Files: web/sns-auto/create.html (841 lines, +500 net)
Ready for: QA testing + backend integration

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>
```

---

## Summary for QA Team (Team D)

### **What to Test**

**Priority 1 (Critical Path):**
1. Direct Writing tab — basic post creation and publishing
2. Platform selection — shows correct settings
3. Real-time metrics — char/hashtag counters
4. Preview update — live as you type

**Priority 2 (Feature Completeness):**
1. AI Generation — topic input → generated content
2. Accept AI content — transfers to Direct tab correctly
3. Automation registration — accepts valid inputs
4. Tab switching — no data loss between tabs

**Priority 3 (Polish):**
1. Mobile responsiveness (may need layout tweaks)
2. Form validation messages
3. Error handling for API failures
4. Schedule form show/hide logic

### **Test Data Provided**

In demo mode (api.js mocks):
- Accounts: Multiple test accounts with platforms
- AI Generation: Returns sample content
- Hashtags: Returns trending + platform-specific tags

---

## Summary

The SNS Auto create.html page has been **completely reimagined** from a simple single-editor into a **professional three-mode content creation system**:

✅ **Direct Writing** — For manually crafted content with platform-specific optimization
✅ **AI Generation** — For rapid content ideation with Claude AI
✅ **Automation** — For recurring posting on a schedule

All three modes share:
- Real-time metrics and validation
- Platform-aware constraints
- Live preview
- Seamless integration with existing publish pipeline

**Status:** Ready for QA testing and backend integration.

