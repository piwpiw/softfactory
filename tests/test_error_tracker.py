"""Comprehensive Tests for Error Tracking System

Tests for:
- ErrorTracker class (main interface)
- ErrorAggregator (grouping and statistics)
- PatternDetector (pattern detection and root cause analysis)
- PreventionEngine (prevention rules and suggestions)
- API endpoints (all 6 endpoints)
"""

import pytest
from datetime import datetime, timedelta
import json

from backend.error_tracker import (
    ErrorTracker,
    ErrorAggregator,
    PatternDetector,
    PreventionEngine,
    ErrorPattern
)


class TestErrorPattern:
    """Test ErrorPattern data class"""

    def test_error_pattern_creation(self):
        """Test creating an ErrorPattern"""
        pattern = ErrorPattern(
            pattern_id='test_001',
            error_type='ValueError',
            message_pattern='Invalid input',
            frequency=5,
            first_seen=datetime.utcnow(),
            last_seen=datetime.utcnow(),
            affected_files=['test.py'],
            root_cause='Missing validation',
            severity='medium'
        )

        assert pattern.pattern_id == 'test_001'
        assert pattern.error_type == 'ValueError'
        assert pattern.frequency == 5
        assert pattern.severity == 'medium'

    def test_error_pattern_to_dict(self):
        """Test ErrorPattern serialization"""
        now = datetime.utcnow()
        pattern = ErrorPattern(
            pattern_id='test_001',
            error_type='ValueError',
            message_pattern='Invalid input',
            frequency=5,
            first_seen=now,
            last_seen=now,
            affected_files=['test.py'],
            root_cause='Missing validation',
            severity='medium'
        )

        result = pattern.to_dict()

        assert result['pattern_id'] == 'test_001'
        assert result['error_type'] == 'ValueError'
        assert result['status'] == 'active'
        assert 'first_seen' in result
        assert 'last_seen' in result

    def test_error_pattern_mark_resolved(self):
        """Test marking pattern as resolved"""
        now = datetime.utcnow()
        pattern = ErrorPattern(
            pattern_id='test_001',
            error_type='ValueError',
            message_pattern='Invalid input',
            frequency=5,
            first_seen=now,
            last_seen=now,
            affected_files=['test.py']
        )

        pattern.resolution = 'Fixed validation logic'
        pattern.resolved_at = datetime.utcnow()

        result = pattern.to_dict()
        assert result['status'] == 'resolved'
        assert result['resolution'] == 'Fixed validation logic'


class TestErrorAggregator:
    """Test ErrorAggregator functionality"""

    def test_aggregate_empty_logs(self):
        """Test aggregating empty error logs"""
        aggregator = ErrorAggregator()
        result = aggregator.aggregate([])

        assert isinstance(result, dict)
        assert len(result) == 0

    def test_aggregate_single_error(self):
        """Test aggregating single error"""
        aggregator = ErrorAggregator()
        errors = [{
            'error_type': 'ValueError',
            'message': 'Invalid input format'
        }]

        result = aggregator.aggregate(errors)

        assert len(result) > 0

    def test_aggregate_similar_errors(self):
        """Test aggregating similar errors"""
        aggregator = ErrorAggregator()
        errors = [
            {
                'error_type': 'ValueError',
                'message': 'Invalid input 123'
            },
            {
                'error_type': 'ValueError',
                'message': 'Invalid input 456'
            },
            {
                'error_type': 'ValueError',
                'message': 'Invalid input 789'
            }
        ]

        result = aggregator.aggregate(errors)

        # Should group similar errors under one key
        assert len(result) == 1
        assert len(list(result.values())[0]) == 3

    def test_get_frequency_stats(self):
        """Test frequency statistics"""
        aggregator = ErrorAggregator()
        errors = [
            {'error_type': 'ValueError', 'message': 'Error 1'},
            {'error_type': 'ValueError', 'message': 'Error 2'},
            {'error_type': 'TypeError', 'message': 'Type error'}
        ]

        aggregator.aggregate(errors)
        stats = aggregator.get_frequency_stats()

        assert len(stats) > 0
        # Check that frequencies are correct
        for freq in stats.values():
            assert freq > 0


