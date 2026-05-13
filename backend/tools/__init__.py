"""
LangGraph Tools 注册中心。

所有 tool 在此统一注册，并提供给主 Agent。

Tool 分类：
- 视觉: 截图与视觉分析
- 游戏信息: 知识库 + 联网搜索合一，内部自动选择来源并总结

记忆读写都不走 tool：
- 读取: MemoryProvider（Context Provider）在入口阶段注入 SP
- 写入: session_end 时 LLM 自动提取，不依赖 tool calling
"""

from langchain_core.tools import BaseTool

from tools.screenshot import screenshot_tool
from tools.game_info_tool import game_info_tool


def get_all_tools() -> list[BaseTool]:
    """获取所有已注册的 tool，供主 Agent 使用。"""
    return [
        screenshot_tool,
        game_info_tool,
    ]
