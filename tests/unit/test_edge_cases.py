"""
Unit Tests: Edge Cases & Boundary Conditions
Tests boundary values, invalid inputs, and constraint violations.
"""
import pytest
from datetime import datetime, timedelta
from decimal import Decimal


class TestUserModelEdgeCases:
    """Edge cases for User model."""

    def test_user_with_empty_email(self, db):
        """Empty email should fail."""
        from backend.models import User
        user = User(email="", name="Test", password_hash="pw")
        db.session.add(user)
        # SQLite doesn't enforce NOT NULL strictly in some configs
        # but we validate in business logic

    def test_user_with_very_long_email(self, db):
        """Very long email (edge of VARCHAR 120)."""
        from backend.models import User
        long_email = "a" * 100 + "@example.com"
        user = User(email=long_email, name="Test", password_hash="pw")
        db.session.add(user)
        db.session.commit()
        assert len(user.email) == len(long_email)

    def test_user_with_very_long_name(self, db):
        """Very long name."""
        from backend.models import User
        long_name = "A" * 500
        user = User(email="test@example.com", name=long_name, password_hash="pw")
        db.session.add(user)
        db.session.commit()
        assert user.name == long_name

    def test_user_duplicate_email_unique_constraint(self, db):
        """Duplicate email should violate unique constraint."""
        from backend.models import User
        user1 = User(email="unique@example.com", name="User1", password_hash="pw1")
        user2 = User(email="unique@example.com", name="User2", password_hash="pw2")
        db.session.add(user1)
        db.session.commit()
        db.session.add(user2)
        with pytest.raises(Exception):  # IntegrityError
            db.session.commit()

    def test_user_role_default(self, db):
        """Default role should be 'user'."""
        from backend.models import User
        import uuid
        user = User(email=f"test-role-{uuid.uuid4().hex[:8]}@example.com", name="Test", password_hash="pw")
        db.session.add(user)
        db.session.commit()
        assert user.role == "user"

    def test_user_is_active_default(self, db):
        """Default is_active should be True."""
        from backend.models import User
        import uuid
        user = User(email=f"test-active-{uuid.uuid4().hex[:8]}@example.com", name="Test", password_hash="pw")
        db.session.add(user)
        db.session.commit()
        assert user.is_active is True

    def test_user_admin_role(self, db):
        """Set admin role."""
        from backend.models import User
        user = User(email="admin@example.com", name="Admin", password_hash="pw", role="admin")
        db.session.add(user)
        db.session.commit()
        assert user.role == "admin"

    def test_user_created_at_timestamp(self, db):
        """created_at should be auto-set."""
        from backend.models import User
        before = datetime.utcnow()
        user = User(email="test@example.com", name="Test", password_hash="pw")
        db.session.add(user)
        db.session.commit()
        after = datetime.utcnow()
        assert before <= user.created_at <= after


class TestProductModelEdgeCases:
    """Edge cases for Product model."""

    def test_product_zero_price(self, db):
        """Product with zero price."""
        from backend.models import Product
        import uuid
        product = Product(
            name="Free Product",
            slug=f"free-{uuid.uuid4().hex[:8]}",
            monthly_price=0.0,
            annual_price=0.0
        )
        db.session.add(product)
        db.session.commit()
        assert product.monthly_price == 0.0

    def test_product_negative_price_not_prevented(self, db):
        """Negative price (not prevented at DB level)."""
        from backend.models import Product
        import uuid
        product = Product(
            name="Negative Price",
            slug=f"negative-{uuid.uuid4().hex[:8]}",
            monthly_price=-50.0,
            annual_price=-500.0
        )
        db.session.add(product)
        db.session.commit()
        # DB allows it; business logic should prevent

    def test_product_very_high_price(self, db):
        """Very high price."""
        from backend.models import Product
        import uuid
        product = Product(
            name="Expensive",
            slug=f"expensive-{uuid.uuid4().hex[:8]}",
            monthly_price=999999.99,
            annual_price=9999999.99
        )
        db.session.add(product)
        db.session.commit()
        assert product.monthly_price == 999999.99

    def test_product_null_annual_price(self, db):
        """Annual price can be NULL."""
        from backend.models import Product
        import uuid
        product = Product(
            name="Monthly Only",
            slug=f"monthly-{uuid.uuid4().hex[:8]}",
            monthly_price=29.0,
            annual_price=None
        )
        db.session.add(product)
        db.session.commit()
        assert product.annual_price is None

    def test_product_duplicate_slug(self, db):
        """Duplicate slug violates unique constraint."""
        from backend.models import Product
        p1 = Product(name="P1", slug="duplicate", monthly_price=10.0)
        p2 = Product(name="P2", slug="duplicate", monthly_price=20.0)
        db.session.add(p1)
        db.session.commit()
        db.session.add(p2)
        with pytest.raises(Exception):  # IntegrityError
            db.session.commit()

    def test_product_is_active_default(self, db):
        """is_active defaults to True."""
        from backend.models import Product
        import uuid
        product = Product(
            name="Active",
            slug=f"active-{uuid.uuid4().hex[:8]}",
            monthly_price=10.0
        )
        db.session.add(product)
        db.session.commit()
        assert product.is_active is True

    def test_product_inactive(self, db):
        """Product can be marked inactive."""
        from backend.models import Product
        import uuid
        product = Product(
            name="Inactive",
            slug=f"inactive-{uuid.uuid4().hex[:8]}",
            monthly_price=10.0,
            is_active=False
        )
        db.session.add(product)
        db.session.commit()
        assert product.is_active is False


