"""OpenAI and OpenAI-compatible API provider."""

from __future__ import annotations

import json
from typing import Any, AsyncIterator

from kairos_code.providers.base import (
    LLMProvider,
    LLMResponse,
    Message,
    MessageRole,
)


class OpenAIProvider(LLMProvider):
    """Provider for OpenAI-compatible APIs (OpenAI, vLLM, LM Studio, etc.)."""

    provider_name = "openai"

    def __init__(self, api_key: str = "", base_url: str = "", **kwargs: Any) -> None:
        super().__init__(api_key=api_key, base_url=base_url, **kwargs)
        self._client = None

    def _get_client(self) -> Any:
        if self._client is None:
            try:
                from openai import AsyncOpenAI
            except ImportError:
                raise ImportError(
                    "openai package is required. Install with: pip install kairos-code[openai]"
                )
            kwargs: dict[str, Any] = {"api_key": self.api_key or "sk-dummy"}
            if self.base_url:
                kwargs["base_url"] = self.base_url
            self._client = AsyncOpenAI(**kwargs)
        return self._client

    def _format_messages(self, messages: list[Message]) -> list[dict[str, Any]]:
        formatted = []
        for msg in messages:
            d: dict[str, Any] = {
                "role": msg.role.value,
                "content": msg.content,
            }
            if msg.name:
                d["name"] = msg.name
            if msg.tool_call_id:
                d["tool_call_id"] = msg.tool_call_id
            if msg.tool_calls:
                d["tool_calls"] = msg.tool_calls
            formatted.append(d)
        return formatted

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
        client = self._get_client()
        params: dict[str, Any] = {
            "model": model,
            "messages": self._format_messages(messages),
            "temperature": temperature,
        }
        if max_tokens is not None:
            params["max_tokens"] = max_tokens
        if tools:
            params["tools"] = tools
        if tool_choice:
            params["tool_choice"] = tool_choice
        if response_format:
            params["response_format"] = response_format
        params.update(kwargs)

        response = await client.chat.completions.create(**params)

        choice = response.choices[0]
        tool_calls_data = []
        if choice.message.tool_calls:
            for tc in choice.message.tool_calls:
                tool_calls_data.append({
                    "id": tc.id,
                    "type": tc.type,
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                })

        usage = response.usage
        return LLMResponse(
            content=choice.message.content or "",
            model=response.model,
            provider=self.provider_name,
            finish_reason=choice.finish_reason or "stop",
            prompt_tokens=usage.prompt_tokens if usage else 0,
            completion_tokens=usage.completion_tokens if usage else 0,
            total_tokens=usage.total_tokens if usage else 0,
            tool_calls=tool_calls_data,
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
        client = self._get_client()
        params: dict[str, Any] = {
            "model": model,
            "messages": self._format_messages(messages),
            "temperature": temperature,
            "stream": True,
        }
        if max_tokens is not None:
            params["max_tokens"] = max_tokens
        if tools:
            params["tools"] = tools
        params.update(kwargs)

        stream = await client.chat.completions.create(**params)
        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    def get_available_models(self) -> list[str]:
        return [
            "gpt-4o",
            "gpt-4o-mini",
            "o1",
            "o1-mini",
            "o3-mini",
        ]
