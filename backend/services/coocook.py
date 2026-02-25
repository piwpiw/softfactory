"""CooCook Service - Chef Booking Platform"""
from flask import Blueprint, request, jsonify, g
from datetime import datetime, date
from sqlalchemy import and_
from ..models import db, Chef, Booking
from ..auth import require_auth, require_subscription

coocook_bp = Blueprint('coocook', __name__, url_prefix='/api/coocook')


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


@coocook_bp.route('/bookings/<int:booking_id>/pay', methods=['POST'])
@require_auth
@require_subscription('coocook')
def process_payment(booking_id):
    """Process payment for a booking"""
    booking = Booking.query.get(booking_id)

    if not booking:
        return jsonify({'error': 'Booking not found'}), 404

    if booking.user_id != g.user_id:
        return jsonify({'error': 'Not authorized'}), 403

    if booking.payment_status == 'paid':
        return jsonify({'error': 'Already paid'}), 400

    data = request.get_json()
    amount = float(data.get('amount', booking.total_price))

    # Validate amount matches booking
    if amount != booking.total_price:
        return jsonify({'error': 'Amount mismatch'}), 400

    # Create payment record
    from ..models import BookingPayment
    payment = BookingPayment(
        booking_id=booking_id,
        user_id=g.user_id,
        amount=amount,
        currency='KRW',
        status='completed',
        transaction_id=f'TXN-{booking_id}-{datetime.utcnow().timestamp()}'
    )

    # Update booking status
    booking.payment_status = 'paid'
    booking.status = 'confirmed'

    db.session.add(payment)
    db.session.commit()

    return jsonify({
        'message': 'Payment processed successfully',
        'payment_id': payment.id,
        'booking_id': booking_id,
        'amount': amount
    }), 200


@coocook_bp.route('/bookings/<int:booking_id>/review', methods=['POST'])
@require_auth
@require_subscription('coocook')
def submit_review(booking_id):
    """Submit a review for a completed booking"""
    booking = Booking.query.get(booking_id)

    if not booking:
        return jsonify({'error': 'Booking not found'}), 404

    if booking.user_id != g.user_id:
        return jsonify({'error': 'Not authorized'}), 403

    if booking.status != 'completed':
        return jsonify({'error': 'Can only review completed bookings'}), 400

    data = request.get_json()
    rating = int(data.get('rating', 5))
    comment = data.get('comment', '')

    # Validate rating
    if rating < 1 or rating > 5:
        return jsonify({'error': 'Rating must be between 1 and 5'}), 400

    # Check if already reviewed
    from ..models import BookingReview
    existing = BookingReview.query.filter_by(booking_id=booking_id).first()
    if existing:
        return jsonify({'error': 'Already reviewed'}), 400

    # Create review
    review = BookingReview(
        booking_id=booking_id,
        user_id=g.user_id,
        chef_id=booking.chef_id,
        rating=rating,
        comment=comment
    )

    # Update chef rating
    chef = booking.chef
    new_rating = (chef.rating * chef.rating_count + rating) / (chef.rating_count + 1)
    chef.rating = new_rating
    chef.rating_count += 1

    db.session.add(review)
    db.session.commit()

    return jsonify({
        'message': 'Review submitted successfully',
        'review_id': review.id,
        'chef_rating': chef.rating,
        'rating_count': chef.rating_count
    }), 201


@coocook_bp.route('/chefs/<int:chef_id>/reviews', methods=['GET'])
def get_chef_reviews(chef_id):
    """Get reviews for a chef"""
    chef = Chef.query.get(chef_id)

    if not chef:
        return jsonify({'error': 'Chef not found'}), 404

    from ..models import BookingReview
    reviews = BookingReview.query.filter_by(chef_id=chef_id).all()

    reviews_data = []
    for review in reviews:
        reviews_data.append({
            'id': review.id,
            'user_id': review.user_id,
            'rating': review.rating,
            'comment': review.comment,
            'created_at': review.created_at.isoformat(),
        })

    return jsonify({
        'chef_id': chef_id,
        'chef_name': chef.name,
        'average_rating': chef.rating,
        'total_reviews': chef.rating_count,
        'reviews': reviews_data
    }), 200
