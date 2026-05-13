"""
PersonaProvider —— 提供 Agent 的人设、性格、说话风格和行为准则。

属于 STATIC 组：内容来自配置文件，整个 session 内不变，可缓存。
"""

from __future__ import annotations

from typing import Any

from context_providers.base import BaseContextProvider, ProviderGroup


class PersonaProvider(BaseContextProvider):
    """
    人设上下文提供者。

    从 agent_config 中读取 persona 相关字段并格式化为 SP 文本。
    整个 session 内容不变，首次 run 后缓存结果。
    """

    name = "persona"
    group = ProviderGroup.STATIC

    def __init__(self, agent_config: dict[str, Any]):
        super().__init__(agent_config)
        self._cache: str | None = None

    async def should_run(self, state: dict[str, Any]) -> bool:
        """人设永远需要。"""
        return True

    async def run(self, state: dict[str, Any]) -> str | None:
        """
        从 agent_config 的 persona 字段组装人设文本。

        缓存结果，同一 session 内只组装一次。
        """
        if self._cache is not None:
            return self._cache

        # TODO: 实现 —— 从 agent_config 中读取 persona 配置
        # persona = self.agent_config.get("persona", {})
        # agent_name = persona.get("name", "小星")
        # background = persona.get("background", "")
        # traits = persona.get("traits_description", "")
        # speaking_style = persona.get("speaking_style", "")
        # guidelines = persona.get("guidelines", [])
        #
        # parts = [
        #     f"你是 {agent_name}，{background}",
        #     "",
        #     f"## 你的性格特征\n{traits}",
        #     "",
        #     f"## 交流风格\n{speaking_style}",
        #     "",
        #     "## 行为准则",
        #     *[f"- {g}" for g in guidelines],
        # ]
        # self._cache = "\n".join(parts)
        # return self._cache

        self._cache = ""  # 占位，待实现
        return self._cache
