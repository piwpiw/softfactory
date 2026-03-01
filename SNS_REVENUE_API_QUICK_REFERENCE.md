# 🔌 SNS Revenue APIs — Quick Reference Guide

> **Purpose**: **Fast lookup for all 19 endpoints**
> **Status**: 🟢 ACTIVE (관리 중)
> **Impact**: [Engineering / Operations]

---

## ⚡ Executive Summary (핵심 요약)
- **주요 내용**: 본 문서는 SNS Revenue APIs — Quick Reference Guide 관련 핵심 명세 및 관리 포인트를 포함합니다.
- **상태**: 현재 최신화 완료 및 검토 됨.
- **연관 문서**: [Master Index](./NOTION_MASTER_INDEX.md)

---

**Fast lookup for all 19 endpoints**

---

## Authentication

All endpoints require Bearer token:
```
Authorization: Bearer <JWT_TOKEN>
```

All endpoints require subscription: `sns-auto`

---

## 1. Link-in-Bio API (6 Endpoints)

### Create Link-in-Bio
```
POST /api/sns/linkinbio
Content-Type: application/json
Authorization: Bearer TOKEN

{
  "slug": "my-shop",
  "title": "My Products",
  "links": [
    {"url": "https://shop.com", "label": "Shop"}
  ],
  "theme": "light"
}
```

### List Link-in-Bios
```
GET /api/sns/linkinbio?page=1&per_page=50&fields=slug,title
Authorization: Bearer TOKEN
```

### Get Single Link-in-Bio
```
GET /api/sns/linkinbio/{id}
Authorization: Bearer TOKEN
```

### Update Link-in-Bio
```
PUT /api/sns/linkinbio/{id}
Content-Type: application/json
Authorization: Bearer TOKEN

{
  "title": "Updated Title",
  "theme": "dark"
}
```

### Delete Link-in-Bio
```
DELETE /api/sns/linkinbio/{id}
Authorization: Bearer TOKEN
```

### Get Stats
```
GET /api/sns/linkinbio/stats/{id}
Authorization: Bearer TOKEN
```

---

## 2. Automation API (6 Endpoints)

### Create Automation
```
POST /api/sns/automate
Content-Type: application/json
Authorization: Bearer TOKEN

{
  "name": "Daily Tips",
  "topic": "Product tips",
  "purpose": "engagement",
  "platforms": ["instagram", "twitter"],
  "frequency": "daily"
}
```

**Purpose:** promotion, engagement, education, community, news
**Frequency:** daily, weekly, biweekly, monthly

### List Automations
```
GET /api/sns/automate?page=1&per_page=50
Authorization: Bearer TOKEN
```

### Get Single Automation
```
GET /api/sns/automate/{id}
Authorization: Bearer TOKEN
```

### Update Automation
```
PUT /api/sns/automate/{id}
Content-Type: application/json
Authorization: Bearer TOKEN

{
  "name": "Updated Name",
  "is_active": false
}
```

### Delete Automation
```
DELETE /api/sns/automate/{id}
Authorization: Bearer TOKEN
```

### Execute Immediately
```
POST /api/sns/automate/{id}/run
Authorization: Bearer TOKEN
```

---

## 3. Trending API (1 Endpoint)

### Get Trending
```
GET /api/sns/trending?platform=instagram&region=KR
Authorization: Bearer TOKEN
```

**Platform:** instagram, twitter, tiktok, linkedin, all
**Region:** KR, US, JP, GB, DE

---

## 4. Content Repurpose API (1 Endpoint)

### Repurpose Content
```
POST /api/sns/repurpose
Content-Type: application/json
Authorization: Bearer TOKEN

{
  "content": "Check our AI tool!",
  "platforms": ["instagram", "twitter", "linkedin"],
  "tone": "professional"
}
```

**Tone:** professional, casual, humorous, inspirational, promotional

---

## 5. Competitor Analysis API (4 Endpoints)

### Add Competitor
```
POST /api/sns/competitor
Content-Type: application/json
Authorization: Bearer TOKEN

{
  "platform": "instagram",
  "username": "@competitor",
  "name": "Competitor Inc"
}
```

### List Competitors
```
GET /api/sns/competitor?page=1&per_page=50
Authorization: Bearer TOKEN
```

### Compare Competitor
```
GET /api/sns/competitor/{id}/compare?period=month
Authorization: Bearer TOKEN
```

**Period:** week, month, year

### Delete Competitor
```
DELETE /api/sns/competitor/{id}
Authorization: Bearer TOKEN
```

---

## 6. ROI Calculator API (1 Endpoint)

### Calculate ROI
```
GET /api/sns/roi?period=month&platform=instagram
Authorization: Bearer TOKEN
```

