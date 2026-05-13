"""
LangGraph Tools 注册中心。

所有 tool 在此统一注册，并提供给主 Agent。
Tool 是 Agent 与外部系统交互的主要方式。

Tool 分类：
- 视觉: 截图与视觉分析
- 记忆: 对话中主动写入长期记忆（读取由 MemoryProvider 负责，不走 tool）
- 游戏信息: 知识库 + 联网搜索合一，内部自动选择来源并总结

注意：长期记忆的**读取**不在此处注册。
读取路径是 MemoryProvider（Context Provider）在入口阶段完成的。
"""

from langchain_core.tools import BaseTool

from tools.screenshot import screenshot_tool
from tools.memory_tool import memory_write_tool
from tools.game_info_tool import game_info_tool


def get_all_tools() -> list[BaseTool]:
    """获取所有已注册的 tool，供主 Agent 使用。"""
    return [
        screenshot_tool,
        memory_write_tool,
        game_info_tool,
    ]
