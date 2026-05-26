# Agentic Customer Intelligence

End-to-end AI engineering case combining customer clustering, persona agents, and a conversational interface for business intelligence.

## Modules

- `ml-clustering`: unsupervised ML pipeline for consumer segmentation and cluster profiling.
- `agentic-personas`: LangGraph persona layer derived from cluster profiles.
- `agentic-personas/backend`: FastAPI service for chat orchestration, RAG, and persistence integration.
- `apps/web`: React interface for stakeholder conversations.
- `infra`: Docker-oriented infrastructure for MongoDB and PostgreSQL/pgvector.
- `docs`: technical report, installation manual, and delivery material.

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

Install dependencies:

```bash
uv sync
```

Copy environment files:

```bash
cp .env.example .env
cp agentic-personas/backend/.env.example agentic-personas/backend/.env
cp apps/web/.env.example apps/web/.env
```

Start databases:

```bash
docker-compose up -d mongo postgres
```

Run ML pipeline (optional, to regenerate clusters and artifacts):

```bash
PYTHONPATH=ml-clustering/src uv run python ml-clustering/run_pipeline.py
```

Ingest knowledge base into pgvector:

```bash
PYTHONPATH=agentic-personas/backend uv run python agentic-personas/backend/scripts/ingest_knowledge_base.py
```

Start backend API (`8010`):

```bash
cd agentic-personas/backend
PYTHONPATH=$(pwd) uv run uvicorn app.main:app --host 0.0.0.0 --port 8010 --reload
```

Start frontend (`5173`):

```bash
cd apps/web
npm install
npm run dev -- --host 0.0.0.0 --port 5173 --strictPort
```

Open:

```text
http://localhost:5173
```

Run the ML notebook:

```bash
uv run jupyter notebook ml-clustering/notebooks/customer_segmentation_clustering.ipynb
```

Notebook path (relative to project):

```text
ml-clustering/notebooks/customer_segmentation_clustering.ipynb
```

## Manuals

Final documents are available in `docs/`:

- Technical report (PDF): `docs/relatorio_final.pdf`
- Technical report (LaTeX): `docs/relatorio_final.tex`
- Installation and operation manual (PDF): `docs/manual_instalacao.pdf`
- Installation and operation manual (LaTeX): `docs/manual_instalacao.tex`

The installation manual includes:

- required components and environment configuration;
- commands to start/stop backend, frontend, and auxiliary API;
- VS Code Run and Debug actions (Start/Stop/Restart and Vector DB actions);
- practical usage guide for collective and individual persona chat.
