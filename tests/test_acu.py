"""Tests for Atomic Change Units (ACU)."""

import pytest
from kairos_code.acu.models import AtomicChangeUnit, ACUStatus
from kairos_code.acu.engine import AtomicChangeEngine


class TestAtomicChangeUnit:
    def test_acu_creation(self):
        acu = AtomicChangeUnit(
            id="ACU-001",
            title="Create JWT Utility",
            description="Helper function for token creation",
            files=["app/core/security.py"],
            acceptance_criteria=["Valid token generated", "Expiration set"],
        )
        assert acu.id == "ACU-001"
        assert acu.status == ACUStatus.INTENT_CAPTURED
        assert len(acu.acceptance_criteria) == 2

    def test_acu_status_transitions(self):
        acu = AtomicChangeUnit(id="ACU-002", title="Add Login")
        acu.status = ACUStatus.PLANNED
        assert acu.status == ACUStatus.PLANNED
        acu.status = ACUStatus.ACCEPTED
        assert acu.status == ACUStatus.ACCEPTED
