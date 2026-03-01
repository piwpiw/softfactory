"""Experience Platform Service - 체험단 통합 플랫폼"""
from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from ..models import db, ExperienceListing, CrawlerLog

experience_bp = Blueprint('experience', __name__, url_prefix='/api/experience')

# Dummy data for MVP - will be replaced with real crawlers in Phase 5
DUMMY_LISTINGS = {
    'coupang_eats': [
        {
            'title': '[쿠팡이츠] 맛집 배달 리뷰 체험단',
            'url': 'https://www.coupangeats.com',
            'deadline': (datetime.utcnow() + timedelta(days=5)).isoformat(),
            'category': '음식',
            'reward': '무료 음식 + 현금 2만원',
            'description': '신규 맛집의 배달 음식을 먹고 솔직한 리뷰를 남겨주세요',
            'image_url': 'https://via.placeholder.com/300x200?text=Coupang+Eats'
        },
        {
            'title': '[쿠팡이츠] 프리미엄 식재료 체험단 모집',
            'url': 'https://www.coupangeats.com',
            'deadline': (datetime.utcnow() + timedelta(days=7)).isoformat(),
            'category': '음식',
            'reward': '식재료 패키지 50만원 상당',
            'description': '프리미엄 식재료를 직접 요리하고 평가해주세요',
            'image_url': 'https://via.placeholder.com/300x200?text=Ingredients'
        },
    ],
    'danggeun': [
        {
            'title': '[당근마켓] 근처 카페 홍보 체험단',
            'url': 'https://www.daangn.com',
            'deadline': (datetime.utcnow() + timedelta(days=3)).isoformat(),
            'category': '카페',
            'reward': '음료 쿠폰 3만원 + 수수료 5천원',
            'description': '당신의 지역 카페를 소개하고 홍보해주세요',
            'image_url': 'https://via.placeholder.com/300x200?text=Cafe'
        },
        {
            'title': '[당근마켓] 편의점 신상품 체험단',
            'url': 'https://www.daangn.com',
            'deadline': (datetime.utcnow() + timedelta(days=10)).isoformat(),
            'category': '편의점',
            'reward': '신상품 무료 + 리뷰비 5천원',
            'description': '편의점 신상품을 먼저 경험하고 평가해주세요',
            'image_url': 'https://via.placeholder.com/300x200?text=Convenience+Store'
        },
        {
            'title': '[당근마켓] 지역 맛집 배달 평가단',
            'url': 'https://www.daangn.com',
            'deadline': (datetime.utcnow() + timedelta(days=8)).isoformat(),
            'category': '음식',
            'reward': '배달 쿠폰 3만원',
            'description': '우리 동네 맛집을 경험하고 솔직한 평가를 남겨주세요',
            'image_url': 'https://via.placeholder.com/300x200?text=Restaurant'
        },
    ],
    'soomgo': [
        {
            'title': '[숨고] 청소 서비스 품질 평가단',
            'url': 'https://www.soomgo.com',
            'deadline': (datetime.utcnow() + timedelta(days=6)).isoformat(),
            'category': '생활서비스',
            'reward': '청소 서비스 무료 + 평가비 5만원',
            'description': '청소 서비스의 품질을 평가하고 피드백을 주세요',
            'image_url': 'https://via.placeholder.com/300x200?text=Cleaning+Service'
        },
        {
            'title': '[숨고] 인테리어 컨설팅 체험단',
            'url': 'https://www.soomgo.com',
            'deadline': (datetime.utcnow() + timedelta(days=12)).isoformat(),
            'category': '인테리어',
            'reward': '컨설팅 비용 50만원 무료',
            'description': '전문가의 인테리어 컨설팅을 받고 평가해주세요',
            'image_url': 'https://via.placeholder.com/300x200?text=Interior+Design'
        },
    ],
    'today_deal': [
        {
            'title': '[오늘의딜] 뷰티 제품 체험단',
            'url': 'https://www.todaysdeal.co.kr',
            'deadline': (datetime.utcnow() + timedelta(days=4)).isoformat(),
            'category': '뷰티',
            'reward': '뷰티 제품 100만원 상당 + 현금 10만원',
            'description': '신상 뷰티 제품을 사용하고 상세 리뷰를 작성해주세요',
            'image_url': 'https://via.placeholder.com/300x200?text=Beauty+Products'
        },
    ]
}


