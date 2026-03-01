"""CooCook Service - Chef Booking Platform (Phase 2-3)"""
from flask import Blueprint, request, jsonify, g
from datetime import datetime, date
from sqlalchemy import and_, or_, func, desc
from ..models import db, Chef, Booking, BookingReview, ShoppingList
from ..auth import require_auth, require_subscription
from .shopping_list import ShoppingListService
import random

coocook_bp = Blueprint('coocook', __name__, url_prefix='/api/coocook')


# ============ MOCK DATA ============

# Nutrition data per ingredient (per 100g)
NUTRITION_DB = {
    'rice': {'calories': 130, 'protein': 2.7, 'carbs': 28.2, 'fat': 0.3, 'fiber': 0.4, 'sodium': 1},
    'chicken breast': {'calories': 165, 'protein': 31.0, 'carbs': 0.0, 'fat': 3.6, 'fiber': 0.0, 'sodium': 74},
    'salmon': {'calories': 208, 'protein': 20.4, 'carbs': 0.0, 'fat': 13.4, 'fiber': 0.0, 'sodium': 59},
    'tofu': {'calories': 76, 'protein': 8.0, 'carbs': 1.9, 'fat': 4.8, 'fiber': 0.3, 'sodium': 7},
    'egg': {'calories': 155, 'protein': 13.0, 'carbs': 1.1, 'fat': 11.0, 'fiber': 0.0, 'sodium': 124},
    'pasta': {'calories': 131, 'protein': 5.0, 'carbs': 25.0, 'fat': 1.1, 'fiber': 1.8, 'sodium': 1},
    'beef': {'calories': 250, 'protein': 26.0, 'carbs': 0.0, 'fat': 15.0, 'fiber': 0.0, 'sodium': 72},
    'shrimp': {'calories': 99, 'protein': 24.0, 'carbs': 0.2, 'fat': 0.3, 'fiber': 0.0, 'sodium': 111},
    'broccoli': {'calories': 34, 'protein': 2.8, 'carbs': 7.0, 'fat': 0.4, 'fiber': 2.6, 'sodium': 33},
    'kimchi': {'calories': 15, 'protein': 1.1, 'carbs': 2.4, 'fat': 0.5, 'fiber': 1.6, 'sodium': 498},
    'mushroom': {'calories': 22, 'protein': 3.1, 'carbs': 3.3, 'fat': 0.3, 'fiber': 1.0, 'sodium': 5},
    'spinach': {'calories': 23, 'protein': 2.9, 'carbs': 3.6, 'fat': 0.4, 'fiber': 2.2, 'sodium': 79},
    'onion': {'calories': 40, 'protein': 1.1, 'carbs': 9.3, 'fat': 0.1, 'fiber': 1.7, 'sodium': 4},
    'garlic': {'calories': 149, 'protein': 6.4, 'carbs': 33.1, 'fat': 0.5, 'fiber': 2.1, 'sodium': 17},
    'olive oil': {'calories': 884, 'protein': 0.0, 'carbs': 0.0, 'fat': 100.0, 'fiber': 0.0, 'sodium': 2},
    'soy sauce': {'calories': 53, 'protein': 8.1, 'carbs': 4.9, 'fat': 0.6, 'fiber': 0.8, 'sodium': 5493},
    'butter': {'calories': 717, 'protein': 0.9, 'carbs': 0.1, 'fat': 81.0, 'fiber': 0.0, 'sodium': 11},
    'potato': {'calories': 77, 'protein': 2.0, 'carbs': 17.5, 'fat': 0.1, 'fiber': 2.2, 'sodium': 6},
    'carrot': {'calories': 41, 'protein': 0.9, 'carbs': 9.6, 'fat': 0.2, 'fiber': 2.8, 'sodium': 69},
    'cheese': {'calories': 402, 'protein': 25.0, 'carbs': 1.3, 'fat': 33.1, 'fiber': 0.0, 'sodium': 621},
}

# Mock menus per chef (menu_id -> menu data)
MOCK_MENUS = {
    1: {'id': 1, 'chef_id': 1, 'name': 'Traditional Bibimbap Set', 'category': 'main',
        'cuisine': 'Korean', 'price': 45000, 'description': 'Classic Korean mixed rice bowl with seasonal vegetables',
        'ingredients': ['rice', 'beef', 'egg', 'spinach', 'mushroom', 'carrot', 'kimchi', 'soy sauce'],
        'servings': 2, 'prep_time': 45},
    2: {'id': 2, 'chef_id': 1, 'name': 'Kimchi Jjigae', 'category': 'soup',
        'cuisine': 'Korean', 'price': 35000, 'description': 'Hearty kimchi stew with tofu and pork',
        'ingredients': ['kimchi', 'tofu', 'onion', 'garlic', 'rice'],
        'servings': 2, 'prep_time': 30},
    3: {'id': 3, 'chef_id': 2, 'name': 'Truffle Pasta Carbonara', 'category': 'main',
        'cuisine': 'Italian', 'price': 55000, 'description': 'Creamy carbonara with truffle oil and pancetta',
        'ingredients': ['pasta', 'egg', 'cheese', 'butter', 'garlic', 'olive oil'],
        'servings': 2, 'prep_time': 35},
    4: {'id': 4, 'chef_id': 2, 'name': 'Risotto ai Funghi', 'category': 'main',
        'cuisine': 'Italian', 'price': 48000, 'description': 'Wild mushroom risotto with parmesan',
        'ingredients': ['rice', 'mushroom', 'onion', 'butter', 'cheese', 'olive oil'],
        'servings': 2, 'prep_time': 40},
    5: {'id': 5, 'chef_id': 3, 'name': 'Premium Sushi Omakase', 'category': 'main',
        'cuisine': 'Japanese', 'price': 95000, 'description': '12-piece chef\'s choice sushi selection',
        'ingredients': ['rice', 'salmon', 'shrimp', 'egg', 'soy sauce'],
        'servings': 1, 'prep_time': 60},
    6: {'id': 6, 'chef_id': 3, 'name': 'Tempura Udon Set', 'category': 'noodle',
        'cuisine': 'Japanese', 'price': 38000, 'description': 'Hand-made udon with crispy vegetable tempura',
        'ingredients': ['shrimp', 'broccoli', 'mushroom', 'onion', 'soy sauce', 'egg'],
        'servings': 2, 'prep_time': 45},
    7: {'id': 7, 'chef_id': 4, 'name': 'Coq au Vin', 'category': 'main',
        'cuisine': 'French', 'price': 65000, 'description': 'Classic French braised chicken in wine sauce',
        'ingredients': ['chicken breast', 'onion', 'mushroom', 'carrot', 'potato', 'butter', 'garlic'],
        'servings': 2, 'prep_time': 90},
    8: {'id': 8, 'chef_id': 4, 'name': 'Beef Bourguignon', 'category': 'main',
        'cuisine': 'French', 'price': 72000, 'description': 'Slow-braised beef stew in red wine',
        'ingredients': ['beef', 'onion', 'carrot', 'potato', 'mushroom', 'garlic', 'butter'],
        'servings': 2, 'prep_time': 120},
    9: {'id': 9, 'chef_id': 5, 'name': 'Tacos al Pastor', 'category': 'main',
        'cuisine': 'Mexican', 'price': 35000, 'description': 'Authentic marinated pork tacos with pineapple',
        'ingredients': ['beef', 'onion', 'garlic', 'rice'],
        'servings': 3, 'prep_time': 40},
    10: {'id': 10, 'chef_id': 5, 'name': 'Ceviche de Camaron', 'category': 'appetizer',
         'cuisine': 'Mexican', 'price': 42000, 'description': 'Fresh shrimp ceviche with citrus and avocado',
         'ingredients': ['shrimp', 'onion', 'garlic'],
         'servings': 2, 'prep_time': 25},
}


