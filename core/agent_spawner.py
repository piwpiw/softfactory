"""
Agent Spawner — Dynamic Agent Generation & Lifecycle Management
Enables agent-generated-agents (recursive agent creation)
"""

import json
import uuid
from typing import Dict, Any, List, Optional, Type
from dataclasses import dataclass, field, asdict
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class AgentRole(Enum):
    """Role hierarchy"""
    ORCHESTRATOR = "orchestrator"
    BUSINESS = "business-strategist"
    ARCHITECT = "architect"
    DEVELOPER = "developer"
    QA = "qa-engineer"
    DEVOPS = "devops"
    SECURITY = "security-auditor"
    SUPPORT = "support"
    SPECIALIST = "specialist"  # Dynamic roles


class AgentStatus(Enum):
    """Agent lifecycle states"""
    PENDING = "pending"
    ACTIVE = "active"
    WORKING = "working"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED = "failed"
    IDLE = "idle"


@dataclass
class AgentCapability:
    """Single capability declaration"""
    name: str
    required: bool = False
    cost_estimate: int = 1000  # tokens
    priority: int = 5  # 1-10
    skills: List[str] = field(default_factory=list)


@dataclass
class AgentAuthority:
    """Authority boundaries"""
    max_parallel_agents: int = 4
    can_spawn_agents: bool = False
    can_override_decisions: bool = False
    scoped_to_phases: List[str] = field(default_factory=list)
    forbidden_actions: List[str] = field(default_factory=list)


@dataclass
class AgentProfile:
    """Complete agent definition"""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    role: AgentRole = AgentRole.SUPPORT
    name: str = ""
    status: AgentStatus = AgentStatus.PENDING
    parent_id: Optional[str] = None  # Agent that spawned this one

    # Capabilities & Authority
    capabilities: List[AgentCapability] = field(default_factory=list)
    authority: AgentAuthority = field(default_factory=AgentAuthority)

    # Execution context
    assigned_task_id: Optional[str] = None
    token_budget: int = 5000
    token_used: int = 0

    # Metadata
    created_at: str = ""
    updated_at: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def is_available(self) -> bool:
        """Check if agent can accept new work"""
        return (
            self.status in [AgentStatus.IDLE, AgentStatus.ACTIVE]
            and self.token_used < self.token_budget
        )

    def can_spawn_agents(self) -> bool:
        """Check if this agent can create sub-agents"""
        return self.authority.can_spawn_agents


class AgentSpawner:
    """
    Spawns and manages agent instances
    Enables agent-generated-agents pattern
    """

    def __init__(self, max_agents: int = 20, registry_path: str = "orchestrator/agent-registry.md"):
        self.agents: Dict[str, AgentProfile] = {}
        self.max_agents = max_agents
        self.registry_path = registry_path
        self._load_registry()

    def _load_registry(self):
        """Load agent authority matrix from registry"""
        try:
            with open(self.registry_path, 'r', encoding='utf-8') as f:
                content = f.read()
            logger.info(f"Loaded agent registry from {self.registry_path}")
        except FileNotFoundError:
            logger.warning(f"Registry not found at {self.registry_path}, using defaults")

    def spawn(
        self,
        role: AgentRole,
        capabilities: List[AgentCapability],
        parent_id: Optional[str] = None,
        token_budget: int = 5000,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[AgentProfile]:
        """
        Spawn a new agent instance

        Args:
            role: Agent role
            capabilities: List of required capabilities
            parent_id: ID of parent agent (if spawned by another agent)
            token_budget: Token allocation
            metadata: Custom metadata

        Returns:
            AgentProfile if successful, None if limits exceeded
        """
        # Check limits
        if len(self.agents) >= self.max_agents:
            logger.warning(f"Agent limit reached ({self.max_agents}), cannot spawn {role.value}")
            return None

        # Validate parent authority if spawning from agent
        if parent_id:
            parent = self.agents.get(parent_id)
            if not parent or not parent.can_spawn_agents():
                logger.error(f"Parent {parent_id} cannot spawn agents")
                return None

        # Create profile
        profile = AgentProfile(
            role=role,
            name=f"{role.value}-{uuid.uuid4().hex[:6]}",
            parent_id=parent_id,
            capabilities=capabilities,
            token_budget=token_budget,
            metadata=metadata or {}
        )

        # Register
        self.agents[profile.id] = profile
        logger.info(f"Spawned agent {profile.id} ({role.value}) | parent: {parent_id}")

        return profile

    def get_agent(self, agent_id: str) -> Optional[AgentProfile]:
        """Retrieve agent by ID"""
        return self.agents.get(agent_id)

    def list_agents(self, status: Optional[AgentStatus] = None) -> List[AgentProfile]:
        """List agents, optionally filtered by status"""
        agents = list(self.agents.values())
        if status:
            agents = [a for a in agents if a.status == status]
        return agents

    def find_available_agents(self, role: Optional[AgentRole] = None) -> List[AgentProfile]:
        """Find agents available for work"""
        candidates = [a for a in self.agents.values() if a.is_available()]
        if role:
            candidates = [a for a in candidates if a.role == role]
        return candidates

    def update_status(self, agent_id: str, status: AgentStatus):
        """Update agent status"""
        if agent_id in self.agents:
            self.agents[agent_id].status = status
            logger.debug(f"Agent {agent_id} status → {status.value}")

    def allocate_task(self, agent_id: str, task_id: str) -> bool:
        """Assign task to agent"""
        agent = self.agents.get(agent_id)
        if not agent or not agent.is_available():
            return False
        agent.assigned_task_id = task_id
        agent.status = AgentStatus.WORKING
        return True

    def release_task(self, agent_id: str):
        """Release agent from current task"""
        if agent_id in self.agents:
            self.agents[agent_id].assigned_task_id = None
            self.agents[agent_id].status = AgentStatus.IDLE

    def consume_tokens(self, agent_id: str, tokens: int) -> bool:
        """Record token consumption"""
        agent = self.agents.get(agent_id)
        if not agent:
            return False
        if agent.token_used + tokens > agent.token_budget:
            logger.warning(f"Agent {agent_id} token budget exceeded")
            return False
        agent.token_used += tokens
        return True

    def terminate(self, agent_id: str):
        """Terminate agent and cleanup"""
        if agent_id in self.agents:
            del self.agents[agent_id]
            logger.info(f"Agent {agent_id} terminated")

    def get_stats(self) -> Dict[str, Any]:
        """Get spawner statistics"""
        return {
            "total_agents": len(self.agents),
            "active_agents": len(self.list_agents(AgentStatus.ACTIVE)),
            "working_agents": len(self.list_agents(AgentStatus.WORKING)),
            "blocked_agents": len(self.list_agents(AgentStatus.BLOCKED)),
            "max_agents": self.max_agents,
            "capacity": len(self.agents) / self.max_agents
        }


# Global spawner instance
_spawner: Optional[AgentSpawner] = None


def get_spawner() -> AgentSpawner:
    """Get or create global spawner"""
    global _spawner
    if _spawner is None:
        _spawner = AgentSpawner()
    return _spawner


def reset_spawner():
    """Reset global spawner (for testing)"""
    global _spawner
    _spawner = None
