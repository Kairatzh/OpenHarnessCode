"""Atomic Change Unit (ACU) models and lifecycle definitions."""

from __future__ import annotations

from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field

from kairos_code.spl.models import CodeExplanation, SemanticIntent


class ACUStatus(str, Enum):
    """Lifecycle status of an Atomic Change Unit."""
    INTENT_CAPTURED = "intent_captured"
    PLANNED = "planned"
    IMPLEMENTED = "implemented"
    VERIFIED = "verified"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    REVISED = "revised"


class AtomicChangeUnit(BaseModel):
    """A minimal, logically coherent, verifiable code increment."""
    id: str = "ACU-001"
    title: str
    intent: Optional[SemanticIntent] = None
    description: str = ""
    files: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)  # IDs of preceding ACUs
    acceptance_criteria: list[str] = Field(default_factory=list)
    verification_command: str = ""
    status: ACUStatus = ACUStatus.INTENT_CAPTURED
    explanation: Optional[CodeExplanation] = None
    git_checkpoint: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    def is_executable(self) -> bool:
        return self.status in (ACUStatus.INTENT_CAPTURED, ACUStatus.PLANNED)
