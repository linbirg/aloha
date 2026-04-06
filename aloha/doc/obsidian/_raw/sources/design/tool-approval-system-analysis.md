# Aloha 工具审批系统分析文档

**日期**：2026-04-04
**版本**：v1.0

---

## 1. 问题描述

### 1.1 错误现象

前端调用 `rm` 命令删除文件时，后端返回错误：

```
Permission denied: Command 'rm' not in allowed list: ['ls', 'cat', 'echo', 'grep', 'find', 'git', 'pwd', 'cd', 'mkdir', 'cp', 'mv', 'head', 'tail', 'wc']
```

`rm` 明明在 `api.py` 的 `ShellTool(allowed_commands=[...])` 中已加入，却仍被拒绝。

### 1.2 根本原因：两套独立的允许列表

工具命令校验涉及**两套独立的允许列表**，它们分别在不同位置校验，且默认值不完全一致：

| 校验层 | 所在文件 | 校验位置 | 默认值 |
|--------|---------|---------|--------|
| `PermissionChecker.check()` | `security/policy.py:132-133` | `SecurityConfig.shell_allowed_commands` | `['ls', 'cat', 'echo', 'grep', 'find', 'git', 'pwd', 'cd', 'mkdir', 'cp', 'mv', 'head', 'tail', 'wc']` |
| `ShellTool._is_safe_command()` | `tools/shell_tool.py:29` | `ShellTool.allowed_commands` | 同上 |

两套列表互不感知，`api.py` 传入 `ShellTool(allowed_commands=[...])` 只能控制第二套，但**第一套的默认值仍然没有 `rm`**。

---

## 2. 执行流程详解

### 2.1 完整调用链

```
前端 ChatView.vue
    └─> chatStore.sendMessage()
        └─> apiClient.chat()
            └─> POST /api/chat/stream

后端 api.py (chat_stream 端点)
    ├─> 创建 ToolRegistry
    ├─> 注册 ShellTool(allowed_commands=["ls", ..., "rm", ...])  ← 第二套
    ├─> 创建 SecurityConfig(shell_allowed_commands=[默认值: 无 rm])  ← 第一套
    ├─> 创建 ToolWrapper(enable_security=True)
    ├─> 创建 ApprovalManager（单例）
    ├─> wrapper.approver.set_approval_manager(manager)
    └─> 创建 StreamingReActLoop

StreamingReActLoop.process_streaming()
    └─> LLM 返回 tool_calls
        └─> _group_by_risk()
            └─> HIGH 风险组
                ├─> _approval_manager.enqueue(request)
                ├─> EventManager.publish("approval_required", ...)
                └─> await _approval_manager.wait(id) [阻塞]

ToolWrapper.execute() — 安全开启时执行顺序
    第69行: permission.risk_level = checker.assess_risk(permission)
    第72行: allowed, reason = checker.check(permission)  ← 【第一道关卡】
    第74行: if not allowed → 直接拒绝，不进入审批流程！
    第91行: approved = await approver.request(permission)
    第111行: result = await tool.execute(**kwargs)
```

### 2.2 两层安全校验的职责划分

#### 第一层：PermissionChecker.check()（checker.py:72，wrapper.py 调用）

```python
# policy.py:54-67
def _check_shell_permission(self, perm: Permission) -> tuple[bool, str]:
    cmd = parts[0].lower()
    if cmd not in self.config.shell_allowed_commands:
        return False, f"Command '{cmd}' not in allowed list: {self.config.shell_allowed_commands}"
    # 检查黑名单正则...
    return True, "Allowed"
```

- **校验**：`SecurityConfig.shell_allowed_commands`
- **行为**：不在列表中 → **立即拒绝**，审批流程不会执行
- **默认值**（policy.py:132-133）：无 `rm`、`dir`、`python`、`pip`、`uv`

#### 第二层：ShellTool._is_safe_command()（shell_tool.py:71-84）

```python
# shell_tool.py:71-84
def _is_safe_command(self, command: str) -> bool:
    parts = shlex.split(command)
    cmd = parts[0]
    return cmd in self.allowed_commands  # 来自显式传入的 allowed_commands
```

- **校验**：`ShellTool(allowed_commands=[...])` 传入的列表
- **行为**：不在列表中 → 返回 `False`，工具执行失败

### 2.3 为什么 rm 被直接拒绝而不走审批

`wrapper.py:72-88`：
```python
allowed, reason = self.checker.check(permission)  # 第一层检查

if not allowed:
    # 审计日志
    return ToolResult(success=False, content="", error=f"Permission denied: {reason}")
    # ← 审批流程（第91行）永远不会执行到这里！
```

两层的关系：
- `PermissionChecker.check()` 是**门卫**，直接说"不在名单里，拒绝"
- `PermissionChecker.assess_risk()` 只返回风险等级，不执行拒绝
- 审批流程在 `Approver.request()` 中，**只对已通过 check 的请求生效**

---

## 3. 相关文件清单

| 文件 | 作用 | 关键行号 |
|------|------|----------|
| `aloha/web/service/api.py` | API 端点 + ShellTool 注册 | 456-478（chat_stream）|
| `aloha/agent/wrapper.py` | 工具执行拦截器 | 42-107（execute）|
| `aloha/security/checker.py` | 权限校验 | 20-36（check），54-77（_check_shell_permission），127-147（assess_risk）|
| `aloha/security/approver.py` | 审批流程 | 30-61（request）|
| `aloha/security/policy.py` | SecurityConfig 定义 | 113-155 |
| `aloha/tools/shell_tool.py` | Shell 工具实现 | 20-29（__init__允许列表），71-84（_is_safe_command）|
| `aloha/agent/loop.py` | ReActLoop + StreamingReActLoop | 302-473 |
| `aloha/agent/approval_manager.py` | 审批队列管理 | 全文 |
| `aloha/web/service/events.py` | SSE 事件管理 | 全文 |

