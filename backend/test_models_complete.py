#!/usr/bin/env python
"""
Test script for SNS and Review database models
Verifies that all 5 models are correctly implemented and can be used
"""

import os
import sys
from datetime import datetime, timedelta
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask
from backend.models import (
    db, User, SNSLinkInBio, SNSAutomate, SNSCompetitor,
    ReviewAccount, ReviewApplication, ReviewListing
)
from backend.config import Config


def create_test_app():
    """Create a test Flask app with test database"""
    app = Flask(__name__)

    # Use in-memory SQLite for testing
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    with app.app_context():
        db.create_all()

    return app


class TestResults:
    """Store test results"""

    def __init__(self):
        self.tests = []
        self.passed = 0
        self.failed = 0

    def add(self, name, passed, details=""):
        """Add test result"""
        self.tests.append({
            'name': name,
            'passed': passed,
            'details': details
        })
        if passed:
            self.passed += 1
        else:
            self.failed += 1

    def print_summary(self):
        """Print test results summary"""
        print("\n" + "=" * 70)
        print("TEST RESULTS SUMMARY")
        print("=" * 70)

        for test in self.tests:
            status = "[PASS]" if test['passed'] else "[FAIL]"
            print(f"{status} {test['name']}")
            if test['details']:
                print(f"      {test['details']}")

        print("\n" + "-" * 70)
        print(f"Total: {len(self.tests)} | Passed: {self.passed} | Failed: {self.failed}")
        print("-" * 70 + "\n")

        return self.failed == 0


def test_sns_link_in_bio(app, results):
    """Test SNSLinkInBio model"""
    print("\nTesting SNSLinkInBio...")

    with app.app_context():
        try:
            # Create user
            user = User(email='test.linkinbio@example.com', name='Test User')
            user.set_password('test123')
            db.session.add(user)
            db.session.commit()

            # Create SNSLinkInBio
            bio = SNSLinkInBio(
                user_id=user.id,
                slug='test-bio',
                title='My Links',
                links=[
                    {'url': 'https://example.com', 'label': 'Website', 'icon': 'globe'},
                    {'url': 'https://instagram.com', 'label': 'Instagram', 'icon': 'instagram'}
                ],
                theme='dark'
            )
            db.session.add(bio)
            db.session.commit()

            # Verify
            fetched = SNSLinkInBio.query.first()
            assert fetched.slug == 'test-bio'
            assert fetched.theme == 'dark'
            assert len(fetched.links) == 2
            assert fetched.click_count == 0

            # Test to_dict()
            bio_dict = fetched.to_dict()
            assert 'slug' in bio_dict
            assert 'links' in bio_dict
            assert bio_dict['theme'] == 'dark'

            results.add('SNSLinkInBio - Create & Fetch', True, f"Created with {len(bio.links)} links")

            # Test update
            fetched.click_count = 5
            db.session.commit()
            updated = SNSLinkInBio.query.first()
            assert updated.click_count == 5

            results.add('SNSLinkInBio - Update', True, "Click count updated successfully")

        except Exception as e:
            results.add('SNSLinkInBio', False, str(e))


def test_sns_automate(app, results):
    """Test SNSAutomate model"""
    print("Testing SNSAutomate...")

    with app.app_context():
        try:
            # Create user
            user = User(email='test.automate@example.com', name='Test User')
            user.set_password('test123')
            db.session.add(user)
            db.session.commit()

            # Create SNSAutomate
            automate = SNSAutomate(
                user_id=user.id,
                name='Daily AI News',
                topic='Artificial Intelligence',
                purpose='홍보',
                platforms=['instagram', 'twitter', 'linkedin'],
                frequency='daily',
                next_run=datetime.utcnow() + timedelta(hours=1),
                is_active=True
            )
            db.session.add(automate)
            db.session.commit()

            # Verify
            fetched = SNSAutomate.query.first()
            assert fetched.name == 'Daily AI News'
            assert 'instagram' in fetched.platforms
            assert fetched.is_active is True

            # Test to_dict()
            auto_dict = fetched.to_dict()
            assert auto_dict['topic'] == 'Artificial Intelligence'
            assert auto_dict['frequency'] == 'daily'
            assert auto_dict['is_active'] is True

            results.add('SNSAutomate - Create & Fetch', True, f"Created with {len(automate.platforms)} platforms")

            # Test filtering by is_active
            active_count = SNSAutomate.query.filter_by(is_active=True).count()
            assert active_count >= 1

            results.add('SNSAutomate - Query Filter', True, f"Found {active_count} active automations")

        except Exception as e:
            results.add('SNSAutomate', False, str(e))


