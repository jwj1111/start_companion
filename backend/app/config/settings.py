"""
应用配置 —— 集中式配置管理。

加载优先级（高覆盖低）：
    环境变量  >  .env 文件  >  config.yaml  >  代码默认值

职责划分：
    config.yaml  → 结构化配置（模型池、角色映射、策略参数），可提交 Git
    .env         → 敏感凭据（各模型的 API Key、数据库密码），不提交 Git
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from loguru import logger
from pydantic_settings import BaseSettings

# 项目根路径
BACKEND_ROOT = Path(__file__).parent.parent.parent
CONFIG_DIR = BACKEND_ROOT / "app" / "config"
PRESETS_DIR = BACKEND_ROOT / "presets"
CUSTOM_DIR = BACKEND_ROOT / "custom"
KNOWLEDGE_DIR = BACKEND_ROOT / "knowledge"


# ============================================================
# YAML 加载
# ============================================================

def _load_yaml_config() -> dict[str, Any]:
    """
    加载 config.yaml。

    查找顺序：
    1. 环境变量 CONFIG_PATH 指定的路径
    2. backend/app/config/config.yaml
    3. 都找不到则返回空字典
    """
    custom_path = os.environ.get("CONFIG_PATH")
    path = Path(custom_path) if custom_path else CONFIG_DIR / "config.yaml"

    if not path.exists():
        logger.info(f"未找到 config.yaml ({path})，使用默认配置")
        return {}

    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    logger.info(f"已加载配置: {path}")
    return data


_yaml = _load_yaml_config()


def _y(*keys: str, default: Any = None) -> Any:
    """从 YAML 嵌套结构中安全取值。"""
    node = _yaml
    for k in keys:
        if not isinstance(node, dict):
            return default
        node = node.get(k)
        if node is None:
            return default
    return node


# ============================================================
# 模型池解析
# ============================================================

def resolve_model_config(pool_name: str) -> dict[str, Any]:
    """
    从模型池中解析一个模型的完整配置。

    流程：
    1. 从 YAML 的 model_pool.{pool_name} 读取选型信息
    2. 通过 api_key_env / base_url_env 从 .env / 环境变量 读取密钥
    3. 合并为一个完整的 dict 返回

    返回示例：
    {
        "provider": "openai",
        "model": "gpt-4o",
        "api_key": "sk-xxx",
        "base_url": "",
        "temperature": 0.8,
        "max_tokens": 4096,
    }
    """
    pool = _y("model_pool", pool_name)
    if pool is None:
        raise ValueError(f"模型池中不存在: {pool_name}")

    config: dict[str, Any] = {
        "provider": pool.get("provider", "openai"),
        "model": pool.get("model", ""),
    }

    # 从环境变量解析密钥
    if key_env := pool.get("api_key_env"):
        config["api_key"] = os.environ.get(key_env, "")
    else:
        config["api_key"] = ""

    if url_env := pool.get("base_url_env"):
        config["base_url"] = os.environ.get(url_env, "")
    else:
        config["base_url"] = ""

    # 透传其他参数（temperature / max_tokens / device 等）
    passthrough_keys = {"temperature", "max_tokens", "device"}
    for k in passthrough_keys:
        if k in pool:
            config[k] = pool[k]

    return config


def resolve_role(role: str) -> dict[str, Any]:
    """
    按角色名解析模型配置。

    流程：model_roles.{role} → 模型池名 → resolve_model_config()
    """
    pool_name = _y("model_roles", role)
    if pool_name is None:
        raise ValueError(
            f"角色 '{role}' 未在 model_roles 中定义。"
            f"已定义的角色: {list((_y('model_roles') or {}).keys())}"
        )
    return resolve_model_config(pool_name)


# ============================================================
# Settings 类（非模型相关的配置）
# ============================================================

class Settings(BaseSettings):
    """
    应用配置（不含模型层）。

    模型配置通过 resolve_role() / resolve_model_config() 动态获取，
    不在 Settings 里写死字段。
    """

    # === 应用 ===
    environment: str = _y("app", "environment", default="development")
    debug: bool = _y("app", "debug", default=True)
    host: str = _y("app", "host", default="0.0.0.0")
    port: int = _y("app", "port", default=8000)
    cors_origins: list[str] = _y(
        "app", "cors_origins",
        default=["http://localhost:5173", "http://localhost:3000"],
    )

    # === 记忆层 - 向量数据库 ===
    vector_db_type: str = _y("memory", "vector_store", "type", default="qdrant")
    vector_db_url: str = ""      # .env: VECTOR_DB_URL
    vector_db_api_key: str = ""  # .env: VECTOR_DB_API_KEY

    # === 记忆层 - 关系型存储 ===
    relational_db_type: str = _y("memory", "relational", "type", default="sqlite")
    sqlite_db_path: str = _y("memory", "relational", "sqlite_path", default="data/companion.db")
    mysql_host: str = "localhost"
    mysql_port: int = 3306
    mysql_database: str = "start_companion"
    mysql_username: str = "root"
    mysql_password: str = ""

    # === 记忆层 - 策略 ===
    short_term_turns_threshold: int = _y("memory", "short_term", "turns_threshold", default=20)
    short_term_keep_recent: int = _y("memory", "short_term", "keep_recent_turns", default=10)
    long_term_importance_threshold: float = _y("memory", "long_term", "importance_threshold", default=0.3)
    long_term_auto_approve: bool = _y("memory", "long_term", "auto_approve_extracted", default=False)
    long_term_recall_limit: int = _y("memory", "long_term", "default_recall_limit", default=5)
    long_term_score_threshold: float = _y("memory", "long_term", "score_threshold", default=0.5)
    retrieval_gate_strategy: str = _y("memory", "retrieval_gate", "strategy", default="rule_based")
    extraction_trigger: str = _y("memory", "extraction", "trigger", default="on_summary_compress")

    # === 语音服务 ===
    asr_provider: str = _y("voice", "asr", "provider", default="whisper_api")
    asr_api_key: str = ""
    asr_base_url: str = ""
    tts_provider: str = _y("voice", "tts", "provider", default="edge_tts")
    tts_voice_id: str = _y("voice", "tts", "voice_id", default="zh-CN-XiaoxiaoNeural")
    tts_api_key: str = ""
    tts_base_url: str = ""

    # === 联网搜索 ===
    web_search_provider: str = _y("services", "web_search", "provider", default="tavily")
    web_search_api_key: str = ""

    class Config:
        env_file = ".env"
        env_prefix = ""

    @property
    def yaml_raw(self) -> dict[str, Any]:
        """获取 YAML 配置的原始字典。"""
        return _yaml


@lru_cache
def get_settings() -> Settings:
    """获取缓存的单例配置对象。"""
    return Settings()
