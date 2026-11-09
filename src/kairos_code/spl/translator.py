"""Semantic Programming Layer — Bidirectional Intent ↔ Code translation."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Optional

from kairos_code.providers.base import Message, MessageRole
from kairos_code.providers.registry import ProviderRegistry
from kairos_code.spl.ast_analyzer import ASTAnalyzer
from kairos_code.spl.models import (
    CodeExplanation,
    EvidenceItem,
    EvidenceStatus,
    SemanticIntent,
    SemanticOperationType,
)


class SemanticProgrammingLayer:
    """Bridges human intent, structured semantic contracts, and real code."""

    def __init__(self, provider_registry: Optional[ProviderRegistry] = None) -> None:
        self.provider_registry = provider_registry or ProviderRegistry()

    async def intent_to_spec(
        self,
        raw_intent: str,
        context_summary: str = "",
        provider_name: str = "openai",
        model_name: str = "gpt-4o",
    ) -> SemanticIntent:
        """Translate high-level developer intent into a structured semantic specification."""
        prompt = f"""You are the Semantic Programming Layer (SPL) of KAIROS Code.
Translate this natural language request into a structured technical specification.

Developer Intent:
"{raw_intent}"

Context:
{context_summary}

Respond with valid JSON:
{{
  "raw_intent": "{raw_intent}",
  "operation": "add_feature", // add_feature, refactor, bugfix, optimize, simplify, test
  "target_component": "e.g. app/auth or core/security",
  "requirements": ["req1", "req2"],
  "constraints": ["preserve existing API", "avoid duplicate queries", "ttl: 300"],
  "acceptance_criteria": ["criteria 1", "criteria 2"],
  "assumptions": ["assumed secret exists in config", "assumed async client"]
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

        try:
            data = json.loads(content)
            return SemanticIntent(**data)
        except Exception:
            return SemanticIntent(
                raw_intent=raw_intent,
                operation=SemanticOperationType.ADD_FEATURE,
                requirements=[raw_intent],
                constraints=["Preserve existing project conventions"],
                acceptance_criteria=["Function executes as intended"],
            )

    async def code_to_intent(
        self,
        file_path: str,
        old_code: str,
        new_code: str,
        test_output: str = "",
        provider_name: str = "openai",
        model_name: str = "gpt-4o",
    ) -> CodeExplanation:
        """Synthesize an evidence-based technical explanation from AST, diff, and tests."""
        # 1. Real AST Symbol Diff (Ground Truth / Observed)
        ast_changes = ASTAnalyzer.diff_symbols(old_code, new_code, file_path)
        function_calls = ASTAnalyzer.extract_function_calls(new_code)

        evidence: list[EvidenceItem] = []
        for sym in ast_changes:
            evidence.append(EvidenceItem(
                statement=f"{sym.change_type.capitalize()} {sym.symbol_type} '{sym.name}' with signature: {sym.signature}",
                status=EvidenceStatus.OBSERVED,
                source=f"ast:{sym.name}",
            ))

        # 2. Test Verification (Ground Truth / Tested)
        tests_passed = 0
        tests_run = 0
        if test_output:
            if "passed" in test_output.lower():
                tests_passed = 1
                tests_run = 1
                evidence.append(EvidenceItem(
                    statement="Automated test suite executed successfully for this change",
                    status=EvidenceStatus.TESTED,
                    source="pytest",
                    details=test_output[:200],
                ))
            else:
                tests_run = 1
                evidence.append(EvidenceItem(
                    statement="Automated test run reported errors or warnings",
                    status=EvidenceStatus.TESTED,
                    source="pytest",
                    details=test_output[:200],
                ))
        else:
            evidence.append(EvidenceItem(
                statement="Automated test suite has not yet been executed for this change",
                status=EvidenceStatus.UNVERIFIED,
                source="test_runner",
            ))

        # 3. LLM Synthesis for human behavior steps and tradeoffs (Inferred)
        prompt = f"""Analyze the code changes in '{file_path}' using the verified facts below.
Do not hallucinate functions that were not in the AST.

Verified AST changes:
{json.dumps([c.model_dump() for c in ast_changes], indent=2)}

Function calls in new code:
{function_calls}

New Code:
```python
{new_code[:4000]}
```

Provide JSON:
{{
  "title": "Short title of the change",
  "purpose": "Precise technical purpose",
  "behavior_steps": ["Step 1: Check cache", "Step 2: Compute if absent"],
  "dependencies": ["dependency names"],
  "tradeoffs_and_alternatives": ["alternative 1 considered"],
  "assumptions_made": ["assumption 1"]
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

        try:
            synth = json.loads(content)
        except Exception:
            synth = {
                "title": f"Updated {file_path}",
                "purpose": "Implemented requested modifications",
                "behavior_steps": [f"Modified symbols: {', '.join(s.name for s in ast_changes)}"],
                "dependencies": [],
                "tradeoffs_and_alternatives": [],
                "assumptions_made": [],
            }

        for step in synth.get("behavior_steps", []):
            evidence.append(EvidenceItem(
                statement=f"Behavior step: {step}",
                status=EvidenceStatus.INFERRED,
                source="llm_synthesis",
            ))

        return CodeExplanation(
            file_path=file_path,
            title=synth.get("title", f"Change in {file_path}"),
            purpose=synth.get("purpose", ""),
            behavior_steps=synth.get("behavior_steps", []),
            dependencies=synth.get("dependencies", []),
            ast_changes=ast_changes,
            evidence=evidence,
            tests_run=tests_run,
            tests_passed=tests_passed,
            tradeoffs_and_alternatives=synth.get("tradeoffs_and_alternatives", []),
            assumptions_made=synth.get("assumptions_made", []),
        )

    async def multi_level_explain(
        self,
        file_path: str,
        code: str,
        level: str = "developer",
        provider_name: str = "openai",
        model_name: str = "gpt-4o",
    ) -> str:
        """Explain a file across 3 developer personas: beginner, developer, architect."""
        prompts = {
            "beginner": "Explain what this file does in simple everyday analogies for someone learning programming.",
            "developer": "Explain the Python functions, classes, types, control flow, and error handling for an experienced engineer.",
            "architect": "Analyze the module's single responsibility, coupling, abstractions, trade-offs, and architectural role.",
        }
        target_prompt = prompts.get(level, prompts["developer"])

        full_prompt = f"""File: {file_path}
{target_prompt}

Code:
```python
{code[:6000]}
```
"""
        provider = self.provider_registry.get(provider_name)
        res = await provider.complete(
            messages=[Message(role=MessageRole.USER, content=full_prompt)],
            model=model_name,
            temperature=0.2,
        )
        return res.content
