from __future__ import annotations

from collections.abc import Iterator

from openai import OpenAI

from .config import settings


def _client() -> OpenAI:
    return OpenAI(base_url=settings.openai_base_url, api_key=settings.openai_api_key or "local")


def generate_answer(prompt: str) -> str:
    if not settings.openai_base_url:
        return "[Mock response] Configure OPENAI_BASE_URL to enable real LLM responses."

    response = _client().chat.completions.create(
        model=settings.openai_model,
        temperature=settings.llm_temperature,
        max_tokens=settings.llm_max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content or ""


def generate_answer_stream(prompt: str) -> Iterator[str]:
    if not settings.openai_base_url:
        yield "[Mock response] Configure OPENAI_BASE_URL to enable real LLM responses."
        return

    stream = _client().chat.completions.create(
        model=settings.openai_model,
        temperature=settings.llm_temperature,
        max_tokens=settings.llm_max_tokens,
        messages=[{"role": "user", "content": prompt}],
        stream=True,
    )
    for chunk in stream:
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta


def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    if not settings.openai_base_url:
        raise RuntimeError("OPENAI_BASE_URL is required for embeddings.")

    response = _client().embeddings.create(
        model=settings.openai_embedding_model,
        input=texts,
    )
    return [list(item.embedding) for item in response.data]


def embed_query(text: str) -> list[float]:
    return embed_texts([text])[0]
