"""Provider registry — manages LLM providers."""

from __future__ import annotations

from typing import Any, Type

from kairos_code.core.exceptions import ProviderError
from kairos_code.providers.base import LLMProvider


class ProviderRegistry:
    """Registry for managing LLM provider instances.
    
    Supports built-in providers (OpenAI, Anthropic, Gemini, Ollama)
    and external plugin providers.
    """

    _builtin_providers: dict[str, str] = {
        "openai": "kairos_code.providers.openai_provider:OpenAIProvider",
        "anthropic": "kairos_code.providers.anthropic_provider:AnthropicProvider",
        "gemini": "kairos_code.providers.gemini_provider:GeminiProvider",
        "google": "kairos_code.providers.gemini_provider:GeminiProvider",
        "ollama": "kairos_code.providers.ollama_provider:OllamaProvider",
        "local": "kairos_code.providers.ollama_provider:OllamaProvider",
    }

    def __init__(self) -> None:
        self._providers: dict[str, LLMProvider] = {}
        self._custom_classes: dict[str, Type[LLMProvider]] = {}

    def register_class(self, name: str, provider_class: Type[LLMProvider]) -> None:
        """Register a custom provider class."""
        self._custom_classes[name] = provider_class

    def _load_builtin(self, name: str) -> Type[LLMProvider]:
        """Dynamically import a built-in provider class."""
        if name not in self._builtin_providers:
            raise ProviderError(f"Unknown provider: {name}. Available: {list(self._builtin_providers.keys())}")
        
        module_path, class_name = self._builtin_providers[name].rsplit(":", 1)
        import importlib
        module = importlib.import_module(module_path)
        return getattr(module, class_name)

    def get(
        self,
        name: str,
        api_key: str = "",
        base_url: str = "",
        **kwargs: Any,
    ) -> LLMProvider:
        """Get or create a provider instance."""
        if name in self._providers:
            return self._providers[name]

        if name in self._custom_classes:
            cls = self._custom_classes[name]
        else:
            cls = self._load_builtin(name)

        provider = cls(api_key=api_key, base_url=base_url, **kwargs)
        self._providers[name] = provider
        return provider

    def configure_from_config(
        self,
        api_keys: dict[str, str],
        base_urls: dict[str, str] | None = None,
    ) -> None:
        """Pre-configure providers from harness config."""
        base_urls = base_urls or {}
        for name, key in api_keys.items():
            self.get(name, api_key=key, base_url=base_urls.get(name, ""))

    def list_available(self) -> list[str]:
        """List all available provider names."""
        names = set(self._builtin_providers.keys())
        names.update(self._custom_classes.keys())
        names.update(self._providers.keys())
        return sorted(names)
