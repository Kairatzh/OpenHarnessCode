"""Core data models and contracts for KAIROS Code."""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


# ── Enums ──────────────────────────────────────────────────────────────

class TaskStatus(str, Enum):
    """Lifecycle status of a task."""
    PENDING = "pending"
    PLANNING = "planning"
    APPROVED = "approved"
    IN_PROGRESS = "in_progress"
    REVIEWING = "reviewing"
    TESTING = "testing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    BLOCKED = "blocked"


class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AgentRole(str, Enum):
    """Built-in agent roles."""
    ARCHITECT = "architect"
    CODER = "coder"
    REVIEWER = "reviewer"
    TESTER = "tester"
    SECURITY = "security"
    RESEARCHER = "researcher"
    REFACTORER = "refactorer"
    DEBUGGER = "debugger"
    DOCUMENTER = "documenter"
    DEVOPS = "devops"
    CUSTOM = "custom"


class AgentCapability(str, Enum):
    """Capabilities that can be granted to agents."""
    FILESYSTEM_READ = "filesystem.read"
    FILESYSTEM_WRITE = "filesystem.write"
    FILESYSTEM_SEARCH = "filesystem.search"
    TERMINAL_EXECUTE = "terminal.execute"
    GIT_READ = "git.read"
    GIT_WRITE = "git.write"
    GIT_INSPECT = "git.inspect"
    NETWORK_ACCESS = "network.access"
    MEMORY_READ = "memory.read"
    MEMORY_WRITE = "memory.write"


# ── Agent Models ───────────────────────────────────────────────────────

class ModelConfig(BaseModel):
    """LLM model configuration for an agent."""
    provider: str = "inherit"
    name: Optional[str] = None
    temperature: float = 0.2
    max_tokens: Optional[int] = None
    top_p: Optional[float] = None
    base_url: Optional[str] = None


class AgentConfig(BaseModel):
    """Configuration for a single agent."""
    id: str
    name: str
    version: str = "1.0.0"
    role: AgentRole = AgentRole.CUSTOM
    model: ModelConfig = Field(default_factory=ModelConfig)
    capabilities: list[AgentCapability] = Field(default_factory=list)
    permissions: dict[str, bool] = Field(default_factory=dict)
    context_includes: list[str] = Field(default_factory=list)
    memory_enabled: bool = True
    memory_scope: str = "project"
    prompt_template: Optional[str] = None
    enabled: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)


# ── Structured Artifacts (Agent Contracts) ─────────────────────────────

class ImplementationStep(BaseModel):
    """A single step in an implementation plan."""
    order: int
    description: str
    agent: AgentRole = AgentRole.CODER
    files: list[str] = Field(default_factory=list)
    dependencies: list[int] = Field(default_factory=list)
    estimated_complexity: str = "medium"


class ImplementationPlan(BaseModel):
    """Structured output from the Architect agent."""
    summary: str
    requirements: list[str] = Field(default_factory=list)
    architecture_notes: str = ""
    files_to_modify: list[str] = Field(default_factory=list)
    files_to_create: list[str] = Field(default_factory=list)
    steps: list[ImplementationStep] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    testing_strategy: str = ""
    acceptance_criteria: list[str] = Field(default_factory=list)


class ReviewFinding(BaseModel):
    """A single finding from the Reviewer agent."""
    file: str
    line: Optional[int] = None
    severity: str = "medium"  # low, medium, high, critical
    category: str = "general" # bug, security, performance, style, architecture
    description: str
    suggestion: Optional[str] = None


class ReviewResult(BaseModel):
    """Structured output from the Reviewer agent."""
    approved: bool
    summary: str = ""
    findings: list[ReviewFinding] = Field(default_factory=list)
    overall_severity: str = "low"
    explanation_for_humans: str = ""  # Plain-text explanation for Vibe Mode


class TestResult(BaseModel):
    """Structured output from the Tester agent."""
    passed: bool
    total_tests: int = 0
    passed_tests: int = 0
    failed_tests: int = 0
    errors: list[str] = Field(default_factory=list)
    coverage: Optional[float] = None
    details: str = ""


class AgentResult(BaseModel):
    """Generic result from any agent execution."""
    agent_id: str
    agent_role: AgentRole
    status: str = "completed"  # completed, blocked, failed
    summary: str = ""
    modified_files: list[str] = Field(default_factory=list)
    created_files: list[str] = Field(default_factory=list)
    tests_to_run: list[str] = Field(default_factory=list)
    issues: list[str] = Field(default_factory=list)
    artifacts: dict[str, Any] = Field(default_factory=dict)
    token_usage: int = 0
    duration_seconds: float = 0.0
    plan: Optional[ImplementationPlan] = None
    review: Optional[ReviewResult] = None
    test_result: Optional[TestResult] = None


# ── Task ───────────────────────────────────────────────────────────────

class Task(BaseModel):
    """A development task managed by the harness."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    title: str
    description: str = ""
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    session_id: Optional[str] = None
    plan: Optional[ImplementationPlan] = None
    results: list[AgentResult] = Field(default_factory=list)
    iteration: int = 0
    max_iterations: int = 5
    token_budget: Optional[int] = None
    tokens_used: int = 0
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def add_result(self, result: AgentResult) -> None:
        """Add an agent result and update token usage."""
        self.results.append(result)
        self.tokens_used += result.token_usage
        self.updated_at = datetime.utcnow()


# ── Session ────────────────────────────────────────────────────────────

class SessionState(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SessionInfo(BaseModel):
    """Information about a harness session."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    state: SessionState = SessionState.ACTIVE
    task_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    current_agent: Optional[str] = None
    workflow: str = "feature_development"
    iteration: int = 0
    events: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
