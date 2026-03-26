"""FileTool - 文件读写工具

提供安全的文件读写操作。
"""

from pathlib import Path
from aloha.agent.tools import BaseTool, ToolResult


class FileTool(BaseTool):
    """文件读写工具

    支持读取和写入文件，可配置目录白名单限制。
    """

    def __init__(self, allowed_read_dirs: list[Path] | None = None, allowed_write_dirs: list[Path] | None = None):
        super().__init__(
            name="file",
            description="读取或写入文件内容",
        )
        self.allowed_read_dirs = allowed_read_dirs or [Path.cwd()]
        self.allowed_write_dirs = allowed_write_dirs or [Path.cwd() / "output"]

    async def execute(self, operation: str, path: str, content: str = "") -> ToolResult:
        """执行文件操作"""
        if operation == "read":
            return await self._read_file(path)
        elif operation == "write":
            return await self._write_file(path, content)
        return ToolResult(success=False, content="", error="Invalid operation. Use 'read' or 'write'.")

    async def _read_file(self, path: str) -> ToolResult:
        """读取文件"""
        try:
            file_path = Path(path).resolve()

            # 检查是否在允许的目录内
            if not self._is_in_allowed_dirs(file_path, self.allowed_read_dirs):
                return ToolResult(
                    success=False,
                    content="",
                    error=f"Path not in allowed read directories: {path}",
                )

            if not file_path.exists():
                return ToolResult(success=False, content="", error="File not found")

            if not file_path.is_file():
                return ToolResult(success=False, content="", error="Path is not a file")

            content = file_path.read_text(encoding="utf-8")
            return ToolResult(success=True, content=content)
        except PermissionError:
            return ToolResult(success=False, content="", error="Permission denied")
        except Exception as e:
            return ToolResult(success=False, content="", error=str(e))

    async def _write_file(self, path: str, content: str) -> ToolResult:
        """写入文件"""
        try:
            file_path = Path(path).resolve()

            # 检查是否在允许的目录内
            if not self._is_in_allowed_dirs(file_path, self.allowed_write_dirs):
                return ToolResult(
                    success=False,
                    content="",
                    error=f"Path not in allowed write directories: {path}",
                )

            # 检查文件扩展名
            blocked_extensions = [".exe", ".dll", ".so", ".sh", ".bat", ".cmd"]
            if file_path.suffix.lower() in blocked_extensions:
                return ToolResult(
                    success=False,
                    content="",
                    error=f"File extension {file_path.suffix} is blocked for security",
                )

            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")
            return ToolResult(success=True, content=f"Successfully written to {path}")
        except PermissionError:
            return ToolResult(success=False, content="", error="Permission denied")
        except Exception as e:
            return ToolResult(success=False, content="", error=str(e))

    def _is_in_allowed_dirs(self, path: Path, allowed_dirs: list[Path]) -> bool:
        """检查路径是否在允许的目录列表中"""
        try:
            path.resolve().relative_to(Path.cwd().resolve())
            for allowed_dir in allowed_dirs:
                try:
                    path.resolve().relative_to(allowed_dir.resolve())
                    return True
                except ValueError:
                    continue
            return False
        except ValueError:
            return False

    def _get_parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "description": "操作类型: read 或 write",
                    "enum": ["read", "write"],
                },
                "path": {
                    "type": "string",
                    "description": "文件路径",
                },
                "content": {
                    "type": "string",
                    "description": "写入内容（仅 write 操作需要）",
                },
            },
            "required": ["operation", "path"],
        }