# ============ EXISTING ENDPOINTS ============

@coocook_bp.route('/chefs', methods=['GET'])
def get_chefs():
    """List chefs with filters"""
    query = Chef.query.filter_by(is_active=True)

    # Filters
    cuisine = request.args.get('cuisine')
    location = request.args.get('location')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 12, type=int)

    if cuisine:
        query = query.filter_by(cuisine_type=cuisine)

    if location:
        query = query.filter(Chef.location.ilike(f'%{location}%'))

    # Pagination
    result = query.paginate(page=page, per_page=per_page)

    chefs_data = []
    for chef in result.items:
        chef_dict = {
            'id': chef.id,
            'name': chef.name,
            'bio': chef.bio,
            'cuisine_type': chef.cuisine_type,
            'location': chef.location,
            'price_per_session': chef.price_per_session,
            'rating': chef.rating,
            'rating_count': chef.rating_count,
        }
        chefs_data.append(chef_dict)

    return jsonify({
        'chefs': chefs_data,
        'total': result.total,
        'pages': result.pages,
        'current_page': page
    }), 200


@coocook_bp.route('/chefs/<int:chef_id>', methods=['GET'])
def get_chef_detail(chef_id):
    """Get chef details"""
    chef = Chef.query.get(chef_id)

    if not chef or not chef.is_active:
        return jsonify({'error': 'Chef not found'}), 404

    return jsonify({
        'id': chef.id,
        'name': chef.name,
        'bio': chef.bio,
        'cuisine_type': chef.cuisine_type,
        'location': chef.location,
        'price_per_session': chef.price_per_session,
        'rating': chef.rating,
        'rating_count': chef.rating_count,
        'user_id': chef.user_id,
    }), 200


@coocook_bp.route('/chefs', methods=['POST'])
@require_auth
def register_chef():
    """Register as a chef"""
    data = request.get_json()

    # Check required fields
    required = ['name', 'cuisine_type', 'location', 'price_per_session']
    if not all(data.get(field) for field in required):
        return jsonify({'error': 'Missing required fields'}), 400

    # Check if already registered
    existing = Chef.query.filter_by(user_id=g.user_id).first()
    if existing:
        return jsonify({'error': 'Already registered as a chef'}), 400

    chef = Chef(
        user_id=g.user_id,
        name=data['name'],
        bio=data.get('bio', ''),
        cuisine_type=data['cuisine_type'],
        location=data['location'],
        price_per_session=float(data['price_per_session']),
    )

    db.session.add(chef)
    db.session.commit()

    return jsonify({
        'id': chef.id,
        'message': 'Chef registered successfully'
    }), 201


@coocook_bp.route('/bookings', methods=['GET'])
@require_auth
@require_subscription('coocook')
def get_my_bookings():
    """Get user's bookings"""
    bookings = Booking.query.filter_by(user_id=g.user_id).all()

    bookings_data = []
    for booking in bookings:
        bookings_data.append({
            'id': booking.id,
            'chef_name': booking.chef.name,
            'chef_cuisine': booking.chef.cuisine_type,
            'booking_date': booking.booking_date.isoformat(),
            'duration_hours': booking.duration_hours,
            'total_price': booking.total_price,
            'status': booking.status,
            'special_requests': booking.special_requests,
            'created_at': booking.created_at.isoformat(),
        })

    return jsonify(bookings_data), 200


@coocook_bp.route('/bookings', methods=['POST'])
@require_auth
@require_subscription('coocook')
def create_booking():
    """Create a booking"""
    data = request.get_json()

    # Validate required fields
    required = ['chef_id', 'booking_date', 'duration_hours']
    if not all(data.get(field) for field in required):
        return jsonify({'error': 'Missing required fields'}), 400

    chef = Chef.query.get(data['chef_id'])
    if not chef or not chef.is_active:
        return jsonify({'error': 'Chef not found'}), 404

    try:
        booking_date = datetime.fromisoformat(data['booking_date']).date()
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid booking date'}), 400

    # Don't allow past dates
    if booking_date < date.today():
        return jsonify({'error': 'Booking date must be in the future'}), 400

    duration = int(data['duration_hours'])
    total_price = duration * chef.price_per_session

    booking = Booking(
        user_id=g.user_id,
        chef_id=chef.id,
        booking_date=booking_date,
        duration_hours=duration,
        total_price=total_price,
        special_requests=data.get('special_requests', ''),
        status='pending'
    )

    db.session.add(booking)
    db.session.commit()

    return jsonify({
        'id': booking.id,
        'message': 'Booking created successfully',
        'total_price': total_price
    }), 201


@coocook_bp.route('/bookings/<int:booking_id>', methods=['GET'])
@require_auth
@require_subscription('coocook')
def get_booking(booking_id):
    """Get booking details"""
    booking = Booking.query.get(booking_id)

    if not booking or booking.user_id != g.user_id:
        return jsonify({'error': 'Booking not found'}), 404

    return jsonify({
        'id': booking.id,
        'chef_id': booking.chef_id,
        'chef_name': booking.chef.name,
        'booking_date': booking.booking_date.isoformat(),
        'duration_hours': booking.duration_hours,
        'total_price': booking.total_price,
        'status': booking.status,
        'special_requests': booking.special_requests,
        'created_at': booking.created_at.isoformat(),
    }), 200


@coocook_bp.route('/bookings/<int:booking_id>', methods=['PUT'])
@require_auth
@require_subscription('coocook')
def update_booking(booking_id):
    """Update booking status (by chef user)"""
    booking = Booking.query.get(booking_id)

    if not booking:
        return jsonify({'error': 'Booking not found'}), 404

    # Only chef can update
    if booking.chef.user_id != g.user_id:
        return jsonify({'error': 'Not authorized'}), 403

    data = request.get_json()
    if 'status' in data:
        booking.status = data['status']
        db.session.commit()

    return jsonify({'message': 'Booking updated'}), 200


# ============ PHASE 2: SEARCH & FILTER ============

