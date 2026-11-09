"""Machine-readable Component Registry for KAIROS Code.

Enables self-explaining architecture (`harness inspect`) and AI self-modification (`harness ask` / `harness customize`).
Every subsystem implements a clear Protocol and declares its metadata, extension points, and configurability.
"""

from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel, Field


class ComponentSpec(BaseModel):
    """Specification of an architectural subsystem or component."""
    id: str
    name: str
    category: str  # core, provider, runtime, orchestrator, tool, context, storage, security, observability
    path: str
    interface: str
    description: str
    configurable: bool = True
    replaceable: bool = True
    active_implementation: str = ""
    extension_points: list[str] = Field(default_factory=list)
    configuration_keys: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)


class ComponentRegistry:
    """Central registry of all KAIROS architecture components.
    
    Provides structured introspection for both developers and AI agents
    that perform self-modification.
    """

    def __init__(self) -> None:
        self._components: dict[str, ComponentSpec] = {}
        self._register_default_components()

    def register(self, spec: ComponentSpec) -> None:
        """Register or update a component specification."""
        self._components[spec.id] = spec

    def get(self, component_id: str) -> Optional[ComponentSpec]:
        """Get component specification by ID."""
        return self._components.get(component_id)

    def list_all(self) -> list[ComponentSpec]:
        """List all registered components."""
        return list(self._components.values())

    def list_by_category(self, category: str) -> list[ComponentSpec]:
        """List components in a given category."""
        return [c for c in self._components.values() if c.category == category]

    def to_architecture_summary(self) -> dict[str, Any]:
        """Generate structured architecture summary for AI or CLI inspection."""
        return {
            "harness": "KAIROS Code",
            "philosophy": "Linux for AI Coding (Local-first, Hackable, Minimal Core, Developer-Owned)",
            "components": [c.model_dump() for c in self._components.values()],
        }

    def _register_default_components(self) -> None:
        """Register all default subsystems with their protocols and paths."""
        defaults = [
            ComponentSpec(
                id="agent_runtime",
                name="Agent Runtime",
                category="runtime",
                path="src/kairos_code/runtime/agent.py",
                interface="AgentRuntime",
                description="Executes agents, manages prompts assembly, and coordinates tool execution.",
                configurable=True,
                replaceable=True,
                active_implementation="kairos_code.runtime.agent.AgentRuntime",
                extension_points=["custom agent roles", "prompt templates", "conversation memory"],
                configuration_keys=["agents", "runtime.max_iterations"],
                dependencies=["prompt_registry", "provider_registry", "event_bus"],
            ),
            ComponentSpec(
                id="prompt_registry",
                name="Prompt Registry",
                category="runtime",
                path="src/kairos_code/runtime/prompt_registry.py",
                interface="PromptRegistry",
                description="6-layer prompt hierarchy (System, Harness, Agent, Workflow, Task, User).",
                configurable=True,
                replaceable=True,
                active_implementation="kairos_code.runtime.prompt_registry.PromptRegistry",
                extension_points=[".harness/agents/*.md", ".harness/rules/*.md", ".harness/prompts/"],
                configuration_keys=["prompts"],
                dependencies=[],
            ),
            ComponentSpec(
                id="orchestrator",
                name="Orchestrator Engine",
                category="orchestrator",
                path="src/kairos_code/orchestrator/engine.py",
                interface="Orchestrator",
                description="Coordinates task workflows, parallel agent runs, approvals, and error recovery.",
                configurable=True,
                replaceable=True,
                active_implementation="kairos_code.orchestrator.engine.Orchestrator",
                extension_points=["custom workflows (.harness/workflows/*.yaml)", "approval callbacks", "event hooks"],
                configuration_keys=["workflow.default", "workflow.require_approval"],
                dependencies=["agent_runtime", "context_engine", "tool_registry", "event_bus"],
            ),
            ComponentSpec(
                id="provider_registry",
                name="LLM Provider Abstraction",
                category="provider",
                path="src/kairos_code/providers/registry.py",
                interface="LLMProvider",
                description="Model-agnostic access to OpenAI, Anthropic, Gemini, Ollama, and local LLMs.",
                configurable=True,
                replaceable=True,
                active_implementation="kairos_code.providers.registry.ProviderRegistry",
                extension_points=["custom provider plugins (ProviderPlugin)"],
                configuration_keys=["llm.default_provider", "llm.default_model", "llm.base_urls"],
                dependencies=[],
            ),
            ComponentSpec(
                id="tool_registry",
                name="Tool Runtime",
                category="tool",
                path="src/kairos_code/tools/base.py",
                interface="Tool",
                description="Controlled access to filesystem, terminal commands, and git.",
                configurable=True,
                replaceable=True,
                active_implementation="kairos_code.tools.base.ToolRegistry",
                extension_points=["custom tools (Tool subclass / ToolPlugin)", ".harness/tools/"],
                configuration_keys=["security.command_allowlist"],
                dependencies=["policy_engine"],
            ),
            ComponentSpec(
                id="context_engine",
                name="Context Engine",
                category="context",
                path="src/kairos_code/context/engine.py",
                interface="ContextEngine",
                description="Indexes repo structure, language, framework, dependencies, and conventions.",
                configurable=True,
                replaceable=True,
                active_implementation="kairos_code.context.engine.ContextEngine",
                extension_points=[".harness/knowledge/", ".harness/rules/"],
                configuration_keys=[],
                dependencies=[],
            ),
            ComponentSpec(
                id="storage",
                name="Local Storage Backend",
                category="storage",
                path="src/kairos_code/storage/sqlite_store.py",
                interface="SQLiteStore",
                description="Local-first persistence for tasks, sessions, event logs, and checkpoints.",
                configurable=True,
                replaceable=True,
                active_implementation="kairos_code.storage.sqlite_store.SQLiteStore",
                extension_points=["custom storage adapters"],
                configuration_keys=[],
                dependencies=[],
            ),
            ComponentSpec(
                id="policy_engine",
                name="Policy Engine",
                category="security",
                path="src/kairos_code/security/policy.py",
                interface="PolicyEngine",
                description="Developer-controlled command filters, filesystem boundaries, and secret redaction.",
                configurable=True,
                replaceable=True,
                active_implementation="kairos_code.security.policy.PolicyEngine",
                extension_points=["custom permission rules", "allowlist/denylist customization"],
                configuration_keys=["security"],
                dependencies=[],
            ),
            ComponentSpec(
                id="self_modifier",
                name="Harness Self-Modification Engine",
                category="core",
                path="src/kairos_code/self_mod/customize.py",
                interface="SelfModificationEngine",
                description="Enables natural language self-modification of agents, workflows, and tools.",
                configurable=True,
                replaceable=True,
                active_implementation="kairos_code.self_mod.customize.SelfModificationEngine",
                extension_points=["harness ask", "harness customize"],
                configuration_keys=[],
                dependencies=["component_registry", "provider_registry"],
            ),
            ComponentSpec(
                id="vibe_engine",
                name="Vibe Mode Engine",
                category="core",
                path="src/kairos_code/vibe/engine.py",
                interface="VibeEngine",
                description="Visual/plain-language review, change explanations, test runner, and undo support.",
                configurable=True,
                replaceable=True,
                active_implementation="kairos_code.vibe.engine.VibeEngine",
                extension_points=["visual diff templates", "plain-text review rules"],
                configuration_keys=["runtime.mode"],
                dependencies=["context_engine", "storage"],
            ),
            ComponentSpec(
                id="spl",
                name="Semantic Programming Layer",
                category="core",
                path="src/kairos_code/spl/translator.py",
                interface="SemanticProgrammingLayer",
                description="Bidirectional translation between developer intent and code, grounded in AST and tests.",
                configurable=True,
                replaceable=True,
                active_implementation="kairos_code.spl.translator.SemanticProgrammingLayer",
                extension_points=["AST analyzers", "evidence sources", "multi-level explainers"],
                configuration_keys=[],
                dependencies=["provider_registry"],
            ),
            ComponentSpec(
                id="acu_engine",
                name="Atomic Change Engine",
                category="runtime",
                path="src/kairos_code/acu/engine.py",
                interface="AtomicChangeEngine",
                description="Incremental programming: manages Atomic Change Units (ACU) with git checkpoints and verification.",
                configurable=True,
                replaceable=True,
                active_implementation="kairos_code.acu.engine.AtomicChangeEngine",
                extension_points=["ACU decomposition strategies", "custom verification runners"],
                configuration_keys=[],
                dependencies=["spl", "tools"],
            ),
            ComponentSpec(
                id="swarm_orchestrator",
                name="Dynamic Swarm Orchestrator",
                category="orchestrator",
                path="src/kairos_code/swarm/orchestrator.py",
                interface="DynamicSwarmOrchestrator",
                description="Autonomous elastic agent swarms with dynamic spawning, task DAGs, resource limits, and retirement.",
                configurable=True,
                replaceable=True,
                active_implementation="kairos_code.swarm.orchestrator.DynamicSwarmOrchestrator",
                extension_points=["mission coordinators", "capability acquisition", "resource allocators"],
                configuration_keys=["runtime.max_parallel_agents"],
                dependencies=["provider_registry", "tools"],
            ),
            ComponentSpec(
                id="interactive_session",
                name="Interactive Dialogue Engine",
                category="core",
                path="src/kairos_code/interactive/session.py",
                interface="InteractiveSession",
                description="Conversational programming interface responding to /why, /logic, /impact, /alternatives, /undo.",
                configurable=True,
                replaceable=True,
                active_implementation="kairos_code.interactive.session.InteractiveSession",
                extension_points=["interactive commands", "custom explainers"],
                configuration_keys=[],
                dependencies=["acu_engine", "spl"],
            ),
        ]
        for spec in defaults:
            self.register(spec)
