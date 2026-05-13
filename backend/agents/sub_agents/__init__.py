"""
子 Agent —— 由主编排器调用的专门化 Agent。

每个子 Agent 都是一个独立的 LangGraph 图，可以被主 Agent 作为 tool 来调用。
只有真正需要多步复杂推理的场景才值得用子 Agent。

已有的子 Agent：
- emotion_analyzer: 分析用户情绪和上下文，驱动 Live2D 表情

已删除：
- game_strategist: 游戏策略查询已合并为 game_info_tool（单 tool 内搜索+总结）
"""
