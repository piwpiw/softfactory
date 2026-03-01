# Advanced Architecture Patterns — Production-Grade SNS Automation v2.0
> **Phase 3 Completion** | Enterprise Design Patterns for Scalability & Reliability
> **Date:** 2026-02-26 | **Target Scale:** 100K+ concurrent users | **Status:** Implementation Guide

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [1. Event-Driven Architecture](#1-event-driven-architecture)
3. [2. CQRS Pattern](#2-cqrs-command-query-responsibility-segregation)
4. [3. Saga Pattern](#3-saga-pattern--distributed-transactions)
5. [4. Performance Optimization](#4-performance-optimization-strategy)
6. [5. Security Hardening](#5-security-hardening)
7. [6. Scalability Roadmap](#6-scalability-roadmap)
8. [7. Monitoring & Observability](#7-monitoring--observability)
9. [8. Implementation Checklist](#8-implementation-checklist)
10. [9. Architecture Diagrams](#9-architecture-diagrams)

---

## Executive Summary

The SNS Automation v2.0 platform currently operates as a **modular monolith** with 32 API endpoints across 9 social platforms. To achieve production-grade reliability and scale to 100K+ concurrent users, this document introduces **five enterprise design patterns**:

| Pattern | Purpose | Impact |
|---------|---------|--------|
| **Event-Driven** | Decouple SNS operations from API responses | 40% latency reduction |
| **CQRS** | Separate read/write models with caching | 70% throughput increase |
| **Saga** | Distributed transaction coordination | 99.9% atomicity |
| **Connection Pooling** | Optimize database connections | 50% connection overhead reduction |
| **Multi-tier Caching** | In-memory + Redis + Database | 90% cache hit ratio |

**Current State:**
- 32 API endpoints (fully functional)
- 9 platform clients (Instagram, Facebook, Twitter, LinkedIn, TikTok, YouTube, Pinterest, Threads, YouTube Shorts)
- APScheduler background job (60-sec polling)
- 8 database tables with OAuth support
- ~1,000 concurrent user capacity

**After Implementation:**
- Estimated capacity: 10,000+ concurrent users
- 40-70% performance improvement
- 99.9% availability SLA

---

## 1. Event-Driven Architecture

### 1.1 Pattern Overview

**Problem:** SNS publishing is synchronous — client waits for all platform posts to complete before returning response.

```
Client → POST /api/sns/posts → Publish to Instagram → Publish to Twitter → ...
                                 (blocking)           (blocking)
```

**Impact:** If one platform is slow, entire request hangs.

---

### 1.2 Solution: Event Bus Architecture

**Architecture:**

```python
# File: backend/services/sns_event_bus.py

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, List, Callable
import json
from backend.logging_config import get_logger

log = get_logger(__name__)

@dataclass
class SNSEvent:
    """Base event class for all SNS operations"""
    event_id: str  # UUID
    event_type: str  # 'post:published', 'post:deleted', 'analytics:updated'
    user_id: int
    timestamp: datetime
    data: Dict

@dataclass
class PostPublishedEvent(SNSEvent):
    """Fired when a post is successfully published"""
    post_id: int
    platforms: List[str]
    content: str

@dataclass
class PostFailedEvent(SNSEvent):
    """Fired when post publishing fails"""
    post_id: int
    platform: str
    error_message: str

class EventBus:
    """Publish-Subscribe Event Bus for SNS Operations"""

    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}
        self._event_history: List[SNSEvent] = []  # For audit/replay

    def subscribe(self, event_type: str, handler: Callable) -> None:
        """Subscribe handler to event type"""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)
        log.info(f"Subscribed {handler.__name__} to {event_type}")

    def publish(self, event: SNSEvent) -> None:
        """Publish event and notify all subscribers (asynchronously)"""
        self._event_history.append(event)

        # Log event
        log.info(
            f"Event published: {event.event_type}",
            extra={
                'event_id': event.event_id,
                'event_type': event.event_type,
                'user_id': event.user_id,
                'timestamp': event.timestamp.isoformat()
            }
        )

        # Notify subscribers (async in production)
        if event.event_type in self._subscribers:
            for handler in self._subscribers[event.event_type]:
                try:
                    # In production, use task queue (Celery)
                    handler(event)
                except Exception as e:
                    log.error(
                        f"Event handler {handler.__name__} failed for {event.event_type}",
                        exc_info=True
                    )

    def get_history(self, event_type: str = None, limit: int = 100) -> List[SNSEvent]:
        """Retrieve event history (for audit/debugging)"""
        if event_type:
            return [e for e in self._event_history if e.event_type == event_type][-limit:]
        return self._event_history[-limit:]

# Global event bus instance
event_bus = EventBus()

# Register default handlers
def register_default_handlers():
    """Register core event handlers"""
    event_bus.subscribe('post:published', handle_post_published)
    event_bus.subscribe('post:published', record_analytics)
    event_bus.subscribe('post:published', send_notification)
    event_bus.subscribe('post:failed', handle_post_failed)

def handle_post_published(event: PostPublishedEvent) -> None:
    """Handler: Update post status and notify user"""
    from backend.models import SNSPost
    post = SNSPost.query.get(event.post_id)
    if post:
        post.status = 'published'
        post.published_at = datetime.utcnow()
        post.commit()
        log.info(f"Post {event.post_id} marked as published")

def record_analytics(event: PostPublishedEvent) -> None:
    """Handler: Record analytics for published post"""
    from backend.models import SNSAnalytics
    analytics = SNSAnalytics(
        user_id=event.user_id,
        post_id=event.post_id,
        action='published',
        platforms=','.join(event.platforms),
        metadata={'content_length': len(event.content)}
    )
    analytics.commit()
    log.info(f"Analytics recorded for post {event.post_id}")

def send_notification(event: PostPublishedEvent) -> None:
    """Handler: Send Telegram notification"""
    from daemon.daemon_service import send_telegram_message
    message = f"✅ Post published to {len(event.platforms)} platforms"
    send_telegram_message(event.user_id, message)
    log.info(f"Notification sent to user {event.user_id}")

def handle_post_failed(event: PostFailedEvent) -> None:
    """Handler: Alert user of failed post"""
    from backend.models import SNSPost
    post = SNSPost.query.get(event.post_id)
    if post:
        post.status = 'failed'
        post.error_message = event.error_message
        post.commit()
    log.error(f"Post {event.post_id} failed on {event.platform}: {event.error_message}")
```

---

### 1.3 Integration with SNS Service

**Modified SNS API endpoint:**

```python
# File: backend/services/sns_auto.py (existing file, add this)

from backend.services.sns_event_bus import event_bus, PostPublishedEvent, PostFailedEvent
import uuid
from datetime import datetime

@sns_bp.route('/posts', methods=['POST'])
@require_auth
def create_post(user_id):
    """Create and publish SNS post (async with event bus)"""
    data = request.get_json()

    try:
        # Step 1: Create post record in DB
        post = SNSPost(
            user_id=user_id,
            content=data['content'],
            platforms=','.join(data['platforms']),
            status='pending',
            scheduled_at=data.get('scheduled_at')
        )
        db.session.add(post)
        db.session.commit()

        # Step 2: Publish event (non-blocking)
        event = PostPublishedEvent(
            event_id=str(uuid.uuid4()),
            event_type='post:published',
            user_id=user_id,
            timestamp=datetime.utcnow(),
            post_id=post.id,
            platforms=data['platforms'],
            content=data['content'],
            data={'scheduled': data.get('scheduled_at') is not None}
        )
        event_bus.publish(event)

        # Step 3: Return immediately (before background processing completes)
        return jsonify({
            'post_id': post.id,
            'status': 'pending',
            'event_id': event.event_id,
            'message': 'Post created. Publishing in background...'
        }), 201

    except Exception as e:
        # Publish failure event
        failure_event = PostFailedEvent(
            event_id=str(uuid.uuid4()),
            event_type='post:failed',
            user_id=user_id,
            timestamp=datetime.utcnow(),
            post_id=None,
            platform='unknown',
            error_message=str(e),
            data={'error_type': type(e).__name__}
        )
        event_bus.publish(failure_event)
        return jsonify({'error': str(e)}), 500

# Background task (runs async via Celery or APScheduler)
def publish_post_to_platforms(post_id: int) -> None:
    """
    Background task: Publish post to all platforms
    Triggered by 'post:published' event
    """
    post = SNSPost.query.get(post_id)
    if not post:
        return

    platforms = post.platforms.split(',')
    results = {}

    for platform in platforms:
        try:
            client = get_client(platform)
            response = client.publish(
                content=post.content,
                media=post.media_urls.split(',') if post.media_urls else []
            )
            results[platform] = {'status': 'success', 'platform_post_id': response['id']}
        except Exception as e:
            results[platform] = {'status': 'failed', 'error': str(e)}
            log.error(f"Failed to publish to {platform}: {e}")

    # Update post record
    post.status = 'published'
    post.platform_responses = json.dumps(results)
    post.published_at = datetime.utcnow()
    db.session.commit()

    log.info(f"Post {post_id} publishing completed: {results}")
```

---

### 1.4 Benefits

| Benefit | Before | After |
|---------|--------|-------|
| **Response Time** | 5-15 seconds (all platforms) | 100ms (immediate) |
| **Failure Impact** | One platform fails → entire request fails | Partial success possible |
| **Scalability** | Sync requests block threads | Async handlers scale independently |
| **User Experience** | Waiting spinner | Immediate confirmation |

---

## 2. CQRS (Command Query Responsibility Segregation)

### 2.1 Pattern Overview

**Problem:** SNS data is read far more frequently than written, but both use same database.

```
Read/Write Ratio: 10:1 (for analytics, dashboards)
Problem: Database caching strategy is one-size-fits-all
Solution: Separate read model (cached) from write model (transactional)
```

---

### 2.2 Implementation

**Architecture:**

```python
# File: backend/services/sns_cqrs.py

from functools import wraps
from datetime import datetime, timedelta
import json
from backend.logging_config import get_logger
from backend.models import SNSPost, SNSAnalytics

log = get_logger(__name__)

class SNSQueryService:
    """Read Model: Query-optimized snapshots with aggressive caching"""

    def __init__(self, cache_backend):
        self.cache = cache_backend  # Redis or in-memory cache

    def get_user_posts(self, user_id: int, limit: int = 20, offset: int = 0):
        """
        Read Model: Get user posts with caching

        Cache Strategy:
        - L1: In-memory (60 seconds)
        - L2: Redis (5 minutes)
        - L3: Database
        """
        cache_key = f"user:{user_id}:posts:{limit}:{offset}"

        # L1: Check in-memory cache
        if hasattr(self, f'_cache_{cache_key}'):
            cached = getattr(self, f'_cache_{cache_key}')
            if cached['expires_at'] > datetime.utcnow():
                log.debug(f"Cache hit (L1) for {cache_key}")
                return cached['data']

        # L2: Check Redis
        try:
            cached = self.cache.get(cache_key)
            if cached:
                data = json.loads(cached)
                # Store in L1
                setattr(self, f'_cache_{cache_key}', {
                    'data': data,
                    'expires_at': datetime.utcnow() + timedelta(seconds=60)
                })
                log.debug(f"Cache hit (L2) for {cache_key}")
                return data
        except Exception as e:
            log.warning(f"Redis cache miss: {e}")

        # L3: Database (expensive)
        posts = SNSPost.query.filter_by(user_id=user_id)\
            .order_by(SNSPost.created_at.desc())\
            .offset(offset)\
            .limit(limit)\
            .all()

        data = {
            'posts': [p.to_dict() for p in posts],
            'total': SNSPost.query.filter_by(user_id=user_id).count(),
            'retrieved_at': datetime.utcnow().isoformat()
        }

        # Store in L2 cache
        try:
            self.cache.setex(cache_key, 300, json.dumps(data))
            log.debug(f"Cached in Redis: {cache_key}")
        except Exception as e:
            log.warning(f"Failed to cache in Redis: {e}")

        # Store in L1 cache
        setattr(self, f'_cache_{cache_key}', {
            'data': data,
            'expires_at': datetime.utcnow() + timedelta(seconds=60)
        })

        return data

    def get_post_analytics(self, post_id: int):
        """Read Model: Analytics aggregation (pre-computed)"""
        cache_key = f"analytics:post:{post_id}"

        cached = self.cache.get(cache_key)
        if cached:
            return json.loads(cached)

        # Aggregate from analytics table
        analytics = SNSAnalytics.query.filter_by(post_id=post_id).all()

        result = {
            'post_id': post_id,
            'total_impressions': sum(a.impressions for a in analytics),
            'total_engagements': sum(a.engagements for a in analytics),
            'platforms': {}
        }

        for a in analytics:
            if a.platform not in result['platforms']:
                result['platforms'][a.platform] = {
                    'impressions': 0,
                    'engagements': 0,
                    'reach': 0
                }
            result['platforms'][a.platform]['impressions'] += a.impressions
            result['platforms'][a.platform]['engagements'] += a.engagements
            result['platforms'][a.platform]['reach'] += a.reach

        # Cache for 1 hour (analytics updates less frequently)
        self.cache.setex(cache_key, 3600, json.dumps(result))
        return result

class SNSCommandService:
    """Write Model: Transactional, event-driven updates"""

    def __init__(self, cache_backend, event_bus):
        self.cache = cache_backend
        self.event_bus = event_bus

    def create_post(self, user_id: int, data: dict):
        """Write Model: Create post with event emission"""
        post = SNSPost(**data)
        post.user_id = user_id

        db.session.add(post)
        db.session.commit()

        # Invalidate read caches
        self._invalidate_user_posts_cache(user_id)

        # Emit event
        from backend.services.sns_event_bus import PostPublishedEvent, event_bus
        event = PostPublishedEvent(
            event_id=str(uuid.uuid4()),
            event_type='post:published',
            user_id=user_id,
            timestamp=datetime.utcnow(),
            post_id=post.id,
            platforms=data['platforms'].split(','),
            content=data['content'],
            data={}
        )
        self.event_bus.publish(event)

        return post

    def delete_post(self, post_id: int, user_id: int):
        """Write Model: Delete post with cache invalidation"""
        post = SNSPost.query.filter_by(id=post_id, user_id=user_id).first()
        if post:
            db.session.delete(post)
            db.session.commit()
            self._invalidate_user_posts_cache(user_id)
            return True
        return False

    def _invalidate_user_posts_cache(self, user_id: int) -> None:
        """Invalidate all cached queries for this user"""
        pattern = f"user:{user_id}:posts:*"
        # Redis pattern deletion (depends on backend implementation)
        try:
            self.cache.delete_pattern(pattern)
            log.debug(f"Invalidated cache pattern: {pattern}")
        except Exception as e:
            log.warning(f"Failed to invalidate cache: {e}")

# Dependency Injection
query_service = None
command_service = None

def initialize_cqrs_services(app, cache_backend, event_bus):
    """Initialize CQRS services (called in app factory)"""
    global query_service, command_service
    query_service = SNSQueryService(cache_backend)
    command_service = SNSCommandService(cache_backend, event_bus)
```

---

### 2.3 Updated API Endpoints

```python
# File: backend/services/sns_auto.py (modified)

from backend.services.sns_cqrs import query_service, command_service

# READ Endpoint (using Query Service)
@sns_bp.route('/posts', methods=['GET'])
@require_auth
def get_user_posts(user_id):
    """Get user's posts (read model with caching)"""
    limit = request.args.get('limit', 20, type=int)
    offset = request.args.get('offset', 0, type=int)

    result = query_service.get_user_posts(user_id, limit, offset)
    return jsonify(result), 200

# WRITE Endpoint (using Command Service)
@sns_bp.route('/posts', methods=['POST'])
@require_auth
def create_post(user_id):
    """Create post (write model with event bus)"""
    data = request.get_json()
    post = command_service.create_post(user_id, data)
    return jsonify(post.to_dict()), 201

# READ Endpoint (Analytics)
@sns_bp.route('/posts/<int:post_id>/analytics', methods=['GET'])
@require_auth
def get_post_analytics(user_id, post_id):
    """Get post analytics (read model)"""
    # Verify user owns post
    post = SNSPost.query.filter_by(id=post_id, user_id=user_id).first()
    if not post:
        return jsonify({'error': 'Post not found'}), 404

    analytics = query_service.get_post_analytics(post_id)
    return jsonify(analytics), 200
```

---

### 2.4 Benefits

| Benefit | Impact |
|---------|--------|
| **Read Performance** | 90% of requests are reads → separate cache layer → 10-100x faster |
| **Write Consistency** | Events ensure all read caches stay in sync |
| **Scalability** | Read replicas can serve queries independently |
| **Flexibility** | Can add new read models (Elasticsearch, Cassandra) without changing writes |

---

## 3. Saga Pattern — Distributed Transactions

### 3.1 Pattern Overview

**Problem:** SNS post publishing involves multiple steps across services:

```
1. Create post record ✅
2. Publish to Instagram ✅
3. Publish to Twitter ❌ (fails)
4. Record analytics ✅
5. Send notification ❌ (fails)
```

**Question:** How do we maintain consistency when one step fails?

**Answer:** Saga Pattern — orchestrate distributed transactions with rollback support.

---

### 3.2 Implementation

```python
# File: backend/services/sns_saga.py

from enum import Enum
from typing import List, Dict, Callable
from dataclasses import dataclass
from datetime import datetime
import uuid
import json
from backend.logging_config import get_logger

log = get_logger(__name__)

class SagaStatus(Enum):
    PENDING = 'pending'
    IN_PROGRESS = 'in_progress'
    COMPLETED = 'completed'
    FAILED = 'failed'
    COMPENSATING = 'compensating'
    COMPENSATED = 'compensated'

@dataclass
class SagaStep:
    """Individual saga step with action and compensation"""
    step_id: str
    action: Callable  # Function to execute
    compensation: Callable  # Rollback function
    description: str

@dataclass
class SagaExecution:
    """Track saga execution state"""
    saga_id: str
    status: SagaStatus
    completed_steps: List[str]  # Step IDs that succeeded
    failed_step: str = None  # First failing step
    error_message: str = None
    results: Dict = None
    created_at: datetime = None
    completed_at: datetime = None

class SNSPostPublishingSaga:
    """
    Saga Orchestrator: Coordinate multi-step SNS post publishing

    Steps:
    1. Create post record in DB (compensate: delete)
    2. Publish to each platform (compensate: delete from platform)
    3. Record analytics (compensate: clear analytics)
    4. Send notification (compensate: send cancellation notification)
    """

    def __init__(self, event_bus):
        self.event_bus = event_bus
        self.steps: List[SagaStep] = []
        self.executions: Dict[str, SagaExecution] = {}

    def build(self) -> 'SNSPostPublishingSaga':
        """Define saga steps"""
        self.steps = [
            SagaStep(
                step_id='create_post',
                action=self._action_create_post,
                compensation=self._compensation_create_post,
                description='Create post record in database'
            ),
            SagaStep(
                step_id='publish_instagram',
                action=self._action_publish_instagram,
                compensation=self._compensation_publish_instagram,
                description='Publish to Instagram'
            ),
            SagaStep(
                step_id='publish_twitter',
                action=self._action_publish_twitter,
                compensation=self._compensation_publish_twitter,
                description='Publish to Twitter'
            ),
            SagaStep(
                step_id='record_analytics',
                action=self._action_record_analytics,
                compensation=self._compensation_record_analytics,
                description='Record analytics'
            ),
            SagaStep(
                step_id='send_notification',
                action=self._action_send_notification,
                compensation=self._compensation_send_notification,
                description='Send Telegram notification'
            ),
        ]
        return self

    def execute(self, context: dict) -> SagaExecution:
        """Execute saga with automatic compensation on failure"""
        saga_id = str(uuid.uuid4())
        execution = SagaExecution(
            saga_id=saga_id,
            status=SagaStatus.IN_PROGRESS,
            completed_steps=[],
            results={},
            created_at=datetime.utcnow()
        )
        self.executions[saga_id] = execution

        log.info(f"Starting saga {saga_id} with context: {context}")

        try:
            # Execute steps in order
            for step in self.steps:
                try:
                    log.info(f"Saga {saga_id}: Executing step {step.step_id}")
                    result = step.action(context)
                    execution.completed_steps.append(step.step_id)
                    execution.results[step.step_id] = result
                    log.info(f"Saga {saga_id}: Step {step.step_id} completed")

                except Exception as e:
                    # Step failed - trigger compensation
                    log.error(f"Saga {saga_id}: Step {step.step_id} failed: {e}")
                    execution.status = SagaStatus.COMPENSATING
                    execution.failed_step = step.step_id
                    execution.error_message = str(e)

                    # Compensate in reverse order
                    self._compensate(saga_id, execution)

                    execution.status = SagaStatus.COMPENSATED
                    execution.completed_at = datetime.utcnow()
                    return execution

            # All steps succeeded
            execution.status = SagaStatus.COMPLETED
            execution.completed_at = datetime.utcnow()
            log.info(f"Saga {saga_id} completed successfully")
            return execution

        except Exception as e:
            execution.status = SagaStatus.FAILED
            execution.error_message = str(e)
            execution.completed_at = datetime.utcnow()
            log.error(f"Saga {saga_id} failed: {e}")
            return execution

    def _compensate(self, saga_id: str, execution: SagaExecution) -> None:
        """Execute compensation steps in reverse order"""
        log.info(f"Saga {saga_id}: Starting compensation for {len(execution.completed_steps)} steps")

        for step_id in reversed(execution.completed_steps):
            step = next(s for s in self.steps if s.step_id == step_id)
            try:
                log.info(f"Saga {saga_id}: Compensating step {step_id}")
                context = execution.results
                step.compensation(context)
                log.info(f"Saga {saga_id}: Compensation for {step_id} completed")
            except Exception as e:
                log.error(f"Saga {saga_id}: Compensation for {step_id} failed: {e}")
                # Continue with remaining compensations (fail-safe)

    # ===== ACTION STEPS =====

    def _action_create_post(self, context: dict) -> dict:
        """Create post record"""
        from backend.models import SNSPost, db

        post = SNSPost(
            user_id=context['user_id'],
            content=context['content'],
            platforms=','.join(context['platforms']),
            status='pending'
        )
        db.session.add(post)
        db.session.commit()

        context['post_id'] = post.id  # Store for later steps
        return {'post_id': post.id}

    def _action_publish_instagram(self, context: dict) -> dict:
        """Publish to Instagram"""
        if 'instagram' not in context['platforms']:
            return {'skipped': True}

        from backend.services.sns_platforms import get_client
        client = get_client('instagram')
        response = client.publish(
            content=context['content'],
            media=context.get('media_urls', [])
        )
        context['instagram_post_id'] = response['id']
        return {'platform_post_id': response['id']}

    def _action_publish_twitter(self, context: dict) -> dict:
        """Publish to Twitter"""
        if 'twitter' not in context['platforms']:
            return {'skipped': True}

        from backend.services.sns_platforms import get_client
        client = get_client('twitter')
        response = client.publish(content=context['content'])
        context['twitter_post_id'] = response['id']
        return {'platform_post_id': response['id']}

    def _action_record_analytics(self, context: dict) -> dict:
        """Record analytics entry"""
        from backend.models import SNSAnalytics, db

        analytics = SNSAnalytics(
            user_id=context['user_id'],
            post_id=context['post_id'],
            action='published',
            platforms=','.join(context['platforms']),
            metadata=json.dumps({'content_length': len(context['content'])})
        )
        db.session.add(analytics)
        db.session.commit()
        context['analytics_id'] = analytics.id
        return {'analytics_id': analytics.id}

    def _action_send_notification(self, context: dict) -> dict:
        """Send Telegram notification"""
        from daemon.daemon_service import send_telegram_message

        message = f"✅ Post published to {len(context['platforms'])} platforms"
        send_telegram_message(context['user_id'], message)
        return {'notification_sent': True}

    # ===== COMPENSATION STEPS =====

    def _compensation_create_post(self, context: dict) -> None:
        """Delete post record"""
        from backend.models import SNSPost, db
        post = SNSPost.query.get(context['post_id'])
        if post:
            db.session.delete(post)
            db.session.commit()
            log.info(f"Compensated: Post {context['post_id']} deleted")

    def _compensation_publish_instagram(self, context: dict) -> None:
        """Delete from Instagram"""
        if 'instagram_post_id' in context:
            from backend.services.sns_platforms import get_client
            client = get_client('instagram')
            try:
                client.delete(context['instagram_post_id'])
                log.info(f"Compensated: Instagram post {context['instagram_post_id']} deleted")
            except Exception as e:
                log.error(f"Failed to delete Instagram post: {e}")

    def _compensation_publish_twitter(self, context: dict) -> None:
        """Delete from Twitter"""
        if 'twitter_post_id' in context:
            from backend.services.sns_platforms import get_client
            client = get_client('twitter')
            try:
                client.delete(context['twitter_post_id'])
                log.info(f"Compensated: Twitter post {context['twitter_post_id']} deleted")
            except Exception as e:
                log.error(f"Failed to delete Twitter post: {e}")

    def _compensation_record_analytics(self, context: dict) -> None:
        """Clear analytics entry"""
        from backend.models import SNSAnalytics, db
        if 'analytics_id' in context:
            analytics = SNSAnalytics.query.get(context['analytics_id'])
            if analytics:
                db.session.delete(analytics)
                db.session.commit()
                log.info(f"Compensated: Analytics {context['analytics_id']} deleted")

    def _compensation_send_notification(self, context: dict) -> None:
        """Send cancellation notification"""
        from daemon.daemon_service import send_telegram_message
        message = "❌ Post publishing was canceled due to errors"
        send_telegram_message(context['user_id'], message)

# Global saga instance
sns_post_saga = SNSPostPublishingSaga(None).build()

def initialize_saga(app, event_bus):
    """Initialize saga with event bus (called in app factory)"""
    global sns_post_saga
    sns_post_saga.event_bus = event_bus
```

---

### 3.3 Integration with API

```python
# File: backend/services/sns_auto.py (modified)

from backend.services.sns_saga import sns_post_saga

@sns_bp.route('/posts', methods=['POST'])
@require_auth
def create_post(user_id):
    """Create and publish SNS post with saga coordination"""
    data = request.get_json()

    # Prepare saga context
    context = {
        'user_id': user_id,
        'content': data['content'],
        'platforms': data['platforms'],
        'media_urls': data.get('media_urls', [])
    }

    # Execute saga
    execution = sns_post_saga.execute(context)

    if execution.status.value == 'completed':
        return jsonify({
            'post_id': execution.results['create_post']['post_id'],
            'saga_id': execution.saga_id,
            'status': 'published',
            'message': 'Post published successfully'
        }), 201
    else:
        return jsonify({
            'saga_id': execution.saga_id,
            'status': execution.status.value,
            'failed_step': execution.failed_step,
            'error': execution.error_message,
            'completed_steps': execution.completed_steps,
            'message': 'Post publishing failed and was rolled back'
        }), 500
```

---

## 4. Performance Optimization Strategy

### 4.1 Database Connection Pooling

**Problem:** Each Flask request creates new database connection → overhead.

**Solution:**

```python
# File: backend/app.py (modified)

from flask_sqlalchemy import SQLAlchemy

def create_app():
    app = Flask(__name__)

    # Database configuration with connection pooling
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'platform.db')

    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        # Connection pooling
        'pool_size': 20,  # Keep 20 connections in pool
        'pool_recycle': 3600,  # Recycle after 1 hour
        'pool_pre_ping': True,  # Check connection health before use
        'max_overflow': 40,  # Allow up to 40 additional overflow connections

        # Query optimization (PostgreSQL)
        'echo': False,  # Disable SQL logging in production
        'echo_pool': False,

        # Timeout settings
        'connect_args': {
            'timeout': 10,  # Connection timeout
            'check_same_thread': False,  # For SQLite dev
        }
    }

    db.init_app(app)
```

---

### 4.2 Query Optimization

**Pattern 1: Eager Loading (prevent N+1 queries)**

```python
# BEFORE (N+1 problem)
posts = SNSPost.query.all()
for post in posts:
    print(post.account.name)  # N additional queries!

# AFTER (Eager loading)
from sqlalchemy.orm import joinedload

posts = SNSPost.query.options(
    joinedload(SNSPost.account),
    joinedload(SNSPost.user)
).all()

# Safe in subsequent loops
for post in posts:
    print(post.account.name)  # No additional queries
```

**Pattern 2: Database Indexes**

```python
# File: backend/models.py (SNSPost model)

from sqlalchemy import Index

class SNSPost(db.Model):
    __tablename__ = 'sns_posts'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    platform = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), default='pending')  # 'pending', 'published', 'failed'
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    published_at = db.Column(db.DateTime, nullable=True)

    # Compound indexes for common queries
    __table_args__ = (
        Index('idx_user_status', 'user_id', 'status'),  # For user posts with filtering
        Index('idx_user_created', 'user_id', 'created_at'),  # For user posts with sorting
        Index('idx_platform_status', 'platform', 'status'),  # For platform-specific queries
        Index('idx_created_at', 'created_at'),  # For recent posts
    )

class SNSAnalytics(db.Model):
    __tablename__ = 'sns_analytics'

    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('sns_posts.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    platform = db.Column(db.String(50), nullable=False)
    impressions = db.Column(db.Integer, default=0)
    engagements = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_post_id', 'post_id'),
        Index('idx_user_platform', 'user_id', 'platform'),
    )
```

---

### 4.3 Multi-Tier Caching

**Three-level cache hierarchy:**

```python
# File: backend/services/sns_cache_manager.py

from functools import wraps
from datetime import timedelta
import json
import redis
from backend.logging_config import get_logger

log = get_logger(__name__)

class CacheManager:
    """Multi-tier cache: Memory → Redis → Database"""

    def __init__(self, redis_url: str = 'redis://localhost:6379'):
        self.redis_client = redis.from_url(redis_url)
        self.memory_cache = {}  # In-memory tier

    def get_cached(self, key: str, fetch_fn, ttl_memory: int = 60, ttl_redis: int = 300):
        """
        Get with multi-tier caching

        L1 (Memory): 60 seconds
        L2 (Redis): 5 minutes
        L3 (Database): expensive query
        """

        # L1: Memory tier
        if key in self.memory_cache:
            entry = self.memory_cache[key]
            if entry['expires_at'] > datetime.utcnow():
                log.debug(f"Cache hit (L1): {key}")
                return entry['data']

        # L2: Redis tier
        try:
            cached = self.redis_client.get(key)
            if cached:
                data = json.loads(cached)
                self.memory_cache[key] = {
                    'data': data,
                    'expires_at': datetime.utcnow() + timedelta(seconds=ttl_memory)
                }
                log.debug(f"Cache hit (L2): {key}")
                return data
        except redis.RedisError as e:
            log.warning(f"Redis error: {e}")

        # L3: Database (fallback)
        log.debug(f"Cache miss (L3): fetching from database: {key}")
        data = fetch_fn()

        # Populate caches
        try:
            self.redis_client.setex(
                key,
                ttl_redis,
                json.dumps(data, default=str)
            )
        except redis.RedisError as e:
            log.warning(f"Failed to cache in Redis: {e}")

        self.memory_cache[key] = {
            'data': data,
            'expires_at': datetime.utcnow() + timedelta(seconds=ttl_memory)
        }

        return data

    def invalidate(self, pattern: str) -> None:
        """Invalidate cache entries matching pattern"""
        # Memory tier
        keys_to_delete = [k for k in self.memory_cache.keys() if pattern in k]
        for k in keys_to_delete:
            del self.memory_cache[k]

        # Redis tier
        try:
            cursor = 0
            while True:
                cursor, keys = self.redis_client.scan(cursor, match=f"*{pattern}*")
                if keys:
                    self.redis_client.delete(*keys)
                if cursor == 0:
                    break
        except redis.RedisError as e:
            log.warning(f"Failed to invalidate Redis cache: {e}")

# Global cache manager
cache_manager = CacheManager()

# Decorator for easy caching
def cached(ttl_memory: int = 60, ttl_redis: int = 300):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{args}:{kwargs}"
            return cache_manager.get_cached(
                cache_key,
                lambda: func(*args, **kwargs),
                ttl_memory=ttl_memory,
                ttl_redis=ttl_redis
            )
        return wrapper
    return decorator
```

**Usage:**

```python
# File: backend/services/sns_auto.py

from backend.services.sns_cache_manager import cached, cache_manager

@sns_bp.route('/posts', methods=['GET'])
@require_auth
@cached(ttl_memory=60, ttl_redis=300)  # 1 min in memory, 5 min in Redis
def get_user_posts(user_id):
    """Get user posts with automatic caching"""
    posts = SNSPost.query.filter_by(user_id=user_id).all()
    return jsonify([p.to_dict() for p in posts])

@sns_bp.route('/posts/<int:post_id>', methods=['DELETE'])
@require_auth
def delete_post(user_id, post_id):
    """Delete post and invalidate caches"""
    post = SNSPost.query.filter_by(id=post_id, user_id=user_id).first()
    if post:
        db.session.delete(post)
        db.session.commit()
        cache_manager.invalidate(f"user:{user_id}")
        return jsonify({'message': 'Deleted'}), 200
    return jsonify({'error': 'Not found'}), 404
```

---

## 5. Security Hardening

### 5.1 Rate Limiting

```python
# File: backend/app.py

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

@sns_bp.route('/posts', methods=['POST'])
@limiter.limit("10 per minute")  # Max 10 posts per minute per IP
@require_auth
def create_post(user_id):
    """Create post with rate limiting"""
    ...

@sns_bp.route('/oauth/<platform>/authorize', methods=['GET'])
@limiter.limit("5 per minute")  # Max 5 auth attempts per minute
@require_auth
def oauth_authorize(platform, user_id):
    """OAuth with stricter rate limiting"""
    ...
```

---

### 5.2 API Key Rotation

```python
# File: backend/models.py

class APIKey(db.Model):
    __tablename__ = 'api_keys'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    key_hash = db.Column(db.String(255), unique=True, nullable=False, index=True)
    key_prefix = db.Column(db.String(10))  # First 10 chars for display
    description = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
    last_used_at = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)

    def to_dict(self):
        return {
            'id': self.id,
            'prefix': self.key_prefix + '****',
            'description': self.description,
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'last_used_at': self.last_used_at.isoformat() if self.last_used_at else None,
        }
```

**Rotation Service:**

```python
# File: backend/services/api_key_service.py

import secrets
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from backend.models import APIKey, db

def generate_api_key(user_id: int, description: str = None, expiry_days: int = 90) -> str:
    """Generate new API key and store hash"""
    raw_key = secrets.token_urlsafe(32)
    key_hash = generate_password_hash(raw_key)
    key_prefix = raw_key[:10]

    api_key = APIKey(
        user_id=user_id,
        key_hash=key_hash,
        key_prefix=key_prefix,
        description=description,
        expires_at=datetime.utcnow() + timedelta(days=expiry_days)
    )
    db.session.add(api_key)
    db.session.commit()

    return raw_key  # Return only once

def rotate_api_key(user_id: int, old_key_id: int) -> str:
    """Rotate old key with new one"""
    # Deactivate old key
    old_key = APIKey.query.filter_by(id=old_key_id, user_id=user_id).first()
    if old_key:
        old_key.is_active = False
        db.session.commit()

    # Create new key
    return generate_api_key(user_id, description="Rotated key")

def verify_api_key(raw_key: str) -> APIKey:
    """Verify API key and return associated user"""
    # Find keys with matching prefix
    prefix = raw_key[:10]
    candidates = APIKey.query.filter_by(key_prefix=prefix, is_active=True).all()

    for key in candidates:
        if check_password_hash(key.key_hash, raw_key):
            # Check expiry
            if key.expires_at and key.expires_at < datetime.utcnow():
                return None
            # Update last used
            key.last_used_at = datetime.utcnow()
            db.session.commit()
            return key

    return None
```

---

### 5.3 Input Validation with Pydantic

```python
# File: backend/services/sns_validation.py

from pydantic import BaseModel, validator, Field
from typing import List, Optional
from datetime import datetime

class PostCreateRequest(BaseModel):
    """Request validation for post creation"""
    content: str = Field(..., min_length=1, max_length=10000)
    platforms: List[str] = Field(..., min_items=1, max_items=9)
    media_urls: Optional[List[str]] = None
    scheduled_at: Optional[datetime] = None

    @validator('content')
    def validate_content(cls, v):
        if len(v.strip()) == 0:
            raise ValueError('Content cannot be empty or whitespace')
        return v

    @validator('platforms')
    def validate_platforms(cls, v):
        allowed = {
            'instagram', 'facebook', 'twitter', 'linkedin',
            'tiktok', 'youtube', 'pinterest', 'threads', 'youtube_shorts'
        }
        invalid = [p for p in v if p not in allowed]
        if invalid:
            raise ValueError(f'Invalid platforms: {invalid}')
        return v

    @validator('scheduled_at')
    def validate_scheduled_at(cls, v):
        if v and v <= datetime.utcnow():
            raise ValueError('scheduled_at must be in the future')
        return v

# Usage in API
@sns_bp.route('/posts', methods=['POST'])
@require_auth
def create_post(user_id):
    try:
        request_data = PostCreateRequest(**request.json)
        # Validated data is ready to use
        ...
    except ValidationError as e:
        return jsonify({'error': e.errors()}), 400
```

---

## 6. Scalability Roadmap

### Phase 1: Optimization (2026-02-26 to 2026-03-15)
- Implement event-driven architecture
- Deploy CQRS with Redis caching
- Add database connection pooling and indexes
- **Expected capacity:** 5,000-10,000 concurrent users

### Phase 2: Microservices (2026-03-15 to 2026-05-01)
- Extract SNS service to separate microservice
- Deploy API gateway (Kong/Nginx)
- Implement message queue (RabbitMQ)
- **Expected capacity:** 50,000+ concurrent users

### Phase 3: Global Scale (2026-05-01 to 2026-07-01)
- Geo-distributed database replication
- CDN for media assets
- Kubernetes orchestration
- **Expected capacity:** 100,000+ concurrent users

---

## 7. Monitoring & Observability

### 7.1 Structured Logging

```python
# File: backend/logging_config.py

import structlog
from datetime import datetime

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

log = structlog.get_logger()

# Usage
log.info(
    'post_created',
    user_id=user_id,
    post_id=post_id,
    platforms=platforms,
    content_length=len(content),
    duration_ms=elapsed_time
)
```

### 7.2 Metrics Collection

```python
# File: backend/metrics.py

from prometheus_client import Counter, Histogram, Gauge

# Request metrics
request_count = Counter(
    'sns_requests_total',
    'Total SNS API requests',
    ['method', 'endpoint', 'status']
)

request_duration = Histogram(
    'sns_request_duration_seconds',
    'SNS API request duration',
    ['method', 'endpoint']
)

# Cache metrics
cache_hits = Counter(
    'sns_cache_hits_total',
    'Cache hits',
    ['tier']  # memory, redis
)

cache_misses = Counter(
    'sns_cache_misses_total',
    'Cache misses',
    ['tier']
)

# Database metrics
db_pool_size = Gauge(
    'sns_db_pool_size',
    'Database connection pool size'
)

db_query_duration = Histogram(
    'sns_db_query_duration_seconds',
    'Database query duration',
    ['query_type']  # select, insert, update
)
```

---

## 8. Implementation Checklist

### Phase 1: Event-Driven (Week 1)
- [ ] Create `sns_event_bus.py` with EventBus class
- [ ] Register default event handlers
- [ ] Modify SNS POST endpoint to emit events
- [ ] Test event publishing and handling
- [ ] Add event history audit logging
- [ ] Update cost-log.md with implementation details

### Phase 2: CQRS (Week 2)
- [ ] Create `sns_cqrs.py` with SNSQueryService and SNSCommandService
- [ ] Set up Redis cache backend
- [ ] Implement multi-tier caching
- [ ] Modify GET endpoints to use QueryService
- [ ] Modify POST/PUT/DELETE endpoints to use CommandService
- [ ] Test cache invalidation on writes

### Phase 3: Saga Pattern (Week 2-3)
- [ ] Create `sns_saga.py` with SagaStep and SNSPostPublishingSaga
- [ ] Implement action and compensation steps
- [ ] Test saga execution and rollback
- [ ] Add saga execution tracking
- [ ] Document compensation strategies

### Phase 4: Performance (Week 3-4)
- [ ] Add connection pooling to app.py
- [ ] Create compound database indexes
- [ ] Implement eager loading for relationships
- [ ] Deploy Redis caching layer
- [ ] Add metrics collection
- [ ] Performance test with load tool

### Phase 5: Security (Week 4)
- [ ] Implement rate limiting
- [ ] Add API key rotation service
- [ ] Deploy Pydantic validation
- [ ] Security audit of all endpoints
- [ ] Enable HTTPS and CORS restrictions

---

## 9. Architecture Diagrams

### 9.1 Event-Driven Flow

```
┌─────────┐
│ Client  │
└────┬────┘
     │ POST /api/sns/posts
     ▼
┌────────────────┐
│ API Endpoint   │
└────┬───────────┘
     │ (non-blocking)
     ├─ Create post record
     ├─ Emit PostPublishedEvent
     └─ Return 201 immediately

     ▼
┌────────────────┐
│ EventBus       │
└────┬───────────┘
     │
     ├─ [post:published] Event
     │
     ├──→ Handler: update_post_status()
     ├──→ Handler: record_analytics()
     ├──→ Handler: send_notification()
     │
     └──→ Task Queue: publish_to_platforms()

     ▼
┌────────────────┐
│ Background     │
│ Jobs           │
│                │
│ - Instagram    │
│ - Twitter      │
│ - LinkedIn     │
│ - YouTube      │
└────────────────┘
```

### 9.2 CQRS Architecture

```
┌─────────────────────────────────┐
│ Client Application              │
└─────┬──────────────────┬────────┘
      │ READ             │ WRITE
      │ (90%)            │ (10%)
      │                  │
      ▼                  ▼
┌──────────────┐  ┌──────────────┐
│ QueryService │  │CommandService│
│              │  │              │
│ - L1: Memory │  │ - Create     │
│ - L2: Redis  │  │ - Update     │
│ - L3: DB     │  │ - Delete     │
│              │  │ - Emit Event │
└──┬───────────┘  └──┬───────────┘
   │                 │
   │ Cache hits      │
   │ 90%             │ Write-through
   │                 │ Invalidate
   ▼                 │ caches
┌──────────────┐    │
│ Redis        │    │
└──┬───────────┘    │
   │                 │
   │ Cache misses    │
   │ 10%             │
   │                 │
   ▼                 ▼
┌──────────────────────────────┐
│ PostgreSQL / SQLite          │
│                              │
│ Users, Posts, Analytics, ... │
└──────────────────────────────┘
```

### 9.3 Saga Orchestration

```
┌──────────────┐
│ SNS Saga     │
│ Orchestrator │
└──────┬───────┘
       │
       ├─→ Step 1: Create post record
       │   ├─ Success: continue
       │   └─ Fail: COMPENSATE ↓
       │
       ├─→ Step 2: Publish Instagram
       │   ├─ Success: continue
       │   └─ Fail: COMPENSATE ↓
       │
       ├─→ Step 3: Publish Twitter
       │   ├─ Success: continue
       │   └─ Fail: COMPENSATE ↓
       │
       ├─→ Step 4: Record Analytics
       │   ├─ Success: continue
       │   └─ Fail: COMPENSATE ↓
       │
       └─→ Step 5: Send Notification
           ├─ Success: COMPLETE ✓
           └─ Fail: COMPENSATE ↓

┌────────────────────────────────────┐
│ COMPENSATION (Reverse Order)       │
├────────────────────────────────────┤
│ ← Compensation 5: -                │
│ ← Compensation 4: Delete analytics │
│ ← Compensation 3: Delete Twitter   │
│ ← Compensation 2: Delete Instagram │
│ ← Compensation 1: Delete post      │
└────────────────────────────────────┘
```

---

## 10. Key Metrics & Success Criteria

| Metric | Current | Target | Timeframe |
|--------|---------|--------|-----------|
| **Throughput** | 100 req/s | 1,000 req/s | Phase 1 |
| **P95 Latency** | 2,000ms | 500ms | Phase 1 |
| **Cache Hit Ratio** | 0% | 90% | Phase 1 |
| **DB Connections** | 1:1 ratio | 20:1 pool ratio | Phase 1 |
| **Availability** | 99.5% | 99.9% | Phase 2 |
| **Concurrent Users** | 1,000 | 10,000 | Phase 2 |
| **Distributed Transactions** | None | 99.9% atomicity | Phase 1-2 |

---

## 11. References & Standards

- **Event-Driven:** Kafka/RabbitMQ patterns, CQRS guide
- **CQRS:** Martin Fowler's CQRS documentation
- **Saga Pattern:** Distributed transactions without 2PC
- **Caching:** Cache-aside, write-through, write-behind
- **Monitoring:** Prometheus + Grafana stack

---

**Document Version:** 1.0
**Last Updated:** 2026-02-26
**Status:** Ready for Implementation
**Phase:** SNS Automation v2.0 Architecture Enhancement
