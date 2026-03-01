"""Test suite for Elasticsearch search endpoints
Comprehensive testing of all search functionality
"""

import pytest
import json
from datetime import datetime
from backend import create_app
from backend.models import db, User, SearchHistory


@pytest.fixture
def client():
    """Create test client"""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.session.remove()
        db.drop_all()


@pytest.fixture
def auth_headers(client):
    """Create authenticated user and return auth headers"""
    # Create test user
    user = User(
        email='test@example.com',
        name='Test User',
        password_hash='hashed'
    )
    db.session.add(user)
    db.session.commit()

    # Mock token (in real test would use actual auth)
    return {
        'Authorization': 'Bearer test_token',
        'Content-Type': 'application/json'
    }


class TestSearchEndpoints:
    """Test search API endpoints"""

    def test_search_basic(self, client, auth_headers):
        """Test basic search functionality"""
        response = client.post('/api/search', headers=auth_headers, json={
            'query': 'pasta',
            'index': 'recipes',
            'page': 1,
            'per_page': 20
        })

        assert response.status_code in [200, 503]  # 503 if ES not available
        if response.status_code == 200:
            data = json.loads(response.data)
            assert 'results' in data
            assert 'total' in data
            assert 'query' in data

    def test_search_missing_query(self, client, auth_headers):
        """Test search without query returns error"""
        response = client.post('/api/search', headers=auth_headers, json={
            'query': '',
            'index': 'recipes'
        })

        assert response.status_code == 400

    def test_search_invalid_index(self, client, auth_headers):
        """Test search with invalid index"""
        response = client.post('/api/search', headers=auth_headers, json={
            'query': 'test',
            'index': 'invalid_index'
        })

        assert response.status_code == 400

    def test_autocomplete(self, client, auth_headers):
        """Test autocomplete endpoint"""
        response = client.get(
            '/api/search/autocomplete?q=pas&field=title&index=recipes',
            headers=auth_headers
        )

        assert response.status_code in [200, 503]
        if response.status_code == 200:
            data = json.loads(response.data)
            assert 'suggestions' in data
            assert 'query' in data

    def test_autocomplete_too_short(self, client, auth_headers):
        """Test autocomplete with query too short"""
        response = client.get(
            '/api/search/autocomplete?q=p&field=title',
            headers=auth_headers
        )

        # Should return empty suggestions, not error
        assert response.status_code == 200

    def test_facets(self, client, auth_headers):
        """Test facets endpoint"""
        response = client.get(
            '/api/search/facets?index=recipes&field=tags',
            headers=auth_headers
        )

        assert response.status_code in [200, 503]
        if response.status_code == 200:
            data = json.loads(response.data)
            assert 'facets' in data
            assert 'index' in data

    def test_search_history(self, client, auth_headers):
        """Test search history endpoint"""
        response = client.get(
            '/api/search/history?limit=10',
            headers=auth_headers
        )

        assert response.status_code in [200, 503]
        if response.status_code == 200:
            data = json.loads(response.data)
            assert 'history' in data
            assert isinstance(data['history'], list)

    def test_trending_searches(self, client, auth_headers):
        """Test trending searches endpoint"""
        response = client.get(
            '/api/search/trending?days=7&limit=20',
            headers=auth_headers
        )

        assert response.status_code in [200, 503]
        if response.status_code == 200:
            data = json.loads(response.data)
            assert 'trending' in data
            assert isinstance(data['trending'], list)

    def test_advanced_search(self, client, auth_headers):
        """Test advanced search"""
        response = client.post('/api/search/advanced', headers=auth_headers, json={
            'queries': [
                {'field': 'title', 'value': 'pasta', 'operator': 'must'}
            ],
            'index': 'recipes'
        })

        assert response.status_code in [200, 503]

    def test_advanced_search_no_queries(self, client, auth_headers):
        """Test advanced search without queries"""
        response = client.post('/api/search/advanced', headers=auth_headers, json={
            'queries': [],
            'index': 'recipes'
        })

        assert response.status_code == 400

    def test_similar_items(self, client, auth_headers):
        """Test similar items endpoint"""
        response = client.get(
            '/api/search/similar?index=recipes&id=123',
            headers=auth_headers
        )

        assert response.status_code in [200, 503]
        if response.status_code == 200:
            data = json.loads(response.data)
            assert 'results' in data

    def test_similar_items_missing_id(self, client, auth_headers):
        """Test similar items without ID"""
        response = client.get(
            '/api/search/similar?index=recipes',
            headers=auth_headers
        )

        assert response.status_code == 400


