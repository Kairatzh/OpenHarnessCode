"""Agent runtime — executes agents with prompt assembly, tools, and hooks."""

from __future__ import annotations

import time
from typing import Any, Optional

from kairos_code.core.events import EventBus, EventType
from kairos_code.core.exceptions import AgentError, BudgetExceededError
from kairos_code.core.models import (
    AgentConfig,
    AgentResult,
    AgentRole,
    Task,
)
from kairos_code.providers.base import LLMProvider, Message, MessageRole
from kairos_code.providers.registry import ProviderRegistry
from kairos_code.runtime.prompt_registry import PromptRegistry


class AgentRuntime:
    """Manages execution of AI agents.
    
    Responsibilities:
    - Assembles multi-layer prompts
    - Executes before_agent and after_agent hooks
    - Routes to selected LLM provider (OpenAI, Anthropic, Gemini, Ollama)
    - Enforces budgets and iteration bounds
    - Emits lifecycle events
    """

    def __init__(
        self,
        provider_registry: ProviderRegistry,
        prompt_registry: PromptRegistry,
        event_bus: EventBus,
        default_provider: str = "openai",
        default_model: str = "gpt-4o",
    ) -> None:
        self.provider_registry = provider_registry
        self.prompt_registry = prompt_registry
        self.event_bus = event_bus
        self.default_provider = default_provider
        self.default_model = default_model
        self._conversations: dict[str, list[Message]] = {}

    async def execute(
        self,
        agent_config: AgentConfig,
        task: Task,
        user_message: str = "",
        extra_context: dict[str, Any] | None = None,
        tools: list[dict[str, Any]] | None = None,
        workflow_instructions: str = "",
        user_instructions: str = "",
    ) -> AgentResult:
        """Execute an agent on a task."""
        start_time = time.time()
        agent_id = agent_config.id

        # Before Agent Hook & Event
        await self.event_bus.emit(
            EventType.BEFORE_AGENT,
            source=agent_id,
            data={"task_id": task.id, "role": agent_config.role.value},
            task_id=task.id,
            session_id=task.session_id,
        )
        await self.event_bus.emit(
            EventType.AGENT_STARTED,
            source=agent_id,
            data={"task_id": task.id, "role": agent_config.role.value},
            task_id=task.id,
            session_id=task.session_id,
        )

        try:
            # 1. Assemble system prompt from registry
            task_context = self._build_task_context(task, extra_context)
            system_prompt = self.prompt_registry.assemble_agent_prompt(
                agent_id=agent_id,
                task_context=task_context,
                workflow_instructions=workflow_instructions,
                user_instructions=user_instructions,
            )

            # 2. Build messages
            messages = self._build_messages(
                agent_id=agent_id,
                system_prompt=system_prompt,
                user_message=user_message or task.description,
            )

            # 3. Resolve provider and model
            provider, model = self._resolve_provider_model(agent_config)

            # 4. Check token budget
            if task.token_budget and task.tokens_used >= task.token_budget:
                raise BudgetExceededError(
                    f"Token budget exhausted: {task.tokens_used}/{task.token_budget}"
                )

            # 5. Call LLM
            response = await provider.complete(
                messages=messages,
                model=model,
                temperature=agent_config.model.temperature,
                max_tokens=agent_config.model.max_tokens,
                tools=tools,
            )

            # 6. Store in conversation
            self._append_to_conversation(
                agent_id,
                Message(role=MessageRole.ASSISTANT, content=response.content),
            )

            duration = time.time() - start_time

            result = AgentResult(
                agent_id=agent_id,
                agent_role=agent_config.role,
                status="completed",
                summary=response.content,
                token_usage=response.total_tokens,
                duration_seconds=round(duration, 2),
            )

            # After Agent Hook & Event
            await self.event_bus.emit(
                EventType.AGENT_COMPLETED,
                source=agent_id,
                data={
                    "task_id": task.id,
                    "tokens": response.total_tokens,
                    "duration": duration,
                },
                task_id=task.id,
                session_id=task.session_id,
            )
            await self.event_bus.emit(
                EventType.AFTER_AGENT,
                source=agent_id,
                data={"result": result.model_dump()},
                task_id=task.id,
                session_id=task.session_id,
            )

            return result

        except BudgetExceededError:
            raise
        except Exception as e:
            duration = time.time() - start_time
            await self.event_bus.emit(
                EventType.AGENT_FAILED,
                source=agent_id,
                data={"error": str(e), "task_id": task.id},
                task_id=task.id,
                session_id=task.session_id,
            )
            return AgentResult(
                agent_id=agent_id,
                agent_role=agent_config.role,
                status="failed",
                summary=f"Agent execution failed: {e}",
                issues=[str(e)],
                duration_seconds=round(duration, 2),
            )

    def _resolve_provider_model(
        self, agent_config: AgentConfig
    ) -> tuple[LLMProvider, str]:
        provider_name = agent_config.model.provider
        if provider_name == "inherit" or not provider_name:
            provider_name = self.default_provider

        model_name = agent_config.model.name
        if not model_name:
            model_name = self.default_model

        provider = self.provider_registry.get(provider_name)
        return provider, model_name

    def _build_messages(
        self,
        agent_id: str,
        system_prompt: str,
        user_message: str,
    ) -> list[Message]:
        messages: list[Message] = [
            Message(role=MessageRole.SYSTEM, content=system_prompt),
        ]

        if agent_id in self._conversations:
            messages.extend(self._conversations[agent_id])

        user_msg = Message(role=MessageRole.USER, content=user_message)
        messages.append(user_msg)
        self._append_to_conversation(agent_id, user_msg)

        return messages

    def _append_to_conversation(self, agent_id: str, message: Message) -> None:
        if agent_id not in self._conversations:
            self._conversations[agent_id] = []
        self._conversations[agent_id].append(message)

    def clear_conversation(self, agent_id: str) -> None:
        self._conversations.pop(agent_id, None)

    def _build_task_context(
        self, task: Task, extra: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        ctx: dict[str, Any] = {
            "task_id": task.id,
            "task_title": task.title,
            "task_description": task.description,
            "task_status": task.status.value,
            "iteration": task.iteration,
            "max_iterations": task.max_iterations,
        }
        if task.plan:
            ctx["plan_summary"] = task.plan.summary
            ctx["files_to_modify"] = task.plan.files_to_modify
            ctx["files_to_create"] = task.plan.files_to_create
            ctx["steps"] = [s.description for s in task.plan.steps]
        if extra:
            ctx.update(extra)
        return ctx
