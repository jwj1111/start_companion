"""
LangGraph Agent 定义。

本包包含：
- graph.py: LangGraph 主编排图定义
- state.py: 图状态结构定义
- nodes.py: 图节点实现（route_input 遍历 Context Providers，call_main_agent 组装 SP）
- sub_agents/: 子 Agent 定义（情感分析等，可作为 tool 暴露）

架构：
    route_input ── Context Providers (人设、档案、记忆 ……) ── 填充 context_parts
        │
        ▼
    主 Agent (ReAct) ──┬── Tool: screenshot（截图分析）
                       ├── Tool: game_info（知识库+联网搜索+总结，合一）
                       └── Sub Agent: emotion_analyzer（情感分析+Live2D）

    背景上下文（context_parts）和 Tool 结果走不同通道：
    - context_parts → 拼入 System Prompt（模型从头就能看到）
    - Tool 结果 → 作为 ToolMessage 在 messages 中（对话中产生）
"""
