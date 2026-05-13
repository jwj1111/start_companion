"""
用户档案的关系型存储实现。

与 memory_cards 表共用同一个数据库文件。
表名: user_profiles
存储方式: JSON 列（一行一用户，data 列存完整档案 JSON）

注意：该实现同时适用于 SQLite 和 MySQL，
SQL 方言差异通过占位符抽象（? vs %s）处理。
"""

from typing import Any

from memory.profile.base import BaseProfileStore


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
        #   user_id    TEXT NOT NULL,
        #   agent_id   TEXT NOT NULL,
        #   data       TEXT NOT NULL DEFAULT '{}',
        #   updated_at DATETIME,
        #   PRIMARY KEY (user_id, agent_id)
        # );
        raise NotImplementedError

    async def get_profile(
        self, user_id: str, agent_id: str
    ) -> dict[str, Any]:
        # TODO: SELECT data FROM user_profiles WHERE user_id=? AND agent_id=?
        #       → json.loads(row["data"]) 或 {} 如果不存在
        raise NotImplementedError

    async def update_profile(
        self,
        user_id: str,
        agent_id: str,
        updates: dict[str, str],
    ) -> None:
        # TODO:
        # 1. current = await self.get_profile(user_id, agent_id)
        # 2. merged = {**current, **updates}
        # 3. INSERT OR REPLACE INTO user_profiles (user_id, agent_id, data, updated_at)
        #    VALUES (?, ?, json.dumps(merged), NOW())
        raise NotImplementedError

    async def replace_profile(
        self,
        user_id: str,
        agent_id: str,
        data: dict[str, str],
    ) -> None:
        # TODO: INSERT OR REPLACE INTO user_profiles (user_id, agent_id, data, updated_at)
        #       VALUES (?, ?, json.dumps(data), NOW())
        raise NotImplementedError

    async def delete_field(
        self, user_id: str, agent_id: str, field: str
    ) -> bool:
        # TODO:
        # 1. current = await self.get_profile(user_id, agent_id)
        # 2. if field in current: del current[field]
        # 3. 写回
        raise NotImplementedError

    async def clear_all(
        self, user_id: str, agent_id: str
    ) -> bool:
        # TODO: DELETE FROM user_profiles WHERE user_id=? AND agent_id=?
        raise NotImplementedError
