"""
用户档案 (User Profile / State Table)。

结构化的确定性记忆：固定字段、覆盖更新、每轮全量注入 prompt。

触发方式：
- 读取: 每轮无条件注入 prompt（量小）
- 写入: 仅在 session_end 时统一提取（对话中靠上下文自然传递）

与记忆卡片的区别：
- 档案：键值对，精确取值，量小（几十个字段），每轮全量注入
- 卡片：自由文本，语义检索，量大（数百上千条），按需检索注入

存储：关系型数据库，EAV 模式（user_id + agent_id + field + value）

设计参考：
- KokoroMemo 的"状态板 (State Table)"
- Character.AI 的 User Persona
"""

from memory.profile.base import BaseProfileStore
from memory.profile.updater import ProfileUpdater

__all__ = ["BaseProfileStore", "ProfileUpdater"]
