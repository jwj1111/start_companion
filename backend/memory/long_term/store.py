"""
长期记忆存储 —— 协调向量库 + 关系型库。

核心职责：
- 写入（去重合并）：新记忆和已有记忆比对相似度，相似则替换，不似则新增
- 读取：query → embedding → 向量检索 → 用 card_id 回填完整卡片
- 更新：同步更新两侧（如果文本变了要重新 embed）
- 删除：两侧同时删除

去重合并策略：
    对每条候选记忆：
    1. 生成 embedding
    2. 在已有记忆中搜索最相似的一条
    3. 相似度 >= merge_threshold → 替换（覆盖旧卡内容）
       相似度 < add_threshold → 新增（全新记忆）
       中间地带 → 按配置决定（默认新增）

用户隔离：所有操作强制带 user_id 过滤。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from loguru import logger

from memory.schema import (
    MemoryCard,
    MemoryCardStatus,
    MemorySearchResult,
)
from memory.vector_stores.base import BaseVectorStore
from memory.relational.base import BaseCardStore


@dataclass
class DeduplicationConfig:
    """去重合并策略的配置。"""

    # 相似度 >= 此值 → 认为是同一条记忆，用新内容替换旧卡
    merge_threshold: float = 0.85

    # 相似度 < 此值 → 认为是全新记忆，追加新卡
    add_threshold: float = 0.60

    # 中间地带（>= add_threshold 且 < merge_threshold）：直接跳过。
    # 宁可漏记也不重复。下次 session 用户再提及时会重新比对。


@dataclass
class UpsertResult:
    """单条记忆去重合并的执行结果。"""
    card_id: str
    action: str  # "added" / "merged" / "skipped"
    merged_with_id: str | None = None  # 如果是 merged，被替换的旧卡 ID
    similarity_score: float | None = None


class LongTermMemoryStore:
    """
    长期记忆存储。

    一个实例通常服务一个 (user_id, agent_id) 组合，
    上层 MemoryManager 在构造时绑定 user/agent，避免业务层误传。
    """

    def __init__(
        self,
        vector_store: BaseVectorStore,
        card_store: BaseCardStore,
        embedding_fn,  # async (text: str) -> list[float]
        dedup_config: DeduplicationConfig | None = None,
    ):
        self.vector_store = vector_store
        self.card_store = card_store
        self.embedding_fn = embedding_fn
        self.dedup = dedup_config or DeduplicationConfig()

    # ================================================================
    # 写入（去重合并）
    # ================================================================

    async def upsert_with_dedup(
        self,
        card: MemoryCard,
    ) -> UpsertResult:
        """
        核心写入方法 —— 带去重合并逻辑。

        流程：
        1. 对 card.content 生成 embedding
        2. 搜索已有记忆中最相似的一条（同 user_id + agent_id + status=active）
        3. 根据相似度决定：替换 / 新增 / 跳过
        4. 执行写入并返回结果
        """
        # TODO: 实现
        # 1. vector = await self.embedding_fn(card.content)
        #
        # 2. hits = await self.vector_store.search(
        #        vector=vector,
        #        limit=1,
        #        filters={
        #            "user_id": card.user_id,
        #            "agent_id": card.agent_id,
        #            "status": MemoryCardStatus.ACTIVE.value,
        #        },
        #    )
        #
        # 3. if hits and hits[0].score >= self.dedup.merge_threshold:
        #        # 替换：更新旧卡的 content + 重新 embed
        #        old_card_id = hits[0].payload["card_id"]
        #        await self.update_card(card.user_id, old_card_id, {"content": card.content})
        #        return UpsertResult(card_id=old_card_id, action="merged",
        #                           merged_with_id=old_card_id, similarity_score=hits[0].score)
        #
        #    elif not hits or hits[0].score < self.dedup.add_threshold:
        #        # 新增
        #        card_id = await self.add_card(card)
        #        return UpsertResult(card_id=card_id, action="added",
        #                           similarity_score=hits[0].score if hits else None)
        #
        #    else:
        #        # 中间地带 → 跳过
        #        return UpsertResult(card_id="", action="skipped",
        #                           similarity_score=hits[0].score)
        raise NotImplementedError

    async def batch_upsert_with_dedup(
        self,
        cards: list[MemoryCard],
    ) -> list[UpsertResult]:
        """
        批量去重合并写入。

        对每条候选记忆依次执行 upsert_with_dedup。
        注意：是串行的，因为前一条的写入可能影响后一条的去重判断。
        """
        results = []
        for card in cards:
            result = await self.upsert_with_dedup(card)
            results.append(result)
            logger.debug(
                f"去重合并: action={result.action}, score={result.similarity_score}, "
                f"card='{card.content[:30]}...'"
            )
        return results

    # ================================================================
    # 写入（无去重，直接新增）
    # ================================================================

    async def add_card(self, card: MemoryCard) -> str:
        """
        直接添加一张卡片（不做去重）。

        用途：用户手动添加 / 需要强制新增的场景。

        流程：
        1. 生成 embedding
        2. 写入向量库
        3. 写入关系库
        4. 返回 card_id
        """
        # TODO: 实现
        raise NotImplementedError

    # ================================================================
    # 读取
    # ================================================================

    async def search(
        self,
        user_id: str,
        agent_id: str,
        query: str,
        limit: int = 10,
        score_threshold: float = 0.5,
    ) -> list[MemorySearchResult]:
        """
        语义检索 —— 召回与 query 相关的卡片。

        过滤条件：
        - user_id（强制）
        - agent_id（强制）
        - status = ACTIVE（只召回生效中的）
        - score >= score_threshold
        """
        # TODO: 实现
        raise NotImplementedError

    async def get_card(self, user_id: str, card_id: str) -> MemoryCard | None:
        """按 ID 获取一张卡片。"""
        return await self.card_store.get(user_id, card_id)

    async def list_cards(
        self,
        user_id: str,
        agent_id: str | None = None,
        status: MemoryCardStatus | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[MemoryCard]:
        """列出用户的卡片（用于审核 / 管理 UI）。"""
        return await self.card_store.list_cards(
            user_id=user_id,
            agent_id=agent_id,
            status=status,
            limit=limit,
            offset=offset,
        )

    # ================================================================
    # 更新
    # ================================================================

    async def update_card(
        self,
        user_id: str,
        card_id: str,
        updates: dict[str, Any],
        mark_user_edited: bool = True,
    ) -> bool:
        """
        更新卡片内容。

        若 content 发生变化，需要重新 embed 并更新向量库。
        若只是改 status/tags，只更新关系库即可。
        """
        # TODO: 实现
        raise NotImplementedError

    async def change_status(
        self,
        user_id: str,
        card_id: str,
        new_status: MemoryCardStatus,
    ) -> bool:
        """变更卡片状态（审核通过 / 归档 / 拒绝）。"""
        # TODO: 调用 update_card
        raise NotImplementedError

    # ================================================================
    # 删除
    # ================================================================

    async def delete_card(self, user_id: str, card_id: str) -> bool:
        """彻底删除一张卡片（向量库 + 关系库同步）。"""
        # TODO: 实现两侧同步删除
        raise NotImplementedError
