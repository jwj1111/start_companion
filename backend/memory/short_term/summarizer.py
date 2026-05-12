"""
短期摘要器 —— 按轮次触发的滚动摘要。

配置项（由 Agent config 传入）：
    short_term_window:
      turns_threshold: 20          # 超过此轮次触发压缩
      keep_recent_turns: 10        # 压缩后保留最近多少轮原样
      summarize_model_role: auxiliary   # 用哪个角色的模型来做摘要

触发策略：
    len(recent_messages) > turns_threshold
      → 取最早的 (total - keep_recent_turns) 条消息
      → 连同旧摘要块一起送给 LLM 做新摘要
      → 替换原内容为 [新摘要块] + [最近 keep_recent_turns 条]
"""

from __future__ import annotations

from typing import Any

from langchain_core.messages import BaseMessage, SystemMessage
from loguru import logger

from memory.short_term.window import ConversationWindow


# 摘要块的标记前缀，用于识别某条 message 是否是摘要而非真实对话
SUMMARY_BLOCK_PREFIX = "[HISTORY_SUMMARY]"


class ShortTermSummarizer:
    """
    按轮次触发的短期摘要器。

    用法：
        summarizer = ShortTermSummarizer(
            summarize_fn=my_llm_summarize,    # async (messages, prev_summary) -> str
            turns_threshold=20,
            keep_recent_turns=10,
        )

        new_window = await summarizer.maybe_compress(window)
    """

    def __init__(
        self,
        summarize_fn,  # async callable: (list[BaseMessage], str | None) -> str
        turns_threshold: int = 20,
        keep_recent_turns: int = 10,
    ):
        self.summarize_fn = summarize_fn
        self.turns_threshold = turns_threshold
        self.keep_recent_turns = keep_recent_turns

        if keep_recent_turns >= turns_threshold:
            raise ValueError("keep_recent_turns 必须小于 turns_threshold")

    # === 公开 API ===

    def should_compress(self, window: ConversationWindow) -> bool:
        """判断当前窗口是否需要触发压缩。"""
        return window.total_turns() > self.turns_threshold

    async def maybe_compress(self, window: ConversationWindow) -> ConversationWindow:
        """
        按需压缩 —— 若达到阈值则执行摘要，否则原样返回。
        """
        if not self.should_compress(window):
            return window
        return await self.compress(window)

    async def compress(self, window: ConversationWindow) -> ConversationWindow:
        """
        执行压缩：
        1. 将 prev_summary + [要被摘要的消息] 送给 LLM
        2. 得到新摘要文本
        3. 返回 [新摘要块] + [最近 keep_recent_turns 条]
        """
        # TODO: 实现
        # 1. 拆分：to_summarize = recent[:-keep_recent_turns], to_keep = recent[-keep_recent_turns:]
        # 2. prev_summary_text = extract_summary_text(window.summary_block) 或 None
        # 3. new_summary_text = await self.summarize_fn(to_summarize, prev_summary_text)
        # 4. new_summary_block = SystemMessage(content=f"{SUMMARY_BLOCK_PREFIX} {new_summary_text}")
        # 5. return ConversationWindow(summary_block=new_summary_block, recent_messages=to_keep)
        logger.info(
            f"触发短期摘要: 当前 {window.total_turns()} 轮 > 阈值 {self.turns_threshold}"
        )
        raise NotImplementedError

    # === 工具 ===

    @staticmethod
    def is_summary_block(msg: BaseMessage) -> bool:
        """判断一条消息是否是历史摘要块。"""
        if not isinstance(msg, SystemMessage):
            return False
        content = msg.content if isinstance(msg.content, str) else ""
        return content.startswith(SUMMARY_BLOCK_PREFIX)

    @staticmethod
    def extract_summary_text(msg: BaseMessage | None) -> str | None:
        """从摘要块中提取纯文本摘要。"""
        if msg is None:
            return None
        if not ShortTermSummarizer.is_summary_block(msg):
            return None
        content = msg.content if isinstance(msg.content, str) else ""
        return content.removeprefix(SUMMARY_BLOCK_PREFIX).strip()


def build_conversation_window(messages: list[BaseMessage]) -> ConversationWindow:
    """
    从一坨 messages 重建 ConversationWindow。

    规则：
    - 如果第一条是摘要块 → 它是 summary_block，其余是 recent
    - 否则整个都是 recent
    """
    if messages and ShortTermSummarizer.is_summary_block(messages[0]):
        return ConversationWindow(
            summary_block=messages[0],
            recent_messages=messages[1:],
        )
    return ConversationWindow(summary_block=None, recent_messages=list(messages))
