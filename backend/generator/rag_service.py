from typing import List, Dict
from pathlib import Path
import sys

from qdrant_client import QdrantClient

# Ensure project root (which holds config.py and utils.py) is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import QDRANT_URL, QDRANT_API_KEY, QDRANT_COLLECTION, EMBEDDING_MODEL
from utils import load_embedding_model, normalize_text


def search_templates(query: str, top_k: int = 5) -> List[dict]:
	client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
	model = load_embedding_model(EMBEDDING_MODEL)
	qvec = model.encode([normalize_text(query)], normalize_embeddings=True)[0].tolist()
	result = client.search(
		collection_name=QDRANT_COLLECTION,
		query_vector=qvec,
		with_payload=True,
		limit=top_k,
	)
	matches: List[dict] = []
	for p in result:
		payload = p.payload or {}
		content: str = payload.get("content", "")
		matches.append({
			"id": payload.get("template_id", str(p.id)),
			"score": float(p.score) if p.score is not None else None,
			"content": content,
		})
	return matches


def detect_placeholders(text: str) -> List[str]:
	import re
	candidates = set()
	candidates.update(re.findall(r"\{([a-zA-Z0-9_ ]{2,40})\}", text))
	candidates.update(re.findall(r"\[\[\s*([a-zA-Z0-9_ ]{2,40})\s*\]\]", text))
	candidates.update(re.findall(r"<\s*([a-zA-Z0-9_ ]{2,40})\s*>", text))
	candidates.update(re.findall(r"\b([A-Z]{3,}(?:_[A-Z]{3,})+)\b", text))
	norm: List[str] = []
	seen = set()
	for c in candidates:
		key = "_".join(c.strip().lower().split())
		if 2 <= len(key) <= 40 and key not in seen:
			seen.add(key)
			norm.append(key)
	return norm


def fill_template(content: str, values: Dict[str, str]) -> str:
	out = content
	for key, val in values.items():
		out = out.replace("{" + key + "}", val)
		out = out.replace("[[" + key + "]]", val)
		out = out.replace("<" + key + ">", val)
		out = out.replace(key.upper(), val)
	return out
