"""关系型卡片存储工厂。"""

from loguru import logger

from memory.relational.base import BaseCardStore
from app.config.settings import get_settings


def get_card_store() -> BaseCardStore:
    """按配置获取卡片存储实例。"""
    settings = get_settings()
    db_type = getattr(settings, "relational_db_type", "sqlite")

    if db_type == "mysql":
        from memory.relational.mysql_store import MysqlCardStore

        logger.debug("创建卡片存储: mysql")
        return MysqlCardStore(
            host=getattr(settings, "mysql_host", "localhost"),
            port=getattr(settings, "mysql_port", 3306),
            database=getattr(settings, "mysql_database", "start_companion"),
            username=getattr(settings, "mysql_username", "root"),
            password=getattr(settings, "mysql_password", ""),
        )

    else:
        # 默认 sqlite
        from memory.relational.sqlite_store import SqliteCardStore

        logger.debug(f"创建卡片存储: sqlite, path={settings.sqlite_db_path}")
        return SqliteCardStore(db_path=settings.sqlite_db_path)