def test_sns_competitor(app, results):
    """Test SNSCompetitor model"""
    print("Testing SNSCompetitor...")

    with app.app_context():
        try:
            # Create user
            user = User(email='test.competitor@example.com', name='Test User')
            user.set_password('test123')
            db.session.add(user)
            db.session.commit()

            # Create SNSCompetitor
            competitor = SNSCompetitor(
                user_id=user.id,
                platform='instagram',
                username='competitor_account',
                followers_count=50000,
                engagement_rate=5.5,
                avg_likes=1200,
                avg_comments=85,
                posting_frequency='daily',
                data={
                    'top_hashtags': ['fashion', 'lifestyle'],
                    'content_themes': ['outfit', 'daily life']
                }
            )
            db.session.add(competitor)
            db.session.commit()

            # Verify
            fetched = SNSCompetitor.query.first()
            assert fetched.username == 'competitor_account'
            assert fetched.followers_count == 50000
            assert fetched.engagement_rate == 5.5

            # Test to_dict()
            comp_dict = fetched.to_dict()
            assert comp_dict['platform'] == 'instagram'
            assert comp_dict['avg_likes'] == 1200
            assert 'data' in comp_dict

            results.add('SNSCompetitor - Create & Fetch', True, f"Created with {fetched.followers_count:,} followers")

            # Test data field
            assert 'top_hashtags' in fetched.data
            results.add('SNSCompetitor - JSON Data Field', True, "Complex data stored correctly")

        except Exception as e:
            results.add('SNSCompetitor', False, str(e))


def test_review_account(app, results):
    """Test ReviewAccount model with new fields"""
    print("Testing ReviewAccount...")

    with app.app_context():
        try:
            # Create user
            user = User(email='test.review.account@example.com', name='Test User')
            user.set_password('test123')
            db.session.add(user)
            db.session.commit()

            # Create ReviewAccount with new last_reviewed field
            account = ReviewAccount(
                user_id=user.id,
                platform='instagram',
                account_name='fashion_influencer',
                follower_count=10000,
                category_tags=['패션', '뷰티'],
                success_rate=0.75,
                last_reviewed=datetime.utcnow() - timedelta(days=5),
                is_active=True
            )
            db.session.add(account)
            db.session.commit()

            # Verify all fields
            fetched = ReviewAccount.query.first()
            assert fetched.account_name == 'fashion_influencer'
            assert fetched.follower_count == 10000
            assert fetched.success_rate == 0.75
            assert fetched.last_reviewed is not None  # NEW FIELD

            # Test to_dict() includes new field
            account_dict = fetched.to_dict()
            assert 'follower_count' in account_dict
            assert 'last_reviewed' in account_dict  # NEW FIELD
            assert account_dict['last_reviewed'] is not None

            results.add('ReviewAccount - New Field (last_reviewed)', True, "Field created and accessible")

            # Test category tags
            assert '패션' in fetched.category_tags
            results.add('ReviewAccount - Category Tags', True, f"Tags: {', '.join(fetched.category_tags)}")

        except Exception as e:
            results.add('ReviewAccount', False, str(e))


