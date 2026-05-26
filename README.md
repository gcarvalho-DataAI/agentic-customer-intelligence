# Agentic Customer Intelligence

End-to-end AI engineering case combining customer clustering, persona agents, and a conversational interface for business intelligence.

## Modules

- `ml-clustering`: unsupervised ML pipeline for consumer segmentation and cluster profiling.
- `agentic-personas`: LangGraph persona layer derived from cluster profiles.
- `apps/api`: FastAPI service for chat orchestration and persistence integration.
- `apps/web`: React interface for stakeholder conversations.
- `infra`: Docker-oriented infrastructure for MongoDB and PostgreSQL/pgvector.
- `docs`: case statement, executive notes, architecture notes, and final delivery material.

## Planned Stack

- Python managed with UV.
- ML with pandas, scikit-learn, matplotlib, and seaborn.
- Agents with LangGraph.
- API with FastAPI.
- Web UI with React.
- Conversation persistence with MongoDB.
- Vector storage with PostgreSQL and pgvector.
- Local services with Docker.

## End-to-End Flow

```text
Synthetic customer data
-> ML preprocessing
-> clustering
-> cluster profiling
-> persona prompt generation
-> LangGraph agents
-> FastAPI chat API
-> React stakeholder interface
```

## Setup

```bash
uv sync
```

Run the ML notebook after installing the environment:

```bash
uv run jupyter notebook ml-clustering/notebooks/customer_segmentation_clustering.ipynb
```

