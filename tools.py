"""
Tool adapters – free / simulated versions of the original tools.
In a real deployment you would swap these for actual API calls
(Jasper, Murf, etc.). Here we use Ollama so everything stays free.
"""

import json
import time
from typing import Dict, Any, Optional

import ollama
from config import OLLAMA_MODEL, OLLAMA_HOST


def _chat(system: str, user: str) -> str:
    """Call local Ollama model."""
    try:
        resp = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            options={"temperature": 0.7}
        )
        return resp["message"]["content"].strip()
    except Exception as e:
        return f"[LLM ERROR – is Ollama running? ] {e}"


def idea_generator(brief: str, brand_voice: Dict, skill_hints: Optional[Dict] = None) -> Dict[str, Any]:
    """Generate campaign ideas / angles."""
    hints = ""
    if skill_hints and skill_hints.get("winning_patterns"):
        hints = f"\nReuse these proven patterns if they fit: {json.dumps(skill_hints['winning_patterns'])}"

    system = f"""You are a creative strategist.
Brand voice: {json.dumps(brand_voice)}
Return a JSON object with keys: angles (list of 3 short ideas), primary_hook, target_emotion.
{hints}"""
    raw = _chat(system, f"Campaign brief: {brief}")
    try:
        start = raw.find("{")
        end = raw.rfind("}") + 1
        return json.loads(raw[start:end])
    except Exception:
        return {"angles": [raw[:200]], "primary_hook": raw[:80], "target_emotion": "curiosity"}


def social_copywriter(brief: str, ideas: Dict, brand_voice: Dict, skill_hints: Optional[Dict] = None) -> Dict[str, Any]:
    """Write social / ad copy (simulates Jasper)."""
    pattern = ""
    if skill_hints and skill_hints.get("winning_patterns", {}).get("headline"):
        pattern = f"Preferred headline pattern: {skill_hints['winning_patterns']['headline']}"

    system = f"""You are an expert performance copywriter.
Brand voice: {json.dumps(brand_voice)}
{pattern}
Return JSON: {{ "headlines": ["...", "...", "..."], "primary_text": "...", "cta": "..." }}"""
    user = f"Brief: {brief}\nWinning angle: {ideas.get('primary_hook', '')}\nEmotion: {ideas.get('target_emotion', '')}"
    raw = _chat(system, user)
    try:
        start = raw.find("{")
        end = raw.rfind("}") + 1
        return json.loads(raw[start:end])
    except Exception:
        return {"headlines": [raw[:60]], "primary_text": raw[:200], "cta": "Learn more"}


def tts_script(brief: str, copy: Dict, skill_hints: Optional[Dict] = None) -> Dict[str, Any]:
    """Generate a short voice-over script (simulates Murf)."""
    style = "clear and friendly"
    if skill_hints and skill_hints.get("winning_patterns", {}).get("voiceover_style"):
        style = skill_hints["winning_patterns"]["voiceover_style"]

    system = f"""You write short product voice-over scripts (15-25 seconds).
Style: {style}
Return JSON: {{ "script": "...", "estimated_seconds": 20, "style": "{style}" }}"""
    user = f"Product brief: {brief}\nKey copy: {copy.get('primary_text', '')}"
    raw = _chat(system, user)
    try:
        start = raw.find("{")
        end = raw.rfind("}") + 1
        return json.loads(raw[start:end])
    except Exception:
        return {"script": raw[:300], "estimated_seconds": 20, "style": style}


def landing_page_copy(brief: str, copy: Dict, brand_voice: Dict) -> Dict[str, Any]:
    """Generate landing-page sections (simulates GTM Copywriter)."""
    system = f"""You write high-converting landing page copy.
Brand voice: {json.dumps(brand_voice)}
Return JSON with keys: hero_headline, hero_subhead, benefits (list of 3), final_cta"""
    user = f"Brief: {brief}\nExisting ad copy: {copy.get('primary_text', '')}"
    raw = _chat(system, user)
    try:
        start = raw.find("{")
        end = raw.rfind("}") + 1
        return json.loads(raw[start:end])
    except Exception:
        return {
            "hero_headline": copy.get("headlines", ["Welcome"])[0],
            "hero_subhead": copy.get("primary_text", "")[:120],
            "benefits": ["Benefit 1", "Benefit 2", "Benefit 3"],
            "final_cta": copy.get("cta", "Get started")
        }


# Registry so the orchestrator can call tools by name
TOOL_REGISTRY = {
    "idea-gen": idea_generator,
    "social-copy": social_copywriter,
    "tts": tts_script,
    "landing-page": landing_page_copy,
}
