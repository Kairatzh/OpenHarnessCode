"""Truth & Verification Protocol (TVP) — Deterministic anti-hallucination verification.

Philosophy: The model NEVER decides whether a task or requirement is completed.
The runtime decides based on empirical facts, executed test exit codes, and real git diffs.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field


class RequirementStatus(str, Enum):
    """Rigorous factual status of an individual requirement."""
    UNVERIFIED = "unverified"      # Declared, but no verified proof exists
    IMPLEMENTED = "implemented"    # File edits/AST symbols exist, but tests have not run
    TESTED = "tested"              # Verified by automated test suite execution (exit code 0)
    REVIEWED = "reviewed"          # Verified by independent Code Reviewer agent
    ACCEPTED = "accepted"          # Verified and confirmed by human developer
    FAILED = "failed"              # Test execution or validation failed


class Requirement(BaseModel):
    """An individual tracked requirement with empirical verification proof."""
    id: str                        # e.g., "REQ-001"
    description: str
    status: RequirementStatus = RequirementStatus.UNVERIFIED
    target_files: list[str] = Field(default_factory=list)
    verification_command: str = "" # e.g. "pytest tests/test_auth.py"
    proof_details: str = ""        # Exit codes, test assertion counts, or diff references
    last_verified_at: Optional[datetime] = None


class ExecutionEvidence(BaseModel):
    """Empirical audit log of actions actually performed in the environment."""
    command_executed: str
    exit_code: int
    stdout_summary: str = ""
    stderr_summary: str = ""
    modified_files: list[str] = Field(default_factory=list)
    git_tree_hash: str = ""
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    @property
    def is_success(self) -> bool:
        return self.exit_code == 0


class TVPReport(BaseModel):
    """Comprehensive Truth & Verification Protocol report."""
    task_id: str
    title: str
    overall_status: str            # "PASSED", "PARTIAL", "FAILED", "UNVERIFIED"
    can_declare_complete: bool = False
    requirements: list[Requirement] = Field(default_factory=list)
    evidence_logs: list[ExecutionEvidence] = Field(default_factory=list)
    unverified_claims: list[str] = Field(default_factory=list)
    invariants_passed: bool = True
    invariant_violations: list[str] = Field(default_factory=list)


class TruthVerifier:
    """Evaluates task completion against empirical evidence, rejecting model claims without proof."""

    @staticmethod
    def evaluate(
        task_id: str,
        title: str,
        requirements: list[Requirement],
        evidence_logs: list[ExecutionEvidence],
        invariant_violations: list[str] | None = None,
    ) -> TVPReport:
        invariant_violations = invariant_violations or []
        unverified_claims: list[str] = []

        # Check each requirement against evidence
        all_tested_or_accepted = True
        for req in requirements:
            if req.status in (RequirementStatus.UNVERIFIED, RequirementStatus.FAILED):
                all_tested_or_accepted = False
                unverified_claims.append(f"{req.id}: {req.description} ({req.status.value})")
            elif req.status == RequirementStatus.IMPLEMENTED:
                # Implemented is NOT enough to claim complete if verification was requested
                all_tested_or_accepted = False
                unverified_claims.append(f"{req.id}: Implemented in code, but automated tests were not run")

        can_complete = (
            len(requirements) > 0
            and all_tested_or_accepted
            and len(invariant_violations) == 0
        )

        overall_status = "PASSED" if can_complete else ("PARTIAL" if any(r.status != RequirementStatus.UNVERIFIED for r in requirements) else "UNVERIFIED")

        return TVPReport(
            task_id=task_id,
            title=title,
            overall_status=overall_status,
            can_declare_complete=can_complete,
            requirements=requirements,
            evidence_logs=evidence_logs,
            unverified_claims=unverified_claims,
            invariants_passed=len(invariant_violations) == 0,
            invariant_violations=invariant_violations,
        )