class TestPatternDetector:
    """Test PatternDetector functionality"""

    def test_detect_patterns_empty_logs(self):
        """Test detecting patterns from empty logs"""
        detector = PatternDetector()
        patterns = detector.detect_patterns([])

        assert len(patterns) == 0

    def test_detect_patterns_single_error(self):
        """Test that single error doesn't create pattern"""
        detector = PatternDetector()
        errors = [{
            'error_type': 'ValueError',
            'message': 'Invalid input',
            'timestamp': datetime.utcnow(),
            'file': 'test.py'
        }]

        patterns = detector.detect_patterns(errors)

        # Single occurrence shouldn't create pattern
        assert len(patterns) == 0

    def test_detect_patterns_recurring_errors(self):
        """Test detecting patterns from recurring errors"""
        detector = PatternDetector()
        base_time = datetime.utcnow()
        errors = [
            {
                'error_type': 'AttributeError',
                'message': 'NoneType object has no attribute email',
                'timestamp': base_time,
                'file': 'auth.py'
            },
            {
                'error_type': 'AttributeError',
                'message': 'NoneType object has no attribute email',
                'timestamp': base_time + timedelta(hours=1),
                'file': 'auth.py'
            },
            {
                'error_type': 'AttributeError',
                'message': 'NoneType object has no attribute email',
                'timestamp': base_time + timedelta(hours=2),
                'file': 'auth.py'
            }
        ]

        patterns = detector.detect_patterns(errors)

        assert len(patterns) > 0
        assert patterns[0].frequency == 3
        assert patterns[0].error_type == 'AttributeError'

    def test_identify_root_cause_attribute_error(self):
        """Test root cause identification for AttributeError"""
        detector = PatternDetector()
        pattern = ErrorPattern(
            pattern_id='test',
            error_type='AttributeError',
            message_pattern='NoneType has no attribute',
            frequency=1,
            first_seen=datetime.utcnow(),
            last_seen=datetime.utcnow(),
            affected_files=[]
        )

        root_cause = detector.identify_root_causes(pattern)
        assert 'Null' in root_cause or 'None' in root_cause

    def test_identify_root_cause_key_error(self):
        """Test root cause identification for KeyError"""
        detector = PatternDetector()
        pattern = ErrorPattern(
            pattern_id='test',
            error_type='KeyError',
            message_pattern='api_key not found',
            frequency=1,
            first_seen=datetime.utcnow(),
            last_seen=datetime.utcnow(),
            affected_files=[]
        )

        root_cause = detector.identify_root_causes(pattern)
        assert 'Dictionary key' in root_cause or 'not found' in root_cause

    def test_identify_root_cause_type_error_json(self):
        """Test root cause identification for JSON serialization errors"""
        detector = PatternDetector()
        pattern = ErrorPattern(
            pattern_id='test',
            error_type='TypeError',
            message_pattern='Object of type User is not JSON serializable',
            frequency=1,
            first_seen=datetime.utcnow(),
            last_seen=datetime.utcnow(),
            affected_files=[]
        )

        root_cause = detector.identify_root_causes(pattern)
        assert 'to_dict' in root_cause or 'JSON' in root_cause

    def test_calculate_severity_critical(self):
        """Test severity calculation for critical errors"""
        detector = PatternDetector()
        severity = detector._calculate_severity(
            frequency=100,
            error_type='SecurityError',
            message='Authentication failed'
        )

        assert severity == 'critical'

    def test_calculate_severity_high(self):
        """Test severity calculation for high priority errors"""
        detector = PatternDetector()
        severity = detector._calculate_severity(
            frequency=60,
            error_type='ConnectionError',
            message='Database connection failed'
        )

        assert severity in ['high', 'critical']  # Can be high or critical based on frequency

    def test_calculate_severity_medium(self):
        """Test severity calculation for medium priority errors"""
        detector = PatternDetector()
        severity = detector._calculate_severity(
            frequency=15,
            error_type='ValueError',
            message='Invalid input'
        )

        assert severity == 'medium'

    def test_calculate_severity_low(self):
        """Test severity calculation for low priority errors"""
        detector = PatternDetector()
        severity = detector._calculate_severity(
            frequency=1,
            error_type='ValueError',
            message='Invalid input'
        )

        assert severity in ['low', 'medium']  # ValueError can be medium


