# ShellTool + ToolWrapper 安全架构重构设计方案

**日期**：2026-04-06
**版本**：v1.0
**状态**：已确认，待实施

---

## 1. 现状问题

### 1.1 双重安全检查，规则不同步

```
ToolWrapper.execute()
  ├── ① PermissionChecker.check()
  │       ├── SecurityConfig.shell_allowed_commands
  │       └── SecurityConfig.shell_blocked_patterns
  └── ② ShellTool._is_safe_command()
          ├── ShellTool.allowed_commands          ← 与①不同步
          └── ShellTool.blocked_patterns          ← 与①不同步
```

两层各自维护一份 `allowed_commands` 和 `blocked_patterns`，正则表达式不一致，添加命令时容易遗漏其中一层。

### 1.2 命令列表散落三处

| 位置 | 命令数 | 包含 `dir` | 包含 `python`/`pip`/`uv` |
|------|--------|-----------|--------------------------|
| `SecurityConfig.shell_allowed_commands` 默认 | 14 | ❌ | ❌ |
| `ShellTool.allowed_commands` 默认 | 14 | ❌ | ❌ |
| `__main__.py:95` / `api.py:195` 显式传入 | 17 | ✅ | ✅ |

`dir`（Windows）和 `python`/`pip`/`uv` 在显式传入的列表中有，但默认值中没有，维护混乱。

### 1.3 职责不清

`ShellTool` 身兼两职：
- **执行**：通过 `subprocess` 运行命令
- **安全**：白名单 + 黑名单正则检查

安全检查本应是全局统一策略，不应分散在各个工具中。

---

## 2. 重构目标

| 目标 | 说明 |
|------|------|
| **单一真实来源** | 所有安全配置（allowed_commands、blocked_patterns）只在一处定义 |
| **单一检查点** | `ToolWrapper` 是唯一的安全检查入口，工具只做纯执行 |
| **配置覆盖** | `SecurityConfig` 是权威配置，`ShellTool` 从中读取，外部可覆盖 |
| **Windows 兼容** | `dir` 等 Windows 命令纳入默认允许列表 |

---

## 3. 重构后架构

### 3.1 调用链

```
ToolWrapper.execute()
  └── PermissionChecker.check()
       ├── SecurityConfig.shell_allowed_commands   ← 唯一允许命令列表
       └── SecurityConfig.shell_blocked_patterns   ← 唯一黑名单正则
  └── ShellTool.execute()                         ← 纯执行，无安全逻辑
```

### 3.2 职责划分

| 模块 | 职责 |
|------|------|
| `SecurityConfig` | 所有安全配置的唯一来源（allowed_commands、blocked_patterns、文件白名单、域名白名单）|
| `PermissionChecker` | 唯一的安全检查点，基于 SecurityConfig |
| `ToolWrapper` | 拦截所有工具调用 → 权限检查 → 审批 → 执行 → 审计 |
| `ShellTool` | 纯命令执行器，无任何安全检查逻辑 |
| `FileTool` / `WebTool` | 纯执行器，无任何安全检查逻辑 |

---

## 4. 详细改动

### 4.1 `security/policy.py` — 新增常量，合并 blocklist

新增两个模块级常量作为唯一真实来源：

```python
# ============================================================
# 唯一真实来源：Shell 命令白名单
# ============================================================
SECURITY_SHELL_ALLOWED_COMMANDS: list[str] = [
    # 基础命令
    "ls", "cat", "echo", "grep", "find", "git", "pwd", "cd",
    "mkdir", "cp", "mv", "rm", "head", "tail", "wc",
    # Windows 命令
    "dir", "type", "copy", "del", "rd",
    # 开发命令
    "python", "pip", "uv", "node", "npm", "cargo", "go",
]

# ============================================================
# 唯一真实来源：Shell 黑名单正则
# ============================================================
SECURITY_SHELL_BLOCKED_PATTERNS: list[str] = [
    r"rm\s+-rf\s+/",           # 递归删除根目录
    r"rm\s+-rf\s+\.",          # 递归删除当前目录
    r"del\s+/[sq]",            # Windows 危险删除
    r"format\s+[a-z]:",        # 格式化磁盘
    r">\s*/dev/",              # 写入设备文件
    r"shutdown",                # 关机命令
    r"reboot",                  # 重启命令
    r"mkfs",                    # 格式化文件系统
    r"dd\s+if=",                # 危险磁盘操作
]
```

`SecurityConfig` 的默认值改为引用常量：

```python
@dataclass
class SecurityConfig:
    shell_allowed_commands: list[str] = field(
        default_factory=lambda: list(SECURITY_SHELL_ALLOWED_COMMANDS)
    )
    shell_blocked_patterns: list[str] = field(
        default_factory=lambda: list(SECURITY_SHELL_BLOCKED_PATTERNS)
    )
    # 其余字段保持不变...
```

### 4.2 `tools/shell_tool.py` — 删除所有安全检查

删除内容：
- `DEFAULT_BLOCKED_COMMANDS` 常量
- `__init__` 中的 `allowed_commands` 参数和 `blocked_patterns` 参数
- `_is_safe_command()` 方法

修改后：

