"""Tests for Prompt Registry and 6-layer prompt hierarchy."""

import pytest
from pathlib import Path
from kairos_code.runtime.prompt_registry import PromptRegistry, AgentPromptSpec


class TestPromptRegistry:
    def test_assemble_layers(self, tmp_path):
        registry = PromptRegistry()
        spec = AgentPromptSpec(
            id="tester",
            name="Test Agent",
            role="tester",
            prompt_body="# Identity\nYou test code.",
        )
        registry.register_agent_spec(spec)

        prompt = registry.assemble_agent_prompt(
            agent_id="tester",
            task_context={"task_title": "Run unit tests"},
            user_instructions="Be fast",
        )

        assert "You test code" in prompt
        assert "Run unit tests" in prompt
        assert "Be fast" in prompt
