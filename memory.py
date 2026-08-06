"""
Persistent Memory – Brand Voice Vault + Goal Templates
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional

from config import MEMORY_DIR, DEFAULT_BRAND_VOICE


class Memory:
    def __init__(self):
        self.brand_file = MEMORY_DIR / "brand_voice.json"
        self.goals_file = MEMORY_DIR / "goal_templates.json"
        self._ensure_defaults()

    def _ensure_defaults(self):
        if not self.brand_file.exists():
            self.brand_file.write_text(json.dumps(DEFAULT_BRAND_VOICE, indent=2))
        if not self.goals_file.exists():
            defaults = {
                "product_launch": {
                    "kpis": ["awareness", "waitlist_signups"],
                    "preferred_chain": ["idea-gen", "social-copy", "tts", "landing-page"],
                    "notes": "Lead with problem → solution → social proof"
                },
                "awareness": {
                    "kpis": ["reach", "engagement"],
                    "preferred_chain": ["idea-gen", "social-copy", "tts"],
                    "notes": "Emotional hook + clear benefit"
                },
                "conversion": {
                    "kpis": ["CTR", "signups", "purchases"],
                    "preferred_chain": ["idea-gen", "social-copy", "landing-page"],
                    "notes": "Strong CTA + urgency + proof"
                }
            }
            self.goals_file.write_text(json.dumps(defaults, indent=2))

    def get_brand_voice(self) -> Dict[str, Any]:
        return json.loads(self.brand_file.read_text())

    def set_brand_voice(self, voice: Dict[str, Any]):
        self.brand_file.write_text(json.dumps(voice, indent=2))

    def get_goal_template(self, goal: str) -> Optional[Dict[str, Any]]:
        templates = json.loads(self.goals_file.read_text())
        return templates.get(goal)

    def list_goals(self) -> Dict[str, Any]:
        return json.loads(self.goals_file.read_text())