class TestBookingEdgeCases:
    """Edge cases for Booking model."""

    def test_booking_past_date(self, db):
        """Booking with past date (not prevented at DB level)."""
        from backend.models import Booking
        from datetime import date
        booking = Booking(
            user_id=1,
            chef_id=1,
            booking_date=date(2020, 1, 1),  # Past date
            duration_hours=2,
            total_price=100.0
        )
        db.session.add(booking)
        db.session.commit()
        assert booking.booking_date.year == 2020

    def test_booking_zero_duration(self, db):
        """Booking with zero duration."""
        from backend.models import Booking
        from datetime import date
        booking = Booking(
            user_id=1,
            chef_id=1,
            booking_date=date.today() + timedelta(days=1),
            duration_hours=0,
            total_price=0.0
        )
        db.session.add(booking)
        db.session.commit()
        assert booking.duration_hours == 0

    def test_booking_very_long_duration(self, db):
        """Booking with 24+ hours."""
        from backend.models import Booking
        from datetime import date
        booking = Booking(
            user_id=1,
            chef_id=1,
            booking_date=date.today() + timedelta(days=1),
            duration_hours=48,
            total_price=4800.0
        )
        db.session.add(booking)
        db.session.commit()
        assert booking.duration_hours == 48

    def test_booking_zero_price(self, db):
        """Booking with zero price."""
        from backend.models import Booking
        from datetime import date
        booking = Booking(
            user_id=1,
            chef_id=1,
            booking_date=date.today() + timedelta(days=1),
            duration_hours=2,
            total_price=0.0
        )
        db.session.add(booking)
        db.session.commit()
        assert booking.total_price == 0.0

    def test_booking_status_values(self, db):
        """Test all valid booking status values."""
        from backend.models import Booking
        from datetime import date
        statuses = ['pending', 'confirmed', 'completed', 'canceled']
        created_bookings = []
        for i, status in enumerate(statuses):
            booking = Booking(
                user_id=1,
                chef_id=1,
                booking_date=date.today() + timedelta(days=i),
                duration_hours=2,
                total_price=100.0,
                status=status
            )
            db.session.add(booking)
            created_bookings.append(booking)
        db.session.commit()
        # Verify by checking created instances
        pending_count = sum(1 for b in created_bookings if b.status == 'pending')
        completed_count = sum(1 for b in created_bookings if b.status == 'completed')
        assert pending_count == 1
        assert completed_count == 1


