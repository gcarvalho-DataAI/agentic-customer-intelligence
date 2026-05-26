from __future__ import annotations

from collections.abc import Iterable

import psycopg

from .config import settings
from .utils import vector_literal

COLLECTION_TABLE = "persona_knowledge_chunks"


def get_connection() -> psycopg.Connection:
    return psycopg.connect(settings.postgres_dsn)


def init_schema() -> None:
    with get_connection() as conn:
        conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
        conn.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {COLLECTION_TABLE} (
                id TEXT PRIMARY KEY,
                doc_id TEXT NOT NULL,
                persona_id TEXT NOT NULL,
                segment_name TEXT NOT NULL,
                doc_type TEXT NOT NULL,
                source_type TEXT NOT NULL,
                confidence TEXT NOT NULL,
                topics TEXT NOT NULL DEFAULT '',
                source_file TEXT NOT NULL,
                content TEXT NOT NULL,
                embedding vector({settings.embedding_dim}) NOT NULL
            )
            """
        )
        conn.execute(
            f"""
            CREATE INDEX IF NOT EXISTS idx_{COLLECTION_TABLE}_persona
            ON {COLLECTION_TABLE} (persona_id)
            """
        )
        conn.execute(
            f"""
            CREATE INDEX IF NOT EXISTS idx_{COLLECTION_TABLE}_embedding
            ON {COLLECTION_TABLE}
            USING ivfflat (embedding vector_cosine_ops)
            WITH (lists = 100)
            """
        )


def reset_collection() -> None:
    with get_connection() as conn:
        conn.execute(f"DROP TABLE IF EXISTS {COLLECTION_TABLE}")
    init_schema()


def add_documents(chunks: Iterable[dict]) -> int:
    rows = list(chunks)
    if not rows:
        return 0
    init_schema()
    with get_connection() as conn:
        with conn.cursor() as cur:
            for row in rows:
                cur.execute(
                    f"""
                    INSERT INTO {COLLECTION_TABLE} (
                        id, doc_id, persona_id, segment_name, doc_type, source_type,
                        confidence, topics, source_file, content, embedding
                    )
                    VALUES (
                        %(id)s, %(doc_id)s, %(persona_id)s, %(segment_name)s, %(doc_type)s,
                        %(source_type)s, %(confidence)s, %(topics)s, %(source_file)s,
                        %(content)s, %(embedding)s::vector
                    )
                    ON CONFLICT (id) DO UPDATE SET
                        content = EXCLUDED.content,
                        embedding = EXCLUDED.embedding
                    """,
                    {
                        **row,
                        "embedding": vector_literal(row["embedding"]),
                    },
                )
    return len(rows)

