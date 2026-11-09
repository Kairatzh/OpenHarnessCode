"""Core Engineering Constitution and 5 Inviolable Principles."""

from __future__ import annotations

from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


class InviolablePrinciple(str, Enum):
    """The 5 Inviolable Principles of OpenHarnessCode."""
    NO_FALSE_COMPLETION = "no_false_completion"
    NO_UNREQUESTED_CHANGES = "no_unrequested_changes"
    SIMPLICITY_FIRST = "simplicity_first"
    INDEPENDENT_VERIFICATION = "independent_verification"
    TRACEABLE_CHANGES = "traceable_changes"


class CoreConstitution(BaseModel):
    """Immutable constitution defining engineering invariants."""
    version: str = "1.0.0"
    principles: dict[str, str] = Field(default_factory=lambda: {
        "1. No False Completion": "An agent cannot declare a task complete without empirical proof (exit codes, test outputs, AST diffs).",
        "2. No Unrequested Changes": "Do not silently modify unapproved files, rewrite unrelated architecture, or add speculative features.",
        "3. Simplicity First": "Always prefer the minimal, direct implementation that satisfies requirements over unnecessary design patterns.",
        "4. Independent Verification": "The implementing agent does not grade its own homework. Reviewers and test runners inspect independently.",
        "5. Traceable Changes": "Every code increment maps to an explicit Requirement ID, git diff, verified evidence, and explanation.",
    })

    built_in_team: list[str] = Field(default_factory=lambda: [
        "architect",
        "implementer",
        "debugger",
        "reviewer",
        "tester",
        "refactorer",
        "explainer",
    ])
