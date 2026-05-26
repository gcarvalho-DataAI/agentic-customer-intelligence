from __future__ import annotations

from pathlib import Path

from .schemas import KnowledgeDocument
from .utils import slugify


def parse_markdown_with_metadata(path: Path) -> tuple[dict[str, object], str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        raise ValueError(f"Missing frontmatter metadata in {path}")

    _, raw_meta, content = text.split("---", 2)
    metadata: dict[str, object] = {}
    current_list_key: str | None = None
    for line in raw_meta.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("- ") and current_list_key:
            value = stripped[2:].strip()
            metadata.setdefault(current_list_key, [])
            assert isinstance(metadata[current_list_key], list)
            metadata[current_list_key].append(value)
            continue
        if ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        key = key.strip()
        value = value.strip()
        if value:
            metadata[key] = value
            current_list_key = None
        else:
            metadata[key] = []
            current_list_key = key

    topics = metadata.get("topics", "")
    if isinstance(topics, list):
        metadata["topics"] = ", ".join(str(item) for item in topics)

    return metadata, content.strip()


def load_knowledge_documents(base_path: Path) -> list[KnowledgeDocument]:
    documents: list[KnowledgeDocument] = []
    for path in sorted(base_path.rglob("*.md")):
        metadata, content = parse_markdown_with_metadata(path)
        doc_id = str(metadata.get("doc_id") or slugify(path.stem))
        document = KnowledgeDocument(
            doc_id=doc_id,
            persona_id=str(metadata.get("persona_id", "shared")),
            segment_name=str(metadata.get("segment_name", "all")),
            doc_type=str(metadata.get("doc_type", "context")),
            source_type=str(metadata.get("source_type", "internal_context")),
            confidence=str(metadata.get("confidence", "medium")),
            topics=str(metadata.get("topics", "")),
            source_file=str(path.relative_to(base_path)),
            content=content,
        )
        documents.append(document)
    return documents


def chunk_document(content: str, chunk_size: int = 900, overlap: int = 150) -> list[str]:
    if len(content) <= chunk_size:
        return [content]

    chunks: list[str] = []
    start = 0
    while start < len(content):
        end = min(start + chunk_size, len(content))
        chunk = content[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end == len(content):
            break
        start = max(0, end - overlap)
    return chunks