```python
class ShellTool(BaseTool):
    def __init__(self, timeout: int = 30):
        super().__init__(
            name="shell",
            description="执行命令行命令",
        )
        self.timeout = timeout

    async def execute(self, command: str, timeout: int = 30) -> ToolResult:
        """执行命令（无任何安全检查，安全由 ToolWrapper 统一控制）"""
        # 不再有 _is_safe_command 调用，直接执行
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=timeout
            )
            # ... 其余不变
```

> **注意**：`timeout` 参数保留，因为这是执行层面的参数，与安全无关。

### 4.3 `security/checker.py` — 保持不变

`PermissionChecker._check_shell_permission()` 保持不变，继续使用 `SecurityConfig` 中的 `shell_allowed_commands` 和 `shell_blocked_patterns`。

### 4.4 `__main__.py` — 移除显式 `allowed_commands`

删除 `ShellTool(allowed_commands=[...])` 中的显式命令列表，改为直接使用默认值：

```python
# 重构前
agent.add_tool(ShellTool(
    allowed_commands=[
        "ls", "dir", "cat", "echo", "grep", "find", "git", "pwd", "cd",
        "mkdir", "cp", "mv", "rm", "head", "tail", "wc", "python", "pip", "uv",
    ]
))

# 重构后
agent.add_tool(ShellTool())  # 从 SecurityConfig 默认值读取
```

若需要额外命令（不常见），通过 `SecurityConfig` 注入：

```python
security_config = SecurityConfig(
    shell_allowed_commands=[*SECURITY_SHELL_ALLOWED_COMMANDS, "custom_cmd"],
)
```

### 4.5 `web/service/api.py` — 同样移除显式列表

两处 `ShellTool(allowed_commands=[...])` 均改为 `ShellTool()`。

### 4.6 `agent/wrapper.py` — 移除对 tool 内部检查的依赖

当前 `wrapper.py` 完全依赖 `PermissionChecker`，不做额外 tool 内部检查。改动极小，只需确认 `ToolWrapper` 不再调用任何 tool 的 `_is_safe_command()`（当前已无此调用，可直接确认）。

---

## 5. 行为变化

| 场景 | 重构前 | 重构后 |
|------|--------|--------|
| `rm` 命令（无参数）| 通过（不在任何 blocklist）| 不变 |
| `rm -rf /` | 被 `blocked_patterns` 拦截 | 不变 |
| `python script.py` | 需显式传入才能允许 | 默认允许 |
| `dir` (Windows) | 需显式传入才能允许 | 默认允许 |
| 新增命令（如 `docker`）| 需改两处（ShellTool + SecurityConfig）| 只改 `SECURITY_SHELL_ALLOWED_COMMANDS` |
| 工具内部安全逻辑 | `ShellTool._is_safe_command()` | 无，纯执行 |

---

## 6. 测试影响

以下测试中的显式 `allowed_commands` 传入需要调整：

| 文件 | 改动 |
|------|------|
| `test_minimax_normalize.py:52` | 移除 `allowed_commands` 参数 |
| `test_minimax_integration.py:59,98` | 移除 `allowed_commands` 参数 |
| `test_cli_say.py:59,99,126,153,189` | 移除 `allowed_commands` 参数 |
| `test_debug.py:41` | 移除 `allowed_commands` 参数 |
| `test_reactloop.py:130,657` | 移除 `shell_allowed_commands` 参数（测试拒绝场景可用 `SecurityConfig(shell_allowed_commands=[])`）|

---

## 7. 待思考问题

### 7.1 `blocked_patterns` 是否需要细化到命令级？

当前所有命令共享同一份 `blocked_patterns`。未来可能需要：

```python
# 命令级别的 block 规则
SECURITY_SHELL_COMMAND_BLOCKS = {
    "rm": [r"-rf\s+/", r"-rf\s+\."],
    "del": [r"/[sq]"],
}
```

当前方案保持平坦列表，暂不实现命令级细分。

### 7.2 `ShellTool` 的 `timeout` 是否应纳入 `SecurityConfig`？

`timeout` 是执行层参数，但高 `timeout` 可能被滥用（如 `sleep 999999`）。是否在 `SecurityConfig` 增加 `shell_max_timeout` 限制？

**当前决定**：保留在 `ShellTool.__init__`，不在安全配置层控制。

### 7.3 是否需要 `ToolWrapper` 在拒绝时返回更详细的原因？

当前返回 `"Permission denied: {reason}"`，reason 来自 `PermissionChecker`。是否需要区分"不在白名单"和"匹配黑名单"两种情况？

**当前决定**：保持现有 `PermissionChecker` 返回值粒度。

---

## 8. 实施步骤

1. 在 `policy.py` 新增 `SECURITY_SHELL_ALLOWED_COMMANDS` 和 `SECURITY_SHELL_BLOCKED_PATTERNS` 常量
2. 更新 `SecurityConfig` 的 `default_factory` 引用新常量
3. 更新 `shell_tool.py`：删除安全检查，只保留执行逻辑
4. 更新 `__main__.py`：移除四处显式 `allowed_commands`
5. 更新 `api.py`：移除两处显式 `allowed_commands`
6. 更新测试文件：移除显式 `allowed_commands` 参数
7. 运行测试验证
