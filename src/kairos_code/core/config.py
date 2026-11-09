"""Configuration management with multi-level merge and profile support.

Priority: Session → Project (.harness/config.yaml) → Global (~/.kairos/config.yaml) → Profile → Defaults.
Philosophy: Developer owns everything. Developer-controlled policies instead of forced guardrails.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Optional

import yaml
from pydantic import BaseModel, Field


# ── Config Models ──────────────────────────────────────────────────────

class LLMConfig(BaseModel):
    """LLM provider configuration."""
    default_provider: str = "openai"  # openai, anthropic, gemini, ollama, local
    default_model: str = "gpt-4o"
    fallback_model: Optional[str] = None
    api_keys: dict[str, str] = Field(default_factory=dict)
    base_urls: dict[str, str] = Field(default_factory=lambda: {
        "ollama": "http://localhost:11434",
        "local": "http://localhost:8000/v1",
    })


class RuntimeConfig(BaseModel):
    """Runtime behavior configuration."""
    mode: str = "developer"  # "developer" or "vibe"
    max_iterations: int = 5
    max_parallel_agents: int = 3
    timeout: int = 600
    token_budget: Optional[int] = None
    retry_on_failure: bool = True
    max_retries: int = 2
    auto_git_checkpoints: bool = True


class SecurityConfig(BaseModel):
    """Developer-controlled security and isolation policies.
    
    In KAIROS, guardrails are NOT forced by the harness core.
    The developer controls permissions, command filters, and approvals.
    """
    enabled: bool = True
    sandbox: str = "none"  # "none", "docker", "subprocess"
    filesystem_access: str = "project_only"  # "project_only" or "unrestricted"
    network_access: bool = True
    command_allowlist: list[str] = Field(
        default_factory=lambda: [
            "python", "pip", "pytest", "git", "ls", "cat", "grep", "find",
            "node", "npm", "npx", "cargo", "go", "make", "docker", "ruff",
        ]
    )
    command_denylist: list[str] = Field(
        default_factory=lambda: [
            "rm -rf /", "sudo rm", "mkfs", "chmod -R 777 /",
        ]
    )
    require_approval: list[str] = Field(
        default_factory=lambda: [
            "implementation_plan",
        ]
    )
    secret_patterns: list[str] = Field(
        default_factory=lambda: [
            r"(?i)(api[_-]?key|secret|token|password)\s*[:=]\s*\S+",
            r"(?i)bearer\s+\S+",
        ]
    )


class ObservabilityConfig(BaseModel):
    """Logging and observability configuration."""
    enabled: bool = True
    log_level: str = "info"
    save_traces: bool = True
    save_agent_conversations: bool = True
    metrics_enabled: bool = True
    session_replay: bool = True
    log_dir: Optional[str] = None


class AgentOverride(BaseModel):
    """Per-agent configuration override."""
    enabled: bool = True
    model_provider: Optional[str] = None
    model_name: Optional[str] = None
    temperature: Optional[float] = None
    prompt_override: Optional[str] = None
    extra_capabilities: list[str] = Field(default_factory=list)


class WorkflowConfig(BaseModel):
    """Workflow configuration."""
    default: str = "feature_development"
    require_approval: list[str] = Field(
        default_factory=lambda: ["implementation_plan"]
    )
    auto_test: bool = True
    auto_review: bool = True


class HarnessConfig(BaseModel):
    """Top-level harness configuration."""
    project_name: str = "kairos-project"
    project_description: str = ""
    project_root: Optional[str] = None
    profile: str = "developer"  # developer, minimal, autonomous, research, strict-review, cost-optimized
    
    llm: LLMConfig = Field(default_factory=LLMConfig)
    runtime: RuntimeConfig = Field(default_factory=RuntimeConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    observability: ObservabilityConfig = Field(default_factory=ObservabilityConfig)
    workflow: WorkflowConfig = Field(default_factory=WorkflowConfig)
    agents: dict[str, AgentOverride] = Field(default_factory=dict)
    
    profiles: list[str] = Field(default_factory=list)
    plugins: list[str] = Field(default_factory=list)

    def get_agent_override(self, agent_id: str) -> AgentOverride:
        """Get override config for a specific agent, with defaults."""
        return self.agents.get(agent_id, AgentOverride())


# ── Config Loading & Merging ───────────────────────────────────────────

def _deep_merge(base: dict, override: dict) -> dict:
    """Deep merge two dicts; override wins for leaf values."""
    merged = base.copy()
    for key, value in override.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _find_config_files(project_root: Path | None = None) -> list[Path]:
    """Find config files in priority order: global, project."""
    files: list[Path] = []

    # Global config (~/.kairos/config.yaml)
    global_dir = Path.home() / ".kairos"
    for name in ("config.yaml", "config.yml", "harness.yaml", "harness.yml"):
        candidate = global_dir / name
        if candidate.exists():
            files.append(candidate)
            break

    # Project config (.harness/config.yaml)
    if project_root:
        for name in (
            ".harness/config.yaml", ".harness/config.yml",
            "harness.yaml", "harness.yml",
            ".kairos.yaml", ".kairos.yml",
        ):
            candidate = project_root / name
            if candidate.exists():
                files.append(candidate)
                break

    return files


def load_config(
    project_root: Path | str | None = None,
    profile_name: str | None = None,
    session_overrides: dict[str, Any] | None = None,
) -> HarnessConfig:
    """Load and merge configuration from all levels.
    
    Priority: Session → Project → Global → Profile → Defaults.
    """
    if project_root is not None:
        project_root = Path(project_root)

    merged: dict[str, Any] = {}

    # Load profile first if requested or from files
    if profile_name:
        profile_path = Path(__file__).parent.parent / "profiles" / f"{profile_name}.yaml"
        if profile_path.exists():
            try:
                with open(profile_path, encoding="utf-8") as f:
                    pdata = yaml.safe_load(f)
                    if pdata:
                        merged = _deep_merge(merged, pdata)
            except Exception:
                pass

    for config_file in _find_config_files(project_root):
        try:
            with open(config_file, encoding="utf-8") as f:
                data = yaml.safe_load(f)
            if data:
                merged = _deep_merge(merged, data)
        except Exception:
            pass

    if session_overrides:
        merged = _deep_merge(merged, session_overrides)

    if project_root:
        merged.setdefault("project_root", str(project_root))

    # Inject API keys from environment
    llm_cfg = merged.setdefault("llm", {})
    api_keys = llm_cfg.setdefault("api_keys", {})
    env_map = {
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "google": "GOOGLE_API_KEY",
        "gemini": "GEMINI_API_KEY",
    }
    for provider, env_var in env_map.items():
        if provider not in api_keys:
            val = os.environ.get(env_var)
            if val:
                api_keys[provider] = val

    return HarnessConfig(**merged)
