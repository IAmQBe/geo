from __future__ import annotations

from openai import AsyncOpenAI

from bot.config import get_settings


class OpenAIClient:
    def __init__(self) -> None:
        settings = get_settings()
        self.model = settings.openai_model
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)

    async def complete(self, prompt: str, temperature: float = 0.2) -> str:
        response = await self.client.responses.create(
            model=self.model,
            input=prompt,
            temperature=temperature,
        )
        return (response.output_text or "").strip()