@coocook_bp.route('/search', methods=['GET'])
def search_chefs():
    """Advanced search with filters for chefs and menus"""
    q = request.args.get('q', '').strip()
    category = request.args.get('category', '').strip()
    cuisine = request.args.get('cuisine', '').strip()
    price_min = request.args.get('price_min', type=float)
    price_max = request.args.get('price_max', type=float)
    rating_min = request.args.get('rating_min', type=float)
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 12, type=int)

    query = Chef.query.filter_by(is_active=True)

    # Text search across name, bio, cuisine_type, location
    if q:
        search_term = f'%{q}%'
        query = query.filter(
            or_(
                Chef.name.ilike(search_term),
                Chef.bio.ilike(search_term),
                Chef.cuisine_type.ilike(search_term),
                Chef.location.ilike(search_term),
            )
        )

    # Filter by cuisine type
    if cuisine:
        query = query.filter(Chef.cuisine_type.ilike(f'%{cuisine}%'))

    # Filter by price range
    if price_min is not None:
        query = query.filter(Chef.price_per_session >= price_min)
    if price_max is not None:
        query = query.filter(Chef.price_per_session <= price_max)

    # Filter by minimum rating
    if rating_min is not None:
        query = query.filter(Chef.rating >= rating_min)

    # Order by rating descending
    query = query.order_by(desc(Chef.rating))

    result = query.paginate(page=page, per_page=per_page)

    chefs_data = []
    for chef in result.items:
        chef_dict = {
            'id': chef.id,
            'name': chef.name,
            'bio': chef.bio,
            'cuisine_type': chef.cuisine_type,
            'location': chef.location,
            'price_per_session': chef.price_per_session,
            'rating': chef.rating,
            'rating_count': chef.rating_count,
        }

        # Attach matching menus from mock data if category filter is applied
        chef_menus = [m for m in MOCK_MENUS.values() if m['chef_id'] == chef.id]
        if category:
            chef_menus = [m for m in chef_menus if m['category'] == category]
        chef_dict['menus'] = chef_menus

        chefs_data.append(chef_dict)

    # If category filter excludes chefs with no matching menus, filter them out
    if category:
        chefs_data = [c for c in chefs_data if c['menus']]

    return jsonify({
        'results': chefs_data,
        'total': len(chefs_data) if category else result.total,
        'pages': result.pages,
        'current_page': page,
        'query': q,
        'filters': {
            'category': category,
            'cuisine': cuisine,
            'price_min': price_min,
            'price_max': price_max,
            'rating_min': rating_min,
        }
    }), 200


@coocook_bp.route('/categories', methods=['GET'])
def get_categories():
    """Get all menu categories with counts"""
    # Build categories from mock menu data
    category_counts = {}
    for menu in MOCK_MENUS.values():
        cat = menu['category']
        if cat in category_counts:
            category_counts[cat]['count'] += 1
        else:
            category_counts[cat] = {'name': cat, 'count': 1}

    categories = [
        {'slug': slug, 'name': data['name'].replace('_', ' ').title(), 'count': data['count']}
        for slug, data in category_counts.items()
    ]

    # Add display names
    CATEGORY_LABELS = {
        'main': 'Main Course',
        'soup': 'Soup & Stew',
        'noodle': 'Noodle',
        'appetizer': 'Appetizer',
        'dessert': 'Dessert',
        'salad': 'Salad',
        'side': 'Side Dish',
    }
    for cat in categories:
        cat['display_name'] = CATEGORY_LABELS.get(cat['slug'], cat['name'])

    return jsonify({
        'categories': sorted(categories, key=lambda x: x['count'], reverse=True)
    }), 200


@coocook_bp.route('/cuisines', methods=['GET'])
def get_cuisines():
    """Get all available cuisine types from active chefs"""
    cuisine_rows = db.session.query(
        Chef.cuisine_type,
        func.count(Chef.id).label('chef_count'),
        func.avg(Chef.rating).label('avg_rating'),
        func.avg(Chef.price_per_session).label('avg_price')
    ).filter(
        Chef.is_active == True
    ).group_by(
        Chef.cuisine_type
    ).order_by(
        desc(func.count(Chef.id))
    ).all()

    cuisines = []
    for row in cuisine_rows:
        cuisines.append({
            'name': row.cuisine_type,
            'chef_count': row.chef_count,
            'avg_rating': round(float(row.avg_rating or 0), 1),
            'avg_price': round(float(row.avg_price or 0), 0),
        })

    return jsonify({'cuisines': cuisines}), 200


@coocook_bp.route('/popular', methods=['GET'])
def get_popular_chefs():
    """Get popular/trending chefs based on rating and booking count"""
    limit = request.args.get('limit', 10, type=int)

    # Get chefs ordered by rating * rating_count (popularity score)
    chefs = Chef.query.filter_by(
        is_active=True
    ).order_by(
        desc(Chef.rating * Chef.rating_count)
    ).limit(limit).all()

    popular_data = []
    for rank, chef in enumerate(chefs, 1):
        # Count recent bookings
        booking_count = Booking.query.filter_by(chef_id=chef.id).count()

        popular_data.append({
            'rank': rank,
            'id': chef.id,
            'name': chef.name,
            'bio': chef.bio,
            'cuisine_type': chef.cuisine_type,
            'location': chef.location,
            'price_per_session': chef.price_per_session,
            'rating': chef.rating,
            'rating_count': chef.rating_count,
            'total_bookings': booking_count,
            'popularity_score': round(chef.rating * chef.rating_count, 1),
        })

    return jsonify({
        'popular_chefs': popular_data,
        'updated_at': datetime.utcnow().isoformat(),
    }), 200


# ============ PHASE 2: NUTRITION CALCULATOR ============

@coocook_bp.route('/nutrition/<int:menu_id>', methods=['GET'])
def get_menu_nutrition(menu_id):
    """Calculate nutrition info for a specific menu"""
    menu = MOCK_MENUS.get(menu_id)
    if not menu:
        return jsonify({'error': 'Menu not found'}), 404

    # Calculate total nutrition from ingredients
    total_nutrition = {
        'calories': 0, 'protein': 0, 'carbs': 0,
        'fat': 0, 'fiber': 0, 'sodium': 0
    }
    ingredient_breakdown = []

    for ingredient_name in menu.get('ingredients', []):
        nutrition = NUTRITION_DB.get(ingredient_name.lower())
        if nutrition:
            # Assume ~150g per ingredient on average (scaled by servings)
            portion_grams = 150
            factor = portion_grams / 100.0

            item_nutrition = {}
            for key in total_nutrition:
                value = round(nutrition[key] * factor, 1)
                item_nutrition[key] = value
                total_nutrition[key] += value

            ingredient_breakdown.append({
                'name': ingredient_name,
                'portion_grams': portion_grams,
                'nutrition': item_nutrition,
            })

    # Round totals
    for key in total_nutrition:
        total_nutrition[key] = round(total_nutrition[key], 1)

    # Per-serving
    servings = menu.get('servings', 1)
    per_serving = {k: round(v / servings, 1) for k, v in total_nutrition.items()}

    # Daily value percentages (based on 2000 cal diet)
    daily_values = {
        'calories': round(per_serving['calories'] / 2000 * 100, 1),
        'protein': round(per_serving['protein'] / 50 * 100, 1),
        'carbs': round(per_serving['carbs'] / 300 * 100, 1),
        'fat': round(per_serving['fat'] / 65 * 100, 1),
        'fiber': round(per_serving['fiber'] / 25 * 100, 1),
        'sodium': round(per_serving['sodium'] / 2300 * 100, 1),
    }

    return jsonify({
        'menu_id': menu_id,
        'menu_name': menu['name'],
        'servings': servings,
        'total_nutrition': total_nutrition,
        'per_serving': per_serving,
        'daily_value_percent': daily_values,
        'ingredient_breakdown': ingredient_breakdown,
        'disclaimer': 'Nutritional values are estimates based on standard portions.',
    }), 200


