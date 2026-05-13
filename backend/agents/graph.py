"""
LangGraph 主编排图。

主 Agent 使用 ReAct 模式：
1. route_input: 遍历 Context Providers 收集背景上下文
2. call_main_agent: 按需调用 tools（截图、游戏信息、记忆写入）
3. process_output: 输出后处理（情感分析、记忆提取、Live2D 映射）
"""

from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import HumanMessage, AIMessage

from agents.state import AgentState
from agents.nodes import (
    route_input,
    call_main_agent,
    process_output,
    should_continue,
)
from tools import get_all_tools


def build_companion_graph() -> StateGraph:
    """
    构建 START Companion 的主 LangGraph 图。

    图结构：
        [input] -> route_input -> call_main_agent -> should_continue?
                                       ↑                    |
                                       |              yes: tools
                                       └────────────────────┘
                                                      |
                                                 no: process_output -> [END]
    """
    # 获取所有已注册的 tools
    tools = get_all_tools()

    # 构建图
    graph = StateGraph(AgentState)

    # 添加节点
    graph.add_node("route_input", route_input)
    graph.add_node("agent", call_main_agent)
    graph.add_node("tools", ToolNode(tools))
    graph.add_node("process_output", process_output)

    # 设置入口节点
    graph.set_entry_point("route_input")

    # 添加边
    graph.add_edge("route_input", "agent")
    graph.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            "output": "process_output",
        },
    )
    graph.add_edge("tools", "agent")
    graph.add_edge("process_output", END)

    return graph


def compile_graph():
    """编译图以供执行。"""
    graph = build_companion_graph()
    return graph.compile()
