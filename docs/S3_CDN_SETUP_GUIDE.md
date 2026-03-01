# S3 & CloudFront Setup Guide

## Overview

This guide provides step-by-step instructions for setting up AWS S3 and CloudFront CDN for file storage and distribution.

## Part 1: AWS S3 Bucket Setup

### 1.1 Create S3 Bucket

1. Log in to AWS Console
2. Navigate to S3 > Buckets > Create bucket
3. Bucket name: `softfactory-uploads`
4. Region: `us-east-1` (or your preferred region)
5. Block public access: Enable
6. Versioning: Enable
7. Encryption: SSE-S3

### 1.2 Configure CORS Policy

```json
[
    {
        "AllowedHeaders": ["*"],
        "AllowedMethods": ["GET", "PUT", "POST", "DELETE"],
        "AllowedOrigins": ["https://yourdomain.com"],
        "ExposeHeaders": ["ETag"],
        "MaxAgeSeconds": 3600
    }
]
```

### 1.3 Configure Lifecycle Rules

**Purpose**: Auto-delete temporary uploads after 7 days

1. Go to Bucket > Management > Lifecycle rules
2. Create rule:
   - Prefix: `uploads/temp/`
   - Expiration: 7 days
   - Status: Enabled

## Part 2: CloudFront CDN Setup

### 2.1 Create CloudFront Distribution

1. CloudFront > Distributions > Create distribution
2. Origin Settings:
   - Origin domain: `softfactory-uploads.s3.us-east-1.amazonaws.com`
   - Origin access: OAC (Origin Access Control)
3. Cache Behavior:
   - Allowed methods: GET, HEAD, OPTIONS
   - Compress objects automatically: Yes
   - Viewer protocol policy: Redirect HTTP to HTTPS
4. Restrictions:
   - Price class: Use only North America and Europe
5. Default root object: (empty)
6. Create distribution

### 2.2 Update S3 Bucket Policy

Add OAC permissions to allow CloudFront access:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AllowCloudFrontOAC",
            "Effect": "Allow",
            "Principal": {
                "Service": "cloudfront.amazonaws.com"
            },
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::softfactory-uploads/*",
            "Condition": {
                "StringEquals": {
                    "AWS:SourceArn": "arn:aws:cloudfront::ACCOUNT_ID:distribution/DISTRIBUTION_ID"
                }
            }
        }
    ]
}
```

## Part 3: IAM User & Access Keys

### 3.1 Create Programmatic Access User

1. IAM > Users > Create user: `softfactory-app`
2. Attach policy (see Section 4)
3. Create access key
4. Copy credentials to `.env`:

```bash
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
```

## Part 4: IAM Policy (File Upload Permissions)

### Minimal Policy

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "S3Upload",
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

## Part 5: Environment Configuration

### .env Variables

```bash
# AWS S3 Configuration
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
AWS_S3_BUCKET=softfactory-uploads
AWS_S3_REGION=us-east-1

# CloudFront CDN
CLOUDFRONT_DOMAIN=d123abc456.cloudfront.net
```

## Part 6: Cache & Invalidation Strategy

### Cache Headers

Files are cached with:
- **Static assets**: `max-age=31536000` (1 year)
- **Dynamic content**: `max-age=3600` (1 hour)
- **Cache on cloudfront**: Yes (compressed)

### Cache Invalidation

Use AWS CLI to invalidate cache:

```bash
aws cloudfront create-invalidation \
    --distribution-id DISTRIBUTION_ID \
    --paths "/*"
```

### Python Script (cache_invalidator.py)

```python
import boto3
import os

def invalidate_cloudfront_cache(paths):
    client = boto3.client('cloudfront')
    distribution_id = os.getenv('CLOUDFRONT_DISTRIBUTION_ID')
    
    response = client.create_invalidation(
        DistributionId=distribution_id,
        InvalidationBatch={
            'Paths': {
                'Quantity': len(paths),
                'Items': paths
            },
            'CallerReference': str(datetime.utcnow().timestamp())
        }
    )
    return response

# Invalidate all files
invalidate_cloudfront_cache(['/*'])

# Invalidate specific user's uploads
invalidate_cloudfront_cache(['/uploads/123/*'])
```

## Part 7: Monitoring & Costs

### CloudWatch Metrics

1. CloudFront > Monitoring > Metrics
2. Track:
   - Requests
   - BytesDownloaded
   - CacheHitRate
   - OriginLatency

### Cost Estimation

**Typical monthly costs for 1TB data:**
- S3 Storage: $23
- CloudFront: $85 (with compression ~40% reduction)
- Data transfer out: $85
- **Total**: ~$193/month

**Cost optimization:**
- Use CloudFront compression (reduces bandwidth 40-70%)
- Lifecycle rules (delete old files)
- Reserved capacity (33% discount)

## Part 8: Security Best Practices

### 1. Block Public S3 Access

```bash
aws s3api put-public-access-block \
    --bucket softfactory-uploads \
    --public-access-block-configuration \
    "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"
```

### 2. Enable Versioning

Protects against accidental deletion.

### 3. Enable Server-Side Encryption

All uploads encrypted with AES256.

### 4. Use Presigned URLs for Private Files

```python
s3_client.generate_presigned_url(
    'get_object',
    Params={'Bucket': 'softfactory-uploads', 'Key': 'file.pdf'},
    ExpiresIn=3600  # 1 hour
)
```

### 5. Restrict CloudFront to HTTPS Only

All traffic redirected to HTTPS.

## Part 9: Testing

### Test Multipart Upload

```bash
curl -X POST http://localhost:8000/api/files/upload \
    -F "file=@large_file.zip"
```

### Test CDN Delivery

```bash
curl -I https://d123abc456.cloudfront.net/uploads/1/file.jpg
```

Check headers:
- `x-cache: Hit from cloudfront` (cache hit)
- `content-encoding: gzip` (compressed)

## Troubleshooting

### 403 Forbidden on CloudFront

- Verify OAC permissions in S3 bucket policy
- Check CloudFront is configured to use OAC

### Slow Uploads

- Use multipart upload (automatic for files >5MB)
- Check AWS region latency
- Consider S3 Transfer Acceleration

### High Bandwidth Costs

- Enable CloudFront compression
- Implement lifecycle rules
- Use CloudFront caching headers

## References

- AWS S3 Documentation: https://docs.aws.amazon.com/s3/
- CloudFront Documentation: https://docs.aws.amazon.com/cloudfront/
- S3 Pricing: https://aws.amazon.com/s3/pricing/
- CloudFront Pricing: https://aws.amazon.com/cloudfront/pricing/
