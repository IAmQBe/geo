from __future__ import annotations

import json

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ai.llm_router import LLMRouter
from ai.prompts.search import search_prompt
from db.models import Place


class NaturalLanguageSearch:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.router = LLMRouter()

    async def search(self, city_id: int, city_name: str, query: str, limit: int = 20) -> list[Place]:
        prompt = search_prompt(query, city_name)
        llm_output = await self.router.route("nl_search", prompt, temperature=0.1)
        keywords = self._extract_keywords(llm_output, fallback=query)

        pattern_filters = [
            or_(
                Place.name.ilike(f"%{word}%"),
                Place.description.ilike(f"%{word}%"),
                Place.ai_description.ilike(f"%{word}%"),
                Place.address.ilike(f"%{word}%"),
            )
            for word in keywords
        ]

        query_stmt = select(Place).where(Place.city_id == city_id, Place.is_active.is_(True))
        for expr in pattern_filters:
            query_stmt = query_stmt.where(expr)

        query_stmt = query_stmt.order_by(Place.rating.desc().nullslast(), Place.id.asc()).limit(limit)
        return list((await self.session.execute(query_stmt)).scalars().all())

    def _extract_keywords(self, llm_output: str, fallback: str) -> list[str]:
        try:
            payload = json.loads(llm_output)
            words = payload.get("keywords")
            if isinstance(words, list):
                tokens = [str(word).strip() for word in words if str(word).strip()]
                if tokens:
                    return tokens[:6]
        except Exception:
            pass

        return [token for token in fallback.split() if token.strip()][:6]
