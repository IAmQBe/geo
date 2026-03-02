from __future__ import annotations

import hashlib
from urllib.parse import urlparse

import httpx

from storage.photo_storage import PhotoStorage


class PhotoDownloader:
    def __init__(self, storage: PhotoStorage) -> None:
        self.storage = storage

    async def download_and_store(self, urls: list[str], prefix: str) -> list[str]:
        stored_keys: list[str] = []
        async with httpx.AsyncClient(timeout=20) as client:
            for url in urls:
                try:
                    response = await client.get(url)
                    response.raise_for_status()
                except Exception:
                    continue

                key = self._build_key(prefix, url)
                await self.storage.put_bytes(key, response.content)
                stored_keys.append(key)
        return stored_keys

    def _build_key(self, prefix: str, url: str) -> str:
        parsed = urlparse(url)
        ext = ".jpg"
        if "." in parsed.path.rsplit("/", maxsplit=1)[-1]:
            ext = "." + parsed.path.rsplit(".", maxsplit=1)[-1][:5]
        digest = hashlib.sha1(url.encode("utf-8")).hexdigest()
        return f"{prefix}/{digest}{ext}"
