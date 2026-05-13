"""
用户档案存储的抽象基类。

采用 JSON 列模式（一行一用户，data 列存 JSON）：
- 读写都是一行操作，比 EAV 简单高效
- JSON 内字段自由，加新字段不用改表结构
- 不同 Agent 可以有不同字段集

表结构：
    user_profiles (
        user_id     TEXT NOT NULL,
        agent_id    TEXT NOT NULL,
        data        TEXT NOT NULL DEFAULT '{}',   -- JSON: {"nickname": "老板", ...}
        updated_at  DATETIME,
        PRIMARY KEY (user_id, agent_id)
    )
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any


class BaseProfileStore(ABC):
    """用户档案存储的抽象基类。"""

    # === 生命周期 ===

    @abstractmethod
    async def init_schema(self) -> None:
        """初始化表结构。"""
        ...

    # === 读取 ===

    @abstractmethod
    async def get_profile(
        self, user_id: str, agent_id: str
    ) -> dict[str, Any]:
        """
        获取某用户对某 Agent 的完整档案。

        返回值：字段字典，如 {"nickname": "老板", "birthday": "5月3日"}
        空档案返回 {}。
        """
        ...

    # === 写入 ===

    @abstractmethod
    async def update_profile(
        self,
        user_id: str,
        agent_id: str,
        updates: dict[str, str],
    ) -> None:
        """
        合并更新档案字段。

        将 updates 中的 key-value 合并到现有档案中（已有则覆盖，新增则追加）。
        不影响 updates 中未提及的字段。
        """
        ...

    @abstractmethod
    async def replace_profile(
        self,
        user_id: str,
        agent_id: str,
        data: dict[str, str],
    ) -> None:
        """
        整体替换档案（用户手动编辑场景）。
        """
        ...

    # === 删除 ===

    @abstractmethod
    async def delete_field(
        self, user_id: str, agent_id: str, field: str
    ) -> bool:
        """删除一个字段（从 JSON 中移除该 key）。"""
        ...

    @abstractmethod
    async def clear_all(
        self, user_id: str, agent_id: str
    ) -> bool:
        """清空某用户的全部档案。"""
        ...

    # === 工具方法 ===

    async def to_prompt_text(
        self, user_id: str, agent_id: str
    ) -> str:
        """
        将档案格式化为可直接注入 system prompt 的文本。

        示例输出：
            关于用户：
            - 称呼: 老板
            - 生日: 5月3日
            - 最爱角色: 枫原万叶
        """
        data = await self.get_profile(user_id, agent_id)
        if not data:
            return ""
        lines = ["关于用户："]
        for key, value in data.items():
            lines.append(f"- {key}: {value}")
        return "\n".join(lines)
