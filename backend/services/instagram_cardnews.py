"""Instagram Cardnews service backed by the database."""
from datetime import datetime

from flask import Blueprint, jsonify, request, g

from ..auth import require_auth
from ..models import (
    db,
    SNSAccount,
    InstagramCardNewsProject,
    InstagramCardNewsRule,
    InstagramCardNewsTemplate,
)

instagram_cardnews_bp = Blueprint('instagram_cardnews', __name__, url_prefix='/api/instagram-cardnews')


DEFAULT_ACCOUNT_META = {
    'profileTone': 'balanced',
    'businessType': 'Content Business',
    'audience': 'Followers and potential customers',
    'contentPillars': ['education', 'product', 'story'],
    'preferredTemplateTags': ['brand'],
    'bestPostingWindow': 'Tue-Thu 09:00-11:00',
    'region': 'KR',
}


def _parse_iso_datetime(value):
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        normalized = value.strip()
        if normalized.endswith('Z'):
            normalized = normalized[:-1] + '+00:00'
        try:
            return datetime.fromisoformat(normalized)
        except ValueError:
            return None
    return None


def _as_list(value):
    return value if isinstance(value, list) else []


def _account_to_cardnews_dict(account):
    meta = account.permissions_json or {}
    default_tags = [account.platform or 'instagram']
    return {
        'id': account.id,
        'name': account.account_name,
        'platform': account.platform,
        'handle': f"@{account.account_name}".replace('@@', '@'),
        'status': 'connected' if account.is_active else 'inactive',
        'followers': account.followers_count or 0,
        'profileTone': meta.get('profileTone', DEFAULT_ACCOUNT_META['profileTone']),
        'businessType': meta.get('businessType', DEFAULT_ACCOUNT_META['businessType']),
        'audience': meta.get('audience', DEFAULT_ACCOUNT_META['audience']),
        'contentPillars': meta.get('contentPillars', DEFAULT_ACCOUNT_META['contentPillars']),
        'preferredTemplateTags': meta.get('preferredTemplateTags', default_tags),
        'bestPostingWindow': meta.get('bestPostingWindow', DEFAULT_ACCOUNT_META['bestPostingWindow']),
        'region': meta.get('region', DEFAULT_ACCOUNT_META['region']),
    }


def _template_query():
    return (
        InstagramCardNewsTemplate.query
        .filter(
            (InstagramCardNewsTemplate.user_id == g.user_id)
            | (InstagramCardNewsTemplate.user_id.is_(None))
        )
        .order_by(InstagramCardNewsTemplate.user_id.asc(), InstagramCardNewsTemplate.updated_at.desc())
    )


def _topic_keywords(payload):
    keywords = payload.get('keywords') or []
    if not isinstance(keywords, list):
        keywords = []
    keywords = [str(item).strip() for item in keywords if str(item).strip()]
    if not keywords:
        topic = str(payload.get('topic') or '').strip()
        if topic:
            keywords = [topic]
    return keywords[:5]


def _build_slide_copy(topic, structure, keywords, tone, slide_count):
    tone_map = {
        'professional': 'clear and evidence-based',
        'dynamic': 'fast and high-energy',
        'friendly': 'warm and easy to understand',
        'narrative': 'story-driven and sequential',
        'balanced': 'concise and practical',
    }
    voice = tone_map.get(tone or 'balanced', 'concise and practical')
    slides = []
    for index in range(slide_count):
        step = structure[index] if index < len(structure) else f'Point {index + 1}'
        keyword = keywords[index % len(keywords)] if keywords else topic
        slides.append({
            'index': index + 1,
            'title': f'{step}: {keyword}',
            'body': f'{topic} focused on {keyword} with a {voice} explanation for slide {index + 1}.',
            'imagePrompt': f'instagram cardnews slide {index + 1}, topic {topic}, keyword {keyword}, tone {tone or "balanced"}',
        })
    return slides


@instagram_cardnews_bp.route('/accounts', methods=['GET'])
@require_auth
def get_accounts():
    accounts = (
        SNSAccount.query
        .filter_by(user_id=g.user_id)
        .filter(SNSAccount.platform.in_(['instagram', 'threads', 'facebook', 'tiktok', 'youtube', 'blog']))
        .order_by(SNSAccount.created_at.desc())
        .all()
    )
    return jsonify([_account_to_cardnews_dict(account) for account in accounts]), 200


@instagram_cardnews_bp.route('/templates', methods=['GET'])
@require_auth
def get_templates():
    return jsonify([item.to_dict() for item in _template_query().all()]), 200


