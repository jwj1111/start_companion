"""
开发者预设。

本目录存放由开发者定义的、**不可变**的预设配置。
用户不能修改本目录下的任何文件。

目录结构：
    presets/
    ├── agents/                  # Agent 角色预设
    │   ├── default/             # 默认通用伴侣
    │   │   ├── persona.yaml    # 人设 & 性格定义
    │   │   ├── prompts.yaml    # 系统提示词模板
    │   │   └── config.yaml     # Agent 行为配置
    │   ├── gaming_buddy/        # 游戏搭子
    │   └── ...
    ├── prompt_templates/        # 通用提示词模板
    └── strategies/              # 对话策略预设

加载优先级：preset（基底） -> user custom（叠加覆盖）
"""
