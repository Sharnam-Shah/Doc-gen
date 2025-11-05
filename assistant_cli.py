import argparse
import sys
from typing import List, Tuple

from qdrant_client import QdrantClient

from config import QDRANT_URL, QDRANT_API_KEY, QDRANT_COLLECTION, EMBEDDING_MODEL
from utils import load_embedding_model, normalize_text


def qdrant_search(query: str, top_k: int = 5) -> List[dict]:
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
    # Look for simple placeholder patterns commonly seen in templates
    import re
    candidates = set()
    # {name}, {rent_amount}
    candidates.update(re.findall(r"\{([a-zA-Z0-9_ ]{2,40})\}", text))
    # [[NAME]], [[address]]
    candidates.update(re.findall(r"\[\[\s*([a-zA-Z0-9_ ]{2,40})\s*\]\]", text))
    # <name>
    candidates.update(re.findall(r"<\s*([a-zA-Z0-9_ ]{2,40})\s*>", text))
    # ALL_CAPS tokens that look like placeholders (e.g., TENANT_NAME)
    candidates.update(re.findall(r"\b([A-Z]{3,}(?:_[A-Z]{3,})+)\b", text))
    # Normalize
    norm = []
    seen = set()
    for c in candidates:
        key = "_".join(c.strip().lower().split())
        if 2 <= len(key) <= 40 and key not in seen:
            seen.add(key)
            norm.append(key)
    return norm


def fill_template(content: str, values: dict) -> str:
    out = content
    # Replace common placeholder styles with the provided values
    for key, val in values.items():
        # {key}
        out = out.replace("{" + key + "}", val)
        # [[key]]
        out = out.replace("[[" + key + "]]", val)
        # <key>
        out = out.replace("<" + key + ">", val)
        # KEY in ALL_CAPS
        out = out.replace(key.upper(), val)
    return out


def interactive_assistant(user_query: str, top_k: int = 5) -> None:
    print(f"User query: {user_query}")
    results = qdrant_search(user_query, top_k=top_k)
    if not results:
        print("No matching templates found.")
        return

    # If clear best match or only one, auto-select; else ask user
    chosen = results[0]
    if len(results) > 1:
        # If scores are close, let user choose
        s0 = results[0]["score"] or 0.0
        s1 = results[1]["score"] or 0.0
        if abs(s0 - s1) < 0.03:
            print("Multiple relevant templates found. Please choose:")
            for i, r in enumerate(results, start=1):
                snippet = (r["content"][:120] + "...") if len(r["content"]) > 120 else r["content"]
                print(f"{i}. {r['id']} | score={r['score']:.4f} | {snippet}")
            while True:
                try:
                    idx = int(input(f"Enter choice [1-{len(results)}]: ").strip())
                    if 1 <= idx <= len(results):
                        chosen = results[idx - 1]
                        break
                except Exception:
                    pass
                print("Invalid choice, try again.")

    content = chosen["content"]
    placeholders = detect_placeholders(content)
    values = {}
    if placeholders:
        print("I will collect the details required to fill the template.")
        for ph in placeholders:
            prompt = ph.replace("_", " ")
            val = input(f"Enter {prompt}: ").strip()
            values[ph] = val
        filled = fill_template(content, values)
        print("\n--- Generated Document ---\n")
        print(filled)
    else:
        print("Template has no detectable placeholders; here is the best matching template:")
        print("\n--- Template ---\n")
        print(content)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Interactive legal template assistant (search + fill)")
    parser.add_argument("--query", required=True, help="What the user wants, e.g., 'rent agreement' or 'NDA'")
    parser.add_argument("--top_k", type=int, default=5)
    args = parser.parse_args()

    interactive_assistant(args.query, args.top_k)


