"""
情感分析子 Agent。

综合分析用户消息、语音语调和游戏上下文，判断用户情绪状态，
并建议合适的陪伴回应方式。

可被主 Agent 作为 tool 调用。
"""

from langgraph.graph import StateGraph, END
from typing import TypedDict, Any


class EmotionState(TypedDict):
    """情感分析所使用的状态。"""
    user_message: str
    conversation_history: list[dict]
    game_context: str | None
    # 输出字段
    emotion: str  # happy, sad, frustrated, excited, neutral 等
    intensity: float  # 0.0 - 1.0
    suggested_tone: str  # 建议的回复语气
    live2d_expression: str  # 映射到 Live2D 表情


async def analyze_emotion(state: EmotionState) -> dict[str, Any]:
    """根据上下文分析情绪。"""
    # TODO: 使用辅助模型 + 情感分析提示词
    # 综合考虑：文本情感、游戏上下文（输 / 赢）、历史对话
    return {
        "emotion": "neutral",
        "intensity": 0.5,
        "suggested_tone": "friendly",
        "live2d_expression": "normal",
    }


def build_emotion_graph() -> StateGraph:
    """构建情感分析子图。"""
    graph = StateGraph(EmotionState)
    graph.add_node("analyze", analyze_emotion)
    graph.set_entry_point("analyze")
    graph.add_edge("analyze", END)
    return graph
