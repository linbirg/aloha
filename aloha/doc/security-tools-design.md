# AI Agent 基础工具与权限控制系统 - 设计方案

## 一、设计目标

实现基础的工具（文件读写、网页访问、命令执行），结合安全控制研究，实现权限提示、审批、授权功能。

## 二、核心需求

- **权限粒度**：操作级 - 同一工具不同操作需要分别授权（例如 file_read 可读所有文件，但 file_write 只能写特定目录）
- **处理方式**：同步阻塞 - Agent 调用工具时暂停，等待用户批准/拒绝
- **初始工具**：文件读写、命令行执行、网页访问（后续可扩展）
- **架构选择**：中间件/代理模式 - 创建一个工具包装器拦截所有工具调用，权限检查在包装器中完成

## 三、系统架构

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Agent     │────▶│  ToolWrapper      │────▶│   基础工具       │
│  (LLM +     │     │  (权限拦截器)      │     │  - FileTool    │
│   Loop)     │     │                  │     │  - ShellTool   │
└─────────────┘     │  - 权限检查        │     │  - WebTool     │
                    │  - 审批流程        │     └─────────────────┘
                    │  - 审计日志        │
                    └──────────────────┘
```

## 四、组件设计

### 1. 工具层 (`aloha/tools/`)

| 工具 | 功能 | 权限控制点 |
|------|------|-----------|
| `FileTool` | 文件读写 | 读：可配置目录白名单；写：限制目录和文件类型 |
| `ShellTool` | 命令执行 | 限制可执行命令、参数检查、危险命令拦截 |
| `WebTool` | 网页访问 | 域名白名单、请求频率限制 |

### 2. 权限控制器 (`aloha/security/`)

```
aloha/security/
├── __init__.py
├── policy.py       # 权限策略定义
├── checker.py      # 权限检查器
├── approver.py     # 审批工作流
└── audit.py        # 审计日志
```

### 3. 配置层 (`aloha/config/`)

```python
# config/security.py
class SecurityConfig:
    file_read_allowed_dirs: list[str]  # 允许读取的目录
    file_write_allowed_dirs: list[str]  # 允许写入的目录
    shell_allowed_commands: list[str]   # 允许执行的命令
    shell_blocked_patterns: list[str]   # 禁止的命令模式
    web_allowed_domains: list[str]      # 允许访问的域名
```

## 五、权限控制流程

```
Agent 调用工具
      │
      ▼
ToolWrapper 拦截
      │
      ▼
权限检查 (PermissionChecker)
      │
      ├── 通过 ──▶ 执行工具 ──▶ 审计日志 ──▶ 返回结果
      │
      └── 拒绝 ──▶ 触发审批流程 (Approver)
                      │
                      ▼
              等待用户批准/拒绝
                      │
              ├── 批准 ──▶ 记录授权 ──▶ 执行工具
              └── 拒绝 ──▶ 返回拒绝信息
```

## 六、关键技术点

### 1. 权限策略定义

```python
@dataclass
class Permission:
    tool: str           # 工具名称
    action: str        # 操作类型 (read/write/execute)
    resource: str       # 资源路径
    risk_level: RiskLevel  # 风险级别
    
class RiskLevel(Enum):
    LOW = "low"         # 自动通过
    MEDIUM = "medium"  # 需要提示
    HIGH = "high"      # 需要审批
```

### 2. 审批回调机制

```python
class ApprovalCallback(Protocol):
    async def request_approval(self, permission: Permission) -> bool:
        """请求用户批准，返回是否批准"""
        pass
    
    async def notify(self, message: str) -> None:
        """通知用户"""
        pass
```

### 3. 审计日志

```python
@dataclass
class AuditLog:
    timestamp: datetime
    tool: str
    action: str
    resource: str
    result: str  # approved/rejected/error
    user_response: str | None
```

## 七、文件结构

```
aloha/
├── tools/
│   ├── __init__.py
│   ├── base.py           # 已存在：BaseTool, ToolResult
│   ├── registry.py       # 已存在：工具注册表
│   ├── file.py           # 新增：文件读写工具
│   ├── shell.py          # 新增：命令执行工具
│   └── web.py            # 新增：网页访问工具
│
├── security/             # 新增：权限控制模块
│   ├── __init__.py
│   ├── policy.py         # 权限策略
│   ├── checker.py        # 权限检查器
│   ├── approver.py       # 审批流程
│   └── audit.py          # 审计日志
│
├── config/
│   ├── security.py       # 新增：安全配置
│   └── schema.py         # 已存在
│
└── agent/
    ├── loop.py           # 已存在
    └── wrapper.py        # 新增：ToolWrapper 包装器
```

## 八、实现顺序建议

1. **第一阶段：基础工具**
   - 实现 FileTool（文件读写）
   - 实现 ShellTool（命令执行）
   - 实现 WebTool（网页访问）

2. **第二阶段：权限框架**
   - 实现 SecurityConfig 配置类
   - 实现 Permission 数据结构
   - 实现 PermissionChecker 权限检查器

3. **第三阶段：审批流程**
   - 实现 ApprovalCallback 协议
   - 实现同步阻塞审批流程
   - 实现审计日志模块

4. **第四阶段：集成**
   - 实现 ToolWrapper 包装器
   - 与 Agent Loop 集成
   - 端到端测试

## 九、参考文档

- `doc/agent-research.md` - AI Agent 架构设计与安全控制研究
- 包含：第一部分 Anthropic 长时间运行 Agent 方案、第二部分安全控制方案、第三部分连续性保障方案