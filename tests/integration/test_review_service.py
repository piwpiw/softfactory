"""
Test Suite for Review Service Endpoints
Team E: 체험단 모음 통합 (Experience Listing Aggregation)
"""

import pytest
from datetime import datetime, timedelta
import json


class TestAggregatedListings:
    """Test /api/review/aggregated endpoints"""

    def test_get_aggregated_listings_basic(self, client, db):
        """Test basic aggregated listings retrieval"""
        from backend.models import ReviewListing

        listing1 = ReviewListing(
            source_platform='revu',
            external_id='revu_001',
            title='Beauty Product Review',
            brand='GlowSkin',
            category='beauty',
            reward_type='상품',
            reward_value=50000,
            deadline=datetime.utcnow() + timedelta(days=30),
            status='active'
        )
        db.session.add(listing1)
        db.session.commit()

        response = client.get('/api/review/aggregated')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['total'] >= 1


class TestDaangnStub:
    """Test Daangn stub endpoint"""

    def test_daangn_nearby_missing_params(self, client):
        """Test Daangn endpoint missing params"""
        response = client.get('/api/review/daangn/nearby')
        assert response.status_code == 400

    def test_daangn_nearby_success(self, client):
        """Test Daangn endpoint with valid params"""
        response = client.get('/api/review/daangn/nearby?lat=37.5&lng=126.9')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