@coocook_bp.route('/nutrition/calculate', methods=['POST'])
def calculate_custom_nutrition():
    """Calculate nutrition for custom list of ingredients"""
    data = request.get_json()
    if not data or not data.get('ingredients'):
        return jsonify({'error': 'Missing ingredients list'}), 400

    ingredients = data['ingredients']  # [{name, grams}]
    servings = data.get('servings', 1)

    total_nutrition = {
        'calories': 0, 'protein': 0, 'carbs': 0,
        'fat': 0, 'fiber': 0, 'sodium': 0
    }
    ingredient_breakdown = []
    unknown_ingredients = []

    for item in ingredients:
        name = item.get('name', '').strip().lower()
        grams = item.get('grams', 100)

        nutrition = NUTRITION_DB.get(name)
        if nutrition:
            factor = grams / 100.0
            item_nutrition = {}
            for key in total_nutrition:
                value = round(nutrition[key] * factor, 1)
                item_nutrition[key] = value
                total_nutrition[key] += value

            ingredient_breakdown.append({
                'name': name,
                'portion_grams': grams,
                'nutrition': item_nutrition,
            })
        else:
            unknown_ingredients.append(name)

    # Round totals
    for key in total_nutrition:
        total_nutrition[key] = round(total_nutrition[key], 1)

    # Per-serving
    per_serving = {k: round(v / servings, 1) for k, v in total_nutrition.items()}

    # Daily value percentages
    daily_values = {
        'calories': round(per_serving['calories'] / 2000 * 100, 1),
        'protein': round(per_serving['protein'] / 50 * 100, 1),
        'carbs': round(per_serving['carbs'] / 300 * 100, 1),
        'fat': round(per_serving['fat'] / 65 * 100, 1),
        'fiber': round(per_serving['fiber'] / 25 * 100, 1),
        'sodium': round(per_serving['sodium'] / 2300 * 100, 1),
    }

    return jsonify({
        'servings': servings,
        'total_nutrition': total_nutrition,
        'per_serving': per_serving,
        'daily_value_percent': daily_values,
        'ingredient_breakdown': ingredient_breakdown,
        'unknown_ingredients': unknown_ingredients,
        'available_ingredients': sorted(NUTRITION_DB.keys()),
    }), 200


# ============ PHASE 2: SHOPPING LIST ============

@coocook_bp.route('/shopping-list', methods=['POST'])
@require_auth
@require_subscription('coocook')
def create_shopping_list():
    """Create shopping list from menu/recipe or custom items"""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Missing request body'}), 400

    name = data.get('name', '')
    menu_id = data.get('menu_id')
    items = data.get('items', [])

    # If menu_id provided, build items from menu ingredients
    if menu_id:
        menu = MOCK_MENUS.get(menu_id)
        if not menu:
            return jsonify({'error': 'Menu not found'}), 404

        if not name:
            name = f"Shopping for {menu['name']}"

        # Build shopping list from menu ingredients
        items = []
        for ingredient_name in menu.get('ingredients', []):
            items.append({
                'name': ingredient_name,
                'quantity': 1,
                'unit': 'pack',
                'checked': False,
                'category': _ingredient_category(ingredient_name),
            })
    elif not items:
        return jsonify({'error': 'Provide menu_id or items list'}), 400
    else:
        # Ensure each item has required fields
        for item in items:
            item.setdefault('checked', False)
            item.setdefault('quantity', 1)
            item.setdefault('unit', 'pc')
            item.setdefault('category', 'other')

    if not name:
        name = f"Shopping List - {datetime.utcnow().strftime('%Y-%m-%d')}"

    shopping_list = ShoppingList(
        user_id=g.user_id,
        name=name,
        items=items,
    )

    db.session.add(shopping_list)
    db.session.commit()

    return jsonify({
        'id': shopping_list.id,
        'message': 'Shopping list created',
        'shopping_list': shopping_list.to_dict(),
    }), 201


@coocook_bp.route('/shopping-list', methods=['GET'])
@require_auth
@require_subscription('coocook')
def get_shopping_lists():
    """Get user's shopping lists"""
    lists = ShoppingList.query.filter_by(
        user_id=g.user_id
    ).order_by(
        desc(ShoppingList.created_at)
    ).all()

    return jsonify({
        'shopping_lists': [sl.to_dict() for sl in lists],
        'total': len(lists),
    }), 200


@coocook_bp.route('/shopping-list/<int:list_id>', methods=['PUT'])
@require_auth
@require_subscription('coocook')
def update_shopping_list(list_id):
    """Update shopping list (check items off, rename, edit items)"""
    shopping_list = ShoppingList.query.get(list_id)

    if not shopping_list or shopping_list.user_id != g.user_id:
        return jsonify({'error': 'Shopping list not found'}), 404

    data = request.get_json()

    if 'name' in data:
        shopping_list.name = data['name']

    if 'items' in data:
        shopping_list.items = data['items']

    # Convenience: toggle a single item's checked state
    if 'toggle_item_index' in data:
        idx = data['toggle_item_index']
        items = shopping_list.items or []
        if 0 <= idx < len(items):
            items[idx]['checked'] = not items[idx].get('checked', False)
            shopping_list.items = items

    shopping_list.updated_at = datetime.utcnow()
    db.session.commit()

    return jsonify({
        'message': 'Shopping list updated',
        'shopping_list': shopping_list.to_dict(),
    }), 200


@coocook_bp.route('/shopping-list/<int:list_id>', methods=['DELETE'])
@require_auth
@require_subscription('coocook')
def delete_shopping_list(list_id):
    """Delete a shopping list"""
    shopping_list = ShoppingList.query.get(list_id)

    if not shopping_list or shopping_list.user_id != g.user_id:
        return jsonify({'error': 'Shopping list not found'}), 404

    db.session.delete(shopping_list)
    db.session.commit()

    return jsonify({'message': 'Shopping list deleted'}), 200


# ============ PHASE 3: ENHANCED SHOPPING LIST (v2.0) ============

