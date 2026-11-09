"""Prompt Registry — multi-layered prompt management system.

Implements the 6-level prompt hierarchy:
  1. SYSTEM   — General model behavior rules
  2. HARNESS  — Harness-specific operation rules  
  3. AGENT    — Agent role and specialization (YAML frontmatter + Markdown)
  4. WORKFLOW — Workflow-specific instructions
  5. TASK     — Current task context and requirements
  6. USER     — User-provided instructions and preferences
"""

from __future__ import annotations

import re
from enum import IntEnum
from pathlib import Path
from typing import Any, Optional

import yaml
from jinja2 import Environment, BaseLoader
from pydantic import BaseModel, Field


class PromptLayer(IntEnum):
    """Prompt layers in priority order (higher = more specific)."""
    SYSTEM = 1
    HARNESS = 2
    AGENT = 3
    WORKFLOW = 4
    TASK = 5
    USER = 6


class PromptTemplate(BaseModel):
    """A single prompt template with metadata."""
    id: str
    layer: PromptLayer
    content: str
    variables: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class AgentPromptSpec(BaseModel):
    """Parsed agent prompt specification from Markdown + YAML frontmatter."""
    id: str = ""
    name: str = ""
    version: str = "1.0.0"
    role: str = ""
    model: dict[str, Any] = Field(default_factory=dict)
    capabilities: list[str] = Field(default_factory=list)
    permissions: dict[str, bool] = Field(default_factory=dict)
    context_includes: list[str] = Field(default_factory=list)
    memory: dict[str, Any] = Field(default_factory=dict)
    workflow: dict[str, Any] = Field(default_factory=dict)
    prompt_body: str = ""


