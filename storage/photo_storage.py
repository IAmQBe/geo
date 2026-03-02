from __future__ import annotations

from storage.minio_client import MinioClient


class PhotoStorage:
    def __init__(self) -> None:
        self.minio = MinioClient()

    async def put_bytes(self, key: str, content: bytes, content_type: str = "image/jpeg") -> None:
        await self.minio.put_bytes(key=key, content=content, content_type=content_type)

    async def url(self, key: str) -> str:
        return await self.minio.presigned_get_url(key)
