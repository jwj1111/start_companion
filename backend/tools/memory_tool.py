"""
记忆写入 Tool —— 让 Agent 在对话中主动记录重要信息。

设计说明：
- 长期记忆的**读取**由 route_input 节点的预注入流程负责（Gate → 改写 → 检索 → 注入 SP），
  不再通过 Tool Calling 实现，因为预注入能让模型"带着记忆从头生成"，体验更好。
- 本文件只保留**写入** tool，允许主模型在对话过程中主动把重要信息存入记忆。
- 写入的卡片默认 status=PENDING，等用户审核通过后才参与后续召回。

用户隔离：
- Tool 内部通过 LangGraph 的 RunnableConfig 获取当前 (user_id, agent_id)。
- 实际存储由 MemoryManager 负责。
"""

from langchain_core.tools import tool


@tool
async def memory_write_tool(content: str, importance: float = 0.5) -> str:
    """
    将重要信息存入长期记忆。

    当对话中出现值得记住的信息时使用此工具，例如用户的偏好、重要事件、关键决定等。
    存入后默认处于待审核状态，需用户确认后才会在未来对话中被召回。

    Args:
        content: 需要记住的信息内容
        importance: 重要性评分 (0.0-1.0)，越高越重要

    Returns:
        存储确认信息
    """
    # TODO: 实现
    # 1. 从 RunnableConfig 或 ContextVar 取出当前 user_id / agent_id
    # 2. manager = await MemoryManager.for_user(user_id, agent_id)
    # 3. card = MemoryCard(
    #        content=content,
    #        importance=importance,
    #        status=MemoryCardStatus.PENDING,
    #        source=MemorySource.LLM_EXTRACTED,
    #    )
    # 4. card_id = await manager.add_manual_card(card)
    # 5. return f"已记录（待审核）: {content[:50]}..."
    raise NotImplementedError("需要对接 MemoryManager")
