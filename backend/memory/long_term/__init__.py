"""
长期记忆子模块 —— 可编辑的记忆卡片。

职责：
- 卡片 CRUD（依赖 card_store 和 vector_store）
- 语义检索（向量召回 + 回填元数据）
- 审核流程（pending → active / rejected）
- 召回统计更新

与外部依赖：
- vector_stores: 向量相似度搜索
- relational: 卡片元数据存储
- models.provider: 获取 embedding 模型
"""

from memory.long_term.store import LongTermMemoryStore

__all__ = ["LongTermMemoryStore"]
