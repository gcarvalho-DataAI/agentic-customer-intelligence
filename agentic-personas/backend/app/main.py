from __future__ import annotations

import json
import logging
import re

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from .config import settings
from .answer_style import normalize_persona_answer
from .llm_client import generate_answer_stream
from .mongo_store import (
    append_message,
    clear_conversation_messages,
    create_conversation,
    delete_conversation,
    finalize_partial_assistant_message,
    get_conversation,
    get_recent_messages,
    list_conversations,
    start_partial_assistant_message,
    update_conversation_title,
    update_partial_assistant_message,
)
from .persona_agent import answer_as_persona, answer_with_multiple_personas
from .persona_loader import get_persona_by_id, load_personas
from .prompt_builder import build_persona_rag_prompt
from .retriever import retrieve_context
from .schemas import (
    ChatRequest,
    ChatResponse,
    ConversationCreateRequest,
    ConversationDetail,
    ConversationSummary,
    ConversationUpdateRequest,
    HealthResponse,
    OperationStatus,
    RetrievalTestRequest,
)

app = FastAPI(title=settings.app_name)
logger = logging.getLogger(__name__)


def _retrieved_doc_payload(ctx) -> dict:
    content_preview = (ctx.content or "").replace("\n", " ").strip()
    if len(content_preview) > 220:
        content_preview = f"{content_preview[:220]}..."
    return {
        "doc_id": ctx.doc_id,
        "persona_id": ctx.persona_id,
        "doc_type": ctx.doc_type,
        "confidence": ctx.confidence,
        "source_file": ctx.source_file,
        "content_preview": content_preview,
        "score": ctx.score,
    }


def _answer_signature(answer: str) -> str:
    text = re.sub(r"\s+", " ", answer.strip())
    if not text:
        return ""
    first_sentence = re.split(r"(?<=[.!?])\s+", text)[0].strip()
    words = first_sentence.split()
    return " ".join(words[:16])

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_origin_regex=settings.cors_allow_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get(f"{settings.api_prefix}/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", app_name=settings.app_name)


@app.get(f"{settings.api_prefix}/personas")
def personas():
    return load_personas()


@app.get(f"{settings.api_prefix}/personas/{{cluster_id}}")
def persona(cluster_id: int):
    try:
        return get_persona_by_id(cluster_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post(f"{settings.api_prefix}/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    if not request.persona_ids:
        raise HTTPException(status_code=400, detail="persona_ids cannot be empty")
    try:
        history_messages = (
            get_recent_messages(request.conversation_id, settings.recent_history_turns * 2)
            if request.conversation_id
            else []
        )
        response = answer_with_multiple_personas(
            question=request.question,
            persona_ids=request.persona_ids,
            include_context=request.include_context,
            history_messages=history_messages,
        )
        if request.conversation_id:
            if not get_conversation(request.conversation_id):
                raise HTTPException(status_code=404, detail="conversation_id not found")
            append_message(
                request.conversation_id,
                "user",
                request.question,
                metadata={"persona_ids": request.persona_ids},
            )
            for answer in response.answers:
                append_message(
                    request.conversation_id,
                    "assistant",
                    answer.answer,
                    metadata={
                        "cluster_id": answer.cluster_id,
                        "segment_name": answer.segment_name,
                        "retrieved_docs": [
                            _retrieved_doc_payload(ctx)
                            for ctx in answer.retrieved_context
                        ],
                    },
                )
            response.conversation_id = request.conversation_id
        return response
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"llm_unavailable: {exc}") from exc


@app.post(f"{settings.api_prefix}/retrieval/test")
def retrieval_test(request: RetrievalTestRequest):
    output = {}
    for persona_id in request.persona_ids:
        output[str(persona_id)] = retrieve_context(request.question, persona_id)
    return {"question": request.question, "results": output}


@app.post(f"{settings.api_prefix}/conversations", response_model=ConversationSummary)
def create_conversation_endpoint(request: ConversationCreateRequest):
    return create_conversation(title=request.title)


@app.get(f"{settings.api_prefix}/conversations", response_model=list[ConversationSummary])
def list_conversations_endpoint(limit: int = 50):
    return list_conversations(limit=limit)


@app.get(f"{settings.api_prefix}/conversations/{{conversation_id}}", response_model=ConversationDetail)
def get_conversation_endpoint(conversation_id: str):
    conversation = get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="conversation not found")
    return conversation


