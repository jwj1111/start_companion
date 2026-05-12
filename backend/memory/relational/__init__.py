"""
关系型存储层。

用于存放记忆卡片的结构化元数据。
与向量数据库配合：
- 向量库负责语义相似度检索
- 关系型库负责 CRUD、列表查询、状态管理、审核流程

当前实现基于 SQLite（aiosqlite），足以支撑单机中小规模。
后续可扩展为 PostgreSQL 等。
"""

from memory.relational.base import BaseCardStore
from memory.relational.factory import get_card_store

__all__ = ["BaseCardStore", "get_card_store"]
