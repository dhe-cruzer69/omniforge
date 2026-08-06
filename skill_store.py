"""
Skill Store – auto-captures and retrieves campaign skills
Uses ChromaDB (local, free) + sentence-transformers embeddings.
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

from config import CHROMA_PATH, SKILLS_DIR, EMBEDDING_MODEL, SKILL_SIMILARITY_THRESHOLD


class SkillStore:
    def __init__(self):
        self.embedder = SentenceTransformer(EMBEDDING_MODEL)
        self.client = chromadb.PersistentClient(
            path=str(CHROMA_PATH),
            settings=Settings(anonymized_telemetry=False)
        )
        self.collection = self.client.get_or_create_collection(
            name="omniforge_skills",
            metadata={"hnsw:space": "cosine"}
        )

    def _embed(self, text: str) -> List[float]:
        return self.embedder.encode(text).tolist()

    def save_skill(self, skill: Dict[str, Any]) -> str:
        """Save a skill document both as JSON and in the vector store."""
        skill_id = skill.get("id") or str(uuid.uuid4())[:8]
        skill["id"] = skill_id
        skill["created_at"] = skill.get("created_at") or datetime.now().isoformat()

        # Persist JSON
        path = SKILLS_DIR / f"skill_{skill_id}.json"
        path.write_text(json.dumps(skill, indent=2))

        # Index for similarity search
        description = f"{skill.get('task', '')} {skill.get('brand', '')} {' '.join(skill.get('tags', []))}"
        self.collection.upsert(
            ids=[skill_id],
            embeddings=[self._embed(description)],
            documents=[description],
            metadatas=[{
                "task": skill.get("task", ""),
                "brand": skill.get("brand", ""),
                "quality_score": float(skill.get("quality_score", 0)),
                "path": str(path),
            }]
        )
        return skill_id

    def find_similar(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Return past skills most similar to the new brief."""
        if self.collection.count() == 0:
            return []

        results = self.collection.query(
            query_embeddings=[self._embed(query)],
            n_results=min(top_k, self.collection.count())
        )

        matches = []
        for i, skill_id in enumerate(results["ids"][0]):
            score = 1 - results["distances"][0][i]  # cosine distance → similarity
            if score < SKILL_SIMILARITY_THRESHOLD:
                continue
            meta = results["metadatas"][0][i]
            path = Path(meta["path"])
            if path.exists():
                skill = json.loads(path.read_text())
                skill["_similarity"] = round(score, 3)
                matches.append(skill)
        return matches

    def list_skills(self) -> List[Dict[str, Any]]:
        skills = []
        for p in SKILLS_DIR.glob("skill_*.json"):
            skills.append(json.loads(p.read_text()))
        return skills

    def update_skill_with_feedback(self, skill_id: str, feedback: str, new_quality: Optional[float] = None):
        """Record a user nudge / edit so the skill self-improves."""
        path = SKILLS_DIR / f"skill_{skill_id}.json"
        if not path.exists():
            return False
        skill = json.loads(path.read_text())
        skill.setdefault("feedback_history", []).append({
            "time": datetime.now().isoformat(),
            "note": feedback
        })
        if new_quality is not None:
            skill["quality_score"] = new_quality
        self.save_skill(skill)
        return True
