"""
知识库检索器 —— 查询游戏知识库。

实现说明：
- 复用 memory.vector_stores 模块的向量存储抽象
- 使用独立的 collection（如 "game_knowledge"）与用户记忆隔离
- 不做用户隔离，因为游戏知识是全局共享的
"""

from dataclasses import dataclass
from typing import Any

from loguru import logger

from memory.vector_stores import get_vector_store
from models.provider import get_embedding_model


@dataclass
class KnowledgeChunk:
    """检索得到的知识片段。"""
    content: str
    source: str
    game_name: str
    relevance_score: float
    metadata: dict[str, Any]


class KnowledgeRetriever:
    """从向量存储中检索相关的游戏知识。"""

    def __init__(self, collection_name: str = "game_knowledge"):
        self.collection_name = collection_name
        self._vector_store = None
        self._embedding_model = None

    def _get_vector_store(self):
        if self._vector_store is None:
            self._vector_store = get_vector_store(self.collection_name)
        return self._vector_store

    def _get_embedding(self):
        if self._embedding_model is None:
            self._embedding_model = get_embedding_model()
        return self._embedding_model

    async def search(
        self,
        query: str,
        game_name: str | None = None,
        limit: int = 5,
        score_threshold: float = 0.5,
    ) -> list[KnowledgeChunk]:
        """
        搜索游戏知识库。

        参数：
            query: 自然语言查询
            game_name: 可选，按游戏过滤
            limit: 最多返回的条数
            score_threshold: 最低相关度阈值

        返回值：
            相关的知识片段列表
        """
        # TODO: 具体实现
        # 1. vector = await self._get_embedding().aembed_query(query)
        # 2. filters = {"game_name": game_name} if game_name else None
        # 3. hits = await self._get_vector_store().search(
        #        vector=vector, limit=limit, filters=filters,
        #        score_threshold=score_threshold
        #    )
        # 4. 把 hits 转为 KnowledgeChunk 返回
        logger.debug(f"知识库搜索: query='{query[:50]}...', game={game_name}")
        return []
