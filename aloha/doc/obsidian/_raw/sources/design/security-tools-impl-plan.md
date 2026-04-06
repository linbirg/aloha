# AI Agent 安全工具与权限控制系统实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: 使用 superpowers:subagent-driven-development (推荐) 或 superpowers:executing-plans 来实现此计划。步骤使用 checkbox (`- [ ]`) 语法进行跟踪。

**Goal:** 实现 AI Agent 基础工具（文件读写、命令执行、网页访问）与权限控制系统（权限检查、审批流程、审计日志）

**Architecture:** 采用中间件/代理模式 - 创建 ToolWrapper 拦截所有工具调用，权限检查在包装器中完成。工具层提供基础操作，权限层提供安全控制，两者通过包装器解耦。

**Tech Stack:** Python, asyncio, dataclasses, pathlib, aiohttp

---

## 文件结构规划

```
aloha/
├── tools/                      # 基础工具层
│   ├── __init__.py
│   ├── file_tool.py           # 文件读写工具
│   ├── shell_tool.py          # 命令执行工具
│   └── web_tool.py            # 网页访问工具
│
├── security/                   # 权限控制层（新建）
│   ├── __init__.py
│   ├── policy.py              # 权限策略定义
│   ├── checker.py             # 权限检查器
│   ├── approver.py            # 审批工作流
│   └── audit.py               # 审计日志
│
├── config/
│   ├── security.py           # 安全配置（新建）
│   └── schema.py              # 已存在
│
└── agent/
    ├── wrapper.py             # ToolWrapper 包装器（新建）
    ├── loop.py                # 已存在
    └── base.py                # 已存在
```

---

## 第一阶段：基础工具实现

### Task 1: FileTool 文件读写工具

**Files:**
- Create: `aloha/tools/file_tool.py`
- Modify: `aloha/tools/__init__.py`
- Test: `aloha/test/test_file_tool.py`

- [ ] **Step 1: 创建 FileTool 基础实现**

```python
"""FileTool - 文件读写工具"""

from pathlib import Path
from aloha.agent.tools import BaseTool, ToolResult


class FileTool(BaseTool):
    """文件读写工具"""

    def __init__(self):
        super().__init__(
            name="file",
            description="读取或写入文件内容",
        )

    async def execute(self, operation: str, path: str, content: str = "") -> ToolResult:
        """执行文件操作"""
        if operation == "read":
            return await self._read_file(path)
        elif operation == "write":
            return await self._write_file(path, content)
        return ToolResult(success=False, content="", error="Invalid operation")

    async def _read_file(self, path: str) -> ToolResult:
        """读取文件"""
        try:
            file_path = Path(path)
            if not file_path.exists():
                return ToolResult(success=False, content="", error="File not found")
            content = file_path.read_text(encoding="utf-8")
            return ToolResult(success=True, content=content)
        except Exception as e:
            return ToolResult(success=False, content="", error=str(e))

    async def _write_file(self, path: str, content: str) -> ToolResult:
        """写入文件"""
        try:
            file_path = Path(path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")
            return ToolResult(success=True, content=f"Written to {path}")
        except Exception as e:
            return ToolResult(success=False, content="", error=str(e))

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
```

- [ ] **Step 2: 更新 tools/__init__.py 导出**

```python
"""Aloha Tools 模块

存放系统自带工具（文件读写、命令执行、Web访问等）。
"""

from aloha.agent.tools import BaseTool, ToolResult, ToolMetadata, ToolRegistry
from aloha.tools.file_tool import FileTool

__all__ = ["BaseTool", "ToolResult", "ToolMetadata", "ToolRegistry", "FileTool"]
```

- [ ] **Step 3: 编写测试验证**

```python
import pytest
from aloha.tools import FileTool

class TestFileTool:
    @pytest.mark.asyncio
    async def test_read_file(self):
        tool = FileTool()
        # 创建临时测试文件
        result = await tool.execute(operation="read", path="test.txt")
        assert result.success is True or "not found" in result.error.lower()
```

---

### Task 2: ShellTool 命令执行工具

**Files:**
- Create: `aloha/tools/shell_tool.py`
- Modify: `aloha/tools/__init__.py`
- Test: `aloha/test/test_shell_tool.py`

