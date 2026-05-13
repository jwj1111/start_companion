"""
MemoryProvider —— 提供从长期记忆中召回的相关卡片。

属于 DYNAMIC 组：每轮根据 Gate 判断是否检索，结果每轮可能不同。

读取流程：
1. Gate 判断（RuleBasedGate，零延迟规则匹配）
2. 条件改写 query（含指代词时用 auxiliary 模型改写，否则用原文）
3. 向量检索 top-K
4. 格式化为文本

与写入侧完全隔离：
- 这里只检索 status=ACTIVE 的卡片
- 写入侧的新卡片是 PENDING，不会被检索到
"""

from __future__ import annotations

from typing import Any

from langchain_core.messages import BaseMessage, HumanMessage
from loguru import logger

from context_providers.base import BaseContextProvider, ProviderGroup
from memory.retrieval_gate import RuleBasedGate


class MemoryProvider(BaseContextProvider):
    """
    长期记忆上下文提供者。

    内部自带 Gate，should_run() 中完成 Gate 判断。
    """

    name = "memory"
    group = ProviderGroup.DYNAMIC

    def __init__(self, agent_config: dict[str, Any]):
        super().__init__(agent_config)
        self._gate = RuleBasedGate(
            min_chars=agent_config.get("memory", {}).get("gate_min_chars", 4),
            default_retrieve=agent_config.get("memory", {}).get("gate_default_retrieve", True),
        )

    async def should_run(self, state: dict[str, Any]) -> bool:
        """
        通过 Gate 判断本轮是否需要检索长期记忆。

        零延迟（纯规则匹配）：
        - 短消息/问候 → False
        - 含引用词 → True
        - 其余 → 默认 True
        """
        last_msg = self._extract_last_user_message(state.get("messages", []))
        if not last_msg:
            return False
        return await self._gate.should_retrieve(last_msg)

    async def run(self, state: dict[str, Any]) -> str | None:
        """
        执行长期记忆检索：条件改写 query → 向量检索 → 格式化。

        返回格式化后的记忆文本，或 None（无相关记忆时）。
        """
        # TODO: 实现 —— 对接 MemoryManager
        # from memory.manager import MemoryManager
        #
        # user_id = state["user_id"]
        # agent_id = state["agent_id"]
        # manager = await MemoryManager.for_user(user_id, agent_id, self.agent_config)
        #
        # # 条件改写 query
        # last_msg = self._extract_last_user_message(state["messages"])
        # recent_context = state["messages"][-6:]
        # query = await manager.rewrite_query_if_needed(last_msg, recent_context)
        #
        # # 向量检索
        # limit = self.agent_config.get("memory", {}).get("retrieval_count", 5)
        # results = await manager.recall(query, limit=limit)
        #
        # if not results:
        #     return None
        #
        # # 格式化
        # lines = []
        # for r in results:
        #     category = r.card.category.value if r.card.category else "other"
        #     lines.append(f"- [{category}] {r.card.content}")
        # return "\n".join(lines)

        return None  # 占位，待实现

    # === 内部工具 ===

    @staticmethod
    def _extract_last_user_message(messages: list[BaseMessage]) -> str | None:
        """从 messages 中取出最后一条用户消息的文本。"""
        for msg in reversed(messages):
            if isinstance(msg, HumanMessage):
                content = msg.content
                return content if isinstance(content, str) else str(content)
        return None
