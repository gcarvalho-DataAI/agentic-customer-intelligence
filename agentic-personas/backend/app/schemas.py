from __future__ import annotations

from pydantic import BaseModel, Field


class PersonaProfile(BaseModel):
    cluster_id: int
    segment_name: str
    cluster_size: int
    cluster_share: float
    profile: dict
    differentiators: list[str] = []
    analytical_notes: list[str] = []
    business_interpretation: str
    persona_prompt: str


class KnowledgeDocument(BaseModel):
    doc_id: str
    persona_id: str
    segment_name: str
    doc_type: str
    source_type: str
    confidence: str
    topics: str = ""
    source_file: str
    content: str


class RetrievedContext(BaseModel):
    doc_id: str
    persona_id: str
    doc_type: str
    confidence: str
    source_file: str
    content: str
    score: float | None = None


class ChatRequest(BaseModel):
    question: str = Field(min_length=1)
    persona_ids: list[int]
    include_context: bool = True
    conversation_id: str | None = None


class RetrievalTestRequest(BaseModel):
    question: str = Field(min_length=1)
    persona_ids: list[int]
    include_context: bool = True


class PersonaAnswer(BaseModel):
    cluster_id: int
    segment_name: str
    answer: str
    retrieved_context: list[RetrievedContext] = []


class ChatResponse(BaseModel):
    question: str
    answers: list[PersonaAnswer]
    conversation_id: str | None = None


class HealthResponse(BaseModel):
    status: str
    app_name: str


class ConversationCreateRequest(BaseModel):
    title: str | None = None


class ConversationUpdateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=80)


class ConversationSummary(BaseModel):
    conversation_id: str
    title: str
    created_at: str | None = None
    updated_at: str | None = None
    message_count: int = 0


class ConversationMessage(BaseModel):
    timestamp: str
    role: str
    content: str
    metadata: dict = {}


class ConversationDetail(BaseModel):
    conversation_id: str
    title: str
    created_at: str | None = None
    updated_at: str | None = None
    messages: list[ConversationMessage] = []


class OperationStatus(BaseModel):
    status: str
