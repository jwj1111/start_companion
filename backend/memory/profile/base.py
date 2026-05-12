"""
用户档案存储的抽象基类。

采用 EAV（Entity-Attribute-Value）模式：
- 字段完全自由，加新字段不用改表结构
- 不同 Agent 可以有不同字段集
- 一个 (user_id, agent_id, field) 只有一个最新值

表结构：
    user_profiles (
        user_id     TEXT NOT NULL,
        agent_id    TEXT NOT NULL,
        field       TEXT NOT NULL,       -- 字段名: "nickname" / "birthday" / ...
        value       TEXT,                -- 字段值: "老板" / "5月3日" / ...
        source      TEXT,                -- "llm_extracted" / "user_manual"
        updated_at  DATETIME,
        PRIMARY KEY (user_id, agent_id, field)
    )
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class ProfileField:
    """档案中的一个字段。"""
    field: str
    value: str
    source: str         # "llm_extracted" / "user_manual" / "system"
    updated_at: datetime


class BaseProfileStore(ABC):
    """用户档案存储的抽象基类。"""

    # === 生命周期 ===

    @abstractmethod
    async def init_schema(self) -> None:
        """初始化表结构。"""
        ...

    # === 读取 ===

    @abstractmethod
    async def get_all(
        self, user_id: str, agent_id: str
    ) -> dict[str, ProfileField]:
        """
        获取某用户对某 Agent 的完整档案。

        返回值：{field_name: ProfileField} 字典
        """
        ...

    @abstractmethod
    async def get_field(
        self, user_id: str, agent_id: str, field: str
    ) -> ProfileField | None:
        """获取单个字段值。"""
        ...

    # === 写入 ===

    @abstractmethod
    async def set_field(
        self,
        user_id: str,
        agent_id: str,
        field: str,
        value: str,
        source: str = "llm_extracted",
    ) -> None:
        """
        设置一个字段值（UPSERT：存在则覆盖，不存在则创建）。
        """
        ...

    @abstractmethod
    async def set_fields(
        self,
        user_id: str,
        agent_id: str,
        updates: dict[str, str],
        source: str = "llm_extracted",
    ) -> None:
        """批量设置多个字段（原子操作）。"""
        ...

    # === 删除 ===

    @abstractmethod
    async def delete_field(
        self, user_id: str, agent_id: str, field: str
    ) -> bool:
        """删除一个字段。"""
        ...

    @abstractmethod
    async def clear_all(
        self, user_id: str, agent_id: str
    ) -> int:
        """清空某用户的全部档案，返回删除条数。"""
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
            - 当前心情: 开心
        """
        fields = await self.get_all(user_id, agent_id)
        if not fields:
            return ""
        lines = ["关于用户："]
        for name, pf in fields.items():
            lines.append(f"- {name}: {pf.value}")
        return "\n".join(lines)
