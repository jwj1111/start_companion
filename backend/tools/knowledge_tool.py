"""
游戏知识库 Tool —— 对游戏专用知识的 RAG。

搜索预先构建好的向量知识库，内容包括：
- 游戏攻略与流程说明
- 角色 / 道具 / 技能信息
- 游戏机制解释
- 玩法技巧与策略
"""

from langchain_core.tools import tool


@tool
async def knowledge_search_tool(query: str, game_name: str | None = None) -> str:
    """
    搜索游戏知识库获取游戏相关信息。

    当用户询问游戏攻略、角色技能、道具效果、游戏机制等问题时使用此工具。

    Args:
        query: 搜索查询，描述想要了解的游戏知识
        game_name: 可选，指定游戏名称以缩小搜索范围

    Returns:
        相关的游戏知识内容
    """
    # TODO: 具体实现
    # 1. 对 query 生成 embedding
    # 2. 在知识向量库中搜索（可选按 game_name 过滤）
    # 3. 对结果重排序
    # 4. 格式化并返回 top 结果
    raise NotImplementedError("需要对接知识库")