- [ ] **Step 1: 创建 ShellTool 基础实现**

```python
"""ShellTool - 命令执行工具"""

import asyncio
import shlex
from aloha.agent.tools import BaseTool, ToolResult


class ShellTool(BaseTool):
    """命令行执行工具"""

    # 危险命令黑名单
    BLOCKED_COMMANDS = {"rm", "del", "format", "shutdown", "reboot"}

    def __init__(self):
        super().__init__(
            name="shell",
            description="执行命令行命令",
        )

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
                output = stdout.decode() + stderr.decode()
                return ToolResult(
                    success=process.returncode == 0,
                    content=output,
                    error=None if process.returncode == 0 else f"Exit code: {process.returncode}",
                )
            except asyncio.TimeoutError:
                process.kill()
                return ToolResult(success=False, content="", error="Command timeout")
        except Exception as e:
            return ToolResult(success=False, content="", error=str(e))

    def _is_safe_command(self, command: str) -> bool:
        """检查命令安全性"""
        parts = shlex.split(command)
        if not parts:
            return False
        cmd = parts[0].lower()
        return cmd not in self.BLOCKED_COMMANDS

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
```

- [ ] **Step 2: 更新 tools/__init__.py 导出**

- [ ] **Step 3: 编写测试**

---

### Task 3: WebTool 网页访问工具

**Files:**
- Create: `aloha/tools/web_tool.py`
- Modify: `aloha/tools/__init__.py`
- Test: `aloha/test/test_web_tool.py`

- [ ] **Step 1: 创建 WebTool 基础实现**

```python
"""WebTool - 网页访问工具"""

import aiohttp
from aloha.agent.tools import BaseTool, ToolResult


class WebTool(BaseTool):
    """网页访问工具"""

    def __init__(self):
        super().__init__(
            name="web",
            description="访问网页并获取内容",
        )
        self._session: aiohttp.ClientSession | None = None

    async def execute(self, url: str, method: str = "GET", data: str = "") -> ToolResult:
        """执行 HTTP 请求"""
        try:
            if self._session is None:
                self._session = aiohttp.ClientSession()

            async with self._session.request(method, url, data=data if data else None) as resp:
                content = await resp.text()
                return ToolResult(
                    success=True,
                    content=f"Status: {resp.status}\n\n{content[:5000]}",
                )
        except Exception as e:
            return ToolResult(success=False, content="", error=str(e))

    async def close(self):
        """关闭 session"""
        if self._session:
            await self._session.close()
            self._session = None

    def _get_parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "要访问的 URL",
                },
                "method": {
                    "type": "string",
                    "description": "HTTP 方法",
                    "enum": ["GET", "POST"],
                    "default": "GET",
                },
                "data": {
                    "type": "string",
                    "description": "POST 请求数据",
                },
            },
            "required": ["url"],
        }
```

- [ ] **Step 2: 更新 tools/__init__.py 导出**

- [ ] **Step 3: 编写测试**

---

## 第二阶段：权限框架实现

### Task 4: SecurityConfig 安全配置

**Files:**
- Create: `aloha/config/security.py`
- Test: `aloha/test/test_security_config.py`

- [ ] **Step 1: 创建安全配置类**

```python
"""SecurityConfig - 安全配置"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol


class ApprovalCallback(Protocol):
    """审批回调协议"""

    async def request_approval(self, permission: "Permission") -> bool:
        """请求用户批准，返回是否批准"""
        pass

    async def notify(self, message: str) -> None:
        """通知用户"""
        pass


@dataclass
class SecurityConfig:
    """安全配置"""

    # 文件操作
    file_read_allowed_dirs: list[Path] = field(
        default_factory=lambda: [Path.cwd(), Path.home() / "workspace"]
    )
    file_write_allowed_dirs: list[Path] = field(
        default_factory=lambda: [Path.cwd() / "output"]
    )
    file_blocked_extensions: list[str] = field(
        default_factory=lambda: [".exe", ".dll", ".so", ".sh"]
    )

    # Shell 操作
    shell_allowed_commands: list[str] = field(
        default_factory=lambda: ["ls", "cat", "echo", "grep", "find", "git"]
    )
    shell_blocked_patterns: list[str] = field(
        default_factory=lambda: [r"rm\s+-rf", r"del\s+/s", r"format"]
    )

    # Web 操作
    web_allowed_domains: list[str] = field(
        default_factory=lambda: ["*"]  # * 表示允许所有
    )
    web_rate_limit: int = 10  # 每分钟请求数限制

    # 审批配置
    auto_approve_low_risk: bool = True
    approval_callback: ApprovalCallback | None = None
```