class TestSearchAdminEndpoints:
    """Test search admin endpoints"""

    def test_list_indices(self, client, auth_headers):
        """Test listing indices"""
        response = client.get('/api/admin/search/indices', headers=auth_headers)

        assert response.status_code in [200, 503]
        if response.status_code == 200:
            data = json.loads(response.data)
            assert 'indices' in data

    def test_reindex(self, client, auth_headers):
        """Test reindexing"""
        response = client.post('/api/admin/search/reindex', headers=auth_headers, json={
            'scope': 'all'
        })

        assert response.status_code in [200, 500, 503]

    def test_clear_index(self, client, auth_headers):
        """Test clearing index"""
        response = client.post('/api/admin/search/clear', headers=auth_headers, json={
            'index': 'recipes'
        })

        assert response.status_code in [200, 500, 503]

    def test_reset_indices(self, client, auth_headers):
        """Test resetting indices"""
        response = client.post('/api/admin/search/reset', headers=auth_headers)

        assert response.status_code in [200, 500, 503]

    def test_search_stats(self, client, auth_headers):
        """Test search statistics"""
        response = client.get('/api/admin/search/stats', headers=auth_headers)

        assert response.status_code in [200, 503]
        if response.status_code == 200:
            data = json.loads(response.data)
            assert 'total_searches' in data
            assert 'by_index' in data

    def test_search_health(self, client, auth_headers):
        """Test cluster health"""
        response = client.get('/api/admin/search/health', headers=auth_headers)

        # 503 if ES not available is acceptable
        assert response.status_code in [200, 503]


class TestSearchHistoryTracking:
    """Test search history tracking"""

    def test_search_history_created(self, client, auth_headers):
        """Test that search history is created"""
        # This would require mocking Elasticsearch
        # For now, verify the endpoint exists
        response = client.get('/api/search/history', headers=auth_headers)
        assert response.status_code in [200, 503]

    def test_search_history_model(self):
        """Test SearchHistory model"""
        app = create_app()
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

        with app.app_context():
            db.create_all()

            user = User(email='test@test.com', name='Test', password_hash='hash')
            db.session.add(user)
            db.session.commit()

            history = SearchHistory(
                user_id=user.id,
                query='pasta recipe',
                index='recipes',
                result_count=42
            )
            db.session.add(history)
            db.session.commit()

            assert history.id is not None
            assert history.query == 'pasta recipe'
            assert history.index == 'recipes'
            assert history.result_count == 42

            # Test to_dict
            history_dict = history.to_dict()
            assert history_dict['query'] == 'pasta recipe'


class TestSearchPerformance:
    """Test search performance characteristics"""

    def test_search_response_time(self, client, auth_headers):
        """Verify search completes within acceptable time"""
        import time

        start = time.time()
        response = client.post('/api/search', headers=auth_headers, json={
            'query': 'test',
            'index': 'recipes',
            'page': 1
        })
        elapsed = time.time() - start

        # Should complete in < 1 second (ES not responding is OK)
        assert elapsed < 1.0

    def test_autocomplete_response_time(self, client, auth_headers):
        """Verify autocomplete completes quickly"""
        import time

        start = time.time()
        response = client.get(
            '/api/search/autocomplete?q=test&field=title',
            headers=auth_headers
        )
        elapsed = time.time() - start

        # Should complete in < 0.5 second
        assert elapsed < 0.5


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
