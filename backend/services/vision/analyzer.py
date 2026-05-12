"""
视觉分析器 —— 使用视觉模型分析游戏截图。

处理流程：
1. 从前端接收截图（base64 或 bytes）
2. 可选地做压缩 / 缩放以提升效率
3. 连同分析提示词一起发送给视觉模型
4. 返回分析结果
"""

import base64
from loguru import logger

from models.provider import get_model


class VisionAnalyzer:
    """使用具备视觉能力的 LLM 来分析游戏截图。"""

    def __init__(self):
        self.model = get_model("vision")

    async def analyze(
        self,
        image_base64: str,
        query: str = "描述这个游戏画面的内容",
        game_context: str = "",
    ) -> str:
        """
        分析一张截图。

        参数：
            image_base64: Base64 编码后的图像数据
            query: 希望从画面中获取的信息或要回答的问题
            game_context: 可选，当前所玩游戏的上下文

        返回值：
            对图像的文本描述或分析结果
        """
        from langchain_core.messages import HumanMessage

        prompt = f"""分析这个游戏截图。
{f'游戏上下文: {game_context}' if game_context else ''}
问题: {query}

请描述你看到的内容，包括:
- 游戏场景/界面
- 关键UI元素（血量、技能、地图等）
- 当前游戏状态
- 任何相关的文字信息"""

        message = HumanMessage(
            content=[
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{image_base64}"},
                },
            ]
        )

        response = await self.model.ainvoke([message])
        logger.debug(f"视觉分析完成: 输出 {len(response.content)} 个字符")
        return response.content

    @staticmethod
    def compress_image(image_bytes: bytes, max_size: int = 1024) -> bytes:
        """压缩图像以减少 token 消耗。"""
        # TODO: 实现图像压缩
        # 可使用 PIL，如果长/宽超过 max_size 则按比例缩放
        return image_bytes
