from __future__ import annotations

import hashlib
import struct
from urllib.parse import urlparse

import httpx

from storage.photo_storage import PhotoStorage


class PhotoDownloader:
    def __init__(self, storage: PhotoStorage) -> None:
        self.storage = storage

    async def download_and_store(self, urls: list[str], prefix: str) -> list[tuple[str, str]]:
        stored: list[tuple[str, str]] = []
        async with httpx.AsyncClient(timeout=20) as client:
            for url in urls:
                try:
                    response = await client.get(url)
                    response.raise_for_status()
                except Exception:
                    continue

                if not self._is_usable_image(response):
                    continue

                key = self._build_key(prefix, url)
                await self.storage.put_bytes(key, response.content)
                stored.append((url, key))
        return stored

    def _build_key(self, prefix: str, url: str) -> str:
        parsed = urlparse(url)
        ext = ".jpg"
        if "." in parsed.path.rsplit("/", maxsplit=1)[-1]:
            ext = "." + parsed.path.rsplit(".", maxsplit=1)[-1][:5]
        digest = hashlib.sha1(url.encode("utf-8")).hexdigest()
        return f"{prefix}/{digest}{ext}"

    def _is_usable_image(self, response: httpx.Response) -> bool:
        content_type = (response.headers.get("content-type") or "").lower()
        if not content_type.startswith("image/"):
            return False

        payload = response.content
        if len(payload) < 8_000:
            return False

        dimensions = self._extract_dimensions(payload)
        if dimensions is None:
            return False
        width, height = dimensions
        if width < 320 or height < 200:
            return False

        ratio = width / max(height, 1)
        if ratio > 4.0 or ratio < 0.25:
            return False
        return True

    def _extract_dimensions(self, data: bytes) -> tuple[int, int] | None:
        if len(data) < 24:
            return None
        if data.startswith(b"\x89PNG\r\n\x1a\n"):
            try:
                width, height = struct.unpack(">II", data[16:24])
                return int(width), int(height)
            except Exception:
                return None
        if data.startswith(b"\xff\xd8"):
            return self._extract_jpeg_dimensions(data)
        if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
            return self._extract_webp_dimensions(data)
        return None

    def _extract_jpeg_dimensions(self, data: bytes) -> tuple[int, int] | None:
        idx = 2
        while idx + 9 < len(data):
            if data[idx] != 0xFF:
                idx += 1
                continue
            marker = data[idx + 1]
            if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                try:
                    height, width = struct.unpack(">HH", data[idx + 5 : idx + 9])
                    return int(width), int(height)
                except Exception:
                    return None
            if marker in (0xD8, 0xD9):
                idx += 2
                continue
            if idx + 4 > len(data):
                return None
            segment_len = struct.unpack(">H", data[idx + 2 : idx + 4])[0]
            if segment_len < 2:
                return None
            idx += 2 + segment_len
        return None

    def _extract_webp_dimensions(self, data: bytes) -> tuple[int, int] | None:
        if len(data) < 30:
            return None
        chunk = data[12:16]
        if chunk == b"VP8X" and len(data) >= 30:
            width = 1 + int.from_bytes(data[24:27], "little")
            height = 1 + int.from_bytes(data[27:30], "little")
            return width, height
        if chunk == b"VP8L" and len(data) >= 25:
            bits = int.from_bytes(data[21:25], "little")
            width = (bits & 0x3FFF) + 1
            height = ((bits >> 14) & 0x3FFF) + 1
            return width, height
        if chunk == b"VP8 " and len(data) >= 30:
            width = struct.unpack("<H", data[26:28])[0] & 0x3FFF
            height = struct.unpack("<H", data[28:30])[0] & 0x3FFF
            return int(width), int(height)
        return None
