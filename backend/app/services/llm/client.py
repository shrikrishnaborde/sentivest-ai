"""Chat-completion LLM client abstraction, mirroring the embedding provider
pattern: the rest of the app depends on `LLMClient`, not on any one SDK.
"""
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from app.core.config import get_settings


@dataclass
class LLMGeneration:
    summary: str
    positive_drivers: list[str] = field(default_factory=list)
    negative_drivers: list[str] = field(default_factory=list)
    key_themes: list[str] = field(default_factory=list)
    model: str = ""


class LLMClient(ABC):
    @abstractmethod
    async def generate_structured(self, system_prompt: str, user_prompt: str) -> LLMGeneration: ...


class OpenAILLMClient(LLMClient):
    def __init__(self, model: str | None = None, api_key: str | None = None):
        from openai import AsyncOpenAI

        settings = get_settings()
        self._model = model or settings.OPENAI_CHAT_MODEL
        self._client = AsyncOpenAI(api_key=api_key or settings.OPENAI_API_KEY)

    async def generate_structured(self, system_prompt: str, user_prompt: str) -> LLMGeneration:
        # Newer reasoning-tier models (e.g. gpt-5.5) reject a non-default
        # temperature outright, so we don't set one — let the model use its
        # default rather than trying to guess which models allow overriding it.
        response = await self._client.chat.completions.create(
            model=self._model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        payload = json.loads(response.choices[0].message.content)
        return LLMGeneration(
            summary=payload.get("summary", ""),
            positive_drivers=payload.get("positive_drivers", []),
            negative_drivers=payload.get("negative_drivers", []),
            key_themes=payload.get("key_themes", []),
            model=self._model,
        )


class AnthropicLLMClient(LLMClient):
    def __init__(self, model: str = "claude-sonnet-5", api_key: str | None = None):
        from anthropic import AsyncAnthropic

        settings = get_settings()
        self._model = model
        self._client = AsyncAnthropic(api_key=api_key or settings.ANTHROPIC_API_KEY)

    async def generate_structured(self, system_prompt: str, user_prompt: str) -> LLMGeneration:
        response = await self._client.messages.create(
            model=self._model,
            max_tokens=1024,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        text = response.content[0].text
        payload = json.loads(text)
        return LLMGeneration(
            summary=payload.get("summary", ""),
            positive_drivers=payload.get("positive_drivers", []),
            negative_drivers=payload.get("negative_drivers", []),
            key_themes=payload.get("key_themes", []),
            model=self._model,
        )


_client: LLMClient | None = None


def get_llm_client() -> LLMClient:
    global _client
    if _client is not None:
        return _client

    settings = get_settings()
    if settings.LLM_PROVIDER in ("openai", "azure_openai"):
        _client = OpenAILLMClient()
    elif settings.LLM_PROVIDER == "anthropic":
        _client = AnthropicLLMClient()
    else:
        raise ValueError(f"Unsupported LLM_PROVIDER: {settings.LLM_PROVIDER}")
    return _client
