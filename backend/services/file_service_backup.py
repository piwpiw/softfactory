"""S3 File Upload & Cloud Storage Management"""
import os
import io
import mimetypes
from datetime import datetime, timedelta
from functools import wraps
import boto3
from botocore.exceptions import ClientError
from flask import Blueprint, request, jsonify, g, current_app
from ..models import db, FileUpload, Invoice, User
from ..auth import require_auth

file_bp = Blueprint('file', __name__, url_prefix='/api/files')

# S3 Configuration
AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_S3_BUCKET = os.getenv('AWS_S3_BUCKET', 'softfactory-uploads')
AWS_S3_REGION = os.getenv('AWS_S3_REGION', 'us-east-1')
CLOUDFRONT_DOMAIN = os.getenv('CLOUDFRONT_DOMAIN')

S3_ENABLED = bool(AWS_ACCESS_KEY and AWS_SECRET_KEY)

# File constraints
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
ALLOWED_TYPES = {
    'image': ['image/jpeg', 'image/png', 'image/webp', 'image/gif'],
    'video': ['video/mp4', 'video/quicktime', 'video/x-msvideo'],
    'document': ['application/pdf', 'application/msword',
                 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                 'application/vnd.ms-excel',
                 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'],
}

# Flatten allowed types
ALLOWED_CONTENT_TYPES = []
for category_types in ALLOWED_TYPES.values():
    ALLOWED_CONTENT_TYPES.extend(category_types)


def get_s3_client():
    """Get S3 client with current app context"""
    if not S3_ENABLED:
        return None
    return boto3.client(
        's3',
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
        region_name=AWS_S3_REGION
    )


def generate_file_key(original_filename: str, user_id: int) -> str:
    """Generate unique S3 key with user isolation"""
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    ext = os.path.splitext(original_filename)[1]
    filename = os.path.splitext(original_filename)[0]
    # Sanitize filename
    filename = ''.join(c for c in filename if c.isalnum() or c in '._- ')[:50]
    return f'uploads/{user_id}/{timestamp}_{filename}{ext}'


def get_file_category(content_type: str) -> str:
    """Determine file category from MIME type"""
    for category, types in ALLOWED_TYPES.items():
        if content_type in types:
            return category
    return 'unknown'


def validate_file(file_obj, content_type: str) -> tuple[bool, str]:
    """Validate file size and type"""
    if not file_obj:
        return False, 'No file provided'

    if content_type not in ALLOWED_CONTENT_TYPES:
        return False, f'File type not allowed: {content_type}'

    # Check size
    file_obj.seek(0, os.SEEK_END)
    file_size = file_obj.tell()
    file_obj.seek(0)

    if file_size > MAX_FILE_SIZE:
        return False, f'File size exceeds {MAX_FILE_SIZE / 1024 / 1024}MB limit'

    if file_size == 0:
        return False, 'File is empty'

    return True, ''


@file_bp.route('/upload', methods=['POST'])
@require_auth
def upload_file():
    """Upload file to S3 and create FileUpload record

    Request: multipart/form-data with 'file' field
    Response: { url, cdn_url, file_key, size, category }
    """
    if not S3_ENABLED:
        return jsonify({
            'error': 'S3 not configured',
            'suggestion': 'Set AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY in .env'
        }), 400

    # Get file from request
    if 'file' not in request.files:
        return jsonify({'error': 'No file field in request'}), 400

    file_obj = request.files['file']
    if file_obj.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    # Validate
    content_type = file_obj.content_type or 'application/octet-stream'
    is_valid, error_msg = validate_file(file_obj, content_type)
    if not is_valid:
        return jsonify({'error': error_msg}), 400

    try:
        s3_client = get_s3_client()
        file_key = generate_file_key(file_obj.filename, g.user_id)

        # Upload to S3
        file_data = file_obj.read()
        s3_client.put_object(
            Bucket=AWS_S3_BUCKET,
            Key=file_key,
            Body=file_data,
            ContentType=content_type,
            Metadata={
                'user_id': str(g.user_id),
                'uploaded_at': datetime.utcnow().isoformat(),
            }
        )

        file_size = len(file_data)
        category = get_file_category(content_type)

        # Generate URLs
        s3_url = f'https://{AWS_S3_BUCKET}.s3.{AWS_S3_REGION}.amazonaws.com/{file_key}'
        cdn_url = f'https://{CLOUDFRONT_DOMAIN}/{file_key}' if CLOUDFRONT_DOMAIN else s3_url

        # Create database record
        upload = FileUpload(
            user_id=g.user_id,
            file_key=file_key,
            original_filename=file_obj.filename,
            file_size=file_size,
            content_type=content_type,
            category=category,
            s3_url=s3_url,
            cdn_url=cdn_url,
            uploaded_at=datetime.utcnow()
        )
        db.session.add(upload)
        db.session.commit()

        return jsonify({
            'file_id': upload.id,
            'url': s3_url,
            'cdn_url': cdn_url,
            'file_key': file_key,
            'size': file_size,
            'category': category,
            'content_type': content_type,
            'original_filename': file_obj.filename,
        }), 201

    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code')
        return jsonify({
            'error': f'S3 error: {error_code}',
            'details': str(e)
        }), 500


@file_bp.route('/<int:file_id>', methods=['GET'])
@require_auth
def get_file_info(file_id):
    """Get file metadata"""
    upload = FileUpload.query.get(file_id)

    if not upload:
        return jsonify({'error': 'File not found'}), 404

    # Check ownership or admin access
    if upload.user_id != g.user_id and not g.user.is_admin:
        return jsonify({'error': 'Not authorized'}), 403

    return jsonify(upload.to_dict()), 200


@file_bp.route('', methods=['GET'])
@require_auth
def list_user_files():
    """List all files uploaded by user

    Query params:
    - category: filter by category (image, video, document)
    - limit: max results (default 50)
    - offset: pagination offset (default 0)
    """
    category = request.args.get('category')
    limit = min(int(request.args.get('limit', 50)), 100)
    offset = int(request.args.get('offset', 0))

    query = FileUpload.query.filter_by(user_id=g.user_id)

    if category:
        query = query.filter_by(category=category)

    total = query.count()
    files = query.order_by(FileUpload.uploaded_at.desc()).limit(limit).offset(offset).all()

    return jsonify({
        'total': total,
        'limit': limit,
        'offset': offset,
        'files': [f.to_dict() for f in files]
    }), 200


@file_bp.route('/<int:file_id>', methods=['DELETE'])
@require_auth
def delete_file(file_id):
    """Delete file from S3 and database"""
    upload = FileUpload.query.get(file_id)

    if not upload:
        return jsonify({'error': 'File not found'}), 404

    if upload.user_id != g.user_id and not g.user.is_admin:
        return jsonify({'error': 'Not authorized'}), 403

    try:
        if S3_ENABLED:
            s3_client = get_s3_client()
            s3_client.delete_object(
                Bucket=AWS_S3_BUCKET,
                Key=upload.file_key
            )

        db.session.delete(upload)
        db.session.commit()

        return jsonify({'message': 'File deleted'}), 200

    except ClientError as e:
        return jsonify({
            'error': 'Failed to delete from S3',
            'details': str(e)
        }), 500


@file_bp.route('/presigned-url', methods=['POST'])
@require_auth
def get_presigned_url():
    """Generate presigned URL for time-limited download

    Body: { file_id, expiration_hours }
    Response: { presigned_url, expires_at }
    """
    data = request.get_json()
    file_id = data.get('file_id')
    expiration_hours = min(int(data.get('expiration_hours', 24)), 168)  # Max 7 days

    upload = FileUpload.query.get(file_id)
    if not upload:
        return jsonify({'error': 'File not found'}), 404

    if upload.user_id != g.user_id and not g.user.is_admin:
        return jsonify({'error': 'Not authorized'}), 403

    if not S3_ENABLED:
        return jsonify({'error': 'S3 not configured'}), 400

    try:
        s3_client = get_s3_client()
        presigned_url = s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': AWS_S3_BUCKET,
                'Key': upload.file_key
            },
            ExpiresIn=expiration_hours * 3600
        )

        expires_at = datetime.utcnow() + timedelta(hours=expiration_hours)

        return jsonify({
            'presigned_url': presigned_url,
            'expires_at': expires_at.isoformat(),
            'file_key': upload.file_key
        }), 200

    except ClientError as e:
        return jsonify({
            'error': 'Failed to generate presigned URL',
            'details': str(e)
        }), 500


