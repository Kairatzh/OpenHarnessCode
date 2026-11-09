"""Interactive Terminal User Interface (TUI) & Command Palette."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box

console = Console()


def render_dashboard(
    project_name: str = "kairos-project",
    profile: str = "developer",
    provider: str = "openai / gpt-4o",
    agents_status: Optional[dict[str, str]] = None,
    active_task: Optional[str] = None,
) -> None:
    """Render the ASCII terminal dashboard."""
    agents_status = agents_status or {
        "Architect": "Ready",
        "Coder": "Ready",
        "Reviewer": "Ready",
        "Tester": "Ready",
        "Security": "Disabled",
    }

    table = Table(box=box.ROUNDED, expand=True, title="[bold cyan]KAIROS CODE HARNESS v0.1.0[/bold cyan]")
    table.add_column("System Info", style="white")
    table.add_column("Agent Team", style="cyan")

    info_text = (
        f"[bold]Project:[/bold]  {project_name}\n"
        f"[bold]Profile:[/bold]  {profile}\n"
        f"[bold]Provider:[/bold] {provider}\n"
        f"[bold]Active:[/bold]   {active_task or 'Idle'}\n"
    )

    agent_lines = []
    for name, status in agents_status.items():
        icon = "[green]●[/green]" if status == "Ready" else "[dim]○[/dim]"
        agent_lines.append(f"{icon} {name:<12} [dim]{status}[/dim]")
    agents_text = "\n".join(agent_lines)

    table.add_row(info_text, agents_text)
    console.print(table)
    console.print("[dim]Commands: /help, /agents, /workflows, /models, /project, /system, /vibe, /exit[/dim]\n")


def print_command_palette() -> None:
    """Display the full Command Palette tree."""
    tree = """[bold cyan]KAIROS Command Palette[/bold cyan]
/
├── [bold]Agents[/bold]
│   ├── /agents list        — List all registered and custom agents
│   ├── /agents create <id> — Create a new agent from template
│   └── /agents inspect <id>— View prompt & capabilities
├── [bold]Workflows[/bold]
│   ├── /workflows list     — View available workflows
│   └── /workflows run <id> — Run a specific workflow
├── [bold]Models[/bold]
│   ├── /models list        — View available model providers
│   └── /models switch <id> — Switch active provider/model
├── [bold]Project[/bold]
│   ├── /project inspect    — Introspect architecture & components
│   ├── /project map        — Show visual structure map
│   └── /project context    — Show indexed project context
├── [bold]Self-Modification[/bold]
│   ├── /customize <prompt> — Modify harness agents & workflows with AI
│   └── /reset              — Reset to default configuration
└── [bold]Vibe Mode[/bold]
    ├── /vibe explain       — Plain-language explanation of recent changes
    ├── /vibe review        — Visual human-friendly code review
    ├── /vibe test          — Run tests with human-friendly summary
    └── /vibe undo          — Roll back changes safely
"""
    console.print(Panel(tree, border_style="cyan"))
