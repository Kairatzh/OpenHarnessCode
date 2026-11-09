"""Vibe Mode Engine — visual, friendly interface layer over the shared core.

Philosophy: One core. Two experiences.
- Developer Mode: Raw CLI, configs, scripts, DSL, full control.
- Vibe Mode: Plain-language explanations, visual diffs, automated tests, safe undo.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, Field

from kairos_code.context.engine import ContextEngine
from kairos_code.providers.base import Message, MessageRole
from kairos_code.providers.registry import ProviderRegistry
from kairos_code.tools.git import GitTool


class VibeReviewSummary(BaseModel):
    """Human-friendly summary for code review in Vibe Mode."""
    what_changed: list[str] = Field(default_factory=list)
    why_it_changed: str = ""
    potential_errors_found: list[str] = Field(default_factory=list)
    tests_status: str = "Not run"
    unverified_aspects: list[str] = Field(default_factory=list)
    human_decisions_needed: list[str] = Field(default_factory=list)
    disclaimer: str = (
        "Note: AI review assists in identifying issues but does not guarantee the absence of bugs. "
        "Always test critical functionality."
    )


class VibeEngine:
    """Core logic powering Vibe Mode features."""

    def __init__(
        self,
        project_root: str | Path,
        provider_registry: Optional[ProviderRegistry] = None,
    ) -> None:
        self.project_root = Path(project_root).resolve()
        self.provider_registry = provider_registry or ProviderRegistry()
        self.context_engine = ContextEngine(self.project_root)
        self.git_tool = GitTool(str(self.project_root))

    async def get_changes_diff(self) -> str:
        """Get git diff of uncommitted or recent changes."""
        res = await self.git_tool.execute(operation="diff")
        if res.success and res.output.strip():
            return res.output
        res_staged = await self.git_tool.execute(operation="diff_staged")
        if res_staged.success and res_staged.output.strip():
            return res_staged.output
        # Check last commit
        res_show = await self.git_tool.execute(operation="show", args="--stat")
        return res_show.output if res_show.success else "No changes detected."

    async def explain_changes(
        self,
        provider_name: str = "openai",
        model_name: str = "gpt-4o",
    ) -> str:
        """Explain current modifications in simple, non-jargon language."""
        diff = await self.get_changes_diff()
        if not diff or "No changes detected" in diff:
            return "No changes detected in your workspace."

        prompt = f"""You are an empathetic senior software developer explaining recent changes to a developer in simple, plain language.
Avoid unnecessary jargon.

Diff:
```
{diff[:8000]}
```

Provide a friendly 3-part breakdown:
1. What was changed in plain words
2. Why these changes were made
3. What you can try next or what to verify
"""
        provider = self.provider_registry.get(provider_name)
        res = await provider.complete(
            messages=[Message(role=MessageRole.USER, content=prompt)],
            model=model_name,
            temperature=0.2,
        )
        return res.content

    async def visual_code_review(
        self,
        provider_name: str = "openai",
        model_name: str = "gpt-4o",
    ) -> VibeReviewSummary:
        """Structured code review with plain-language advice and honest disclaimer."""
        diff = await self.get_changes_diff()
        if not diff or "No changes detected" in diff:
            return VibeReviewSummary(
                what_changed=["No changes detected."],
                why_it_changed="Workspace is clean.",
            )

        prompt = f"""Perform a code review on these changes for Vibe Mode.
Diff:
```
{diff[:8000]}
```

Return structured JSON with keys:
- what_changed: list of short bullets
- why_it_changed: brief summary
- potential_errors_found: list of issues or edge cases
- tests_status: recommendation on what tests to run
- unverified_aspects: parts that the AI could not fully verify
- human_decisions_needed: any architecture/product questions for the human
"""
        provider = self.provider_registry.get(provider_name)
        res = await provider.complete(
            messages=[Message(role=MessageRole.USER, content=prompt)],
            model=model_name,
            temperature=0.1,
        )

        import json
        import re

        content = res.content.strip()
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", content)
        if match:
            content = match.group(1).strip()

        try:
            data = json.loads(content)
            return VibeReviewSummary(**data)
        except Exception:
            return VibeReviewSummary(
                what_changed=["Recent file updates in workspace"],
                why_it_changed=res.content[:300],
                potential_errors_found=["Review output formatting fallback"],
            )

    async def test_my_code(self) -> dict[str, Any]:
        """Automatically detect and run tests, providing a simple human explanation."""
        ctx = await self.context_engine.gather()
        cmd = ""
        if ctx.language == "python":
            cmd = "pytest"
        elif ctx.language in ("javascript", "typescript"):
            cmd = "npm test"
        elif ctx.language == "rust":
            cmd = "cargo test"
        else:
            cmd = "pytest"

        import os
        try:
            if os.name == "nt":
                proc = await asyncio.create_subprocess_shell(
                    cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=str(self.project_root),
                )
            else:
                proc = await asyncio.create_subprocess_exec(
                    cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=str(self.project_root),
                )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=60)
            output = stdout.decode("utf-8", errors="replace") + stderr.decode("utf-8", errors="replace")
            passed = proc.returncode == 0
            return {
                "command": cmd,
                "passed": passed,
                "summary": "All tests passed successfully! 🎉" if passed else "Some tests failed. See details below. ⚠️",
                "output": output[:3000],
            }
        except Exception as e:
            return {
                "command": cmd,
                "passed": False,
                "summary": f"Could not run test suite ({cmd}): {e}",
                "output": str(e),
            }

    async def undo_changes(self) -> str:
        """Revert changes back to previous checkpoint or clean git state."""
        res = await self.git_tool.execute(operation="rollback")
        if res.success:
            return "Changes successfully rolled back to clean state. ↩️"
        return f"Rollback failed: {res.error}"

    async def ask_about_code(
        self,
        question: str,
        provider_name: str = "openai",
        model_name: str = "gpt-4o",
    ) -> str:
        """Ask any question about the project code."""
        ctx = await self.context_engine.gather()
        prompt = f"""You are a helpful software tutor answering questions about this project.
Context:
{ctx.to_prompt_section()}

User Question: {question}
Answer clearly and concisely.
"""
        provider = self.provider_registry.get(provider_name)
        res = await provider.complete(
            messages=[Message(role=MessageRole.USER, content=prompt)],
            model=model_name,
            temperature=0.2,
        )
        return res.content

    async def get_project_map(self) -> str:
        """Produce a visual tree and summary of project components."""
        ctx = await self.context_engine.gather()
        return f"""Project Map: {ctx.project_name} ({ctx.language})
Root: {ctx.project_root}

Structure:
{ctx.structure}

Key Files:
{', '.join(ctx.key_files) if ctx.key_files else 'None detected'}
"""
