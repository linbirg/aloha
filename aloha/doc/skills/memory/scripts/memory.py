"""记忆核心模块 - 管理和持久化记忆"""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Any

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.analyzer import analyze_file, analyze_project_structure
from scripts.config import MemoryConfig


# 默认长期记忆模板
DEFAULT_LONGTERM_TEMPLATE = """# 长期记忆

## 代码风格
- 命名规范：
- 缩进：
- 注释风格：
- 其他：

## 技术栈
- 编程语言：
- 框架：
- 库：
- 工具：

## 项目结构
- 入口文件：
- 模块组织：
- 配置文件：

## 用户偏好
- 测试框架：
- 代码规范：
- 其他：

---

*最后更新: {timestamp}*
"""

# 默认会话记忆模板
DEFAULT_SESSION_TEMPLATE = """# 会话记忆 - {timestamp}

## 本次分析的代码特征

## 临时备注

---

"""


class MemoryManager:
    """记忆管理器"""

    def __init__(self, workspace_root: str | None = None):
        self.config = MemoryConfig(workspace_root)
        self.config.load()

    def _ensure_memory_dir(self) -> None:
        """确保记忆目录存在"""
        Path(self.config.get_longterm_path()).parent.mkdir(parents=True, exist_ok=True)

    def load_longterm(self) -> str:
        """加载长期记忆"""
        path = self.config.get_longterm_path()
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return f.read()

        # 创建默认记忆
        self._ensure_memory_dir()
        content = DEFAULT_LONGTERM_TEMPLATE.format(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        self.save_longterm(content)
        return content

    def load_session(self) -> str:
        """加载会话记忆"""
        path = self.config.get_session_path()
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return f.read()

        # 创建默认记忆
        content = DEFAULT_SESSION_TEMPLATE.format(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        self.save_session(content)
        return content

    def save_longterm(self, content: str) -> None:
        """保存长期记忆"""
        self._ensure_memory_dir()
        with open(self.config.get_longterm_path(), "w", encoding="utf-8") as f:
            f.write(content)

    def save_session(self, content: str) -> None:
        """保存会话记忆"""
        self._ensure_memory_dir()
        with open(self.config.get_session_path(), "w", encoding="utf-8") as f:
            f.write(content)

    def clear_session(self) -> str:
        """清除会话记忆"""
        content = DEFAULT_SESSION_TEMPLATE.format(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        self.save_session(content)
        return content

    def merge_to_longterm(self) -> str:
        """将会话记忆合并到长期记忆"""
        longterm = self.load_longterm()
        session = self.load_session()

        # 提取会话中的有用信息并追加到长期记忆
        # 简单实现：追加会话内容到长期记忆
        merged = longterm + "\n\n---\n\n" + session

        # 更新长期记忆
        merged = merged.replace(
            "*最后更新: *",
            f"*最后更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*"
        )

        self.save_longterm(merged)

        # 清除会话
        self.clear_session()

        return merged

    def show_memory(self, memory_type: str = "both") -> str:
        """显示记忆内容"""
        result = []

        if memory_type in ("both", "longterm"):
            result.append("=" * 40)
            result.append("长期记忆")
            result.append("=" * 40)
            result.append(self.load_longterm())

        if memory_type in ("both", "session"):
            result.append("")
            result.append("=" * 40)
            result.append("会话记忆")
            result.append("=" * 40)
            result.append(self.load_session())

        return "\n".join(result)

    def analyze_and_update(self, file_path: str) -> dict[str, Any]:
        """分析文件并更新记忆"""
        if self.config.should_ignore(file_path):
            return {"status": "ignored", "reason": "File matches ignore pattern"}

        # 分析文件
        analysis = analyze_file(file_path)

        if "error" in analysis:
            return analysis

        # 构建记忆更新内容
        updates = self._build_memory_update(analysis)

        # 读取现有记忆
        session = self.load_session()

        # 追加新分析结果
        new_session = session.rstrip() + "\n\n---\n\n" + f"## {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: {os.path.basename(file_path)}\n"

        for key, value in updates.items():
            new_session += f"- {key}: {value}\n"

        self.save_session(new_session)

        return {
            "status": "success",
            "file": file_path,
            "analysis": analysis,
            "updates": updates,
        }

    def _build_memory_update(self, analysis: dict[str, Any]) -> dict[str, str]:
        """从分析结果构建记忆更新内容"""
        updates: dict[str, str] = {}

        if "language" in analysis:
            updates["语言"] = analysis["language"]

        if "indent_style" in analysis:
            indent = analysis["indent_style"]
            if indent["type"] == "spaces":
                updates["缩进"] = f"{indent['size']} 空格"
            elif indent["type"] == "tabs":
                updates["缩进"] = "Tab"
            else:
                updates["缩进"] = "未知"

        if "naming_conventions" in analysis:
            updates["命名规范"] = ", ".join(analysis["naming_conventions"])

        if "frameworks" in analysis and analysis["frameworks"]:
            updates["框架/库"] = ", ".join(analysis["frameworks"])

        return updates

    def get_memory_summary(self) -> dict[str, Any]:
        """获取记忆摘要"""
        longterm = self.load_longterm()
        session = self.load_session()

        return {
            "longterm_path": self.config.get_longterm_path(),
            "session_path": self.config.get_session_path(),
            "longterm_size": len(longterm),
            "session_size": len(session),
            "auto_load": self.config.is_auto_load(),
            "auto_save": self.config.is_auto_save(),
        }


def get_memory_manager(workspace_root: str | None = None) -> MemoryManager:
    """获取记忆管理器实例"""
    return MemoryManager(workspace_root)
