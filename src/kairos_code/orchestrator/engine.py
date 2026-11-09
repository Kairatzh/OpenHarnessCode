"""Orchestrator engine — executes workflows and coordinates agents."""

from __future__ import annotations

import asyncio
import time
from typing import Any, Callable, Coroutine, Optional

from kairos_code.core.config import HarnessConfig
from kairos_code.core.events import EventBus, EventType
from kairos_code.core.exceptions import (
    ApprovalRequiredError,
    TimeoutError,
    WorkflowError,
)
from kairos_code.core.models import (
    AgentConfig,
    AgentResult,
    AgentRole,
    SessionInfo,
    SessionState,
    Task,
    TaskStatus,
)
from kairos_code.context.engine import ContextEngine
from kairos_code.orchestrator.workflows import (
    Workflow,
    WorkflowStep,
    WorkflowStepType,
    FeatureDevelopmentWorkflow,
    BugfixWorkflow,
)
from kairos_code.orchestrator.hooks import HookManager
from kairos_code.providers.registry import ProviderRegistry
from kairos_code.runtime.agent import AgentRuntime
from kairos_code.runtime.prompt_registry import PromptRegistry
from kairos_code.tools.base import ToolRegistry


ApprovalCallback = Callable[[str, dict[str, Any]], Coroutine[Any, Any, bool]]


