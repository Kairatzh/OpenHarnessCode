# OPENHARNESSCODE_SPEC: Interactive AI Programming & Elastic Swarms

> **Direction**: Programming *with* AI, not asking AI to program.  
> **Repository**: `OpenHarnessCode` / `KAIROS Code`  
> **Status**: Technical Specification v0.2.0  
> **License**: Apache-2.0  

---

## 1. Architectural Philosophy

Existing AI coding assistants suffer from three fundamental deficiencies:
1. **Loss of Developer Control**: Large multi-file monolithic code dumps make it impossible to know what genuinely changed or why.
2. **Context Amnesia**: Iterating on subtle logic forces developers to repeatedly re-explain existing architecture, invariants, and constraints.
3. **Paternalistic / Rigid Autonomy**: Fixed agent teams (e.g. 1 planner, 1 coder) fail on open-ended research, while unbounded generation leads to hallucinated dependencies and untruthful explanations.

**OpenHarnessCode** resolves this by establishing **Evidence-Based Incremental Development**:
- Code is evolved through **Atomic Change Units (ACUs)**.
- Developer intent is explicitly translated into verified syntax structures via the **Semantic Programming Layer (SPL)**.
- Agents operate in an **Elastic Dynamic Swarm**, scaling up or down with resource-aware worker scheduling.

---

## 2. The Four Programming Modes

| Mode | Control Model | Execution Pattern | Best Suited For |
| :--- | :--- | :--- | :--- |
| **1. Interactive Mode** | Developer-Led | Step-by-step ACUs, conversational commands (`/why`, `/logic`, `/impact`), instant undo | Daily feature coding, refactoring, library integrations |
| **2. Collaborative Mode** | Shared Control | Human oversees dynamic agent team, approvals on milestones, continuous diff review | Complex subsystem builds, architectural migrations |
| **3. Autonomous Mode** | AI-Led | Periodic checkpoints (e.g. every 30m), automated test suites, bounded retries | Overnight feature implementations, bug squashing |
| **4. Research Mode** | Experiment-Driven | Swarm surveys publications, GitHub repositories, runs benchmarks, synthesizes report | Architecture trade-off studies, technology evaluation |

---

## 3. Semantic Programming Layer (SPL)

The SPL bridges natural language developer intent, structured semantic contracts, and concrete code changes.

```
┌─────────────────────────────────┐
│     Developer Natural Intent    │
│  "Add caching with 5m TTL..."   │
└────────────────┬────────────────┘
                 │
                 ▼ [Intent-to-Spec]
┌─────────────────────────────────┐
│     Semantic Representation     │
│  • Operation: add_feature       │
│  • Requirements: [ttl=300]      │
│  • Constraints: [no error cache]│
│  • Acceptance Criteria          │
└────────────────┬────────────────┘
                 │
                 ▼ [Code Execution]
┌─────────────────────────────────┐
│       AST + Git + Tests         │
│  • ast: FunctionDef(get_cached) │
│  • git: diff app/cache.py       │
│  • pytest: 5 passed             │
└────────────────┬────────────────┘
                 │
                 ▼ [Code-to-Intent]
┌─────────────────────────────────┐
│    Evidence-Based Explanation   │
│  [OBSERVED] AST symbols changed │
│  [TESTED] Verified by pytest    │
│  [INFERRED] Algorithmic steps   │
│  [UNVERIFIED] External assumptions│
└─────────────────────────────────┘
```

### 3.1. Evidence Taxonomy

To prevent models from hallucinating explanations of what the code purportedly does:
- `OBSERVED`: Verified by deterministic tools (AST parser, git diff, LSP symbol graph).
- `TESTED`: Verified by automated test runner execution (`pytest`, `npm test`, `cargo test`).
- `INFERRED`: Synthesized by LLM reasoning about intent, algorithms, or trade-offs.
- `UNVERIFIED`: Assertions or external assumptions that have not yet undergone verification.

---

## 4. Atomic Change Units (ACU)

An **Atomic Change Unit (ACU)** is the minimal unit of logically complete, verified software evolution.

### 4.1. Contract Schema

```python
class AtomicChangeUnit(BaseModel):
    id: str                         # e.g., "ACU-001"
    title: str                      # e.g., "JWT Token Generator"
    intent: Optional[SemanticIntent]
    description: str
    files: list[str]                # Target files touched
    dependencies: list[str]         # Preceding ACU IDs
    acceptance_criteria: list[str]  # Verifiable criteria
    verification_command: str       # e.g. "pytest tests/test_security.py"
    status: ACUStatus               # INTENT_CAPTURED -> PLANNED -> IMPLEMENTED -> VERIFIED -> ACCEPTED
    explanation: Optional[CodeExplanation] # Grounded in AST and test output
    git_checkpoint: Optional[str]   # Tagged git checkpoint for safe 1-click rollback
```

