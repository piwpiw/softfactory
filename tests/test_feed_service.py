"""Tests for CooCook Feed Service"""
import pytest
from datetime import datetime
from backend.models import (
    db, User, Recipe, RecipeReview, RecipeLike, UserFollow, Feed, CookingSession
)
from backend.services.feed_service import FeedService
from flask import Flask


@pytest.fixture
def app():
    """Create Flask app for testing"""
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['TESTING'] = True
    db.init_app(app)

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


def test_post_review(app):
    """Test posting a recipe review"""
    with app.app_context():
        # Create test user and recipe
        user = User(email='test@test.com', name='Test User', password_hash='hash')
        chef = User(email='chef@test.com', name='Chef', password_hash='hash')
        recipe = Recipe(
            title='Test Recipe',
            name='Test Recipe',
            cuisine='Korean',
            difficulty='easy',
            prep_time=30,
            servings=2,
            ingredients_json=[],
            chef_id=1
        )

        db.session.add_all([user, chef, recipe])
        db.session.commit()

        # Test review posting
        result = FeedService.post_review(
            recipe_id=recipe.id,
            user_id=user.id,
            rating=5,
            text='Delicious!',
            photos=[]
        )

        assert result['success'] is True
        assert result['review_id'] is not None


def test_like_recipe(app):
    """Test liking a recipe"""
    with app.app_context():
        # Create test data
        user = User(email='test@test.com', name='Test User', password_hash='hash')
        chef = User(email='chef@test.com', name='Chef', password_hash='hash')
        recipe = Recipe(
            title='Test Recipe',
            name='Test Recipe',
            cuisine='Korean',
            difficulty='easy',
            prep_time=30,
            servings=2,
            ingredients_json=[],
            chef_id=1
        )

        db.session.add_all([user, chef, recipe])
        db.session.commit()

        # Test liking
        result = FeedService.like_recipe(recipe.id, user.id)
        assert result['success'] is True
        assert result['liked'] is True

        # Test unliking
        result = FeedService.like_recipe(recipe.id, user.id)
        assert result['success'] is True
        assert result['liked'] is False


def test_follow_chef(app):
    """Test following a chef"""
    with app.app_context():
        # Create test users
        user = User(email='test@test.com', name='Test User', password_hash='hash')
        chef = User(email='chef@test.com', name='Chef', password_hash='hash')
        chef_profile = Chef(user_id=1, name='Chef', cuisine_type='Korean', price_per_session=100)

        db.session.add_all([user, chef, chef_profile])
        db.session.commit()

        # Test following
        result = FeedService.follow_chef(chef_profile.id, user.id)
        assert result['success'] is True
        assert result['following'] is True

        # Test unfollowing
        result = FeedService.follow_chef(chef_profile.id, user.id)
        assert result['success'] is True
        assert result['following'] is False


def test_get_user_profile(app):
    """Test getting user profile"""
    with app.app_context():
        # Create test user
        user = User(email='test@test.com', name='Test User', password_hash='hash')
        db.session.add(user)
        db.session.commit()

        # Get profile
        result = FeedService.get_user_profile(user.id)
        assert result['success'] is True
        assert 'user' in result
        assert 'stats' in result
        assert result['stats']['reviews_posted'] == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