@app.patch(f"{settings.api_prefix}/conversations/{{conversation_id}}", response_model=OperationStatus)
def update_conversation_endpoint(conversation_id: str, request: ConversationUpdateRequest):
    if not update_conversation_title(conversation_id, request.title):
        raise HTTPException(status_code=404, detail="conversation not found")
    return OperationStatus(status="updated")


@app.delete(f"{settings.api_prefix}/conversations/{{conversation_id}}", response_model=OperationStatus)
def delete_conversation_endpoint(conversation_id: str):
    if not delete_conversation(conversation_id):
        raise HTTPException(status_code=404, detail="conversation not found")
    return OperationStatus(status="deleted")


@app.delete(
    f"{settings.api_prefix}/conversations/{{conversation_id}}/messages",
    response_model=OperationStatus,
)
def clear_conversation_messages_endpoint(conversation_id: str):
    if not clear_conversation_messages(conversation_id):
        raise HTTPException(status_code=404, detail="conversation not found")
    return OperationStatus(status="cleared")


@app.post(f"{settings.api_prefix}/chat/stream")
def chat_stream(request: ChatRequest):
    if not request.persona_ids:
        raise HTTPException(status_code=400, detail="persona_ids cannot be empty")

    conversation_id = request.conversation_id
    if conversation_id and not get_conversation(conversation_id):
        raise HTTPException(status_code=404, detail="conversation_id not found")

    def sse_event(event: str, payload: dict) -> str:
        return f"event: {event}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"

    def event_generator():
        user_persisted = False
        current_persona: dict | None = None
        current_answer_chunks: list[str] = []
        current_retrieved_docs: list[dict] = []
        current_message_id: str | None = None
        last_persisted_len = 0
        prior_answer_signatures: list[str] = []
        try:
            if conversation_id:
                append_message(
                    conversation_id,
                    "user",
                    request.question,
                    metadata={"persona_ids": request.persona_ids},
                )
                user_persisted = True

            for persona_id in request.persona_ids:
                history_messages = (
                    get_recent_messages(conversation_id, settings.recent_history_turns * 2)
                    if conversation_id
                    else []
                )
                answer = answer_as_persona(
                    question=request.question,
                    persona_id=persona_id,
                    include_context=request.include_context,
                    history_messages=history_messages,
                    prior_answer_signatures=prior_answer_signatures,
                )
                current_persona = {"cluster_id": answer.cluster_id, "segment_name": answer.segment_name}
                current_answer_chunks = []
                current_retrieved_docs = [_retrieved_doc_payload(ctx) for ctx in answer.retrieved_context]
                current_message_id = None
                last_persisted_len = 0

                yield sse_event(
                    "persona_start",
                    {
                        "cluster_id": answer.cluster_id,
                        "segment_name": answer.segment_name,
                    },
                )

                answer_text = answer.answer.strip()
                current_answer_chunks = [answer_text]
                yield sse_event(
                    "delta",
                    {
                        "cluster_id": answer.cluster_id,
                        "segment_name": answer.segment_name,
                        "text": answer_text,
                    },
                )
                signature = _answer_signature(answer_text)
                if signature:
                    prior_answer_signatures.append(signature)
                yield sse_event(
                    "persona_end",
                    {
                        "cluster_id": answer.cluster_id,
                        "segment_name": answer.segment_name,
                        "answer": answer_text,
                    },
                )
                if conversation_id and user_persisted:
                    append_message(
                        conversation_id,
                        "assistant",
                        answer_text,
                        metadata={
                            "cluster_id": answer.cluster_id,
                            "segment_name": answer.segment_name,
                            "retrieved_docs": current_retrieved_docs,
                        },
                    )
                current_persona = None
                current_answer_chunks = []
                current_retrieved_docs = []
                current_message_id = None
                last_persisted_len = 0

            yield sse_event(
                "done",
                {
                    "conversation_id": conversation_id,
                    "question": request.question,
                },
            )
        except KeyError as exc:
            yield sse_event("error", {"message": str(exc)})
        except Exception as exc:
            yield sse_event("error", {"message": f"stream_error: {exc}"})
        finally:
            if (
                conversation_id
                and user_persisted
                and current_persona
                and current_answer_chunks
                and current_message_id
            ):
                finalize_partial_assistant_message(
                    conversation_id=conversation_id,
                    message_id=current_message_id,
                    content="".join(current_answer_chunks).strip(),
                    partial=True,
                )

    return StreamingResponse(event_generator(), media_type="text/event-stream")
