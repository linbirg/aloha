"""ShellTool - 命令执行工具

提供安全的命令行执行功能，支持危险命令拦截和白名单控制。
"""

import asyncio
import shlex
from aloha.agent.tools import BaseTool, ToolResult


class ShellTool(BaseTool):
    """命令行执行工具

    支持白名单命令和黑名单模式检查，确保安全执行。
    """

    # 默认危险命令黑名单
    DEFAULT_BLOCKED_COMMANDS = {"rm", "del", "format", "shutdown", "reboot", "mkfs"}

    def __init__(
        self,
        allowed_commands: list[str] | None = None,
        blocked_patterns: list[str] | None = None,
    ):
        super().__init__(
            name="shell",
            description="执行命令行命令",
        )
        self.allowed_commands = allowed_commands or [
            "ls",
            "cat",
            "echo",
            "grep",
            "find",
            "git",
            "pwd",
            "cd",
            "mkdir",
            "cp",
            "mv",
            "rm",
            "head",
            "tail",
            "wc",
        ]
        self.blocked_patterns = blocked_patterns or [
            r"rm\s+-rf",
            r"del\s+/[sq]",
            r"format\s+[a-z]:",
            r">\s*/dev/",
        ]

    async def execute(self, command: str, timeout: int = 30) -> ToolResult:
        """执行命令"""
        # 安全检查
        if not self._is_safe_command(command):
            return ToolResult(
                success=False,
                content="",
                error="Command blocked for security reasons",
            )

        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), timeout=timeout
                )
                output = stdout.decode("utf-8", errors="replace") + stderr.decode(
                    "utf-8", errors="replace"
                )

                if not output:
                    output = "(empty output)"

                return ToolResult(
                    success=process.returncode == 0,
                    content=output,
                    error=None
                    if process.returncode == 0
                    else f"Exit code: {process.returncode}",
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return ToolResult(
                    success=False,
                    content="",
                    error=f"Command timed out after {timeout} seconds",
                )
        except PermissionError:
            return ToolResult(success=False, content="", error="Permission denied")
        except Exception as e:
            return ToolResult(success=False, content="", error=str(e))

    def _is_safe_command(self, command: str) -> bool:
        """检查命令安全性"""
        if not command or not command.strip():
            return False

        parts = shlex.split(command)
        if not parts:
            return False

        cmd = parts[0].lower()

        # 检查是否在允许的命令列表中
        if cmd not in self.allowed_commands:
            return False

        # 检查黑名单模式
        import re

        for pattern in self.blocked_patterns:
            try:
                if re.search(pattern, command, re.IGNORECASE):
                    return False
            except re.error:
                pass  # 忽略无效的正则表达式

        return True

    def _get_parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "要执行的命令",
                },
                "timeout": {
                    "type": "integer",
                    "description": "超时时间（秒）",
                    "default": 30,
                },
            },
            "required": ["command"],
        }
