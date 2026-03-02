from __future__ import annotations

from ai.ollama_client import OllamaClient
from ai.openai_client import OpenAIClient
from bot.config import get_settings


class LLMRouter:
    ROUTING_RULES = {
        "recommendations": "openai",
        "description_generation": "local",
        "nl_search": "openai",
        "trend_analysis": "openai",
        "simple_classification": "local",
    }

    def __init__(self) -> None:
        settings = get_settings()
        self.settings = settings
        self.openai_client = OpenAIClient() if settings.openai_api_key else None
        self.ollama_client = OllamaClient()

    async def route(self, task_type: str, prompt: str, temperature: float = 0.2) -> str:
        provider = self.ROUTING_RULES.get(task_type, "openai")

        if provider == "openai" and self.openai_client is not None:
            try:
                return await self.openai_client.complete(prompt, temperature=temperature)
            except Exception:
                return await self.ollama_client.complete(prompt, temperature=temperature)

        return await self.ollama_client.complete(prompt, temperature=temperature)
