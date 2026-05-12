"""
LangGraph 图节点实现。

每个节点都是一个函数，接收当前状态并返回状态更新。

节点列表：
- route_input      : 入口预处理（加载配置、短期压缩、可选召回长期记忆）
- call_main_agent  : 调 LLM（带 tools）
- should_continue  : 条件边 —— tool 分支或输出分支
- process_output   : 输出后处理（提取情感、提取记忆、映射 Live2D）
"""

from __future__ import annotations

from typing import Any

from loguru import logger

from agents.state import AgentState
from memory.manager import MemoryManager
from memory.short_term.summarizer import build_conversation_window
from models.provider import get_model


# ============================================================
# 节点：入口预处理
# ============================================================

async def route_input(state: AgentState) -> dict[str, Any]:
    """
    输入路由节点 —— 在调用主 Agent 之前准备上下文。

    主要职责：
    1. 加载 Agent 配置（已在外部做好，这里只使用）
    2. 短期记忆：按轮次阈值判断是否压缩
    3. 长期记忆：按 Retrieval Gate 判断是否召回，若是则注入
    """
    user_id = state["user_id"]
    agent_id = state["agent_id"]
    logger.info(f"route_input: user={user_id}, agent={agent_id}")

    # TODO: 实现
    # 1. manager = await MemoryManager.for_user(user_id, agent_id, state["agent_config"])
    #
    # 2. 短期压缩：
    #    window = build_conversation_window(state["messages"])
    #    new_window = await manager.maybe_compress(window)
    #    if new_window is not window:  # 发生了压缩
    #        messages_update = new_window.to_langchain_messages()
    #        # 用 RemoveMessage 或直接替换 state.messages（需要特殊处理）
    #
    # 3. 长期召回：
    #    last_user_msg = extract_last_user_message(state["messages"])
    #    recalled_text = None
    #    if last_user_msg and await manager.should_recall(last_user_msg):
    #        results = await manager.recall(last_user_msg, limit=5)
    #        recalled_text = format_memories_for_prompt(results)
    #
    # 4. return {"recalled_memory_text": recalled_text, ...}
    return {
        "recalled_memory_text": None,
    }


# ============================================================
# 节点：主 Agent
# ============================================================

async def call_main_agent(state: AgentState) -> dict[str, Any]:
    """
    主 Agent 节点 —— 使用 ReAct 模式调用 LLM。

    会把召回的长期记忆文本、游戏知识、截图上下文等注入到 System Prompt 里。
    """
    from tools import get_all_tools

    model = get_model("main")
    tools = get_all_tools()
    model_with_tools = model.bind_tools(tools)

    # TODO: 组装带上下文注入的 messages
    # 1. system_prompt = build_system_prompt(
    #        agent_config=state["agent_config"],
    #        recalled_memory=state.get("recalled_memory_text"),
    #        screen_context=state.get("current_screen_context"),
    #        game_knowledge=state.get("game_knowledge"),
    #    )
    # 2. full_messages = [SystemMessage(content=system_prompt)] + state["messages"]
    # 3. response = await model_with_tools.ainvoke(full_messages)

    response = await model_with_tools.ainvoke(state["messages"])
    return {"messages": [response]}


# ============================================================
# 条件边
# ============================================================

def should_continue(state: AgentState) -> str:
    """
    决定下一步是执行 tool 还是进入输出处理。

    返回值：
        "tools"  - 当最后一条消息包含 tool 调用时
        "output" - 已可以生成最终回复
    """
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return "output"


# ============================================================
# 节点：输出后处理
# ============================================================

async def process_output(state: AgentState) -> dict[str, Any]:
    """
    输出处理节点 —— 对话完成后的副作用。

    主要职责：
    1. 情感分析 & Live2D 动作映射
    2. 提取长期记忆并写入（PENDING 状态，等用户审核）
    3. 如需要可触发短期压缩（也可放在下一轮 route_input）
    """
    user_id = state["user_id"]
    agent_id = state["agent_id"]
    session_id = state.get("session_id", "")

    # TODO: 实现
    # 1. 情感分析
    #    last_msg = state["messages"][-1]
    #    emotion = await analyze_emotion(last_msg, auxiliary_model)
    #    live2d_action = emotion_to_live2d(emotion, state["agent_config"])
    #
    # 2. 提取记忆（从最近一批完整对话中）
    #    manager = await MemoryManager.for_user(user_id, agent_id, state["agent_config"])
    #    recent_messages = state["messages"][-10:]  # 提取范围可调
    #    await manager.extract_and_store(recent_messages, session_id=session_id)

    return {
        "emotion_label": None,
        "live2d_action": None,
    }
