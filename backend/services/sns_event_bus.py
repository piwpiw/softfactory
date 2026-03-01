"""SNS Event Bus - Event-Driven Architecture for SNS Operations

Provides publish-subscribe pattern for decoupling SNS operations from API responses.
All SNS events (post published, deleted, analytics updated) are published to this bus.

Events:
- post:published — Post successfully published to platforms
- post:failed — Post publishing failed
- post:deleted — Post deleted by user
- analytics:updated — Analytics data updated for post
"""

from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import Dict, List, Callable, Optional
from enum import Enum
import uuid
import json
import threading
from backend.logging_config import get_logger

log = get_logger(__name__)


class EventType(Enum):
    """Enumeration of SNS event types"""
    POST_PUBLISHED = 'post:published'
    POST_FAILED = 'post:failed'
    POST_DELETED = 'post:deleted'
    ANALYTICS_UPDATED = 'analytics:updated'
    CAMPAIGN_LAUNCHED = 'campaign:launched'
    INBOX_MESSAGE_RECEIVED = 'inbox:message_received'


@dataclass
class SNSEvent:
    """Base event class for all SNS operations"""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str = ''
    user_id: int = 0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    data: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Convert event to dictionary for serialization"""
        return {
            'event_id': self.event_id,
            'event_type': self.event_type,
            'user_id': self.user_id,
            'timestamp': self.timestamp.isoformat(),
            'data': self.data
        }

    def to_json(self) -> str:
        """Convert event to JSON string"""
        return json.dumps(self.to_dict(), default=str)


@dataclass
class PostPublishedEvent(SNSEvent):
    """Event fired when a post is successfully published to platforms"""
    post_id: int = 0
    platforms: List[str] = field(default_factory=list)
    content: str = ''
    scheduled: bool = False

    def __post_init__(self):
        self.event_type = EventType.POST_PUBLISHED.value
        self.data = {
            'post_id': self.post_id,
            'platforms': self.platforms,
            'content_length': len(self.content),
            'scheduled': self.scheduled
        }


@dataclass
class PostFailedEvent(SNSEvent):
    """Event fired when post publishing fails"""
    post_id: Optional[int] = None
    platform: str = ''
    error_message: str = ''
    error_type: str = ''

    def __post_init__(self):
        self.event_type = EventType.POST_FAILED.value
        self.data = {
            'post_id': self.post_id,
            'platform': self.platform,
            'error_message': self.error_message,
            'error_type': self.error_type
        }


@dataclass
class PostDeletedEvent(SNSEvent):
    """Event fired when a post is deleted"""
    post_id: int = 0
    platforms: List[str] = field(default_factory=list)

    def __post_init__(self):
        self.event_type = EventType.POST_DELETED.value
        self.data = {
            'post_id': self.post_id,
            'platforms': self.platforms
        }


@dataclass
class AnalyticsUpdatedEvent(SNSEvent):
    """Event fired when analytics are updated for a post"""
    post_id: int = 0
    platform: str = ''
    impressions: int = 0
    engagements: int = 0
    reach: int = 0

    def __post_init__(self):
        self.event_type = EventType.ANALYTICS_UPDATED.value
        self.data = {
            'post_id': self.post_id,
            'platform': self.platform,
            'impressions': self.impressions,
            'engagements': self.engagements,
            'reach': self.reach
        }


class EventBus:
    """
    Publish-Subscribe Event Bus for SNS Operations

    Decouples event publishers from subscribers, allowing asynchronous processing.
    Maintains event history for audit and replay capabilities.

    Usage:
        bus = EventBus()
        bus.subscribe('post:published', handle_post_published)
        event = PostPublishedEvent(user_id=1, post_id=123, platforms=['instagram'])
        bus.publish(event)
    """

    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}
        self._event_history: List[SNSEvent] = []
        self._history_lock = threading.Lock()  # Thread-safe history access
        self._max_history_size = 10000  # Keep last 10k events

    def subscribe(self, event_type: str, handler: Callable, priority: int = 0) -> None:
        """
        Subscribe a handler to an event type

        Args:
            event_type: Event type to subscribe to (e.g., 'post:published')
            handler: Callable that receives the event
            priority: Higher priority handlers are called first (default: 0)
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []

        self._subscribers[event_type].append((priority, handler))
        self._subscribers[event_type].sort(key=lambda x: x[0], reverse=True)

        log.info(
            f"Handler subscribed to event",
            extra={
                'handler': handler.__name__,
                'event_type': event_type,
                'priority': priority
            }
        )

    def unsubscribe(self, event_type: str, handler: Callable) -> bool:
        """Remove a handler from an event type"""
        if event_type not in self._subscribers:
            return False

        original_len = len(self._subscribers[event_type])
        self._subscribers[event_type] = [
            (p, h) for p, h in self._subscribers[event_type]
            if h != handler
        ]

        if len(self._subscribers[event_type]) < original_len:
            log.info(
                f"Handler unsubscribed from event",
                extra={'handler': handler.__name__, 'event_type': event_type}
            )
            return True
        return False

    def publish(self, event: SNSEvent, async_handlers: bool = False) -> None:
        """
        Publish an event to all subscribed handlers

        Args:
            event: SNSEvent instance to publish
            async_handlers: If True, handlers run in separate threads (default: False)
        """
        # Store in history
        with self._history_lock:
            self._event_history.append(event)
            # Keep only last N events to prevent memory bloat
            if len(self._event_history) > self._max_history_size:
                self._event_history = self._event_history[-self._max_history_size:]

        log.info(
            f"Event published",
            extra={
                'event_id': event.event_id,
                'event_type': event.event_type,
                'user_id': event.user_id,
                'timestamp': event.timestamp.isoformat()
            }
        )

        # Notify subscribers
        if event.event_type in self._subscribers:
            handlers = self._subscribers[event.event_type]

            for priority, handler in handlers:
                if async_handlers:
                    # Run in separate thread (non-blocking)
                    thread = threading.Thread(
                        target=self._safe_call_handler,
                        args=(handler, event)
                    )
                    thread.daemon = True
                    thread.start()
                else:
                    # Run synchronously
                    self._safe_call_handler(handler, event)

    def _safe_call_handler(self, handler: Callable, event: SNSEvent) -> None:
        """Safely call a handler with error handling"""
        try:
            handler(event)
        except Exception as e:
            log.error(
                f"Event handler failed",
                extra={
                    'handler': handler.__name__,
                    'event_type': event.event_type,
                    'event_id': event.event_id,
                    'error': str(e)
                },
                exc_info=True
            )

    def get_history(
        self,
        event_type: Optional[str] = None,
        user_id: Optional[int] = None,
        limit: int = 100
    ) -> List[SNSEvent]:
        """
        Retrieve event history for audit/debugging

        Args:
            event_type: Filter by event type (optional)
            user_id: Filter by user ID (optional)
            limit: Maximum number of events to return
        """
        with self._history_lock:
            results = list(self._event_history)

        if event_type:
            results = [e for e in results if e.event_type == event_type]
        if user_id:
            results = [e for e in results if e.user_id == user_id]

        return results[-limit:]

    def get_statistics(self) -> Dict:
        """Get event bus statistics"""
        with self._history_lock:
            events = list(self._event_history)

        stats = {
            'total_events': len(events),
            'unique_event_types': len(set(e.event_type for e in events)),
            'unique_users': len(set(e.user_id for e in events)),
            'handlers_registered': sum(len(h) for h in self._subscribers.values()),
            'event_types': list(set(e.event_type for e in events))
        }

        return stats


