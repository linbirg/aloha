# Aloha Agent

**Aloha** 是一个轻量级 Python AI Agent 框架（Python 3.10+），基于 nanobot 架构设计。支持会话/任务管理、分层技能、灵活 prompt、记忆管理和带安全审批控制的工具系统。

```
版本: 0.1.0
```

---

## 核心特性

| 特性 | 说明 |
|------|------|
| **ReAct Agent 循环** | 主流的思考-行动循环，工具调用与 LLM 推理交替进行 |
| **多 Provider 支持** | OpenAI、MiniMax、Anthropic、DeepSeek、OpenRouter 等 OpenAI 兼容接口 |
| **内置工具** | `FileTool`（文件读写）、`ShellTool`（命令执行）、`WebTool`（HTTP 请求） |
| **安全审批** | 三级风险等级（LOW/MEDIUM/HIGH），高风险操作需用户审批 |
| **实时 SSE 推送** | 工具审批请求、LLM thinking 过程、消息流通过 SSE 实时推送到前端 |
| **流式响应** | `StreamingReActLoop` 支持端到端流式，LLM token 增量输出 |
| **记忆系统** | 会话记忆（SessionMemory）+ 长期记忆（LongTermMemory） |
| **技能系统** | 分层技能加载（SkillsLoader），支持在运行时动态挂载 |
| **Vue 3 前端** | 基于 Pinia + Vue Router 的 Web 交互界面 |

---

## 快速开始

### 安装依赖

```bash
cd aloha
pip install -r requirements.txt
```

### 配置 API Key

在 `~/.aloha/config.toml`（或 `config.json`）中配置 Provider：

```toml
[providers.minimax]
api_key = "your-api-key"
base_url = "https://api.minimaxi.com/v1"
default_model = "MiniMax-M2.7"
```

优先级：`~/.aloha/config.toml` > 项目 `config.toml` > 环境变量 > 代码默认值。

### 运行交互式 Chat

```bash
cd aloha
python -m aloha chat
```

### 运行单条消息

```bash
python -m aloha say "你好，帮我整理一下工作目录"
```

### 启动 Web 前端

```bash
# 后端 API 服务
cd aloha
pip install fastapi uvicorn
python -m aloha web

# 前端开发服务器（另一个终端）
cd aloha/web
npm install
npm run dev
```

---

## 项目结构

```
aloha/
├── agent/               # 核心 Agent 逻辑
│   ├── base.py         # Agent 抽象基类
│   ├── loop.py         # ReActLoop + StreamingReActLoop
│   ├── tools.py        # BaseTool、ToolResult、ToolRegistry
│   ├── wrapper.py      # ToolWrapper（安全拦截器）
│   ├── skills.py       # SkillsLoader 技能加载器
│   ├── events.py       # ApprovalRequest、RiskLevel
│   └── approval_manager.py  # ApprovalManager（审批队列 + 超时）
├── bus/                # 消息总线（队列式 pub/sub）
├── config/             # 配置系统（Pydantic schema）
│   └── schema.py       # AlohaConfig
├── lib/                # 工具库
│   └── logger.py       # 日志模块
├── memory/             # 记忆系统
│   ├── session.py      # SessionMemory
│   └── longterm.py     # LongTermMemory
├── providers/          # LLM Provider
│   ├── base.py         # BaseProvider、Message、Response、ToolCall
│   ├── openai_provider.py
│   └── minimax_provider.py
├── prompts/            # Prompt 模板加载器
│   └── loader.py       # PromptLoader
├── security/           # 安全策略与审批
│   ├── policy.py       # RiskLevel、Permission、SecurityConfig
│   ├── checker.py      # PermissionChecker
│   ├── approver.py     # Approver（同步/异步审批）
│   └── audit.py        # AuditLogger
├── skills/             # 技能系统
├── templates/prompts/  # 默认 Prompt 模板
│   ├── SOUL.md         # Agent 核心价值观
│   ├── AGENT.md        # Agent 行为定义
│   ├── RULES.md        # 工具使用规则
│   ├── SYSTEM.md       # 系统级指令
│   └── USER.md         # 用户交互模板
├── tools/              # 内置工具
│   ├── file_tool.py    # 文件读写（目录白名单）
│   ├── shell_tool.py   # Shell 命令（命令白名单 + 模式黑名单）
│   └── web_tool.py     # HTTP 请求（域名白名单 + 速率限制）
├── web/                # Vue 3 前端
│   ├── src/
│   │   ├── components/ # MessageBubble、ToolApprovalCard、ChatInput...
│   │   ├── stores/      # Pinia stores（chat、events）
│   │   ├── composables/ # useApprovalEvents（SSE 订阅）
│   │   ├── views/       # ChatView
│   │   └── api/         # API client
│   └── service/
│       ├── api.py       # FastAPI 后端
│       └── events.py    # EventManager（SSE 发布/订阅）
└── test/               # 测试套件
```

