"""
记忆层的核心数据结构。

设计参考：
- KokoroMemo 的记忆卡片 + 收件箱审核机制

设计决策：
- 不设 importance 字段：LLM 打分不稳定且无实际用途，提取质量靠 prompt 约束
- 不设 category 字段：分类对检索无帮助（向量检索靠语义），对用户展示意义不大
- 保留 tags：自由标签比固定分类更灵活，用户可自行编辑
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class MemoryCardStatus(str, Enum):
    """记忆卡片的生命周期状态。"""

    PENDING = "pending"      # 待审核（LLM 刚提取出来）
    ACTIVE = "active"        # 生效中，会参与召回
    ARCHIVED = "archived"    # 已归档，不再参与召回但保留历史
    REJECTED = "rejected"    # 用户已拒绝（比 archive 更强的信号，不再自动提取相同内容）


class MemorySource(str, Enum):
    """记忆来源 —— 用于追溯与质量控制。"""

    LLM_EXTRACTED = "llm_extracted"     # 由 LLM 从对话中自动提取
    USER_MANUAL = "user_manual"         # 用户手动添加
    SYSTEM = "system"                   # 系统预置（如默认人设关联信息）
    IMPORTED = "imported"               # 从外部导入


@dataclass
class MemoryCard:
    """
    记忆卡片 —— 长期记忆的基本单位。

    存储策略：
    - 向量数据库：存 embedding + 关键 payload（用于语义检索 + 过滤）
    - 关系型数据库：存完整卡片元数据（用于 CRUD + 列表展示 + 审核流程）
    两者通过 `id` 字段关联。
    """

    # === 标识 ===
    id: str
    user_id: str                            # 归属用户，强隔离关键字段
    agent_id: str                           # 归属 Agent

    # === 内容 ===
    content: str                            # 记忆文本
    tags: list[str] = field(default_factory=list)  # 自由标签，便于用户管理

    # === 状态 ===
    status: MemoryCardStatus = MemoryCardStatus.PENDING

    # === 来源追溯 ===
    source: MemorySource = MemorySource.LLM_EXTRACTED
    source_session_id: str = ""             # 从哪个会话提取
    source_message_ids: list[str] = field(default_factory=list)

    # === 可编辑性 ===
    user_edited: bool = False               # 用户是否手动修改过内容
    editable: bool = True                   # 是否允许编辑（系统级条目可锁定）

    # === 时间 ===
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    last_recalled_at: datetime | None = None
    recall_count: int = 0                   # 被召回次数，用于热度排序与整合决策

    # === 失效机制（可选） ===
    expires_at: datetime | None = None      # None 表示永不过期

    # === 向量引用 ===
    vector_id: str = ""

    # === 自由扩展 ===
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_vector_payload(self) -> dict[str, Any]:
        """
        构造写入向量库的 payload。

        只包含检索时需要过滤的字段，其他完整信息在关系库里。
        """
        return {
            "card_id": self.id,
            "user_id": self.user_id,
            "agent_id": self.agent_id,
            "status": self.status.value,
            "tags": self.tags,
        }


@dataclass
class MemorySearchResult:
    """记忆检索结果。"""

    card: MemoryCard
    relevance_score: float                  # 语义相似度 0.0 - 1.0