# Global event bus instance
event_bus = EventBus()


def register_default_handlers(event_bus_instance: EventBus = None) -> None:
    """
    Register default event handlers for SNS operations

    Called during application initialization to set up core handlers.
    """
    global event_bus
    if event_bus_instance:
        event_bus = event_bus_instance

    # Register handlers with priority (higher = earlier execution)
    event_bus.subscribe('post:published', handle_post_published, priority=100)
    event_bus.subscribe('post:published', record_analytics, priority=50)
    event_bus.subscribe('post:published', send_notification, priority=10)

    event_bus.subscribe('post:failed', handle_post_failed, priority=100)
    event_bus.subscribe('post:failed', notify_user_of_failure, priority=50)

    event_bus.subscribe('post:deleted', handle_post_deleted, priority=100)

    event_bus.subscribe('analytics:updated', update_post_summary, priority=50)

    log.info("Default event handlers registered")


# ============ DEFAULT HANDLERS ============

def handle_post_published(event: PostPublishedEvent) -> None:
    """
    Handler: Update post status to published

    Executed when a post is successfully published.
    """
    try:
        from backend.models import SNSPost, db

        post = SNSPost.query.get(event.post_id)
        if post:
            post.status = 'published'
            post.published_at = datetime.utcnow()
            db.session.commit()

            log.info(
                f"Post marked as published",
                extra={'post_id': event.post_id, 'platforms': event.platforms}
            )
        else:
            log.warning(f"Post not found", extra={'post_id': event.post_id})

    except Exception as e:
        log.error(f"Failed to handle post published event", exc_info=True)


