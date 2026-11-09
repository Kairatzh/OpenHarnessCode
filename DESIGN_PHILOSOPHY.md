# DESIGN PHILOSOPHY: The Linux for AI Coding Harness

> **Build your own Harness.**  
> *No locked workflows. No mandatory agents. No hidden restrictions.*

KAIROS Code is not another wrapper over proprietary assistants or an opinionated black-box IDE.  
It is designed as the **Linux for AI Coding Harness**: a hackable, minimal, local-first foundational environment from which any developer can assemble their own customized multi-agent coding machine.

---

## 1. Core Principles

- **Local-first by Design**: Runs on your machine, stores state in SQLite and local files, requires zero mandatory cloud accounts or external telemetry.
- **Hackable**: Every prompt, agent role, permission, workflow, and model adapter is decoupled and user-editable.
- **Minimal Core**: A lean orchestrator and event bus. Everything else is pluggable.
- **Developer-Controlled Policies (No Forced Guardrails)**: Safety mechanisms (command filtering, git checkpoints, sandboxing, approvals) exist as tools under the *developer's* control, never as arbitrary restrictions imposed by the harness author.
- **Model Freedom**: Seamlessly switch between OpenAI, Anthropic Claude, Google Gemini, Ollama, vLLM, or self-hosted local weights.
- **User Ownership**: All history, decisions (ADRs), prompt overrides, and project memory stay in your repository under `.harness/`.

---

## 2. The Three Golden Rules

### Rule 1: The Core Must Stay Small
Any feature that can be implemented as an agent, a workflow, a tool, or a plugin must **never** be hardcoded into the core engine.

### Rule 2: Everything Must Be Replaceable
Every single subsystem implements a formal Python `Protocol` or abstract contract:
- `LLMProvider`
- `AgentRuntime`
- `Orchestrator`
- `ToolRegistry`
- `ContextEngine`
- `StorageBackend`
- `PolicyEngine`

### Rule 3: The Developer Is the Owner
The harness works for you, not the other way around. The developer chooses autonomy levels, approving or bypassing any stage as desired.

---

## 3. One Core. Two Experiences.

```
                  ┌───────────────────────────────┐
                  │       KAIROS Core Runtime     │
                  │  (Events · Orchestrator · DB) │
                  └───────────────┬───────────────┘
                                  │
         ┌────────────────────────┴────────────────────────┐
         │                                                 │
┌────────▼──────────────┐                       ┌──────────▼────────────┐
│    DEVELOPER MODE     │                       │       VIBE MODE       │
├───────────────────────┤                       ├───────────────────────┤
│ • Power CLI & Scripts │                       │ • Plain-English Diffs │
│ • Custom Agent DSL    │                       │ • Visual Code Review  │
│ • Raw Diffs & Git Ops │                       │ • "Test My Code"      │
│ • YAML Workflows      │                       │ • Safe 1-Click Undo   │
│ • Component Registry  │                       │ • Code QA Tutor       │
└───────────────────────┘                       └───────────────────────┘
```

---

## 4. Killer Feature: AI Self-Modification

Through the machine-readable **Component Registry** (`src/kairos_code/core/registry.py`), KAIROS Code understands its own architecture:
- `kairos inspect` outputs all active components, protocols, and extension points.
- `kairos ask "<instruction>"` or `kairos customize` lets the developer instruct the harness in natural language to create new agents, add custom tools, or adjust workflows.
- Changes are presented as a unified diff for developer confirmation before touching the filesystem.

---

## 5. Filesystem Component Architecture (`.harness/`)

```
.harness/
├── config.yaml          # Project configuration & provider settings
├── agents/              # Custom agent Markdown definitions with YAML frontmatter
│   ├── architect.md
│   ├── coder.md
│   └── torch_optimizer.md
├── workflows/           # Custom workflow pipelines
│   └── feature.yaml
├── rules/               # Project-wide coding and architectural rules
│   ├── coding.md
│   └── security.md
├── knowledge/           # Portable project memory
│   ├── architecture.md
│   └── decisions/       # Architecture Decision Records (ADRs)
└── kairos.db            # Local SQLite database (tasks, sessions, traces)
```
