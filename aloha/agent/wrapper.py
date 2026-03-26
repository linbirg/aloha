"""ToolWrapper - 工具包装器

拦截所有工具调用，执行权限检查和审批流程。
"""

import time
from aloha.agent.tools import ToolRegistry, ToolResult
from aloha.security import (
    SecurityConfig,
    Permission,
    PermissionChecker,
    Approver,
    AuditLogger,
    AuditResult,
)


class ToolWrapper:
    """工具包装器 - 权限拦截器

    包装 ToolRegistry，拦截所有工具调用，执行：
    1. 权限检查 (PermissionChecker)
    2. 审批流程 (Approver)
    3. 审计日志 (AuditLogger)
    """

    def __init__(
        self,
        registry: ToolRegistry,
        config: SecurityConfig | None = None,
        enable_security: bool = True,
    ):
        self.registry = registry
        self.config = config or SecurityConfig()
        self.enable_security = enable_security

        # 初始化组件
        self.checker = PermissionChecker(self.config)
        self.approver = Approver(self.config)
        self.audit = AuditLogger()

    async def execute(self, tool_name: str, **kwargs) -> ToolResult:
        """执行工具（带权限检查）

        Args:
            tool_name: 工具名称
            **kwargs: 工具参数

        Returns:
            ToolResult: 工具执行结果
        """
        start_time = time.time()

        # 获取工具
        tool = self.registry.get(tool_name)
        if not tool:
            return ToolResult(
                success=False,
                content="",
                error=f"Tool '{tool_name}' not found",
            )

        # 如果未启用安全，直接执行
        if not self.enable_security:
            return await tool.execute(**kwargs)

        # 构建权限请求
        permission = self._build_permission(tool_name, kwargs)
        permission.risk_level = self.checker.assess_risk(permission)

        # 权限检查
        allowed, reason = self.checker.check(permission)

        if not allowed:
            duration_ms = (time.time() - start_time) * 1000
            self.audit.log_approval(
                tool=tool_name,
                action=kwargs.get("operation", "execute"),
                resource=kwargs.get("path", kwargs.get("command", kwargs.get("url", ""))),
                risk_level=permission.risk_level.value,
                approved=False,
                error=reason,
            )
            return ToolResult(
                success=False,
                content="",
                error=f"Permission denied: {reason}",
            )

        # 审批流程
        approved = await self.approver.request(permission)

        if not approved:
            duration_ms = (time.time() - start_time) * 1000
            self.audit.log_approval(
                tool=tool_name,
                action=kwargs.get("operation", "execute"),
                resource=kwargs.get("path", kwargs.get("command", kwargs.get("url", ""))),
                risk_level=permission.risk_level.value,
                approved=False,
                user_response="rejected",
            )
            return ToolResult(
                success=False,
                content="",
                error="Permission rejected by user",
            )

        # 执行工具
        try:
            result = await tool.execute(**kwargs)

            # 记录审计
            duration_ms = (time.time() - start_time) * 1000
            self.audit.log_approval(
                tool=tool_name,
                action=kwargs.get("operation", "execute"),
                resource=kwargs.get("path", kwargs.get("command", kwargs.get("url", ""))),
                risk_level=permission.risk_level.value,
                approved=result.success,
                user_response="approved" if result.success else None,
                error=result.error,
            )

            # 添加执行时间到元数据
            if result.metadata is None:
                result.metadata = {}
            result.metadata["duration_ms"] = duration_ms

            return result

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.audit.log_error(
                tool=tool_name,
                action=kwargs.get("operation", "execute"),
                resource=kwargs.get("path", kwargs.get("command", kwargs.get("url", ""))),
                error=str(e),
            )
            return ToolResult(
                success=False,
                content="",
                error=f"Execution error: {str(e)}",
            )

    def _build_permission(self, tool_name: str, kwargs: dict) -> Permission:
        """构建权限请求

        Args:
            tool_name: 工具名称
            kwargs: 工具参数

        Returns:
            Permission: 权限请求
        """
        action = kwargs.get("operation", "execute")
        resource = ""

        # 根据工具类型提取资源
        if tool_name == "file":
            resource = kwargs.get("path", "")
        elif tool_name == "shell":
            resource = kwargs.get("command", "")
        elif tool_name == "web":
            resource = kwargs.get("url", "")

        return Permission(
            tool=tool_name,
            action=action,
            resource=str(resource),
            metadata=kwargs,
        )

    def register(self, tool) -> None:
        """注册工具

        Args:
            tool: 工具实例
        """
        self.registry.register(tool)

    def unregister(self, name: str) -> bool:
        """注销工具

        Args:
            name: 工具名称

        Returns:
            bool: 是否成功
        """
        return self.registry.unregister(name)

    def get(self, name: str):
        """获取工具

        Args:
            name: 工具名称

        Returns:
            工具实例或 None
        """
        return self.registry.get(name)

    def has(self, name: str) -> bool:
        """检查工具是否存在

        Args:
            name: 工具名称

        Returns:
            bool: 是否存在
        """
        return self.registry.has(name)

    def list_tools(self) -> list[str]:
        """列出所有工具

        Returns:
            list[str]: 工具名称列表
        """
        return self.registry.list_tools()

    def get_tools_schema(self) -> list[dict]:
        """获取工具 schema

        Returns:
            list[dict]: schema 列表
        """
        return self.registry.get_tools_schema()

    def get_audit_logs(self) -> list:
        """获取审计日志

        Returns:
            list: 审计日志列表
        """
        return self.audit.logs

    def get_audit_stats(self) -> dict:
        """获取审计统计

        Returns:
            dict: 统计信息
        """
        return self.audit.get_stats()

    def enable_security_mode(self) -> None:
        """启用安全模式"""
        self.enable_security = True

    def disable_security_mode(self) -> None:
        """禁用安全模式（开发/测试用）"""
        self.enable_security = False