---

## 安全模型

### 风险等级

| 等级 | 值 | 行为 |
|------|-----|------|
| `LOW` | 低 | 自动批准（若 `auto_approve_low_risk=True`）|
| `MEDIUM` | 中 | 需用户明确审批 |
| `HIGH` | 高 | 需用户明确审批 |

### 工具风险对应

| 工具 | 操作 | 风险等级 |
|------|------|---------|
| `shell` | execute | HIGH |
| `file` | write | HIGH |
| `file` | read | MEDIUM |
| `web` | any | MEDIUM |

### 两层 Allow List

`ShellTool` 的 `rm` 等危险命令曾在两层独立的白名单中被拦截：

1. **`PermissionChecker.check()`** — `SecurityConfig.shell_allowed_commands`（`security/policy.py`）
2. **`ShellTool._is_safe_command()`** — `ShellTool.allowed_commands`（`tools/shell_tool.py`）

需同时在两层添加命令才能放行。

### 审批流程

```
ToolWrapper (wrapper.py)
  └── PermissionChecker.check()        ← 第一层：风险评估 + 白名单校验
       └── Approver.request()           ← 第二层：用户审批（LOW 自动跳过）
            ├── auto_approve (LOW)      ← 同步直接返回
            ├── wait() (MEDIUM/HIGH)    ← 阻塞等待用户决策
            └── ApprovalManager         ← SSE 模式下异步 Future
                 └── SSE 推送 → 前端 ToolApprovalCard → 用户点击 → 审批结果
```

---

## SSE 实时事件系统

`StreamingReActLoop` 通过 `EventManager` 实时推送以下事件到前端：

| 事件 | 内容 | 说明 |
|------|------|------|
| `heartbeat` | `{timestamp}` | 保活心跳（每 2 秒）|
| `approval_required` | `ApprovalRequest` | 需要用户审批 |
| `tool_result` | `{tool_call_id, success, content}` | 工具执行结果 |
| `approval_completed` | `{approval_id, decision}` | 审批已完成 |
| `thinking` | `{content}` | LLM thinking 增量 |
| `message` | `{message}` | 最终助手消息 |

前端通过 `EventSource` 连接 `/api/events?session_id=xxx`，审批结果提交到 `POST /api/approvals/{id}`。

---

## 内置工具

### FileTool

文件读写工具，通过 `allowed_read_dirs` / `allowed_write_dirs` 白名单限制访问范围。

### ShellTool

命令执行工具，通过 `allowed_commands` 白名单和 `blocked_patterns` 黑名单双重保护。

默认白名单命令：`cat, cd, cp, echo, grep, ls, mkdir, mv, ps, pwd, rm, sed, sort, tail, tee, touch, tree, which, xargs`

> `rm` 在两层白名单中均已默认添加（v0.1.0+）

### WebTool

HTTP 请求工具，通过 `allowed_domains` 白名单限制可访问域名，支持速率限制。

---

## 测试

```bash
# 运行所有测试
cd aloha && pytest

# 运行单个测试文件
cd aloha && pytest aloha/test/test_agent.py -v

# 仅运行单元测试
cd aloha && pytest -m unit

# 运行带覆盖率
cd aloha && pytest --cov=aloha --cov-report=term-missing
```

---

## 配置示例

### TOML（`~/.aloha/config.toml`）

```toml
[agents.defaults]
workspace = "~/.aloha/workspace"
model = "MiniMax-M2.7"
provider = "openai"
max_tokens = 8192
context_window_tokens = 65536
temperature = 0.1
max_tool_iterations = 40

[providers.minimax]
api_key = "your-api-key"
base_url = "https://api.minimaxi.com/v1"
default_model = "MiniMax-M2.7"
temperature = 0.1
max_tokens = 8192

[tools]
restrict_to_workspace = false
```

详细配置说明参见 [doc/config.md](aloha/doc/config.md)。

---

## 添加自定义工具

```python
from aloha.agent import BaseTool, ToolResult, ToolRegistry

class MyTool(BaseTool):
    def __init__(self):
        super().__init__(name="mytool", description="我的自定义工具")

    async def execute(self, **kwargs) -> ToolResult:
        return ToolResult(success=True, content="执行结果")

registry = ToolRegistry()
registry.register(MyTool())
```

---

## License

MIT
