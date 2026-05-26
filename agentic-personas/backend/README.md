# Persona RAG Backend

FastAPI backend for synthetic persona agents grounded in:

- ML-generated cluster profiles.
- Persona-specific Markdown knowledge base.
- PostgreSQL with pgvector.
- OpenAI-compatible local LLM and embedding API.

## Environment

The local LLM API should expose:

```text
POST /v1/chat/completions
POST /v1/embeddings
```

Recommended local API settings:

```env
EMBEDDING_OUTPUT_DIM=768
EMBEDDING_DIM_STRATEGY=truncate
```

Backend env:

```bash
cp agentic-personas/backend/.env.example agentic-personas/backend/.env
```

## Run

```bash
docker-compose up -d postgres
cp agentic-personas/backend/.env.example agentic-personas/backend/.env
PYTHONPATH=agentic-personas/backend uv run python agentic-personas/backend/scripts/ingest_knowledge_base.py
PYTHONPATH=agentic-personas/backend uv run uvicorn app.main:app --reload --port 8010
```

Use port `8010` for this backend to avoid colliding with the local LLM API, which commonly runs on `8000`.

## Endpoints

- `GET /api/health`
- `GET /api/personas`
- `GET /api/personas/{cluster_id}`
- `POST /api/chat`
- `POST /api/retrieval/test`
- `POST /api/conversations`
- `GET /api/conversations`
- `GET /api/conversations/{conversation_id}`
- `DELETE /api/conversations/{conversation_id}/messages`
- `DELETE /api/conversations/{conversation_id}`

## RAG Design

The statistical cluster profile is the primary source of truth. Retrieved documents are secondary context used to enrich reasoning about:

- price sensitivity
- promotions
- loyalty
- channel switching
- trust
- habit
- uncertainty

The prompt instructs the LLM not to invent new statistics and not to treat retrieved context as proof about the exact cluster.

## pgvector

Ingestion creates:

```text
persona_knowledge_chunks
```

The table stores chunk text, metadata, and `embedding vector(768)`.

Retrieval uses persona-aware filtering:

```text
selected persona documents + shared documents
```

It does not retrieve documents from other personas.

## Retrieval Debug

```bash
curl -X POST http://127.0.0.1:8010/api/retrieval/test \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Como reagiriam a aumento de preço com cashback?",
    "persona_ids": [0],
    "include_context": true
  }'
```

## Chat Example

```bash
curl -X POST http://127.0.0.1:8010/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Como vocês reagiriam a um aumento de preço de 10% na categoria de bebidas?",
    "persona_ids": [0, 1, 2],
    "include_context": true
  }'
```

## Troubleshooting

If ingestion fails, check:

- Postgres is running: `docker-compose up -d postgres`
- pgvector extension exists: `CREATE EXTENSION IF NOT EXISTS vector`
- local LLM API is running on `OPENAI_BASE_URL`
- embedding model is valid in the local API
- local API returns vectors with `EMBEDDING_DIM=1536`

If `/api/chat` returns mock or connection errors, validate:

```bash
curl http://127.0.0.1:8000/v1/models \
  -H "Authorization: Bearer local"
```
