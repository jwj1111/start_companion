"""
游戏信息查询 Tool —— 一站式获取游戏相关信息。

设计说明：
- 合并了原来分散的 knowledge_search_tool 和 web_search_tool
- 主 Agent 不需要操心"该用知识库还是联网"，本 tool 内部自动判断
- 搜集到的原始信息由 auxiliary 模型压缩总结后返回，避免大段原文污染主 Agent 上下文

查询策略：
1. 如果游戏知识库可用且有结果 → 使用知识库结果
2. 如果知识库不可用或无结果 → 联网搜索
3. 用 auxiliary 模型将原始结果压缩为简洁回答

截图上下文：
- 主 Agent 可以先调 screenshot_tool 获取画面描述，再调本 tool 时通过 screen_context 传入
- 也可以没有截图，本 tool 同样能工作（screen_context 为空即可）

未来扩展：
- 如果查询逻辑变复杂（如需要多轮检索+推理），可将内部逻辑升级为 LangGraph 子图
- 对外接口（tool 签名）不变，主图不需要改动
"""

from langchain_core.tools import tool


@tool
async def game_info_tool(query: str, screen_context: str = "") -> str:
    """
    查询游戏相关信息并给出总结。

    当用户询问游戏攻略、角色技能、道具效果、游戏机制、版本更新等问题时使用此工具。
    会自动选择最佳信息来源（知识库或联网搜索），并将结果压缩为简洁回答。

    Args:
        query: 游戏相关的问题
        screen_context: 当前游戏画面的描述（可选，由 screenshot_tool 获取后传入）

    Returns:
        针对问题的简洁回答
    """
    # TODO: 实现
    #
    # 1. 构建检索 query（如果有画面上下文，拼接进去提高相关性）
    # enriched_query = f"{query}\n当前画面：{screen_context}" if screen_context else query
    #
    # 2. 尝试知识库检索
    # raw_info = None
    # try:
    #     from knowledge.retriever import KnowledgeRetriever
    #     retriever = KnowledgeRetriever()
    #     chunks = await retriever.search(enriched_query, limit=3)
    #     if chunks:
    #         raw_info = "\n\n".join(c.content for c in chunks)
    # except Exception:
    #     pass  # 知识库不可用时静默降级
    #
    # 3. 知识库没结果 → 联网搜索
    # if not raw_info:
    #     raw_info = await _web_search(enriched_query)
    #
    # if not raw_info:
    #     return "抱歉，我暂时找不到相关信息。"
    #
    # 4. 用 auxiliary 模型压缩总结（不把大段原文返回给主 Agent）
    # from models.provider import get_model
    # auxiliary = get_model("auxiliary")
    # prompt = (
    #     f"根据以下参考信息，简洁回答用户的游戏问题。\n\n"
    #     f"参考信息：\n{raw_info}\n\n"
    #     f"{'当前游戏画面：' + screen_context + chr(10) if screen_context else ''}"
    #     f"用户问题：{query}\n\n"
    #     f"简洁回答（200字以内）："
    # )
    # response = await auxiliary.ainvoke(prompt)
    # return response.content
    raise NotImplementedError("需要对接搜索 Provider 和/或知识库")


async def _web_search(query: str) -> str | None:
    """
    联网搜索的内部实现。

    支持多种搜索 Provider（tavily / serper / bing），由配置决定。
    返回拼接好的搜索结果文本，或 None。
    """
    # TODO: 实现
    # 1. 从配置读取搜索 provider
    # 2. 执行搜索
    # 3. 格式化结果
    return None