### 4.2. ACU Lifecycle
1. `Intent Captured`: Developer describes the change in natural language or semantic commands.
2. `Planned`: System decomposes the change, identifies affected files and tests.
3. `Pre-Checkpoint`: Automated `git checkpoint` created.
4. `Implemented`: Code generated and written to workspace.
5. `Verified`: Automated tests run against the change.
6. `Explained`: Truthful AST + Evidence explanation generated.
7. `Decision`: Developer reviews evidence and selects `accept`, `reject` (triggers rollback), or `revise`.

---

## 5. Interactive Programming Dialogue Protocol

Developers converse with the codebase using structured commands that operate directly on project context:

| Command | Semantics | Output |
| :--- | :--- | :--- |
| `/spec` | View active ACU requirements and criteria | Formal contract and acceptance criteria |
| `/why` | Explain architectural decision and trade-offs | Rationale and alternatives considered |
| `/logic` | Step-by-step function control flow | Algorithmic breakdown |
| `/impact` | Blast-radius analysis | Downstream callers, imports, schemas, and tests affected |
| `/alternatives` | Counter-factual architecture proposals | Simpler vs more robust alternative designs |
| `/assume` | Surface implicit assumptions | Invariants assumed by the model |
| `/simplify` | Refactor for minimal complexity | Cognitive complexity reduction |
| `/optimize` | Analyze memory, query, and algorithmic cost | Profiling suggestions |
| `/test` | Verify current code state | Test suite execution and failure analysis |
| `/undo` | Roll back to clean state | Instant restoration of prior checkpoint |
| `/continue` | Advance to next scheduled ACU | Queue progression |

---

## 6. Dynamic Agent Swarm Protocol

Unlike static harnesses with 4 hardcoded agents, OpenHarnessCode supports an **Elastic Agent Swarm**:

```
                       ┌─────────────────────────┐
                       │   Mission Coordinator   │
                       └────────────┬────────────┘
                                    │
           ┌────────────────────────┼────────────────────────┐
           │                        │                        │
┌──────────▼──────────┐  ┌──────────▼──────────┐  ┌──────────▼──────────┐
│   Research Team     │  │   Analysis Team     │  │  Verification Team  │
│ • Paper Analyst     │  │ • Architecture Comp │  │ • Benchmark Runner  │
│ • GitHub Scanner    │  │ • Feasibility Audit │  │ • Critic Agent      │
└──────────┬──────────┘  └──────────┬──────────┘  └──────────┬──────────┘
           │                        │                        │
           └────────────────────────┼────────────────────────┘
                                    │
                       ┌────────────▼────────────┐
                       │   Synthesis Artifact    │
                       │   (FINAL_REPORT.md)     │
                       └─────────────────────────┘
```

### 6.1. Swarm Entities
1. **Mission**: Macro objective with dependency DAG, timeout bounds, and checkpoint cadence.
2. **MissionTask**: Granular unit of work assigned to a specialized agent.
3. **DynamicAgent**: Spawned just-in-time with custom role instructions, capabilities, and tools.
4. **Artifact**: Immutable verified output (code, report, benchmark JSON, dataset).
5. **CapabilityRequest**: Agents can dynamically request new tools (e.g. arXiv API, database profiler).

### 6.2. Resource-Aware Concurrency
- `N Logical Agents` are scheduled across `K Physical Workers` (default: 3 concurrent LLM execution slots).
- Prevents resource exhaustion on local models (Ollama/vLLM) and manages API token rates.

---

## 7. Machine-Readable Component Registry

Every subsystem declares its metadata in `src/kairos_code/core/registry.py`:

```yaml
components:
  - id: spl
    interface: SemanticProgrammingLayer
    path: src/kairos_code/spl/translator.py
    configurable: true
    replaceable: true
  - id: acu_engine
    interface: AtomicChangeEngine
    path: src/kairos_code/acu/engine.py
    configurable: true
    replaceable: true
  - id: swarm_orchestrator
    interface: DynamicSwarmOrchestrator
    path: src/kairos_code/swarm/orchestrator.py
    configurable: true
    replaceable: true
  - id: interactive_session
    interface: InteractiveSession
    path: src/kairos_code/interactive/session.py
    configurable: true
    replaceable: true
```

Command `kairos inspect` outputs the live state of all subsystems and available extension points.  
Command `kairos ask "<instruction>"` modifies agents, tools, and workflows safely via `.harness/`.
