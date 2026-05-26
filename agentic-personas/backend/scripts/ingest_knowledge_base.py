from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config import settings
from app.knowledge_loader import chunk_document, load_knowledge_documents
from app.llm_client import embed_texts
from app.vector_store import add_documents, reset_collection


def main() -> None:
    documents = load_knowledge_documents(settings.knowledge_base_path)
    rows: list[dict] = []
    texts: list[str] = []
    metadata_rows: list[dict] = []

    for document in documents:
        for idx, chunk in enumerate(chunk_document(document.content)):
            chunk_id = f"{document.doc_id}_{idx}"
            texts.append(chunk)
            metadata_rows.append(
                {
                    "id": chunk_id,
                    "doc_id": document.doc_id,
                    "persona_id": document.persona_id,
                    "segment_name": document.segment_name,
                    "doc_type": document.doc_type,
                    "source_type": document.source_type,
                    "confidence": document.confidence,
                    "topics": document.topics,
                    "source_file": document.source_file,
                    "content": chunk,
                }
            )

    embeddings = embed_texts(texts)
    for row, embedding in zip(metadata_rows, embeddings, strict=True):
        rows.append({**row, "embedding": embedding})

    reset_collection()
    inserted = add_documents(rows)
    print(f"Loaded documents: {len(documents)}")
    print(f"Inserted chunks: {inserted}")


if __name__ == "__main__":
    main()

