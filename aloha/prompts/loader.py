"""Prompt Loader - Prompt 文件加载器

参照 nanobot 设计，统一的 prompt 文件加载器。
支持从多个搜索路径加载标准 prompt 文件。
"""

from pathlib import Path
from typing import Any

# 标准 prompt 文件名清单（按加载顺序）
PROMPT_FILES = ["SOUL", "AGENT", "RULES", "SYSTEM", "USER"]

# 默认搜索路径
DEFAULT_SEARCH_PATHS = [
    Path("./prompts"),  # 项目根目录
    Path("~/.aloha/workspace").expanduser(),  # 用户 workspace 目录
]


class PromptLoader:
    """统一的 Prompt 加载器

    加载所有标准的 md 文件（SOUL.md, AGENT.md 等），
    并按顺序拼接构建 system prompt。

    遵循"约定大于配置"原则：标准文件名自动发现加载。
    遵循"DRY"原则：统一加载逻辑，避免重复代码。
    """

    def __init__(self, search_paths: list[Path] | None = None):
        """初始化加载器

        Args:
            search_paths: 自定义搜索路径列表。如果为 None，使用默认路径。
        """
        self.search_paths = search_paths or DEFAULT_SEARCH_PATHS

    def load(self, name: str) -> str | None:
        """加载指定名称的 prompt 文件

        Args:
            name: 文件名（不含 .md 后缀），如 "AGENT"、"USER"

        Returns:
            文件内容，如果文件不存在则返回 None
        """
        filename = f"{name}.md"
        for search_path in self.search_paths:
            if not search_path.exists():
                continue
            file_path = search_path / filename
            if file_path.exists() and file_path.is_file():
                try:
                    return file_path.read_text(encoding="utf-8")
                except UnicodeDecodeError:
                    # 尝试其他编码
                    try:
                        return file_path.read_text(encoding="gbk")
                    except Exception:
                        continue
                except Exception:
                    continue
        return None

    def load_all(self) -> dict[str, str]:
        """加载所有约定的 prompt 文件

        Returns:
            字典，key 为文件名（不含 .md），value 为文件内容
        """
        result: dict[str, str] = {}
        for name in PROMPT_FILES:
            content = self.load(name)
            if content:
                result[name] = content
        return result

    def build_system_prompt(self) -> str:
        """按顺序拼接所有 prompt 文件构建 system prompt

        按 SOUL -> AGENT -> RULES -> SYSTEM -> USER 顺序拼接。
        跳过不存在的文件。

        Returns:
            拼接后的 system prompt 字符串
        """
        prompts = self.load_all()
        if not prompts:
            return ""

        parts: list[str] = []
        for name in PROMPT_FILES:
            if name in prompts and prompts[name].strip():
                parts.append(f"# {name}\n{prompts[name].strip()}")

        return "\n\n---\n\n".join(parts)

    def list_available(self) -> list[dict[str, Any]]:
        """列出所有可用的 prompt 文件

        Returns:
            可用文件列表，每项包含 name、path、exists 信息
        """
        result: list[dict[str, Any]] = []
        for name in PROMPT_FILES:
            content = self.load(name)
            result.append({
                "name": name,
                "file": f"{name}.md",
                "exists": content is not None,
                "empty": content is None or not content.strip(),
            })
        return result

    @classmethod
    def get_default_prompts_dir(cls) -> Path:
        """获取默认的 prompts 目录路径

        Returns:
            默认 prompts 目录路径（workspace 目录）
        """
        return Path("~/.aloha/workspace").expanduser()

    @classmethod
    def ensure_prompts_dir(cls) -> Path:
        """确保默认 prompts 目录存在

        Returns:
            prompts 目录路径
        """
        prompts_dir = cls.get_default_prompts_dir()
        prompts_dir.mkdir(parents=True, exist_ok=True)
        return prompts_dir
