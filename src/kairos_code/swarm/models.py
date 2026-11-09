"""Dynamic Agent Swarm models — Missions, Dynamic Agents, Tasks, and Artifacts."""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field


class MissionStatus(str, Enum):
    INITIALIZED = "initialized"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskStatus(str, Enum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


class Artifact(BaseModel):
    """A verified result produced by an agent in a mission."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str
    artifact_type: str  # "code", "report", "benchmark", "dataset", "json"
    content: str
    file_path: Optional[str] = None
    created_by_agent: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)


class CapabilityRequest(BaseModel):
    """Proposal by an agent to add or acquire a new tool/capability dynamically."""
    name: str
    purpose: str
    required_tools: list[str] = Field(default_factory=list)
    proposed_code: str = ""
    requested_permissions: list[str] = Field(default_factory=list)
    approved: bool = False


class DynamicAgent(BaseModel):
    """An agent dynamically spawned for a specific mission subtask."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str
    specialization: str
    system_prompt: str
    capabilities: list[str] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_tasks: int = 0
    is_active: bool = True
    capability_requests: list[CapabilityRequest] = Field(default_factory=list)


class MissionTask(BaseModel):
    """A concrete unit of work within a larger mission."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    title: str
    description: str
    assigned_agent_id: Optional[str] = None
    required_specialization: str = ""
    dependencies: list[str] = Field(default_factory=list)  # IDs of blocking tasks
    status: TaskStatus = TaskStatus.PENDING
    artifact_id: Optional[str] = None
    result_summary: str = ""
    iterations: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ResourceLimits(BaseModel):
    """Resource constraints for elastic agent execution."""
    max_physical_workers: int = 3   # Physical concurrent LLM execution slots
    max_logical_agents: int = 30    # Max virtual agents in the swarm
    max_task_depth: int = 5         # Maximum decomposition depth
    timeout_seconds: int = 28800    # 8 hours for overnight missions
    checkpoint_interval_seconds: int = 1800  # Checkpoint every 30 mins
    token_budget: Optional[int] = None


class Mission(BaseModel):
    """An overarching autonomous objective (e.g. overnight research & build)."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    title: str
    objective: str
    status: MissionStatus = MissionStatus.INITIALIZED
    tasks: list[MissionTask] = Field(default_factory=list)
    agents: list[DynamicAgent] = Field(default_factory=list)
    artifacts: list[Artifact] = Field(default_factory=list)
    resource_limits: ResourceLimits = Field(default_factory=ResourceLimits)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    def get_task(self, task_id: str) -> Optional[MissionTask]:
        for t in self.tasks:
            if t.id == task_id:
                return t
        return None

    def get_ready_tasks(self) -> list[MissionTask]:
        """Tasks whose dependencies are all completed."""
        completed_ids = {t.id for t in self.tasks if t.status == TaskStatus.COMPLETED}
        return [
            t for t in self.tasks
            if t.status == TaskStatus.PENDING and all(dep in completed_ids for dep in t.dependencies)
        ]
