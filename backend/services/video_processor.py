"""Video Processing System — FFmpeg integration, transcoding, metadata extraction"""
import os
import json
import subprocess
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from functools import wraps
import boto3
from botocore.exceptions import ClientError
from flask import Blueprint, request, jsonify, g, current_app, send_file
from werkzeug.utils import secure_filename

from ..models import db, Video, VideoVariant, VideoThumbnail, VideoProcessingJob, User
from ..auth import require_auth

video_bp = Blueprint('videos', __name__, url_prefix='/api/videos')

# S3 Configuration
AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_S3_BUCKET = os.getenv('AWS_S3_BUCKET', 'softfactory-uploads')
AWS_S3_REGION = os.getenv('AWS_S3_REGION', 'us-east-1')
CLOUDFRONT_DOMAIN = os.getenv('CLOUDFRONT_DOMAIN')

S3_ENABLED = bool(AWS_ACCESS_KEY and AWS_SECRET_KEY)

# FFmpeg Configuration
FFMPEG_PATH = os.getenv('FFMPEG_PATH', 'ffmpeg')
FFPROBE_PATH = os.getenv('FFPROBE_PATH', 'ffprobe')

# Video constraints
MAX_VIDEO_SIZE = 1024 * 1024 * 1024  # 1GB
MAX_VIDEO_DURATION = 3600  # 1 hour in seconds
ALLOWED_VIDEO_TYPES = ['video/mp4', 'video/quicktime', 'video/x-msvideo', 'video/webm']

# Transcoding profiles
TRANSCODE_PROFILES = {
    '360p': {
        'width': 640,
        'height': 360,
        'bitrate': '500k',
        'format': 'mp4',
        'codec': 'libx264'
    },
    '720p': {
        'width': 1280,
        'height': 720,
        'bitrate': '2500k',
        'format': 'mp4',
        'codec': 'libx264'
    },
    '1080p': {
        'width': 1920,
        'height': 1080,
        'bitrate': '5000k',
        'format': 'mp4',
        'codec': 'libx264'
    },
    'source': {
        'format': 'mp4',
        'codec': 'copy'
    }
}

WEBM_PROFILE = {
    'format': 'webm',
    'codec': 'libvpx-vp9',
    'bitrate': '1000k'
}


def get_s3_client():
    """Get S3 client"""
    if not S3_ENABLED:
        return None
    return boto3.client(
        's3',
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
        region_name=AWS_S3_REGION
    )


def generate_video_key(original_filename: str, user_id: int, variant: str = None) -> str:
    """Generate unique S3 key for video"""
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    ext = os.path.splitext(original_filename)[1]
    filename = secure_filename(os.path.splitext(original_filename)[0])[:50]

    if variant:
        return f'videos/{user_id}/{timestamp}_{filename}_{variant}.mp4'
    return f'videos/{user_id}/{timestamp}_{filename}{ext}'


