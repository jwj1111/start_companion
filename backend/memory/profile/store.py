"""
用户档案的关系型存储实现。

与 memory_cards 表共用同一个数据库连接。
表名: user_profiles

注意：该实现同时适用于 SQLite 和 MySQL，
SQL 方言差异通过占位符抽象（? vs %s）处理。
"""

from memory.profile.base import BaseProfileStore, ProfileField
from memory.schema import MemoryCardStatus


class RelationalProfileStore(BaseProfileStore):
    """
    基于关系型数据库（SQLite / MySQL）的档案存储。

    通过注入的 db_connection 适配不同数据库。
    """

    def __init__(self, db_connection):
        """
        参数：
            db_connection: 异步数据库连接（aiosqlite / aiomysql pool）
        """
        self._conn = db_connection

    async def init_schema(self) -> None:
        """建表。"""
        # TODO: CREATE TABLE IF NOT EXISTS user_profiles (
        #   user_id TEXT NOT NULL,
        #   agent_id TEXT NOT NULL,
        #   field TEXT NOT NULL,
        #   value TEXT,
        #   source TEXT DEFAULT 'llm_extracted',
        #   updated_at DATETIME,
        #   PRIMARY KEY (user_id, agent_id, field)
        # );
        raise NotImplementedError

    async def get_all(
        self, user_id: str, agent_id: str
    ) -> dict[str, ProfileField]:
        # TODO: SELECT * FROM user_profiles WHERE user_id=? AND agent_id=?
        raise NotImplementedError

    async def get_field(
        self, user_id: str, agent_id: str, field: str
    ) -> ProfileField | None:
        # TODO: SELECT * FROM user_profiles WHERE user_id=? AND agent_id=? AND field=?
        raise NotImplementedError

    async def set_field(
        self,
        user_id: str,
        agent_id: str,
        field: str,
        value: str,
        source: str = "llm_extracted",
    ) -> None:
        # TODO: INSERT OR REPLACE INTO user_profiles (user_id, agent_id, field, value, source, updated_at)
        #       VALUES (?, ?, ?, ?, ?, NOW())
        raise NotImplementedError

    async def set_fields(
        self,
        user_id: str,
        agent_id: str,
        updates: dict[str, str],
        source: str = "llm_extracted",
    ) -> None:
        # TODO: 批量 UPSERT，建议在事务中执行
        raise NotImplementedError

    async def delete_field(
        self, user_id: str, agent_id: str, field: str
    ) -> bool:
        # TODO: DELETE FROM user_profiles WHERE user_id=? AND agent_id=? AND field=?
        raise NotImplementedError

    async def clear_all(
        self, user_id: str, agent_id: str
    ) -> int:
        # TODO: DELETE FROM user_profiles WHERE user_id=? AND agent_id=?
        raise NotImplementedError
