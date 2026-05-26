from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel

from .service import PersonaOrchestrator


app = FastAPI(title="Agentic Personas API")
orchestrator = PersonaOrchestrator()


class ChatRequest(BaseModel):
    question: str


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "agentic-personas-api"}


@app.get("/segments")
def segments() -> dict[str, list[str]]:
    return {"segments": orchestrator.segment_names}


@app.post("/chat")
def chat(payload: ChatRequest) -> dict[str, object]:
    responses = orchestrator.ask(payload.question)
    return {"question": payload.question, "responses": responses}

