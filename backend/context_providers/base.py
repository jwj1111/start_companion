"""
Context Provider 抽象基类。

每个 Provider 必须实现：
- name: 唯一标识，也是 context_parts 字典中的 key
- group: STATIC（固定）或 DYNAMIC（每轮变化）
- should_run(): 本轮是否需要执行
- run(): 执行逻辑，返回文本或 None
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any


class ProviderGroup(str, Enum):
    """Provider 分组 —— 决定在双SP模式下归属哪个 SystemMessage。"""

    STATIC = "static"    # 固定内容（人设、准则），可缓存
    DYNAMIC = "dynamic"  # 每轮可能变化（档案、记忆）


class BaseContextProvider(ABC):
    """
    背景上下文提供者的抽象基类。

    子类需要实现：
    - name (class var): 唯一名称标识
    - group (class var): STATIC 或 DYNAMIC
    - should_run(): 判断本轮是否需要执行
    - run(): 执行并返回文本

    约定：
    - run() 返回 None 或空字符串表示本轮不提供内容
    - Provider 之间互相独立，不应有依赖关系
    - 每个 Provider 内部可以有自己的 Gate / 缓存 / 子流程
    """

    # 子类必须覆盖
    name: str = ""
    group: ProviderGroup = ProviderGroup.DYNAMIC

    def __init__(self, agent_config: dict[str, Any]):
        """
        初始化 Provider。

        Args:
            agent_config: Agent 配置（预设 + 用户微调合并后的结果）
        """
        self.agent_config = agent_config

    @abstractmethod
    async def should_run(self, state: dict[str, Any]) -> bool:
        """
        判断本轮是否需要执行此 Provider。

        轻量判断，不应有 IO 操作（或极轻量的 IO）。
        返回 False 时 run() 不会被调用。
        """
        ...

    @abstractmethod
    async def run(self, state: dict[str, Any]) -> str | None:
        """
        执行 Provider 逻辑，返回要注入 SP 的文本。

        返回 None 或 "" 表示本轮无内容可提供。
        """
        ...

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name='{self.name}' group='{self.group.value}'>"
