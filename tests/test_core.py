"""Tests for core models, configuration, registry, and event bus."""

import pytest
from kairos_code.core.models import (
    Task,
    TaskStatus,
    AgentConfig,
    AgentRole,
    AgentResult,
    ImplementationPlan,
    ImplementationStep,
)
from kairos_code.core.config import HarnessConfig, _deep_merge
from kairos_code.core.events import EventBus, EventType, Event
from kairos_code.core.registry import ComponentRegistry


class TestTask:
    def test_create_task(self):
        task = Task(title="Build authentication", description="JWT based auth")
        assert task.title == "Build authentication"
        assert task.status == TaskStatus.PENDING
        assert len(task.id) == 8

    def test_add_result(self):
        task = Task(title="Test")
        result = AgentResult(
            agent_id="coder",
            agent_role=AgentRole.CODER,
            status="completed",
            token_usage=250,
        )
        task.add_result(result)
        assert len(task.results) == 1
        assert task.tokens_used == 250


class TestConfigMerge:
    def test_deep_merge(self):
        base = {"llm": {"default_provider": "openai", "default_model": "gpt-4o"}}
        override = {"llm": {"default_model": "gpt-4o-mini"}, "runtime": {"max_iterations": 10}}
        merged = _deep_merge(base, override)
        assert merged["llm"]["default_provider"] == "openai"
        assert merged["llm"]["default_model"] == "gpt-4o-mini"
        assert merged["runtime"]["max_iterations"] == 10


class TestEventBus:
    @pytest.mark.asyncio
    async def test_publish_and_subscribe(self):
        bus = EventBus()
        events_received = []

        async def handler(event: Event):
            events_received.append(event)

        bus.subscribe(EventType.TASK_CREATED, handler)
        await bus.emit(EventType.TASK_CREATED, source="test", data={"hello": "world"})

        assert len(events_received) == 1
        assert events_received[0].data["hello"] == "world"


class TestComponentRegistry:
    def test_registry_contains_subsystems(self):
        reg = ComponentRegistry()
        all_comps = reg.list_all()
        ids = [c.id for c in all_comps]

        assert "agent_runtime" in ids
        assert "orchestrator" in ids
        assert "prompt_registry" in ids
        assert "provider_registry" in ids
        assert "self_modifier" in ids
        assert "vibe_engine" in ids

    def test_architecture_summary(self):
        reg = ComponentRegistry()
        summary = reg.to_architecture_summary()
        assert summary["harness"] == "KAIROS Code"
        assert len(summary["components"]) >= 8
