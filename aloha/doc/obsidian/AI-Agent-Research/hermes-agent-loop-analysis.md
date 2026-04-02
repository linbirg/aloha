---
title: Hermes Agent Agent循环逻辑深度分析
date: 2026-04-01
tags:
  - AI-Agent
  - Hermes
  - NousResearch
  - agent-loop
  - tool-calling
---

# Hermes Agent Agent循环逻辑深度分析

## 一、核心循环机制概述

Hermes Agent 采用**手动 ReAct 循环**实现，而非依赖 AI SDK 的自动工具调用。这种实现方式提供了更精细的控制能力。

### 循环架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        AIAgent.run()                             │
├─────────────────────────────────────────────────────────────────┤
│  1. 初始化消息列表                                               │
│     ├── system_prompt (prompt_builder构建)                       │
│     ├── 技能索引 (skills_system_prompt)                          │
│     ├── 上下文文件 (context_files_prompt)                        │
│     └── 用户消息                                                  │
│                                                                  │
│  2. 进入循环 (max_iterations=90)                                 │
│     │                                                            │
│     ▼                                                            │
│  ┌──────────────────┐                                           │
│  │  调用 LLM API    │◄────────────────────────────────┐         │
│  │  (client.chat.com│                                 │         │
│  │   pletions.create│                                 │         │
│  └────────┬─────────┘                                 │         │
│           │                                            │         │
│           ▼                                            │         │
│  ┌──────────────────┐                                  │         │
│  │ 检查响应类型     │                                  │         │
│  │ - tool_calls?   │                                  │         │
│  │ - content?      │                                  │         │
│  │ - reasoning?   │                                  │         │
│  └────────┬─────────┘                                  │         │
│           │                                            │         │
│     ┌─────┴─────┐                                      │         │
│     │           │                                      │         │
│     ▼           ▼                                      │         │
│  ┌────────┐  ┌────────┐                                │         │
│  │有工具调│  │无工具调│                                │         │
│  │用/tool │  │用/直接 │                                │         │
│  │_calls  │  │返回内容│                                │         │
│  └────┬───┘  └───┬────┘                                │         │
│       │          │                                      │         │
│       ▼          │                                      │         │
│  ┌───────────┐   │                                      │         │
│  │ 逐个处理  │   │                                      │         │
│  │ tool_call │   │                                      │         │
│  └─────┬─────┘   │                                      │         │
│        │         │                                      │         │
│        ▼         │                                      │         │
│  ┌───────────┐  │                                      │         │
│  │ handle_   │  │                                      │         │
│  │ function_ │  │                                      │         │
│  │ call()    │  │                                      │         │
│  └─────┬─────┘  │                                      │         │
│        │        │                                      │         │
│        ▼        │                                      │         │
│  ┌───────────┐  │                                      │         │
│  │ 添加 tool │  │                                      │         │
│  │ _result   │  │                                      │         │
│  │ 消息      │  │                                      │         │
│  └─────┬─────┘  │                                      │         │
│        │        │                                      │         │
│        └────┬───┘                                      │         │
│             │                                          │         │
│             ▼                                          │         │
│      循环回到 LLM API 调用                             │         │
│             │                                          │         │
│             └──────────────────┐                       │         │
│                                │                       │         │
│                                ▼                       │         │
│                    达到 max_iterations                  │         │
│                    或                                     │         │
│                    无 tool_calls (完成)                  │         │
│                                                                  │
│  3. 返回最终响应                                                │
└─────────────────────────────────────────────────────────────────┘
```

---

## 二、核心代码分析

### 1. AIAgent 类定义

```python
class AIAgent:
    def __init__(
        self,
        base_url: str = None,
        api_key: str = None,
        provider: str = None,
        model: str = "anthropic/claude-opus-4.6",
        max_iterations: int = 90,  # 默认90次工具调用迭代
        tool_delay: float = 1.0,
        enabled_toolsets: List[str] = None,
        disabled_toolsets: List[str] = None,
        # ... 其他参数
    ):
```

### 2. 消息格式

Hermes 使用 OpenAI 格式的消息，包含以下角色：

| 角色 | 说明 |
|------|------|
| `system` | 系统提示词 |
| `user` | 用户消息 |
| `assistant` | AI 回复（可能包含 tool_calls） |
| `tool` | 工具执行结果 |

### 3. 工具调用处理流程

从 trajectory 代码可以看出工具调用循环的处理方式：

```python
# 遍历消息，检查 tool_calls
while i < len(messages):
    msg = messages[i]
    
    if msg["role"] == "assistant":
        # 检查是否有工具调用
        if "tool_calls" in msg and msg["tool_calls"]:
            # 处理每个 tool_call
            for tool_call in msg["tool_calls"]:
                # 解析参数
                arguments = json.loads(tool_call["function"]["arguments"])
                # ... 执行工具
            
            # 收集后续的工具响应
            j = i + 1
            while j < len(messages) and messages[j]["role"] == "tool":
                tool_responses.append(messages[j])
                j += 1
```

---

## 三、关键技术特性

### 1. 流式输出支持

Hermes 支持多种回调用于流式处理：

| 回调 | 用途 |
|------|------|
| `tool_progress_callback` | 工具执行进度 |
| `thinking_callback` | thinking 内容 |
| `reasoning_callback` | reasoning 内容 |
| `stream_delta_callback` | 流式输出增量 |
| `step_callback` | 步骤完成回调 |

### 2. 上下文管理

- **ContextCompressor**: 上下文压缩，控制 token 使用
- **prompt_builder**: 构建系统提示词
- **trajectory**: 保存对话轨迹用于训练

### 3. 工具系统

```python
from model_tools import (
    get_tool_definitions,
    get_toolset_for_tool,
    handle_function_call,
    check_toolset_requirements,
)
```

工具通过 `handle_function_call()` 手动执行，而不是依赖 SDK 自动执行。

---

## 四、与 AI SDK 自动循环对比

### Hermes 手动循环 vs AI SDK 自动循环

| 特性 | Hermes Agent | AI SDK (Mastra) |
|------|-------------|-----------------|
| **循环实现** | 手动 while 循环 | 自动工具调用 |
| **控制粒度** | 精细 | 粗粒度 |
| **迭代限制** | `max_iterations=90` | `stopWhen: stepCountIs(n)` |
| **流式处理** | 自定义回调 | 内置 stream |
| **工具执行** | `handle_function_call()` | SDK 自动处理 |
| **错误处理** | 手动重试 | 内置重试 |

### 代码对比

**Hermes 手动循环（伪代码）:**
```python
while iteration < max_iterations:
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        tools=tool_definitions,
    )
    
    if response.choices[0].message.tool_calls:
        for tool_call in response.choices[0].message.tool_calls:
            result = handle_function_call(tool_call)
            messages.append({
                "role": "tool",
                "content": result,
                "tool_call_id": tool_call.id
            })
    else:
        break
    
    iteration += 1
