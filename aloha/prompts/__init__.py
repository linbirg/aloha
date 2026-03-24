"""Prompts 模块 - Prompt 文件加载器

提供从文件系统加载 AGENT.md、USER.md、SOUL.md 等标准 prompt 文件的功能。

标准文件：
- SOUL.md: Agent 核心价值观/灵魂
- AGENT.md: Agent 角色定义
- RULES.md: 行为规则/约束
- SYSTEM.md: 系统级指令
- USER.md: 用户偏好/上下文
"""

from aloha.prompts.loader import PromptLoader

__all__ = ["PromptLoader"]
