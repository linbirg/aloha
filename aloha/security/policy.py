"""Security Policy - 安全策略定义

定义权限、风险级别和权限规则的数据结构。
"""

from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from pathlib import Path
from typing import Protocol


class RiskLevel(Enum):
    """风险级别"""
    LOW = "low"       # 自动通过
    MEDIUM = "medium" # 需要提示
    HIGH = "high"     # 需要审批


@dataclass
class Permission:
    """权限请求

    表示一次工具调用的权限请求。
    """
    tool: str           # 工具名称 (file, shell, web)
    action: str         # 操作类型 (read, write, execute)
    resource: str       # 资源路径
    risk_level: RiskLevel = RiskLevel.MEDIUM
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict | None = None

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "tool": self.tool,
            "action": self.action,
            "resource": self.resource,
            "risk_level": self.risk_level.value,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class PermissionPolicy:
    """权限策略

    定义默认风险级别和规则列表。
    """
    default_risk_level: RiskLevel = RiskLevel.MEDIUM
    rules: list["PermissionRule"] = field(default_factory=list)


@dataclass
class PermissionRule:
    """权限规则

    定义特定工具/操作/资源的权限匹配规则。
    """
    tool: str
    action: str
    pattern: str  # 正则表达式
    risk_level: RiskLevel
    allow: bool = True


class ApprovalCallback(Protocol):
    """审批回调协议

    用于请求用户审批和发送通知。
    """

    async def request_approval(self, permission: Permission) -> bool:
        """请求用户批准，返回是否批准"""
        ...

    async def notify(self, message: str) -> None:
        """通知用户"""
        ...


class MockApprovalCallback:
    """模拟审批回调（用于测试和开发）"""

    async def request_approval(self, permission: Permission) -> bool:
        """自动批准所有请求（开发模式）"""
        return True

    async def notify(self, message: str) -> None:
        """打印通知消息"""
        print(f"[Approval] {message}")


@dataclass
class SecurityConfig:
    """安全配置

    集中管理所有安全相关配置。
    """

    # 文件操作配置
    file_read_allowed_dirs: list[Path] = field(
        default_factory=lambda: [Path.cwd(), Path.home() / "workspace"]
    )
    file_write_allowed_dirs: list[Path] = field(
        default_factory=lambda: [Path.cwd() / "output"]
    )
    file_blocked_extensions: list[str] = field(
        default_factory=lambda: [".exe", ".dll", ".so", ".sh", ".bat", ".cmd"]
    )

    # Shell 操作配置
    shell_allowed_commands: list[str] = field(
        default_factory=lambda: ["ls", "cat", "echo", "grep", "find", "git", "pwd", "cd", "mkdir", "cp", "mv", "head", "tail", "wc"]
    )
    shell_blocked_patterns: list[str] = field(
        default_factory=lambda: [r"rm\s+-rf", r"del\s+/[sq]", r"format\s+[a-z]:", r">\s*/dev/"]
    )

    # Web 操作配置
    web_allowed_domains: list[str] = field(
        default_factory=lambda: ["*"]  # * 表示允许所有
    )
    web_rate_limit: int = 10  # 每分钟请求数限制

    # 审批配置
    auto_approve_low_risk: bool = True
    approval_callback: ApprovalCallback | None = None

    def get_file_read_dirs(self) -> list[Path]:
        """获取允许读取的目录列表"""
        return self.file_read_allowed_dirs

    def get_file_write_dirs(self) -> list[Path]:
        """获取允许写入的目录列表"""
        return self.file_write_allowed_dirs