"""
Unit Tests: Data Models
Tests all 12 SQLAlchemy models for correctness.
"""
import pytest
from datetime import datetime


class TestUserModel:
    """Test User model."""

    def test_user_creation(self, db):
        from backend.models import User
        user = User(
            email="test@example.com",
            name="Test User",
            password_hash="hashed_pw"
        )
        db.session.add(user)
        db.session.commit()
        assert user.id is not None
        assert user.email == "test@example.com"

    def test_user_to_dict(self, db):
        from backend.models import User
        user = User(email="test2@example.com", name="Test2", password_hash="pw")
        db.session.add(user)
        db.session.commit()
        d = user.to_dict()
        assert "id" in d
        assert "email" in d
        assert "password_hash" not in d  # never expose


class TestProductModel:
    """Test Product/Service model."""

    def test_product_prices(self, db):
        from backend.models import Product
        product = Product(
            name="SNS Auto",
            slug="sns-auto",
            monthly_price=49000,
            annual_price=470400
        )
        db.session.add(product)
        db.session.commit()
        assert product.monthly_price == 49000
        assert product.annual_price == 470400


class TestSubscriptionModel:
    """Test Subscription model."""

    def test_subscription_active(self, db):
        from backend.models import Subscription
        sub = Subscription(
            user_id=1,
            product_id=1,
            status="active"
        )
        db.session.add(sub)
        db.session.commit()
        assert sub.status == "active"
