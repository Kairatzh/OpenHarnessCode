# OPENHARNESSCODE CONSTITUTION: Engineering Invariants & Truth Protocol

> **Version**: 1.0.0  
> **Repository**: OpenHarnessCode / KAIROS Code  
> **Status**: Official Engineering Constitution  
> **License**: Apache-2.0  

---

## 1. The Three-Tier Architecture (Two Levels of Freedom)

OpenHarnessCode enforces technical separation between the deterministic execution foundation and user customization:

```
┌───────────────────────────────────────────────────────────────┐
│ Layer 3: User Extensions & Customization                      │
│ • Custom agents (.harness/agents/)                           │
│ • Custom workflows (.harness/workflows/)                      │
│ • Custom tools, plugins, and prompt overrides                 │
│ • Fully hackable, hot-reloadable without modifying source      │
├───────────────────────────────────────────────────────────────┤
│ Layer 2: Standard Agent System (Built-In Engineering Team)    │
│ • 7 pre-configured specialized roles                          │
│ • Standard workflows (feature, bugfix, research)              │
│ • Pre-built profiles (vibe-coder, developer, autonomous)     │
│ • Works out of the box with zero configuration required       │
├───────────────────────────────────────────────────────────────┤
│ Layer 1: Stable Core & Engineering Constitution (Immutable)   │
│ • Execution runtime, task lifecycle, and event bus            │
│ • Truth & Verification Protocol (TVP)                         │
│ • Deterministic test runner & AST symbol analyzer             │
│ • Immutable contracts protected from accidental prompt drift  │
└───────────────────────────────────────────────────────────────┘
```

---

## 2. The Five Inviolable Principles

Regardless of the LLM chosen (OpenAI, Claude, Gemini, or local Ollama), these five principles are deterministically enforced by the runtime:

### Principle 1: No False Completion
An agent cannot declare a task or requirement complete simply by asserting so in natural language. Completion is an empirical status determined strictly by the runtime upon verifying exit codes, test assertions, and file diffs.

### Principle 2: No Unrequested Changes
Agents are forbidden from silently altering unapproved files, rewriting existing working architecture, or introducing unrequested features. Every file modification must correlate directly with an approved Requirement ID.

### Principle 3: Simplicity First
Always favor the simplest, most direct implementation satisfying the acceptance criteria. Prohibit premature abstractions, speculative design patterns, and bloated helper hierarchies.

### Principle 4: Independent Verification
The implementing agent does **not** grade its own homework. Real test suites are executed directly by the harness runtime, and code diffs are evaluated independently by the Code Reviewer and Refactoring Reviewer.

### Principle 5: Traceable Changes
Every code increment must map transparently to:
- An explicit Requirement ID (`REQ-XXX`).
- An Atomic Change Unit (`ACU-XXX`).
- Ground-truth AST symbol diffs (`[OBSERVED]`).
- Automated test output (`[TESTED]`).
- A human-readable technical explanation.

---

## 3. Standard Built-In Engineering Team (7 Specialized Roles)

| Role | Agent ID | Responsibility | Permissions |
| :--- | :--- | :--- | :--- |
| **1. Architect** | `architect` | Analyzes task requirements, explores existing patterns, creates minimal implementation plans with clear dependency bounds. | Read-Only (Filesystem, Git) |
| **2. Implementer** | `implementer` | Writes code strictly adhering to the specification. Bound by anti-bloat constraints; no unrequested changes. | Read & Write (Project files, Terminal) |
| **3. Debugger** | `debugger` | Investigates stack traces, failing assertions, boundary conditions, and inter-component exceptions. | Read-Only Diagnostics & Test Execution |
| **4. Code Reviewer** | `reviewer` | Independently audits git diffs, security vulnerabilities, layer boundaries, and correctness. | Read-Only (Filesystem, Git Diff) |
| **5. Test Engineer** | `tester` | Discovers and executes automated tests (`pytest`, `npm test`, `cargo test`), evaluates real exit codes, checks edge cases. | Read & Execute (Terminal test runners) |
| **6. Refactoring Reviewer** | `refactorer` | Audits code for accidental complexity, dead code, duplicated helper functions, and unnecessary abstractions. | Read-Only (AST, Git Diff) |
| **7. Explainer** | `explainer` | Synthesizes evidence-based multi-level explanations of changes (Beginner, Developer, Architect) grounded in verified AST facts. | Read-Only (Codebase, AST, Evidence) |

