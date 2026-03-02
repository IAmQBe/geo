from parser.types import ParsedPlace


class Validator:
    def validate(self, place: ParsedPlace) -> bool:
        if not place.name.strip():
            return False
        if not place.source_url.strip():
            return False
        return True
