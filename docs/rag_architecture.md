# Persona RAG Architecture

## Objective

The RAG layer enriches synthetic persona agents with contextual knowledge while keeping the ML cluster profile as the primary source of truth.

The goal is not to let retrieved documents redefine a persona. The goal is to help each persona answer business questions with better reasoning about price sensitivity, channel switching, promotions, loyalty, habits, trust, and uncertainty.

## Architecture

```text
React UI
  -> FastAPI backend
  -> Persona loader
  -> Persona-aware retriever
  -> PostgreSQL + pgvector
  -> Prompt builder
  -> OpenAI-compatible local LLM API
  -> Persona answer + retrieved context
```

## Data Sources

### Primary Source

`ml-clustering/outputs/cluster_profiles.json`

This file contains:

- `cluster_id`
- `segment_name`
- `cluster_size`
- `cluster_share`
- `profile`
- `differentiators`
- `analytical_notes`
- `business_interpretation`
- `persona_prompt`

This is the statistical source of truth.

### Secondary Source

`agentic-personas/knowledge_base`

Markdown documents enrich interpretation with general behavioral and business context. They are intentionally secondary and must not introduce new statistics.

## Knowledge Base Layout

```text
knowledge_base/
├── shared/
├── persona_0/
├── persona_1/
└── persona_2/
```

Documents under `shared` can be retrieved by any persona. Documents under `persona_N` can only be retrieved for that persona.

## Document Metadata

Each Markdown document starts with frontmatter:

```markdown
---
doc_id: shared_price_sensitivity
persona_id: shared
segment_name: all
doc_type: price_sensitivity
source_type: external_context
confidence: medium
topics:
  - price increase
  - perceived value
---
```

Metadata is stored with each pgvector chunk and returned in retrieval responses for explainability.

## Ingestion Flow

```text
Markdown file
  -> parse metadata
  -> split into chunks
  -> call local /v1/embeddings
  -> store chunk + metadata + embedding in PostgreSQL
```

The ingestion script is idempotent: it drops and recreates the vector table before loading documents.

Command:

```bash
PYTHONPATH=agentic-personas/backend uv run python agentic-personas/backend/scripts/ingest_knowledge_base.py
```

## pgvector Table

Table:

```text
persona_knowledge_chunks
```

Important columns:

- `id`
- `doc_id`
- `persona_id`
- `segment_name`
- `doc_type`
- `source_type`
- `confidence`
- `topics`
- `source_file`
- `content`
- `embedding vector(1536)`

Similarity operator:

```sql
embedding <=> query_embedding
```

The backend uses cosine distance through `vector_cosine_ops`.

## Retrieval Logic

For persona `0`, retrieval searches:

```text
persona_0
shared
```

It never retrieves from:

```text
persona_1
persona_2
```

This prevents cross-contamination between personas.

Default behavior:

- retrieve persona-specific chunks
- retrieve shared chunks
- deduplicate
- return top `TOP_K`

## Prompt Construction

The final prompt includes:

- role and guardrails
- statistical cluster profile
- differentiators versus base
- analytical notes
- business interpretation
- retrieved context
- user question

The prompt explicitly states:

- cluster profile is primary
- retrieved context is secondary
- do not invent statistics
- answer in first person plural
- mention uncertainty when evidence is weak

## API Endpoints

### `GET /api/health`

Checks application status.

### `GET /api/personas`

Returns all personas loaded from `cluster_profiles.json`.

### `GET /api/personas/{cluster_id}`

Returns one persona.

### `POST /api/retrieval/test`

Debug endpoint for retrieval. It returns chunks without calling the LLM.

### `POST /api/chat`

Runs the full flow:

```text
persona profile
  + retrieved context
  + prompt builder
  + LLM response
```

## Local LLM API

The backend expects an OpenAI-compatible local API:

```env
OPENAI_BASE_URL=http://127.0.0.1:8000/v1
OPENAI_API_KEY=local
OPENAI_MODEL=qwen-linkedin
OPENAI_EMBEDDING_MODEL=nomic-embed
EMBEDDING_DIM=1536
```

The local LLM API should expose:

```text
POST /v1/chat/completions
POST /v1/embeddings
```

Recommended local embedding compatibility:

```env
EMBEDDING_OUTPUT_DIM=1536
EMBEDDING_DIM_STRATEGY=pad_truncate
```

## Guardrails

The RAG layer must not:

- invent new demographic or behavioral statistics
- claim retrieved context proves exact cluster behavior
- ignore weak differentiation in the mainstream cluster
- retrieve documents from another persona-specific folder
- override `cluster_profiles.json`

## Demo Narrative

In the presentation, explain:

1. Clustering creates statistically grounded personas.
2. RAG adds behavioral reasoning, not new facts.
3. pgvector retrieval is filtered per persona.
4. The response shows retrieved context for auditability.
5. The mainstream cluster is explicitly labeled as lower differentiation instead of overinterpreted.

