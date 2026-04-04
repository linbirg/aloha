"""Approver - 审批工作流

处理权限请求的审批流程，包括同步阻塞的用户确认。
"""

import asyncio
from aloha.security.policy import (
    Permission,
    RiskLevel,
    SecurityConfig,
    ApprovalCallback,
)


class Approver:
    """审批工作流

    处理权限请求的审批。根据配置自动批准低风险请求，
    或通过回调请求用户审批，或通过 ApprovalManager 异步等待。
    """

    def __init__(self, config: SecurityConfig):
        self.config = config
        self._pending_requests: dict[str, asyncio.Future[bool]] = {}
        self._approval_manager = None

    def set_approval_manager(self, manager) -> None:
        self._approval_manager = manager

    async def request(self, permission: Permission) -> bool:
        """请求审批

        Args:
            permission: 权限请求

        Returns:
            是否批准
        """
        if permission.risk_level == RiskLevel.LOW and self.config.auto_approve_low_risk:
            return True

        if self._approval_manager:
            from aloha.agent.events import ApprovalRequest

            request = ApprovalRequest(
                id=permission.id,
                tool_name=permission.tool,
                action=permission.action,
                arguments=permission.metadata or {},
                risk_level=permission.risk_level,
                description=f"{permission.tool}: {permission.resource}",
                resource=permission.resource,
            )
            await self._approval_manager.enqueue(request)
            return await self._approval_manager.wait(request.id)

        if self.config.approval_callback:
            try:
                return await self.config.approval_callback.request_approval(permission)
            except Exception:
                return False

        return False

    async def request_with_blocking(
        self,
        permission: Permission,
        timeout: float = 60.0,
    ) -> bool:
        """同步阻塞的审批请求

        等待用户响应，超时后返回 False。

        Args:
            permission: 权限请求
            timeout: 超时时间（秒）

        Returns:
            是否批准
        """
        if permission.risk_level == RiskLevel.LOW and self.config.auto_approve_low_risk:
            return True

        if self.config.approval_callback:
            try:
                # 尝试使用回调，如果回调支持超时则使用
                if hasattr(
                    self.config.approval_callback, "request_approval_with_timeout"
                ):
                    return await self.config.approval_callback.request_approval_with_timeout(
                        permission, timeout
                    )
                else:
                    # 如果回调不支持超时，使用 asyncio.wait_for
                    return await asyncio.wait_for(
                        self.config.approval_callback.request_approval(permission),
                        timeout=timeout,
                    )
            except asyncio.TimeoutError:
                return False
            except Exception:
                return False

        return False

    async def notify(self, message: str) -> None:
        """发送通知

        Args:
            message: 通知消息
        """
        if self.config.approval_callback:
            try:
                await self.config.approval_callback.notify(message)
            except Exception:
                pass  # 忽略通知错误

    def create_approval_prompt(self, permission: Permission) -> str:
        """创建审批提示文本

        Args:
            permission: 权限请求

        Returns:
            格式化的提示文本
        """
        risk_emoji = {
            RiskLevel.LOW: "🟢",
            RiskLevel.MEDIUM: "🟡",
            RiskLevel.HIGH: "🔴",
        }

        emoji = risk_emoji.get(permission.risk_level, "⚪")

        return f"""{emoji} Permission Request

Tool: {permission.tool}
Action: {permission.action}
Resource: {permission.resource}
Risk Level: {permission.risk_level.value.upper()}

Timestamp: {permission.timestamp.isoformat()}

Do you approve this request? (yes/no)"""
