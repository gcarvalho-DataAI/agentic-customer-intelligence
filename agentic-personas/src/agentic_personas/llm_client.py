from __future__ import annotations

from openai import OpenAI


class OpenAICompatibleClient:
    def __init__(self, base_url: str, api_key: str, model: str, temperature: float = 0.2) -> None:
        self._client = OpenAI(base_url=base_url, api_key=api_key)
        self._model = model
        self._temperature = temperature

    def ask(self, system_prompt: str, user_message: str) -> str:
        response = self._client.chat.completions.create(
            model=self._model,
            temperature=self._temperature,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
        )
        return response.choices[0].message.content or ""

