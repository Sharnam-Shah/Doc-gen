import argparse
from typing import List

from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels

from config import QDRANT_URL, QDRANT_API_KEY, QDRANT_COLLECTION, EMBEDDING_MODEL
from utils import load_embedding_model, normalize_text


def search(query: str, top_k: int = 3) -> List[dict]:
    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
    model = load_embedding_model(EMBEDDING_MODEL)
    query_vector = model.encode([normalize_text(query)], normalize_embeddings=True)[0].tolist()

    result = client.search(
        collection_name=QDRANT_COLLECTION,
        query_vector=query_vector,
        with_payload=True,
        limit=top_k,
    )

    matches: List[dict] = []
    for point in result:
        payload = point.payload or {}
        content: str = payload.get("content", "")
        excerpt = (content[:240] + "...") if len(content) > 240 else content
        matches.append({
            "id": payload.get("template_id", str(point.id)),
            "score": float(point.score) if point.score is not None else None,
            "excerpt": excerpt,
        })
    return matches


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Semantic search over legal templates")
    parser.add_argument("--query", required=True, help="Search query")
    parser.add_argument("--top_k", type=int, default=3, help="Number of results")
    args = parser.parse_args()

    results = search(args.query, args.top_k)
    for i, r in enumerate(results, start=1):
        print(f"#{i} | score={r['score']:.4f} | id={r['id']}")
        print(r["excerpt"]) 
        print()


