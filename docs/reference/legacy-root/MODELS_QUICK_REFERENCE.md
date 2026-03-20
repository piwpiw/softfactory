# 📘 Database Models — Quick Reference Guide

> **Purpose**: | Model | Purpose | Fields | Indexes | Status |
> **Status**: 🟢 ACTIVE (관리 중)
> **Impact**: [Engineering / Operations]

---

## ⚡ Executive Summary (핵심 요약)
- **주요 내용**: 본 문서는 Database Models — Quick Reference Guide 관련 핵심 명세 및 관리 포인트를 포함합니다.
- **상태**: 현재 최신화 완료 및 검토 됨.
- **연관 문서**: [Master Index](./NOTION_MASTER_INDEX.md)

---

## 🎯 At a Glance

| Model | Purpose | Fields | Indexes | Status |
|-------|---------|--------|---------|--------|
| SNSLinkInBio | Link landing page | 9 | 2 | ✅ Ready |
| SNSAutomate | Auto-posting rules | 11 | 3 | ✅ Ready |
| SNSCompetitor | Competitor tracking | 12 | 3 | ✅ Ready |
| ReviewAccount | Review accounts | 12 | — | ✅ Ready |
| ReviewApplication | Review submissions | 9 | 4 | ✅ Ready |

---

## 📍 File Locations

```
/d/Project/
├── backend/
│   ├── models.py                    ← All 5 models here
│   ├── migration_helpers.py         ← Schema verification
│   ├── test_models_complete.py      ← 14 tests (100% pass)
│   ├── DATABASE_MODELS_COMPLETE.md  ← Detailed specs
│   └── services/
│       ├── sns_auto.py              ← SNS API routes
│       └── review.py                ← Review API routes
├── SNS_REVIEW_MODELS_DELIVERABLE.md ← Full delivery docs
└── MISSION_COMPLETE_DATABASE_MODELS.md ← Completion summary
```

---

## 🔍 Model Specifications

### SNSLinkInBio
```python
db.Column('id', Integer, primary_key=True)
db.Column('user_id', Integer, ForeignKey('users.id'), nullable=False)
db.Column('slug', String(100), unique=True, nullable=False)  # URL slug
db.Column('title', String(255))
db.Column('links', JSON, default=[])  # [{url, label, icon}]
db.Column('theme', String(50), default='light')
db.Column('click_count', Integer, default=0)
db.Column('created_at', DateTime, default=utcnow)
db.Column('updated_at', DateTime, default=utcnow, onupdate=utcnow)
```

### SNSAutomate
```python
db.Column('id', Integer, primary_key=True)
db.Column('user_id', Integer, ForeignKey('users.id'), nullable=False)
db.Column('name', String(255), nullable=False)
db.Column('topic', String(500))
db.Column('purpose', String(500))  # '홍보', '판매', '커뮤니티'
db.Column('platforms', JSON, default=[])  # List of platforms
db.Column('frequency', String(50), default='daily')
db.Column('next_run', DateTime)  # For scheduler
db.Column('is_active', Boolean, default=True)
db.Column('created_at', DateTime, default=utcnow)
db.Column('updated_at', DateTime, default=utcnow, onupdate=utcnow)
```

### SNSCompetitor
```python
db.Column('id', Integer, primary_key=True)
db.Column('user_id', Integer, ForeignKey('users.id'), nullable=False)
db.Column('platform', String(50), nullable=False)
db.Column('username', String(255), nullable=False)
db.Column('followers_count', Integer, default=0)
db.Column('engagement_rate', Float, default=0.0)
db.Column('avg_likes', Integer, default=0)
db.Column('avg_comments', Integer, default=0)
db.Column('posting_frequency', String(50))
db.Column('data', JSON, default={})  # Custom analytics
db.Column('last_analyzed', DateTime, default=utcnow, onupdate=utcnow)
db.Column('created_at', DateTime, default=utcnow)
```

### ReviewAccount (Extended)
```python
db.Column('id', Integer, primary_key=True)
db.Column('user_id', Integer, ForeignKey('users.id'), nullable=False)
db.Column('platform', String(50), nullable=False)
db.Column('account_name', String(255), nullable=False)
db.Column('credentials_enc', String(1000))
db.Column('follower_count', Integer, default=0)
db.Column('category_tags', JSON, default=[])
db.Column('success_rate', Float, default=0.0)
db.Column('last_reviewed', DateTime, nullable=True)  # ← NEW (2026-02-26)
db.Column('is_active', Boolean, default=True)
db.Column('created_at', DateTime, default=utcnow)
db.Column('updated_at', DateTime, default=utcnow, onupdate=utcnow)
```

