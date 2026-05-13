"""
检索门控（Retrieval Gate）—— 判断本轮是否需要召回长期记忆。

设计说明（针对口语多模态游戏陪聊场景）：
- 长期记忆存的是用户的个人信息、偏好、过去的事件
- 大部分对话轮次不需要翻旧记忆（聊的是当前发生的事）
- 只有用户引用过去（"上次""记得""之前"）才需要搜

策略：默认不搜，含引用词才搜。
Gate 通过后，MemoryProvider 一律用 auxiliary 模型改写 query 再检索。
"""

from abc import ABC, abstractmethod

from loguru import logger


class BaseRetrievalGate(ABC):
    """检索门控的抽象基类。"""

    @abstractmethod
    async def should_retrieve(self, user_message: str) -> bool:
        """判断当前 user message 是否需要触发长期记忆召回。"""
        ...


class AlwaysRetrieveGate(BaseRetrievalGate):
    """总是召回 —— 用于测试/调试。"""

    async def should_retrieve(self, user_message: str) -> bool:
        return True


class RuleBasedGate(BaseRetrievalGate):
    """
    基于规则的门控 —— 生产环境默认使用。

    零延迟（纯字符串匹配），逻辑：
    - 含引用词 → 搜
    - 其余 → 不搜
    """

    REFERENCE_PATTERNS: set[str] = {
        "上次", "那个", "之前", "记得", "我说过", "还记得",
        "以前", "那天", "当时", "你忘了", "又", "跟之前",
    }

    async def should_retrieve(self, user_message: str) -> bool:
        msg = user_message.strip()
        for pattern in self.REFERENCE_PATTERNS:
            if pattern in msg:
                logger.debug(f"Gate: 引用词命中 '{pattern}'，触发召回")
                return True
        return False
