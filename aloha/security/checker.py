"""PermissionChecker - 权限检查器

根据安全配置检查权限请求是否允许。
"""

import re
from pathlib import Path
from aloha.security.policy import Permission, RiskLevel, SecurityConfig


class PermissionChecker:
    """权限检查器

    对工具调用进行权限检查，返回是否允许执行及原因。
    """

    def __init__(self, config: SecurityConfig):
        self.config = config

    def check(self, permission: Permission) -> tuple[bool, str]:
        """检查权限

        Args:
            permission: 权限请求

        Returns:
            (是否通过, 原因)
        """
        if permission.tool == "file":
            return self._check_file_permission(permission)
        elif permission.tool == "shell":
            return self._check_shell_permission(permission)
        elif permission.tool == "web":
            return self._check_web_permission(permission)

        # 未知工具，默认允许（可在生产环境中改为拒绝）
        return True, "Tool not found in security config, allowing"

    def _check_file_permission(self, perm: Permission) -> tuple[bool, str]:
        """检查文件权限"""
        path = Path(perm.resource)

        if perm.action == "read":
            return self._check_path_in_dirs(path, self.config.file_read_allowed_dirs, "read")
        elif perm.action == "write":
            # 检查扩展名
            if path.suffix.lower() in self.config.file_blocked_extensions:
                return False, f"File extension {path.suffix} is blocked for security"

            return self._check_path_in_dirs(path, self.config.file_write_allowed_dirs, "write")

        return True, "Unknown file action"

    def _check_shell_permission(self, perm: Permission) -> tuple[bool, str]:
        """检查 Shell 权限"""
        if not perm.resource or not perm.resource.strip():
            return False, "Empty command"

        parts = perm.resource.split()
        if not parts:
            return False, "Empty command"

        cmd = parts[0].lower()

        # 检查是否在允许的命令列表中
        if cmd not in self.config.shell_allowed_commands:
            return False, f"Command '{cmd}' not in allowed list: {self.config.shell_allowed_commands}"

        # 检查黑名单模式
        for pattern in self.config.shell_blocked_patterns:
            try:
                if re.search(pattern, perm.resource, re.IGNORECASE):
                    return False, f"Command matches blocked pattern: {pattern}"
            except re.error:
                pass  # 忽略无效的正则表达式

        return True, "Allowed"

    def _check_web_permission(self, perm: Permission) -> tuple[bool, str]:
        """检查 Web 权限"""
        from urllib.parse import urlparse

        try:
            parsed = urlparse(perm.resource)
            domain = parsed.netloc
        except Exception:
            return False, "Invalid URL"

        if "*" in self.config.web_allowed_domains:
            return True, "All domains allowed"

        for allowed in self.config.web_allowed_domains:
            if domain == allowed or domain.endswith(f".{allowed}"):
                return True, "Allowed by whitelist"

        return False, f"Domain '{domain}' not in allowed list: {self.config.web_allowed_domains}"

    def _check_path_in_dirs(self, path: Path, allowed_dirs: list[Path], action: str) -> tuple[bool, str]:
        """检查路径是否在允许的目录列表中"""
        try:
            resolved_path = path.resolve()
            resolved_cwd = Path.cwd().resolve()

            # 允许访问 cwd 内的文件
            try:
                resolved_path.relative_to(resolved_cwd)
                is_in_cwd = True
            except ValueError:
                is_in_cwd = False

            for allowed_dir in allowed_dirs:
                try:
                    resolved_path.relative_to(allowed_dir.resolve())
                    return True, f"Allowed by whitelist: {allowed_dir}"
                except ValueError:
                    continue

            # 如果不在 cwd 内，也不是允许的目录，则拒绝
            if not is_in_cwd:
                return False, f"Path not in allowed {action} directories: {path}"

            return True, f"Allowed (in current working directory)"

        except Exception as e:
            return False, f"Error checking path: {str(e)}"

    def assess_risk(self, permission: Permission) -> RiskLevel:
        """评估风险级别

        根据操作类型和资源评估风险级别。
        """
        # 高风险操作
        if permission.tool == "shell":
            return RiskLevel.HIGH

        if permission.tool == "file" and permission.action == "write":
            return RiskLevel.HIGH

        # 中风险操作
        if permission.tool == "file" and permission.action == "read":
            return RiskLevel.MEDIUM

        if permission.tool == "web":
            return RiskLevel.MEDIUM

        # 低风险操作
        return RiskLevel.LOW