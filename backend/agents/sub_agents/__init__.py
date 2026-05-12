"""
子 Agent —— 由主编排器调用的专门化 Agent。

每个子 Agent 都是一个独立的 LangGraph 图，可以被主 Agent 作为 tool 来调用。

已有的子 Agent：
- emotion_analyzer: 分析用户情绪和上下文
- game_strategist: 提供游戏相关的建议与策略
"""