class PromptRegistry:
    """Central registry for managing, loading, and assembling prompts.
    
    Supports loading from:
    - Built-in prompt files (src/kairos_code/prompts/)
    - Project-level overrides (.harness/agents/, .harness/rules/)
    - Dynamic runtime registration
    """

    def __init__(self) -> None:
        self._templates: dict[str, PromptTemplate] = {}
        self._agent_specs: dict[str, AgentPromptSpec] = {}
        self._rules: dict[str, str] = {}
        self._jinja_env = Environment(loader=BaseLoader())

    def load_builtin_prompts(self, prompts_dir: Path) -> None:
        """Load built-in prompt templates from a directory."""
        if not prompts_dir.exists():
            return
        for file in prompts_dir.rglob("*.md"):
            spec = self._parse_agent_file(file)
            if spec.id:
                self._agent_specs[spec.id] = spec
        for file in prompts_dir.rglob("*.yaml"):
            self._load_yaml_prompts(file)
        for file in prompts_dir.rglob("*.yml"):
            self._load_yaml_prompts(file)

    def load_project_overrides(self, harness_dir: Path) -> None:
        """Load project-level prompt overrides from .harness/ directory."""
        agents_dir = harness_dir / "agents"
        if agents_dir.exists():
            for file in agents_dir.glob("*.md"):
                spec = self._parse_agent_file(file)
                if spec.id:
                    self._agent_specs[spec.id] = spec

        rules_dir = harness_dir / "rules"
        if rules_dir.exists():
            for file in rules_dir.glob("*.md"):
                rule_name = file.stem
                self._rules[rule_name] = file.read_text(encoding="utf-8")

    def register_agent_spec(self, spec: AgentPromptSpec) -> None:
        """Register or override an agent prompt specification."""
        self._agent_specs[spec.id] = spec

    def assemble_agent_prompt(
        self,
        agent_id: str,
        task_context: dict[str, Any] | None = None,
        workflow_instructions: str = "",
        user_instructions: str = "",
        rules: list[str] | None = None,
    ) -> str:
        """Assemble a complete prompt for an agent from all layers.
        
        Merges: SYSTEM + HARNESS + AGENT + WORKFLOW + TASK + USER + RULES
        """
        parts: list[str] = []

        # Layer 1: SYSTEM
        system_tpl = self._templates.get("system")
        if system_tpl:
            parts.append(self._render(system_tpl.content, task_context or {}))

        # Layer 2: HARNESS
        harness_tpl = self._templates.get("harness")
        if harness_tpl:
            parts.append(self._render(harness_tpl.content, task_context or {}))

        # Layer 3: AGENT
        spec = self._agent_specs.get(agent_id)
        if spec and spec.prompt_body:
            parts.append(self._render(spec.prompt_body, task_context or {}))

        # Layer 4: WORKFLOW
        if workflow_instructions:
            parts.append(f"# Workflow Instructions\n\n{workflow_instructions}")

        # Layer 5: TASK
        if task_context:
            task_section = self._format_task_context(task_context)
            if task_section:
                parts.append(task_section)

        # Layer 6: USER
        if user_instructions:
            parts.append(f"# User Instructions\n\n{user_instructions}")

        # Rules
        if rules:
            for rule_name in rules:
                if rule_name in self._rules:
                    parts.append(f"# Rule: {rule_name}\n\n{self._rules[rule_name]}")

        return "\n\n---\n\n".join(parts)

    def get_agent_spec(self, agent_id: str) -> AgentPromptSpec | None:
        return self._agent_specs.get(agent_id)

    def list_agents(self) -> list[str]:
        return list(self._agent_specs.keys())

    def list_rules(self) -> list[str]:
        return list(self._rules.keys())

    def _parse_agent_file(self, path: Path) -> AgentPromptSpec:
        text = path.read_text(encoding="utf-8")
        frontmatter: dict[str, Any] = {}
        body = text

        match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)", text, re.DOTALL)
        if match:
            try:
                frontmatter = yaml.safe_load(match.group(1)) or {}
            except yaml.YAMLError:
                frontmatter = {}
            body = match.group(2)

        agent_id = frontmatter.get("id", path.stem)
        return AgentPromptSpec(
            id=agent_id,
            name=frontmatter.get("name", agent_id),
            version=str(frontmatter.get("version", "1.0.0")),
            role=frontmatter.get("role", agent_id),
            model=frontmatter.get("model", {}),
            capabilities=frontmatter.get("capabilities", []),
            permissions=frontmatter.get("permissions", {}),
            context_includes=frontmatter.get("context", {}).get("include", [])
                if isinstance(frontmatter.get("context"), dict) else [],
            memory=frontmatter.get("memory", {}),
            workflow=frontmatter.get("workflow", {}),
            prompt_body=body.strip(),
        )

    def _load_yaml_prompts(self, path: Path) -> None:
        try:
            with open(path, encoding="utf-8") as f:
                data = yaml.safe_load(f)
            if not isinstance(data, dict):
                return
            for key, value in data.items():
                if isinstance(value, str):
                    layer = PromptLayer.SYSTEM if "system" in key.lower() else PromptLayer.HARNESS
                    self._templates[key] = PromptTemplate(
                        id=key, layer=layer, content=value
                    )
        except Exception:
            pass

    def _render(self, template_str: str, context: dict[str, Any]) -> str:
        try:
            tpl = self._jinja_env.from_string(template_str)
            return tpl.render(**context)
        except Exception:
            return template_str

    def _format_task_context(self, context: dict[str, Any]) -> str:
        parts = ["# Task Context"]
        for key, value in context.items():
            if key.startswith("_"):
                continue
            if isinstance(value, list):
                parts.append(f"\n## {key.replace('_', ' ').title()}")
                for item in value:
                    parts.append(f"- {item}")
            elif isinstance(value, dict):
                parts.append(f"\n## {key.replace('_', ' ').title()}")
                for k, v in value.items():
                    parts.append(f"- **{k}**: {v}")
            else:
                parts.append(f"\n**{key.replace('_', ' ').title()}**: {value}")
        return "\n".join(parts)
