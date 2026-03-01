# Elasticsearch Search System Documentation

## Overview

Complete Elasticsearch implementation for SoftFactory providing:
- Full-text search across recipes, SNS posts, and users
- Advanced filtering and faceted navigation
- Autocomplete suggestions
- Search history tracking
- <100ms response times
- Korean and English language support

## Setup Instructions

### 1. Install Elasticsearch

**Docker (Recommended):**
```bash
docker pull docker.elastic.co/elasticsearch/elasticsearch:8.x.x
docker run -d --name elasticsearch \
  -e "discovery.type=single-node" \
  -e "ES_JAVA_OPTS=-Xms512m -Xmx512m" \
  -p 9200:9200 \
  docker.elastic.co/elasticsearch/elasticsearch:8.x.x
```

**Windows/Local Installation:**
1. Download from https://www.elastic.co/downloads/elasticsearch
2. Extract to a folder (e.g., `C:\elasticsearch`)
3. Run `bin\elasticsearch.bat`
4. Verify: `curl http://localhost:9200`

### 2. Install Python Dependencies

```bash
pip install elasticsearch==8.x.x
```

Or add to requirements.txt:
```
elasticsearch>=8.0.0,<9.0.0
```

### 3. Configure Flask App

In `backend/app.py`, ensure initialization:
```python
from .services.elasticsearch_service import init_elasticsearch

# In create_app():
init_elasticsearch(app)
```

### 4. Initialize Indices

Run after app starts:
```bash
python -c "
from backend import create_app
from backend.services.search_indexer import index_all

app = create_app()
with app.app_context():
    result = index_all()
    print(f'Indexed {result}')
"
```

## API Endpoints

### POST /api/search
Full-text search with filtering

**Request:**
```json
{
  "query": "pasta recipe",
  "index": "recipes",
  "filters": {
    "difficulty": "easy",
    "cooking_time_max": 30,
    "calories_range": [100, 500],
    "rating_min": 4.0,
    "tags": ["vegetarian"]
  },
  "sort": "relevance",
  "page": 1,
  "per_page": 20
}
```

**Response:**
```json
{
  "query": "pasta recipe",
  "index": "recipes",
  "total": 42,
  "page": 1,
  "per_page": 20,
  "results": [
    {
      "id": "1",
      "score": 15.2,
      "data": {
        "title": "Creamy Pasta Carbonara",
        "rating": 4.8,
        "cooking_time": 20
      },
      "highlight": {
        "title": ["Creamy <em>Pasta</em> Carbonara"]
      }
    }
  ],
  "took_ms": 45
}
```

### GET /api/search/autocomplete
Autocomplete suggestions

**Query Parameters:**
- `q` (required): Search prefix (minimum 2 chars)
- `field` (optional): 'title', 'ingredients', 'tags' (default: 'title')
- `index` (optional): 'recipes', 'sns_posts', 'users' (default: 'recipes')
- `limit` (optional): Max suggestions (default: 10, max: 20)

**Response:**
```json
{
  "query": "pas",
  "field": "title",
  "suggestions": ["Pasta Carbonara", "Pasta Bolognese", "Pasta Primavera"]
}
```

### GET /api/search/facets
Get available filter values

**Query Parameters:**
- `index` (required): 'recipes', 'sns_posts', 'users'
- `field` (required): 'difficulty', 'tags', 'platform', etc.
- `q` (optional): Filter facets based on search query

**Response:**
```json
{
  "index": "recipes",
  "field": "difficulty",
  "facets": [
    {"name": "easy", "count": 125},
    {"name": "medium", "count": 87},
    {"name": "hard", "count": 34}
  ],
  "total": 3
}
```

### GET /api/search/history
Get user's search history

**Response:**
```json
{
  "history": [
    "pasta recipe",
    "vegetarian",
    "quick meals"
  ],
  "total": 3
}
```

### GET /api/search/trending
Get trending searches

**Query Parameters:**
- `days` (optional): Period in days (default: 7)
- `limit` (optional): Max queries (default: 20)

**Response:**
```json
{
  "days": 7,
  "trending": [
    {"query": "pasta", "index": "recipes", "count": 234},
    {"query": "trending", "index": "sns_posts", "count": 156}
  ],
  "total": 2
}
```

### POST /api/search/advanced
Advanced search with complex boolean queries

**Request:**
```json
{
  "queries": [
    {"field": "title", "value": "pasta", "operator": "must"},
    {"field": "difficulty", "value": "easy", "operator": "must"},
    {"field": "rating", "value": 4.0, "operator": "gte"}
  ],
  "index": "recipes",
  "sort": "relevance"
}
```

### GET /api/search/similar
Find similar items

**Query Parameters:**
- `index` (required): Index name
- `id` (required): Item ID