@coocook_bp.route('/shopping-lists', methods=['POST'])
@require_auth
@require_subscription('coocook')
def create_shopping_list_v2():
    """
    Create shopping list from recipes with automatic merging and price estimation.

    Request body:
    {
        "name": "Weekly Shopping",
        "recipe_ids": [1, 2, 3],  // optional
        "serving_sizes": {"1": 2, "2": 1}  // optional, default 1
    }
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Missing request body'}), 400

    name = data.get('name', f"Shopping List - {datetime.utcnow().strftime('%Y-%m-%d')}")
    recipe_ids = data.get('recipe_ids', [])
    serving_sizes = data.get('serving_sizes', {})

    try:
        shopping_list = ShoppingListService.create_list(
            user_id=g.user_id,
            name=name,
            recipe_ids=recipe_ids,
            serving_sizes=serving_sizes,
        )

        return jsonify({
            'id': shopping_list.id,
            'message': 'Shopping list created successfully',
            'shopping_list': shopping_list.to_dict(),
        }), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 400


@coocook_bp.route('/shopping-lists', methods=['GET'])
@require_auth
@require_subscription('coocook')
def get_shopping_lists_v2():
    """Get all shopping lists for user"""
    lists = ShoppingListService.get_user_lists(g.user_id)

    return jsonify({
        'shopping_lists': [sl.to_dict() for sl in lists],
        'total': len(lists),
    }), 200


@coocook_bp.route('/shopping-lists/<int:list_id>', methods=['GET'])
@require_auth
@require_subscription('coocook')
def get_shopping_list_details(list_id):
    """Get shopping list with full details and price estimate"""
    details = ShoppingListService.get_list_details(list_id, g.user_id)

    if not details:
        return jsonify({'error': 'Shopping list not found'}), 404

    price_estimate = ShoppingListService.calculate_total_price(list_id, g.user_id)

    return jsonify({
        'shopping_list': details,
        'price_estimate': price_estimate,
    }), 200


@coocook_bp.route('/shopping-lists/<int:list_id>', methods=['PUT'])
@require_auth
@require_subscription('coocook')
def update_shopping_list_v2(list_id):
    """
    Update shopping list name or items.

    Request body:
    {
        "name": "New name",  // optional
        "items": [...]  // optional, full items array
    }
    """
    shopping_list = ShoppingList.query.get(list_id)

    if not shopping_list or shopping_list.user_id != g.user_id:
        return jsonify({'error': 'Shopping list not found'}), 404

    data = request.get_json()

    if 'name' in data:
        shopping_list.name = data['name']

    if 'items' in data:
        shopping_list.items = data['items']

    shopping_list.updated_at = datetime.utcnow()
    db.session.commit()

    return jsonify({
        'message': 'Shopping list updated',
        'shopping_list': shopping_list.to_dict(),
    }), 200


@coocook_bp.route('/shopping-lists/<int:list_id>', methods=['DELETE'])
@require_auth
@require_subscription('coocook')
def delete_shopping_list_v2(list_id):
    """Delete shopping list"""
    shopping_list = ShoppingList.query.get(list_id)

    if not shopping_list or shopping_list.user_id != g.user_id:
        return jsonify({'error': 'Shopping list not found'}), 404

    db.session.delete(shopping_list)
    db.session.commit()

    return jsonify({'message': 'Shopping list deleted'}), 200


@coocook_bp.route('/shopping-lists/<int:list_id>/items', methods=['POST'])
@require_auth
@require_subscription('coocook')
def add_shopping_list_item(list_id):
    """
    Add item to shopping list.

    Request body:
    {
        "ingredient": "chicken breast",
        "quantity": 2,
        "unit": "lb"
    }
    """
    data = request.get_json()

    if not data or not data.get('ingredient'):
        return jsonify({'error': 'Missing ingredient'}), 400

    ingredient = data['ingredient']
    quantity = data.get('quantity', 1)
    unit = data.get('unit', 'pack')

    shopping_list = ShoppingListService.add_item(
        list_id=list_id,
        ingredient=ingredient,
        quantity=quantity,
        unit=unit,
        user_id=g.user_id,
    )

    if not shopping_list:
        return jsonify({'error': 'Shopping list not found'}), 404

    return jsonify({
        'message': 'Item added to shopping list',
        'shopping_list': shopping_list.to_dict(),
    }), 201


@coocook_bp.route('/shopping-lists/<int:list_id>/items/<int:item_id>', methods=['PATCH'])
@require_auth
@require_subscription('coocook')
def update_shopping_list_item(list_id, item_id):
    """
    Update shopping list item (quantity, checked status).

    Request body:
    {
        "quantity": 3,  // optional
        "is_checked": true  // optional
    }
    """
    data = request.get_json()

    shopping_list = ShoppingListService.update_item(
        list_id=list_id,
        item_index=item_id,
        quantity=data.get('quantity') if data else None,
        is_checked=data.get('is_checked') if data else None,
        user_id=g.user_id,
    )

    if not shopping_list:
        return jsonify({'error': 'Shopping list or item not found'}), 404

    return jsonify({
        'message': 'Item updated',
        'shopping_list': shopping_list.to_dict(),
    }), 200


@coocook_bp.route('/shopping-lists/<int:list_id>/items/<int:item_id>', methods=['DELETE'])
@require_auth
@require_subscription('coocook')
def delete_shopping_list_item(list_id, item_id):
    """Delete item from shopping list"""
    shopping_list = ShoppingListService.delete_item(
        list_id=list_id,
        item_index=item_id,
        user_id=g.user_id,
    )

    if not shopping_list:
        return jsonify({'error': 'Shopping list or item not found'}), 404

    return jsonify({
        'message': 'Item deleted',
        'shopping_list': shopping_list.to_dict(),
    }), 200


@coocook_bp.route('/shopping-lists/<int:list_id>/price-estimate', methods=['GET'])
@require_auth
@require_subscription('coocook')
def get_shopping_list_price(list_id):
    """Get price estimate for shopping list items"""
    price_estimate = ShoppingListService.calculate_total_price(list_id, g.user_id)

    if not price_estimate:
        return jsonify({'error': 'Shopping list not found'}), 404

    return jsonify(price_estimate), 200


def _ingredient_category(name):
    """Categorize an ingredient for shopping list grouping"""
    categories = {
        'produce': ['broccoli', 'spinach', 'onion', 'garlic', 'carrot', 'mushroom', 'potato'],
        'protein': ['chicken breast', 'beef', 'salmon', 'shrimp', 'tofu', 'egg'],
        'grain': ['rice', 'pasta'],
        'dairy': ['cheese', 'butter'],
        'condiment': ['soy sauce', 'olive oil', 'kimchi'],
    }
    for category, items in categories.items():
        if name.lower() in items:
            return category
    return 'other'


# ============ PHASE 3: FEED & RECOMMENDATIONS ============
# (Feed endpoints moved to feed.py and coocook_feed_service)


@coocook_bp.route('/recommendations', methods=['GET'])
@require_auth
@require_subscription('coocook')
def get_recommendations():
    """AI-powered recommendations (mock) based on user history"""
    limit = request.args.get('limit', 6, type=int)

    # Gather user's booking history to determine preferences
    user_bookings = Booking.query.filter_by(user_id=g.user_id).all()

    # Determine preferred cuisines from bookings
    booked_chef_ids = set()
    cuisine_preference = {}
    for booking in user_bookings:
        booked_chef_ids.add(booking.chef_id)
        cuisine = booking.chef.cuisine_type
        cuisine_preference[cuisine] = cuisine_preference.get(cuisine, 0) + 1

    # Sort cuisines by preference
    sorted_cuisines = sorted(cuisine_preference.items(), key=lambda x: x[1], reverse=True)
    preferred_cuisines = [c[0] for c in sorted_cuisines[:3]] if sorted_cuisines else []

    # Recommend chefs: prioritize same cuisine, then by rating
    query = Chef.query.filter_by(is_active=True)
    all_chefs = query.order_by(desc(Chef.rating)).all()

    recommended_chefs = []
    # First, chefs in preferred cuisines they haven't booked
    for chef in all_chefs:
        if chef.id not in booked_chef_ids and chef.cuisine_type in preferred_cuisines:
            recommended_chefs.append(chef)
    # Then, other high-rated chefs
    for chef in all_chefs:
        if chef not in recommended_chefs and chef.id not in booked_chef_ids:
            recommended_chefs.append(chef)
    # Include previously booked chefs at the end (re-booking)
    for chef in all_chefs:
        if chef not in recommended_chefs:
            recommended_chefs.append(chef)

    recommendations = []
    for chef in recommended_chefs[:limit]:
        # Get matching menus
        chef_menus = [m for m in MOCK_MENUS.values() if m['chef_id'] == chef.id]

        reason = 'Highly rated chef'
        if chef.cuisine_type in preferred_cuisines and chef.id not in booked_chef_ids:
            reason = f'Based on your {chef.cuisine_type} preference'
        elif chef.id in booked_chef_ids:
            reason = 'Book again - you enjoyed this chef'

        recommendations.append({
            'type': 'chef',
            'chef': {
                'id': chef.id,
                'name': chef.name,
                'bio': chef.bio,
                'cuisine_type': chef.cuisine_type,
                'location': chef.location,
                'price_per_session': chef.price_per_session,
                'rating': chef.rating,
                'rating_count': chef.rating_count,
            },
            'menus': chef_menus[:2],
            'reason': reason,
            'confidence': round(random.uniform(0.75, 0.98), 2),
        })

    # Menu recommendations
    menu_recs = []
    all_menus = list(MOCK_MENUS.values())
    random.shuffle(all_menus)
    for menu in all_menus[:3]:
        menu_recs.append({
            'type': 'menu',
            'menu': menu,
            'reason': f"Popular {menu['cuisine']} dish",
            'confidence': round(random.uniform(0.70, 0.95), 2),
        })

    return jsonify({
        'chef_recommendations': recommendations,
        'menu_recommendations': menu_recs,
        'preferred_cuisines': preferred_cuisines,
        'total_bookings_analyzed': len(user_bookings),
    }), 200


# ============ PHASE 3: MENUS ENDPOINT ============

@coocook_bp.route('/menus', methods=['GET'])
def get_menus():
    """Get all available menus (from mock data)"""
    chef_id = request.args.get('chef_id', type=int)
    category = request.args.get('category', '').strip()
    cuisine = request.args.get('cuisine', '').strip()

    menus = list(MOCK_MENUS.values())

    if chef_id:
        menus = [m for m in menus if m['chef_id'] == chef_id]
    if category:
        menus = [m for m in menus if m['category'] == category]
    if cuisine:
        menus = [m for m in menus if m['cuisine'].lower() == cuisine.lower()]

    return jsonify({
        'menus': menus,
        'total': len(menus),
    }), 200


# ============ PHASE 3: RECIPES ENDPOINTS ============

def _enrich_recipe(menu_data):
    """Convert MOCK_MENUS to Recipe format with additional metadata"""
    # Get chef info
    chef = Chef.query.get(menu_data['chef_id'])

    # Generate mock rating and review count based on menu
    rating = round(random.uniform(4.0, 5.0), 1)
    review_count = random.randint(5, 150)

    return {
        'id': menu_data['id'],
        'name': menu_data['name'],
        'description': menu_data['description'],
        'cuisine': menu_data['cuisine'],
        'category': menu_data['category'],
        'price': menu_data['price'],
        'prep_time': menu_data['prep_time'],
        'servings': menu_data['servings'],
        'ingredients': menu_data['ingredients'],
        'rating': rating,
        'review_count': review_count,
        'difficulty': _categorize_difficulty(menu_data['prep_time']),
        'chef_id': menu_data['chef_id'],
        'chef_name': chef.name if chef else 'Unknown',
        'chef_bio': chef.bio if chef else '',
        'created_at': datetime.utcnow().isoformat(),
    }


def _categorize_difficulty(prep_time):
    """Categorize recipe difficulty based on prep time"""
    if prep_time <= 30:
        return 'easy'
    elif prep_time <= 60:
        return 'medium'
    else:
        return 'hard'


@coocook_bp.route('/recipes', methods=['GET'])
def get_recipes():
    """Get all recipes with filtering, sorting, and pagination

    Query params:
    - cuisine: Filter by cuisine (e.g., 'Korean', 'Italian')
    - difficulty: Filter by difficulty (easy/medium/hard)
    - prep_time: Max prep time in minutes
    - sort_by: Sort key (popularity/prep_time/price) - default: popularity
    - sort_order: asc/desc (default: desc)
    - page: Page number (default: 1)
    - per_page: Items per page (default: 12)

    Response:
    {
        "recipes": [...],
        "total": 10,
        "pages": 1,
        "current_page": 1,
        "filters": {...}
    }
    """
    # Get query parameters
    cuisine = request.args.get('cuisine', '').strip()
    difficulty = request.args.get('difficulty', '').strip()
    prep_time_max = request.args.get('prep_time', type=int)
    sort_by = request.args.get('sort_by', 'popularity').lower()
    sort_order = request.args.get('sort_order', 'desc').lower()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 12, type=int)

    # Validate pagination
    page = max(1, page)
    per_page = max(1, min(per_page, 100))  # Cap at 100

    # Get all recipes from mock menus
    recipes = []
    for menu_data in MOCK_MENUS.values():
        recipes.append(_enrich_recipe(menu_data))

    # Apply filters
    if cuisine:
        recipes = [r for r in recipes if r['cuisine'].lower() == cuisine.lower()]

    if difficulty:
        valid_difficulties = ['easy', 'medium', 'hard']
        if difficulty.lower() in valid_difficulties:
            recipes = [r for r in recipes if r['difficulty'] == difficulty.lower()]

    if prep_time_max is not None and prep_time_max > 0:
        recipes = [r for r in recipes if r['prep_time'] <= prep_time_max]

    # Apply sorting
    if sort_by == 'prep_time':
        recipes.sort(key=lambda r: r['prep_time'], reverse=(sort_order == 'desc'))
    elif sort_by == 'price':
        recipes.sort(key=lambda r: r['price'], reverse=(sort_order == 'desc'))
    else:  # popularity (rating * review_count)
        recipes.sort(
            key=lambda r: r['rating'] * r['review_count'],
            reverse=(sort_order == 'desc')
        )

    # Paginate
    total = len(recipes)
    pages = (total + per_page - 1) // per_page
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    paginated_recipes = recipes[start_idx:end_idx]

    return jsonify({
        'recipes': paginated_recipes,
        'total': total,
        'pages': pages,
        'current_page': page,
        'filters': {
            'cuisine': cuisine or None,
            'difficulty': difficulty or None,
            'prep_time_max': prep_time_max,
        },
        'sort': {
            'by': sort_by,
            'order': sort_order,
        }
    }), 200


@coocook_bp.route('/recipes/trending', methods=['GET'])
def get_trending_recipes():
    """Get top 7 trending recipes based on rating and review count

    Response:
    {
        "trending": [...],
        "total": 7,
        "updated_at": "2026-02-26T..."
    }
    """
    limit = request.args.get('limit', 7, type=int)
    limit = max(1, min(limit, 20))  # Cap between 1 and 20

    # Get all recipes
    recipes = []
    for menu_data in MOCK_MENUS.values():
        recipes.append(_enrich_recipe(menu_data))

    # Sort by popularity (rating * review_count)
    recipes.sort(
        key=lambda r: r['rating'] * r['review_count'],
        reverse=True
    )

    trending = recipes[:limit]

    return jsonify({
        'trending': trending,
        'total': len(trending),
        'updated_at': datetime.utcnow().isoformat(),
    }), 200


@coocook_bp.route('/recipes/search', methods=['POST'])
def search_recipes():
    """Search recipes by keyword

    Request body:
    {
        "q": "search query",
        "cuisine": "optional cuisine filter",
        "difficulty": "optional difficulty filter",
        "max_prep_time": "optional max prep time"
    }

    Response:
    {
        "results": [...],
        "query": "search query",
        "count": 5
    }
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Missing request body'}), 400

    q = data.get('q', '').strip().lower()
    if not q:
        return jsonify({'error': 'Search query (q) is required'}), 400

    # Get optional filters
    cuisine = data.get('cuisine', '').strip()
    difficulty = data.get('difficulty', '').strip()
    max_prep_time = data.get('max_prep_time', type=int) if isinstance(data.get('max_prep_time'), int) else None

    # Build initial recipe list
    recipes = []
    for menu_data in MOCK_MENUS.values():
        recipes.append(_enrich_recipe(menu_data))

    # Search: match against name, description, cuisine, ingredients
    results = []
    for recipe in recipes:
        search_fields = [
            recipe['name'].lower(),
            recipe['description'].lower(),
            recipe['cuisine'].lower(),
            recipe['category'].lower(),
            recipe['chef_name'].lower(),
        ] + [ing.lower() for ing in recipe['ingredients']]

        if any(q in field for field in search_fields):
            results.append(recipe)

    # Apply filters
    if cuisine:
        results = [r for r in results if r['cuisine'].lower() == cuisine.lower()]

    if difficulty:
        valid_difficulties = ['easy', 'medium', 'hard']
        if difficulty.lower() in valid_difficulties:
            results = [r for r in results if r['difficulty'] == difficulty.lower()]

    if max_prep_time is not None and max_prep_time > 0:
        results = [r for r in results if r['prep_time'] <= max_prep_time]

    # Sort by relevance (popularity score)
    results.sort(key=lambda r: r['rating'] * r['review_count'], reverse=True)

    return jsonify({
        'results': results,
        'query': q,
        'count': len(results),
        'filters_applied': {
            'cuisine': cuisine or None,
            'difficulty': difficulty or None,
            'max_prep_time': max_prep_time,
        }
    }), 200


