"""LangGraph 状态结构定义 —— 定义流经图中各节点的状态数据。"""

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

    # === 上下文信息（由各 tool / node 填充） ===
    # 当前截图分析结果
    current_screen_context: str | None
    # 本轮从长期记忆召回的卡片（已格式化为文本，待注入 prompt）
    recalled_memory_text: str | None
    # 检索到的游戏知识
    game_knowledge: list[str] | None
    # 联网搜索结果
    web_search_results: list[str] | None

    # === 输出元数据 ===
    # 情感标签（用于驱动 Live2D 表情）
    emotion_label: str | None
    # Live2D 动作触发
    live2d_action: str | None
    # TTS 参数调整
    tts_params: dict | None
