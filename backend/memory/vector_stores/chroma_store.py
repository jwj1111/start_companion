"""Chroma 向量存储实现（占位，待实现）。"""

from typing import Any

from memory.vector_stores.base import BaseVectorStore, VectorSearchHit


class ChromaVectorStore(BaseVectorStore):
    """ChromaDB 向量数据库后端（适合本地开发）。"""

    def __init__(self, collection_name: str, persist_dir: str = "./data/chroma"):
        super().__init__(collection_name)
        self.persist_dir = persist_dir
        self._client = None
        self._collection = None

    async def ensure_collection(self, vector_size: int) -> None:
        # TODO: 使用 chromadb.PersistentClient 初始化
        raise NotImplementedError

    async def drop_collection(self) -> None:
        raise NotImplementedError

    async def upsert(self, id: str, vector: list[float], payload: dict[str, Any]) -> None:
        raise NotImplementedError

    async def batch_upsert(
        self, items: list[tuple[str, list[float], dict[str, Any]]]
    ) -> None:
        raise NotImplementedError

    async def search(
        self,
        vector: list[float],
        limit: int = 10,
        filters: dict[str, Any] | None = None,
        score_threshold: float | None = None,
    ) -> list[VectorSearchHit]:
        raise NotImplementedError

    async def delete(self, id: str) -> None:
        raise NotImplementedError

    async def delete_by_filter(self, filters: dict[str, Any]) -> int:
        raise NotImplementedError