@coocook_bp.route('/recipes/<int:recipe_id>', methods=['GET'])
def get_recipe_detail(recipe_id):
    """Get detailed recipe information

    Response includes:
    - Basic info (name, description, cuisine, etc.)
    - Nutrition information
    - Rating and review count
    - Chef information
    - Ingredients with instructions
    """
    menu = MOCK_MENUS.get(recipe_id)
    if not menu:
        return jsonify({'error': 'Recipe not found'}), 404

    recipe = _enrich_recipe(menu)

    # Get nutrition info
    total_nutrition = {
        'calories': 0, 'protein': 0, 'carbs': 0,
        'fat': 0, 'fiber': 0, 'sodium': 0
    }
    ingredient_breakdown = []

    for ingredient_name in menu.get('ingredients', []):
        nutrition = NUTRITION_DB.get(ingredient_name.lower())
        if nutrition:
            portion_grams = 150
            factor = portion_grams / 100.0

            item_nutrition = {}
            for key in total_nutrition:
                value = round(nutrition[key] * factor, 1)
                item_nutrition[key] = value
                total_nutrition[key] += value

            ingredient_breakdown.append({
                'name': ingredient_name,
                'portion_grams': portion_grams,
                'nutrition': item_nutrition,
            })

    # Round totals
    for key in total_nutrition:
        total_nutrition[key] = round(total_nutrition[key], 1)

    # Per-serving
    servings = menu.get('servings', 1)
    per_serving = {k: round(v / servings, 1) for k, v in total_nutrition.items()}

    # Add nutrition to recipe
    recipe['nutrition'] = {
        'total': total_nutrition,
        'per_serving': per_serving,
        'servings': servings,
        'ingredient_breakdown': ingredient_breakdown,
    }

    return jsonify(recipe), 200


