"""
记忆管理器 —— 对外的统一入口。

职责：
- 组装 档案 / 短期 / 长期 / 门控 / 提取器 各子组件
- 绑定 (user_id, agent_id)，确保所有操作在用户隔离下进行
- 暴露给上层 (Context Provider / API) 的简洁接口

长期记忆读取路径（由 MemoryProvider 调用）：
    1. Gate 判断本轮是否需要检索 → should_recall()
    2. Gate 通过 → 一律改写 query → rewrite_query()
    3. 向量检索 top-K → recall()
    4. 结果由 MemoryProvider 格式化后注入 SP

长期记忆写入路径：
    - session_end 时：extract_and_store() 批量提取 + 去重合并
    - 对话中 tool：memory_write_tool → add_manual_card()

使用示例：
    manager = await MemoryManager.for_user(user_id="alice", agent_id="default")

    # 读取侧（MemoryProvider 中）
    profile_text = await manager.get_profile_text()
    if await manager.should_recall(user_message):
        query = await manager.rewrite_query(user_message, recent_messages)
        memories = await manager.recall(query, limit=5)

    # 写入侧（session_end / process_output 中）
    await manager.extract_and_store(conversation, session_id=sid)
    await manager.update_profile_on_session_end(session_messages)
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
        rewrite_fn=None,  # async (user_msg: str, context: list[BaseMessage]) -> str
    ):
        self.user_id = user_id
        self.agent_id = agent_id
        self.profile_store = profile_store
        self.profile_updater = profile_updater
        self.long_term = long_term
        self.summarizer = summarizer
        self.extractor = extractor
        self.retrieval_gate = retrieval_gate or RuleBasedGate()
        self.rewrite_fn = rewrite_fn  # 由 auxiliary 模型提供

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
    # 长期记忆卡片：读取（Gate → 改写 → 检索）
    # ================================================================

    async def should_recall(self, user_message: str) -> bool:
        """
        Gate 判断：本轮是否需要召回长期记忆。

        零延迟（纯规则匹配），由 RuleBasedGate 实现。
        """
        return await self.retrieval_gate.should_retrieve(user_message)

    async def rewrite_query(
        self,
        user_message: str,
        recent_messages: list[BaseMessage] | None = None,
    ) -> str:
        """
        改写 query —— 用 auxiliary 模型将用户消息改写为适合向量检索的 query。

        Gate 通过后一律调用此方法（不判断有没有指代词）。
        理由：即使没有指代词，改写也能去除噪声词、提取关键语义，提升检索质量。

        降级容错：如果 rewrite_fn 未配置，退化为直接使用原文。

        Args:
            user_message: 用户当前消息
            recent_messages: 最近几轮对话（提供上下文帮助改写），建议传 3-6 轮

        Returns:
            适合向量检索的 query 文本
        """
        if self.rewrite_fn is None:
            logger.debug("rewrite_fn 未配置，使用原文作为检索 query")
            return user_message

        context = recent_messages or []
        rewritten = await self.rewrite_fn(user_message, context)
        logger.debug(f"Query 改写: '{user_message}' → '{rewritten}'")
        return rewritten

    async def recall(
        self,
        query: str,
        limit: int = 5,
        score_threshold: float = 0.5,
    ) -> list[MemorySearchResult]:
        """从长期记忆中召回相关卡片（只检索 status=ACTIVE 的）。"""
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
        - 相似度 >= merge_threshold → 替换旧卡
        - 相似度 < add_threshold → 新增卡片
        - 中间地带 → 跳过（宁可漏记不重复）

        返回实际落库（新增或更新）的卡片 ID 列表。
        """
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
        """用户手动添加 / tool 主动写入一张卡片（不做去重）。"""
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

        组装流程：
        1. 创建 profile_store + profile_updater
        2. 创建 vector_store + card_store → LongTermMemoryStore
        3. 创建 summarizer（带 summarize_fn）
        4. 创建 extractor（带 extract_fn）
        5. 创建 retrieval_gate
        6. 创建 rewrite_fn（基于 auxiliary 模型）
        7. 组装并返回 MemoryManager 实例
        """
        # TODO: 实现完整组装
        # 1. profile_store = RelationalProfileStore(db_conn)
        #    await profile_store.init_schema()
        #    profile_updater = ProfileUpdater(profile_store, update_fn=...)
        #
        # 2. vector_store = get_vector_store("user_memories")
        #    await vector_store.ensure_collection(vector_size=...)
        #    card_store = get_card_store()
        #    await card_store.init_schema()
        #    embedding_fn = lambda text: get_embedding_model().aembed_query(text)
        #    long_term = LongTermMemoryStore(vector_store, card_store, embedding_fn)
        #
        # 3. summarize_fn = 基于 get_model("auxiliary") 的包装
        #    summarizer = ShortTermSummarizer(summarize_fn, turns_threshold=20, keep_recent_turns=10)
        #
        # 4. extract_fn = 基于 get_model("auxiliary") 的包装（带提示词）
        #    extractor = MemoryExtractor(extract_fn)
        #
        # 5. gate = RuleBasedGate()  # 或从 agent_config 读取参数
        #
        # 6. rewrite_fn = 基于 get_model("auxiliary") 的改写函数
        #    async def rewrite_fn(user_msg, context):
        #        prompt = f"将以下用户消息改写为适合向量检索的查询...\n{user_msg}"
        #        return await auxiliary_model.ainvoke(prompt)
        #
        # 7. return cls(user_id, agent_id, profile_store, profile_updater,
        #              long_term, summarizer, extractor, gate, rewrite_fn)
        logger.info(f"构造 MemoryManager: user={user_id}, agent={agent_id}")
        raise NotImplementedError
