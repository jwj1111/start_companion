"""
用户自定义空间。

本目录存放用户的个性化覆盖配置。
其结构与 presets/ 相似，但仅包含用户主动修改过的字段。

目录结构：
    custom/
    ├── {user_id}/
    │   ├── agents/
    │   │   ├── {agent_id}/
    │   │   │   ├── persona_overrides.yaml  # 用户对人设的微调
    │   │   │   └── config_overrides.yaml   # 用户对配置的微调
    │   │   └── ...
    │   └── preferences.yaml                # 用户全局偏好
    └── ...

加载逻辑：
    final_config = deep_merge(preset_config, user_custom_config)

重要：
- 本目录与 presets/ 完全隔离；
- 开发者更新预设不会影响用户自定义；
- 用户自定义只作为叠加层，永远不会修改基底预设。
"""
