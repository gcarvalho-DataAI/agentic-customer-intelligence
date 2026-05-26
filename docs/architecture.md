# Architecture

```text
data/dados_sinteticos.csv
        |
        v
ml-clustering
        |
        v
cluster_profiles.json
        |
        v
agentic-personas / LangGraph
        |
        v
apps/api / FastAPI
        |
        v
apps/web / React
```

## Persistence

- MongoDB stores conversations and message history.
- PostgreSQL with pgvector stores embeddings and retrieval-oriented artifacts.

## UI Direction

The React interface should follow the visual identity of Galaxies, while keeping the stakeholder workflow direct: select personas, ask a business question, compare answers, and inspect cluster profile evidence.

