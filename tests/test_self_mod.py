"""Tests for self-modification engine."""

import pytest
from kairos_code.core.registry import ComponentRegistry
from kairos_code.self_mod.customize import SelfModificationEngine


class TestSelfModification:
    def test_inspection(self, tmp_path):
        reg = ComponentRegistry()
        engine = SelfModificationEngine(tmp_path, reg)
        info = engine.inspect_architecture()

        assert "active_components" in info
        assert len(info["active_components"]) >= 5

    def test_fallback_plan_generation_and_apply(self, tmp_path):
        reg = ComponentRegistry()
        engine = SelfModificationEngine(tmp_path, reg)
        plan = engine._fallback_plan("add a pytorch_optimizer agent")

        assert len(plan.changes) == 1
        assert "pytorch_optimizer.md" in plan.changes[0].file_path

        applied = engine.apply_plan(plan)
        assert len(applied) == 1
        assert (tmp_path / ".harness" / "agents" / "pytorch_optimizer.md").exists()
