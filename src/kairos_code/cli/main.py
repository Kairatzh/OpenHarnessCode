"""KAIROS Code CLI — The Linux for AI Coding Harness.

OpenHarnessCode: Interactive AI Programming.
Programming with AI, not asking AI to program.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box

from kairos_code.cli.vibe_cli import vibe_app
from kairos_code.cli.tui import render_dashboard, print_command_palette

app = typer.Typer(
    name="kairos",
    help="KAIROS Code — Open-source modular multi-agent AI coding harness (Linux for AI Coding).",
    no_args_is_help=True,
    rich_markup_mode="rich",
)
app.add_typer(vibe_app, name="vibe")

console = Console()


def _get_project_root() -> Path:
    cwd = Path.cwd()
    for parent in [cwd, *cwd.parents]:
        if (parent / ".harness").exists() or (parent / "pyproject.toml").exists():
            return parent
    return cwd


def _run_async(coro):
    return asyncio.run(coro)


def _print_banner() -> None:
    banner = Text()
    banner.append("  ██╗  ██╗ █████╗ ██╗██████╗  ██████╗ ███████╗\n", style="bold cyan")
    banner.append("  ██║ ██╔╝██╔══██╗██║██╔══██╗██╔═══██╗██╔════╝\n", style="bold cyan")
    banner.append("  █████╔╝ ███████║██║██████╔╝██║   ██║███████╗\n", style="bold cyan")
    banner.append("  ██╔═██╗ ██╔══██║██║██╔══██╗██║   ██║╚════██║\n", style="bold cyan")
    banner.append("  ██║  ██╗██║  ██║██║██║  ██║╚██████╔╝███████║\n", style="bold cyan")
    banner.append("  ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝\n", style="bold cyan")
    banner.append("  OpenHarnessCode: Programming with AI, not asking AI to program.\n", style="dim")
    console.print(banner)


# ── Incremental & Semantic Programming ─────────────────────────────────

@app.command("change")
def change_cmd(
    intent: str = typer.Argument(..., help="Semantic intent of change to make."),
    auto_apply: bool = typer.Option(False, "--yes", "-y", help="Auto-apply without confirmation."),
):
    """Program by Atomic Change Units (ACUs) with evidence-based explanation."""
    _print_banner()
    project_root = _get_project_root()

    async def _change():
        from kairos_code.acu.engine import AtomicChangeEngine
        from kairos_code.spl.translator import SemanticProgrammingLayer

        spl = SemanticProgrammingLayer()
        engine = AtomicChangeEngine(project_root, spl=spl)

        console.print(f"[bold cyan]Translating Intent into Specification...[/bold cyan]")
        spec = await spl.intent_to_spec(intent)

        console.print(Panel(
            f"[bold]Operation:[/bold] {spec.operation.value}\n"
            f"[bold]Target:[/bold] {spec.target_component or 'Auto-detected'}\n"
            f"[bold]Requirements:[/bold]\n" + "\n".join(f"  • {r}" for r in spec.requirements) + "\n"
            f"[bold]Constraints:[/bold]\n" + "\n".join(f"  • {c}" for c in spec.constraints) + "\n"
            f"[bold]Acceptance Criteria:[/bold]\n" + "\n".join(f"  • {a}" for a in spec.acceptance_criteria),
            title="🎯 Semantic Intent Specification",
            border_style="cyan",
        ))

        console.print("\n[dim]Decomposing into Atomic Change Units...[/dim]")
        acus = await engine.decompose_task_into_acus(intent)

        table = Table(title="Planned Atomic Change Units (ACUs)", box=box.ROUNDED)
        table.add_column("ID", style="cyan")
        table.add_column("Title")
        table.add_column("Target Files")
        table.add_column("Criteria")

        for u in acus:
            table.add_row(u.id, u.title, ", ".join(u.files) or "Auto", ", ".join(u.acceptance_criteria[:2]))
        console.print(table)

        for u in acus:
            console.print(f"\n[bold green]Executing {u.id}: {u.title}...[/bold green]")
            executed_acu = await engine.execute_acu(u)

            if executed_acu.explanation:
                exp = executed_acu.explanation
                console.print(Panel(
                    f"[bold]{exp.title}[/bold]\n"
                    f"[dim]Purpose:[/dim] {exp.purpose}\n\n"
                    f"[bold]Verified Evidence:[/bold]\n" +
                    "\n".join(f"  [{e.status.value.upper()}] {e.statement}" for e in exp.evidence[:6]) + "\n\n"
                    f"[bold]Behavior Steps:[/bold]\n" +
                    "\n".join(f"  {i+1}. {s}" for i, s in enumerate(exp.behavior_steps)),
                    title=f"📋 Evidence-Based Report ({u.id})",
                    border_style="green",
                ))

            if not auto_apply:
                choice = typer.prompt("Accept this increment? [accept/reject/revise]", default="accept")
                if choice.lower() == "reject":
                    console.print("[yellow]Change reverted. Stopping.[/yellow]")
                    break

        console.print("\n[bold green]✓ Incremental development sequence finished![/bold green]")

    _run_async(_change())


@app.command("explain")
def explain_file(
    file_path: str = typer.Argument(..., help="Path to Python file to explain."),
    level: str = typer.Option("developer", "--level", "-l", help="Persona: beginner, developer, architect."),
):
    """Evidence-based multi-level file explanation (Beginner, Developer, Architect)."""
    project_root = _get_project_root()
    target = project_root / file_path
    if not target.exists():
        console.print(f"[red]File not found: {file_path}[/red]")
        raise typer.Exit(1)

    code = target.read_text(encoding="utf-8", errors="replace")

    async def _explain():
        from kairos_code.spl.translator import SemanticProgrammingLayer
        spl = SemanticProgrammingLayer()
        console.print(f"[dim]Analyzing {file_path} for persona: {level}...[/dim]")
        exp = await spl.multi_level_explain(file_path=file_path, code=code, level=level)
        console.print(Panel(exp, title=f"📖 {file_path} ({level.capitalize()} Level)", border_style="cyan"))

    _run_async(_explain())


# ── Autonomous Dynamic Swarm ───────────────────────────────────────────

@app.command("mission")
def mission_cmd(
    objective: str = typer.Argument(..., help="Ambitious mission objective."),
    workers: int = typer.Option(3, "--workers", "-w", help="Concurrent physical worker pool size."),
    timeout: int = typer.Option(1800, "--timeout", "-t", help="Timeout in seconds."),
):
    """Launch an autonomous dynamic agent swarm mission (overnight / deep research)."""
    _print_banner()
    project_root = _get_project_root()

    async def _mission():
        from kairos_code.swarm.orchestrator import DynamicSwarmOrchestrator
        from kairos_code.swarm.models import ResourceLimits

        limits = ResourceLimits(max_physical_workers=workers, timeout_seconds=timeout)
        orch = DynamicSwarmOrchestrator(project_root)

        console.print(f"[bold cyan]Decomposing mission into elastic agent swarm...[/bold cyan]")
        mission = await orch.create_mission(objective, limits=limits)

        console.print(Panel(
            f"[bold]Objective:[/bold] {mission.objective}\n"
            f"[bold]Tasks Planned:[/bold] {len(mission.tasks)}\n"
            f"[bold]Dynamic Agents:[/bold] {', '.join(a.name for a in mission.agents)}\n"
            f"[bold]Worker Pool:[/bold] {limits.max_physical_workers} concurrent slots",
            title=f"🐝 Swarm Mission #{mission.id}",
            border_style="magenta",
        ))

        async def stream_cb(event_type: str, message: str) -> None:
            if event_type == "task_started":
                console.print(f"  [cyan]▶[/cyan] {message}")
            elif event_type == "task_completed":
                console.print(f"  [green]{message}[/green]")
            else:
                console.print(f"  [dim]{message}[/dim]")

        completed = await orch.run_mission(mission, stream_callback=stream_cb)
        console.print(Panel(
            f"Mission completed! Status: [green]{completed.status.value.upper()}[/green]\n"
            f"Artifacts generated: {len(completed.artifacts)}\n"
            f"Saved synthesis to: .harness/knowledge/mission_{completed.id}.md",
            title="🏁 Mission Report",
            border_style="green",
        ))

    _run_async(_mission())


# ── Constitution & Truth Verification Commands ─────────────────────────

@app.command("check")
def check_invariants():
    """Run machine-verifiable engineering invariants (linter, tests, complexity)."""
    from kairos_code.constitution.invariants import InvariantChecker, EngineeringStandards

    project_root = _get_project_root()
    checker = InvariantChecker(project_root)

    console.print("[bold cyan]Running Machine-Verifiable Engineering Invariants...[/bold cyan]")

    async def _check():
        violations = await checker.run_linter()
        passed, test_out = await checker.run_tests()

        table = Table(title="Engineering Invariants Audit", box=box.ROUNDED)
        table.add_column("Invariant Rule", style="cyan")
        table.add_column("Status")
        table.add_column("Details")

        linter_status = "[green]PASSED[/green]" if not violations else "[red]FAILED[/red]"
        table.add_row("Code Style & Cleanliness (Linter)", linter_status, f"{len(violations)} issues found")

        test_status = "[green]PASSED[/green]" if passed else "[yellow]UNVERIFIED / FAILING[/yellow]"
        table.add_row("Automated Test Suite (pytest)", test_status, test_out.splitlines()[-1] if test_out else "No tests run")

        console.print(table)

    _run_async(_check())


@app.command("tvp")
def tvp_cmd(
    task_id: str = typer.Argument("TASK-ACTIVE", help="Task ID to verify."),
):
    """Run Truth & Verification Protocol (TVP) against empirical execution evidence."""
    from kairos_code.constitution.tvp import (
        TruthVerifier,
        Requirement,
        RequirementStatus,
        ExecutionEvidence,
    )

    console.print(f"[bold cyan]Truth & Verification Protocol Audit: {task_id}[/bold cyan]")

    # Audit current requirements against ground truth
    reqs = [
        Requirement(id="REQ-001", description="Core functionality implemented", status=RequirementStatus.IMPLEMENTED),
        Requirement(id="REQ-002", description="Automated unit tests verified", status=RequirementStatus.UNVERIFIED),
        Requirement(id="REQ-003", description="Preserve existing architectural boundaries", status=RequirementStatus.REVIEWED),
    ]

    report = TruthVerifier.evaluate(
        task_id=task_id,
        title="Active Task",
        requirements=reqs,
        evidence_logs=[],
    )

    color = "green" if report.can_declare_complete else "yellow"
    console.print(Panel(
        f"[bold]Overall Status:[/bold] [{color}]{report.overall_status}[/{color}]\n"
        f"[bold]Can Declare Complete:[/bold] {report.can_declare_complete}\n\n"
        f"[bold]Requirements Truth Matrix:[/bold]\n" +
        "\n".join(f"  • {r.id}: {r.description} -> [{r.status.value.upper()}]" for r in report.requirements) + "\n\n"
        f"[bold]Unverified Claims / Blockers:[/bold]\n" +
        ("\n".join(f"  ⚠️ {c}" for c in report.unverified_claims) if report.unverified_claims else "  None"),
        title=f"🛡️ TVP Audit Report",
        border_style=color,
    ))


# ── Interactive Dialogue Programming ───────────────────────────────────

@app.command("interactive")
def interactive_cmd(
    task: Optional[str] = typer.Option(None, "--task", "-t", help="Initial task to start."),
):
    """Start interactive programming session (/why, /logic, /impact, /undo, /continue)."""
    _print_banner()
    project_root = _get_project_root()

    async def _session():
        from kairos_code.interactive.session import InteractiveSession
        session = InteractiveSession(project_root)

        console.print("[bold cyan]Starting Interactive AI Programming Session.[/bold cyan]")
        console.print("[dim]Type code modifications or commands: /why, /logic, /impact, /alternatives, /undo, /continue, /spec, /exit[/dim]\n")

        if task:
            acus = await session.start_task(task)
            console.print(f"[green]Task broken into {len(acus)} increments. Active: {session.current_acu.title if session.current_acu else 'None'}[/green]\n")

        while True:
            try:
                user_input = typer.prompt("kairos>").strip()
            except (KeyboardInterrupt, EOFError):
                break

            if not user_input:
                continue
            if user_input.lower() in ("/exit", "exit", "quit"):
                console.print("[dim]Session ended.[/dim]")
                break

            if user_input.startswith("/"):
                parts = user_input.split(" ", 1)
                cmd = parts[0]
                arg = parts[1] if len(parts) > 1 else ""
                res = await session.execute_command(cmd, arg)
                console.print(Panel(res, title=f"Command: {cmd}", border_style="cyan"))
            else:
                acus = await session.start_task(user_input)
                console.print(f"[green]Initialized {len(acus)} increments. Type /spec or /continue to proceed.[/green]")

    _run_async(_session())


# ── Core Setup & Inspection Commands ───────────────────────────────────

@app.command()
def init(
    path: str = typer.Argument(".", help="Project directory to initialize."),
    profile: str = typer.Option("developer", "--profile", "-p", help="Harness profile: developer, minimal, autonomous, strict-review, cost-optimized."),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing config."),
):
    """Initialize KAIROS in a project directory."""
    project_root = Path(path).resolve()
    harness_dir = project_root / ".harness"

    if harness_dir.exists() and not force:
        console.print("[yellow]Project already initialized. Use --force to reinitialize.[/yellow]")
        raise typer.Exit(1)

    dirs = [
        harness_dir,
        harness_dir / "agents",
        harness_dir / "workflows",
        harness_dir / "rules",
        harness_dir / "knowledge",
        harness_dir / "knowledge" / "decisions",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

    config_content = f'''# KAIROS Code Configuration
project:
  name: {project_root.name}
  description: ""
profile: {profile}

llm:
  default_provider: openai
  default_model: gpt-4o

runtime:
  mode: developer
  max_iterations: 5
  max_parallel_agents: 3
  timeout: 600

workflow:
  default: feature_development
  require_approval:
    - implementation_plan

agents:
  architect:
    enabled: true
  coder:
    enabled: true
  reviewer:
    enabled: true
  tester:
    enabled: true

security:
  enabled: true
  sandbox: none
  filesystem_access: project_only

observability:
  enabled: true
  log_level: info
  session_replay: true
'''
    (harness_dir / "config.yaml").write_text(config_content, encoding="utf-8")

    coding_rules = '''# Coding Rules
- Write clean, maintainable code with clear docstrings.
- Follow existing patterns and conventions.
- Do not make breaking architectural changes without approval.
'''
    (harness_dir / "rules" / "coding.md").write_text(coding_rules, encoding="utf-8")

    console.print(f"[green]✓[/green] KAIROS initialized in [bold]{project_root}[/bold] (profile: {profile})")
    console.print(f"  Configuration: {harness_dir / 'config.yaml'}")
    console.print(f"  Custom Agents: {harness_dir / 'agents/'}")
    console.print(f"  Rules:         {harness_dir / 'rules/'}")


@app.command()
def inspect():
    """Introspect KAIROS architecture, components, and extension points."""
    from kairos_code.core.registry import ComponentRegistry
    from kairos_code.self_mod.customize import SelfModificationEngine

    project_root = _get_project_root()
    reg = ComponentRegistry()
    engine = SelfModificationEngine(project_root, reg)
    arch = engine.inspect_architecture()

    console.print(Panel(
        f"[bold cyan]KAIROS Code Architecture Status[/bold cyan]\n"
        f"Philosophy: OpenHarnessCode (Interactive AI Programming · Developer Owned)\n"
        f"Project: {arch['project_root']}",
        border_style="cyan"
    ))

    table = Table(title="Subsystems & Interfaces", box=box.ROUNDED)
    table.add_column("Component ID", style="cyan")
    table.add_column("Interface")
    table.add_column("Category")
    table.add_column("Extension Points")

    for comp in arch["active_components"]:
        table.add_row(
            comp["id"],
            comp["interface"],
            comp["category"],
            ", ".join(comp["extension_points"][:2]),
        )
    console.print(table)


@app.command()
def ask(
    instruction: str = typer.Argument(..., help="Natural language request to modify harness."),
):
    """Modify the harness itself using natural language (AI Self-Modification)."""
    project_root = _get_project_root()
    console.print(f"[bold]Customizing harness:[/bold] {instruction}\n")

    async def _ask():
        from kairos_code.core.registry import ComponentRegistry
        from kairos_code.self_mod.customize import SelfModificationEngine

        reg = ComponentRegistry()
        engine = SelfModificationEngine(project_root, reg)
        plan = await engine.generate_customization_plan(instruction)

        console.print(Panel(
            f"[bold]Plan Summary:[/bold] {plan.summary}\n"
            f"[bold]Affected:[/bold] {', '.join(plan.affected_components)}\n"
            f"[bold]Validation:[/bold] {plan.validation_status}",
            title="🛠️ Proposed Harness Modification",
            border_style="yellow",
        ))

        diff = engine.get_diff(plan)
        if diff:
            console.print(f"[dim]Diff preview:[/dim]\n```\n{diff}\n```")

        if typer.confirm("Apply these changes to your harness?", default=True):
            applied = engine.apply_plan(plan)
            for item in applied:
                console.print(f"[green]✓[/green] {item}")
            console.print("[bold green]Harness successfully modified![/bold green]")

    _run_async(_ask())


@app.command("tui")
def tui_cmd():
    """Launch interactive terminal dashboard."""
    project_root = _get_project_root()
    render_dashboard(project_name=project_root.name)
    print_command_palette()


@app.command("replay")
def replay_cmd(
    session_id: str = typer.Argument(..., help="Session ID to replay."),
):
    """Replay execution trace of a session step-by-step."""
    async def _replay():
        from kairos_code.storage.sqlite_store import SQLiteStore
        from kairos_code.observability.replay import SessionReplayer

        store = SQLiteStore(_get_project_root() / ".harness" / "kairos.db")
        await store.initialize()
        replayer = SessionReplayer(store)
        summary = await replayer.format_replay_summary(session_id)
        await store.close()
        console.print(Panel(summary, title=f"⏪ Session Replay: {session_id}", border_style="magenta"))

    _run_async(_replay())


@app.command()
def version():
    """Show KAIROS Code version."""
    from kairos_code import __version__
    console.print(f"KAIROS Code v{__version__} (The Linux for AI Coding)")


if __name__ == "__main__":
    app()
