"""记忆功能配置管理模块"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml


# 用户目录下的记忆文件路径
USER_MEMORY_DIR = os.path.expanduser("~/.roo/skills/memory")

DEFAULT_CONFIG: dict[str, Any] = {
    "memory": {
        "longterm_path": os.path.join(USER_MEMORY_DIR, "longterm.md"),
        "session_path": os.path.join(USER_MEMORY_DIR, "session.md"),
        "config_path": os.path.join(USER_MEMORY_DIR, "config.yaml"),
        "auto_load": True,
        "auto_save": True,
        "ignore_patterns": [
            "*.min.js",
            "*.pyc",
            "__pycache__",
            "node_modules",
            ".git",
            "*.ico",
            "*.png",
            "*.jpg",
            "*.lock",
        ],
    }
}


class MemoryConfig:
    """记忆功能配置类"""

    def __init__(self, workspace_root: str | None = None):
        self.workspace_root = workspace_root or os.getcwd()
        self._config: dict[str, Any] = {}
        # 优先使用用户目录下的配置
        self._config_file = os.path.expanduser("~/.roo/skills/memory/config.yaml")

    def load(self) -> dict[str, Any]:
        """加载配置文件，不存在则创建默认配置"""
        if os.path.exists(self._config_file):
            with open(self._config_file, "r", encoding="utf-8") as f:
                self._config = yaml.safe_load(f) or {}
        else:
            self._config = DEFAULT_CONFIG.copy()
            self._ensure_dir()
            self.save()
        return self._config

    def save(self) -> None:
        """保存配置到文件"""
        self._ensure_dir()
        with open(self._config_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(self._config, f, allow_unicode=True, default_flow_style=False)

    def _ensure_dir(self) -> None:
        """确保配置目录存在"""
        Path(self._config_file).parent.mkdir(parents=True, exist_ok=True)

    def get_longterm_path(self) -> str:
        """获取长期记忆文件路径（用户目录）"""
        return self._config.get("memory", {}).get("longterm_path") or os.path.expanduser("~/.roo/skills/memory/longterm.md")

    def get_session_path(self) -> str:
        """获取会话记忆文件路径（用户目录）"""
        return self._config.get("memory", {}).get("session_path") or os.path.expanduser("~/.roo/skills/memory/session.md")

    def is_auto_load(self) -> bool:
        """是否自动加载记忆"""
        return self._config.get("memory", {}).get("auto_load", True)

    def is_auto_save(self) -> bool:
        """是否自动保存记忆"""
        return self._config.get("memory", {}).get("auto_save", True)

    def get_ignore_patterns(self) -> list[str]:
        """获取忽略文件模式"""
        return self._config.get("memory", {}).get("ignore_patterns", [])

    def should_ignore(self, file_path: str) -> bool:
        """检查文件是否应该被忽略"""
        import fnmatch

        filename = os.path.basename(file_path)
        patterns = self.get_ignore_patterns()
        return any(fnmatch.fnmatch(filename, pattern) for pattern in patterns)


def get_config(workspace_root: str | None = None) -> MemoryConfig:
    """获取配置单例"""
    return MemoryConfig(workspace_root)
