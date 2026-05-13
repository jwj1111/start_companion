"""
基于 MySQL（aiomysql）的记忆卡片存储实现。

表结构与 sqlite_store.py 保持一致，仅 SQL 方言和连接方式不同。

依赖：
    pip install aiomysql

配置示例（config.yaml）：
    relational:
      type: mysql
      host: "localhost"
      port: 3306
      database: "start_companion"
      username: "root"
      password: "xxx"
      pool_size: 10
"""

from memory.relational.base import BaseCardStore
from memory.schema import MemoryCard, MemoryCardStatus


class MysqlCardStore(BaseCardStore):
    """基于 MySQL 的记忆卡片存储。"""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 3306,
        database: str = "ai_companion",
        username: str = "root",
        password: str = "",
        pool_size: int = 10,
    ):
        self.host = host
        self.port = port
        self.database = database
        self.username = username
        self.password = password
        self.pool_size = pool_size
        self._pool = None

    async def _get_pool(self):
        """懒初始化连接池。"""
        # TODO: 使用 aiomysql.create_pool(...)
        raise NotImplementedError

    # === 生命周期 ===

    async def init_schema(self) -> None:
        """创建表与索引（如不存在）。"""
        # TODO: CREATE TABLE IF NOT EXISTS memory_cards (...)
        #   id VARCHAR(64) PRIMARY KEY,
        #   user_id VARCHAR(64) NOT NULL,
        #   agent_id VARCHAR(64) NOT NULL,
        #   content TEXT NOT NULL,
        #   tags JSON,
        #   status VARCHAR(32) NOT NULL,
        #   source VARCHAR(32),
        #   source_session_id VARCHAR(64),
        #   source_message_ids JSON,
        #   user_edited TINYINT(1),
        #   editable TINYINT(1),
        #   created_at DATETIME,
        #   updated_at DATETIME,
        #   last_recalled_at DATETIME,
        #   recall_count INT DEFAULT 0,
        #   expires_at DATETIME,
        #   vector_id VARCHAR(64),
        #   metadata JSON,
        #   INDEX idx_user_agent (user_id, agent_id),
        #   INDEX idx_user_status (user_id, status)
        # ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        raise NotImplementedError

    # === CRUD ===

    async def create(self, card: MemoryCard) -> str:
        # TODO: INSERT INTO memory_cards ...
        raise NotImplementedError

    async def get(self, user_id: str, card_id: str) -> MemoryCard | None:
        # TODO: SELECT * FROM memory_cards WHERE id=%s AND user_id=%s
        raise NotImplementedError

    async def update(self, user_id: str, card_id: str, updates: dict) -> bool:
        # TODO: UPDATE memory_cards SET ... WHERE id=%s AND user_id=%s
        raise NotImplementedError

    async def delete(self, user_id: str, card_id: str) -> bool:
        # TODO: DELETE FROM memory_cards WHERE id=%s AND user_id=%s
        raise NotImplementedError

    # === 查询 ===

    async def list_cards(
        self,
        user_id: str,
        agent_id: str | None = None,
        status: MemoryCardStatus | None = None,
        tags: list[str] | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[MemoryCard]:
        # TODO: 动态拼接 WHERE 子句 + LIMIT / OFFSET
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
        # TODO: SELECT * WHERE user_id=%s AND id IN (...)
        raise NotImplementedError

    # === 统计 ===

    async def bump_recall_stats(self, user_id: str, card_ids: list[str]) -> None:
        # TODO: UPDATE memory_cards
        #       SET recall_count = recall_count + 1,
        #           last_recalled_at = NOW()
        #       WHERE user_id=%s AND id IN (...)
        raise NotImplementedError
