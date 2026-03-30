# Aloha 重构设计方案

## 概述

本文档定义了 Aloha 项目的重构计划，目标是简化代码、修复不合理的地方、明确职责边界。

## 现状分析

### 当前模块结构

```
aloha/
├── agent/        # Agent 核心（base.py, loop.py, skills.py, tools.py, wrapper.py）
├── providers/   # LLM 提供商（base.py, openai_provider.py, minimax_provider.py）
├── tools/        # 工具（file_tool.py, shell_tool.py, web_tool.py）
├── security/     # 安全（approver.py, audit.py, checker.py, policy.py）
├── memory/       # 内存（session.py, longterm.py）
├── bus/          # 消息总线（queue.py）
├── config/       # 配置（schema.py）
├── prompts/     # 提示词（loader.py）
├── lib/          # 日志（logger.py）
├── examples/     # 示例（chat_with_ai.py 574行, simple_agent.py, with_skills.py）
├── web/          # Vue.js Web UI
├── test/         # 测试
└── templates/    # 提示词模板
```

### 发现的问题

| 模块 | 问题 | 严重程度 |
|------|------|----------|
| **agent/** | base.py 与 loop.py 职责边界不清 | 高 |
| **agent/** | 缺少事件系统（无流式回调） | 高 |
| **agent/** | tools.py 与 wrapper.py 功能重叠 | 中 |
| **security/** | approver.py、checker.py、policy.py 职责重叠 | 高 |
| **security/** | 权限审批流程过于复杂 | 中 |
| **providers/** | 抽象基类有冗余方法 | 低 |
| **tools/** | 三个工具缺少统一基类 | 中 |
| **examples/** | chat_with_ai.py 使用 Gradio，应删除 | 高 |
| **web/** | 不再与 Gradio 混合，Web UI 独立 | 中 |

## 重构目标

### 1. 核心轻量化
- 将示例代码移出主项目
- 保持核心库精简专注

### 2. 职责分离
- 每个模块有清晰单一的职责
- 模块间通过明确定义的接口通信

### 3. 事件驱动
- 添加简单的事件系统
- 支持流式响应回调

### 4. 统一抽象
- 工具统一基类
- Provider 统一接口

---

## 第一部分：Agent 模块重构

### 现状

```
agent/
├── base.py       # Agent 抽象基类（55行）
├── loop.py       # ReActLoop 实现（277行）
├── skills.py     # Skills 加载（待分析）
├── tools.py      # ToolRegistry（与 wrapper.py 重叠）
└── wrapper.py    # ToolWrapper 权限包装
```

### 设计目标

1. **分离抽象与实现** - Agent 基类只定义接口，ReActLoop 实现具体逻辑
2. **引入事件系统** - 支持 agent_start、message_update、tool_execution 等事件
3. **统一工具注册** - ToolRegistry 独立，ToolWrapper 作为装饰器

### 新结构

```
agent/
├── __init__.py           # 导出
├── base.py               # Agent 抽象基类（精简）
├── react.py              # ReActLoop 实现
├── events.py             # 事件系统定义
├── registry.py           # ToolRegistry（从 tools.py 提取）
└── hooks.py              # Hooks 定义（before_tool_call, after_tool_call）
```

### 事件系统设计

```python
# events.py
from enum import Enum
from dataclasses import dataclass
from typing import Any

class EventType(Enum):
    AGENT_START = "agent_start"
    AGENT_END = "agent_end"
    TURN_START = "turn_start"
    TURN_END = "turn_end"
    MESSAGE_START = "message_start"
    MESSAGE_UPDATE = "message_update"  # 流式更新
    MESSAGE_END = "message_end"
    TOOL_EXECUTION_START = "tool_execution_start"
    TOOL_EXECUTION_UPDATE = "tool_execution_update"
    TOOL_EXECUTION_END = "tool_execution_end"

@dataclass
class AgentEvent:
    type: EventType
    data: dict[str, Any]
    timestamp: float

class EventEmitter:
    """简单事件发射器"""
    def __init__(self):
        self._handlers: dict[EventType, list[callable]] = {}
    
    def on(self, event_type: EventType, handler: callable):
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
    
    def emit(self, event: AgentEvent):
        for handler in self._handlers.get(event.type, []):
            handler(event)
```

### Agent 基类设计

```python
# base.py
from abc import ABC, abstractmethod
from typing import Any

class Agent(ABC):
    """Agent 抽象基类"""
    
    @abstractmethod
    async def process(self, user_input: str) -> str:
        """处理用户输入"""
        pass
    
    @abstractmethod
    async def run(self) -> None:
        """运行 agent"""
        pass
    
    # 事件支持
    def on(self, event_type: EventType, handler: callable):
        self._events.on(event_type, handler)
    
    def emit(self, event: AgentEvent):
        self._events.emit(event)
```

### Hooks 设计

```python
# hooks.py
from dataclasses import dataclass
from typing import Any

@dataclass
class ToolCallContext:
    tool_name: str
    args: dict[str, Any]
    tool_call_id: str

@dataclass  
class ToolResultContext:
    tool_name: str
    result: Any
    is_error: bool

class Hooks:
    """工具执行钩子"""
    
    def __init__(self):
        self._before_tool_call: list[callable] = []
        self._after_tool_call: list[callable] = []
    
    def before_tool_call(self, fn: callable):
        self._before_tool_call.append(fn)
    
    def after_tool_call(self, fn: callable):
        self._after_tool_call.append(fn)
    
    async def run_before_tool_call(self, ctx: ToolCallContext):
        for fn in self._before_tool_call:
            result = await fn(ctx)
            if result and result.get("block"):
                return result  # 阻止执行
    
    async fn in self._after_tool_call:
        await fn(ctx)
```

---

## 第二部分：Security 模块简化

### 现状

```
security/
├── approver.py   # 审批工作流（122行）
├── audit.py      # 审计日志
├── checker.py    # 风险检查
└── policy.py     # 策略定义
```

问题：
- Approver 和 Checker 功能重叠
- 权限策略与业务逻辑耦合
- 审计模块使用复杂

### 设计目标

1. **合并审批服务** - Approver + Checker → ApprovalService
2. **简化策略定义** - 策略与执行分离
3. **独立审计** - 审计作为轻量日志服务

### 新结构

```
security/
├── __init__.py           # 导出
├── policy.py             # 策略定义（精简）
├── approval.py           # 审批服务（合并 approver + checker）
├── audit.py              # 审计日志（简化）
└── callback.py           # 回调协议定义
```

### 简化设计

```python
# policy.py
from enum import Enum

class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class Permission:
    tool: str
    action: str
    resource: str
    risk_level: RiskLevel
    args: dict = field(default_factory=dict)
```

```python
# approval.py
class ApprovalService:
    """简化的审批服务"""
    
    def __init__(self, callback: ApprovalCallback | None = None):
        self.callback = callback
    
    async def request(self, permission: Permission) -> bool:
        """请求审批"""
        if permission.risk_level == RiskLevel.LOW:
            return True  # 低风险自动批准
        
        if self.callback:
            return await self.callback.request_approval(permission)
        
        return False  # 无回调则拒绝
    
    def check(self, permission: Permission) -> bool:
        """快速检查（无异步）"""
        return permission.risk_level == RiskLevel.LOW
```

```python
# audit.py
class AuditLog:
    """轻量审计日志"""
    
    def __init__(self, log_dir: Path | None = None):
        self.log_dir = log_dir or Path("~/.aloha/audit")
        self.log_file = self.log_dir / "audit.jsonl"
    
    def log(self, event: str, permission: Permission, approved: bool):
        """记录审计日志"""
        entry = {
            "event": event,
            "permission": permission.__dict__,
            "approved": approved,
            "timestamp": time.time()
        }
        with open(self.log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")
```

---

## 第三部分：Providers 模块

### 现状

```python
# base.py 有两个相似方法
async def chat(...)  # 基础聊天
async def chat_with_tools(...)  # 带工具聊天（实际与 chat 相同）
```

### 设计目标

1. **统一接口** - 一个 chat 方法，支持可选工具
2. **标准化响应** - 流式响应通过回调

### 新设计

```python
# base.py
class BaseProvider(ABC):
    """LLM Provider 抽象基类"""
    
    async def chat(
        self,
        messages: list[Message],
        tools: list[dict] | None = None,
        model: str | None = None,
        on_chunk: callable | None = None,  # 流式回调
    ) -> Response:
        """发送聊天请求
        
        Args:
            messages: 消息列表
            tools: 工具定义（可选）
            model: 模型名称（可选）
            on_chunk: 流式响应回调（可选）
        """
        pass
```

---

## 第四部分：Tools 模块统一

### 现状

- file_tool.py、shell_tool.py、web_tool.py 各自独立
- 缺少统一基类
- 错误处理不一致

### 设计目标

1. **统一基类** - BaseTool 抽象类
2. **标准错误处理** - 工具异常统一抛出
3. **统一参数验证** - TypeBox 或手动验证

### 新设计

```python
# base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

@dataclass
class ToolResult:
    content: list[dict[str, Any]]
    details: dict[str, Any] = field(default_factory=dict)
    is_error: bool = False

class BaseTool(ABC):
    """工具基类"""
    
    name: str
    description: str
    parameters: dict  # JSON Schema
    
    @abstractmethod
    async def execute(
        self,
        tool_call_id: str,
        params: dict[str, Any],
        signal: Any = None,
        on_update: callable | None = None,
    ) -> ToolResult:
        """执行工具
        
        Args:
            tool_call_id: 工具调用 ID
            params: 工具参数
            signal: 取消信号
            on_update: 进度回调（可选）
        """
        pass
    
    def to_schema(self) -> dict:
        """转换为工具 schema"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters
        }
```

---

## 第五部分：目录整理

### 现状问题

- chat_with_ai.py 使用 Gradio，应删除
- 示例代码与核心逻辑混合

### 整理方案

```
aloha/                    # 核心库（精简，无 Gradio 依赖）
├── agent/               # Agent 核心
├── providers/           # LLM 提供商
├── tools/               # 工具
├── security/           # 安全
├── memory/             # 内存
├── bus/                # 消息总线
├── config/             # 配置
├── prompts/            # 提示词
├── lib/                # 日志
└── web/                # Vue.js Web UI（独立）

删除：
- examples/chat_with_ai.py（使用 Gradio）
```

### 行动

1. **删除** chat_with_ai.py
2. **保留** simple_agent.py 作为最小示例
3. **创建** aloha-examples/ 目录存放其他示例（如果需要）

---

## 第六部分：实施计划

### 阶段 1：基础设施（事件系统）

1. 创建 `agent/events.py` - 事件类型和发射器
2. 修改 `agent/base.py` - 集成事件系统
3. 修改 `agent/loop.py` - 发射事件

### 阶段 2：Security 简化

1. 合并 `approver.py` + `checker.py` → `approval.py`
2. 简化 `policy.py` - 精简 Permission 定义
3. 简化 `audit.py` - 轻量 JSONL 存储

### 阶段 3：Providers 统一

1. 统一 `base.py` 接口
2. 标准化流式响应

### 阶段 4：Tools 统一

1. 创建 `tools/base.py` - BaseTool 基类
2. 重构 file_tool.py、shell_tool.py、web_tool.py

### 阶段 5：示例整理

1. 移除 chat_with_ai.py（使用 Gradio）
2. 保留 simple_agent.py 作为最小示例

---

## 附录：requirements.txt 修改

### 移除 Gradio 依赖

```diff
- # Web UI 支持
- gradio>=4.0.0       # Web UI 框架，用于构建 AI 对话界面
```

保留的依赖：
- openai, tiktoken - LLM 调用
- pydantic, python-dotenv, tomli, PyYAML - 配置
- pytest, pytest-asyncio - 测试
- click - CLI
- aiohttp - HTTP 客户端

---

## 兼容性考虑

- 保持现有 API 兼容
- 新增接口兼容旧代码
- 逐步迁移，不破坏现有功能

---

## 总结

通过本次重构：

1. **代码简化** - 职责清晰，减少重复
2. **事件驱动** - 支持流式响应
3. **统一抽象** - 工具和 Provider 统一
4. **示例分离** - 核心库与示例分离

重构后的 Aloha 将更加精简、可维护，同时保持现有功能兼容。
