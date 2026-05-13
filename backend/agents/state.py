"""
LangGraph 状态结构定义 —— 定义流经图中各节点的状态数据。

设计原则：
- context_parts 是所有背景上下文的统一容器（由 Context Providers 填充）
- Tool 的执行结果不需要单独字段，它们作为 ToolMessage 自然存在于 messages 中
- 新增功能模块时只需新增 Provider，不需要改 state 定义
"""

from typing import Annotated, Any, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """
    主 Agent 图的状态。

    该状态贯穿 LangGraph 图的所有节点。
    """

    # === 会话与身份 ===
    messages: Annotated[list[BaseMessage], add_messages]
    session_id: str
    agent_id: str
    user_id: str                              # 用于记忆层的用户隔离

    # === Agent 配置（预设 + 用户自定义 合并后的结果） ===
    agent_config: dict[str, Any]

    # === 背景上下文（由 Context Providers 在 route_input 中填充） ===
    # key = provider name, value = 该 provider 产出的文本
    # 例: {"persona": "你是小星...", "profile": "称呼: 老板...", "memory": "上次..."}
    # 为空的 provider 不会出现在字典中
    # Tool 的结果（截图、知识库、搜索）不在这里，它们作为 ToolMessage 存在于 messages 中
    context_parts: dict[str, str]

    # === 输出元数据 ===
    # 情感标签（用于驱动 Live2D 表情）
    emotion_label: str | None
    # Live2D 动作触发
    live2d_action: str | None
    # TTS 参数调整
    tts_params: dict | None
