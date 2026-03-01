# 🔌 File Storage & S3 Integration API

> **Purpose**: **Version:** 1.0
> **Status**: 🟢 ACTIVE (관리 중)
> **Impact**: [Engineering / Operations]

---

## ⚡ Executive Summary (핵심 요약)
- **주요 내용**: 본 문서는 File Storage & S3 Integration API 관련 핵심 명세 및 관리 포인트를 포함합니다.
- **상태**: 현재 최신화 완료 및 검토 됨.
- **연관 문서**: [Master Index](./NOTION_MASTER_INDEX.md)

---

**Version:** 1.0
**Status:** Production Ready
**Base URL:** `/api/files`

## Overview

Cloud-based file storage using Amazon S3 with CloudFront CDN support.

- **Max file size:** 50MB
- **Supported types:** Images, Videos, Documents
- **Storage:** AWS S3 with optional CloudFront distribution
- **Authentication:** JWT token required

---

## Endpoints

### 1. Upload File

**POST** `/api/files/upload`

Upload a file to S3 and create metadata record.

**Headers:**
```
Authorization: Bearer {jwt_token}
Content-Type: multipart/form-data
```

**Request:**
```bash
curl -X POST http://localhost:8000/api/files/upload \
  -H "Authorization: Bearer {token}" \
  -F "file=@document.pdf"
```

**Response:** (201 Created)
```json
{
  "file_id": 42,
  "url": "https://softfactory-uploads.s3.us-east-1.amazonaws.com/uploads/123/20260226_143022_document.pdf",
  "cdn_url": "https://d123abc456.cloudfront.net/uploads/123/20260226_143022_document.pdf",
  "file_key": "uploads/123/20260226_143022_document.pdf",
  "size": 2048576,
  "category": "document",
  "content_type": "application/pdf",
  "original_filename": "document.pdf"
}
```

**Errors:**
- `400 Bad Request` — File validation failed (size, type)
- `400 Bad Request` — No file provided or empty file
- `500 Server Error` — S3 upload failed

---

### 2. Get File Info

**GET** `/api/files/{file_id}`

Retrieve metadata for a specific file.

**Headers:**
```
Authorization: Bearer {jwt_token}
```

**Response:** (200 OK)
```json
{
  "id": 42,
  "file_key": "uploads/123/20260226_143022_document.pdf",
  "original_filename": "document.pdf",
  "file_size": 2048576,
  "content_type": "application/pdf",
  "category": "document",
  "s3_url": "https://...",
  "cdn_url": "https://...",
  "uploaded_at": "2026-02-26T14:30:22",
  "expires_at": null
}
```

---

### 3. List User Files

**GET** `/api/files`

List all files uploaded by the authenticated user.

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `category` | string | (none) | Filter by category: `image`, `video`, `document` |
| `limit` | int | 50 | Max results per page (max 100) |
| `offset` | int | 0 | Pagination offset |

**Example:**
```bash
GET /api/files?category=image&limit=20&offset=0
```

**Response:** (200 OK)
```json
{
  "total": 47,
  "limit": 20,
  "offset": 0,
  "files": [
    {
      "id": 42,
      "file_key": "uploads/123/20260226_143022_screenshot.png",
      "original_filename": "screenshot.png",
      "file_size": 1024000,
      "content_type": "image/png",
      "category": "image",
      "s3_url": "https://...",
      "cdn_url": "https://...",
      "uploaded_at": "2026-02-26T14:30:22",
      "expires_at": null
    }
  ]
}
```

---

### 4. Generate Presigned URL

**POST** `/api/files/presigned-url`

Generate a time-limited download URL for a file.

**Headers:**
```
Authorization: Bearer {jwt_token}
Content-Type: application/json
```

**Request:**
```json
{
  "file_id": 42,
  "expiration_hours": 24
}
```

**Response:** (200 OK)
```json
{
  "presigned_url": "https://softfactory-uploads.s3.us-east-1.amazonaws.com/uploads/123/...?AWSAccessKeyId=...",
  "expires_at": "2026-02-27T14:30:22",
  "file_key": "uploads/123/20260226_143022_document.pdf"
}
```

**Parameters:**
- `expiration_hours` (1-168, default: 24) — URL expiration time in hours

---

### 5. Delete File

**DELETE** `/api/files/{file_id}`

Delete a file from S3 and database.

**Headers:**
```
Authorization: Bearer {jwt_token}
```

**Response:** (200 OK)
```json
{
  "message": "File deleted"
}
```

**Errors:**
- `404 Not Found` — File not found
- `403 Forbidden` — Not authorized (different user)
- `500 Server Error` — S3 deletion failed

---

## File Categories & Supported Types

### Images
- `image/jpeg` — JPG/JPEG
- `image/png` — PNG
- `image/webp` — WebP
- `image/gif` — GIF

### Videos
- `video/mp4` — MP4
- `video/quicktime` — MOV
- `video/x-msvideo` — AVI

### Documents
- `application/pdf` — PDF
- `application/msword` — DOC
- `application/vnd.openxmlformats-officedocument.wordprocessingml.document` — DOCX
- `application/vnd.ms-excel` — XLS
- `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` — XLSX

---

## Configuration

Set these environment variables in `.env`:

```env
# AWS S3
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/...
AWS_S3_BUCKET=softfactory-uploads
AWS_S3_REGION=us-east-1

# CloudFront (optional)
CLOUDFRONT_DOMAIN=d123abc456.cloudfront.net
```

### AWS IAM Policy

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::softfactory-uploads",
        "arn:aws:s3:::softfactory-uploads/*"
      ]
    }
  ]
}
```

---

## Database Schema

### FileUpload Model

```python
class FileUpload(db.Model):
    id: int
    user_id: int (FK Users)
    file_key: str (S3 key)
    original_filename: str
    file_size: int (bytes)
    content_type: str (MIME type)
    category: str (image/video/document)
    s3_url: str
    cdn_url: str
    uploaded_at: datetime
    expires_at: datetime (optional)
```

---

## Best Practices

1. **File Size:** Validate on client-side before upload
2. **Security:** Always verify JWT token and user ownership
3. **CDN:** Use `cdn_url` for public/static files, `s3_url` for private content
4. **Expiration:** Set TTL for temporary files (e.g., invoices, reports)
5. **Cleanup:** Implement periodic deletion of orphaned files

---

## Examples

### Upload Image with JavaScript

```javascript
const fileInput = document.getElementById('file-input');
const file = fileInput.files[0];

const formData = new FormData();
formData.append('file', file);

const response = await fetch('/api/files/upload', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`
  },
  body: formData
});

const { cdn_url, file_id } = await response.json();
console.log('Uploaded:', cdn_url);
```

### List User Documents

```bash
curl -H "Authorization: Bearer {token}" \
  "http://localhost:8000/api/files?category=document&limit=10"
```

---

## Error Handling

| Code | Error | Cause |
|------|-------|-------|
| 400 | File size exceeds limit | File > 50MB |
| 400 | File type not allowed | MIME type not in whitelist |
| 400 | File is empty | File size = 0 bytes |
| 403 | Not authorized | Different user or not admin |
| 404 | File not found | File doesn't exist |
| 500 | S3 error | AWS connectivity issue |

---

## Rate Limiting (Recommended)

- Upload: 10 requests per minute per user
- List: 100 requests per minute per user
- Delete: 50 requests per minute per user