"""Local-first Ollama & local HTTP provider for offline / self-hosted models."""

from __future__ import annotations

import json
from typing import Any, AsyncIterator

import httpx

from kairos_code.providers.base import (
    LLMProvider,
    LLMResponse,
    Message,
    MessageRole,
)


class OllamaProvider(LLMProvider):
    """Provider for local Ollama instances (offline, local-first)."""

    provider_name = "ollama"

    def __init__(self, api_key: str = "", base_url: str = "http://localhost:11434", **kwargs: Any) -> None:
        super().__init__(api_key=api_key, base_url=base_url or "http://localhost:11434", **kwargs)

    async def complete(
        self,
        messages: list[Message],
        model: str,
        temperature: float = 0.2,
        max_tokens: int | None = None,
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str | None = None,
        response_format: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        url = f"{self.base_url.rstrip('/')}/api/chat"
        formatted_messages = [
            {"role": m.role.value, "content": m.content}
            for m in messages
        ]

        payload: dict[str, Any] = {
            "model": model,
            "messages": formatted_messages,
            "stream": False,
            "options": {
                "temperature": temperature,
            },
        }
        if max_tokens:
            payload["options"]["num_predict"] = max_tokens

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        async with httpx.AsyncClient(timeout=180.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()

        content = data.get("message", {}).get("content", "")
        prompt_tokens = data.get("prompt_eval_count", 0)
        completion_tokens = data.get("eval_count", 0)

        return LLMResponse(
            content=content,
            model=model,
            provider=self.provider_name,
            finish_reason=data.get("done_reason", "stop"),
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
        )

    async def stream(
        self,
        messages: list[Message],
        model: str,
        temperature: float = 0.2,
        max_tokens: int | None = None,
        tools: list[dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        url = f"{self.base_url.rstrip('/')}/api/chat"
        formatted_messages = [
            {"role": m.role.value, "content": m.content}
            for m in messages
        ]

        payload = {
            "model": model,
            "messages": formatted_messages,
            "stream": True,
            "options": {"temperature": temperature},
        }

        async with httpx.AsyncClient(timeout=180.0) as client:
            async with client.stream("POST", url, json=payload) as response:
                async for line in response.aiter_lines():
                    if line:
                        chunk = json.loads(line)
                        if "message" in chunk and "content" in chunk["message"]:
                            yield chunk["message"]["content"]

    def get_available_models(self) -> list[str]:
        return [
            "qwen2.5-coder:7b",
            "qwen2.5-coder:14b",
            "qwen2.5-coder:32b",
            "llama3.3:70b",
            "deepseek-r1:14b",
            "codellama:13b",
        ]