### ReviewApplication (Extended)
```python
db.Column('id', Integer, primary_key=True)
db.Column('listing_id', Integer, ForeignKey('review_listings.id'), nullable=False)
db.Column('account_id', Integer, ForeignKey('review_accounts.id'), nullable=False)
db.Column('applied_at', DateTime, default=utcnow)
db.Column('status', String(50), default='pending')
db.Column('result', String(500))
db.Column('review_url', String(500))
db.Column('review_posted_at', DateTime)
db.Column('review_content', Text)  # ← NEW (2026-02-26)
```

---

## 🚀 Usage Examples

### Create SNSLinkInBio
```python
from backend.models import SNSLinkInBio, db

bio = SNSLinkInBio(
    user_id=1,
    slug='my-links',
    title='My Links',
    links=[
        {'url': 'https://example.com', 'label': 'Website', 'icon': 'globe'}
    ],
    theme='dark'
)
db.session.add(bio)
db.session.commit()

# Serialize for API
print(bio.to_dict())
```

### Create SNSAutomate
```python
from backend.models import SNSAutomate, db
from datetime import datetime, timedelta

rule = SNSAutomate(
    user_id=1,
    name='Daily AI News',
    topic='Artificial Intelligence',
    purpose='홍보',
    platforms=['instagram', 'twitter'],
    frequency='daily',
    next_run=datetime.utcnow() + timedelta(hours=1),
    is_active=True
)
db.session.add(rule)
db.session.commit()
```

### Query SNSCompetitor
```python
from backend.models import SNSCompetitor

# Get all competitors for a user
competitors = SNSCompetitor.query.filter_by(user_id=1).all()

# Get Instagram competitors
ig_competitors = SNSCompetitor.query.filter_by(
    user_id=1,
    platform='instagram'
).all()

# Sort by engagement rate
top_competitors = SNSCompetitor.query.filter_by(user_id=1)\
    .order_by(SNSCompetitor.engagement_rate.desc())\
    .limit(10)\
    .all()
```

### Update ReviewAccount (with new field)
```python
from backend.models import ReviewAccount, db
from datetime import datetime

account = ReviewAccount.query.get(123)
account.last_reviewed = datetime.utcnow()  # NEW FIELD
account.success_rate = 0.85
db.session.commit()
```

### Create ReviewApplication (with new field)
```python
from backend.models import ReviewApplication, db
from datetime import datetime

app = ReviewApplication(
    listing_id=456,
    account_id=789,
    status='completed',
    review_url='https://instagram.com/p/abc123',
    review_posted_at=datetime.utcnow(),
    review_content='Amazing product! Highly recommend.'  # NEW FIELD
)
db.session.add(app)
db.session.commit()
```

---

## 🔧 Testing Models

### Run Complete Test Suite
```bash
cd /d/Project
python backend/test_models_complete.py
```

### Verify Schema
```bash
python -m backend.migration_helpers
```

### Check Database
```bash
sqlite3 platform.db ".schema sns_link_in_bios"
sqlite3 platform.db "SELECT COUNT(*) FROM sns_automates;"
```

---

## 📊 Performance Tips

### Use Indexes for Filtering
```python
# Fast (indexed)
SNSAutomate.query.filter_by(user_id=1, is_active=True).all()

# Fast (indexed)
SNSCompetitor.query.filter_by(platform='instagram').all()

# Fast (indexed)
SNSLinkInBio.query.filter_by(slug='my-links').first()
```

### Avoid N+1 Queries
```python
# Slow (N+1)
for competitor in SNSCompetitor.query.all():
    print(competitor.user.name)

# Fast (joined)
from sqlalchemy.orm import joinedload
competitors = SNSCompetitor.query\
    .options(joinedload(SNSCompetitor.user))\
    .all()
```

---

## 🆘 Troubleshooting

### Model Not Found
```
Error: ImportError: cannot import SNSLinkInBio
Solution: Ensure backend/models.py is in PYTHONPATH
```

### Table Not Exists
```
Error: sqlite3.OperationalError: no such table: sns_link_in_bios
Solution: Run init_db(app) or restart Flask app
```

### Field Not Found
```
Error: AttributeError: 'ReviewAccount' has no attribute 'last_reviewed'
Solution: Check database is created with updated schema
Run: python -m backend.migration_helpers
```

---

## 📞 Documentation Links

| Document | Purpose |
|----------|---------|
| DATABASE_MODELS_COMPLETE.md | Detailed specifications |
| SNS_REVIEW_MODELS_DELIVERABLE.md | Full delivery summary |
| MISSION_COMPLETE_DATABASE_MODELS.md | Completion report |
| MODELS_QUICK_REFERENCE.md | This file |

---

## ✅ Verification Checklist

- [x] All 5 models implemented
- [x] All fields present
- [x] All indexes created
- [x] All to_dict() methods work
- [x] Tests passing (14/14)
- [x] Database verified
- [x] Documentation complete
- [x] Code committed (52781c7d)

---

**Last Updated:** 2026-02-26
**Status:** ✅ PRODUCTION READY
**Test Results:** 14/14 PASS