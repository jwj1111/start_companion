"""
LangGraph Tools 注册中心。

所有 tool 在此统一注册，并提供给主 Agent。
Tool 是 Agent 与外部系统交互的主要方式。

Tool 分类：
- 视觉: 截图与视觉分析
- 语音: ASR / TTS 控制
- 记忆: 长期记忆读写
- 知识: 游戏知识库 RAG
- 搜索: 联网搜索
- 子 Agent: 将子 Agent 作为 tool 调用
"""

from langchain_core.tools import BaseTool

from tools.screenshot import screenshot_tool
from tools.memory_tool import memory_read_tool, memory_write_tool
from tools.knowledge_tool import knowledge_search_tool
from tools.web_search_tool import web_search_tool


def get_all_tools() -> list[BaseTool]:
    """获取所有已注册的 tool，供主 Agent 使用。"""
    return [
        screenshot_tool,
        memory_read_tool,
        memory_write_tool,
        knowledge_search_tool,
        web_search_tool,
    ]
