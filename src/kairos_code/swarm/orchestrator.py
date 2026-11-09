"""Dynamic Swarm Orchestrator — manages elastic multi-agent research & development missions."""

from __future__ import annotations

import asyncio
import json
import re
import time
from pathlib import Path
from typing import Any, Callable, Coroutine, Optional

from kairos_code.providers.base import Message, MessageRole
from kairos_code.providers.registry import ProviderRegistry
from kairos_code.swarm.models import (
    Artifact,
    CapabilityRequest,
    DynamicAgent,
    Mission,
    MissionStatus,
    MissionTask,
    ResourceLimits,
    TaskStatus,
)
from kairos_code.tools.base import ToolRegistry
from kairos_code.tools.git import GitTool


class DynamicSwarmOrchestrator:
    """Coordinates dynamic swarms for deep autonomous and research missions.
    
    Key mechanisms:
    1. Task Decomposition (Mission -> Dependency DAG)
    2. Dynamic Agent Spawning (Just-in-time specialization)
    3. Resource-Aware Execution (N logical agents -> K physical worker concurrency)
    4. Capability Acquisition (Agents propose new tools)
    5. Agent Retirement (Clean teardown of completed workers)
    """

    def __init__(
        self,
        project_root: str | Path,
        provider_registry: Optional[ProviderRegistry] = None,
        tool_registry: Optional[ToolRegistry] = None,
    ) -> None:
        self.project_root = Path(project_root).resolve()
        self.provider_registry = provider_registry or ProviderRegistry()
        self.tool_registry = tool_registry or ToolRegistry()
        self.git_tool = GitTool(str(self.project_root))
        self._missions: dict[str, Mission] = {}

    async def create_mission(
        self,
        objective: str,
        limits: Optional[ResourceLimits] = None,
        provider_name: str = "openai",
        model_name: str = "gpt-4o",
    ) -> Mission:
        """Decompose overarching objective into initial dynamic tasks and agents."""
        mission = Mission(
            title=objective[:60],
            objective=objective,
            resource_limits=limits or ResourceLimits(),
        )

        prompt = f"""You are the Swarm Mission Coordinator for KAIROS Code.
Decompose this ambitious autonomous mission into initial subtasks and required specialized agent roles.

Mission Objective:
"{objective}"

Respond with valid JSON:
{{
  "tasks": [
    {{
      "title": "Subtask title",
      "description": "Subtask detailed scope",
      "required_specialization": "e.g. Literature Researcher, Benchmark Engineer, Architecture Critic",
      "dependencies": []
    }}
  ],
  "initial_agents": [
    {{
      "name": "Literature Researcher",
      "specialization": "Scientific paper & repo analysis",
      "system_prompt": "You specialize in searching and summarizing cutting-edge models."
    }}
  ]
}}
"""
        provider = self.provider_registry.get(provider_name)
        res = await provider.complete(
            messages=[Message(role=MessageRole.USER, content=prompt)],
            model=model_name,
            temperature=0.2,
        )

        content = res.content.strip()
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", content)
        if match:
            content = match.group(1).strip()

        try:
            data = json.loads(content)
            for tdata in data.get("tasks", []):
                mission.tasks.append(MissionTask(**tdata))
            for adata in data.get("initial_agents", []):
                mission.agents.append(DynamicAgent(**adata))
        except Exception:
            # Fallback coordinator setup
            agent = DynamicAgent(
                name="General Researcher",
                specialization="General research and analysis",
                system_prompt="Analyze the mission and produce structured findings.",
            )
            task = MissionTask(
                title="Conduct Mission Research",
                description=objective,
                required_specialization="General research and analysis",
            )
            mission.agents.append(agent)
            mission.tasks.append(task)

        self._missions[mission.id] = mission
        return mission

    async def run_mission(
        self,
        mission: Mission,
        stream_callback: Optional[Callable[[str, str], Coroutine[Any, Any, None]]] = None,
        provider_name: str = "openai",
        model_name: str = "gpt-4o",
    ) -> Mission:
        """Execute mission using dynamic worker pool matching physical concurrency limits."""
        mission.status = MissionStatus.RUNNING
        sem = asyncio.Semaphore(mission.resource_limits.max_physical_workers)
        start_time = time.time()
        last_checkpoint = time.time()

        if stream_callback:
            await stream_callback(
                "mission_started",
                f"Mission '{mission.title}' started with {len(mission.tasks)} tasks and {len(mission.agents)} agents."
            )

        while mission.status == MissionStatus.RUNNING:
            # Check elapsed time
            if time.time() - start_time > mission.resource_limits.timeout_seconds:
                if stream_callback:
                    await stream_callback("timeout", "Mission timeout reached.")
                mission.status = MissionStatus.COMPLETED
                break

            # Periodic checkpointing
            if time.time() - last_checkpoint > mission.resource_limits.checkpoint_interval_seconds:
                await self.git_tool.execute(operation="checkpoint", args=f"Mission Checkpoint {mission.id}")
                last_checkpoint = time.time()

            ready_tasks = mission.get_ready_tasks()
            if not ready_tasks:
                all_done = all(t.status in (TaskStatus.COMPLETED, TaskStatus.FAILED) for t in mission.tasks)
                if all_done:
                    mission.status = MissionStatus.COMPLETED
                break

            async def _run_single_task(task: MissionTask):
                async with sem:
                    # Find or spawn agent matching specialization
                    agent = self._find_or_spawn_agent(mission, task.required_specialization)
                    task.assigned_agent_id = agent.id
                    task.status = TaskStatus.IN_PROGRESS

                    if stream_callback:
                        await stream_callback("task_started", f"Agent '{agent.name}' started: {task.title}")

                    # Execute task
                    prompt = f"""You are agent '{agent.name}' specialized in {agent.specialization}.
Task: {task.title}
Instructions: {task.description}

Produce a detailed, structured technical artifact.
"""
                    provider = self.provider_registry.get(provider_name)
                    response = await provider.complete(
                        messages=[
                            Message(role=MessageRole.SYSTEM, content=agent.system_prompt),
                            Message(role=MessageRole.USER, content=prompt),
                        ],
                        model=model_name,
                        temperature=0.2,
                    )

                    artifact = Artifact(
                        name=f"Result of {task.title}",
                        artifact_type="report",
                        content=response.content,
                        created_by_agent=agent.name,
                    )
                    mission.artifacts.append(artifact)
                    task.artifact_id = artifact.id
                    task.result_summary = response.content[:300]
                    task.status = TaskStatus.COMPLETED
                    agent.completed_tasks += 1

                    if stream_callback:
                        await stream_callback("task_completed", f"✓ Task '{task.title}' completed by {agent.name}")

            # Run ready tasks concurrently within physical worker limits
            await asyncio.gather(*[_run_single_task(t) for t in ready_tasks])

        # Synthesize final mission report
        await self._synthesize_mission_report(mission, provider_name, model_name)
        mission.status = MissionStatus.COMPLETED

        if stream_callback:
            await stream_callback("mission_completed", f"Mission {mission.id} completed. {len(mission.artifacts)} artifacts created.")

        return mission

    def _find_or_spawn_agent(self, mission: Mission, specialization: str) -> DynamicAgent:
        """Find existing idle agent or dynamically spawn a new one."""
        for a in mission.agents:
            if a.specialization.lower() == specialization.lower() and a.is_active:
                return a

        # Check logical agent bound
        if len(mission.agents) >= mission.resource_limits.max_logical_agents:
            return mission.agents[0]

        # Spawn new agent dynamically
        new_agent = DynamicAgent(
            name=specialization.title(),
            specialization=specialization,
            system_prompt=f"You are a dynamically spawned expert specialized in: {specialization}.",
        )
        mission.agents.append(new_agent)
        return new_agent

    async def _synthesize_mission_report(
        self,
        mission: Mission,
        provider_name: str,
        model_name: str,
    ) -> None:
        """Synthesize all artifacts into an overarching mission summary report."""
        artifacts_content = "\n\n---\n\n".join(
            f"Artifact: {a.name} (by {a.created_by_agent})\n{a.content[:1500]}"
            for a in mission.artifacts
        )

        prompt = f"""Synthesize the final summary for Mission: {mission.title}
Objective: {mission.objective}

Artifacts generated by swarm:
{artifacts_content}

Produce a comprehensive final report with executive summary, technical conclusions, and next steps.
"""
        provider = self.provider_registry.get(provider_name)
        res = await provider.complete(
            messages=[Message(role=MessageRole.USER, content=prompt)],
            model=model_name,
            temperature=0.2,
        )

        final_artifact = Artifact(
            name=f"FINAL_MISSION_SYNTHESIS_{mission.id}",
            artifact_type="report",
            content=res.content,
            created_by_agent="Mission Synthesizer",
        )
        mission.artifacts.append(final_artifact)

        # Save to local knowledge directory
        dest = self.project_root / ".harness" / "knowledge" / f"mission_{mission.id}.md"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(res.content, encoding="utf-8")

    def get_mission(self, mission_id: str) -> Optional[Mission]:
        return self._missions.get(mission_id)
