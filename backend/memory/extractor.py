"""
记忆提取器 —— 从对话中抽取可记入长期的内容。

触发时机：
- 短期摘要触发时：对被压缩的那批消息做一次提取
- 会话结束时：对整个会话做一次提取
- 其他业务自定义时机

提取的记忆默认状态为 PENDING（待审），
等用户审核通过后才变 ACTIVE。

设计决策：
- 不让 LLM 打 importance 分（不稳定且无实际用途）
- 提取质量完全靠 prompt 约束（"只提取重要信息，不提取闲聊"）
"""

from __future__ import annotations

from dataclasses import dataclass, field

from langchain_core.messages import BaseMessage
from loguru import logger

from memory.schema import MemoryCard, MemoryCardStatus, MemorySource


@dataclass
class ExtractionCandidate:
    """LLM 提取出的一条候选记忆（尚未落库）。"""

    content: str
    tags: list[str] = field(default_factory=list)


class MemoryExtractor:
    """
    记忆提取器 —— 把对话送给 LLM，得到结构化的候选记忆列表。

    具体的 LLM 调用由 extract_fn 注入，本类只负责流程。
    """

    def __init__(
        self,
        extract_fn,  # async (messages: list[BaseMessage]) -> list[ExtractionCandidate]
    ):
        self.extract_fn = extract_fn

    async def extract(
        self,
        messages: list[BaseMessage],
        user_id: str,
        agent_id: str,
        session_id: str,
        source_message_ids: list[str] | None = None,
    ) -> list[MemoryCard]:
        """
        从一批消息中提取候选记忆并转为 MemoryCard（未落库）。

        流程：
        1. 调用 extract_fn 让 LLM 输出 ExtractionCandidate 列表
        2. 封装为 MemoryCard（status=PENDING, source=LLM_EXTRACTED）
        3. 调用方决定是否调 LongTermMemoryStore.add_card 落库
        """
        # TODO: 实现
        # 1. candidates = await self.extract_fn(messages)
        # 2. 为每个 candidate 生成 uuid，封装为 MemoryCard
        # 3. 返回 list[MemoryCard]
        logger.info(
            f"提取记忆候选: user={user_id}, agent={agent_id}, messages={len(messages)}"
        )
        raise NotImplementedError
