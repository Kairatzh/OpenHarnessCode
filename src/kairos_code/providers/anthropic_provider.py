"""Anthropic Claude provider."""

from __future__ import annotations

from typing import Any, AsyncIterator

from kairos_code.providers.base import (
    LLMProvider,
    LLMResponse,
    Message,
    MessageRole,
)


class AnthropicProvider(LLMProvider):
    """Provider for Anthropic Claude models."""

    provider_name = "anthropic"

    def __init__(self, api_key: str = "", base_url: str = "", **kwargs: Any) -> None:
        super().__init__(api_key=api_key, base_url=base_url, **kwargs)
        self._client = None

    def _get_client(self) -> Any:
        if self._client is None:
            try:
                from anthropic import AsyncAnthropic
            except ImportError:
                raise ImportError(
                    "anthropic package is required. Install with: pip install kairos-code[anthropic]"
                )
            kwargs: dict[str, Any] = {"api_key": self.api_key}
            if self.base_url:
                kwargs["base_url"] = self.base_url
            self._client = AsyncAnthropic(**kwargs)
        return self._client

    def _split_system_and_messages(
        self, messages: list[Message]
    ) -> tuple[str, list[dict[str, Any]]]:
        """Anthropic separates system instructions from user/assistant turns."""
        system_parts: list[str] = []
        formatted: list[dict[str, Any]] = []
        for msg in messages:
            if msg.role == MessageRole.SYSTEM:
                system_parts.append(msg.content)
            else:
                role = "user" if msg.role == MessageRole.USER else "assistant"
                formatted.append({"role": role, "content": msg.content})

        if not formatted:
            formatted.append({"role": "user", "content": "Hello"})

        return "\n\n".join(system_parts), formatted

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
        system, formatted = self._split_system_and_messages(messages)

        params: dict[str, Any] = {
            "model": model,
            "messages": formatted,
            "max_tokens": max_tokens or 4096,
            "temperature": temperature,
        }
        if system:
            params["system"] = system
        if tools:
            params["tools"] = self._convert_tools(tools)
        params.update(kwargs)

        response = await client.messages.create(**params)

        content_parts = []
        tool_calls_data = []
        for block in response.content:
            if block.type == "text":
                content_parts.append(block.text)
            elif block.type == "tool_use":
                tool_calls_data.append({
                    "id": block.id,
                    "type": "function",
                    "function": {
                        "name": block.name,
                        "arguments": str(block.input),
                    },
                })

        return LLMResponse(
            content="\n".join(content_parts),
            model=model,
            provider=self.provider_name,
            finish_reason=response.stop_reason or "end_turn",
            prompt_tokens=response.usage.input_tokens,
            completion_tokens=response.usage.output_tokens,
            total_tokens=response.usage.input_tokens + response.usage.output_tokens,
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
        system, formatted = self._split_system_and_messages(messages)

        params: dict[str, Any] = {
            "model": model,
            "messages": formatted,
            "max_tokens": max_tokens or 4096,
            "temperature": temperature,
        }
        if system:
            params["system"] = system
        params.update(kwargs)

        async with client.messages.stream(**params) as stream:
            async for text in stream.text_stream:
                yield text

    def _convert_tools(self, tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
        anthropic_tools = []
        for tool in tools:
            if tool.get("type") == "function":
                func = tool["function"]
                anthropic_tools.append({
                    "name": func["name"],
                    "description": func.get("description", ""),
                    "input_schema": func.get("parameters", {"type": "object", "properties": {}}),
                })
            else:
                anthropic_tools.append(tool)
        return anthropic_tools

    def get_available_models(self) -> list[str]:
        return [
            "claude-3-7-sonnet-20250219",
            "claude-3-5-sonnet-20241022",
            "claude-3-5-haiku-20241022",
        ]