@experience_bp.route('/listings', methods=['GET'])
def get_listings():
    """Get all or filtered listings"""
    site = request.args.get('site')
    category = request.args.get('category')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 12, type=int)

    # For MVP, use dummy data
    all_listings = []
    for site_name, listings in DUMMY_LISTINGS.items():
        for listing in listings:
            listing_copy = listing.copy()
            listing_copy['site'] = site_name
            all_listings.append(listing_copy)

    # Filter by site
    if site:
        all_listings = [l for l in all_listings if l['site'] == site]

    # Filter by category
    if category:
        all_listings = [l for l in all_listings if l.get('category') == category]

    # Pagination
    start = (page - 1) * per_page
    end = start + per_page
    paginated = all_listings[start:end]

    return jsonify({
        'total': len(all_listings),
        'page': page,
        'per_page': per_page,
        'pages': (len(all_listings) + per_page - 1) // per_page,
        'data': paginated
    }), 200


@experience_bp.route('/listings/<int:listing_id>', methods=['GET'])
def get_listing_detail(listing_id):
    """Get single listing detail"""
    all_listings = []
    for site_name, listings in DUMMY_LISTINGS.items():
        for idx, listing in enumerate(listings):
            listing_copy = listing.copy()
            listing_copy['id'] = hash((site_name, idx)) % 10000
            listing_copy['site'] = site_name
            all_listings.append(listing_copy)

    for listing in all_listings:
        if listing['id'] == listing_id:
            return jsonify(listing), 200

    return jsonify({'error': 'Listing not found'}), 404


@experience_bp.route('/stats', methods=['GET'])
def get_stats():
    """Get platform statistics"""
    total_listings = sum(len(listings) for listings in DUMMY_LISTINGS.values())

    site_stats = {}
    for site, listings in DUMMY_LISTINGS.items():
        site_stats[site] = {
            'count': len(listings),
            'categories': list(set(l.get('category', '미분류') for l in listings))
        }

    # Get category stats
    category_stats = {}
    for site_name, listings in DUMMY_LISTINGS.items():
        for listing in listings:
            cat = listing.get('category', '미분류')
            category_stats[cat] = category_stats.get(cat, 0) + 1

    return jsonify({
        'total_listings': total_listings,
        'total_sites': len(DUMMY_LISTINGS),
        'sites': site_stats,
        'categories': category_stats,
        'last_updated': datetime.utcnow().isoformat()
    }), 200


@experience_bp.route('/crawl', methods=['POST'])
def trigger_crawl():
    """Trigger crawler (MVP: returns dummy response)"""
    site = request.json.get('site') if request.is_json else None

    if site:
        count = len(DUMMY_LISTINGS.get(site, []))
        return jsonify({
            'status': 'success',
            'site': site,
            'listings_found': count,
            'timestamp': datetime.utcnow().isoformat()
        }), 200

    total = sum(len(listings) for listings in DUMMY_LISTINGS.values())
    return jsonify({
        'status': 'success',
        'total_listings_found': total,
        'sites_crawled': list(DUMMY_LISTINGS.keys()),
        'timestamp': datetime.utcnow().isoformat()
    }), 200


@experience_bp.route('/categories', methods=['GET'])
def get_categories():
    """Get all available categories"""
    categories = set()
    for listings in DUMMY_LISTINGS.values():
        for listing in listings:
            cat = listing.get('category', '미분류')
            categories.add(cat)

    return jsonify({
        'categories': sorted(list(categories))
    }), 200


@experience_bp.route('/sites', methods=['GET'])
def get_sites():
    """Get all available sites"""
    sites = list(DUMMY_LISTINGS.keys())

    site_info = {}
    for site in sites:
        site_info[site] = {
            'name': site.replace('_', ' ').title(),
            'count': len(DUMMY_LISTINGS[site])
        }

    return jsonify({
        'sites': site_info
    }), 200