@instagram_cardnews_bp.route('/templates', methods=['POST'])
@require_auth
def create_template():
    payload = request.get_json(silent=True) or {}
    name = str(payload.get('name') or '').strip()
    if not name:
        return jsonify({'error': 'name is required'}), 400

    template = InstagramCardNewsTemplate(
        user_id=g.user_id,
        name=name,
        tone=str(payload.get('tone') or 'balanced').strip(),
        description=str(payload.get('description') or '').strip(),
        slides=int(payload.get('slides') or payload.get('slide_count') or 8),
        structure_json=_as_list(payload.get('structure')),
        design_json=payload.get('design') if isinstance(payload.get('design'), dict) else {},
        format=str(payload.get('format') or 'instagram-carousel-4-5').strip(),
        tags_json=_as_list(payload.get('tags')),
    )
    db.session.add(template)
    db.session.commit()
    return jsonify(template.to_dict()), 201


@instagram_cardnews_bp.route('/templates/<int:template_id>', methods=['GET'])
@require_auth
def get_template(template_id):
    template = _template_query().filter_by(id=template_id).first()
    if not template:
        return jsonify({'error': 'template not found'}), 404
    return jsonify(template.to_dict()), 200


@instagram_cardnews_bp.route('/templates/<int:template_id>', methods=['PUT'])
@require_auth
def update_template(template_id):
    template = InstagramCardNewsTemplate.query.filter_by(id=template_id, user_id=g.user_id).first()
    if not template:
        return jsonify({'error': 'template not found'}), 404

    payload = request.get_json(silent=True) or {}
    template.name = str(payload.get('name') or template.name).strip()
    template.tone = str(payload.get('tone') or template.tone or 'balanced').strip()
    template.description = str(payload.get('description') or template.description or '').strip()
    template.slides = int(payload.get('slides') or payload.get('slide_count') or template.slides or 8)
    if 'structure' in payload:
        template.structure_json = _as_list(payload.get('structure'))
    if isinstance(payload.get('design'), dict):
        template.design_json = payload.get('design')
    if 'format' in payload:
        template.format = str(payload.get('format') or template.format).strip()
    if 'tags' in payload:
        template.tags_json = _as_list(payload.get('tags'))
    db.session.commit()
    return jsonify(template.to_dict()), 200


@instagram_cardnews_bp.route('/templates/<int:template_id>', methods=['DELETE'])
@require_auth
def delete_template(template_id):
    template = InstagramCardNewsTemplate.query.filter_by(id=template_id, user_id=g.user_id).first()
    if not template:
        return jsonify({'error': 'template not found'}), 404
    db.session.delete(template)
    db.session.commit()
    return jsonify({'ok': True, 'removed': template_id}), 200


@instagram_cardnews_bp.route('/dm-rules', methods=['GET'])
@require_auth
def get_rules():
    rules = (
        InstagramCardNewsRule.query
        .filter_by(user_id=g.user_id)
        .order_by(InstagramCardNewsRule.updated_at.desc(), InstagramCardNewsRule.id.desc())
        .all()
    )
    return jsonify([rule.to_dict() for rule in rules]), 200


@instagram_cardnews_bp.route('/dm-rules', methods=['POST'])
@require_auth
def create_rule():
    payload = request.get_json(silent=True) or {}
    keyword = str(payload.get('keyword') or '').strip()
    reply = str(payload.get('reply') or '').strip()
    if not keyword or not reply:
        return jsonify({'error': 'keyword and reply are required'}), 400

    rule = InstagramCardNewsRule(
        user_id=g.user_id,
        keyword=keyword,
        reply=reply,
        action=str(payload.get('action') or 'notify').strip(),
    )
    db.session.add(rule)
    db.session.commit()
    return jsonify(rule.to_dict()), 201


@instagram_cardnews_bp.route('/projects', methods=['GET'])
@require_auth
def get_projects():
    projects = (
        InstagramCardNewsProject.query
        .filter_by(user_id=g.user_id)
        .order_by(InstagramCardNewsProject.updated_at.desc(), InstagramCardNewsProject.created_at.desc())
        .all()
    )
    return jsonify([project.to_dict() for project in projects]), 200


