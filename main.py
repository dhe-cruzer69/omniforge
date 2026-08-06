#!/usr/bin/env python3
"""
OmniForge CLI – free local AI workbench orchestrator
"""

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from orchestrator import Orchestrator
from skill_store import SkillStore
from memory import Memory

app = typer.Typer(help="OmniForge – free local AI campaign orchestrator")
console = Console()


@app.command()
def run(
    brief: str = typer.Argument(..., help="Campaign brief, e.g. 'reusable coffee cup for zero-wasters'"),
    goal: str = typer.Option("product_launch", help="Goal template: product_launch | awareness | conversion"),
    no_capture: bool = typer.Option(False, help="Do not auto-save a skill"),
    quality: float = typer.Option(8.5, help="Quality score to attach to the skill"),
):
    """Plan, execute and (optionally) capture a campaign skill."""
    orch = Orchestrator()
    orch.run_campaign(brief, goal=goal, auto_capture=not no_capture, quality=quality)


@app.command()
def skills():
    """List all captured skills."""
    store = SkillStore()
    all_skills = store.list_skills()
    if not all_skills:
        console.print("[yellow]No skills captured yet. Run a campaign first.[/yellow]")
        return

    table = Table(title="Captured Skills")
    table.add_column("ID", style="cyan")
    table.add_column("Task")
    table.add_column("Score", justify="right")
    table.add_column("Chain")
    table.add_column("Runtime", justify="right")

    for s in all_skills:
        table.add_row(
            s.get("id", "?"),
            s.get("task", "")[:50],
            str(s.get("quality_score", "-")),
            " → ".join(s.get("tool_chain", [])),
            f"{s.get('runtime_sec', '-')}s",
        )
    console.print(table)


@app.command()
def feedback(
    skill_id: str = typer.Argument(..., help="Skill ID to update"),
    note: str = typer.Argument(..., help="What you changed / learned"),
    score: float = typer.Option(None, help="Optional new quality score"),
):
    """Record a human edit so the skill self-improves."""
    store = SkillStore()
    ok = store.update_skill_with_feedback(skill_id, note, score)
    if ok:
        console.print(f"[green]✓ Feedback recorded for skill {skill_id}[/green]")
    else:
        console.print(f"[red]Skill {skill_id} not found[/red]")


@app.command()
def brand(
    show: bool = typer.Option(True, help="Show current brand voice"),
    tone: str = typer.Option(None, help="New tone description"),
    style: str = typer.Option(None, help="New style description"),
):
    """View or update the Brand Voice Vault."""
    mem = Memory()
    if tone or style:
        voice = mem.get_brand_voice()
        if tone:
            voice["tone"] = tone
        if style:
            voice["style"] = style
        mem.set_brand_voice(voice)
        console.print("[green]✓ Brand voice updated[/green]")
    console.print(Panel(str(mem.get_brand_voice()), title="Brand Voice Vault"))


@app.command()
def demo():
    """Run a quick demo campaign (eco coffee cup)."""
    console.print(Panel(
        "Demo: reusable coffee cup campaign for zero-wasters\n"
        "This will call the local Ollama model several times.",
        title="OmniForge Demo",
        border_style="magenta"
    ))
    orch = Orchestrator()
    orch.run_campaign(
        brief="reusable coffee cup, target zero-wasters, eco-friendly, modern design",
        goal="product_launch",
        auto_capture=True,
        quality=9.0
    )


if __name__ == "__main__":
    app()
