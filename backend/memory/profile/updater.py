"""
档案更新器 —— session_end 时统一提取并更新档案字段。

设计决策：
- 对话进行中：不做任何档案操作，靠短期上下文自然传递
- 短期压缩时：摘要器会保留设定类信息（靠 prompt 引导）
- session_end：统一把整段对话送给 LLM，一次性提取可更新的字段

这样做的好处：
- 零中间开销（对话中不多调一次 LLM）
- 实现简单（只有一个触发点）
- 体验无损（短期窗口内模型本就能看到原始消息）

提示词示例（给 auxiliary 模型）：
    "根据以下完整对话，提取可以更新到用户档案的信息。
     只输出有明确依据的字段，不要猜测。无可更新则输出空 {}。
     输出格式: {"field_name": "value", ...}

     当前档案: {current_profile}
     完整对话: {session_messages}"
"""

from __future__ import annotations

from langchain_core.messages import BaseMessage
from loguru import logger

from memory.profile.base import BaseProfileStore


class ProfileUpdater:
    """
    档案更新器 —— 仅在 session_end 时触发。

    参数：
        profile_store: 档案存储实例
        extract_fn: async (messages, current_profile_text) -> dict[str, str]
                    由 LLM 实现，返回需要更新的字段字典
    """

    def __init__(
        self,
        profile_store: BaseProfileStore,
        extract_fn,  # async (list[BaseMessage], str) -> dict[str, str]
    ):
        self.profile_store = profile_store
        self.extract_fn = extract_fn

    async def update_on_session_end(
        self,
        user_id: str,
        agent_id: str,
        session_messages: list[BaseMessage],
    ) -> dict[str, str]:
        """
        session 结束时调用 —— 从整段对话中提取档案更新。

        流程：
        1. 获取当前档案文本（作为 LLM 的参考，避免重复提取已有信息）
        2. 调 extract_fn（LLM）从完整对话中提取字段
        3. 若有更新，写入 profile_store（覆盖旧值）
        4. 返回实际更新了哪些字段

        返回值：
            更新了的字段字典（空 {} 表示无更新）
        """
        # TODO: 实现
        # 1. current_text = await self.profile_store.to_prompt_text(user_id, agent_id)
        # 2. updates = await self.extract_fn(session_messages, current_text)
        # 3. if updates:
        #        await self.profile_store.set_fields(user_id, agent_id, updates, source="llm_extracted")
        #        logger.info(f"档案已更新: user={user_id}, fields={list(updates.keys())}")
        # 4. return updates
        logger.debug(f"session_end 档案提取: user={user_id}, agent={agent_id}")
        raise NotImplementedError
