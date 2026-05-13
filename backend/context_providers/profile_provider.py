"""
ProfileProvider —— 提供用户档案（结构化的 EAV 字段）。

属于 DYNAMIC 组：虽然档案更新不频繁（session_end 时才更新），
但不同用户/不同 session 档案不同，且中途可能被手动修改，所以每轮读取。
实际开销很小（几十个字段的 DB 查询）。
"""

from __future__ import annotations

from typing import Any

from loguru import logger

from context_providers.base import BaseContextProvider, ProviderGroup


class ProfileProvider(BaseContextProvider):
    """
    用户档案上下文提供者。

    每轮调用 MemoryManager.get_profile_text() 获取全量档案文本。
    """

    name = "profile"
    group = ProviderGroup.DYNAMIC

    async def should_run(self, state: dict[str, Any]) -> bool:
        """档案每轮都读。"""
        return True

    async def run(self, state: dict[str, Any]) -> str | None:
        """
        读取用户档案并格式化。

        返回示例：
            关于用户：
            - 称呼: 老板
            - 生日: 5月3日
            - 最爱角色: 枫原万叶
        """
        # TODO: 实现 —— 对接 MemoryManager
        # from memory.manager import MemoryManager
        #
        # user_id = state["user_id"]
        # agent_id = state["agent_id"]
        # manager = await MemoryManager.for_user(user_id, agent_id, self.agent_config)
        # text = await manager.get_profile_text()
        # return text if text else None

        return None  # 占位，待实现
