"""
记忆管理器 —— 对外的统一入口。

职责：
- 组装 档案 / 短期 / 长期 / 门控 / 提取器 各子组件
- 绑定 (user_id, agent_id)，确保所有操作在用户隔离下进行
- 暴露给上层 (LangGraph 节点 / API) 的简洁接口

使用示例：
    manager = await MemoryManager.for_user(user_id="alice", agent_id="default")

    # 档案（每轮都用）
    profile_text = await manager.get_profile_text()
    await manager.update_profile(recent_messages)

    # 长期卡片（按需）
    if await manager.should_recall(user_message):
        memories = await manager.recall(user_message, limit=5)

    # 短期压缩
    new_window = await manager.maybe_compress(window)

    # 写入卡片
    await manager.extract_and_store(conversation)
"""

from __future__ import annotations

from langchain_core.messages import BaseMessage
from loguru import logger

from memory.schema import MemoryCard, MemorySearchResult
from memory.long_term.store import LongTermMemoryStore
from memory.short_term.summarizer import ShortTermSummarizer
from memory.short_term.window import ConversationWindow
from memory.retrieval_gate import BaseRetrievalGate, RuleBasedGate
from memory.extractor import MemoryExtractor
from memory.profile.base import BaseProfileStore
from memory.profile.updater import ProfileUpdater


class MemoryManager:
    """
    记忆管理器 —— 对外入口。

    绑定 (user_id, agent_id)，确保跨模块调用都带着同一对身份。
    """

    def __init__(
        self,
        user_id: str,
        agent_id: str,
        profile_store: BaseProfileStore,
        profile_updater: ProfileUpdater,
        long_term: LongTermMemoryStore,
        summarizer: ShortTermSummarizer,
        extractor: MemoryExtractor,
        retrieval_gate: BaseRetrievalGate | None = None,
    ):
        self.user_id = user_id
        self.agent_id = agent_id
        self.profile_store = profile_store
        self.profile_updater = profile_updater
        self.long_term = long_term
        self.summarizer = summarizer
        self.extractor = extractor
        self.retrieval_gate = retrieval_gate or RuleBasedGate()

    # ================================================================
    # 用户档案（结构化，每轮读取 / session_end 写入）
    # ================================================================

    async def get_profile_text(self) -> str:
        """获取当前用户档案，格式化为可注入 prompt 的文本（每轮调用）。"""
        return await self.profile_store.to_prompt_text(self.user_id, self.agent_id)

    async def update_profile_on_session_end(
        self, session_messages: list[BaseMessage]
    ) -> dict[str, str]:
        """
        session 结束时调用 —— 从整段对话中提取档案更新。

        返回值：实际更新了的字段字典（空 {} 表示无更新）
        """
        return await self.profile_updater.update_on_session_end(
            user_id=self.user_id,
            agent_id=self.agent_id,
            session_messages=session_messages,
        )

    # ================================================================
    # 长期记忆卡片：读取
    # ================================================================

    async def should_recall(self, user_message: str) -> bool:
        """判断本轮是否需要召回长期记忆。"""
        return await self.retrieval_gate.should_retrieve(user_message)

    async def recall(
        self,
        query: str,
        limit: int = 5,
        score_threshold: float = 0.5,
    ) -> list[MemorySearchResult]:
        """从长期记忆中召回相关卡片。"""
        return await self.long_term.search(
            user_id=self.user_id,
            agent_id=self.agent_id,
            query=query,
            limit=limit,
            score_threshold=score_threshold,
        )

    # ================================================================
    # 长期记忆卡片：写入
    # ================================================================

    async def extract_and_store(self, messages, session_id: str = "") -> list[str]:
        """
        从一批对话中提取候选记忆 → 逐条去重合并写入。

        去重逻辑：
        - 新记忆和已有记忆比对余弦相似度
        - 高于 merge_threshold → 替换旧卡（认为是同一条信息的更新）
        - 低于 add_threshold → 新增卡片（全新记忆）
        - 中间地带 → 按配置决定

        返回实际落库（新增或更新）的卡片 ID 列表。
        """
        from memory.long_term.store import UpsertResult

        cards = await self.extractor.extract(
            messages=messages,
            user_id=self.user_id,
            agent_id=self.agent_id,
            session_id=session_id,
        )
        if not cards:
            return []

        results = await self.long_term.batch_upsert_with_dedup(cards)
        return [r.card_id for r in results if r.action in ("added", "merged")]

    async def add_manual_card(self, card: MemoryCard) -> str:
        """用户手动添加一张卡片。"""
        assert card.user_id == self.user_id
        assert card.agent_id == self.agent_id
        return await self.long_term.add_card(card)

    # ================================================================
    # 短期记忆：摘要
    # ================================================================

    async def maybe_compress(self, window: ConversationWindow) -> ConversationWindow:
        """按轮次阈值判断是否压缩短期对话。"""
        return await self.summarizer.maybe_compress(window)

    # ================================================================
    # 工厂
    # ================================================================

    @classmethod
    async def for_user(
        cls,
        user_id: str,
        agent_id: str,
        agent_config: dict | None = None,
    ) -> "MemoryManager":
        """
        便捷工厂方法 —— 按当前配置与 (user, agent) 构造一个 Manager。

        具体组装逻辑在此处完成，业务层只需关注这一个入口。
        """
        # TODO: 组装流程
        # 1. profile_store = RelationalProfileStore(db_conn)
        #    await profile_store.init_schema()
        #    profile_updater = ProfileUpdater(profile_store, update_fn=...)
        # 2. vector_store = get_vector_store("user_memories")
        #    await vector_store.ensure_collection(vector_size=...)
        # 3. card_store = get_card_store()
        #    await card_store.init_schema()
        # 4. embedding_fn = lambda text: get_embedding_model().aembed_query(text)
        # 5. long_term = LongTermMemoryStore(vector_store, card_store, embedding_fn)
        # 6. summarize_fn = 基于 get_model("auxiliary") 的包装
        #    summarizer = ShortTermSummarizer(summarize_fn, turns_threshold=..., keep_recent_turns=...)
        # 7. extract_fn = 基于 get_model("auxiliary") 的包装（带提示词）
        #    extractor = MemoryExtractor(extract_fn)
        # 8. gate = RuleBasedGate() 或从 agent_config 读取
        # 9. return cls(user_id, agent_id, profile_store, profile_updater,
        #              long_term, summarizer, extractor, gate)
        logger.info(f"构造 MemoryManager: user={user_id}, agent={agent_id}")
        raise NotImplementedError
        #    await vector_store.ensure_collection(vector_size=...)
        # 2. card_store = get_card_store()
        #    await card_store.init_schema()
        # 3. embedding_fn = lambda text: get_embedding_model().aembed_query(text)
        # 4. long_term = LongTermMemoryStore(vector_store, card_store, embedding_fn)
        # 5. summarize_fn = 基于 get_model("auxiliary") 的包装
        #    summarizer = ShortTermSummarizer(summarize_fn, turns_threshold=..., keep_recent_turns=...)
        # 6. extract_fn = 基于 get_model("auxiliary") 的包装（带提示词）
        #    extractor = MemoryExtractor(extract_fn)
        # 7. gate = RuleBasedGate()  或从 agent_config 读取
        # 8. return cls(user_id, agent_id, long_term, summarizer, extractor, gate)
        logger.info(f"构造 MemoryManager: user={user_id}, agent={agent_id}")
        raise NotImplementedError
