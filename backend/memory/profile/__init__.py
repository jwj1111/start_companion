"""
用户档案 (User Profile)。

结构化的确定性记忆：JSON 列存储，覆盖更新，每轮全量注入 prompt。

存储方式：关系型数据库，JSON 列（一行一用户，data 存完整档案 JSON）

触发方式：
- 读取: 每轮由 ProfileProvider 全量注入 SP（一行查询，很快）
- 写入: 仅在 session_end 时统一提取（对话中靠上下文自然传递）

与记忆卡片的区别：
- 档案：键值对 JSON，精确取值，量小（十几个字段），每轮全量注入
- 卡片：自由文本，语义检索，量大，按需检索注入

设计参考：
- KokoroMemo 的"状态板 (State Table)"
- EVE AI 的 128 记忆槽
"""

from memory.profile.base import BaseProfileStore
from memory.profile.updater import ProfileUpdater

__all__ = ["BaseProfileStore", "ProfileUpdater"]
