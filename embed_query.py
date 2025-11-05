import argparse
from typing import List

from config import EMBEDDING_MODEL
from utils import load_embedding_model, normalize_text


def embed_query(query: str) -> List[float]:
    model = load_embedding_model(EMBEDDING_MODEL)
    text = normalize_text(query)
    vector = model.encode([text], normalize_embeddings=True)[0].tolist()
    return vector


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Embed a query using MiniLM-L6-v2")
    parser.add_argument("--query", required=True, help="User query to embed")
    args = parser.parse_args()

    vec = embed_query(args.query)
    print({"dim": len(vec), "preview": vec[:8]})


