"""
向量存储实现层。

通过统一的 BaseVectorStore 接口支持多种向量数据库：
- qdrant: 生产推荐，元数据过滤强
- chroma: 开发用，简单轻量
- milvus: 大规模场景

一个实例绑定一个 collection，不同用途使用不同实例：
- 用户记忆:    collection="user_memories"
- 游戏知识库:  collection="game_knowledge"
- 对话片段:    collection="conversation_chunks"

使用工厂 `get_vector_store(collection_name)` 获取对应实例。
"""

from memory.vector_stores.base import BaseVectorStore, VectorSearchHit
from memory.vector_stores.factory import get_vector_store

__all__ = ["BaseVectorStore", "VectorSearchHit", "get_vector_store"]
