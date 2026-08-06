"""
OmniForge Configuration
All free / local by default.
"""

from pathlib import Path

# Paths
ROOT = Path(__file__).parent
SKILLS_DIR = ROOT / "skills"
MEMORY_DIR = ROOT / "memory"
WORKFLOWS_DIR = ROOT / "workflows"
CHROMA_PATH = ROOT / "chroma_db"

# Ensure directories exist
for d in [SKILLS_DIR, MEMORY_DIR, WORKFLOWS_DIR, CHROMA_PATH]:
    d.mkdir(parents=True, exist_ok=True)

# LLM (Ollama - completely free & local)
OLLAMA_MODEL = "llama3.2"          # or "mistral", "phi3", "gemma2", etc.
OLLAMA_HOST = "http://localhost:11434"

# Embedding model (runs locally via sentence-transformers)
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# Similarity threshold to reuse a past skill
SKILL_SIMILARITY_THRESHOLD = 0.78

# Default brand voice (can be overridden per project)
DEFAULT_BRAND_VOICE = {
    "tone": "clear, helpful, modern",
    "style": "concise with concrete benefits",
    "avoid": ["hype", "jargon", "clickbait"],
}