def extract_metadata(file_path: str) -> dict:
    """Extract video metadata using ffprobe"""
    try:
        cmd = [
            FFPROBE_PATH,
            '-v', 'error',
            '-show_format',
            '-show_streams',
            '-of', 'json',
            file_path
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            return None

        data = json.loads(result.stdout)

        # Extract video stream
        video_stream = None
        for stream in data.get('streams', []):
            if stream.get('codec_type') == 'video':
                video_stream = stream
                break

        if not video_stream:
            return None

        return {
            'duration': float(data.get('format', {}).get('duration', 0)),
            'width': video_stream.get('width'),
            'height': video_stream.get('height'),
            'fps': float(video_stream.get('r_frame_rate', '30').split('/')[0]) if video_stream.get('r_frame_rate') else 30,
            'codec': video_stream.get('codec_name'),
            'bitrate': video_stream.get('bit_rate')
        }
    except Exception as e:
        current_app.logger.error(f"Error extracting metadata: {str(e)}")
        return None


def generate_thumbnail(input_file: str, output_file: str, timestamp: float = 5.0) -> bool:
    """Generate thumbnail from video"""
    try:
        cmd = [
            FFMPEG_PATH,
            '-i', input_file,
            '-ss', str(timestamp),
            '-vf', 'scale=320:180',
            '-vframes', '1',
            output_file,
            '-y'
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return result.returncode == 0
    except Exception as e:
        current_app.logger.error(f"Error generating thumbnail: {str(e)}")
        return False


def transcode_video(input_file: str, output_file: str, profile: str) -> bool:
    """Transcode video to specified quality"""
    try:
        config = TRANSCODE_PROFILES.get(profile, TRANSCODE_PROFILES['source'])

        if config['codec'] == 'copy':
            # Copy without re-encoding
            cmd = [
                FFMPEG_PATH,
                '-i', input_file,
                '-c', 'copy',
                output_file,
                '-y'
            ]
        else:
            # Scale and re-encode
            scale_filter = f"scale={config['width']}:{config['height']}"
            cmd = [
                FFMPEG_PATH,
                '-i', input_file,
                '-vf', scale_filter,
                '-c:v', config['codec'],
                '-b:v', config['bitrate'],
                '-c:a', 'aac',
                '-b:a', '128k',
                output_file,
                '-y'
            ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        return result.returncode == 0
    except Exception as e:
        current_app.logger.error(f"Error transcoding video: {str(e)}")
        return False


def upload_to_s3(file_path: str, s3_key: str, content_type: str = 'video/mp4') -> bool:
    """Upload file to S3"""
    try:
        if not S3_ENABLED:
            return False

        s3 = get_s3_client()
        with open(file_path, 'rb') as f:
            s3.put_object(
                Bucket=AWS_S3_BUCKET,
                Key=s3_key,
                Body=f,
                ContentType=content_type,
                Metadata={
                    'uploaded_at': datetime.utcnow().isoformat(),
                }
            )
        return True
    except ClientError as e:
        current_app.logger.error(f"S3 upload error: {str(e)}")
        return False


def validate_video_file(file_obj, content_type: str) -> tuple[bool, str]:
    """Validate video file"""
    if not file_obj:
        return False, 'No file provided'

    if content_type not in ALLOWED_VIDEO_TYPES:
        return False, f'File type not allowed: {content_type}'

    # Check size
    file_obj.seek(0, os.SEEK_END)
    file_size = file_obj.tell()
    file_obj.seek(0)

    if file_size > MAX_VIDEO_SIZE:
        return False, f'File size exceeds {MAX_VIDEO_SIZE / 1024 / 1024 / 1024}GB limit'

    if file_size == 0:
        return False, 'File is empty'

    return True, ''


def create_processing_job(video_id: int, job_type: str, parameters: dict = None) -> VideoProcessingJob:
    """Create a processing job"""
    job = VideoProcessingJob(
        video_id=video_id,
        job_type=job_type,
        parameters=parameters or {}
    )
    db.session.add(job)
    db.session.commit()
    return job


@video_bp.route('/upload', methods=['POST'])
@require_auth
def upload_video():
    """Upload and initialize video processing

    Request: multipart/form-data with 'file' and optional 'title', 'description'
    Response: { video_id, status, processing_jobs }
    """
    if not S3_ENABLED:
        return jsonify({
            'error': 'S3 not configured',
            'suggestion': 'Set AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY in .env'
        }), 400

    # Validate file
    if 'file' not in request.files:
        return jsonify({'error': 'No file field in request'}), 400

    file_obj = request.files['file']
    if file_obj.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    content_type = file_obj.content_type or 'video/mp4'
    is_valid, error_msg = validate_video_file(file_obj, content_type)
    if not is_valid:
        return jsonify({'error': error_msg}), 400

    # Get optional metadata
    title = request.form.get('title', file_obj.filename)
    description = request.form.get('description', '')

    try:
        # Save temporarily
        temp_dir = tempfile.mkdtemp()
        temp_file = os.path.join(temp_dir, 'original.tmp')

        file_obj.save(temp_file)

        # Extract metadata
        metadata = extract_metadata(temp_file)
        if not metadata:
            shutil.rmtree(temp_dir)
            return jsonify({'error': 'Could not read video metadata'}), 400

        # Check duration
        if metadata['duration'] > MAX_VIDEO_DURATION:
            shutil.rmtree(temp_dir)
            return jsonify({
                'error': f'Video duration exceeds {MAX_VIDEO_DURATION // 60} minutes limit'
            }), 400

        # Create video record
        video = Video(
            user_id=g.user_id,
            original_filename=file_obj.filename,
            file_key=generate_video_key(file_obj.filename, g.user_id),
            file_size=os.path.getsize(temp_file),
            mime_type=content_type,
            title=title,
            description=description,
            duration=metadata['duration'],
            width=metadata['width'],
            height=metadata['height'],
            fps=metadata['fps'],
            codec=metadata['codec'],
            processing_status='processing'
        )
        db.session.add(video)
        db.session.commit()

        # Upload original to S3
        if not upload_to_s3(temp_file, video.file_key, content_type):
            shutil.rmtree(temp_dir)
            video.processing_status = 'failed'
            video.processing_error = 'Failed to upload original file to S3'
            db.session.commit()
            return jsonify({'error': 'Upload to S3 failed'}), 500

        # Create processing jobs
        jobs = []

        # Thumbnails
        for ts, thumb_type in [(5.0, 'main'), (0.0, 'preview')]:
            job = create_processing_job(
                video.id,
                'thumbnail',
                {'timestamp': ts, 'type': thumb_type}
            )
            jobs.append(job.to_dict())

        # Transcoding jobs
        for quality in ['360p', '720p', '1080p']:
            job = create_processing_job(
                video.id,
                f'transcode_{quality}',
                {'quality': quality}
            )
            jobs.append(job.to_dict())

        # WebM variant
        job = create_processing_job(
            video.id,
            'transcode_webm',
            {}
        )
        jobs.append(job.to_dict())

        shutil.rmtree(temp_dir)

        return jsonify({
            'video_id': video.id,
            'status': 'processing',
            'duration': metadata['duration'],
            'width': metadata['width'],
            'height': metadata['height'],
            'processing_jobs': jobs
        }), 202

    except Exception as e:
        shutil.rmtree(temp_dir, ignore_errors=True)
        current_app.logger.error(f"Video upload error: {str(e)}")
        return jsonify({'error': 'Upload failed: ' + str(e)}), 500


@video_bp.route('/<int:video_id>/status', methods=['GET'])
@require_auth
def get_video_status(video_id: int):
    """Get video processing status

    Response: { status, progress, variants, thumbnails, error }
    """
    video = Video.query.filter_by(id=video_id, user_id=g.user_id).first()
    if not video:
        return jsonify({'error': 'Video not found'}), 404

    # Get processing jobs
    jobs = VideoProcessingJob.query.filter_by(video_id=video_id).all()
    total_jobs = len(jobs)
    completed_jobs = sum(1 for j in jobs if j.status == 'completed')
    failed_jobs = sum(1 for j in jobs if j.status == 'failed')

    progress = int((completed_jobs / total_jobs * 100) if total_jobs > 0 else 0)

    return jsonify({
        'video_id': video.id,
        'status': video.processing_status,
        'progress': progress,
        'completed_jobs': completed_jobs,
        'total_jobs': total_jobs,
        'failed_jobs': failed_jobs,
        'error': video.processing_error,
        'variants': [v.to_dict() for v in video.variants],
        'thumbnails': [t.to_dict() for t in video.thumbnails]
    }), 200


@video_bp.route('/<int:video_id>', methods=['GET'])
@require_auth
def get_video(video_id: int):
    """Get video details

    Response: Full video object with variants and thumbnails
    """
    video = Video.query.filter_by(id=video_id, user_id=g.user_id).first()
    if not video:
        return jsonify({'error': 'Video not found'}), 404

    return jsonify(video.to_dict()), 200


@video_bp.route('/<int:video_id>/stream/<quality>', methods=['GET'])
@require_auth
def stream_video(video_id: int, quality: str):
    """Stream video at specified quality

    Quality: 360p, 720p, 1080p, source
    """
    video = Video.query.filter_by(id=video_id).first()
    if not video:
        return jsonify({'error': 'Video not found'}), 404

    # Check access
    if video.user_id != g.user_id and not video.is_public:
        return jsonify({'error': 'Access denied'}), 403

    # Get variant
    variant = VideoVariant.query.filter_by(
        video_id=video_id,
        quality=quality
    ).first()

    if not variant or variant.processing_status != 'completed':
        return jsonify({'error': 'Variant not available'}), 404

    # Return streaming URL (or implement actual streaming)
    if S3_ENABLED and CLOUDFRONT_DOMAIN:
        streaming_url = f'https://{CLOUDFRONT_DOMAIN}/{variant.file_key}'
    else:
        streaming_url = f'https://{AWS_S3_BUCKET}.s3.{AWS_S3_REGION}.amazonaws.com/{variant.file_key}'

    return jsonify({
        'url': streaming_url,
        'quality': quality,
        'width': variant.width,
        'height': variant.height,
        'bitrate': variant.bitrate
    }), 200


@video_bp.route('/<int:video_id>/thumbnail/<int:thumb_id>', methods=['GET'])
@require_auth
def get_thumbnail(video_id: int, thumb_id: int):
    """Get thumbnail image URL

    Response: { url }
    """
    video = Video.query.filter_by(id=video_id).first()
    if not video:
        return jsonify({'error': 'Video not found'}), 404

    # Check access
    if video.user_id != g.user_id and not video.is_public:
        return jsonify({'error': 'Access denied'}), 403

    thumbnail = VideoThumbnail.query.filter_by(id=thumb_id, video_id=video_id).first()
    if not thumbnail:
        return jsonify({'error': 'Thumbnail not found'}), 404

    # Return thumbnail URL
    if S3_ENABLED and CLOUDFRONT_DOMAIN:
        thumbnail_url = f'https://{CLOUDFRONT_DOMAIN}/{thumbnail.file_key}'
    else:
        thumbnail_url = f'https://{AWS_S3_BUCKET}.s3.{AWS_S3_REGION}.amazonaws.com/{thumbnail.file_key}'

    return jsonify({
        'url': thumbnail_url,
        'type': thumbnail.thumbnail_type,
        'width': thumbnail.width,
        'height': thumbnail.height
    }), 200


@video_bp.route('/<int:video_id>', methods=['DELETE'])
@require_auth
def delete_video(video_id: int):
    """Delete video

    Response: { message }
    """
    video = Video.query.filter_by(id=video_id, user_id=g.user_id).first()
    if not video:
        return jsonify({'error': 'Video not found'}), 404

    # Soft delete
    video.is_deleted = True
    video.processing_status = 'deleted'
    db.session.commit()

    return jsonify({'message': 'Video deleted'}), 200


@video_bp.route('/', methods=['GET'])
@require_auth
def list_videos():
    """List user's videos with pagination

    Query params: page=1, per_page=20
    """
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    videos = Video.query.filter_by(
        user_id=g.user_id,
        is_deleted=False
    ).order_by(Video.created_at.desc()).paginate(page=page, per_page=per_page)

    return jsonify({
        'videos': [v.to_dict() for v in videos.items],
        'total': videos.total,
        'pages': videos.pages,
        'current_page': page
    }), 200


@video_bp.route('/<int:video_id>', methods=['PATCH'])
@require_auth
def update_video(video_id: int):
    """Update video metadata

    Request: { title, description, is_public }
    """
    video = Video.query.filter_by(id=video_id, user_id=g.user_id).first()
    if not video:
        return jsonify({'error': 'Video not found'}), 404

    data = request.get_json()

    if 'title' in data:
        video.title = data['title']
    if 'description' in data:
        video.description = data['description']
    if 'is_public' in data:
        video.is_public = data['is_public']

    db.session.commit()

    return jsonify(video.to_dict()), 200


@video_bp.route('/process/worker', methods=['POST'])
def process_video_job():
    """Process a video job (called by background worker)

    This would be called by a Celery worker or similar background task processor
    """
    # Get next pending job
    job = VideoProcessingJob.query.filter_by(status='pending').first()
    if not job:
        return jsonify({'message': 'No pending jobs'}), 200

    # Mark as processing
    job.status = 'processing'
    job.started_at = datetime.utcnow()
    db.session.commit()

    try:
        video = Video.query.get(job.video_id)

        # Download original video from S3
        temp_dir = tempfile.mkdtemp()
        input_file = os.path.join(temp_dir, 'input.mp4')

        if S3_ENABLED:
            s3 = get_s3_client()
            s3.download_file(AWS_S3_BUCKET, video.file_key, input_file)
        else:
            return handle_job_failure(job, 'S3 not enabled')

        # Process based on job type
        if job.job_type == 'thumbnail':
            process_thumbnail_job(video, job, input_file, temp_dir)
        elif job.job_type.startswith('transcode_'):
            process_transcode_job(video, job, input_file, temp_dir)

        shutil.rmtree(temp_dir, ignore_errors=True)

        # Check if all jobs completed
        all_jobs = VideoProcessingJob.query.filter_by(video_id=job.video_id).all()
        if all(j.status in ['completed', 'failed'] for j in all_jobs):
            video.processing_status = 'completed'
            video.processing_completed_at = datetime.utcnow()

        db.session.commit()

    except Exception as e:
        current_app.logger.error(f"Job processing error: {str(e)}")
        handle_job_failure(job, str(e))


def process_thumbnail_job(video, job, input_file, temp_dir):
    """Process thumbnail generation job"""
    thumb_type = job.parameters.get('type', 'main')
    timestamp = job.parameters.get('timestamp', 5.0)

    output_file = os.path.join(temp_dir, f'thumb_{thumb_type}.jpg')

    if not generate_thumbnail(input_file, output_file, timestamp):
        raise Exception(f'Thumbnail generation failed for {thumb_type}')

    # Upload to S3
    s3_key = generate_video_key(video.original_filename, video.user_id, f'thumb_{thumb_type}')

    if not upload_to_s3(output_file, s3_key, 'image/jpeg'):
        raise Exception(f'Failed to upload thumbnail to S3')

    # Create thumbnail record
    thumbnail = VideoThumbnail(
        video_id=video.id,
        thumbnail_type=thumb_type,
        file_key=s3_key,
        file_size=os.path.getsize(output_file),
        width=320,
        height=180,
        timestamp=timestamp
    )
    db.session.add(thumbnail)

    # Mark job complete
    job.status = 'completed'
    job.completed_at = datetime.utcnow()


def process_transcode_job(video, job, input_file, temp_dir):
    """Process video transcoding job"""
    quality = job.parameters.get('quality', 'source')

    # Determine output format
    output_file = os.path.join(temp_dir, f'output_{quality}.mp4')
    s3_key = generate_video_key(video.original_filename, video.user_id, f'{quality}')

    if not transcode_video(input_file, output_file, quality):
        raise Exception(f'Transcoding failed for {quality}')

    # Upload to S3
    if not upload_to_s3(output_file, s3_key, 'video/mp4'):
        raise Exception(f'Failed to upload variant to S3')

    # Get output metadata
    output_metadata = extract_metadata(output_file)

    # Create variant record
    profile = TRANSCODE_PROFILES.get(quality, {})
    variant = VideoVariant(
        video_id=video.id,
        quality=quality,
        format='mp4',
        bitrate=profile.get('bitrate'),
        file_key=s3_key,
        file_size=os.path.getsize(output_file),
        width=output_metadata.get('width'),
        height=output_metadata.get('height'),
        duration=output_metadata.get('duration'),
        processing_status='completed'
    )
    db.session.add(variant)

    # Mark job complete
    job.status = 'completed'
    job.completed_at = datetime.utcnow()


def handle_job_failure(job, error_msg):
    """Handle job processing failure"""
    job.status = 'failed'
    job.error_message = error_msg
    job.retry_count += 1

    if job.retry_count >= job.max_retries:
        video = Video.query.get(job.video_id)
        video.processing_status = 'failed'
        video.processing_error = f'Job {job.job_type} failed: {error_msg}'

    db.session.commit()
    current_app.logger.error(f"Job {job.id} failed: {error_msg}")