# ============ PHASE 3: NUTRITION ENGINE ENDPOINTS ============

from .nutrition_engine import (
    calculate_nutrition,
    calculate_recipe_nutrition,
    get_allergen_info,
    rate_nutrition,
    get_daily_value_percentages,
    format_nutrition_summary,
)


@coocook_bp.route('/nutrition/calculate', methods=['POST'])
def nutrition_calculate():
    """
    Calculate nutrition from a custom list of ingredients.

    Request body:
    {
        "ingredients": [
            {"name": "chicken breast", "quantity_g": 200},
            {"name": "rice", "quantity_g": 150}
        ]
    }

    Returns: Full nutrition breakdown with macros
    """
    data = request.get_json()

    if not data or not data.get('ingredients'):
        return jsonify({'error': 'Missing ingredients list'}), 400

    ingredients = data.get('ingredients', [])

    # Validate ingredient format
    for item in ingredients:
        if not isinstance(item, dict) or 'name' not in item:
            return jsonify({'error': 'Invalid ingredient format'}), 400

    try:
        nutrition_result = calculate_nutrition(ingredients)

        # Add daily value percentages
        nutrition_result['daily_value%'] = get_daily_value_percentages(
            nutrition_result
        )

        # Add score
        nutrition_result['nutrition_score'] = rate_nutrition(
            nutrition_result['calories'],
            nutrition_result['carbs'],
            nutrition_result['protein'],
            nutrition_result['fat'],
            nutrition_result['fiber'],
        )

        return jsonify(nutrition_result), 200

    except Exception as e:
        return jsonify({'error': f'Calculation error: {str(e)}'}), 500


@coocook_bp.route('/recipes/<int:recipe_id>/nutrition', methods=['GET'])
def get_recipe_nutrition(recipe_id):
    """
    Get nutrition information for a specific recipe/menu.

    Query params:
    - servings: int (optional, overrides menu servings)

    Returns: Total nutrition, per-serving breakdown, macros
    """
    menu = MOCK_MENUS.get(recipe_id)

    if not menu:
        return jsonify({'error': 'Recipe not found'}), 404

    # Get override servings from query param
    servings = request.args.get('servings', type=int)

    # Format recipe for calculation
    recipe = {
        'name': menu.get('name', f'Menu {recipe_id}'),
        'ingredients': [
            {'name': ing, 'quantity_g': 150}  # Default 150g per ingredient
            for ing in menu.get('ingredients', [])
        ],
        'servings': servings or menu.get('servings', 1),
    }

    try:
        nutrition_result = calculate_recipe_nutrition(recipe, servings)

        # Add daily value percentages
        nutrition_result['per_serving_daily_value%'] = get_daily_value_percentages(
            nutrition_result['per_serving']
        )

        # Add score for per-serving
        nutrition_result['per_serving_nutrition_score'] = rate_nutrition(
            nutrition_result['per_serving']['calories'],
            nutrition_result['per_serving']['carbs'],
            nutrition_result['per_serving']['protein'],
            nutrition_result['per_serving']['fat'],
            nutrition_result['per_serving']['fiber'],
        )

        # Add menu metadata
        nutrition_result['menu_id'] = recipe_id
        nutrition_result['chef_id'] = menu.get('chef_id')
        nutrition_result['category'] = menu.get('category')
        nutrition_result['cuisine'] = menu.get('cuisine')

        return jsonify(nutrition_result), 200

    except Exception as e:
        return jsonify({'error': f'Calculation error: {str(e)}'}), 500


