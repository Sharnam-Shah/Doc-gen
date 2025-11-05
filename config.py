import os
from dotenv import load_dotenv


load_dotenv()


def get_env(name: str, default: str | None = None) -> str:
    value = os.getenv(name, default)
    if value is None:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


QDRANT_URL: str = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_API_KEY: str | None = os.getenv("QDRANT_API_KEY") or None
QDRANT_COLLECTION: str = os.getenv("QDRANT_COLLECTION", "legal_templates")
EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

# Embedding dimensionality for MiniLM-L6-v2 is 384
EMBEDDING_DIM: int = 384

# Data directory for templates
TEMPLATE_DIR: str = os.path.join("data", "templates")