@instagram_cardnews_bp.route('/projects', methods=['POST'])
@require_auth
def create_project():
    payload = request.get_json(silent=True) or {}
    title = str(payload.get('title') or '').strip()
    topic = str(payload.get('topic') or '').strip()
    if not title or not topic:
        return jsonify({'error': 'title and topic are required'}), 400

    template_id = payload.get('template_id') or (payload.get('templates') or {}).get('used_template_id')
    template = None
    if template_id:
        template = _template_query().filter_by(id=int(template_id)).first()

    project = InstagramCardNewsProject(
        user_id=g.user_id,
        template_id=template.id if template else None,
        title=title,
        topic=topic,
        tone=str(payload.get('tone') or 'balanced').strip(),
        slide_count=int(payload.get('slide_count') or 8),
        status=str(payload.get('status') or ('scheduled' if payload.get('scheduled_at') else 'ready')).strip(),
        account_ids_json=_as_list(payload.get('accountIds')),
        templates_json=payload.get('templates') if isinstance(payload.get('templates'), dict) else {},
        channels_json=_as_list(payload.get('channels')),
        preview_json=_as_list(payload.get('preview')),
        automation_json=payload.get('automation') if isinstance(payload.get('automation'), dict) else {},
        draft_json=payload.get('draft') if isinstance(payload.get('draft'), dict) else {},
        scheduled_at=_parse_iso_datetime(payload.get('scheduled_at') or payload.get('scheduledAt')),
        last_post_url=str(payload.get('last_post_url') or '').strip(),
    )
    db.session.add(project)
    db.session.commit()
    return jsonify(project.to_dict()), 201


@instagram_cardnews_bp.route('/projects/<int:project_id>', methods=['GET'])
@require_auth
def get_project(project_id):
    project = InstagramCardNewsProject.query.filter_by(id=project_id, user_id=g.user_id).first()
    if not project:
        return jsonify({'error': 'project not found'}), 404
    return jsonify(project.to_dict()), 200


@instagram_cardnews_bp.route('/generate', methods=['POST'])
@require_auth
def generate_cardnews():
    payload = request.get_json(silent=True) or {}
    topic = str(payload.get('topic') or '').strip()
    if not topic:
        return jsonify({'error': 'topic is required'}), 400

    template_id = payload.get('template_id')
    template = _template_query().filter_by(id=int(template_id)).first() if template_id else None
    structure = _as_list(payload.get('structure')) or (template.structure_json if template else []) or ['Hook', 'Evidence', 'CTA']
    slide_count = int(payload.get('slide_count') or (template.slides if template else 6) or 6)
    tone = str(payload.get('tone') or (template.tone if template else 'balanced')).strip()
    design = payload.get('design') if isinstance(payload.get('design'), dict) else (template.design_json if template else {})
    keywords = _topic_keywords(payload)
    slides = _build_slide_copy(topic, structure, keywords, tone, slide_count)

    return jsonify({
        'id': int(datetime.utcnow().timestamp() * 1000),
        'status': 'ready',
        'title': f'{topic} cardnews',
        'topic': topic,
        'slide_count': slide_count,
        'tone': tone,
        'account_ids': _as_list(payload.get('account_ids')),
        'channels': _as_list(payload.get('channels')),
        'design': design or {},
        'preview_text': f'Generated from topic={topic} with {len(keywords)} keyword anchors.',
        'slides': slides,
        'automation': payload.get('automation') if isinstance(payload.get('automation'), dict) else {},
    }), 200


@instagram_cardnews_bp.route('/projects/<int:project_id>/publish', methods=['POST'])
@require_auth
def publish_project(project_id):
    project = InstagramCardNewsProject.query.filter_by(id=project_id, user_id=g.user_id).first()
    if not project:
        return jsonify({'error': 'project not found'}), 404

    channel_states = []
    has_connected_target = False
    for channel in project.channels_json or []:
        account_id = channel.get('accountId')
        account = SNSAccount.query.filter_by(id=account_id, user_id=g.user_id).first() if account_id else None
        can_deliver = bool(account and account.is_active and account.access_token)
        if can_deliver:
            has_connected_target = True
        channel_states.append({
            **channel,
            'status': 'dispatch_ready' if can_deliver else 'connection_required',
        })

    project.channels_json = channel_states
    project.status = 'dispatch_ready' if has_connected_target else 'queued'
    project.published_at = datetime.utcnow()
    project.last_post_url = ''
    db.session.commit()

    return jsonify({
        'id': project.id,
        'status': project.status,
        'channels': channel_states,
        'published_at': project.published_at.isoformat() if project.published_at else None,
        'message': 'External delivery was queued. Connected channel tokens are required for final publish.' if not has_connected_target else 'Delivery is ready for connected channels.',
    }), 200


@instagram_cardnews_bp.route('/simulate-dm', methods=['POST'])
@require_auth
def simulate_dm():
    payload = request.get_json(silent=True) or {}
    message = str(payload.get('message') or '').strip().lower()
    rules = InstagramCardNewsRule.query.filter_by(user_id=g.user_id).all()
    matched = [rule for rule in rules if rule.keyword.lower() in message]
    return jsonify({
        'message': payload.get('message') or '',
        'matched_count': len(matched),
        'triggered': [
            {'keyword': rule.keyword, 'suggestion': rule.reply, 'action': rule.action}
            for rule in matched
        ],
        'confidence': 0.9 if matched else 0.25,
        'recommended_action': 'auto_reply' if matched else 'human_review',
    }), 200
