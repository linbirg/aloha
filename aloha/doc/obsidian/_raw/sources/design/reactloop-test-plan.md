# ReActLoop 单元测试计划

## 1. 测试概述

本测试计划针对 `ReActLoop` 的核心逻辑进行全面测试，主要包括：
- ReAct 主循环逻辑（工具调用循环）
- 权限检查逻辑（PermissionChecker）
- 审批流程逻辑（Approver）
- 工具包装器（ToolWrapper）集成

## 2. 测试架构

```
┌─────────────────────────────────────────────────────────────┐
│                      Test Architecture                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │   Mock LLM   │───▶│  ReActLoop    │───▶│ ToolWrapper  │  │
│  │   Provider   │    │   (Agent)     │    │ (Security)   │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│         │                   │                   │            │
│         ▼                   ▼                   ▼            │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              Test Double Layer                           │ │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────────┐    │ │
│  │  │MockTool    │  │MockApprover│  │MockPermission  │    │ │
│  │  │            │  │            │  │Checker         │    │ │
│  │  └────────────┘  └────────────┘  └────────────────┘    │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## 3. 测试模块与用例

### 3.1 ReActLoop 工具调用循环测试

#### 3.1.1 TestReActLoopToolExecution

| 用例ID | 测试场景 | 测试输入 | 预期结果 |
|--------|----------|----------|----------|
| REACT-001 | 无工具调用的简单响应 | LLM返回纯文本响应 | 返回响应内容，不执行工具 |
| REACT-002 | 单次工具调用 | LLM返回1个工具调用 | 执行工具，返回结果 |
| REACT-003 | 多次工具调用 | LLM返回2+个工具调用 | 顺序执行所有工具 |
| REACT-004 | 工具调用循环-成功 | 工具执行后LLM返回最终响应 | 循环结束，返回最终响应 |
| REACT-005 | 工具调用循环-继续 | 工具执行后LLM返回新工具调用 | 继续循环执行 |
| REACT-006 | 工具执行失败处理 | 工具执行返回失败 | 记录失败日志，不添加工具消息 |
| REACT-007 | 达到最大迭代次数 | 超过5次工具调用 | 停止循环，返回当前内容 |
| REACT-008 | 空工具调用列表 | tool_calls为空 | 直接返回响应内容 |

#### 3.1.2 TestReActLoopMessageBuilding

| 用例ID | 测试场景 | 测试输入 | 预期结果 |
|--------|----------|----------|----------|
| MSG-001 | 构建带系统提示的消息 | system_prompt设置 | 消息包含system role |
| MSG-002 | 构建带会话历史的消息 | session_memory有历史 | 消息包含history消息 |
| MSG-003 | 工具结果消息添加 | 工具执行成功 | 添加tool role消息 |
| MSG-004 | 工具失败不添加消息 | 工具执行失败 | 不添加工具消息 |

### 3.2 ToolWrapper 权限拦截测试

#### 3.2.1 TestToolWrapperExecute

| 用例ID | 测试场景 | 测试输入 | 预期结果 |
|--------|----------|----------|----------|
| WRAP-001 | 安全禁用时直接执行 | enable_security=False | 跳过权限检查，直接执行 |
| WRAP-002 | 工具不存在 | tool_name不存在 | 返回ToolResult(success=False) |
| WRAP-003 | 权限检查拒绝 | PermissionChecker返回False | 拒绝执行，返回错误 |
| WRAP-004 | 审批被拒绝 | Approver.request()返回False | 拒绝执行，记录审计 |
| WRAP-005 | 审批通过-执行成功 | 所有检查通过 | 执行工具，返回成功结果 |
| WRAP-006 | 审批通过-执行失败 | 工具执行抛出异常 | 返回ToolResult(success=False) |
| WRAP-007 | 审计日志记录 | 任何执行 | 审计日志包含执行记录 |

#### 3.2.2 TestToolWrapperPermissionBuilding

| 用例ID | 测试场景 | 测试输入 | 预期结果 |
|--------|----------|----------|----------|
| PERM-001 | 构建文件工具权限 | tool_name="file" | 正确提取path参数 |
| PERM-002 | 构建shell工具权限 | tool_name="shell" | 正确提取command参数 |
| PERM-003 | 构建web工具权限 | tool_name="web" | 正确提取url参数 |

### 3.3 PermissionChecker 权限检查测试

#### 3.3.1 TestFilePermissionCheck

| 用例ID | 测试场景 | 测试输入 | 预期结果 |
|--------|----------|----------|----------|
| FILE-001 | 允许目录内的文件-read | path在allowed_dirs | (True, "Allowed by whitelist") |
| FILE-002 | 允许目录外的文件-read | path不在allowed_dirs且不在cwd | (False, "not in allowed dirs") |
| FILE-003 | CWD内的文件-read | path在当前目录 | (True, "in current working directory") |
| FILE-004 | 允许目录内的文件-write | path在allowed_dirs | (True, "Allowed by whitelist") |
| FILE-005 | 阻塞扩展名-write | .exe/.dll等 | (False, "extension is blocked") |
| FILE-006 | 目录外非CWD-write | path不在allowed_dirs且不在cwd | (False, "not in allowed dirs") |

#### 3.3.2 TestShellPermissionCheck

| 用例ID | 测试场景 | 测试输入 | 预期结果 |
|--------|----------|----------|----------|
| SHELL-001 | 允许的命令 | command在allowed列表 | (True, "Allowed") |
| SHELL-002 | 不允许的命令 | command不在allowed列表 | (False, "not in allowed list") |
| SHELL-003 | 空命令 | command="" | (False, "Empty command") |
| SHELL-004 | 匹配黑名单模式 | command匹配blocked_pattern | (False, "matches blocked pattern") |
| SHELL-005 | 大小写不敏感 | Command="LS" | (True, "Allowed") |

#### 3.3.3 TestWebPermissionCheck

| 用例ID | 测试场景 | 测试输入 | 预期结果 |
|--------|----------|----------|----------|
| WEB-001 | 允许所有域名 | web_allowed_domains=["*"] | (True, "All domains allowed") |
| WEB-002 | 白名单域名 | domain在列表中 | (True, "Allowed by whitelist") |
| WEB-003 | 白名单子域名 | domain=example.com, allowed=com | (True, "Allowed by whitelist") |
| WEB-004 | 不允许的域名 | domain不在列表 | (False, "not in allowed list") |
| WEB-005 | 无效URL | 无效的resource | (False, "Invalid URL") |

#### 3.3.4 TestRiskAssessment

| 用例ID | 测试场景 | 测试输入 | 预期结果 |
|--------|----------|----------|----------|
| RISK-001 | Shell工具高风险 | tool="shell" | RiskLevel.HIGH |
| RISK-002 | 文件写高风险 | tool="file", action="write" | RiskLevel.HIGH |
| RISK-003 | 文件读中风险 | tool="file", action="read" | RiskLevel.MEDIUM |
| RISK-004 | Web操作中风险 | tool="web" | RiskLevel.MEDIUM |

### 3.4 Approver 审批流程测试

#### 3.4.1 TestApprovalRequest

| 用例ID | 测试场景 | 测试输入 | 预期结果 |
|--------|----------|----------|----------|
| APRV-001 | 低风险自动通过 | risk_level=LOW, auto_approve=True | True |
| APRV-002 | 低风险关闭自动通过 | risk_level=LOW, auto_approve=False | 回调结果 |
| APRV-003 | 中风险需要审批 | risk_level=MEDIUM | 调用approval_callback |
| APRV-004 | 高风险需要审批 | risk_level=HIGH | 调用approval_callback |
| APRV-005 | 回调异常时拒绝 | callback抛出异常 | False |
| APRV-006 | 无回调默认拒绝 | approval_callback=None | False |

#### 3.4.2 TestBlockingApproval

| 用例ID | 测试场景 | 测试输入 | 预期结果 |
|--------|----------|----------|----------|
| BLOCK-001 | 超时测试 | 审批超时 | 返回False |
| BLOCK-002 | 带超时的回调 | callback支持timeout | 使用回调的超时 |
| BLOCK-003 | 不支持超时的回调 | callback不支持timeout | 使用asyncio.wait_for |

#### 3.4.3 TestApprovalPrompt

| 用例ID | 测试场景 | 测试输入 | 预期结果 |
|--------|----------|----------|----------|
| PROMPT-001 | 低风险提示 | risk=LOW | 包含🟢 emoji |
| PROMPT-002 | 中风险提示 | risk=MEDIUM | 包含🟡 emoji |
| PROMPT-003 | 高风险提示 | risk=HIGH | 包含🔴 emoji |
| PROMPT-004 | 提示内容完整性 | 完整permission | 包含tool/action/resource/risk |

## 4. 测试数据设计

### 4.1 Mock工具

```python
class MockTool(BaseTool):
    """用于测试的模拟工具"""
    def __init__(self, should_succeed: bool = True):
        super().__init__(name="mock_tool", description="Mock tool")
        self.should_succeed = should_succeed
    
    async def execute(self, **kwargs) -> ToolResult:
        if self.should_succeed:
            return ToolResult(success=True, content=f"Executed: {kwargs}")
        return ToolResult(success=False, content="", error="Mock failure")
