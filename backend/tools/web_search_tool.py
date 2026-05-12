"""
联网搜索 Tool —— 从互联网获取实时信息。

当知识库中没有答案、或需要最新信息（补丁说明、活动、新闻等）时使用。
"""

from langchain_core.tools import tool


@tool
async def web_search_tool(query: str) -> str:
    """
    联网搜索获取实时信息。

    当知识库中没有答案，或需要最新信息（游戏更新、活动、补丁说明等）时使用此工具。

    Args:
        query: 搜索查询

    Returns:
        搜索结果摘要
    """
    # TODO: 具体实现
    # 支持多种 Provider: tavily / serper / bing
    # 1. 从配置读取搜索 provider
    # 2. 执行搜索
    # 3. 格式化并摘要结果
    raise NotImplementedError("需要对接搜索 Provider")
