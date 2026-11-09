"""Workflow definitions — composable development pipelines."""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Any, Optional

import yaml
from pydantic import BaseModel, Field


class WorkflowStepType(str, Enum):
    AGENT = "agent"
    APPROVAL = "approval"
    PARALLEL = "parallel"
    CONDITIONAL = "conditional"
    TOOL = "tool"
    CHECKPOINT = "checkpoint"


class WorkflowStep(BaseModel):
    """A single step in a workflow pipeline."""
    id: str
    name: str
    type: WorkflowStepType = WorkflowStepType.AGENT
    agent: Optional[str] = None
    agents: list[str] = Field(default_factory=list)
    condition: Optional[str] = None
    on_success: Optional[str] = None
    on_failure: Optional[str] = None
    on_rejection: Optional[str] = None
    max_retries: int = 2
    timeout: int = 300
    required: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)


class Workflow(BaseModel):
    """A complete workflow pipeline definition."""
    id: str
    name: str
    description: str = ""
    version: str = "1.0.0"
    steps: list[WorkflowStep] = Field(default_factory=list)
    entry_step: str = ""
    max_iterations: int = 5
    timeout: int = 1800
    metadata: dict[str, Any] = Field(default_factory=dict)

    def get_step(self, step_id: str) -> WorkflowStep | None:
        for step in self.steps:
            if step.id == step_id:
                return step
        return None

    def get_next_step(self, current_id: str, success: bool = True) -> WorkflowStep | None:
        current = self.get_step(current_id)
        if not current:
            return None

        next_id = current.on_success if success else current.on_failure
        if next_id:
            return self.get_step(next_id)

        for i, step in enumerate(self.steps):
            if step.id == current_id and i + 1 < len(self.steps):
                return self.steps[i + 1]
        return None

    @classmethod
    def from_yaml(cls, path: Path) -> Workflow:
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return cls(**data)


# ── Built-in Workflows ─────────────────────────────────────────────────

def FeatureDevelopmentWorkflow() -> Workflow:
    return Workflow(
        id="feature_development",
        name="Feature Development",
        description="Plan → Approve → Checkpoint → Code → Test + Review → Report",
        steps=[
            WorkflowStep(
                id="context",
                name="Context Discovery",
                type=WorkflowStepType.TOOL,
                metadata={"tool": "context_gather"},
            ),
            WorkflowStep(
                id="architect",
                name="Architecture & Planning",
                type=WorkflowStepType.AGENT,
                agent="architect",
                on_success="approve_plan",
                on_failure="architect",
                max_retries=2,
            ),
            WorkflowStep(
                id="approve_plan",
                name="Approve Implementation Plan",
                type=WorkflowStepType.APPROVAL,
                on_success="checkpoint_pre",
                on_rejection="architect",
            ),
            WorkflowStep(
                id="checkpoint_pre",
                name="Pre-Implementation Checkpoint",
                type=WorkflowStepType.CHECKPOINT,
                on_success="coder",
            ),
            WorkflowStep(
                id="coder",
                name="Implementation",
                type=WorkflowStepType.AGENT,
                agent="coder",
                on_success="validate",
                on_failure="coder",
                max_retries=3,
            ),
            WorkflowStep(
                id="validate",
                name="Testing & Review",
                type=WorkflowStepType.PARALLEL,
                agents=["tester", "reviewer"],
                on_success="final_report",
                on_failure="fix",
            ),
            WorkflowStep(
                id="fix",
                name="Fix Issues",
                type=WorkflowStepType.AGENT,
                agent="coder",
                on_success="validate",
                on_failure="final_report",
                max_retries=2,
            ),
            WorkflowStep(
                id="final_report",
                name="Final Report",
                type=WorkflowStepType.CHECKPOINT,
            ),
        ],
        entry_step="context",
    )


def BugfixWorkflow() -> Workflow:
    return Workflow(
        id="bugfix",
        name="Bugfix",
        description="Diagnose → Fix → Test → Review → Complete",
        steps=[
            WorkflowStep(
                id="context",
                name="Context Discovery",
                type=WorkflowStepType.TOOL,
                metadata={"tool": "context_gather"},
            ),
            WorkflowStep(
                id="diagnose",
                name="Diagnose Issue",
                type=WorkflowStepType.AGENT,
                agent="architect",
                on_success="fix",
            ),
            WorkflowStep(
                id="fix",
                name="Fix Bug",
                type=WorkflowStepType.AGENT,
                agent="coder",
                on_success="test",
                on_failure="fix",
                max_retries=3,
            ),
            WorkflowStep(
                id="test",
                name="Verify Fix",
                type=WorkflowStepType.AGENT,
                agent="tester",
                on_success="review",
                on_failure="fix",
            ),
            WorkflowStep(
                id="review",
                name="Review Changes",
                type=WorkflowStepType.AGENT,
                agent="reviewer",
                on_success="complete",
                on_failure="fix",
            ),
            WorkflowStep(
                id="complete",
                name="Complete",
                type=WorkflowStepType.CHECKPOINT,
            ),
        ],
        entry_step="context",
    )
