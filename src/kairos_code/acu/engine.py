"""Atomic Change Engine — manages incremental development step by step."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Callable, Coroutine, Optional

from kairos_code.acu.models import ACUStatus, AtomicChangeUnit
from kairos_code.providers.base import Message, MessageRole
from kairos_code.providers.registry import ProviderRegistry
from kairos_code.spl.translator import SemanticProgrammingLayer
from kairos_code.tools.git import GitTool


class AtomicChangeEngine:
    """Orchestrates development through discrete, verifiable Atomic Change Units."""

    def __init__(
        self,
        project_root: str | Path,
        provider_registry: Optional[ProviderRegistry] = None,
        spl: Optional[SemanticProgrammingLayer] = None,
    ) -> None:
        self.project_root = Path(project_root).resolve()
        self.provider_registry = provider_registry or ProviderRegistry()
        self.spl = spl or SemanticProgrammingLayer(self.provider_registry)
        self.git_tool = GitTool(str(self.project_root))
        self._acus: dict[str, AtomicChangeUnit] = {}

    async def decompose_task_into_acus(
        self,
        task_description: str,
        project_context: str = "",
        provider_name: str = "openai",
        model_name: str = "gpt-4o",
    ) -> list[AtomicChangeUnit]:
        """Decompose a large task into a sequence of Atomic Change Units."""
        prompt = f"""You are the Incremental Programming Architect for KAIROS Code.
Decompose the following task into discrete Atomic Change Units (ACUs).
Each ACU must represent a single, logically complete, verifiable change (e.g. 1. Utility -> 2. Schema -> 3. Endpoint -> 4. Middleware -> 5. Integration).

Task:
"{task_description}"

Context:
{project_context}

Respond with valid JSON:
[
  {{
    "id": "ACU-001",
    "title": "JWT Token Generator",
    "description": "Create access token helper function",
    "files": ["app/core/security.py"],
    "dependencies": [],
    "acceptance_criteria": ["Generates valid JWT with expiration"],
    "verification_command": "pytest tests/test_security.py"
  }}
]
"""
        provider = self.provider_registry.get(provider_name)
        res = await provider.complete(
            messages=[Message(role=MessageRole.USER, content=prompt)],
            model=model_name,
            temperature=0.1,
        )

        content = res.content.strip()
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", content)
        if match:
            content = match.group(1).strip()

        try:
            data = json.loads(content)
            units = [AtomicChangeUnit(**item) for item in data]
        except Exception:
            units = [
                AtomicChangeUnit(
                    id="ACU-001",
                    title="Implement Core Logic",
                    description=task_description,
                    acceptance_criteria=["Task implemented"],
                )
            ]

        for u in units:
            self._acus[u.id] = u

        return units

    async def execute_acu(
        self,
        acu: AtomicChangeUnit,
        on_review_requested: Optional[Callable[[AtomicChangeUnit], Coroutine[Any, Any, str]]] = None,
        provider_name: str = "openai",
        model_name: str = "gpt-4o",
    ) -> AtomicChangeUnit:
        """Execute a single ACU:
        1. Capture checkpoint
        2. Generate implementation
        3. Run verification test
        4. Synthesize evidence-based explanation
        5. Request developer acceptance
        """
        # 1. Git checkpoint before starting ACU
        check_res = await self.git_tool.execute(operation="checkpoint", args=f"Pre-{acu.id}: {acu.title}")
        if check_res.success:
            acu.git_checkpoint = check_res.metadata.get("checkpoint_tag")

        acu.status = ACUStatus.PLANNED

        # 2. Implement change using LLM
        prompt = f"""You are executing Atomic Change Unit {acu.id}: {acu.title}
Description: {acu.description}
Files to touch: {acu.files}
Criteria: {acu.acceptance_criteria}

Generate the exact python code implementation for the target files.
Return JSON with format:
{{
  "files": [
    {{
      "path": "path/to/file.py",
      "content": "file code here"
    }}
  ]
}}
"""
        provider = self.provider_registry.get(provider_name)
        res = await provider.complete(
            messages=[Message(role=MessageRole.USER, content=prompt)],
            model=model_name,
            temperature=0.1,
        )

        content = res.content.strip()
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", content)
        if match:
            content = match.group(1).strip()

        old_code = ""
        new_code = ""
        target_path = ""

        try:
            data = json.loads(content)
            for f in data.get("files", []):
                target_path = f["path"]
                dest = self.project_root / target_path
                if dest.exists():
                    old_code = dest.read_text(encoding="utf-8", errors="replace")
                new_code = f["content"]
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_text(new_code, encoding="utf-8")
                acu.files.append(target_path)
            acu.status = ACUStatus.IMPLEMENTED
        except Exception as e:
            acu.status = ACUStatus.REJECTED
            return acu

        # 3. Verification test
        test_output = ""
        if acu.verification_command:
            import os
            import asyncio
            try:
                proc = await asyncio.create_subprocess_shell(
                    acu.verification_command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=str(self.project_root),
                )
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=45)
                test_output = stdout.decode("utf-8", errors="replace") + stderr.decode("utf-8", errors="replace")
            except Exception as e:
                test_output = f"Test execution error: {e}"

        # 4. Synthesize Code-to-Intent Evidence Explanation
        acu.explanation = await self.spl.code_to_intent(
            file_path=target_path or "code",
            old_code=old_code,
            new_code=new_code,
            test_output=test_output,
            provider_name=provider_name,
            model_name=model_name,
        )
        acu.status = ACUStatus.VERIFIED

        # 5. Review callback
        if on_review_requested:
            decision = await on_review_requested(acu)
            if decision == "accept":
                acu.status = ACUStatus.ACCEPTED
            elif decision == "reject":
                acu.status = ACUStatus.REJECTED
                await self.git_tool.execute(operation="rollback")
            elif decision == "revise":
                acu.status = ACUStatus.REVISED
        else:
            acu.status = ACUStatus.ACCEPTED

        return acu

    def get_acu(self, acu_id: str) -> Optional[AtomicChangeUnit]:
        return self._acus.get(acu_id)

    def list_acus(self) -> list[AtomicChangeUnit]:
        return list(self._acus.values())
