"""
Consultation Bus — Inter-Agent Communication & Collaboration
Real-time message passing, decision coordination, conflict resolution
"""

import json
import uuid
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime
import logging
from queue import PriorityQueue, Empty
import threading

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """Message categories"""
    REQUEST = "request"
    RESPONSE = "response"
    QUESTION = "question"
    DECISION = "decision"
    ALERT = "alert"
    UPDATE = "update"
    HANDOFF = "handoff"
    ACK = "ack"


class MessagePriority(Enum):
    """Message urgency levels"""
    LOW = 3
    NORMAL = 2
    HIGH = 1
    CRITICAL = 0


@dataclass
class Message:
    """Inter-agent message"""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    from_agent: str = ""
    to_agent: Optional[str] = None  # None = broadcast
    message_type: MessageType = MessageType.REQUEST
    priority: MessagePriority = MessagePriority.NORMAL

    # Content
    subject: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)

    # Coordination
    requires_decision: bool = False
    decision_deadline: Optional[str] = None
    related_task_id: Optional[str] = None

    # Metadata
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    status: str = "pending"
    replies: List['Message'] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict (for JSON serialization)"""
        data = asdict(self)
        data['message_type'] = self.message_type.value
        data['priority'] = self.priority.value
        data['replies'] = [r.to_dict() for r in self.replies]
        return data

    def is_urgent(self) -> bool:
        """Check if message is time-critical"""
        return self.priority in [MessagePriority.HIGH, MessagePriority.CRITICAL]


@dataclass
class Decision:
    """Recorded decision point"""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    message_id: str = ""
    approver_agent: str = ""
    choice: str = ""
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    rationale: str = ""
    impact: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ConsultationBus:
    """
    Central message bus for agent collaboration

    Patterns:
    - Request-Response: Agent A → Agent B (specific answer)
    - Broadcast: Agent A → All (information sharing)
    - Question: Agent A → Orchestrator (decision needed)
    - Handoff: Agent A → Agent B (task transfer)
    """

    def __init__(self, max_queue_size: int = 1000):
        self.queue: PriorityQueue = PriorityQueue(maxsize=max_queue_size)
        self.messages: Dict[str, Message] = {}  # Archived messages
        self.decisions: Dict[str, Decision] = {}  # Decision log
        self.subscriptions: Dict[str, List[Callable]] = {}  # Event listeners
        self.lock = threading.RLock()

    def publish(self, message: Message) -> bool:
        """
        Publish message to bus

        Returns:
            True if queued, False if queue full
        """
        try:
            with self.lock:
                # Convert priority to queue priority (lower = higher priority)
                priority_value = message.priority.value
                # Use message ID as tiebreaker to avoid comparing Message objects
                self.queue.put((priority_value, message.created_at, message.id, message), block=False)
                self.messages[message.id] = message

                # Log
                logger.info(
                    f"Message {message.id} | {message.from_agent} → "
                    f"{message.to_agent or 'BROADCAST'} | "
                    f"{message.message_type.value}"
                )

                # Trigger subscriptions
                self._trigger_subscriptions(message)
                return True
        except Exception as e:
            logger.error(f"Failed to publish message: {e}")
            return False

    def consume(self, agent_id: str, timeout: float = 0.5) -> Optional[Message]:
        """
        Retrieve next message for agent

        Returns:
            Message if available (targeted or broadcast), None if timeout
        """
        try:
            while True:
                _, _, _, message = self.queue.get(timeout=timeout)

                # Check if message is for this agent
                if message.to_agent is None:  # Broadcast
                    return message
                elif message.to_agent == agent_id:  # Targeted
                    return message
                # Not for this agent, re-queue
                else:
                    self.queue.put(
                        (message.priority.value, message.created_at, message.id, message)
                    )
        except Empty:
            return None

    def request(
        self,
        from_agent: str,
        to_agent: str,
        subject: str,
        payload: Dict[str, Any],
        require_response: bool = True
    ) -> str:
        """
        Send request message

        Returns:
            Message ID for tracking response
        """
        message = Message(
            from_agent=from_agent,
            to_agent=to_agent,
            message_type=MessageType.REQUEST,
            priority=MessagePriority.NORMAL,
            subject=subject,
            payload=payload
        )
        self.publish(message)
        return message.id

    def ask_question(
        self,
        from_agent: str,
        subject: str,
        payload: Dict[str, Any],
        requires_decision: bool = True
    ) -> str:
        """
        Ask orchestrator (broadcast question)

        Returns:
            Message ID for tracking answer
        """
        message = Message(
            from_agent=from_agent,
            to_agent=None,  # Broadcast to orchestrator
            message_type=MessageType.QUESTION,
            priority=MessagePriority.HIGH,
            subject=subject,
            payload=payload,
            requires_decision=requires_decision
        )
        self.publish(message)
        return message.id

    def alert(
        self,
        from_agent: str,
        subject: str,
        payload: Dict[str, Any],
        is_critical: bool = False
    ) -> str:
        """
        Send alert (escalation)

        Returns:
            Message ID
        """
        message = Message(
            from_agent=from_agent,
            to_agent=None,  # Broadcast alert
            message_type=MessageType.ALERT,
            priority=MessagePriority.CRITICAL if is_critical else MessagePriority.HIGH,
            subject=subject,
            payload=payload
        )
        self.publish(message)
        return message.id

    def handoff(
        self,
        from_agent: str,
        to_agent: str,
        task_id: str,
        context: Dict[str, Any]
    ) -> str:
        """
        Hand off task to another agent

        Returns:
            Message ID
        """
        message = Message(
            from_agent=from_agent,
            to_agent=to_agent,
            message_type=MessageType.HANDOFF,
            priority=MessagePriority.HIGH,
            subject=f"Handoff task {task_id}",
            payload={"task_id": task_id, "context": context},
            related_task_id=task_id
        )
        self.publish(message)
        return message.id

    def reply(
        self,
        to_message_id: str,
        from_agent: str,
        payload: Dict[str, Any],
        is_decision: bool = False
    ) -> str:
        """
        Reply to specific message

        Returns:
            Message ID
        """
        original = self.messages.get(to_message_id)
        if not original:
            logger.error(f"Original message {to_message_id} not found")
            return ""

        message = Message(
            from_agent=from_agent,
            to_agent=original.from_agent,
            message_type=MessageType.DECISION if is_decision else MessageType.RESPONSE,
            priority=MessagePriority.HIGH,
            subject=f"Re: {original.subject}",
            payload=payload
        )

        self.publish(message)
        original.replies.append(message)
        return message.id

    def record_decision(
        self,
        message_id: str,
        approver_agent: str,
        choice: str,
        rationale: str = "",
        impact: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Record decision made in response to question

        Returns:
            Decision ID
        """
        decision = Decision(
            message_id=message_id,
            approver_agent=approver_agent,
            choice=choice,
            rationale=rationale,
            impact=impact or {}
        )

        with self.lock:
            self.decisions[decision.id] = decision

        logger.info(
            f"Decision {decision.id} | {approver_agent} → {choice}"
        )

        return decision.id

    def subscribe(
        self,
        event_type: str,
        callback: Callable[[Message], None],
        agent_id: Optional[str] = None
    ):
        """
        Subscribe to messages (event listener pattern)

        event_type: "request", "question", "alert", "handoff", etc.
        callback: Function to call when matching message arrives
        agent_id: Only listen if agent_id is recipient (None = all)
        """
        key = f"{event_type}:{agent_id or 'all'}"
        if key not in self.subscriptions:
            self.subscriptions[key] = []
        self.subscriptions[key].append(callback)

    def _trigger_subscriptions(self, message: Message):
        """Trigger subscribed callbacks for message"""
        # Generic subscriptions
        key = f"{message.message_type.value}:all"
        if key in self.subscriptions:
            for callback in self.subscriptions[key]:
                try:
                    callback(message)
                except Exception as e:
                    logger.error(f"Subscription callback failed: {e}")

        # Agent-specific subscriptions
        if message.to_agent:
            key = f"{message.message_type.value}:{message.to_agent}"
            if key in self.subscriptions:
                for callback in self.subscriptions[key]:
                    try:
                        callback(message)
                    except Exception as e:
                        logger.error(f"Subscription callback failed: {e}")

    def get_message_stats(self) -> Dict[str, Any]:
        """Get bus statistics"""
        with self.lock:
            return {
                "total_messages": len(self.messages),
                "queue_size": self.queue.qsize(),
                "decisions_recorded": len(self.decisions),
                "subscriptions": len(self.subscriptions)
            }

    def clear_old_messages(self, keep_count: int = 500):
        """Archive old messages to save memory"""
        with self.lock:
            if len(self.messages) > keep_count:
                # Keep newest N messages
                sorted_messages = sorted(
                    self.messages.items(),
                    key=lambda x: x[1].created_at,
                    reverse=True
                )
                to_keep = dict(sorted_messages[:keep_count])
                self.messages = to_keep
                logger.info(f"Archived messages, keeping {len(to_keep)}")


# Global bus instance
_bus: Optional[ConsultationBus] = None


def get_bus() -> ConsultationBus:
    """Get or create global consultation bus"""
    global _bus
    if _bus is None:
        _bus = ConsultationBus()
    return _bus


def reset_bus():
    """Reset global bus (for testing)"""
    global _bus
    _bus = None