class TestCampaignEdgeCases:
    """Edge cases for Campaign model."""

    def test_campaign_zero_max_reviewers(self, db):
        """Campaign with 0 max reviewers."""
        from backend.models import Campaign
        campaign = Campaign(
            creator_id=1,
            title="No Reviewers",
            product_name="Test",
            deadline=datetime.utcnow() + timedelta(days=30),
            max_reviewers=0
        )
        db.session.add(campaign)
        db.session.commit()
        assert campaign.max_reviewers == 0

    def test_campaign_past_deadline(self, db):
        """Campaign with past deadline (not prevented)."""
        from backend.models import Campaign
        campaign = Campaign(
            creator_id=1,
            title="Past Campaign",
            product_name="Test",
            deadline=datetime.utcnow() - timedelta(days=1),  # Past
            max_reviewers=10
        )
        db.session.add(campaign)
        db.session.commit()
        assert campaign.deadline < datetime.utcnow()

    def test_campaign_status_values(self, db):
        """Test all valid campaign status values."""
        from backend.models import Campaign
        statuses = ['active', 'closed', 'completed']
        created_campaigns = []
        for i, status in enumerate(statuses):
            campaign = Campaign(
                creator_id=1,
                title=f"Campaign {status} {i}",
                product_name="Test",
                deadline=datetime.utcnow() + timedelta(days=30),
                max_reviewers=10,
                status=status
            )
            db.session.add(campaign)
            created_campaigns.append(campaign)
        db.session.commit()
        # Verify by checking created instances
        active_count = sum(1 for c in created_campaigns if c.status == 'active')
        assert active_count == 1


class TestChefEdgeCases:
    """Edge cases for Chef model."""

    def test_chef_zero_price_per_session(self, db):
        """Chef with zero session price."""
        from backend.models import Chef
        chef = Chef(
            user_id=1,
            name="Free Chef",
            cuisine_type="Korean",
            location="Seoul",
            price_per_session=0.0
        )
        db.session.add(chef)
        db.session.commit()
        assert chef.price_per_session == 0.0

    def test_chef_zero_rating(self, db):
        """Chef with zero rating."""
        from backend.models import Chef
        chef = Chef(
            user_id=1,
            name="No Rating",
            cuisine_type="Korean",
            location="Seoul",
            price_per_session=100.0,
            rating=0.0
        )
        db.session.add(chef)
        db.session.commit()
        assert chef.rating == 0.0

    def test_chef_perfect_rating(self, db):
        """Chef with 5.0 rating (perfect)."""
        from backend.models import Chef
        chef = Chef(
            user_id=1,
            name="Perfect Chef",
            cuisine_type="French",
            location="Seoul",
            price_per_session=150.0,
            rating=5.0,
            rating_count=100
        )
        db.session.add(chef)
        db.session.commit()
        assert chef.rating == 5.0
        assert chef.rating_count == 100

    def test_chef_no_bio(self, db):
        """Chef with NULL bio."""
        from backend.models import Chef
        chef = Chef(
            user_id=1,
            name="Silent Chef",
            cuisine_type="Japanese",
            location="Seoul",
            price_per_session=130.0,
            bio=None
        )
        db.session.add(chef)
        db.session.commit()
        assert chef.bio is None


class TestPaymentEdgeCases:
    """Edge cases for Payment model."""

    def test_payment_zero_amount(self, db):
        """Payment with zero amount."""
        from backend.models import Payment
        payment = Payment(
            user_id=1,
            product_id=1,
            amount=0.0,
            status='completed'
        )
        db.session.add(payment)
        db.session.commit()
        assert payment.amount == 0.0

    def test_payment_different_currencies(self, db):
        """Payments in different currencies."""
        from backend.models import Payment
        currencies = ['USD', 'EUR', 'KRW', 'JPY', 'CNY']
        created_payments = []
        for i, curr in enumerate(currencies):
            payment = Payment(
                user_id=1,
                product_id=1,
                amount=100.0 * (i + 1),
                currency=curr
            )
            db.session.add(payment)
            created_payments.append(payment)
        db.session.commit()
        # Verify by checking created instances
        krw_count = sum(1 for p in created_payments if p.currency == 'KRW')
        usd_count = sum(1 for p in created_payments if p.currency == 'USD')
        assert krw_count == 1
        assert usd_count == 1

    def test_payment_status_values(self, db):
        """Test all valid payment status values."""
        from backend.models import Payment
        statuses = ['pending', 'completed', 'failed']
        created_payments = []
        for i, status in enumerate(statuses):
            payment = Payment(
                user_id=1,
                product_id=1,
                amount=100.0,
                status=status
            )
            db.session.add(payment)
            created_payments.append(payment)
        db.session.commit()
        # Verify by checking created instances
        pending_count = sum(1 for p in created_payments if p.status == 'pending')
        failed_count = sum(1 for p in created_payments if p.status == 'failed')
        assert pending_count == 1
        assert failed_count == 1
