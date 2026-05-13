"""
记忆层。

本模块采用"结构化档案 + 短期滚动 + 长期卡片"三部分结构：

┌──────────────────────────────────────────────────────────┐
│ 用户档案 (Profile)                                       │
│   存储: 关系型数据库，JSON 列（一行一用户）              │
│   读取: ProfileProvider → 每轮全量注入 SP                │
│   写入: session_end 时由 LLM 统一提取更新                │
│   示例: {"nickname": "老板", "birthday": "5月3日"}       │
└──────────────────────────────────────────────────────────┘
┌──────────────────────────────────────────────────────────┐
│ 短期记忆 (Short-term)                                    │
│   存储: LangGraph State.messages（内存）                  │
│   策略: 轮次超过阈值 → Summarizer 摘要旧消息             │
│   读取: 摘要块自然存在于 messages 列表中，随对话流入 LLM  │
└──────────────────────────────────────────────────────────┘
┌──────────────────────────────────────────────────────────┐
│ 长期记忆 (Long-term) —— 可编辑的记忆卡片                 │
│   存储: 向量数据库（语义检索）+ 关系型数据库（元数据）   │
│   读取: MemoryProvider → Gate(引用词触发) → 改写 → 检索  │
│   写入: session_end 提取 + 去重合并                      │
│   审核: 新卡片 status=PENDING，用户审核后变 ACTIVE        │
└──────────────────────────────────────────────────────────┘

数据流：

    [读取侧 - route_input 遍历 Context Providers]
    ┌─────────────────────────────────────────────────┐
    │ ProfileProvider: get_profile() → 全量注入 SP    │
    │ MemoryProvider:                                 │
    │    ├─ RuleBasedGate: 含引用词才触发             │
    │    ├─ Gate 通过 → auxiliary 改写 query           │
    │    └─ 向量检索 top-K → 格式化 → 注入 SP        │
    └─────────────────────────────────────────────────┘

    [写入侧 - session_end]
    ┌─────────────────────────────────────────────────┐
    │ extractor: LLM 从对话中提取候选记忆 → 去重合并  │
    │ profile_updater: 从对话提取档案字段 → merge 更新 │
    └─────────────────────────────────────────────────┘

子模块：
- schema.py            : 核心数据结构 (MemoryCard 等)
- profile/             : 用户档案（JSON 列存储）
- short_term/          : 短期记忆管理 + 滚动摘要
- long_term/           : 长期记忆卡片 CRUD + 语义检索
- retrieval_gate.py    : 检索门控（引用词触发）
- extractor.py         : 记忆提取器（对话 → 候选卡片）
- manager.py           : 统一入口（对外暴露的唯一 API）
"""

from memory.schema import (
    MemoryCard,
    MemoryCardStatus,
    MemorySource,
    MemorySearchResult,
)
from memory.manager import MemoryManager

__all__ = [
    "MemoryCard",
    "MemoryCardStatus",
    "MemorySource",
    "MemorySearchResult",
    "MemoryManager",
]
