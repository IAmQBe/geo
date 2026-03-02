from parser.types import ParsedPlace


class Deduplicator:
    def deduplicate(self, places: list[ParsedPlace]) -> list[ParsedPlace]:
        seen: set[tuple[str, str | None]] = set()
        unique: list[ParsedPlace] = []
        for place in places:
            key = (place.name.strip().lower(), place.source_id)
            if key in seen:
                continue
            seen.add(key)
            unique.append(place)
        return unique
