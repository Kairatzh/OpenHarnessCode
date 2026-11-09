"""Interactive Programming Session — dialogue-driven coding commands."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from kairos_code.acu.engine import AtomicChangeEngine
from kairos_code.acu.models import AtomicChangeUnit
from kairos_code.providers.base import Message, MessageRole
from kairos_code.providers.registry import ProviderRegistry
from kairos_code.spl.translator import SemanticProgrammingLayer
from kairos_code.tools.git import GitTool


class InteractiveSession:
    """Manages conversational, command-driven programming with the developer."""

    def __init__(
        self,
        project_root: str | Path,
        provider_registry: Optional[ProviderRegistry] = None,
        provider_name: str = "openai",
        model_name: str = "gpt-4o",
    ) -> None:
        self.project_root = Path(project_root).resolve()
        self.provider_registry = provider_registry or ProviderRegistry()
        self.provider_name = provider_name
        self.model_name = model_name
        self.spl = SemanticProgrammingLayer(self.provider_registry)
        self.acu_engine = AtomicChangeEngine(self.project_root, self.provider_registry, self.spl)
        self.git_tool = GitTool(str(self.project_root))

        self.current_acu: Optional[AtomicChangeUnit] = None
        self.acu_queue: list[AtomicChangeUnit] = []
        self.history: list[dict[str, Any]] = []

    async def start_task(self, task_description: str) -> list[AtomicChangeUnit]:
        """Start task by decomposing into sequential Atomic Change Units (ACUs)."""
        self.acu_queue = await self.acu_engine.decompose_task_into_acus(
            task_description=task_description,
            provider_name=self.provider_name,
            model_name=self.model_name,
        )
        if self.acu_queue:
            self.current_acu = self.acu_queue[0]
        return self.acu_queue

    async def execute_command(self, command: str, arg: str = "") -> str:
        """Handle semantic programming commands (/why, /logic, /impact, etc.)."""
        cmd = command.strip().lower()

        if cmd == "/spec":
            if not self.current_acu:
                return "No active Atomic Change Unit. Start a task first."
            criteria = "\n".join(f"- {c}" for c in self.current_acu.acceptance_criteria)
            return (
                f"### Active ACU: {self.current_acu.id} - {self.current_acu.title}\n"
                f"**Description**: {self.current_acu.description}\n"
                f"**Target Files**: {', '.join(self.current_acu.files) or 'TBD'}\n"
                f"**Acceptance Criteria**:\n{criteria}\n"
                f"**Status**: {self.current_acu.status.value}"
            )

        elif cmd == "/why":
            return await self._ask_llm(
                f"Why was this architectural solution and design chosen for ACU: '{self.current_acu.title if self.current_acu else arg}'? Explain trade-offs and rationale."
            )

        elif cmd == "/logic":
            return await self._ask_llm(
                f"Walk through the step-by-step algorithmic logic of the current code change: '{self.current_acu.title if self.current_acu else arg}'."
            )

        elif cmd == "/impact":
            return await self._ask_llm(
                f"What other components, callers, schemas, and tests in this project are impacted by changing: '{self.current_acu.title if self.current_acu else arg}'?"
            )

        elif cmd == "/alternatives":
            return await self._ask_llm(
                f"What alternative implementations were considered for '{self.current_acu.title if self.current_acu else arg}'? Contrast simplicity, performance, and maintainability."
            )

        elif cmd == "/assume":
            if self.current_acu and self.current_acu.explanation and self.current_acu.explanation.assumptions_made:
                return "Assumptions made by system:\n" + "\n".join(f"- {a}" for a in self.current_acu.explanation.assumptions_made)
            return await self._ask_llm(
                f"List all explicit and implicit assumptions being made in: '{self.current_acu.title if self.current_acu else arg}'."
            )

        elif cmd == "/simplify":
            return await self._ask_llm(
                f"Propose a simpler implementation for '{self.current_acu.title if self.current_acu else arg}' that minimizes cognitive overhead while meeting acceptance criteria."
            )

        elif cmd == "/optimize":
            return await self._ask_llm(
                f"Analyze performance, memory, and database query optimizations for '{self.current_acu.title if self.current_acu else arg}'."
            )

        elif cmd == "/test":
            res = await self.git_tool.execute(operation="status")
            return f"Git Status:\n{res.output}\n(Use verification_command to run test suite)"

        elif cmd == "/undo":
            res = await self.git_tool.execute(operation="rollback")
            return f"Reverted last change: {res.output or res.error or 'Done'}"

        elif cmd == "/continue":
            if not self.acu_queue:
                return "All Atomic Change Units completed! 🎉"
            # Advance to next ACU
            completed = self.acu_queue.pop(0)
            self.history.append({"acu": completed.id, "status": completed.status.value})
            if self.acu_queue:
                self.current_acu = self.acu_queue[0]
                return f"Advanced to next increment: {self.current_acu.id} - {self.current_acu.title}"
            else:
                self.current_acu = None
                return "All increments completed! Task finished."

        else:
            return f"Unknown command: {command}. Available: /why, /logic, /impact, /alternatives, /assume, /simplify, /optimize, /test, /undo, /continue, /spec"

    async def _ask_llm(self, query: str) -> str:
        provider = self.provider_registry.get(self.provider_name)
        res = await provider.complete(
            messages=[
                Message(
                    role=MessageRole.SYSTEM,
                    content="You are an interactive AI pair programmer assisting an experienced software engineer.",
                ),
                Message(role=MessageRole.USER, content=query),
            ],
            model=self.model_name,
            temperature=0.2,
        )
        return res.content
