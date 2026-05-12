"""
LangGraph Agent 定义。

本包包含：
- graph.py: LangGraph 主编排图定义
- state.py: 图状态结构定义
- nodes.py: 图节点实现
- sub_agents/: 子 Agent 定义（情感分析、游戏策略等）

架构：
    主 Agent (ReAct) ──┬── Tools (截图、语音、搜索、记忆 ……)
                       └── 子 Agent (emotion_analyzer, game_strategist ……)
"""
