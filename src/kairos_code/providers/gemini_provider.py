"""Google Gemini provider."""

from __future__ import annotations

from typing import Any, AsyncIterator

from kairos_code.providers.base import (
    LLMProvider,
    LLMResponse,
    Message,
    MessageRole,
)


class GeminiProvider(LLMProvider):
    """Provider for Google Gemini models."""

    provider_name = "gemini"

    def __init__(self, api_key: str = "", base_url: str = "", **kwargs: Any) -> None:
        super().__init__(api_key=api_key, base_url=base_url, **kwargs)
        self._client = None

    def _get_client(self) -> Any:
        if self._client is None:
            try:
                import google.generativeai as genai
            except ImportError:
                raise ImportError(
                    "google-generativeai package is required. "
                    "Install with: pip install kairos-code[google]"
                )
            genai.configure(api_key=self.api_key)
            self._client = genai
        return self._client

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
        genai = self._get_client()

        system_parts: list[str] = []
        history: list[dict[str, Any]] = []
        last_user_msg = ""

        for msg in messages:
            if msg.role == MessageRole.SYSTEM:
                system_parts.append(msg.content)
            elif msg.role == MessageRole.USER:
                last_user_msg = msg.content
                history.append({"role": "user", "parts": [msg.content]})
            elif msg.role == MessageRole.ASSISTANT:
                history.append({"role": "model", "parts": [msg.content]})

        gen_config = {"temperature": temperature}
        if max_tokens:
            gen_config["max_output_tokens"] = max_tokens

        gen_model = genai.GenerativeModel(
            model_name=model,
            system_instruction="\n\n".join(system_parts) if system_parts else None,
            generation_config=gen_config,
        )

        if len(history) > 1:
            chat = gen_model.start_chat(history=history[:-1])
            response = chat.send_message(last_user_msg)
        else:
            response = gen_model.generate_content(last_user_msg or "Hello")

        text = ""
        if response.parts:
            text = response.parts[0].text or ""

        usage_meta = getattr(response, "usage_metadata", None)
        prompt_tokens = getattr(usage_meta, "prompt_token_count", 0) or 0
        completion_tokens = getattr(usage_meta, "candidates_token_count", 0) or 0

        return LLMResponse(
            content=text,
            model=model,
            provider=self.provider_name,
            finish_reason="stop",
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
        genai = self._get_client()

        system_parts = []
        last_msg = ""
        for msg in messages:
            if msg.role == MessageRole.SYSTEM:
                system_parts.append(msg.content)
            elif msg.role == MessageRole.USER:
                last_msg = msg.content

        gen_config = {"temperature": temperature}
        if max_tokens:
            gen_config["max_output_tokens"] = max_tokens

        gen_model = genai.GenerativeModel(
            model_name=model,
            system_instruction="\n\n".join(system_parts) if system_parts else None,
            generation_config=gen_config,
        )

        response = gen_model.generate_content(last_msg, stream=True)
        for chunk in response:
            if chunk.text:
                yield chunk.text

    def get_available_models(self) -> list[str]:
        return [
            "gemini-2.5-pro",
            "gemini-2.5-flash",
            "gemini-2.0-flash",
            "gemini-1.5-pro",
        ]
