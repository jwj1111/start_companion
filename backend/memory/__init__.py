"""
记忆层。

本模块采用"结构化档案 + 短期滚动 + 长期卡片"三部分结构：

┌──────────────────────────────────────────────────────────┐
│ 用户档案 (Profile / State Table)                          │
│   存储: 关系型数据库（EAV 模式）                         │
│   特点: 固定字段，覆盖更新，每轮全量注入 prompt           │
│   触发: 每轮对话后 LLM 判断是否有字段需更新              │
│   示例: nickname="老板", birthday="5月3日"                │
└──────────────────────────────────────────────────────────┘
┌──────────────────────────────────────────────────────────┐
│ 短期记忆 (Short-term)                                    │
│   存储: LangGraph State.messages（内存）                  │
│   策略: 轮次超过阈值 → Summarizer 摘要旧消息             │
└──────────────────────────────────────────────────────────┘
┌──────────────────────────────────────────────────────────┐
│ 长期记忆 (Long-term) —— 可编辑的记忆卡片                 │
│   存储: 向量数据库（语义）+ 关系型数据库（元数据）       │
│   特点: 自由追加，语义检索，按需注入                     │
│   触发: Retrieval Gate 决定是否检索；提取按策略触发       │
└──────────────────────────────────────────────────────────┘

子模块：
- schema.py            : 核心数据结构 (MemoryCard 等)
- profile/             : 用户档案（结构化键值对）
- short_term/          : 短期记忆管理 + 滚动摘要
- long_term/           : 长期记忆卡片 CRUD + 语义检索
- retrieval_gate.py    : 检索门控
- extractor.py         : 记忆提取器
- manager.py           : 统一入口
"""

from memory.schema import (
    MemoryCard,
    MemoryCardStatus,
    MemoryCategory,
    MemorySource,
    MemorySearchResult,
)
from memory.manager import MemoryManager

__all__ = [
    "MemoryCard",
    "MemoryCardStatus",
    "MemoryCategory",
    "MemorySource",
    "MemorySearchResult",
    "MemoryManager",
]
