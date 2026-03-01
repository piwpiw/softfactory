# AWS IAM Policy for SoftFactory File Storage

## User Permissions

### Full S3 + CloudFront Policy for Application

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "S3UploadDownload",
            "Effect": "Allow",
            "Action": [
                "s3:PutObject",
                "s3:GetObject",
                "s3:DeleteObject",
                "s3:ListBucket",
                "s3:GetObjectTagging",
                "s3:PutObjectTagging"
            ],
            "Resource": [
                "arn:aws:s3:::softfactory-uploads",
                "arn:aws:s3:::softfactory-uploads/*"
            ]
        },
        {
            "Sid": "MultipartUpload",
            "Effect": "Allow",
            "Action": [
                "s3:AbortMultipartUpload",
                "s3:ListMultipartUploadParts",
                "s3:ListBucketMultipartUploads"
            ],
            "Resource": [
                "arn:aws:s3:::softfactory-uploads/*"
            ]
        },
        {
            "Sid": "CloudFrontInvalidation",
            "Effect": "Allow",
            "Action": [
                "cloudfront:CreateInvalidation",
                "cloudfront:GetInvalidation",
                "cloudfront:ListInvalidations"
            ],
            "Resource": [
                "arn:aws:cloudfront::ACCOUNT_ID:distribution/DISTRIBUTION_ID"
            ]
        }
    ]
}
```

### Restricted Policy (Read-Only for CDN)

For public API access (read-only):

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "S3ReadOnly",
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
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

### MinIO/Local S3-Compatible (Development)

For local S3 testing with MinIO:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "MinIOAccess",
            "Effect": "Allow",
            "Action": "*",
            "Resource": "*"
        }
    ]
}
```

Set environment for MinIO:
```bash
AWS_ENDPOINT_URL=http://localhost:9000
AWS_ACCESS_KEY_ID=minioadmin
AWS_SECRET_ACCESS_KEY=minioadmin
```

## S3 Bucket Policy

Allow CloudFront distribution to access bucket:

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
        },
        {
            "Sid": "DenyInsecureTransport",
            "Effect": "Deny",
            "Principal": "*",
            "Action": "s3:*",
            "Resource": [
                "arn:aws:s3:::softfactory-uploads",
                "arn:aws:s3:::softfactory-uploads/*"
            ],
            "Condition": {
                "Bool": {
                    "aws:SecureTransport": "false"
                }
            }
        }
    ]
}
```

## Encryption & Permissions

### Server-Side Encryption (SSE-S3)

Default for all uploads. Automatically handled by boto3.

### Client-Side Encryption Key

For additional security with sensitive files:

```bash
# Generate encryption key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Set in environment
S3_CLIENT_ENCRYPTION_KEY=...
```

## Installation & Configuration

### Step 1: Create IAM User

```bash
aws iam create-user --user-name softfactory-app
```

### Step 2: Attach Policy

```bash
aws iam put-user-policy \
    --user-name softfactory-app \
    --policy-name S3CDNPolicy \
    --policy-document file://policy.json
```

### Step 3: Create Access Key

```bash
aws iam create-access-key --user-name softfactory-app
```

Response:
```json
{
    "AccessKey": {
        "AccessKeyId": "AKIAIOSFODNN7EXAMPLE",
        "SecretAccessKey": "wJalrXUtnFEMI/K7MDENG+bPxRfiCYEXAMPLEKEY"
    }
}
```

### Step 4: Save to .env

```bash
echo "AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE" >> .env
echo "AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG+bPxRfiCYEXAMPLEKEY" >> .env
```

## Testing Permissions

### List bucket contents

```bash
aws s3 ls s3://softfactory-uploads/
```

### Upload test file

```bash
aws s3 cp test.jpg s3://softfactory-uploads/test/
```

### Create presigned URL

```bash
aws s3 presign s3://softfactory-uploads/test.jpg --expires-in 3600
```

## Audit & Monitoring

### View IAM User Activity

```bash
aws cloudtrail lookup-events \
    --lookup-attributes AttributeKey=ResourceName,AttributeValue=softfactory-uploads
```

### CloudWatch Alarms

```bash
# Alert on large uploads
aws cloudwatch put-metric-alarm \
    --alarm-name S3LargeFileUpload \
    --metric-name GetRequests \
    --namespace AWS/S3 \
    --threshold 100 \
    --comparison-operator GreaterThanThreshold
```

## Troubleshooting

### Access Denied Error

Check policy is attached:
```bash
aws iam list-user-policies --user-name softfactory-app
```

View full policy:
```bash
aws iam get-user-policy --user-name softfactory-app --policy-name S3CDNPolicy
```

### Slow Multipart Upload

Increase chunk size or threads. Check AWS region latency.

### CloudFront Cache Stale

Invalidate cache:
```bash
aws cloudfront create-invalidation \
    --distribution-id DISTRIBUTION_ID \
    --paths "/*"
```
