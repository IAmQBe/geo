from parser.types import ParsedPlace


class Normalizer:
    def normalize(self, place: ParsedPlace) -> ParsedPlace:
        place.name = " ".join(place.name.split())
        if place.address:
            place.address = " ".join(place.address.split())
        if place.website and not place.website.startswith(("http://", "https://")):
            place.website = f"https://{place.website}"
        return place
