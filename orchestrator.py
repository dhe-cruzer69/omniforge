"""
OmniForge Orchestrator – the "Hermes-like layer above"
Plans → Executes → Captures skill → Learns from feedback
"""

import time
import json
from datetime import datetime
from typing import Dict, Any, List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from skill_store import SkillStore
from memory import Memory
from tools import TOOL_REGISTRY
from config import SKILL_SIMILARITY_THRESHOLD

console = Console()


class Orchestrator:
    def __init__(self):
        self.skills = SkillStore()
        self.memory = Memory()

    def plan(self, brief: str, goal: str = "product_launch") -> Dict[str, Any]:
        """
        Inspect the brief, look for similar past skills,
        and decide the tool chain + parameters.
        """
        console.print("\n[bold cyan]🧠 Orchestrator planning...[/bold cyan]")

        # 1. Memory
        brand_voice = self.memory.get_brand_voice()
        goal_tpl = self.memory.get_goal_template(goal) or {}

        # 2. Skill retrieval
        similar = self.skills.find_similar(brief, top_k=2)
        best_skill = similar[0] if similar else None

        # 3. Decide chain
        if best_skill and best_skill.get("_similarity", 0) >= SKILL_SIMILARITY_THRESHOLD:
            chain = best_skill.get("tool_chain", goal_tpl.get("preferred_chain", ["idea-gen", "social-copy"]))
            source = f"Reusing skill '{best_skill.get('task')}' (similarity {best_skill['_similarity']})"
            skill_hints = best_skill
            estimated_speedup = "≈40% faster (skill reuse)"
        else:
            chain = goal_tpl.get("preferred_chain", ["idea-gen", "social-copy", "tts", "landing-page"])
            source = "No strong past skill found → using goal template"
            skill_hints = None
            estimated_speedup = "baseline"

        plan = {
            "brief": brief,
            "goal": goal,
            "brand_voice": brand_voice,
            "chain": chain,
            "skill_hints": skill_hints,
            "source": source,
            "estimated_speedup": estimated_speedup,
            "created_at": datetime.now().isoformat(),
        }
        return plan

    def execute(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """Run the planned tool chain and collect results."""
        console.print(Panel(
            f"[bold]{plan['brief']}[/bold]\n"
            f"Chain: {' → '.join(plan['chain'])}\n"
            f"{plan['source']}\n"
            f"Expected: {plan['estimated_speedup']}",
            title="📋 Execution Plan",
            border_style="green"
        ))

        results = {}
        start = time.time()
        brand = plan["brand_voice"]
        hints = plan.get("skill_hints")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Running workflow...", total=len(plan["chain"]))

            # Sequential for simplicity (can be parallelised later)
            ideas = None
            copy = None

            for tool_name in plan["chain"]:
                progress.update(task, description=f"Running [cyan]{tool_name}[/cyan]...")
                tool_fn = TOOL_REGISTRY.get(tool_name)
                if not tool_fn:
                    results[tool_name] = {"error": f"Unknown tool: {tool_name}"}
                    progress.advance(task)
                    continue

                if tool_name == "idea-gen":
                    ideas = tool_fn(plan["brief"], brand, hints)
                    results[tool_name] = ideas
                elif tool_name == "social-copy":
                    copy = tool_fn(plan["brief"], ideas or {}, brand, hints)
                    results[tool_name] = copy
                elif tool_name == "tts":
                    results[tool_name] = tool_fn(plan["brief"], copy or {}, hints)
                elif tool_name == "landing-page":
                    results[tool_name] = tool_fn(plan["brief"], copy or {}, brand)
                else:
                    results[tool_name] = tool_fn(plan["brief"], brand, hints)

                progress.advance(task)
                time.sleep(0.3)  # tiny pause for UX

        runtime = round(time.time() - start, 1)
        return {
            "plan": plan,
            "results": results,
            "runtime_sec": runtime,
            "finished_at": datetime.now().isoformat(),
        }

    def capture_skill(self, execution: Dict[str, Any], quality_score: float = 8.0,
                      tags: Optional[List[str]] = None) -> str:
        """Distill the run into a reusable skill document."""
        plan = execution["plan"]
        results = execution["results"]

        # Extract simple winning patterns (heuristic)
        patterns = {}
        if "social-copy" in results:
            headlines = results["social-copy"].get("headlines", [])
            if headlines:
                patterns["headline"] = headlines[0][:60]
            patterns["cta"] = results["social-copy"].get("cta", "")
        if "tts" in results:
            patterns["voiceover_style"] = results["tts"].get("style", "")

        skill = {
            "task": plan["brief"],
            "brand": "default",
            "voice": plan["brand_voice"],
            "winning_patterns": patterns,
            "tool_chain": plan["chain"],
            "runtime_sec": execution["runtime_sec"],
            "quality_score": quality_score,
            "tags": tags or [],
            "results_snapshot": {
                k: (v if not isinstance(v, dict) else {kk: str(vv)[:120] for kk, vv in v.items()})
                for k, v in results.items()
            }
        }
        skill_id = self.skills.save_skill(skill)
        console.print(f"[green]✓ Skill captured → skill_{skill_id}.json[/green]")
        return skill_id

    def run_campaign(self, brief: str, goal: str = "product_launch",
                     auto_capture: bool = True, quality: float = 8.5) -> Dict[str, Any]:
        """Full plan → execute → capture cycle."""
        plan = self.plan(brief, goal)
        execution = self.execute(plan)

        # Pretty print results
        console.print("\n[bold magenta]📦 Results[/bold magenta]")
        for tool, output in execution["results"].items():
            console.print(Panel(json.dumps(output, indent=2)[:800], title=tool, border_style="blue"))

        console.print(f"\n⏱  Runtime: {execution['runtime_sec']}s")

        skill_id = None
        if auto_capture:
            skill_id = self.capture_skill(execution, quality_score=quality)

        return {"execution": execution, "skill_id": skill_id}
