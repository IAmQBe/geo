from parser.types import ParsedPlace


class Extractor:
    def from_payload(self, payload: dict) -> ParsedPlace:
        return ParsedPlace(
            name=payload.get("name", ""),
            address=payload.get("address"),
            source_url=payload.get("source_url", ""),
            source_id=payload.get("source_id"),
            rating=payload.get("rating"),
            review_count=payload.get("review_count", 0),
            lat=payload.get("lat"),
            lon=payload.get("lon"),
            phone=payload.get("phone"),
            website=payload.get("website"),
            description=payload.get("description"),
            working_hours=payload.get("working_hours"),
            price_range=payload.get("price_range"),
            photos=list(payload.get("photos", [])),
            raw_payload=payload,
        )
