"""
记忆层。

本模块采用"结构化档案 + 短期滚动 + 长期卡片"三部分结构：

┌──────────────────────────────────────────────────────────┐
│ 用户档案 (Profile)                                       │
│   存储: 关系型数据库（EAV 模式）                         │
│   读取: 每轮全量注入 System Prompt                       │
│   写入: session_end 时由 LLM 统一提取更新                │
│   示例: nickname="老板", birthday="5月3日"                │
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
│   读取: Gate → 条件改写 query → 向量检索 → 注入 SP       │
│   写入: session_end 提取 + 去重合并；对话中 tool 主动写入 │
│   审核: 新卡片 status=PENDING，用户审核后变 ACTIVE        │
└──────────────────────────────────────────────────────────┘

数据流：

    [读取侧 - route_input 节点]
    ┌─────────────────────────────────────────────────┐
    │ 1. Profile: get_profile_text() → 全量注入 SP    │
    │ 2. 短期: build_conversation_window() → 检查压缩 │
    │ 3. 长期: RuleBasedGate                          │
    │    ├─ 不搜 → recalled_text = None               │
    │    └─ 要搜:                                     │
    │       ├─ 含指代词 → LLM改写query                │
    │       └─ 不含 → 用原文                          │
    │       → 向量检索 top-5 → 格式化 → 注入 SP       │
    └─────────────────────────────────────────────────┘

    [写入侧 - process_output / session_end]
    ┌─────────────────────────────────────────────────┐
    │ 1. extractor: LLM 从对话中提取候选记忆          │
    │ 2. long_term: 去重合并后写入 (PENDING)          │
    │ 3. profile_updater: 从对话提取档案字段更新      │
    └─────────────────────────────────────────────────┘

    读取和写入完全隔离：
    - 读取只看 status=ACTIVE 的卡片
    - 写入新卡片默认 status=PENDING
    - 审核通过后才会被读取侧检索到

子模块：
- schema.py            : 核心数据结构 (MemoryCard 等)
- profile/             : 用户档案（结构化键值对）
- short_term/          : 短期记忆管理 + 滚动摘要
- long_term/           : 长期记忆卡片 CRUD + 语义检索
- retrieval_gate.py    : 检索门控（规则判断是否需要召回）
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
