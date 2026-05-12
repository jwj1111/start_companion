"""
向量存储工厂 —— 按配置返回对应的向量库实现。

用法：
    store = get_vector_store("user_memories")   # 用户记忆
    store = get_vector_store("game_knowledge")  # 知识库

具体使用 Qdrant / Chroma / Milvus 由配置文件决定。
"""

from loguru import logger

from memory.vector_stores.base import BaseVectorStore
from app.config.settings import get_settings


def get_vector_store(collection_name: str) -> BaseVectorStore:
    """
    按配置获取向量存储实例。

    参数：
        collection_name: 逻辑 collection 名（记忆 / 知识库 等）

    返回值：
        BaseVectorStore 实例
    """
    settings = get_settings()
    provider = settings.vector_db_type

    logger.debug(f"创建向量存储: provider={provider}, collection={collection_name}")

    if provider == "qdrant":
        from memory.vector_stores.qdrant_store import QdrantVectorStore

        return QdrantVectorStore(
            collection_name=collection_name,
            url=settings.vector_db_url,
            api_key=settings.vector_db_api_key,
        )

    elif provider == "chroma":
        from memory.vector_stores.chroma_store import ChromaVectorStore

        return ChromaVectorStore(
            collection_name=collection_name,
            persist_dir=settings.vector_db_url,  # chroma 用本地路径
        )

    elif provider == "milvus":
        from memory.vector_stores.milvus_store import MilvusVectorStore

        return MilvusVectorStore(
            collection_name=collection_name,
            url=settings.vector_db_url,
            api_key=settings.vector_db_api_key,
        )

    else:
        raise ValueError(f"未知的向量库类型: {provider}")
