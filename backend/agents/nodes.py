"""
LangGraph 图节点实现。

每个节点都是一个函数，接收当前状态并返回状态更新。

节点列表：
- route_input      : 入口预处理（遍历 Context Providers 收集背景上下文）
- call_main_agent  : 调 LLM（带 tools），用 context_parts 组装 SP
- should_continue  : 条件边 —— tool 分支或输出分支
- process_output   : 输出后处理（情感分析、记忆提取、Live2D 映射）

Context Providers 架构：
    每个功能模块（人设、档案、记忆...）是一个独立的 Provider：
    - 有自己的 Gate（should_run）
    - 有自己的处理逻辑（run）
    - 产出一段文本 → 存入 context_parts
    新增/删除模块不需要改本文件。

System Prompt 组装模式（通过配置切换，方便测试）：
    - "unified": 所有 context_parts 拼成一个 SystemMessage
    - "split":   STATIC 组拼一个 SP + DYNAMIC 组拼一个 SP（两个 SystemMessage）
"""

from __future__ import annotations

from typing import Any

from langchain_core.messages import BaseMessage, SystemMessage
from loguru import logger

from agents.state import AgentState
from context_providers import (
    get_all_providers,
    get_static_providers,
    get_dynamic_providers,
)
from context_providers.base import BaseContextProvider
from models.provider import get_model


# ============================================================
# SP 组装
# ============================================================

def _build_unified_sp(context_parts: dict[str, str]) -> list[SystemMessage]:
    """
    统一模式：所有上下文拼成一个 SystemMessage。

    按 key 的顺序（即 Provider 注册顺序）逐段拼接。
    每段之间用空行分隔。
    """
    sections = []
    for name, text in context_parts.items():
        if text:
            sections.append(text)
    if not sections:
        return []
    return [SystemMessage(content="\n\n".join(sections))]


def _build_split_sp(context_parts: dict[str, str], providers: list[BaseContextProvider]) -> list[SystemMessage]:
    """
    分离模式：STATIC 组拼一个 SP，DYNAMIC 组拼一个 SP。

    好处：固定的人设 SP 可以利用模型的 prompt caching。
    """
    static_names = {p.name for p in get_static_providers(providers)}
    dynamic_names = {p.name for p in get_dynamic_providers(providers)}

    static_sections = [text for name, text in context_parts.items() if name in static_names and text]
    dynamic_sections = [text for name, text in context_parts.items() if name in dynamic_names and text]

    messages = []
    if static_sections:
        messages.append(SystemMessage(content="\n\n".join(static_sections)))
    if dynamic_sections:
        messages.append(SystemMessage(content="\n\n".join(dynamic_sections)))
    return messages


def build_system_messages(
    context_parts: dict[str, str],
    providers: list[BaseContextProvider],
    mode: str = "unified",
) -> list[SystemMessage]:
    """
    根据配置模式组装 System Message(s)。

    Args:
        context_parts: Provider 产出的文本字典
        providers: 当前启用的 Provider 列表（用于分组判断）
        mode: "unified"（一个SP）或 "split"（两个SP）

    Returns:
        一个或两个 SystemMessage 的列表
    """
    if mode == "split":
        return _build_split_sp(context_parts, providers)
    else:
        return _build_unified_sp(context_parts)


# ============================================================
# 节点：入口预处理
# ============================================================

async def route_input(state: AgentState) -> dict[str, Any]:
    """
    输入路由节点 —— 遍历 Context Providers 收集背景上下文。

    每个 Provider 是一个独立沙箱：
    - PersonaProvider: 读配置文件 → 人设文本
    - ProfileProvider: 读 EAV 数据库 → 档案文本
    - MemoryProvider: Gate → 改写 → 向量检索 → 记忆文本
    - ... 未来新增 Provider 不需要改这里

    短期记忆的压缩也在此处检查（独立于 Provider 体系，因为它直接操作 messages）。
    """
    user_id = state["user_id"]
    agent_id = state["agent_id"]
    agent_config = state.get("agent_config", {})
    logger.info(f"route_input: user={user_id}, agent={agent_id}")

    # 1. 遍历 Context Providers
    providers = get_all_providers(agent_config)
    context_parts: dict[str, str] = {}

    for provider in providers:
        try:
            if await provider.should_run(state):
                result = await provider.run(state)
                if result:
                    context_parts[provider.name] = result
                    logger.debug(f"Provider '{provider.name}' 产出 {len(result)} 字符")
        except NotImplementedError:
            # 骨架阶段 provider 未实现时静默跳过
            logger.debug(f"Provider '{provider.name}' 未实现，跳过")
        except Exception as e:
            # 单个 provider 失败不应阻断整个流程
            logger.warning(f"Provider '{provider.name}' 执行异常: {e}")

    # 2. 短期记忆压缩（直接操作 messages，不属于 context_parts）
    # TODO: 实现
    # from memory.short_term.summarizer import build_conversation_window
    # from memory.manager import MemoryManager
    # manager = await MemoryManager.for_user(user_id, agent_id, agent_config)
    # window = build_conversation_window(state["messages"])
    # new_window = await manager.maybe_compress(window)
    # if new_window is not window:
    #     return {"context_parts": context_parts, "messages": new_window.to_langchain_messages()}

    return {"context_parts": context_parts}


# ============================================================
# 节点：主 Agent
# ============================================================

async def call_main_agent(state: AgentState) -> dict[str, Any]:
    """
    主 Agent 节点 —— 使用 ReAct 模式调用 LLM。

    SP 组装逻辑：
    1. 从 state["context_parts"] 中读取所有背景上下文
    2. 按配置的 sp_mode（"unified" 或 "split"）组装成 SystemMessage(s)
    3. 拼接 state["messages"]（包含对话历史 + ToolMessage）
    4. 调用 LLM

    Tool（截图、知识库、搜索等）的结果不需要注入 SP：
    - 它们的结果作为 ToolMessage 已经在 messages 中
    - 模型下一次被调用时自然能看到
    """
    from tools import get_all_tools

    agent_config = state.get("agent_config", {})
    context_parts = state.get("context_parts", {})

    model = get_model("main")
    tools = get_all_tools()
    model_with_tools = model.bind_tools(tools)

    # 组装 SP
    sp_mode = agent_config.get("sp_mode", "unified")  # "unified" 或 "split"
    providers = get_all_providers(agent_config)
    system_messages = build_system_messages(context_parts, providers, mode=sp_mode)

    # 拼接完整消息列表
    full_messages = system_messages + state["messages"]

    response = await model_with_tools.ainvoke(full_messages)
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
    3. 档案更新（仅 session_end 时，不在此处）

    注意：记忆写入与读取完全隔离。
    - 写入的新卡片 status=PENDING，不会被读取侧的向量检索命中
    - 只有用户审核通过（PENDING → ACTIVE）后，才参与下一次召回
    """
    user_id = state["user_id"]
    agent_id = state["agent_id"]
    session_id = state.get("session_id", "")

    # TODO: 实现
    # from memory.manager import MemoryManager
    #
    # # 1. 情感分析
    # last_msg = state["messages"][-1]
    # emotion = await analyze_emotion(last_msg, auxiliary_model)
    # live2d_action = emotion_to_live2d(emotion, state["agent_config"])
    #
    # # 2. 提取记忆（从最近一批完整对话中）
    # manager = await MemoryManager.for_user(user_id, agent_id, state["agent_config"])
    # recent_messages = state["messages"][-10:]
    # await manager.extract_and_store(recent_messages, session_id=session_id)

    return {
        "emotion_label": None,
        "live2d_action": None,
    }