---

## 4. 修复方案

### 4.1 问题定位

`SecurityConfig.shell_allowed_commands` 的默认值缺少 `rm`，导致 `PermissionChecker.check()` 在第一道关卡就拒绝了 `rm`，根本走不到 `ShellTool._is_safe_command()` 和审批流程。

### 4.2 修复内容

| 位置 | 文件 | 行号 | 修复前 | 修复后 |
|------|------|------|--------|--------|
| `SecurityConfig.shell_allowed_commands` | `policy.py` | 133 | 无 `rm` | 加 `rm` |
| `ShellTool.allowed_commands` 默认值 | `shell_tool.py` | 29 | 无 `rm` | 加 `rm` |
| `api.py` ShellTool 显式列表 | `api.py` | 457-477 | ✅ 已有 `rm` | 无需修改 |
| `__main__.py` ShellTool 列表 | `__main__.py` | 95-114, 182-203 | ✅ 已有 `rm` | 无需修改 |

---

## 5. 工具审批模式详解

### 5.1 安全关闭时（enable_security=False）

```python
# wrapper.py:64-65
if not self.enable_security:
    return await tool.execute(**kwargs)  # 直接执行，跳过所有检查
```

### 5.2 安全开启时（enable_security=True）

```
请求到达
  └─> PermissionChecker.check()        ← 门卫：不在 shell_allowed_commands → 直接拒绝
        ├─ 通过
        └─> PermissionChecker.assess_risk()  ← 评估风险等级
              ├─ LOW（无需审批）→ 直接执行
              └─ HIGH/MEDIUM
                    └─> Approver.request()
                          ├─ 有 ApprovalManager → SSE 异步审批流程（阻塞等待）
                          ├─ 有 ApprovalCallback → 调用回调
                          └─ 无 → 直接拒绝
```

### 5.3 三种审批模式

| 模式 | 触发条件 | 行为 |
|------|----------|------|
| **自动通过** | `RiskLevel=LOW` 且 `auto_approve_low_risk=True` | 跳过审批，直接执行 |
| **SSE 异步审批** | `_approval_manager` 已设置（Web/SSE 模式） | 阻塞等待前端响应 |
| **回调审批** | `approval_callback` 已设置（CLI 模式） | 调用回调函数 |
| **直接拒绝** | 以上均不满足 | 无审批机制，拒绝执行 |

---

## 6. SSE 审批流程

### 6.1 事件流

```
Backend                          Frontend
  │                                  │
  │  EventManager.publish()          │
  │  event: approval_required ────► │  显示 ToolApprovalCard
  │                                  │
  │                                  │  用户点击批准/拒绝
  │◄─── POST /api/approvals/{id} ───│
  │                                  │
  │  ApprovalManager.resolve()       │
  │  wait() 返回结果                  │
  │                                  │
  │  执行工具（如果批准）              │
  │                                  │
  │  EventManager.publish()          │
  │  event: tool_result ─────────►  │  更新界面
  │  event: message ─────────────►   │  显示最终回复
```

### 6.2 SSE 事件类型

| 事件名 | 方向 | 说明 |
|--------|------|------|
| `approval_required` | 后端→前端 | 工具需要审批 |
| `approval_completed` | 后端→前端 | 审批完成（批准/拒绝）|
| `approval_timeout` | 后端→前端 | 5分钟超时 |
| `tool_result` | 后端→前端 | 工具执行结果 |
| `thinking` | 后端→前端 | 思考内容（追加）|
| `message` | 后端→前端 | 最终回复 |
| `heartbeat` | 后端→前端 | 保活（每5秒）|
| `error` | 后端→前端 | 错误 |

### 6.3 审批队列

- FIFO 队列，一次只处理一个 `approval_required`
- `queue_position` / `queue_total` 告知前端排队位置
- 幂等性：`_resolved` 字典防止重复审批

### 6.4 幂等性

```python
# approval_manager.py
_resolved: dict[str, ApprovalDecision]  # 已完成的审批

def resolve(self, approval_id, decision, reason):
    if approval_id in self._resolved:
        return False  # 幂等：重复 resolve 返回 False
```

---

## 7. 风险评估逻辑

### 7.1 风险等级（PermissionChecker.assess_risk）

| 工具 | 操作 | 风险等级 |
|------|------|----------|
| shell | 任意命令 | HIGH |
| file | write/create/execute | HIGH |
| file | read | MEDIUM |
| web | 任意 | MEDIUM |
| 其他 | 任意 | LOW |

### 7.2 黑名单正则（不区分大小写）

```
rm\s+-rf     → 递归强制删除（危险）
del\s+/[sq]  → Windows 强制删除
format\s+[a-z]: → 格式化磁盘
>\s*/dev/    → 输出到设备文件
```

---

## 8. 配置修改记录

| 日期 | 修改内容 | 文件 |
|------|---------|------|
| 2026-04-04 | `rm` 加入 `api.py` ShellTool 显式列表 | `api.py` |
| 2026-04-04 | `rm` 加入 `__main__.py` ShellTool 列表 | `__main__.py` |
| 2026-04-04 | `rm` 加入 `SecurityConfig.shell_allowed_commands` 默认值 | `policy.py` |
| 2026-04-04 | `rm` 加入 `ShellTool.allowed_commands` 默认值 | `shell_tool.py` |
