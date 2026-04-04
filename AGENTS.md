# AGENTS.md — Aloha Agent Framework

## 项目概述

Aloha 是一个轻量级 Python AI Agent 框架（Python 3.10+），支持会话/任务管理、分层技能、灵活 prompt、记忆管理和带安全审批控制的工具系统。

项目根目录: `aloha/`

## 构建 / Lint / 测试命令

```bash
# 安装依赖
cd aloha && pip install -r requirements.txt

# 运行所有测试
cd aloha && pytest

# 运行单个测试文件
cd aloha && pytest aloha/test/test_agent.py -v

# 运行单个测试函数
cd aloha && pytest aloha/test/test_agent.py::TestMemory::test_session_memory_add_message -v
cd aloha && pytest aloha/test/test_reactloop.py::TestReActLoop::test_single_tool_call -v

# 仅运行单元测试（跳过集成测试）
cd aloha && pytest -m "unit"

# 运行集成测试（需要 ALOHA_TEST_INTEGRATION=1 和 API keys）
cd aloha && pytest -m "integration"

# 运行带覆盖率
cd aloha && pytest --cov=aloha --cov-report=term-missing
```

## 代码风格

### 通用规则

- **PEP 8** — 遵循标准 Python 约定
- **snake_case** 命名所有标识符 — 禁止缩写、camelCase 或 Hungarian notation
- **无注释** — 除非用户明确要求
- **中文 docstrings** — 所有模块/类/函数的 docstrings 使用简体中文
- **英文 inline 注释** — 仅在混用中文会破坏可读性时使用

### 导入顺序（用空行分隔）

1. 标准库 (`from abc import ABC, abstractmethod`)
2. 第三方库 (`from openai import AsyncOpenAI`, `from pydantic import BaseModel`)
3. 本地应用 (`from aloha.providers.base import BaseProvider`)

禁止使用通配符导入 (`from foo import *`)。

### 格式化

- 4 空格缩进
- 最大行长度: **120 字符**（软限制，优先可读性）
- 多行 dict/list 调用使用**尾随逗号**
- 所有函数参数和返回值使用**类型提示**
- 使用 `str | None`（Python 3.10+ 联合语法），禁止 `Optional[str]` 或 `Union[...]`
- 顶级类/函数定义之间空行，类内方法定义之间不空行

### 命名约定

| 元素 | 约定 | 示例 |
|------|------|------|
| 模块 | snake_case | `openai_provider.py` |
| 类 | PascalCase | `OpenAIProvider` |
| 函数/方法 | snake_case | `add_user_message` |
| 变量 | snake_case | `tool_calls` |
| 常量 | SCREAMING_SNAKE_CASE | `MAX_TOOL_ITERATIONS` |
| 私有成员 | 前置下划线 | `_tools` |

### 类型注解

- 使用**具体类型**或 `Any`，避免泛型 `object`
- 使用 `@dataclass` 作为纯数据容器（`Message`, `Response`, `ToolCall`, `ToolResult`）
- 使用 `@dataclass` + `@property` 或 `BaseModel`（Pydantic）处理需要验证的配置
- 使用 `Protocol` 实现结构子类型（接口模式）
- 禁止 `typing.cast`

### 错误处理

- **抛出异常**: 使用 `raise ValueError(...)` 并提供描述性消息
- **异步函数**: 自然传播异常，不静默吞掉
- **工具执行**: 返回 `ToolResult(success=False, error="...")` 而非抛出
- **权限/安全错误**: 返回 `ToolResult(success=False, error="Permission denied: ...")`
- **外部 API 错误**: 捕获特定异常，通过 `aloha.lib.logger` 记录，返回错误结果

### 日志

- 使用 `aloha.lib.logger`（`LOG_DEBUG`, `LOG_INFO`, `LOG_WARNING`, `LOG_ERROR`）
- 提交前移除或保护调试日志

## 项目结构

```
aloha/
├── agent/        # 核心 agent 逻辑
├── bus/          # 消息总线（队列式 pub/sub）
├── config/       # 配置加载 + Pydantic 模型
├── lib/          # 工具（logger）
├── memory/       # 会话记忆 + 长期记忆
├── prompts/      # Prompt 模板加载器
├── providers/    # LLM providers
├── security/     # 安全策略、权限检查、审批、审计
├── skills/       # 技能加载器
├── templates/    # 默认 prompt 模板
├── test/         # 测试
└── tools/        # 内置工具（file, shell, web）
```

## 关键模式

### 异步优先
整个 agent 循环是异步的。所有涉及 I/O 的公共方法使用 `async def`。

### 工具模式
使用 `BaseTool.to_openai_schema()` 自动生成 OpenAI function-calling schema。用 `ToolRegistry` 管理多个工具。

### 消息流
`Message` → `SessionMemory.add_message()` → `SessionMemory.get_messages()` → provider `chat()`

### 安全
- `PermissionChecker` — 根据 `SecurityConfig` 规则评估权限
- `Approver` — 根据风险级别请求用户审批
- `ToolWrapper` — 包装 `ToolRegistry` 并执行安全检查
- `RiskLevel`: `LOW`（自动批准）、`MEDIUM`（提示）、`HIGH`（需要审批）

### 测试约定
- 使用 `pytest.mark.asyncio` 标记异步测试
- 使用 `@pytest.mark.unit` / `@pytest.mark.integration` 区分测试类型
- 使用 `unittest.mock.AsyncMock` / `MagicMock` mock providers 和 tools
- 测试文件: `test_*.py`，测试类: `Test*`，测试方法: `test_*`
- 方法 docstring 使用大写测试 ID（如 `"""REACT-001: 无工具调用..."""`）

### 添加新组件

**新 LLM provider:**
1. 继承 `BaseProvider`（`aloha/providers/base.py`）
2. 实现 `async def chat()` 和 `async def chat_with_tools()`
3. 返回 `Response(...)` dataclass
4. 添加到 `aloha/providers/__init__.py`

**新工具:**
1. 继承 `BaseTool`（`aloha/agent/tools.py`）
2. 实现 `async def execute(self, **kwargs) -> ToolResult`
3. 可选：重写 `to_openai_schema()` 自定义参数 schema
4. 通过 `ToolRegistry.register(ToolInstance())` 注册

## 配置

通过 `aloha.config.schema.AlohaConfig`（Pydantic）加载。优先级：`~/.aloha/config.toml` > 项目 `config.toml` > 默认值。环境变量可用 `${VAR_NAME}` 引用。
