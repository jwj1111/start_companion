"""Qdrant 向量存储实现。"""

from typing import Any

from loguru import logger

from memory.vector_stores.base import BaseVectorStore, VectorSearchHit


class QdrantVectorStore(BaseVectorStore):
    """Qdrant 向量数据库后端。"""

    def __init__(self, collection_name: str, url: str, api_key: str = ""):
        super().__init__(collection_name)
        self.url = url
        self.api_key = api_key
        self._client = None

    async def _get_client(self):
        """懒初始化 Qdrant 客户端。"""
        if self._client is None:
            from qdrant_client import AsyncQdrantClient

            kwargs: dict[str, Any] = {"url": self.url}
            if self.api_key:
                kwargs["api_key"] = self.api_key
            self._client = AsyncQdrantClient(**kwargs)
        return self._client

    # === 生命周期 ===

    async def ensure_collection(self, vector_size: int) -> None:
        """确保 collection 存在。"""
        from qdrant_client.models import Distance, VectorParams

        client = await self._get_client()
        collections = await client.get_collections()
        existing = {c.name for c in collections.collections}

        if self.collection_name not in existing:
            await client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
            )
            logger.info(f"已创建 Qdrant collection: {self.collection_name}")

    async def drop_collection(self) -> None:
        client = await self._get_client()
        await client.delete_collection(self.collection_name)
        logger.warning(f"已删除 Qdrant collection: {self.collection_name}")

    # === 数据操作 ===

    async def upsert(
        self,
        id: str,
        vector: list[float],
        payload: dict[str, Any],
    ) -> None:
        from qdrant_client.models import PointStruct

        client = await self._get_client()
        await client.upsert(
            collection_name=self.collection_name,
            points=[PointStruct(id=id, vector=vector, payload=payload)],
        )

    async def batch_upsert(
        self,
        items: list[tuple[str, list[float], dict[str, Any]]],
    ) -> None:
        from qdrant_client.models import PointStruct

        client = await self._get_client()
        points = [PointStruct(id=i, vector=v, payload=p) for i, v, p in items]
        await client.upsert(collection_name=self.collection_name, points=points)

    async def search(
        self,
        vector: list[float],
        limit: int = 10,
        filters: dict[str, Any] | None = None,
        score_threshold: float | None = None,
    ) -> list[VectorSearchHit]:
        client = await self._get_client()
        query_filter = self._build_filter(filters) if filters else None

        results = await client.search(
            collection_name=self.collection_name,
            query_vector=vector,
            limit=limit,
            query_filter=query_filter,
            score_threshold=score_threshold,
        )

        return [
            VectorSearchHit(id=str(r.id), score=r.score, payload=r.payload or {})
            for r in results
        ]

    async def delete(self, id: str) -> None:
        from qdrant_client.models import PointIdsList

        client = await self._get_client()
        await client.delete(
            collection_name=self.collection_name,
            points_selector=PointIdsList(points=[id]),
        )

    async def delete_by_filter(self, filters: dict[str, Any]) -> int:
        from qdrant_client.models import FilterSelector

        client = await self._get_client()
        query_filter = self._build_filter(filters)
        result = await client.delete(
            collection_name=self.collection_name,
            points_selector=FilterSelector(filter=query_filter),
        )
        # Qdrant 的 delete 不直接返回删除数量，这里返回 0 由调用方自行查询
        return 0

    # === 内部工具 ===

    def _build_filter(self, filters: dict[str, Any]):
        """将通用过滤字典翻译为 Qdrant Filter 对象。"""
        from qdrant_client.models import Filter, FieldCondition, MatchValue, MatchAny

        conditions = []
        for key, value in filters.items():
            if isinstance(value, list):
                # 列表值 → MatchAny（任一命中即可）
                conditions.append(FieldCondition(key=key, match=MatchAny(any=value)))
            else:
                conditions.append(FieldCondition(key=key, match=MatchValue(value=value)))

        return Filter(must=conditions)