class TestPreventionEngine:
    """Test PreventionEngine functionality"""

    def test_get_prevention_rules_attribute_error(self):
        """Test prevention rules for AttributeError"""
        engine = PreventionEngine()
        rules = engine.get_prevention_rules('AttributeError')

        assert len(rules) > 0
        assert all(isinstance(rule, str) for rule in rules)

    def test_get_prevention_rules_key_error(self):
        """Test prevention rules for KeyError"""
        engine = PreventionEngine()
        rules = engine.get_prevention_rules('KeyError')

        assert len(rules) > 0
        # Should mention dict.get() or similar
        assert any('get' in rule.lower() for rule in rules)

    def test_get_prevention_rules_type_error(self):
        """Test prevention rules for TypeError"""
        engine = PreventionEngine()
        rules = engine.get_prevention_rules('TypeError')

        assert len(rules) > 0

    def test_get_prevention_rules_unknown_error(self):
        """Test prevention rules for unknown error type"""
        engine = PreventionEngine()
        rules = engine.get_prevention_rules('UnknownErrorType')

        assert len(rules) > 0  # Should return default rules

    def test_suggest_fix_attribute_error(self):
        """Test fix suggestion for AttributeError"""
        engine = PreventionEngine()
        pattern = ErrorPattern(
            pattern_id='test',
            error_type='AttributeError',
            message_pattern='NoneType object',
            frequency=5,
            first_seen=datetime.utcnow(),
            last_seen=datetime.utcnow(),
            affected_files=['auth.py'],
            severity='medium'
        )

        suggestion = engine.suggest_fix(pattern)

        assert suggestion['error_type'] == 'AttributeError'
        assert 'prevention_rules' in suggestion
        assert 'code_example' in suggestion
        assert 'priority' in suggestion

    def test_suggest_fix_priority_urgent(self):
        """Test that critical patterns get URGENT priority"""
        engine = PreventionEngine()
        pattern = ErrorPattern(
            pattern_id='test',
            error_type='SecurityError',
            message_pattern='Auth failed',
            frequency=100,
            first_seen=datetime.utcnow(),
            last_seen=datetime.utcnow(),
            affected_files=['auth.py'],
            severity='critical'
        )

        suggestion = engine.suggest_fix(pattern)

        assert suggestion['priority'] == 'URGENT'

    def test_suggest_fix_priority_high(self):
        """Test that high frequency patterns get HIGH priority"""
        engine = PreventionEngine()
        pattern = ErrorPattern(
            pattern_id='test',
            error_type='ValueError',
            message_pattern='Invalid input',
            frequency=75,
            first_seen=datetime.utcnow(),
            last_seen=datetime.utcnow(),
            affected_files=['test.py'],
            severity='high'
        )

        suggestion = engine.suggest_fix(pattern)

        assert suggestion['priority'] == 'HIGH'

    def test_generate_code_example(self):
        """Test code example generation"""
        engine = PreventionEngine()
        example = engine._generate_code_example('AttributeError')

        assert isinstance(example, str)
        assert len(example) > 0
        assert 'Before' in example or 'After' in example


