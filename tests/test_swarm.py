"""Tests for Dynamic Agent Swarm models and coordinator."""

import pytest
from kairos_code.swarm.models import (
    Mission,
    MissionTask,
    DynamicAgent,
    Artifact,
    ResourceLimits,
    TaskStatus,
    MissionStatus,
)


class TestDynamicSwarm:
    def test_mission_dependency_graph(self):
        mission = Mission(
            title="VLM Research",
            objective="Analyze drone perception architectures",
        )

        task1 = MissionTask(id="T1", title="Survey papers", status=TaskStatus.COMPLETED)
        task2 = MissionTask(id="T2", title="Evaluate models", dependencies=["T1"], status=TaskStatus.PENDING)
        task3 = MissionTask(id="T3", title="Run benchmarks", dependencies=["T2"], status=TaskStatus.PENDING)

        mission.tasks.extend([task1, task2, task3])

        ready = mission.get_ready_tasks()
        assert len(ready) == 1
        assert ready[0].id == "T2"

    def test_dynamic_agent_spawn(self):
        agent = DynamicAgent(
            name="Paper Analyst",
            specialization="arXiv Paper Analysis",
            system_prompt="Analyze ML papers",
        )
        assert agent.specialization == "arXiv Paper Analysis"
        assert agent.completed_tasks == 0

    def test_artifact_creation(self):
        artifact = Artifact(
            name="survey_results.md",
            artifact_type="report",
            content="# Survey Findings",
            created_by_agent="Paper Analyst",
        )
        assert artifact.name == "survey_results.md"
        assert artifact.created_by_agent == "Paper Analyst"
