"""Semantic Programming Layer (SPL) data models and evidence schemas."""

from __future__ import annotations

from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field


class EvidenceStatus(str, Enum):
    """Truthfulness and verification status of a factual statement."""
    OBSERVED = "observed"      # Confirmed directly by tool/AST/git diff
    TESTED = "tested"          # Confirmed by executing automated tests
    INFERRED = "inferred"      # Deduced by LLM reasoning
    UNVERIFIED = "unverified"  # Assumed or speculative, requires check


class EvidenceItem(BaseModel):
    """An individual piece of evidence supporting a claim or change."""
    statement: str
    status: EvidenceStatus
    source: str = ""  # e.g., "ast:get_access_token", "git:diff:auth.py", "pytest:test_jwt"
    details: str = ""


class SemanticOperationType(str, Enum):
    ADD_FEATURE = "add_feature"
    REFACTOR = "refactor"
    BUGFIX = "bugfix"
    OPTIMIZE = "optimize"
    SIMPLIFY = "simplify"
    TEST = "test"


class SemanticIntent(BaseModel):
    """Developer intent translated into a structured semantic representation."""
    raw_intent: str
    operation: SemanticOperationType = SemanticOperationType.ADD_FEATURE
    target_component: str = ""
    requirements: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    acceptance_criteria: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)


class ASTSymbolChange(BaseModel):
    """Symbol-level change extracted via AST parsing."""
    symbol_type: str  # function, class, method, import
    name: str
    change_type: str  # added, modified, removed
    file_path: str
    signature: str = ""
    docstring: str = ""
    callers: list[str] = Field(default_factory=list)


class CodeExplanation(BaseModel):
    """Evidence-based code explanation synthesized from AST, Git, and Tests."""
    file_path: str
    title: str
    purpose: str
    behavior_steps: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    ast_changes: list[ASTSymbolChange] = Field(default_factory=list)
    evidence: list[EvidenceItem] = Field(default_factory=list)
    tests_run: int = 0
    tests_passed: int = 0
    tradeoffs_and_alternatives: list[str] = Field(default_factory=list)
    assumptions_made: list[str] = Field(default_factory=list)