class Orchestrator:
    """Main orchestrator — coordinates the entire development lifecycle.
    
    Philosophy: The Developer Is the Owner.
    Workflows are composable and replaceable.
    """

    def __init__(
        self,
        config: HarnessConfig,
        provider_registry: ProviderRegistry,
        prompt_registry: PromptRegistry,
        tool_registry: ToolRegistry,
        event_bus: EventBus,
        approval_callback: ApprovalCallback | None = None,
    ) -> None:
        self.config = config
        self.provider_registry = provider_registry
        self.prompt_registry = prompt_registry
        self.tool_registry = tool_registry
        self.event_bus = event_bus
        self.approval_callback = approval_callback

        self.agent_runtime = AgentRuntime(
            provider_registry=provider_registry,
            prompt_registry=prompt_registry,
            event_bus=event_bus,
            default_provider=config.llm.default_provider,
            default_model=config.llm.default_model,
        )

        self.context_engine = ContextEngine(
            project_root=config.project_root or "."
        )

        self.hooks = HookManager(event_bus)

        self._workflows: dict[str, Workflow] = {
            "feature_development": FeatureDevelopmentWorkflow(),
            "bugfix": BugfixWorkflow(),
        }

        self._agent_configs: dict[str, AgentConfig] = {}
        self._load_agent_configs()

        self._sessions: dict[str, SessionInfo] = {}

    def register_workflow(self, workflow: Workflow) -> None:
        self._workflows[workflow.id] = workflow

    def register_agent_config(self, config: AgentConfig) -> None:
        self._agent_configs[config.id] = config

    async def run_task(
        self,
        task: Task,
        workflow_id: str | None = None,
        stream_callback: Callable[[str, str], Coroutine[Any, Any, None]] | None = None,
    ) -> Task:
        wf_id = workflow_id or self.config.workflow.default
        workflow = self._workflows.get(wf_id)
        if not workflow:
            raise WorkflowError(f"Unknown workflow: {wf_id}")

        session = SessionInfo(
            task_id=task.id,
            workflow=wf_id,
        )
        task.session_id = session.id
        self._sessions[session.id] = session

        await self.event_bus.emit(
            EventType.SESSION_STARTED,
            source="orchestrator",
            data={"task_id": task.id, "workflow": wf_id},
            session_id=session.id,
            task_id=task.id,
        )

        if stream_callback:
            await stream_callback("session_started", f"Session {session.id} started with workflow: {workflow.name}")

        try:
            await self._execute_workflow(task, workflow, session, stream_callback)
        except Exception as e:
            task.status = TaskStatus.FAILED
            session.state = SessionState.FAILED
            await self.event_bus.emit(
                EventType.WORKFLOW_FAILED,
                source="orchestrator",
                data={"error": str(e)},
                session_id=session.id,
                task_id=task.id,
            )
            if stream_callback:
                await stream_callback("error", f"Workflow failed: {e}")

        session.state = SessionState.COMPLETED if task.status == TaskStatus.COMPLETED else SessionState.FAILED
        session.updated_at = task.updated_at

        await self.event_bus.emit(
            EventType.SESSION_ENDED,
            source="orchestrator",
            data={"final_status": task.status.value},
            session_id=session.id,
            task_id=task.id,
        )
        await self.event_bus.emit(
            EventType.TASK_COMPLETED if task.status == TaskStatus.COMPLETED else EventType.TASK_FAILED,
            source="orchestrator",
            data={"task": task.model_dump()},
            session_id=session.id,
            task_id=task.id,
        )

        return task

    async def _execute_workflow(
        self,
        task: Task,
        workflow: Workflow,
        session: SessionInfo,
        stream_callback: Callable | None = None,
    ) -> None:
        current_step = workflow.get_step(workflow.entry_step)
        if not current_step and workflow.steps:
            current_step = workflow.steps[0]

        task.status = TaskStatus.IN_PROGRESS
        retries_per_step: dict[str, int] = {}
        start_time = time.time()

        while current_step:
            elapsed = time.time() - start_time
            if elapsed > workflow.timeout:
                raise TimeoutError(f"Workflow timed out after {elapsed:.0f}s")

            if task.iteration >= workflow.max_iterations:
                raise WorkflowError(f"Max iterations ({workflow.max_iterations}) reached")

            step_id = current_step.id
            session.current_agent = step_id
            task.iteration += 1

            await self.event_bus.emit(
                EventType.WORKFLOW_STEP_STARTED,
                source="orchestrator",
                data={"step": step_id, "step_name": current_step.name},
                session_id=session.id,
                task_id=task.id,
            )

            if stream_callback:
                await stream_callback("step_started", f"Step: {current_step.name}")

            success = False
            try:
                success = await self._execute_step(
                    task, current_step, session, stream_callback
                )
            except ApprovalRequiredError as e:
                # Check if developer requested approvals for this step
                if self.approval_callback and (step_id in self.config.workflow.require_approval or "all" in self.config.workflow.require_approval):
                    approved = await self.approval_callback(
                        e.action, {"task": task.model_dump(), "details": e.details}
                    )
                    if approved:
                        success = True
                    else:
                        next_step_id = current_step.on_rejection
                        if next_step_id:
                            current_step = workflow.get_step(next_step_id)
                            continue
                        else:
                            task.status = TaskStatus.CANCELLED
                            return
                else:
                    success = True

            await self.event_bus.emit(
                EventType.WORKFLOW_STEP_COMPLETED,
                source="orchestrator",
                data={"step": step_id, "success": success},
                session_id=session.id,
                task_id=task.id,
            )

            if stream_callback:
                status_str = "✓" if success else "✗"
                await stream_callback("step_completed", f"{status_str} {current_step.name}")

            if success:
                next_step = workflow.get_next_step(step_id, success=True)
            else:
                retries_per_step.setdefault(step_id, 0)
                retries_per_step[step_id] += 1
                if retries_per_step[step_id] < current_step.max_retries:
                    continue
                next_step = workflow.get_next_step(step_id, success=False)

            if next_step is None:
                if success:
                    task.status = TaskStatus.COMPLETED
                else:
                    task.status = TaskStatus.FAILED
                break

            current_step = next_step

        if task.status == TaskStatus.IN_PROGRESS:
            task.status = TaskStatus.COMPLETED

    async def _execute_step(
        self,
        task: Task,
        step: WorkflowStep,
        session: SessionInfo,
        stream_callback: Callable | None = None,
    ) -> bool:
        if step.type == WorkflowStepType.AGENT:
            return await self._run_agent_step(task, step, stream_callback)

        elif step.type == WorkflowStepType.APPROVAL:
            raise ApprovalRequiredError(
                action=step.name,
                details=self._format_approval_details(task),
            )

        elif step.type == WorkflowStepType.PARALLEL:
            return await self._run_parallel_step(task, step, stream_callback)

        elif step.type == WorkflowStepType.TOOL:
            return await self._run_tool_step(task, step)

        elif step.type == WorkflowStepType.CHECKPOINT:
            return await self._run_checkpoint(task, step)

        return True

    async def _run_agent_step(
        self,
        task: Task,
        step: WorkflowStep,
        stream_callback: Callable | None = None,
    ) -> bool:
        agent_id = step.agent
        if not agent_id:
            return False

        agent_config = self._agent_configs.get(agent_id)
        if not agent_config:
            return True

        override = self.config.get_agent_override(agent_id)
        if not override.enabled:
            return True

        context = await self.context_engine.gather()

        result = await self.agent_runtime.execute(
            agent_config=agent_config,
            task=task,
            extra_context={"project_context": context.to_prompt_section()},
        )

        task.add_result(result)

        if stream_callback:
            await stream_callback("agent_result", result.summary[:400])

        return result.status == "completed"

    async def _run_parallel_step(
        self,
        task: Task,
        step: WorkflowStep,
        stream_callback: Callable | None = None,
    ) -> bool:
        if not step.agents:
            return True

        tasks_list = []
        for agent_id in step.agents:
            agent_config = self._agent_configs.get(agent_id)
            if not agent_config:
                continue
            override = self.config.get_agent_override(agent_id)
            if not override.enabled:
                continue
            tasks_list.append(
                self.agent_runtime.execute(agent_config=agent_config, task=task)
            )

        if not tasks_list:
            return True

        results = await asyncio.gather(*tasks_list, return_exceptions=True)

        all_success = True
        for r in results:
            if isinstance(r, Exception):
                all_success = False
            elif isinstance(r, AgentResult):
                task.add_result(r)
                if r.status != "completed":
                    all_success = False

        return all_success

    async def _run_tool_step(self, task: Task, step: WorkflowStep) -> bool:
        tool_name = step.metadata.get("tool", "")
        if tool_name == "context_gather":
            context = await self.context_engine.gather()
            task.metadata["project_context"] = context.model_dump()
            return True
        return True

    async def _run_checkpoint(self, task: Task, step: WorkflowStep) -> bool:
        if self.config.runtime.auto_git_checkpoints:
            git_tool = self.tool_registry.get("git")
            if git_tool:
                res = await git_tool.execute(operation="checkpoint", args=f"Task {task.id}: {step.name}")
                if res.success:
                    await self.event_bus.emit(
                        EventType.CHECKPOINT_CREATED,
                        source="orchestrator",
                        data={"checkpoint": res.metadata.get("checkpoint_tag", "")},
                        task_id=task.id,
                    )
        return True

    def _format_approval_details(self, task: Task) -> str:
        parts = [f"Task: {task.title}"]
        if task.plan:
            parts.append(f"Plan: {task.plan.summary}")
            if task.plan.files_to_modify:
                parts.append(f"Files to modify: {', '.join(task.plan.files_to_modify)}")
        return "\n".join(parts)

    def _load_agent_configs(self) -> None:
        defaults = [
            AgentConfig(
                id="architect",
                name="Software Architect",
                role=AgentRole.ARCHITECT,
                capabilities=["filesystem.read", "filesystem.search", "git.inspect"],
                permissions={"filesystem_write": False, "terminal_execute": False},
            ),
            AgentConfig(
                id="coder",
                name="Software Engineer",
                role=AgentRole.CODER,
                capabilities=["filesystem.read", "filesystem.write", "filesystem.search", "terminal.execute", "git.read"],
                permissions={"filesystem_write": True, "terminal_execute": True},
            ),
            AgentConfig(
                id="reviewer",
                name="Code Reviewer",
                role=AgentRole.REVIEWER,
                capabilities=["filesystem.read", "filesystem.search", "git.inspect"],
                permissions={"filesystem_write": False, "terminal_execute": False},
            ),
            AgentConfig(
                id="tester",
                name="Test Engineer",
                role=AgentRole.TESTER,
                capabilities=["filesystem.read", "filesystem.search", "terminal.execute"],
                permissions={"filesystem_write": False, "terminal_execute": True},
            ),
            AgentConfig(
                id="security",
                name="Security Analyst",
                role=AgentRole.SECURITY,
                capabilities=["filesystem.read", "filesystem.search"],
                permissions={"filesystem_write": False, "terminal_execute": False},
            ),
        ]
        for cfg in defaults:
            self._agent_configs[cfg.id] = cfg

    def get_session(self, session_id: str) -> SessionInfo | None:
        return self._sessions.get(session_id)

    def list_workflows(self) -> list[str]:
        return list(self._workflows.keys())
