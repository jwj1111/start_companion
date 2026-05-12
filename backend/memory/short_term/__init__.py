"""
短期记忆子模块 —— 滚动窗口 + 按轮次触发的摘要替换。

核心策略：
- 对话轮次未达阈值：原样传递所有消息
- 对话轮次达到阈值：把最老的一批消息送给 LLM 摘要，
  用摘要块替换原始消息，保持整体消息数可控

效果示意：

    [User1, AI1, User2, AI2, ..., User20, AI20]     # 超过阈值
                    ↓ 触发压缩
    [Summary_of_1_to_10, User11, AI11, ..., User20, AI20]
                    ↓ 再对话若干轮后再次触发
    [Summary_of_1_to_20, User21, AI21, ..., User30, AI30]

摘要块是一条特殊的 SystemMessage / HumanMessage，
内容形如："[历史摘要] 早些时候 Alice 告诉我她喜欢用万叶，
          后来我们讨论了深渊挑战的配队..."
"""

from memory.short_term.summarizer import ShortTermSummarizer
from memory.short_term.window import ConversationWindow

__all__ = ["ShortTermSummarizer", "ConversationWindow"]