---

## 4. Truth & Verification Protocol (TVP)

The **Truth & Verification Protocol** replaces blind LLM confidence with empirical verification:

```
┌────────────────────────────────────────────────────────┐
│ 1. Requirement Tracking                                │
│ • REQ-001: JWT Generation [TESTED]                    │
│ • REQ-002: Preserve Registration [OBSERVED]            │
│ • REQ-003: Auth Unit Tests [UNVERIFIED] ⚠️             │
├────────────────────────────────────────────────────────┤
│ 2. Execution Evidence Log                              │
│ • Command: pytest tests/test_jwt.py -> Exit Code: 0    │
│ • Git tree: 2 files modified (app/auth.py, tests/auth) │
├────────────────────────────────────────────────────────┤
│ 3. Independent Code Review                             │
│ • Reviewer Verdict: APPROVED (0 critical, 0 high)     │
│ • Refactorer Verdict: BALANCED (No dead code)          │
├────────────────────────────────────────────────────────┤
│ 4. Truthful Completion Decision                        │
│ • Overall Status: PARTIAL (REQ-003 pending test run)   │
│ • Can Declare Complete: FALSE                          │
└────────────────────────────────────────────────────────┘
```

### 4.1. The Truth States
- `UNVERIFIED`: Declared in prompt or plan, but no test or tool has evaluated it.
- `IMPLEMENTED`: Code exists in workspace, but automated tests have not executed.
- `TESTED`: Automated test runner executed with exit code `0`.
- `REVIEWED`: Independent Code Reviewer approved the diff.
- `ACCEPTED`: Confirmed by human developer.

---

## 5. Machine-Verifiable Engineering Standards

To keep the codebase clean without 5000-word prompt bloat, OpenHarnessCode integrates machine checkers:
- **Style & Cleanliness**: `Ruff` (Python) / `ESLint` (TypeScript).
- **Static Typing**: `Mypy` / `Pyright`.
- **Security Audits**: `Bandit` / `Semgrep`.
- **Layer Boundary Enforcement**: `import-linter`.
- **Complexity Metrics**: `Radon` (Cyclomatic complexity $\le 15$).

---

## 6. Profiles Matrix

OpenHarnessCode ships with three official operational profiles:

### 1. `vibe-coder`
- **Focus**: Simplicity, fast iterations, conversational building.
- **Workflow**: Automated planning, 1-click test validation, plain-language change summaries, safe git rollback.
- **Agents active**: Architect, Implementer, Reviewer, Tester, Explainer.

### 2. `developer`
- **Focus**: Professional software engineering standard.
- **Workflow**: Rigorous TVP verification, AST-level evidence logs, interactive dialog (`/why`, `/logic`, `/impact`, `/undo`).
- **Agents active**: Full 7-agent engineering team.

### 3. `autonomous`
- **Focus**: Long-running, overnight, and deep research missions.
- **Workflow**: Dynamic elastic swarm, DAG task decomposition, periodic 30-minute git checkpoints, bounded physical worker pool ($K=3$), independent synthesis.
- **Agents active**: Dynamic agent spawning with just-in-time specialization.

---

## 7. Open-Source Precedents & Inspirations

OpenHarnessCode synthesizes insights from modern agentic engineering:
- **OpenAI Harness Engineering (Feb 11, 2026)**: Architecture invariants, machine-checkable constraints, technical debt cleanup.
- **Roo Code**: Custom modes, YAML configurations, role-specific capabilities.
- **OpenHands**: Microagent skills, repository customization, event lifecycle hooks.
- **Continue**: Project-level rules and role-based prompt composition.
- **HAR**: Machine-readable project contracts, isolated worktrees, evidence logs.
- **Keel**: Independent adversarial reviews, grounding claims in external sources.
- **Claude Code**: Pre-commit formatting hooks, compact context restoration.
