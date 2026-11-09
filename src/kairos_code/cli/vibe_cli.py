"""Vibe Mode CLI commands."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

from kairos_code.vibe.engine import VibeEngine

vibe_app = typer.Typer(
    name="vibe",
    help="Vibe Mode — Plain-language explanations, visual review, automated tests, safe undo.",
    no_args_is_help=True,
)
console = Console()


def _run_async(coro):
    return asyncio.run(coro)


@vibe_app.command("explain")
def explain():
    """Explain current project changes in friendly, plain language."""
    engine = VibeEngine(project_root=".")
    console.print("[dim]Analyzing workspace changes...[/dim]")
    explanation = _run_async(engine.explain_changes())
    console.print(Panel(explanation, title="💡 What Changed & Why", border_style="cyan"))


@vibe_app.command("review")
def review():
    """Visual code review with plain-language notes and honest disclaimer."""
    engine = VibeEngine(project_root=".")
    console.print("[dim]Reviewing changes...[/dim]")
    summary = _run_async(engine.visual_code_review())

    table = Table(title="🔍 Visual Code Review", box=box.ROUNDED)
    table.add_column("Category", style="cyan")
    table.add_column("Details")

    table.add_row("What Changed", "\n".join(f"• {c}" for c in summary.what_changed))
    table.add_row("Why", summary.why_it_changed)
    table.add_row("Potential Errors", "\n".join(f"• {e}" for e in summary.potential_errors_found) or "None identified")
    table.add_row("Tests Status", summary.tests_status)
    table.add_row("Needs Decision", "\n".join(f"• {d}" for d in summary.human_decisions_needed) or "None")

    console.print(table)
    console.print(f"[dim yellow]ℹ️ {summary.disclaimer}[/dim yellow]")


@vibe_app.command("test")
def test_code():
    """Run tests and explain results in plain English."""
    engine = VibeEngine(project_root=".")
    console.print("[dim]Running test suite...[/dim]")
    res = _run_async(engine.test_my_code())

    border = "green" if res["passed"] else "red"
    console.print(Panel(
        f"[bold]{res['summary']}[/bold]\n\n"
        f"[dim]Command: {res['command']}[/dim]\n\n"
        f"```\n{res['output'][:1500]}\n```",
        title="🧪 Test Results",
        border_style=border,
    ))


@vibe_app.command("undo")
def undo():
    """Undo changes and return to a clean state."""
    engine = VibeEngine(project_root=".")
    confirm = typer.confirm("Are you sure you want to revert uncommitted changes?")
    if confirm:
        res = _run_async(engine.undo_changes())
        console.print(res)


@vibe_app.command("ask")
def ask(question: str = typer.Argument(..., help="Question about your code.")):
    """Ask any question about your codebase."""
    engine = VibeEngine(project_root=".")
    console.print(f"[dim]Thinking...[/dim]")
    answer = _run_async(engine.ask_about_code(question))
    console.print(Panel(answer, title=f"💬 Question: {question}", border_style="blue"))


@vibe_app.command("map")
def project_map():
    """Show visual map of project structure and key components."""
    engine = VibeEngine(project_root=".")
    pmap = _run_async(engine.get_project_map())
    console.print(Panel(pmap, title="🗺️ Project Map", border_style="green"))