---

### Task 5: Permission 数据结构

**Files:**
- Modify: `aloha/security/policy.py`
- Test: `aloha/test/test_policy.py`

- [ ] **Step 1: 创建权限策略模块**

```python
"""Security Policy - 安全策略定义"""

from dataclasses import dataclass
from enum import Enum
from datetime import datetime


class RiskLevel(Enum):
    """风险级别"""
    LOW = "low"       # 自动通过
    MEDIUM = "medium" # 需要提示
    HIGH = "high"     # 需要审批


@dataclass
class Permission:
    """权限请求"""
    tool: str           # 工具名称
    action: str         # 操作类型 (read/write/execute)
    resource: str       # 资源路径
    risk_level: RiskLevel = RiskLevel.LOW
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict | None = None


@dataclass
class PermissionPolicy:
    """权限策略"""
    default_risk_level: RiskLevel = RiskLevel.MEDIUM
    rules: list["PermissionRule"] = field(default_factory=list)


@dataclass
class PermissionRule:
    """权限规则"""
    tool: str
    action: str
    pattern: str  # 正则表达式
    risk_level: RiskLevel
    allow: bool = True
```

---

### Task 6: PermissionChecker 权限检查器

**Files:**
- Create: `aloha/security/checker.py`
- Test: `aloha/test/test_checker.py`

- [ ] **Step 1: 创建权限检查器**

```python
"""PermissionChecker - 权限检查器"""

import re
from pathlib import Path
from aloha.config.security import SecurityConfig
from aloha.security.policy import Permission, RiskLevel


class PermissionChecker:
    """权限检查器"""

    def __init__(self, config: SecurityConfig):
        self.config = config

    def check(self, permission: Permission) -> tuple[bool, str]:
        """检查权限，返回 (是否通过, 原因)"""
        
        if permission.tool == "file":
            return self._check_file_permission(permission)
        elif permission.tool == "shell":
            return self._check_shell_permission(permission)
        elif permission.tool == "web":
            return self._check_web_permission(permission)
        
        return True, "Tool not found in security config, allowing"

    def _check_file_permission(self, perm: Permission) -> tuple[bool, str]:
        """检查文件权限"""
        path = Path(perm.resource)
        
        if perm.action == "read":
            for allowed_dir in self.config.file_read_allowed_dirs:
                try:
                    path.resolve().relative_to(allowed_dir.resolve())
                    return True, "Allowed by whitelist"
                except ValueError:
                    continue
            return False, f"Path not in allowed read directories: {perm.resource}"
        
        elif perm.action == "write":
            # 检查扩展名
            if path.suffix in self.config.file_blocked_extensions:
                return False, f"File extension {path.suffix} is blocked"
            
            for allowed_dir in self.config.file_write_allowed_dirs:
                try:
                    path.resolve().relative_to(allowed_dir.resolve())
                    return True, "Allowed by whitelist"
                except ValueError:
                    continue
            return False, f"Path not in allowed write directories: {perm.resource}"
        
        return True, "Unknown action"

    def _check_shell_permission(self, perm: Permission) -> tuple[bool, str]:
        """检查 Shell 权限"""
        cmd = perm.resource.split()[0] if perm.resource else ""
        
        # 检查白名单
        if cmd not in self.config.shell_allowed_commands:
            return False, f"Command {cmd} not in allowed list"
        
        # 检查黑名单模式
        for pattern in self.config.shell_blocked_patterns:
            if re.search(pattern, perm.resource):
                return False, f"Command matches blocked pattern: {pattern}"
        
        return True, "Allowed"

    def _check_web_permission(self, perm: Permission) -> tuple[bool, str]:
        """检查 Web 权限"""
        from urllib.parse import urlparse
        
        domain = urlparse(perm.resource).netloc
        
        if "*" in self.config.web_allowed_domains:
            return True, "All domains allowed"
        
        for allowed in self.config.web_allowed_domains:
            if domain.endswith(allowed):
                return True, "Allowed by whitelist"
        
        return False, f"Domain {domain} not in allowed list"
```