**Period:** week, month, year, all
**Platform:** instagram, twitter, linkedin, (all)

---

## Common Response Formats

### Success (200/201)
```json
{
  "success": true,
  "data": {},
  "timestamp": "2026-02-26T10:00:00"
}
```

### Error (400/404/422)
```json
{
  "success": false,
  "error": "Error message",
  "timestamp": "2026-02-26T10:00:00"
}
```

### List Response
```json
{
  "success": true,
  "data": [...],
  "pagination": {
    "page": 1,
    "per_page": 50,
    "total_pages": 4
  },
  "total": 175,
  "timestamp": "2026-02-26T10:00:00"
}
```

---

## HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | OK - Success |
| 201 | Created - Resource created |
| 400 | Bad Request - Missing/invalid fields |
| 401 | Unauthorized - No/invalid token |
| 404 | Not Found - Resource doesn't exist |
| 422 | Unprocessable - Invalid enum value |
| 500 | Server Error - Database/exception |

---

## Query Parameters

### Pagination
```
?pagination=offset&page=1&per_page=50
OR
?pagination=cursor&cursor=100&per_page=50
```

### Filtering
```
?fields=slug,title,created_at
```

### Filtering (by status/platform)
```
?platform=instagram
?status=active
?period=month
```

---

## Common Validations

### Enum Values
```
Purpose: promotion, engagement, education, community, news
Frequency: daily, weekly, biweekly, monthly
Tone: professional, casual, humorous, inspirational, promotional
Platform: instagram, twitter, tiktok, linkedin, facebook, youtube, pinterest, threads
Theme: light, dark
Region: KR, US, JP, GB, DE
Period: week, month, year, all
```

### Constraints
```
Slug: alphanumeric + hyphen only, unique per user
Character limits:
  - Instagram: 2,200 chars
  - Twitter: 280 chars
  - Facebook: 63,206 chars
  - LinkedIn: 3,000 chars
  - TikTok: 4,000 chars
  - Pinterest: 500 chars
  - Threads: 500 chars
```

---

## Error Examples

### Missing Required Fields
```
Status: 400
{
  "success": false,
  "error": "Missing fields: title"
}
```

### Duplicate Slug
```
Status: 422
{
  "success": false,
  "error": "Slug already exists"
}
```

### Invalid Enum
```
Status: 422
{
  "success": false,
  "error": "Invalid frequency. Must be one of: daily, weekly, biweekly, monthly"
}
```

### Not Found
```
Status: 404
{
  "success": false,
  "error": "Link-in-Bio not found"
}
```

### Unauthorized
```
Status: 401
{
  "success": false,
  "error": "Authorization header missing or invalid"
}
```

---

## Testing with cURL

### Get Valid Token
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password"
  }'
```

### Create Link-in-Bio
```bash
TOKEN="<token-from-above>"

curl -X POST http://localhost:8000/api/sns/linkinbio \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "slug": "test",
    "title": "Test"
  }'
```

### List with Pagination
```bash
curl "http://localhost:8000/api/sns/linkinbio?page=1&per_page=10" \
  -H "Authorization: Bearer $TOKEN"
```

### Filter Fields
```bash
curl "http://localhost:8000/api/sns/linkinbio?fields=slug,created_at" \
  -H "Authorization: Bearer $TOKEN"
```

---

## Performance Tips

1. **Use Field Filtering** - Reduce payload size
   ```
   ?fields=slug,title
   ```

2. **Use Cursor Pagination** - For large datasets
   ```
   ?pagination=cursor&cursor=100&per_page=50
   ```

3. **Check Caching** - Some endpoints cached 15 min-1 hour
   - Trending: 1 hour cache
   - ROI: 15 min cache
   - Lists: 5 min cache

4. **Use Appropriate Per-Page** - Balance between requests and response size
   ```
   ?per_page=50  (default good)
   ```

---

## Integration Checklist

- [ ] Add JWT token to Authorization header
- [ ] Verify subscription is 'sns-auto'
- [ ] Handle all status codes (200, 201, 400, 401, 404, 422, 500)
- [ ] Parse pagination in list responses
- [ ] Implement field filtering for bandwidth optimization
- [ ] Cache responses locally when possible
- [ ] Set up retry logic for 5xx errors
- [ ] Log all errors for debugging
- [ ] Monitor API response times
- [ ] Test all CRUD operations

---

## Support

For issues or questions:
1. Check the full API documentation: `SNS_REVENUE_API_COMPLETE.md`
2. Review the delivery summary: `SNS_REVENUE_API_DELIVERY_SUMMARY.md`
3. Check the implementation report: `FINAL_SNS_REVENUE_IMPLEMENTATION_REPORT.md`

---

**Last Updated:** 2026-02-26
**API Version:** 1.0
**Status:** Production Ready ✅