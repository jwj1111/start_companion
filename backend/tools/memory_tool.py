"""
记忆读写 Tool。

让 Agent 能够在对话中**主动**调用：
- 从长期记忆中检索（作为自动召回的补充，避免漏召回）
- 把重要信息写入长期记忆（默认 PENDING，等用户审核）

这些 tool 通过 LangGraph 的 ReAct 机制暴露给主 Agent。
实际的存储由 MemoryManager 负责，这里只做接口转发。

注意：
- Tool 内部需要拿到当前 (user_id, agent_id)，通常通过上下文注入（见 TODO）
- 用户隔离由 MemoryManager 内部保证，这里不做二次校验
"""

from langchain_core.tools import tool


@tool
async def memory_read_tool(query: str) -> str:
    """
    从长期记忆中检索与当前话题相关的信息。

    当需要回忆之前的对话内容、用户偏好、或重要事件时使用此工具。

    Args:
        query: 检索查询，描述想要回忆的内容

    Returns:
        相关的记忆内容列表（纯文本拼接）
    """
    # TODO: 实现
    # 1. 从 RunnableConfig 或 ContextVar 里取出当前 user_id / agent_id
    # 2. manager = await MemoryManager.for_user(user_id, agent_id, ...)
    # 3. results = await manager.recall(query, limit=5)
    # 4. 格式化为文本返回
    raise NotImplementedError("需要对接 MemoryManager")


@tool
async def memory_write_tool(content: str, importance: float = 0.5) -> str:
    """
    将重要信息存入长期记忆。

    当对话中出现值得记住的信息时使用此工具，例如用户的偏好、重要事件、关键决定等。
    存入后默认处于 PENDING 状态，等用户审核。

    Args:
        content: 需要记住的信息内容
        importance: 重要性评分 (0.0-1.0)，越高越重要

    Returns:
        存储确认信息
    """
    # TODO: 实现
    # 1. 从上下文取 user_id / agent_id
    # 2. 构造 MemoryCard(content=..., importance=..., status=PENDING, source=LLM_EXTRACTED)
    # 3. manager.long_term.add_card(card)
    raise NotImplementedError("需要对接 MemoryManager")
