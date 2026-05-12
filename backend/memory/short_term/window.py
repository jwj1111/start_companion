"""
对话窗口 —— 短期记忆的数据结构。

它是对 LangGraph State.messages 的一个逻辑视图，
由 "[可选的历史摘要块] + [最近 N 条原始消息]" 组成。
"""

from dataclasses import dataclass, field

from langchain_core.messages import BaseMessage


@dataclass
class ConversationWindow:
    """
    对话窗口 —— 短期记忆的数据表示。

    这不是持久化对象，而是从 LangGraph State 重建出来的视图，
    方便摘要器判断是否需要触发压缩。
    """

    # 早期对话的摘要块（可能为 None，表示还没触发过摘要）
    summary_block: BaseMessage | None = None

    # 最近未被摘要的原始消息
    recent_messages: list[BaseMessage] = field(default_factory=list)

    def total_turns(self) -> int:
        """
        估算当前窗口的对话轮数。

        简化规则：一个 user message 算一轮（tool 调用等不计）。
        具体实现可按需调整。
        """
        # TODO: 精确实现时过滤 ToolMessage / SystemMessage
        return len(self.recent_messages)

    def to_langchain_messages(self) -> list[BaseMessage]:
        """还原为 LangChain 的 messages 列表，供 LLM 使用。"""
        result: list[BaseMessage] = []
        if self.summary_block is not None:
            result.append(self.summary_block)
        result.extend(self.recent_messages)
        return result
