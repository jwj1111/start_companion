"""
预设管理器 —— 加载并合并预设 + 用户自定义。

核心原则：预设是不可变的基底，用户自定义仅作为叠加层。
最终配置 = deep_merge(preset, user_custom)
"""

from pathlib import Path
from typing import Any
import yaml
from copy import deepcopy
from loguru import logger

from app.config.settings import PRESETS_DIR, CUSTOM_DIR


def deep_merge(base: dict, overlay: dict) -> dict:
    """
    将 overlay 深度合并到 base 上。
    overlay 中的值优先级更高。
    """
    result = deepcopy(base)
    for key, value in overlay.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = deepcopy(value)
    return result


class PresetManager:
    """管理 Agent 预设与用户自定义的加载与合并。"""

    def __init__(self):
        self.presets_dir = PRESETS_DIR / "agents"
        self.custom_dir = CUSTOM_DIR

    def list_agents(self) -> list[str]:
        """列出所有可用的 Agent 预设 ID。"""
        if not self.presets_dir.exists():
            return []
        return [d.name for d in self.presets_dir.iterdir() if d.is_dir()]

    def load_agent_config(
        self, agent_id: str, user_id: str | None = None
    ) -> dict[str, Any]:
        """
        加载完整的 Agent 配置（预设 + 用户微调）。

        参数：
            agent_id: Agent 预设 ID
            user_id: 可选，传入后会加载该用户的自定义配置

        返回值：
            合并后的完整配置字典
        """
        # 加载基底预设
        preset = self._load_preset(agent_id)

        if not user_id:
            return preset

        # 加载用户自定义覆盖
        overrides = self._load_user_overrides(agent_id, user_id)

        if not overrides:
            return preset

        # 校验用户仅覆盖了允许的字段
        allowed = preset.get("user_customizable_fields", [])
        # TODO: 根据 allowed 字段列表对 overrides 做校验

        # 合并
        merged = deep_merge(preset, overrides)
        logger.debug(f"已加载合并后的配置: agent={agent_id}, user={user_id}")
        return merged

    def save_user_overrides(
        self, agent_id: str, user_id: str, overrides: dict[str, Any]
    ) -> None:
        """保存用户的自定义覆盖。"""
        custom_path = self.custom_dir / user_id / "agents" / agent_id
        custom_path.mkdir(parents=True, exist_ok=True)

        persona_file = custom_path / "persona_overrides.yaml"
        with open(persona_file, "w", encoding="utf-8") as f:
            yaml.dump(overrides, f, allow_unicode=True, default_flow_style=False)

        logger.info(f"已保存用户自定义: user={user_id}, agent={agent_id}")

    def _load_preset(self, agent_id: str) -> dict[str, Any]:
        """加载某个 Agent 的基底预设文件。"""
        agent_dir = self.presets_dir / agent_id
        if not agent_dir.exists():
            raise FileNotFoundError(f"找不到预设: {agent_id}")

        config = {}
        for yaml_file in agent_dir.glob("*.yaml"):
            with open(yaml_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
                config = deep_merge(config, data)

        return config

    def _load_user_overrides(
        self, agent_id: str, user_id: str
    ) -> dict[str, Any] | None:
        """加载用户自定义覆盖文件。"""
        custom_dir = self.custom_dir / user_id / "agents" / agent_id
        if not custom_dir.exists():
            return None

        overrides = {}
        for yaml_file in custom_dir.glob("*_overrides.yaml"):
            with open(yaml_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
                overrides = deep_merge(overrides, data)

        return overrides if overrides else None
