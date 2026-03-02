from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from ai.llm_router import LLMRouter
from ai.prompts.description import description_prompt
from db.models import Place


class DescriptionGenerator:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.router = LLMRouter()

    async def generate_for_place(self, place: Place) -> str:
        prompt = description_prompt(place)
        response = await self.router.route("description_generation", prompt, temperature=0.4)
        return response.strip()
