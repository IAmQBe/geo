from __future__ import annotations

from typing import Any


def iter_dicts(payload: Any):
    if isinstance(payload, dict):
        yield payload
        for value in payload.values():
            yield from iter_dicts(value)
        return

    if isinstance(payload, list):
        for item in payload:
            yield from iter_dicts(item)


def iter_values(payload: Any):
    if isinstance(payload, dict):
        for value in payload.values():
            yield value
            yield from iter_values(value)
    elif isinstance(payload, list):
        for item in payload:
            yield item
            yield from iter_values(item)


def is_http_url(value: str) -> bool:
    lowered = value.lower()
    return lowered.startswith("http://") or lowered.startswith("https://")


def as_text(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, str):
        cleaned = " ".join(value.split()).strip()
        return cleaned or None
    return None


def to_float(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)

    if isinstance(value, str):
        candidate = value.strip().replace(",", ".")
        try:
            return float(candidate)
        except ValueError:
            return None
    return None


def to_int(value: Any) -> int | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)

    if isinstance(value, str):
        digits = "".join(ch for ch in value if ch.isdigit())
        if not digits:
            return None
        try:
            return int(digits)
        except ValueError:
            return None
    return None


def find_first(payload: Any, keys: set[str]) -> Any | None:
    for row in iter_dicts(payload):
        for key, value in row.items():
            if key.lower() in keys and value not in (None, "", [], {}):
                return value
    return None


def find_text(payload: Any, keys: set[str]) -> str | None:
    value = find_first(payload, keys)
    return as_text(value)


def find_float(payload: Any, keys: set[str]) -> float | None:
    value = find_first(payload, keys)
    return to_float(value)


def find_int(payload: Any, keys: set[str]) -> int | None:
    value = find_first(payload, keys)
    return to_int(value)


def find_coordinates(payload: Any) -> tuple[float | None, float | None]:
    lat = find_float(payload, {"lat", "latitude"})
    lon = find_float(payload, {"lon", "lng", "longitude"})
    if lat is not None and lon is not None and _valid_coords(lat, lon):
        return lat, lon

    for row in iter_dicts(payload):
        for key, value in row.items():
            lowered = key.lower()
            if not any(token in lowered for token in ("coord", "point", "position", "center", "geometry")):
                continue

            coords = _extract_from_value(value)
            if coords is not None:
                return coords

    return None, None


def _extract_from_value(value: Any) -> tuple[float, float] | None:
    if isinstance(value, dict):
        lat = find_float(value, {"lat", "latitude"})
        lon = find_float(value, {"lon", "lng", "longitude"})
        if lat is not None and lon is not None and _valid_coords(lat, lon):
            return lat, lon

        for nested in value.values():
            out = _extract_from_value(nested)
            if out is not None:
                return out
        return None

    if isinstance(value, list):
        if len(value) >= 2:
            first = to_float(value[0])
            second = to_float(value[1])
            if first is not None and second is not None:
                lon, lat = first, second
                if _valid_coords(lat, lon):
                    return lat, lon

                lat, lon = first, second
                if _valid_coords(lat, lon):
                    return lat, lon

        for item in value:
            out = _extract_from_value(item)
            if out is not None:
                return out

    return None


def _valid_coords(lat: float, lon: float) -> bool:
    return -90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0


def collect_urls(payload: Any, key_tokens: tuple[str, ...], limit: int = 20) -> list[str]:
    results: list[str] = []
    seen: set[str] = set()

    for row in iter_dicts(payload):
        for key, value in row.items():
            lowered = key.lower()
            if not any(token in lowered for token in key_tokens):
                continue

            if isinstance(value, str) and is_http_url(value):
                if value not in seen:
                    results.append(value)
                    seen.add(value)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, str) and is_http_url(item) and item not in seen:
                        results.append(item)
                        seen.add(item)
                    elif isinstance(item, dict):
                        for nested in item.values():
                            if isinstance(nested, str) and is_http_url(nested) and nested not in seen:
                                results.append(nested)
                                seen.add(nested)

            if len(results) >= limit:
                return results[:limit]

    return results[:limit]


def collect_phones(payload: Any, limit: int = 5) -> list[str]:
    values: list[str] = []
    seen: set[str] = set()
    for row in iter_dicts(payload):
        for key, value in row.items():
            lowered = key.lower()
            if "phone" not in lowered and "tel" not in lowered:
                continue

            if isinstance(value, str):
                phone = _sanitize_phone(value)
                if phone and phone not in seen:
                    values.append(phone)
                    seen.add(phone)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, str):
                        phone = _sanitize_phone(item)
                        if phone and phone not in seen:
                            values.append(phone)
                            seen.add(phone)
                    elif isinstance(item, dict):
                        for nested in item.values():
                            if isinstance(nested, str):
                                phone = _sanitize_phone(nested)
                                if phone and phone not in seen:
                                    values.append(phone)
                                    seen.add(phone)
            if len(values) >= limit:
                return values[:limit]

    return values[:limit]


def _sanitize_phone(raw: str) -> str | None:
    text = raw.strip()
    if not text:
        return None
    digits = "".join(ch for ch in text if ch.isdigit())
    if len(digits) < 6:
        return None
    return text


def pick_external_website(urls: list[str]) -> str | None:
    for url in urls:
        lowered = url.lower()
        if "2gis.ru" in lowered or "yandex." in lowered:
            continue
        return url
    return None


def maybe_price_range(payload: Any) -> str | None:
    raw = find_text(payload, {"price", "price_range", "pricing", "average_check", "avg_check"})
    if not raw:
        return None

    text = raw.lower()
    if "₽" in raw:
        return raw[:20]

    number = to_int(raw)
    if number is None:
        return raw[:20]

    if number < 700:
        return "₽"
    if number < 1600:
        return "₽₽"
    if number < 3000:
        return "₽₽₽"
    return "₽₽₽₽"
