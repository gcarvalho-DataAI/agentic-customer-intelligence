# Agentic Personas

This module consumes `ml-clustering/outputs/cluster_profiles.json` and instantiates one persona agent per cluster using LangGraph.

## Functional Scope

- Load cluster profiles exported by the ML pipeline.
- Build one persona behavior prompt per segment.
- Orchestrate one node/agent per persona in LangGraph plus a final aggregation node.
- Call an OpenAI-compatible LLM endpoint (local API).

## Project Structure

```text
agentic-personas/
├── run_chat.py
└── src/agentic_personas/
    ├── app/
    │   ├── agents/
    │   │   ├── graph.py
    │   │   └── personas/
    │   │       └── prompts/
    │   │           └── agent.md
    │   └── tools/
    │       └── prompting.py
    ├── config.py
    ├── llm_client.py
    ├── profiles.py
    └── service.py
```

## Environment

Set environment variables before running:

```bash
export LLM_BASE_URL="http://localhost:8000/v1"
export LLM_API_KEY="local-key"
export LLM_MODEL="gpt-4o-mini"
export LLM_TEMPERATURE="0.2"
export CLUSTER_PROFILES_PATH="ml-clustering/outputs/cluster_profiles.json"
```

For your setup, `LLM_BASE_URL` should point to your local API in `~/Documentos/llama_cpp_api`.

## Run CLI

```bash
uv sync
PYTHONPATH=agentic-personas/src uv run python agentic-personas/run_chat.py
```

The CLI asks one business question and prints persona responses side by side in terminal output.

## FastAPI + pgvector RAG Backend

The functional API backend lives in:

```text
agentic-personas/backend
```

It uses:

- FastAPI for API routes.
- PostgreSQL + pgvector for retrieval.
- The local OpenAI-compatible API for chat and embeddings.
- `ml-clustering/outputs/cluster_profiles.json` as the persona source of truth.

Expected local LLM API settings:

```env
OPENAI_BASE_URL=http://127.0.0.1:8000/v1
OPENAI_API_KEY=local
OPENAI_MODEL=qwen-linkedin
OPENAI_EMBEDDING_MODEL=nomic-embed
EMBEDDING_DIM=1536
```

The local LLM API should be started with embedding output compatibility:

```env
EMBEDDING_OUTPUT_DIM=1536
EMBEDDING_DIM_STRATEGY=pad_truncate
```

Run:

```bash
docker-compose up -d postgres
cp agentic-personas/backend/.env.example agentic-personas/backend/.env
PYTHONPATH=agentic-personas/backend uv run python agentic-personas/backend/scripts/ingest_knowledge_base.py
PYTHONPATH=agentic-personas/backend uv run uvicorn app.main:app --reload --port 8000
```