def record_analytics(event: PostPublishedEvent) -> None:
    """
    Handler: Record analytics entry for published post

    Creates analytics record to track impressions, engagements, etc.
    """
    try:
        from backend.models import SNSAnalytics, db

        for platform in event.platforms:
            analytics = SNSAnalytics(
                user_id=event.user_id,
                post_id=event.post_id,
                platform=platform,
                action='published',
                metadata=json.dumps({
                    'content_length': len(event.content),
                    'scheduled': event.scheduled,
                    'published_at': datetime.utcnow().isoformat()
                })
            )
            db.session.add(analytics)

        db.session.commit()

        log.info(
            f"Analytics recorded for published post",
            extra={'post_id': event.post_id, 'platforms': event.platforms}
        )

    except Exception as e:
        log.error(f"Failed to record analytics", exc_info=True)


def send_notification(event: PostPublishedEvent) -> None:
    """
    Handler: Send notification to user (Telegram/Email)

    Notifies user that their post has been published.
    """
    try:
        # Import here to avoid circular dependency
        from daemon.daemon_service import send_telegram_message

        platforms_str = ', '.join(event.platforms)
        message = f"✅ Your post has been published to {platforms_str}"

        send_telegram_message(event.user_id, message)

        log.info(
            f"Notification sent to user",
            extra={'user_id': event.user_id, 'post_id': event.post_id}
        )

    except ImportError:
        log.warning("Telegram daemon not available, skipping notification")
    except Exception as e:
        log.error(f"Failed to send notification", exc_info=True)


def handle_post_failed(event: PostFailedEvent) -> None:
    """Handler: Update post status to failed"""
    try:
        from backend.models import SNSPost, db

        if event.post_id:
            post = SNSPost.query.get(event.post_id)
            if post:
                post.status = 'failed'
                post.error_message = event.error_message
                db.session.commit()

                log.error(
                    f"Post publishing failed",
                    extra={
                        'post_id': event.post_id,
                        'platform': event.platform,
                        'error': event.error_message
                    }
                )

    except Exception as e:
        log.error(f"Failed to handle post failed event", exc_info=True)


def notify_user_of_failure(event: PostFailedEvent) -> None:
    """Handler: Notify user of posting failure"""
    try:
        from daemon.daemon_service import send_telegram_message

        message = f"❌ Failed to publish post on {event.platform}: {event.error_message}"
        send_telegram_message(event.user_id, message)

        log.info(
            f"Failure notification sent",
            extra={'user_id': event.user_id, 'post_id': event.post_id}
        )

    except Exception as e:
        log.error(f"Failed to send failure notification", exc_info=True)


def handle_post_deleted(event: PostDeletedEvent) -> None:
    """Handler: Handle post deletion"""
    try:
        from backend.models import SNSPost, db

        post = SNSPost.query.get(event.post_id)
        if post:
            db.session.delete(post)
            db.session.commit()

            log.info(
                f"Post deleted",
                extra={'post_id': event.post_id, 'platforms': event.platforms}
            )

    except Exception as e:
        log.error(f"Failed to handle post deleted event", exc_info=True)


def update_post_summary(event: AnalyticsUpdatedEvent) -> None:
    """Handler: Update post summary analytics"""
    try:
        from backend.models import SNSPost, db

        post = SNSPost.query.get(event.post_id)
        if post:
            # Update post summary fields
            if not hasattr(post, 'total_impressions'):
                post.total_impressions = 0
                post.total_engagements = 0

            post.total_impressions += event.impressions
            post.total_engagements += event.engagements
            db.session.commit()

            log.info(
                f"Post summary updated",
                extra={
                    'post_id': event.post_id,
                    'impressions': event.impressions,
                    'engagements': event.engagements
                }
            )

    except Exception as e:
        log.error(f"Failed to update post summary", exc_info=True)


# ============ UTILITY FUNCTIONS ============

def get_event_bus() -> EventBus:
    """Get the global event bus instance"""
    global event_bus
    return event_bus


def reset_event_bus() -> None:
    """Reset event bus (for testing)"""
    global event_bus
    event_bus = EventBus()
