"""
截图与视觉分析 Tool。

捕获当前的游戏画面，并用视觉模型理解游戏状态、UI 元素与画面上下文。

截图本身由前端通过 WebSocket 提供；本 tool 会请求一张截图，
并交给视觉模型进行分析。
"""

from langchain_core.tools import tool


@tool
async def screenshot_tool(query: str = "描述当前游戏画面") -> str:
    """
    截图并分析当前游戏画面。

    当需要了解用户正在玩什么、游戏当前状态、或需要视觉信息来回答问题时使用此工具。

    Args:
        query: 针对截图的分析问题，例如"当前角色血量是多少"、"这是什么游戏场景"

    Returns:
        对当前游戏画面的分析描述
    """
    # TODO: 具体实现
    # 1. 通过 WebSocket 向前端请求一张截图
    # 2. 将图像转为 base64
    # 3. 连同 query 发送给视觉模型
    # 4. 返回分析结果
    raise NotImplementedError("需要对接视觉分析流水线")