---

## 第三阶段：审批流程实现

### Task 7: Approver 审批工作流

**Files:**
- Create: `aloha/security/approver.py`
- Test: `aloha/test/test_approver.py`

- [ ] **Step 1: 创建审批器**

```python
"""Approver - 审批工作流"""

import asyncio
from aloha.config.security import SecurityConfig, ApprovalCallback
from aloha.security.policy import Permission, RiskLevel


class Approver:
    """审批工作流"""

    def __init__(self, config: SecurityConfig):
        self.config = config

    async def request(self, permission: Permission) -> bool:
        """请求审批"""
        # 低风险且配置允许自动通过
        if permission.risk_level == RiskLevel.LOW and self.config.auto_approve_low_risk:
            return True

        # 使用回调请求用户审批
        if self.config.approval_callback:
            return await self.config.approval_callback.request_approval(permission)

        # 没有回调时，默认拒绝
        return False

    async def notify(self, message: str) -> None:
        """发送通知"""
        if self.config.approval_callback:
            await self.config.approval_callback.notify(message)
```

---

### Task 8: Audit 审计日志

**Files:**
- Create: `aloha/security/audit.py`
- Test: `aloha/test/test_audit.py`

- [ ] **Step 1: 创建审计日志**

```python
"""Audit - 审计日志"""

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
    """审计日志条目"""
    timestamp: datetime = field(default_factory=datetime.now)
    tool: str = ""
    action: str = ""
    resource: str = ""
    risk_level: str = ""
    result: AuditResult = AuditResult.APPROVED
    user_response: str | None = None
    error: str | None = None


class AuditLogger:
    """审计日志记录器"""

    def __init__(self, log_file: TextIO | None = None):
        self.log_file = log_file
        self.logs: list[AuditLog] = []

    def log(self, audit_log: AuditLog) -> None:
        """记录审计日志"""
        self.logs.append(audit_log)
        
        # 写入文件
        if self.log_file:
            self.log_file.write(json.dumps({
                "timestamp": audit_log.timestamp.isoformat(),
                "tool": audit_log.tool,
                "action": audit_log.action,
                "resource": audit_log.resource,
                "risk_level": audit_log.risk_level,
                "result": audit_log.result.value,
                "user_response": audit_log.user_response,
                "error": audit_log.error,
            }) + "\n")

    def get_recent(self, count: int = 10) -> list[AuditLog]:
        """获取最近的日志"""
        return self.logs[-count:]

    def search(self, tool: str | None = None, result: AuditResult | None = None) -> list[AuditLog]:
        """搜索日志"""
        logs = self.logs
        if tool:
            logs = [l for l in logs if l.tool == tool]
        if result:
            logs = [l for l in logs if l.result == result]
        return logs
```

---

## 第四阶段：集成实现

### Task 9: ToolWrapper 工具包装器

**Files:**
- Create: `aloha/agent/wrapper.py`
- Test: `aloha/test/test_wrapper.py`

- [ ] **Step 1: 创建工具包装器**

