# 📝 🎨 새 서비스 추가 가이드 (10-30분)

> **Purpose**: SoftFactory에 4번째 서비스를 추가합니다.
> **Status**: 🟢 ACTIVE (관리 중)
> **Impact**: [Engineering / Operations]

---

## ⚡ Executive Summary (핵심 요약)
- **주요 내용**: 본 문서는 🎨 새 서비스 추가 가이드 (10-30분) 관련 핵심 명세 및 관리 포인트를 포함합니다.
- **상태**: 현재 최신화 완료 및 검토 됨.
- **연관 문서**: [Master Index](./NOTION_MASTER_INDEX.md)

---

> **마지막 업데이트:** 2026-02-23 | **난이도:** ⭐⭐ (중상)

---

## 🎯 목표

SoftFactory에 4번째 서비스를 추가합니다.

**예시:** "Community" 서비스 (커뮤니티 관리)

---

## 📋 단계별 가이드

### 1️⃣ 백엔드 서비스 모듈 생성 (5분)

**파일:** `backend/services/community.py`

```python
"""Community Service - Community Management"""
from flask import Blueprint, request, jsonify, g
from ..models import db
from ..auth import require_auth, require_subscription

community_bp = Blueprint('community', __name__, url_prefix='/api/community')


@community_bp.route('/posts', methods=['GET'])
@require_subscription('community')
@require_auth
def get_posts():
    """Get community posts"""
    page = request.args.get('page', 1, type=int)
    # TODO: 구현
    return jsonify({'posts': [], 'total': 0, 'page': page}), 200


@community_bp.route('/posts', methods=['POST'])
@require_subscription('community')
@require_auth
def create_post():
    """Create community post"""
    data = request.get_json()
    # TODO: 구현
    return jsonify({'id': 1, 'message': 'Post created'}), 201
```

**핵심:**
- Blueprint 이름: `community_bp`
- URL 프리픽스: `/api/community`
- 데코레이터: `@require_subscription('community')` + `@require_auth`

---

### 2️⃣ DB 모델 추가 (5분)

**파일:** `backend/models.py` 끝에 추가

```python
class CommunityPost(db.Model):
    """Community posts"""
    __tablename__ = 'community_posts'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), default='general')  # general, feedback, bugs
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref='community_posts')

    def __repr__(self):
        return f'<CommunityPost {self.title}>'


class CommunityComment(db.Model):
    """Comments on community posts"""
    __tablename__ = 'community_comments'

    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('community_posts.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    post = db.relationship('CommunityPost', backref='comments', cascade='all, delete-orphan')
    user = db.relationship('User', backref='community_comments')
```

---

### 3️⃣ Product 추가 (2분)

**파일:** `backend/models.py` → `init_db()` 함수 수정

찾기:
```python
def init_db(app):
    db.create_all()

    # 기존 Products
    products = Product.query.all()
    if len(products) == 0:
        coocook = Product(...)
        sns = Product(...)
        review = Product(...)
```

추가:
```python
        community = Product(
            slug='community',
            name='Community',
            description='Community management & discussion',
            icon='💬',
            monthly_price=19.99,
            annual_price=199.99,
            stripe_price_id_monthly='price_community_monthly',
            stripe_price_id_annual='price_community_annual'
        )
        db.session.add(community)
```

---

### 4️⃣ Blueprint 등록 (1분)

**파일:** `backend/app.py`

찾기:
```python
from .services.coocook import coocook_bp
from .services.sns_auto import sns_bp
from .services.review import review_bp
```

추가:
```python
from .services.community import community_bp
```

찾기:
```python
app.register_blueprint(coocook_bp)
app.register_blueprint(sns_bp)
app.register_blueprint(review_bp)
```

추가:
```python
app.register_blueprint(community_bp)
```

---

### 5️⃣ 프론트엔드 폴더 생성 (5분)

**폴더:** `web/community/` 생성

**파일 1:** `web/community/index.html`

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Community</title>
    <link href="https://cdn.tailwindcss.com" rel="stylesheet">
    <script src="../../platform/api.js"></script>
</head>
<body class="bg-gray-50">
    <div class="container mx-auto p-4">
        <h1 class="text-3xl font-bold mb-6">Community 💬</h1>

        <div id="posts" class="space-y-4">
            <!-- Posts will load here -->
        </div>
    </div>

    <script>
        // TODO: 구현
        console.log('Community page loaded');
    </script>
</body>
</html>
```

**파일 2:** `web/community/create.html`

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>New Post</title>
    <link href="https://cdn.tailwindcss.com" rel="stylesheet">
    <script src="../../platform/api.js"></script>
</head>
<body>
    <div class="container mx-auto p-4">
        <h1 class="text-3xl font-bold mb-6">New Post</h1>

        <form class="space-y-4" id="postForm">
            <div>
                <label>Title</label>
                <input type="text" id="title" required class="w-full border p-2 rounded">
            </div>
            <div>
                <label>Content</label>
                <textarea id="content" required class="w-full border p-2 rounded h-40"></textarea>
            </div>
            <button type="submit" class="bg-blue-500 text-white px-4 py-2 rounded">
                Post
            </button>
        </form>
    </div>

    <script>
        // TODO: 구현
    </script>
</body>
</html>
```

---

### 6️⃣ 테스트 (2분)

```bash
# 1. 앱 재시작
python start_platform.py

# 2. 테스트 API
curl http://localhost:8000/api/community/posts \
  -H "Authorization: Bearer YOUR_TOKEN"

# 3. 페이지 접속
# http://localhost:8000/web/community/index.html
```

---

## ✅ 체크리스트

- [ ] `backend/services/community.py` 생성
- [ ] DB 모델 추가 (CommunityPost, CommunityComment)
- [ ] Product 추가 (name, price)
- [ ] Blueprint import & register (app.py)
- [ ] `web/community/` 폴더 + HTML 페이지
- [ ] 앱 재시작
- [ ] API 테스트 (`/api/community/posts`)
- [ ] 페이지 접속 테스트

---

## 🎯 완료 후 더하기

| 기능 | 시간 | 난이도 |
|------|------|--------|
| 포스트 CRUD | 15분 | ⭐ |
| 댓글 기능 | 20분 | ⭐ |
| 좋아요 기능 | 10분 | ⭐ |
| 검색 기능 | 20분 | ⭐⭐ |
| 카테고리 필터 | 10분 | ⭐ |
| 사용자 프로필 | 15분 | ⭐⭐ |

---

## 🚀 예상 시간

```
모델 정의:     5분
API 라우트:   10분
등록/설정:     3분
프론트엔드:    5분
테스트:        2분
────────────────
총합:         25분
```

---

## 💡 팁

1. **모델 먼저:** DB 모델 정의 후 API 작성
2. **데코레이터:** `@require_subscription('service-slug')` 반드시 `@require_auth` 위에
3. **JSON 응답:** 일관된 형식 유지
4. **에러 처리:** 404, 400, 401 적절히 반환
5. **테스트:** curl 또는 Postman으로 API 먼저 테스트

---

## 📚 참고

- 모델 참고: [backend/models.py](../backend/models.py)
- 서비스 예시: [backend/services/coocook.py](../backend/services/coocook.py)
- 프론트엔드 예시: [web/coocook/](../web/coocook/)

---

**질문?** → [TEAM.md](TEAM.md) 에서 05-Backend Developer 또는 06-Frontend Developer 찾기

**마지막 업데이트:** 2026-02-23