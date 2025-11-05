import os
from pathlib import Path
import uuid
from typing import List, Tuple

from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels

from config import QDRANT_URL, QDRANT_API_KEY, QDRANT_COLLECTION, EMBEDDING_MODEL, EMBEDDING_DIM, TEMPLATE_DIR
from utils import load_embedding_model, normalize_text, file_md5, batch_encode


def read_templates(folder: str) -> List[Tuple[str, str]]:
    templates: List[Tuple[str, str]] = []
    for path in sorted(Path(folder).glob("*.txt")):
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        templates.append((path.name, content))
    return templates


def ensure_collection(client: QdrantClient, collection: str, dim: int) -> None:
    exists = False
    try:
        info = client.get_collection(collection_name=collection)
        exists = info.status is not None
    except Exception:
        exists = False

    if not exists:
        client.recreate_collection(
            collection_name=collection,
            vectors_config=qmodels.VectorParams(
                size=dim,
                distance=qmodels.Distance.COSINE,
            ),
        )


def upsert_templates(templates: List[Tuple[str, str]]) -> None:
    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
    ensure_collection(client, QDRANT_COLLECTION, EMBEDDING_DIM)

    model = load_embedding_model(EMBEDDING_MODEL)

    ids: List[str] = []
    payloads: List[dict] = []
    texts: List[str] = []

    for filename, content in templates:
        cleaned = normalize_text(content)
        content_hash = file_md5(os.path.join(TEMPLATE_DIR, filename))
        # Use deterministic UUID derived from filename to satisfy Qdrant ID requirements
        det_id = str(uuid.uuid5(uuid.NAMESPACE_URL, filename))
        ids.append(det_id)
        payloads.append({
            "template_id": filename,
            "content": cleaned,
            "content_md5": content_hash,
        })
        texts.append(cleaned)

    vectors = batch_encode(model, texts)

    points = [
        qmodels.PointStruct(id=ids[i], vector=vectors[i], payload=payloads[i])
        for i in range(len(ids))
    ]

    client.upsert(collection_name=QDRANT_COLLECTION, points=points, wait=True)
    print(f"Upserted {len(points)} templates into collection '{QDRANT_COLLECTION}'.")


if __name__ == "__main__":
    if not Path(TEMPLATE_DIR).exists():
        raise SystemExit(
            f"Template directory '{TEMPLATE_DIR}' not found. Run 'python ingest_templates.py' first."
        )
    templates_data = read_templates(TEMPLATE_DIR)
    if not templates_data:
        raise SystemExit(
            f"No templates found in '{TEMPLATE_DIR}'. Add .txt templates or run 'python ingest_templates.py'."
        )
    upsert_templates(templates_data)


