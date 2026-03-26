"""Audit - 审计日志

记录所有工具调用的权限检查和执行结果。
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import TextIO
import json


class AuditResult(Enum):
    """审计结果"""
    APPROVED = "approved"
    REJECTED = "rejected"
    ERROR = "error"


@dataclass
class AuditLog:
    """审计日志条目

    记录一次工具调用的完整审计信息。
    """
    timestamp: datetime = field(default_factory=datetime.now)
    tool: str = ""
    action: str = ""
    resource: str = ""
    risk_level: str = ""
    result: AuditResult = AuditResult.APPROVED
    user_response: str | None = None
    error: str | None = None
    duration_ms: float | None = None

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "tool": self.tool,
            "action": self.action,
            "resource": self.resource,
            "risk_level": self.risk_level,
            "result": self.result.value,
            "user_response": self.user_response,
            "error": self.error,
            "duration_ms": self.duration_ms,
        }

    def to_json(self) -> str:
        """转换为 JSON 字符串"""
        return json.dumps(self.to_dict())


class AuditLogger:
    """审计日志记录器

    管理审计日志的记录、查询和导出。
    """

    def __init__(self, log_file: TextIO | None = None):
        self.log_file = log_file
        self.logs: list[AuditLog] = []

    def log(self, audit_log: AuditLog) -> None:
        """记录审计日志

        Args:
            audit_log: 审计日志条目
        """
        self.logs.append(audit_log)

        # 写入文件
        if self.log_file:
            try:
                self.log_file.write(audit_log.to_json() + "\n")
                self.log_file.flush()
            except Exception:
                pass  # 忽略写入错误

    def log_approval(
        self,
        tool: str,
        action: str,
        resource: str,
        risk_level: str,
        approved: bool,
        user_response: str | None = None,
        error: str | None = None,
    ) -> None:
        """快捷方法：记录审批结果

        Args:
            tool: 工具名称
            action: 操作类型
            resource: 资源路径
            risk_level: 风险级别
            approved: 是否批准
            user_response: 用户响应
            error: 错误信息
        """
        self.log(AuditLog(
            tool=tool,
            action=action,
            resource=resource,
            risk_level=risk_level,
            result=AuditResult.APPROVED if approved else AuditResult.REJECTED,
            user_response=user_response,
            error=error,
        ))

    def log_error(
        self,
        tool: str,
        action: str,
        resource: str,
        error: str,
    ) -> None:
        """快捷方法：记录错误

        Args:
            tool: 工具名称
            action: 操作类型
            resource: 资源路径
            error: 错误信息
        """
        self.log(AuditLog(
            tool=tool,
            action=action,
            resource=resource,
            risk_level="unknown",
            result=AuditResult.ERROR,
            error=error,
        ))

    def get_recent(self, count: int = 10) -> list[AuditLog]:
        """获取最近的日志

        Args:
            count: 返回数量

        Returns:
            审计日志列表
        """
        return self.logs[-count:]

    def get_by_tool(self, tool: str) -> list[AuditLog]:
        """获取指定工具的日志

        Args:
            tool: 工具名称

        Returns:
            审计日志列表
        """
        return [log for log in self.logs if log.tool == tool]

    def get_by_result(self, result: AuditResult) -> list[AuditLog]:
        """获取指定结果的日志

        Args:
            result: 审计结果

        Returns:
            审计日志列表
        """
        return [log for log in self.logs if log.result == result]

    def search(
        self,
        tool: str | None = None,
        result: AuditResult | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> list[AuditLog]:
        """搜索日志

        Args:
            tool: 工具名称过滤
            result: 审计结果过滤
            start_time: 开始时间
            end_time: 结束时间

        Returns:
            符合条件的审计日志列表
        """
        logs = self.logs

        if tool:
            logs = [log for log in logs if log.tool == tool]

        if result:
            logs = [log for log in logs if log.result == result]

        if start_time:
            logs = [log for log in logs if log.timestamp >= start_time]

        if end_time:
            logs = [log for log in logs if log.timestamp <= end_time]

        return logs

    def get_stats(self) -> dict:
        """获取统计信息

        Returns:
            统计字典
        """
        total = len(self.logs)
        if total == 0:
            return {"total": 0}

        approved = len([log for log in self.logs if log.result == AuditResult.APPROVED])
        rejected = len([log for log in self.logs if log.result == AuditResult.REJECTED])
        errors = len([log for log in self.logs if log.result == AuditResult.ERROR])

        return {
            "total": total,
            "approved": approved,
            "rejected": rejected,
            "errors": errors,
            "approval_rate": round(approved / total * 100, 2) if total > 0 else 0,
        }

    def clear(self) -> None:
        """清空日志"""
        self.logs.clear()

    def export_json(self) -> str:
        """导出为 JSON

        Returns:
            JSON 字符串
        """
        return json.dumps([log.to_dict() for log in self.logs], indent=2)