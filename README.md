# KAIROS Code

> **The Linux for AI Coding: Your coding environment. Your agents. Your rules.**

Open-source, modular, multi-agent AI coding harness for autonomous software development.

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/python-3.10+-green.svg)](https://www.python.org)
[![Local First](https://img.shields.io/badge/architecture-local--first-success.svg)](DESIGN_PHILOSOPHY.md)

---

## Three-Tier Freedom Architecture

OpenHarnessCode separates the deterministic engine from user customizations:

1. **Layer 1: Stable Core & Engineering Constitution (Immutable)**:
   - Execution runtime, task lifecycle, event bus.
   - **Truth & Verification Protocol (TVP)**: The model never grades its own work; the runtime evaluates completion based on exit codes and real AST diffs.
   - The **5 Inviolable Principles**: No False Completion, No Unrequested Changes, Simplicity First, Independent Verification, Traceable Changes.
2. **Layer 2: Standard Agent System (7 Built-In Specialized Roles)**:
   - **Architect**: Requirements analysis & minimal dependency planning.
   - **Implementer**: Code generation strictly scoped to requirements (no unrequested changes).
   - **Debugger**: Traceback & edge-case root cause isolation.
   - **Code Reviewer**: Independent read-only audit of diffs, security, and layer boundaries.
   - **Test Engineer**: Executes deterministic test suites, inspects exit codes and boundary coverage.
   - **Refactoring Reviewer**: Audits code for dead code, duplicated helpers, and unnecessary abstractions.
   - **Explainer**: Synthesizes multi-level explanations (Beginner, Developer, Architect) grounded in verified AST facts.
3. **Layer 3: User Extensions**:
   - Custom agents in `.harness/agents/`, custom workflows in `.harness/workflows/`, custom rules, and plugins. Hot-reloadable without touching core files.

---

## Machine-Verifiable Engineering Standards

To guarantee clean architecture without 5,000-word prompt bloat, OpenHarnessCode integrates machine checkers:
- **Linter & Style**: `Ruff`
- **Type Checking**: `Pyright` / `Mypy`
- **Security Audits**: `Bandit` / `Semgrep`
- **Testing**: Deterministic `pytest` runs
- **Complexity**: Cyclomatic complexity constraints

Run verification anytime:
```bash
kairos check
kairos tvp verify
```

---

## What is KAIROS Code / OpenHarnessCode?

KAIROS Code is **not** an opaque wrapper around Claude Code, Cursor, or Aider.  
It is built on a different philosophy: **Developer owns everything**.

- 🐧 **Linux for AI Coding**: A clean, modular, extensible foundation. No forced workflows. No mandatory agents.
- 💻 **One Core. Two Experiences**:
  - **Developer Mode**: CLI, YAML DSL, direct prompt hacking, custom agents, hooks, full control.
  - **Vibe Mode**: Plain-English explanations, visual code review, automated testing, 1-click safe undo.
- 🧬 **Self-Modification**: The harness understands its own architecture via a machine-readable `ComponentRegistry`. Customize agents and workflows in natural language (`kairos ask "Add PyTorch optimizer agent"`).
- 🔒 **Local-first by Design**: SQLite persistence, local file tree, zero telemetry, offline execution with Ollama/vLLM.
- 🛡️ **Developer-Controlled Policies**: Safety tools (checkpoints, command filters, approvals) under your command, not imposed as guardrails.

---

## High-Level Architecture

```
                  ┌───────────────────────────────┐
                  │    Developer UX (CLI & TUI)   │
                  │   Developer Mode & Vibe Mode  │
                  └───────────────┬───────────────┘
                                  │
                  ┌───────────────▼───────────────┐
                  │    Harness Orchestrator       │
                  │ (Planning · Routing · Events) │
                  └───────────────┬───────────────┘
                                  │
    ┌────────────────┬────────────┴───┬────────────────┬────────────────┐
    │                │                │                │                │
┌───▼────────┐ ┌─────▼──────┐ ┌───────▼──────┐ ┌───────▼──────┐ ┌───────▼──────┐
│Agent       │ │Context     │ │Tool Runtime  │ │Policy &      │ │Observability │
│Runtime     │ │Engine      │ │(FS, Bash,    │ │Permissions   │ │(Logs, Traces,│
│(Prompts,   │ │(Tree, Repo,│ │ Git)         │ │(Developer    │ │ Replay)      │
│ Memory)    │ │ Conventions│ │              │ │ Controlled)  │ │              │
└───┬────────┘ └────────────┘ └──────────────┘ └──────────────┘ └──────────────┘
    │
┌───▼────────────────────────────────────────┐
│ Model Providers                            │
│ OpenAI · Anthropic · Gemini · Ollama/Local │
└────────────────────────────────────────────┘
```

---

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/your-org/kairos-code.git
cd kairos-code

# Install locally
pip install -e .

# With specific providers:
pip install -e ".[openai,anthropic,google,ollama]"
```

### Initialize a Project

```bash
# Initialize with developer profile
kairos init

# Or initialize with a pre-configured profile:
kairos init --profile minimal
kairos init --profile autonomous
kairos init --profile strict-review
kairos init --profile cost-optimized
```

### Run a Development Task

```bash
# Run a task
kairos run "Create a REST API for user registration with JWT authentication"

# Run with a specific workflow
kairos run "Fix login token expiration" --workflow bugfix

# Auto-approve actions
kairos run "Refactor database models" --auto-approve
```

---

## Two Experiences: Developer Mode & Vibe Mode

### Developer Mode
Designed for engineers who want total control over configuration, pipelines, and prompt layers:
```bash
kairos config show              # Show merged configuration
kairos agent list               # List active and custom agents
kairos agent create researcher  # Scaffold custom agent in .harness/agents/
kairos inspect                  # Introspect architecture and subsystems
kairos replay <session_id>      # Replay step-by-step trace of a session
```

### Vibe Mode
Designed for high-level builders who want clarity without complex terminal setup:
```bash
kairos vibe explain             # Plain-language explanation of recent changes
kairos vibe review              # Visual review with edge-case notes
kairos vibe test                # Run tests with human-friendly summary
kairos vibe undo                # 1-click rollback of changes
kairos vibe ask "How does auth work?"  # Interactive codebase QA
kairos vibe map                 # Visual project component map
```

---

## Killer Feature: Harness Self-Modification

Because KAIROS Code maintains a machine-readable **Component Registry**, it can inspect and modify itself via natural language:

```bash
kairos ask "Add a new agent for PyTorch optimization using local Qwen model with access to Python"
```

The self-modification engine will:
1. Introspect active subsystems via `ComponentRegistry`.
2. Propose new agent definitions (`.harness/agents/torch_optimizer.md`) and configuration updates.
3. Validate syntax and produce a unified diff.
4. Apply the changes upon user confirmation.

---

## 6-Layer Prompt Hierarchy

Prompts are split into distinct layers of responsibility:

1. **SYSTEM**: General model behavior rules.
2. **HARNESS**: Harness-specific operation rules.
3. **AGENT**: Role, capabilities, constraints (YAML frontmatter + Markdown).
4. **WORKFLOW**: Process instructions (e.g. feature development vs bugfix).
5. **TASK**: Current task requirements and context.
6. **USER**: User overrides and runtime directions.

---

## Project Structure (`.harness/`)

```
my-project/
├── .harness/
│   ├── config.yaml          # Project configuration
│   ├── agents/              # Custom agent Markdown definitions
│   │   ├── architect.md
│   │   ├── coder.md
│   │   └── reviewer.md
│   ├── workflows/           # Custom workflow YAML pipelines
│   │   ├── feature.yaml
│   │   └── bugfix.yaml
│   ├── rules/               # Coding and architectural rules
│   │   ├── coding.md
│   │   └── security.md
│   ├── knowledge/           # Portable project memory
│   │   ├── architecture.md
│   │   └── decisions/       # ADRs (Architectural Decision Records)
│   └── kairos.db            # Local SQLite storage (sessions, tasks, traces)
```

---

## Design Philosophy

Read [DESIGN_PHILOSOPHY.md](DESIGN_PHILOSOPHY.md) for the 3 Golden Rules and architectural decisions.

## License

Apache License 2.0. See [LICENSE](LICENSE) for details.