@coocook_bp.route('/allergen-check', methods=['POST'])
def check_allergens():
    """
    Check for allergens in a list of ingredients.

    Request body:
    {
        "ingredients": ["chicken breast", "egg", "shrimp"]
    }

    Returns: Detected allergens, warnings, safe/unsafe status
    """
    data = request.get_json()

    if not data or not data.get('ingredients'):
        return jsonify({'error': 'Missing ingredients list'}), 400

    ingredients = data.get('ingredients', [])

    if not isinstance(ingredients, list):
        return jsonify({'error': 'Ingredients must be a list'}), 400

    # Validate each is a string
    for ing in ingredients:
        if not isinstance(ing, str):
            return jsonify({'error': 'All ingredients must be strings'}), 400

    try:
        allergen_result = get_allergen_info(ingredients)

        return jsonify({
            'input_ingredients': ingredients,
            'allergens': allergen_result['allergens'],
            'allergen_count': allergen_result['allergen_count'],
            'has_top_8_allergens': allergen_result['has_top_8_allergens'],
            'ingredients_with_allergens': allergen_result['ingredients_with_allergens'],
            'warnings': allergen_result['warnings'],
            'is_safe': allergen_result['is_safe'],
            'timestamp': datetime.utcnow().isoformat(),
        }), 200

    except Exception as e:
        return jsonify({'error': f'Allergen check error: {str(e)}'}), 500


@coocook_bp.route('/nutrition/db', methods=['GET'])
def get_nutrition_database():
    """
    Get the list of available ingredients in the nutrition database.

    Returns: List of all ingredient names and their per-100g nutritional values
    """
    from .nutrition_engine import NUTRITION_DB

    ingredients = []
    for name, nutrition in sorted(NUTRITION_DB.items()):
        ingredients.append({
            'name': name,
            'per_100g': nutrition,
        })

    return jsonify({
        'available_ingredients': ingredients,
        'total_count': len(ingredients),
    }), 200


# ============ SOCIAL FEED ENDPOINTS ============

@coocook_bp.route('/feed', methods=['GET'])
@require_auth
def get_user_feed():
    """
    Get personalized feed for the authenticated user.

    Query Parameters:
    - limit: Number of items (default 20, max 100)
    - offset: Pagination offset (default 0)

    Returns: {
        'feed': [Feed items with user/recipe/activity info],
        'total': Total count,
        'has_more': Boolean,
        'next_offset': Next offset for pagination
    }
    """
    from .feed_service import FeedService

    try:
        user_id = g.user_id
        limit = min(int(request.args.get('limit', 20)), 100)
        offset = int(request.args.get('offset', 0))

        result = FeedService.get_user_feed(user_id, limit, offset)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': f'Feed retrieval failed: {str(e)}'}), 500


@coocook_bp.route('/recipes/<int:recipe_id>/review', methods=['POST'])
@require_auth
def post_recipe_review(recipe_id):
    """
    Post a review for a recipe.

    Request body: {
        'rating': 1-5,
        'text': Review text (max 500 chars),
        'photos': Optional list of photo URLs
    }

    Returns: {'success': bool, 'review_id': int, 'message': str}
    """
    from .feed_service import FeedService

    try:
        user_id = g.user_id
        data = request.get_json()

        rating = data.get('rating')
        text = data.get('text', '')
        photos = data.get('photos', [])

        if not rating:
            return jsonify({'success': False, 'message': 'Rating is required'}), 400

        result = FeedService.post_review(recipe_id, user_id, rating, text, photos)
        status_code = 200 if result.get('success') else 400
        return jsonify(result), status_code
    except Exception as e:
        return jsonify({'success': False, 'message': f'Review submission failed: {str(e)}'}), 500


@coocook_bp.route('/recipes/<int:recipe_id>/reviews', methods=['GET'])
def get_recipe_reviews(recipe_id):
    """
    Get reviews for a recipe with pagination and filtering.

    Query Parameters:
    - page: Page number (default 1)
    - per_page: Reviews per page (default 10, max 50)
    - sort: Sort order - 'recent', 'helpful', 'rating_high', 'rating_low'

    Returns: {
        'reviews': [Review objects],
        'total': Total count,
        'page': Current page,
        'total_pages': Total pages,
        'average_rating': float,
        'rating_distribution': {1: count, 2: count, ...}
    }
    """
    from .feed_service import FeedService

    try:
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 10)), 50)
        sort = request.args.get('sort', 'recent')

        result = FeedService.get_reviews(recipe_id, page, per_page, sort)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': f'Review retrieval failed: {str(e)}'}), 500


@coocook_bp.route('/recipes/<int:recipe_id>/like', methods=['POST'])
@require_auth
def like_recipe(recipe_id):
    """
    Like or unlike a recipe (toggle).

    Returns: {
        'success': bool,
        'liked': bool,
        'like_count': int,
        'message': str
    }
    """
    from .feed_service import FeedService

    try:
        user_id = g.user_id
        result = FeedService.like_recipe(recipe_id, user_id)
        status_code = 200 if result.get('success') else 400
        return jsonify(result), status_code
    except Exception as e:
        return jsonify({'success': False, 'message': f'Like action failed: {str(e)}'}), 500


@coocook_bp.route('/chefs/<int:chef_id>/follow', methods=['POST'])
@require_auth
def follow_chef(chef_id):
    """
    Follow or unfollow a chef (toggle).

    Returns: {
        'success': bool,
        'following': bool,
        'message': str
    }
    """
    from .feed_service import FeedService

    try:
        user_id = g.user_id
        result = FeedService.follow_chef(chef_id, user_id)
        status_code = 200 if result.get('success') else 400
        return jsonify(result), status_code
    except Exception as e:
        return jsonify({'success': False, 'message': f'Follow action failed: {str(e)}'}), 500


@coocook_bp.route('/user/profile', methods=['GET'])
@require_auth
def get_user_profile():
    """
    Get authenticated user's profile with statistics.

    Returns: {
        'user': User object,
        'stats': {
            'cooking_sessions': count,
            'saved_recipes': count,
            'followers': count,
            'following': count,
            'reviews_posted': count,
            'activity_level': 'active'|'moderate'|'inactive'
        },
        'recent_activity': [Feed items]
    }
    """
    from .feed_service import FeedService

    try:
        user_id = g.user_id
        result = FeedService.get_user_profile(user_id)
        status_code = 200 if result.get('success') else 400
        return jsonify(result), status_code
    except Exception as e:
        return jsonify({'success': False, 'message': f'Profile retrieval failed: {str(e)}'}), 500


@coocook_bp.route('/recipes/<int:recipe_id>/share', methods=['POST'])
@require_auth
def share_recipe(recipe_id):
    """
    Track recipe share event.

    Request body: {
        'platform': 'facebook'|'twitter'|'whatsapp'|'email'|'generic'
    }

    Returns: {
        'success': bool,
        'share_count': int,
        'message': str
    }
    """
    from .feed_service import FeedService

    try:
        user_id = g.user_id
        data = request.get_json() or {}
        platform = data.get('platform', 'generic')

        result = FeedService.share_recipe(recipe_id, user_id, platform)
        status_code = 200 if result.get('success') else 400
        return jsonify(result), status_code
    except Exception as e:
        return jsonify({'success': False, 'message': f'Share action failed: {str(e)}'}), 500