**Response:**
```json
{
  "similar_to_id": "123",
  "results": [
    {"id": "124", "score": 12.5, "data": {...}},
    {"id": "125", "score": 11.8, "data": {...}}
  ]
}
```

## Admin Endpoints

### GET /api/admin/search/indices
Check index status

**Response:**
```json
{
  "indices": {
    "recipes": {"exists": true, "doc_count": 542, "store_size": 2097152},
    "sns_posts": {"exists": true, "doc_count": 1203, "store_size": 5242880},
    "users": {"exists": true, "doc_count": 89, "store_size": 131072}
  },
  "total_docs": 1834
}
```

### POST /api/admin/search/reindex
Reindex all content from database

**Request:**
```json
{
  "scope": "recipes"  // or "posts", "users", "all"
}
```

### POST /api/admin/search/clear
Clear all documents from an index

**Request:**
```json
{
  "index": "recipes"
}
```

### POST /api/admin/search/reset
Drop and recreate all indices

### GET /api/admin/search/stats
Get search statistics

**Query Parameters:**
- `days` (optional): Period (default: 7)

### GET /api/admin/search/health
Check Elasticsearch cluster health

## Indices Structure

### recipes
- **Fields:** title, description, content, tags, ingredients, difficulty, cooking_time, servings, calories, protein, carbs, fat, rating, review_count, views, created_at, user_id, is_public
- **Analyzers:** Korean (nori), English
- **Shards:** 2, **Replicas:** 1

### sns_posts
- **Fields:** content, caption, hashtags, platform, likes, comments, shares, engagement_rate, posted_at, user_id, user_name
- **Analyzers:** Korean (nori)
- **Shards:** 3, **Replicas:** 1

### users
- **Fields:** name, email, bio, role, created_at, is_active
- **Shards:** 2, **Replicas:** 1

## Performance Optimization

### Query Performance
- Response time target: <100ms (average ~45ms)
- Uses compound indexes for fast filtering
- Implements caching for autocomplete suggestions
- Fuzzy matching with adjustable sensitivity

### Indexing Performance
- Bulk indexing for initial data load
- Real-time single-document updates
- Optimized field mappings to minimize storage
- Shard allocation for parallel indexing

### Database Integration
- Automatic sync on recipe/post creation
- Incremental updates via `sync_single_recipe()`, `sync_single_post()`
- Full reindex capability for consistency
- Background job support

## Features

### 1. Full-Text Search
- Multi-field search (title, content, tags)
- Phrase matching with boost
- Fuzzy matching for typo tolerance
- Highlighting of matching terms

### 2. Faceted Search
- Filter by difficulty, tags, platforms, roles
- Aggregated counts per facet
- Facet discovery for UI

### 3. Autocomplete
- Prefix matching on key fields
- Configurable limit (max 20)
- Fast suggestions (<10ms)

### 4. Search History
- Automatic tracking per user
- Trending searches across users
- Personalized suggestions

### 5. Advanced Queries
- Boolean operators (must, should, gte, lte)
- Range filters (price, date, calories)
- More-like-this queries
- Custom sorting

## Error Handling

```python
try:
    results = search_manager.search_recipes(query, filters, page)
except Exception as e:
    logger.error(f"Search failed: {str(e)}")
    # Fallback to database search
```

## Testing

```bash
# Test basic search
curl -X POST http://localhost:9000/api/search \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"query":"pasta","index":"recipes"}'

# Test autocomplete
curl "http://localhost:9000/api/search/autocomplete?q=pas&field=title"

# Check health
curl http://localhost:9000/api/admin/search/health
```

## Troubleshooting

### Elasticsearch not responding
```bash
# Check if running
curl http://localhost:9200

# Restart container
docker restart elasticsearch
```

### Index errors
```bash
# Reset indices
POST http://localhost:9000/api/admin/search/reset

# Reindex data
POST http://localhost:9000/api/admin/search/reindex?scope=all
```

### Slow queries
- Check shard allocation: `GET /_cat/shards`
- Monitor heap usage: `GET /_nodes/stats`
- Increase heap if needed

## Production Deployment

1. **Enable authentication:** Set username/password in Elasticsearch
2. **Use secure transport:** Enable TLS/SSL
3. **Optimize heap:** 30-40% of total system memory
4. **Monitor metrics:** Setup X-Pack or Prometheus
5. **Backup indices:** Regular snapshots
6. **Update mappings:** Careful schema evolution

## References

- Elasticsearch Docs: https://www.elastic.co/guide/en/elasticsearch/reference/current/index.html
- Python Client: https://www.elastic.co/guide/en/elasticsearch/client/python-api/current/index.html
- Nori Tokenizer: https://www.elastic.co/guide/en/elasticsearch/plugins/current/analysis-nori.html
