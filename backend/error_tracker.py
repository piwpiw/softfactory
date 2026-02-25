"""Error Tracking and Prevention System

Production-ready error logging, aggregation, pattern detection, and prevention.
Implements centralized error management for enterprise reliability tracking.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict
import hashlib
import re
from sqlalchemy import func

from .models import db


class ErrorPattern:
    """Represents a detected error pattern with metadata"""

    def __init__(
        self,
        pattern_id: str,
        error_type: str,
        message_pattern: str,
        frequency: int,
        first_seen: datetime,
        last_seen: datetime,
        affected_files: List[str],
        root_cause: Optional[str] = None,
        severity: str = 'low'
    ):
        self.pattern_id = pattern_id
        self.error_type = error_type
        self.message_pattern = message_pattern
        self.frequency = frequency
        self.first_seen = first_seen
        self.last_seen = last_seen
        self.affected_files = affected_files
        self.root_cause = root_cause
        self.severity = severity  # low, medium, high, critical
        self.resolution = None
        self.resolved_at = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            'pattern_id': self.pattern_id,
            'error_type': self.error_type,
            'message_pattern': self.message_pattern,
            'frequency': self.frequency,
            'first_seen': self.first_seen.isoformat(),
            'last_seen': self.last_seen.isoformat(),
            'affected_files': self.affected_files,
            'root_cause': self.root_cause,
            'severity': self.severity,
            'resolution': self.resolution,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'status': 'resolved' if self.resolved_at else 'active'
        }


class ErrorAggregator:
    """Groups similar errors for pattern analysis"""

    def __init__(self):
        self.error_groups: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.patterns: Dict[str, ErrorPattern] = {}

    def aggregate(self, error_logs: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Group errors by type and normalize message patterns.

        Args:
            error_logs: List of error log dictionaries

        Returns:
            Dictionary with normalized error groups
        """
        for error in error_logs:
            # Create normalized key from error type and message pattern
            group_key = self._create_group_key(error['error_type'], error['message'])
            self.error_groups[group_key].append(error)

        return self.error_groups

    def get_frequency_stats(self) -> Dict[str, int]:
        """
        Get frequency statistics for each error group.

        Returns:
            Dictionary mapping group keys to error counts
        """
        return {
            group_key: len(errors)
            for group_key, errors in self.error_groups.items()
        }

    def _create_group_key(self, error_type: str, message: str) -> str:
        """
        Create normalized group key from error type and message.
        Replaces variable parts (numbers, IDs) with placeholders.
        """
        # Replace common variable parts
        normalized = message
        normalized = re.sub(r'\d+', 'N', normalized)  # Replace numbers
        normalized = re.sub(r'[a-f0-9]{8}-[a-f0-9-]+', 'UUID', normalized)  # UUIDs
        normalized = re.sub(r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b', 'EMAIL', normalized)  # Emails

        # Create hash-based key
        key_string = f"{error_type}:{normalized}"
        key_hash = hashlib.md5(key_string.encode()).hexdigest()[:12]

        return key_hash


class PatternDetector:
    """Detects systematic error patterns and root causes"""

    def __init__(self):
        self.detected_patterns: Dict[str, ErrorPattern] = {}

    def detect_patterns(self, error_logs: List[Dict[str, Any]]) -> List[ErrorPattern]:
        """
        Detect recurring error patterns from logs.

        Args:
            error_logs: List of error log dictionaries

        Returns:
            List of detected ErrorPattern objects
        """
        if not error_logs:
            return []

        aggregator = ErrorAggregator()
        groups = aggregator.aggregate(error_logs)
        stats = aggregator.get_frequency_stats()

        patterns = []

        for group_key, errors in groups.items():
            if len(errors) >= 2:  # Only flag as pattern if >= 2 occurrences
                pattern = self._create_pattern_from_group(group_key, errors)
                pattern.severity = self._calculate_severity(
                    len(errors),
                    pattern.error_type,
                    pattern.message_pattern
                )
                self.detected_patterns[pattern.pattern_id] = pattern
                patterns.append(pattern)

        # Sort by frequency (highest first)
        patterns.sort(key=lambda p: p.frequency, reverse=True)

        return patterns

    def identify_root_causes(self, pattern: ErrorPattern) -> str:
        """
        Identify likely root cause for an error pattern.

        Args:
            pattern: ErrorPattern to analyze

        Returns:
            Root cause description
        """
        error_type = pattern.error_type
        message = pattern.message_pattern

        # Rule-based root cause identification
        if 'AttributeError' in error_type:
            if 'NoneType' in message:
                return 'Null/None object accessed without null check'
            else:
                return 'Missing or undefined attribute accessed'

        elif 'KeyError' in error_type:
            return 'Dictionary key not found; missing validation before access'

        elif 'IndexError' in error_type:
            return 'List index out of bounds; insufficient bounds checking'

        elif 'TypeError' in error_type:
            if 'JSON' in message or 'serializable' in message:
                return 'Object type not JSON serializable; missing to_dict() method'
            else:
                return 'Type mismatch in operation'

        elif 'ValueError' in error_type:
            return 'Invalid value provided; input validation required'

        elif 'FileNotFoundError' in error_type:
            return 'File path issue; use absolute paths or verify existence'

        elif 'ConnectionError' in error_type:
            return 'Database/network connection failed; retry logic needed'

        elif '401' in message or 'Unauthorized' in message:
            return 'Authentication failed; check token/credentials order'

        elif '403' in message or 'Forbidden' in message:
            return 'Permission denied; check decorator order or scope'

        elif 'DatabaseError' in error_type:
            return 'Database constraint or transaction error'

        else:
            return 'Unknown; requires manual investigation'

    def _create_pattern_from_group(
        self,
        group_key: str,
        errors: List[Dict[str, Any]]
    ) -> ErrorPattern:
        """Create ErrorPattern from grouped errors"""
        first_error = errors[0]
        last_error = errors[-1]

        affected_files = list(set(e.get('file', 'unknown') for e in errors))

        pattern = ErrorPattern(
            pattern_id=group_key,
            error_type=first_error['error_type'],
            message_pattern=first_error['message'][:100],  # Truncate for pattern
            frequency=len(errors),
            first_seen=first_error['timestamp'],
            last_seen=last_error['timestamp'],
            affected_files=affected_files
        )

        # Identify root cause
        pattern.root_cause = self.identify_root_causes(pattern)

        return pattern

    def _calculate_severity(
        self,
        frequency: int,
        error_type: str,
        message: str
    ) -> str:
        """Determine error severity based on type and frequency"""
        # Critical indicators
        if any(x in error_type for x in ['SecurityError', 'AuthenticationError', 'CriticalError']):
            return 'critical'

        if 'database' in message.lower() and frequency > 10:
            return 'critical'

        # High severity indicators
        if frequency > 50:
            return 'high'

        if any(x in error_type for x in ['ConnectionError', 'TimeoutError']):
            return 'high'

        # Medium severity indicators
        if frequency > 10:
            return 'medium'

        if any(x in error_type for x in ['ValueError', 'TypeError', 'AttributeError']):
            return 'medium'

        # Low severity (default)
        return 'low'


class PreventionEngine:
    """Suggests preventive measures based on error patterns"""

    # Prevention rules mapped by error type
    PREVENTION_RULES = {
        'AttributeError': [
            'Always check for None before accessing attributes: if obj is not None: obj.attr',
            'Use optional chaining or getattr() with default: getattr(obj, "attr", None)',
            'Add type hints and enforce type checking',
            'Add try-except with specific handling'
        ],
        'KeyError': [
            'Use .get() method with default: dict.get(key, default)',
            'Check key existence before access: if key in dict:',
            'Use defaultdict for automatic default values',
            'Add input validation before dictionary access'
        ],
        'IndexError': [
            'Check list length before access: if len(list) > index:',
            'Use try-except for safe list access',
            'Add bounds checking in loop iterations',
            'Consider using list comprehensions with guards'
        ],
        'TypeError': [
            'Verify JSON serialization with to_dict() method',
            'Add type hints and runtime type checking',
            'Validate input types at function entry',
            'Use isinstance() for runtime type verification'
        ],
        'ValueError': [
            'Add input validation before parsing/conversion',
            'Use try-except around format/conversion operations',
            'Document expected value ranges/formats',
            'Add defensive checks in processing logic'
        ],
        'FileNotFoundError': [
            'Use absolute paths instead of relative paths: os.path.abspath(path)',
            'Verify file exists before access: os.path.exists(path)',
            'Create files/directories if missing',
            'Document expected file locations clearly'
        ],
        'ConnectionError': [
            'Implement retry logic with exponential backoff',
            'Add connection pooling and keep-alives',
            'Implement circuit breaker pattern',
            'Add comprehensive error logging for debugging'
        ],
        '401_Unauthorized': [
            'Verify token format and expiration',
            'Check authentication before authorization checks',
            'Place @require_auth at BOTTOM of decorator stack',
            'Validate JWT signature and claims'
        ],
        '403_Forbidden': [
            'Place @require_subscription AFTER @require_auth',
            'Verify user permissions/roles match requirement',
            'Add detailed permission checks',
            'Log permission denied events for audit'
        ],
        'DatabaseError': [
            'Use database transactions with rollback',
            'Add constraint validation before insert/update',
            'Implement proper schema migrations',
            'Add connection pooling and timeout handling'
        ]
    }

    def get_prevention_rules(self, error_type: str) -> List[str]:
        """
        Get prevention rules for a specific error type.

        Args:
            error_type: Type of error (e.g., 'AttributeError', 'TypeError')

        Returns:
            List of prevention rules
        """
        # Try exact match first
        if error_type in self.PREVENTION_RULES:
            return self.PREVENTION_RULES[error_type]

        # Try partial matches
        for rule_type, rules in self.PREVENTION_RULES.items():
            if rule_type in error_type:
                return rules

        # Default prevention rules
        return [
            'Add comprehensive error logging',
            'Add input validation',
            'Add try-except error handling',
            'Add unit tests covering failure cases'
        ]

    def suggest_fix(self, error_pattern: ErrorPattern) -> Dict[str, Any]:
        """
        Generate fix suggestions for an error pattern.

        Args:
            error_pattern: ErrorPattern to analyze

        Returns:
            Dictionary with fix suggestions and code examples
        """
        prevention_rules = self.get_prevention_rules(error_pattern.error_type)

        suggestion = {
            'pattern_id': error_pattern.pattern_id,
            'error_type': error_pattern.error_type,
            'root_cause': error_pattern.root_cause,
            'affected_files': error_pattern.affected_files,
            'frequency': error_pattern.frequency,
            'severity': error_pattern.severity,
            'prevention_rules': prevention_rules,
            'code_example': self._generate_code_example(error_pattern.error_type),
            'priority': self._calculate_fix_priority(error_pattern)
        }

        return suggestion

    def _generate_code_example(self, error_type: str) -> str:
        """Generate code example for fixing error"""
        examples = {
            'AttributeError': '''
# Before (Error-prone)
user = get_user()
print(user.email)  # AttributeError if user is None

# After (Safe)
user = get_user()
if user is not None:
    print(user.email)
# Or use safe access:
print(getattr(user, 'email', 'N/A'))
            ''',
            'KeyError': '''
# Before (Error-prone)
value = config['api_key']  # KeyError if missing

# After (Safe)
value = config.get('api_key', 'default_value')
# Or check first:
if 'api_key' in config:
    value = config['api_key']
            ''',
            'TypeError': '''
# Before (Error-prone)
response = {'user': user_obj}  # JSON not serializable

# After (Safe)
response = {'user': user_obj.to_dict()}
# Or add to model:
class User:
    def to_dict(self):
        return {'id': self.id, 'email': self.email}
            ''',
            '401_Unauthorized': '''
# Before (Error-prone)
@app.route('/api/data')
@require_subscription('premium')  # Runs first!
@require_auth
def get_data():
    return jsonify(...)

# After (Correct)
@app.route('/api/data')
@require_auth                     # Runs first
@require_subscription('premium')  # Runs second
def get_data():
    return jsonify(...)
            '''
        }

        return examples.get(error_type, '# Add proper error handling and validation')

    def _calculate_fix_priority(self, pattern: ErrorPattern) -> str:
        """Determine priority for fixing based on pattern characteristics"""
        if pattern.severity == 'critical':
            return 'URGENT'
        elif pattern.severity == 'high' or pattern.frequency > 50:
            return 'HIGH'
        elif pattern.severity == 'medium' or pattern.frequency > 10:
            return 'MEDIUM'
        else:
            return 'LOW'


class ErrorTracker:
    """Main error tracking interface - enterprise-grade error management"""

    def __init__(self, db_session=None):
        """
        Initialize ErrorTracker.

        Args:
            db_session: SQLAlchemy session (defaults to db.session)
        """
        self.db = db_session or db.session
        self.pattern_detector = PatternDetector()
        self.prevention_engine = PreventionEngine()
        self.error_cache: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.patterns: Dict[str, ErrorPattern] = {}

    def log_error(
        self,
        error_type: str,
        message: str,
        traceback: str,
        context: Optional[Dict[str, Any]] = None,
        project_id: Optional[str] = None,
        user_id: Optional[int] = None,
        file: str = 'unknown',
        line: int = 0
    ) -> Dict[str, Any]:
        """
        Log an error with full context.

        Args:
            error_type: Type of error (e.g., 'ValueError')
            message: Error message
            traceback: Full traceback
            context: Additional context dictionary
            project_id: Project identifier
            user_id: User ID if applicable
            file: Source file where error occurred
            line: Line number where error occurred

        Returns:
            Dictionary with logged error details and pattern_id if new pattern detected
        """
        error_log = {
            'error_type': error_type,
            'message': message,
            'traceback': traceback,
            'context': context or {},
            'project_id': project_id,
            'user_id': user_id,
            'file': file,
            'line': line,
            'timestamp': datetime.utcnow()
        }

        # Cache error locally
        cache_key = f"{error_type}:{project_id or 'global'}"
        self.error_cache[cache_key].append(error_log)

        # Cleanup old cache (keep last 1000 per project)
        if len(self.error_cache[cache_key]) > 1000:
            self.error_cache[cache_key] = self.error_cache[cache_key][-1000:]

        # Attempt pattern detection for cached errors
        patterns = self.pattern_detector.detect_patterns(self.error_cache[cache_key])
        for pattern in patterns:
            self.patterns[pattern.pattern_id] = pattern

        result = {
            'logged': True,
            'timestamp': error_log['timestamp'].isoformat(),
            'error_id': hashlib.md5(
                f"{error_type}{message}{error_log['timestamp']}".encode()
            ).hexdigest()[:12]
        }

        # Add pattern info if detected
        if patterns:
            result['pattern_detected'] = True
            result['pattern_id'] = patterns[0].pattern_id

        return result

    def get_recent_errors(
        self,
        limit: int = 10,
        project_id: Optional[str] = None,
        error_type: Optional[str] = None,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Get recent errors with filtering.

        Args:
            limit: Maximum errors to return
            project_id: Filter by project ID
            error_type: Filter by error type
            offset: Pagination offset

        Returns:
            Dictionary with error logs and metadata
        """
        all_errors = []

        for cache_key, errors in self.error_cache.items():
            if project_id:
                # Filter by project
                errors = [e for e in errors if e['project_id'] == project_id]

            if error_type:
                # Filter by error type
                errors = [e for e in errors if e['error_type'] == error_type]

            all_errors.extend(errors)

        # Sort by timestamp (newest first)
        all_errors.sort(key=lambda e: e['timestamp'], reverse=True)

        # Paginate
        paginated = all_errors[offset:offset + limit]

        return {
            'errors': [
                {
                    'error_type': e['error_type'],
                    'message': e['message'],
                    'timestamp': e['timestamp'].isoformat(),
                    'file': e['file'],
                    'line': e['line'],
                    'project_id': e['project_id']
                }
                for e in paginated
            ],
            'total': len(all_errors),
            'count': len(paginated),
            'offset': offset,
            'limit': limit
        }

    def get_error_patterns(
        self,
        error_type: Optional[str] = None,
        severity: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get detected error patterns.

        Args:
            error_type: Filter by error type
            severity: Filter by severity level

        Returns:
            List of error patterns as dictionaries
        """
        patterns = list(self.patterns.values())

        if error_type:
            patterns = [p for p in patterns if p.error_type == error_type]

        if severity:
            patterns = [p for p in patterns if p.severity == severity]

        # Sort by frequency (highest first)
        patterns.sort(key=lambda p: p.frequency, reverse=True)

        return [p.to_dict() for p in patterns]

    def report_pattern_fixed(
        self,
        pattern_id: str,
        resolution: str
    ) -> Dict[str, Any]:
        """
        Mark an error pattern as fixed/resolved.

        Args:
            pattern_id: Pattern ID to mark as resolved
            resolution: Description of fix applied

        Returns:
            Dictionary with resolution details
        """
        if pattern_id not in self.patterns:
            return {
                'success': False,
                'error': f'Pattern {pattern_id} not found'
            }

        pattern = self.patterns[pattern_id]
        pattern.resolution = resolution
        pattern.resolved_at = datetime.utcnow()

        return {
            'success': True,
            'pattern_id': pattern_id,
            'resolved_at': pattern.resolved_at.isoformat(),
            'resolution': resolution
        }

    def get_prevention_suggestions(self, error_type: str) -> Dict[str, Any]:
        """
        Get prevention suggestions for an error type.

        Args:
            error_type: Type of error

        Returns:
            Dictionary with prevention rules and code examples
        """
        # Get or create a temporary pattern for analysis
        pattern = ErrorPattern(
            pattern_id=f"temp_{error_type}",
            error_type=error_type,
            message_pattern='',
            frequency=0,
            first_seen=datetime.utcnow(),
            last_seen=datetime.utcnow(),
            affected_files=[]
        )

        pattern.root_cause = self.pattern_detector.identify_root_causes(pattern)

        return self.prevention_engine.suggest_fix(pattern)

    def get_health_check(self) -> Dict[str, Any]:
        """
        Get error tracking system health and statistics.

        Returns:
            Dictionary with health metrics
        """
        total_errors = sum(len(errors) for errors in self.error_cache.values())
        total_patterns = len([p for p in self.patterns.values() if not p.resolved_at])
        resolved_patterns = len([p for p in self.patterns.values() if p.resolved_at])

        # Calculate error rate (errors in last hour)
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        recent_errors = sum(
            len([e for e in errors if e['timestamp'] > one_hour_ago])
            for errors in self.error_cache.values()
        )

        # Identify critical patterns
        critical_patterns = [
            p for p in self.patterns.values()
            if p.severity == 'critical' and not p.resolved_at
        ]

        return {
            'status': 'healthy' if not critical_patterns else 'critical',
            'total_errors_tracked': total_errors,
            'active_patterns': total_patterns,
            'resolved_patterns': resolved_patterns,
            'recent_error_rate': f"{recent_errors}/hour",
            'critical_patterns': len(critical_patterns),
            'critical_pattern_ids': [p.pattern_id for p in critical_patterns]
        }
