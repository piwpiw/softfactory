import json
from datetime import date, timedelta

from backend.models import db, Booking, Chef, User


def seed_booking(app):
    with app.app_context():
        user = db.session.get(User, 1)
        if user is None:
            user = User(id=1, email='demo@softfactory.com', name='Demo User', email_verified=True)
            user.set_password('demo123')
            db.session.add(user)

        chef_user = db.session.get(User, 2)
        if chef_user is None:
            chef_user = User(id=2, email='chef@example.com', name='Chef Owner', email_verified=True)
            chef_user.set_password('chef123')
            db.session.add(chef_user)

        db.session.flush()

        chef = db.session.get(Chef, 1)
        if chef is None:
            chef = Chef(
                id=1,
                user_id=chef_user.id,
                name='Chef Park',
                bio='Korean cuisine specialist',
                cuisine_type='Korean',
                location='Seoul',
                price_per_session=120.0,
                is_active=True,
            )
            db.session.add(chef)
            db.session.flush()

        booking = Booking(
            user_id=user.id,
            chef_id=chef.id,
            booking_date=date.today() + timedelta(days=5),
            duration_hours=2,
            status='confirmed',
            total_price=240.0,
            special_requests='Less spicy please',
        )
        db.session.add(booking)
        db.session.commit()
        return booking.id


def test_booking_owner_can_reschedule_and_total_is_recalculated(app, client, auth_headers):
    booking_id = seed_booking(app)
    next_date = date.today() + timedelta(days=9)

    response = client.put(
        f'/api/coocook/bookings/{booking_id}',
        headers=auth_headers,
        json={'booking_date': next_date.isoformat(), 'duration_hours': 3},
    )

    assert response.status_code == 200
    data = json.loads(response.data)
    booking = data['booking']
    assert booking['booking_date'] == next_date.isoformat()
    assert booking['duration_hours'] == 3
    assert booking['total_price'] == 360.0
    assert booking['cuisine'] == 'Korean'
    assert booking['location'] == 'Seoul'


def test_booking_owner_can_cancel_booking(app, client, auth_headers):
    booking_id = seed_booking(app)

    response = client.put(
        f'/api/coocook/bookings/{booking_id}',
        headers=auth_headers,
        json={'status': 'cancelled', 'special_requests': 'Customer requested cancellation'},
    )

    assert response.status_code == 200
    data = json.loads(response.data)
    booking = data['booking']
    assert booking['status'] == 'cancelled'
    assert booking['special_requests'] == 'Customer requested cancellation'
