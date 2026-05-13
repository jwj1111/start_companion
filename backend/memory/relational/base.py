"""
记忆卡片关系型存储的抽象基类。

所有读写操作必须在接口层强制要求 user_id，
实现类在查询时自动加入 WHERE user_id = ? 过滤。
"""

from abc import ABC, abstractmethod

from memory.schema import MemoryCard, MemoryCardStatus


class BaseCardStore(ABC):
    """
    记忆卡片的关系型存储接口。

    用户隔离：所有操作必须传入 user_id，实现层强制过滤。
    """

    # === 生命周期 ===

    @abstractmethod
    async def init_schema(self) -> None:
        """初始化数据库结构（建表）。"""
        ...

    # === CRUD ===

    @abstractmethod
    async def create(self, card: MemoryCard) -> str:
        """插入一张新卡片，返回其 id。"""
        ...

    @abstractmethod
    async def get(self, user_id: str, card_id: str) -> MemoryCard | None:
        """按 id 获取一张卡片，user_id 用于隔离校验。"""
        ...

    @abstractmethod
    async def update(
        self,
        user_id: str,
        card_id: str,
        updates: dict,
    ) -> bool:
        """更新卡片字段，返回是否成功。"""
        ...

    @abstractmethod
    async def delete(self, user_id: str, card_id: str) -> bool:
        """删除一张卡片。"""
        ...

    # === 查询 ===

    @abstractmethod
    async def list_cards(
        self,
        user_id: str,
        agent_id: str | None = None,
        status: MemoryCardStatus | None = None,
        tags: list[str] | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[MemoryCard]:
        """按条件列出卡片（分页）。"""
        ...

    @abstractmethod
    async def count(
        self,
        user_id: str,
        agent_id: str | None = None,
        status: MemoryCardStatus | None = None,
    ) -> int:
        """统计符合条件的卡片数量。"""
        ...

    @abstractmethod
    async def get_by_ids(
        self,
        user_id: str,
        card_ids: list[str],
    ) -> list[MemoryCard]:
        """批量获取多张卡片（用于向量检索后回填完整数据）。"""
        ...

    # === 统计与元信息 ===

    @abstractmethod
    async def bump_recall_stats(self, user_id: str, card_ids: list[str]) -> None:
        """
        更新召回统计信息 —— recall_count +1，last_recalled_at = now。
        用于记忆热度排序和整合决策。
        """
        ...
