from abc import ABC, abstractmethod

from parser.types import ParseContext, ParsedPlace


class BaseParser(ABC):
    source_name: str

    @abstractmethod
    async def parse(self, context: ParseContext) -> list[ParsedPlace]:
        """Load places from source and return normalized raw entities."""

    async def health_check(self) -> bool:
        return True
