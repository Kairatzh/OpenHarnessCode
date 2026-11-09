"""Tests for Engineering Constitution, TVP, and Invariants."""

import pytest
from kairos_code.constitution.core_contract import CoreConstitution, InviolablePrinciple
from kairos_code.constitution.tvp import (
    Requirement,
    RequirementStatus,
    ExecutionEvidence,
    TruthVerifier,
)
from kairos_code.constitution.invariants import (
    EngineeringStandards,
    InvariantChecker,
)


class TestConstitution:
    def test_constitution_principles(self):
        const = CoreConstitution()
        assert len(const.principles) == 5
        assert len(const.built_in_team) == 7
        assert "implementer" in const.built_in_team
        assert "debugger" in const.built_in_team
        assert "refactorer" in const.built_in_team


class TestTruthAndVerificationProtocol:
    def test_cannot_complete_with_unverified_tests(self):
        reqs = [
            Requirement(id="REQ-001", description="Implement auth", status=RequirementStatus.IMPLEMENTED),
            Requirement(id="REQ-002", description="Run tests", status=RequirementStatus.UNVERIFIED),
        ]
        report = TruthVerifier.evaluate(task_id="T1", title="Auth", requirements=reqs, evidence_logs=[])

        assert not report.can_declare_complete
        assert report.overall_status in ("PARTIAL", "UNVERIFIED")
        assert len(report.unverified_claims) >= 1

    def test_completes_when_all_verified(self):
        reqs = [
            Requirement(id="REQ-001", description="Implement auth", status=RequirementStatus.TESTED),
            Requirement(id="REQ-002", description="Preserve routes", status=RequirementStatus.REVIEWED),
        ]
        report = TruthVerifier.evaluate(task_id="T2", title="Auth", requirements=reqs, evidence_logs=[])

        assert report.can_declare_complete
        assert report.overall_status == "PASSED"
        assert len(report.unverified_claims) == 0


class TestInvariantChecker:
    @pytest.mark.asyncio
    async def test_detects_unrequested_file_changes(self, tmp_path):
        checker = InvariantChecker(tmp_path)
        violations = await checker.check_unrequested_files(
            touched_files=["app/auth.py", "app/unrelated_billing.py"],
            allowed_files=["app/auth.py"],
        )
        assert len(violations) == 1
        assert "unrelated_billing.py" in violations[0].details