```python
"""ToolWrapper - 工具包装器

拦截所有工具调用，执行权限检查和审批流程。
"""

from aloha.agent.tools import BaseTool, ToolRegistry, ToolResult
from aloha.config.security import SecurityConfig
from aloha.security.policy import Permission, RiskLevel
from aloha.security.checker import PermissionChecker
from aloha.security.approver import Approver
from aloha.security.audit import AuditLogger, AuditLog, AuditResult


class ToolWrapper:
    """工具包装器 - 权限拦截器"""

    def __init__(
        self,
        registry: ToolRegistry,
        config: SecurityConfig,
    ):
        self.registry = registry
        self.config = config
        self.checker = PermissionChecker(config)
        self.approver = Approver(config)
        self.audit = AuditLogger()

    async def execute(self, tool_name: str, **kwargs) -> ToolResult:
        """执行工具（带权限检查）"""
        # 获取工具
        tool = self.registry.get(tool_name)
        if not tool:
            return ToolResult(
                success=False,
                content="",
                error=f"Tool '{tool_name}' not found",
            )

        # 构建权限请求
        permission = self._build_permission(tool_name, kwargs)

        # 权限检查
        allowed, reason = self.checker.check(permission)
        
        if not allowed:
            self.audit.log(AuditLog(
                tool=tool_name,
                action=kwargs.get("operation", "execute"),
                resource=kwargs.get("path", kwargs.get("command", "")),
                risk_level=permission.risk_level.value,
                result=AuditResult.REJECTED,
                error=reason,
            ))
            return ToolResult(success=False, content="", error=f"Permission denied: {reason}")

        # 审批流程
        approved = await self.approver.request(permission)
        
        if not approved:
            self.audit.log(AuditLog(
                tool=tool_name,
                action=kwargs.get("operation", "execute"),
                resource=kwargs.get("path", kwargs.get("command", "")),
                risk_level=permission.risk_level.value,
                result=AuditResult.REJECTED,
                user_response="rejected",
            ))
            return ToolResult(success=False, content="", error="Permission rejected by user")

        # 执行工具
        result = await tool.execute(**kwargs)
        
        # 记录审计
        self.audit.log(AuditLog(
            tool=tool_name,
            action=kwargs.get("operation", "execute"),
            resource=kwargs.get("path", kwargs.get("command", "")),
            risk_level=permission.risk_level.value,
            result=AuditResult.APPROVED if result.success else AuditResult.ERROR,
            user_response="approved" if result.success else None,
            error=result.error,
        ))

        return result

    def _build_permission(self, tool_name: str, kwargs: dict) -> Permission:
        """构建权限请求"""
        action = kwargs.get("operation", "execute")
        resource = kwargs.get("path", kwargs.get("command", kwargs.get("url", ""))))
        
        # 简单风险评估
        risk = RiskLevel.MEDIUM
        if tool_name == "shell" or (tool_name == "file" and action == "write"):
            risk = RiskLevel.HIGH
        
        return Permission(
            tool=tool_name,
            action=action,
            resource=str(resource),
            risk_level=risk,
            metadata=kwargs,
        )
```

---

### Task 10: 与 Agent Loop 集成

**Files:**
- Modify: `aloha/agent/loop.py`
- Test: `aloha/test/test_react_loop_integration.py`

- [ ] **Step 1: 修改 ReActLoop 支持 ToolWrapper**

```python
# 在 ReActLoop.__init__ 中添加
self._tool_wrapper: ToolWrapper | None = None

def set_tool_wrapper(self, wrapper: ToolWrapper):
    """设置工具包装器"""
    self._tool_wrapper = wrapper
    # 替换默认的 tools 执行
    self._use_wrapper = True
```

- [ ] **Step 2: 修改 _execute_tool 使用包装器**

```python
async def _execute_tool(self, tool_call) -> None:
    tool_name = tool_call.name
    tool_args = tool_call.arguments
    
    self.thought_logs.append(f"🛠️ 调用工具: {tool_name}")
    self.thought_logs.append(f"📝 参数: {tool_args}")

    # 使用包装器执行
    if hasattr(self, "_use_wrapper") and self._tool_wrapper:
        result = await self._tool_wrapper.execute(tool_name, **tool_args)
    else:
        result = await self.tools.execute_tool(tool_name, **tool_args)

    # 处理结果...
```

---

## 执行顺序

1. **Task 1-3**: 实现基础工具（FileTool, ShellTool, WebTool）
2. **Task 4**: 实现安全配置（SecurityConfig）
3. **Task 5-6**: 实现权限框架（Permission, PermissionChecker）
4. **Task 7-8**: 实现审批流程（Approver, Audit）
5. **Task 9-10**: 集成（ToolWrapper 与 Agent Loop）

---

## 执行方式

**Plan complete. Two execution options:**

1. **Subagent-Driven (推荐)** - 每个任务由独立的子 Agent 执行，任务间进行审查
2. **Inline Execution** - 在当前会话中执行任务，使用 executing-plans 技能

**Which approach?**