@file_bp.route('/cleanup', methods=['POST'])
@require_auth
def cleanup_orphaned_files():
    """Admin: Delete files not referenced by any order/document

    Requires admin access
    """
    if not g.user.is_admin:
        return jsonify({'error': 'Admin access required'}), 403

    data = request.get_json(silent=True) or {}
    try:
        older_than_days = max(0, min(365, int(data.get('older_than_days', 7) or 7)))
    except (TypeError, ValueError):
        return jsonify({'error': 'older_than_days must be an integer'}), 400
    dry_run = bool(str(data.get('dry_run', '').strip()).lower() in ('1', 'true', 'yes'))

    cutoff = datetime.utcnow() - timedelta(days=older_than_days)
    referenced_file_ids = {
        file_id for file_id, in db.session.query(Invoice.pdf_file_id)
        .filter(Invoice.pdf_file_id.isnot(None))
        .all()
    }

    orphan_candidates = FileUpload.query.filter(
        FileUpload.uploaded_at < cutoff,
        FileUpload.id.notin_(referenced_file_ids) if referenced_file_ids else True
    ).all()

    deleted_ids = []
    failed = []

    if dry_run:
        return jsonify({
            'dry_run': True,
            'older_than_days': older_than_days,
            'orphan_files': [
                {
                    'file_id': upload.id,
                    'file_key': upload.file_key,
                    'user_id': upload.user_id,
                    'created_at': upload.uploaded_at.isoformat() if upload.uploaded_at else None,
                }
                for upload in orphan_candidates
            ],
            'count': len(orphan_candidates),
        }), 200

    s3_client = get_s3_client() if S3_ENABLED else None
    for upload in orphan_candidates:
        try:
            if s3_client:
                try:
                    s3_client.delete_object(
                        Bucket=AWS_S3_BUCKET,
                        Key=upload.file_key
                    )
                except ClientError as e:
                    failed.append({'file_id': upload.id, 'error': str(e)})
                    continue
            db.session.delete(upload)
            deleted_ids.append(upload.id)
        except Exception as e:
            failed.append({'file_id': upload.id, 'error': str(e)})

    if deleted_ids:
        db.session.commit()

    return jsonify({
        'dry_run': False,
        'older_than_days': older_than_days,
        'deleted_count': len(deleted_ids),
        'deleted_file_ids': deleted_ids,
        'failed_count': len(failed),
        'failed': failed,
    }), 200
