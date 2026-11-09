"""Base interfaces for LLM providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, AsyncIterator, Optional

from pydantic import BaseModel, Field


class MessageRole(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class Message(BaseModel):
    """A single message in a conversation."""
    role: MessageRole
    content: str
    name: Optional[str] = None
    tool_call_id: Optional[str] = None
    tool_calls: Optional[list[dict[str, Any]]] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class LLMResponse(BaseModel):
    """Response from an LLM provider."""
    content: str
    model: str = ""
    provider: str = ""
    finish_reason: str = "stop"
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    tool_calls: list[dict[str, Any]] = Field(default_factory=list)
    raw_response: Optional[dict[str, Any]] = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def has_tool_calls(self) -> bool:
        return len(self.tool_calls) > 0


class LLMProvider(ABC):
    """Abstract base class for LLM providers.
    
    Model-agnostic interface enabling agents to execute against
    OpenAI, Anthropic, Gemini, Ollama, or custom local backends.
    """

    provider_name: str = "base"

    def __init__(self, api_key: str = "", base_url: str = "", **kwargs: Any) -> None:
        self.api_key = api_key
        self.base_url = base_url
        self.extra_config = kwargs

    @abstractmethod
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
        """Send messages to the LLM and get a response."""
        ...

    @abstractmethod
    async def stream(
        self,
        messages: list[Message],
        model: str,
        temperature: float = 0.2,
        max_tokens: int | None = None,
        tools: list[dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """Stream a response from the LLM."""
        ...

    async def check_health(self) -> bool:
        """Check if the provider is reachable."""
        try:
            resp = await self.complete(
                messages=[Message(role=MessageRole.USER, content="ping")],
                model="default",
                max_tokens=5,
            )
            return bool(resp.content)
        except Exception:
            return False

    def get_available_models(self) -> list[str]:
        """Return list of commonly available models for this provider."""
        return []