```

### 4.2 Mock审批回调

```python
class MockApprovalCallback:
    """模拟审批回调"""
    def __init__(self, should_approve: bool = True):
        self.should_approve = should_approve
        self.called = False
        self.received_permission = None
    
    async def request_approval(self, permission: Permission) -> bool:
        self.called = True
        self.received_permission = permission
        return self.should_approve
```

### 4.3 Mock Provider

```python
class MockLLMProvider:
    """模拟LLM Provider - 支持工具调用"""
    def __init__(self, responses: list[Response]):
        self.responses = responses
        self.call_count = 0
    
    async def chat_with_tools(self, messages, tools, model) -> Response:
        resp = self.responses[self.call_count]
        self.call_count += 1
        return resp
```

## 5. 测试环境要求

- Python 3.10+
- pytest
- pytest-asyncio
- unittest.mock

## 6. 执行策略

1. **单元测试**：每个模块独立测试，使用Mock隔离依赖
2. **集成测试**：测试ReActLoop与ToolWrapper的集成
3. **执行顺序**：
   - 先运行单元测试（PermissionChecker, Approver）
   - 再运行集成测试（ToolWrapper, ReActLoop）

## 7. 覆盖率目标

| 模块 | 目标覆盖率 |
|------|------------|
| ReActLoop._handle_response | 90%+ |
| ReActLoop._execute_tool | 90%+ |
| ToolWrapper.execute | 90%+ |
| PermissionChecker | 95%+ |
| Approver | 90%+ |