```

**AI SDK 自动循环:**
```python
result = generateText(model, {
    tools: tool_definitions,
    stopWhen: stepCountIs(10),
})
```

---

## 五、ReAct 模式实现

Hermes 采用经典的 ReAct（Reasoning + Acting）模式：

### ReAct 流程

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Think     │────►│    Act      │────►│   Observe   │
│  (reasoning)│     │ (tool_call) │     │(tool_result)│
└─────────────┘     └─────────────┘     └─────────────┘
       │                                         │
       │     ┌─────────────┐                    │
       └────►│  Decision   │◄───────────────────┘
             │ (继续/停止)  │
             └─────────────┘
```

### reasoning 处理

```python
def _extract_reasoning(self, assistant_message):
    # 支持多种 reasoning 格式
    # 1. native thinking tokens
    # 2. <REASONING_SCRATCHPAD> XML tags
    # 3. content 中的 reasoning
```

---

## 六、并行工具执行

Hermes 支持并行工具调用：

```python
def _should_parallelize_tool_batch(tool_calls) -> bool:
    """判断是否并行执行工具"""
    if len(tool_calls) <= 1:
        return False
    
    # 检查工具是否独立
    tool_names = [tc.function.name for tc in tool_calls]
    # ...
```

---

## 七、错误处理与恢复

### 1. API 错误处理

```python
def _summarize_api_error(error: Exception) -> str:
    # 处理 Cloudflare HTML 错误
    # 解析 JSON 错误体
    # 清理错误消息
```

### 2. 预算警告

```python
# 预算警告会在工具结果中嵌入
[BUDGET WARNING: Iteration 45/90...]
```

---

## 八、记忆与上下文

### 1. 会话持久化

```python
def _persist_session(self, messages, conversation_history=None):
    # 保存会话到数据库
    # 写入 brain.jsonl
```

### 2. 上下文压缩

```python
from agent.context_compressor import ContextCompressor
# 在上下文过长时触发压缩
```

---

## 九、对 Aloha 的启示

### 1. 选择手动循环的原因

Hermes 选择手动循环可能因为：
- 需要更精细的迭代控制（90次迭代）
- 需要自定义轨迹保存
- 需要与 Honcho 集成
- 需要多工具并行处理

### 2. 建议的循环实现

```python
class AgentLoop:
    def __init__(self, max_iterations: int = 50):
        self.max_iterations = max_iterations
    
    async def run(self, user_input: str):
        messages = self._build_messages(user_input)
        
        for iteration in range(self.max_iterations):
            response = await self._call_llm(messages)
            
            if response.tool_calls:
                # 手动处理工具调用
                for tool_call in response.tool_calls:
                    result = await self._execute_tool(tool_call)
                    messages.append(tool_result_message)
                
                # 检查是否需要压缩上下文
                if self._should_compress(messages):
                    messages = await self._compress(messages)
            else:
                # 无工具调用，完成
                return response.content
        
        # 达到最大迭代次数
        return self._handle_max_iterations()
```

### 3. 流式输出建议

```python
# 使用回调实现流式输出
async def run_streaming(self, user_input: str):
    async for chunk in self._stream_llm(messages):
        if chunk.tool_calls:
            # 处理工具调用
            self.tool_progress_callback(chunk)
        else:
            # 流式输出内容
            self.stream_delta_callback(chunk)
```

---

## 十、总结

Hermes Agent 的 Agent 循环是**手动实现的 ReAct 循环**，提供了：

1. **精细控制**: 90次迭代限制，自定义循环逻辑
2. **完整轨迹**: 保存训练数据格式的对话轨迹
3. **并行工具**: 支持工具并行执行
4. **流式回调**: 多种回调支持实时反馈
5. **错误恢复**: 完善的错误处理机制

这种实现方式比 AI SDK 的自动循环更复杂，但提供了更大的灵活性，适合需要深度定制的 Agent 系统。

---

## 参考资料

- [Hermes Agent GitHub](https://github.com/NousResearch/hermes-agent)
- [run_agent.py](https://github.com/NousResearch/hermes-agent/blob/main/run_agent.py)
- [model_tools](https://github.com/NousResearch/hermes-agent/blob/main/model_tools/)
