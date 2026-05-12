"""
向量存储抽象基类。

设计要点：
1. 所有检索操作必须带 user_id（由上层强制传入），在存储层做最终校验
2. 支持按 collection 分隔不同用途的数据（记忆 vs 知识库）
3. 过滤条件统一为字典格式，由各实现类翻译为具体查询语法
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class VectorSearchHit:
    """向量检索的单条命中结果。"""

    id: str
    score: float
    payload: dict[str, Any]


class BaseVectorStore(ABC):
    """
    向量数据库后端的抽象基类。

    一个实例绑定一个 collection。
    不同用途（用户记忆 / 游戏知识库）应当使用不同的实例。
    """

    def __init__(self, collection_name: str):
        self.collection_name = collection_name

    # === 生命周期 ===

    @abstractmethod
    async def ensure_collection(self, vector_size: int) -> None:
        """确保 collection 已创建（若不存在则创建）。"""
        ...

    @abstractmethod
    async def drop_collection(self) -> None:
        """删除整个 collection（慎用，通常只在测试中使用）。"""
        ...

    # === 数据操作 ===

    @abstractmethod
    async def upsert(
        self,
        id: str,
        vector: list[float],
        payload: dict[str, Any],
    ) -> None:
        """插入或更新一条向量。payload 必须包含 user_id。"""
        ...

    @abstractmethod
    async def batch_upsert(
        self,
        items: list[tuple[str, list[float], dict[str, Any]]],
    ) -> None:
        """批量插入或更新。"""
        ...

    @abstractmethod
    async def search(
        self,
        vector: list[float],
        limit: int = 10,
        filters: dict[str, Any] | None = None,
        score_threshold: float | None = None,
    ) -> list[VectorSearchHit]:
        """
        按向量相似度搜索。

        参数：
            vector: 查询向量
            limit: 返回条数上限
            filters: 按 payload 字段过滤，形如
                     {"user_id": "xxx", "agent_id": "yyy", "status": "active"}
            score_threshold: 相似度阈值，低于此值的不返回

        重要：调用方必须传入 user_id 过滤条件，上层会校验。
        """
        ...

    @abstractmethod
    async def delete(self, id: str) -> None:
        """按 id 删除一条向量。"""
        ...

    @abstractmethod
    async def delete_by_filter(self, filters: dict[str, Any]) -> int:
        """按过滤条件批量删除，返回删除条数。"""
        ...