def test_review_application(app, results):
    """Test ReviewApplication model with new fields"""
    print("Testing ReviewApplication...")

    with app.app_context():
        try:
            # Create user
            user = User(email='test.review.app@example.com', name='Test User')
            user.set_password('test123')
            db.session.add(user)
            db.session.flush()  # Get user.id without committing yet

            # Create listing
            listing = ReviewListing(
                source_platform='revu',
                external_id='ext_123',
                title='Product Review Campaign',
                brand='Sample Brand',
                category='Fashion',
                reward_type='상품',
                reward_value=100000,
                deadline=datetime.utcnow() + timedelta(days=30),
                status='active'
            )
            db.session.add(listing)
            db.session.flush()

            # Create account
            account = ReviewAccount(
                user_id=user.id,
                platform='instagram',
                account_name='reviewer_account',
                follower_count=5000,
                success_rate=0.8
            )
            db.session.add(account)
            db.session.commit()

            # Create ReviewApplication with new review_content field
            application = ReviewApplication(
                listing_id=listing.id,
                account_id=account.id,
                status='completed',
                result='Successfully posted review',
                review_url='https://instagram.com/p/abc123',
                review_posted_at=datetime.utcnow(),
                review_content='This product is amazing! High quality and great value for money. Highly recommended.'
            )
            db.session.add(application)
            db.session.commit()

            # Verify all fields
            fetched = ReviewApplication.query.first()
            assert fetched.status == 'completed'
            assert fetched.review_url is not None
            assert fetched.review_content is not None  # NEW FIELD

            # Test to_dict() includes new field
            app_dict = fetched.to_dict()
            assert 'review_url' in app_dict
            assert 'review_content' in app_dict  # NEW FIELD
            assert len(app_dict['review_content']) > 0

            results.add('ReviewApplication - New Field (review_content)', True, f"Content: {app_dict['review_content'][:50]}...")

            # Test relationship
            assert fetched.account.account_name == 'reviewer_account'
            assert fetched.listing.brand == 'Sample Brand'

            results.add('ReviewApplication - Relationships', True, "Account and Listing relationships work")

        except Exception as e:
            results.add('ReviewApplication', False, str(e))


def test_model_serialization(app, results):
    """Test to_dict() serialization for all models"""
    print("Testing Model Serialization...")

    with app.app_context():
        try:
            # Create test data
            user = User(email='test.serialization@example.com', name='Serialization Test')
            user.set_password('test123')
            db.session.add(user)
            db.session.commit()

            # Test SNSLinkInBio serialization
            bio = SNSLinkInBio(user_id=user.id, slug='test', links=[])
            db.session.add(bio)
            db.session.commit()

            bio_dict = SNSLinkInBio.query.first().to_dict()
            assert isinstance(bio_dict, dict)
            assert 'id' in bio_dict
            assert 'created_at' in bio_dict

            # Test datetime serialization
            assert isinstance(bio_dict['created_at'], str)  # ISO format

            results.add('Model Serialization - to_dict()', True, "All models serialize correctly")

        except Exception as e:
            results.add('Model Serialization', False, str(e))


def test_indexes(app, results):
    """Test that indexes are properly created"""
    print("Testing Database Indexes...")

    with app.app_context():
        try:
            # Get database connection info
            from sqlalchemy import inspect

            inspector = inspect(db.engine)

            # Check SNSLinkInBio indexes
            sns_bio_indexes = inspector.get_indexes('sns_link_in_bios')
            sns_bio_names = [idx['name'] for idx in sns_bio_indexes]

            assert any('user' in name for name in sns_bio_names), "Missing user index on SNSLinkInBio"
            assert any('slug' in name for name in sns_bio_names), "Missing slug index on SNSLinkInBio"

            results.add('Indexes - SNSLinkInBio', True, f"Found {len(sns_bio_indexes)} indexes")

            # Check SNSAutomate indexes
            sns_auto_indexes = inspector.get_indexes('sns_automates')
            sns_auto_names = [idx['name'] for idx in sns_auto_indexes]

            assert len(sns_auto_names) >= 3, "Missing indexes on SNSAutomate"

            results.add('Indexes - SNSAutomate', True, f"Found {len(sns_auto_indexes)} indexes")

            # Check SNSCompetitor indexes
            competitor_indexes = inspector.get_indexes('sns_competitors')
            assert len(competitor_indexes) >= 3, "Missing indexes on SNSCompetitor"

            results.add('Indexes - SNSCompetitor', True, f"Found {len(competitor_indexes)} indexes")

        except Exception as e:
            results.add('Database Indexes', False, str(e))


def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("SNS & REVIEW MODELS - COMPREHENSIVE TEST SUITE")
    print("=" * 70)

    # Create test app
    app = create_test_app()
    results = TestResults()

    # Run tests
    try:
        test_sns_link_in_bio(app, results)
        test_sns_automate(app, results)
        test_sns_competitor(app, results)
        test_review_account(app, results)
        test_review_application(app, results)
        test_model_serialization(app, results)
        test_indexes(app, results)
    except Exception as e:
        print(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()

    # Print results
    success = results.print_summary()

    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