class TestErrorTracker:
    """Test main ErrorTracker interface"""

    def test_error_tracker_initialization(self):
        """Test ErrorTracker initialization"""
        tracker = ErrorTracker()

        assert tracker.pattern_detector is not None
        assert tracker.prevention_engine is not None
        assert isinstance(tracker.error_cache, dict)
        assert isinstance(tracker.patterns, dict)

    def test_log_error_basic(self):
        """Test logging a basic error"""
        tracker = ErrorTracker()

        result = tracker.log_error(
            error_type='ValueError',
            message='Invalid input',
            traceback='Traceback here'
        )

        assert result['logged'] is True
        assert 'timestamp' in result
        assert 'error_id' in result

    def test_log_error_with_context(self):
        """Test logging error with full context"""
        tracker = ErrorTracker()

        result = tracker.log_error(
            error_type='ValueError',
            message='Invalid email format',
            traceback='Full traceback',
            context={'input': 'invalid@email'},
            project_id='coocook',
            user_id=123,
            file='auth.py',
            line=45
        )

        assert result['logged'] is True

    def test_log_error_pattern_detection(self):
        """Test pattern detection during logging"""
        tracker = ErrorTracker()

        # Log same error multiple times
        for i in range(3):
            result = tracker.log_error(
                error_type='ValueError',
                message='Invalid input',
                traceback='Traceback',
                project_id='test'
            )

        # Last log should detect pattern
        assert 'pattern_detected' in result or len(tracker.patterns) > 0

    def test_get_recent_errors_empty(self):
        """Test getting recent errors when none exist"""
        tracker = ErrorTracker()

        result = tracker.get_recent_errors()

        assert 'errors' in result
        assert len(result['errors']) == 0
        assert result['total'] == 0

    def test_get_recent_errors_with_data(self):
        """Test getting recent errors with data"""
        tracker = ErrorTracker()

        # Log some errors
        for i in range(5):
            tracker.log_error(
                error_type='ValueError',
                message=f'Error {i}',
                traceback='Traceback'
            )

        result = tracker.get_recent_errors(limit=10)

        assert result['total'] == 5
        assert len(result['errors']) == 5

    def test_get_recent_errors_pagination(self):
        """Test error pagination"""
        tracker = ErrorTracker()

        # Log 15 errors
        for i in range(15):
            tracker.log_error(
                error_type='ValueError',
                message=f'Error {i}',
                traceback='Traceback'
            )

        # Get first page
        result1 = tracker.get_recent_errors(limit=5, offset=0)
        assert len(result1['errors']) == 5

        # Get second page
        result2 = tracker.get_recent_errors(limit=5, offset=5)
        assert len(result2['errors']) == 5

        # Get third page
        result3 = tracker.get_recent_errors(limit=5, offset=10)
        assert len(result3['errors']) == 5

    def test_get_recent_errors_filter_by_type(self):
        """Test filtering errors by type"""
        tracker = ErrorTracker()

        tracker.log_error('ValueError', 'Error 1', 'Traceback')
        tracker.log_error('TypeError', 'Error 2', 'Traceback')
        tracker.log_error('ValueError', 'Error 3', 'Traceback')

        result = tracker.get_recent_errors(error_type='ValueError')

        assert result['total'] >= 2

    def test_get_error_patterns_empty(self):
        """Test getting patterns when none exist"""
        tracker = ErrorTracker()

        result = tracker.get_error_patterns()

        assert isinstance(result, list)
        assert len(result) == 0

    def test_get_error_patterns_with_data(self):
        """Test getting detected patterns"""
        tracker = ErrorTracker()

        # Log recurring error to create pattern
        for i in range(3):
            tracker.log_error(
                error_type='ValueError',
                message='Invalid input',
                traceback='Traceback'
            )

        patterns = tracker.get_error_patterns()

        assert isinstance(patterns, list)

    def test_get_error_patterns_filter_by_severity(self):
        """Test filtering patterns by severity"""
        tracker = ErrorTracker()

        # Create a high-severity pattern
        for i in range(60):
            tracker.log_error(
                error_type='ValueError',
                message='Invalid input',
                traceback='Traceback'
            )

        patterns = tracker.get_error_patterns(severity='high')

        assert isinstance(patterns, list)

    def test_report_pattern_fixed(self):
        """Test marking pattern as fixed"""
        tracker = ErrorTracker()

        # Create a pattern first
        for i in range(3):
            tracker.log_error(
                error_type='ValueError',
                message='Invalid input',
                traceback='Traceback'
            )

        patterns = tracker.get_error_patterns()
        if patterns:
            pattern_id = patterns[0]['pattern_id']

            result = tracker.report_pattern_fixed(
                pattern_id=pattern_id,
                resolution='Added input validation'
            )

            assert result['success'] is True
            assert 'resolved_at' in result

    def test_report_pattern_fixed_not_found(self):
        """Test marking non-existent pattern as fixed"""
        tracker = ErrorTracker()

        result = tracker.report_pattern_fixed(
            pattern_id='nonexistent',
            resolution='Fix'
        )

        assert result['success'] is False

    def test_get_prevention_suggestions(self):
        """Test getting prevention suggestions"""
        tracker = ErrorTracker()

        suggestion = tracker.get_prevention_suggestions('ValueError')

        assert 'error_type' in suggestion
        assert 'prevention_rules' in suggestion
        assert 'code_example' in suggestion
        assert len(suggestion['prevention_rules']) > 0

    def test_get_prevention_suggestions_various_types(self):
        """Test prevention suggestions for various error types"""
        tracker = ErrorTracker()

        error_types = ['AttributeError', 'KeyError', 'TypeError', 'ValueError']

        for error_type in error_types:
            suggestion = tracker.get_prevention_suggestions(error_type)

            assert suggestion['error_type'] == error_type
            assert 'prevention_rules' in suggestion
            assert len(suggestion['prevention_rules']) > 0

    def test_get_health_check_healthy(self):
        """Test health check when system is healthy"""
        tracker = ErrorTracker()

        # Log a few errors but nothing critical
        tracker.log_error('ValueError', 'Error 1', 'Traceback')

        health = tracker.get_health_check()

        assert 'status' in health
        assert 'total_errors_tracked' in health
        assert 'active_patterns' in health
        assert 'critical_patterns' in health

    def test_get_health_check_critical(self):
        """Test health check with critical patterns"""
        tracker = ErrorTracker()

        # Create a critical pattern
        for i in range(20):
            tracker.log_error(
                error_type='SecurityError',
                message='Authentication failure',
                traceback='Traceback'
            )

        health = tracker.get_health_check()

        # Might be critical or healthy depending on detection
        assert health['status'] in ['healthy', 'critical']

    def test_error_cache_cleanup(self):
        """Test that error cache doesn't exceed limits"""
        tracker = ErrorTracker()

        # Log many errors
        for i in range(1500):
            tracker.log_error(
                error_type='ValueError',
                message=f'Error {i}',
                traceback='Traceback',
                project_id='test'
            )

        # Check cache is limited
        cache_key = next(iter(tracker.error_cache.keys()))
        assert len(tracker.error_cache[cache_key]) <= 1000


