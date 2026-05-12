"""
基于 SQLite（aiosqlite）的记忆卡片存储实现。

表结构：
    memory_cards (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        agent_id TEXT NOT NULL,
        content TEXT NOT NULL,
        category TEXT NOT NULL,
        tags TEXT,                    -- JSON array
        importance REAL,
        status TEXT NOT NULL,
        source TEXT,
        source_session_id TEXT,
        source_message_ids TEXT,      -- JSON array
        user_edited INTEGER,
        editable INTEGER,
        created_at TEXT,
        updated_at TEXT,
        last_recalled_at TEXT,
        recall_count INTEGER,
        expires_at TEXT,
        vector_id TEXT,
        metadata TEXT                 -- JSON
    )

索引：
    idx_user_agent (user_id, agent_id)
    idx_user_status (user_id, status)
"""

from memory.relational.base import BaseCardStore
from memory.schema import MemoryCard, MemoryCardStatus, MemoryCategory


class SqliteCardStore(BaseCardStore):
    """基于 SQLite 的记忆卡片存储。"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._conn = None

    async def _get_conn(self):
        """懒初始化连接。"""
        # TODO: 使用 aiosqlite.connect(self.db_path)
        raise NotImplementedError

    # === 生命周期 ===

    async def init_schema(self) -> None:
        """创建表与索引。"""
        # TODO: 执行建表 SQL
        raise NotImplementedError

    # === CRUD ===

    async def create(self, card: MemoryCard) -> str:
        # TODO: INSERT INTO memory_cards ...
        raise NotImplementedError

    async def get(self, user_id: str, card_id: str) -> MemoryCard | None:
        # TODO: SELECT * FROM memory_cards WHERE id=? AND user_id=?
        raise NotImplementedError

    async def update(self, user_id: str, card_id: str, updates: dict) -> bool:
        # TODO: UPDATE memory_cards SET ... WHERE id=? AND user_id=?
        # 同时更新 updated_at
        raise NotImplementedError

    async def delete(self, user_id: str, card_id: str) -> bool:
        # TODO: DELETE FROM memory_cards WHERE id=? AND user_id=?
        raise NotImplementedError

    # === 查询 ===

    async def list_cards(
        self,
        user_id: str,
        agent_id: str | None = None,
        status: MemoryCardStatus | None = None,
        category: MemoryCategory | None = None,
        tags: list[str] | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[MemoryCard]:
        # TODO: 动态拼接 WHERE 子句
        raise NotImplementedError

    async def count(
        self,
        user_id: str,
        agent_id: str | None = None,
        status: MemoryCardStatus | None = None,
    ) -> int:
        # TODO: SELECT COUNT(*) ...
        raise NotImplementedError

    async def get_by_ids(
        self, user_id: str, card_ids: list[str]
    ) -> list[MemoryCard]:
        # TODO: SELECT * WHERE user_id=? AND id IN (...)
        raise NotImplementedError

    # === 统计 ===

    async def bump_recall_stats(self, user_id: str, card_ids: list[str]) -> None:
        # TODO: UPDATE memory_cards
        #       SET recall_count = recall_count + 1,
        #           last_recalled_at = ?
        #       WHERE user_id=? AND id IN (...)
        raise NotImplementedError

    # === 序列化工具 ===

    @staticmethod
    def _row_to_card(row: dict) -> MemoryCard:
        """把 DB 行转为 MemoryCard 实例。"""
        # TODO: JSON 反序列化 tags / source_message_ids / metadata
        #       解析 enum 字段
        #       解析 datetime 字段
        raise NotImplementedError

    @staticmethod
    def _card_to_row(card: MemoryCard) -> dict:
        """把 MemoryCard 转为 DB 行字典。"""
        # TODO: JSON 序列化
        raise NotImplementedError
