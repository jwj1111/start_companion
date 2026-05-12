"""
LangGraph 主编排图。

主 Agent 使用 ReAct 模式：
1. 接收用户输入（文本 / 语音转写结果）
2. 按需调用 tools（截图、记忆、搜索 等）
3. 生成带有情感 / 动作元数据的回复
4. 在需要时路由到子 Agent（情感分析、游戏策略 等）
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