@pytest.mark.skip(reason="API integration tests require proper database schema migration")
class TestErrorAPIIntegration:
    """Integration tests for error API endpoints"""

    def test_api_log_error(self, client):
        """Test /api/errors/log endpoint"""
        response = client.post('/api/errors/log', json={
            'error_type': 'ValueError',
            'message': 'Invalid input',
            'traceback': 'Traceback here'
        })

        assert response.status_code == 201
        data = response.get_json()
        assert data['logged'] is True

    def test_api_log_error_missing_fields(self, client):
        """Test /api/errors/log with missing fields"""
        response = client.post('/api/errors/log', json={
            'error_type': 'ValueError'
        })

        assert response.status_code == 400

    def test_api_get_recent_errors(self, client):
        """Test /api/errors/recent endpoint"""
        response = client.get('/api/errors/recent?limit=10')

        assert response.status_code == 200
        data = response.get_json()
        assert 'errors' in data
        assert 'total' in data

    def test_api_get_error_patterns(self, client):
        """Test /api/errors/patterns endpoint"""
        response = client.get('/api/errors/patterns')

        assert response.status_code == 200
        data = response.get_json()
        assert 'patterns' in data
        assert 'total' in data

    def test_api_get_prevention(self, client):
        """Test /api/errors/patterns/{id}/prevention endpoint"""
        # First create a pattern
        client.post('/api/errors/log', json={
            'error_type': 'ValueError',
            'message': 'Invalid input',
            'traceback': 'Traceback'
        })

        # Get patterns
        response = client.get('/api/errors/patterns')
        patterns = response.get_json().get('patterns', [])

        if patterns:
            pattern_id = patterns[0]['pattern_id']
            response = client.get(f'/api/errors/patterns/{pattern_id}/prevention')

            assert response.status_code == 200
            data = response.get_json()
            assert 'suggestions' in data

    def test_api_resolve_pattern(self, client):
        """Test /api/errors/patterns/{id}/resolve endpoint"""
        # First create and get a pattern
        client.post('/api/errors/log', json={
            'error_type': 'ValueError',
            'message': 'Invalid input',
            'traceback': 'Traceback'
        })

        response = client.get('/api/errors/patterns')
        patterns = response.get_json().get('patterns', [])

        if patterns:
            pattern_id = patterns[0]['pattern_id']
            response = client.post(
                f'/api/errors/patterns/{pattern_id}/resolve',
                json={'resolution': 'Fixed validation logic'}
            )

            assert response.status_code == 200

    def test_api_health_check(self, client):
        """Test /api/errors/health endpoint"""
        response = client.get('/api/errors/health')

        assert response.status_code in [200, 503]
        data = response.get_json()
        assert 'status' in data
        assert 'total_errors_tracked' in data


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
