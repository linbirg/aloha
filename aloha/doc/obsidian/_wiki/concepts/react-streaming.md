---
title: ReAct 流式机制
type: concept
tags: [react, streaming, agent, loop]
created: 2026-04-06
updated: 2026-04-06
sources: [mastra-loop-analysis, hermes-agent-loop-analysis, ai-sdk-tool-loop-analysis]
summary: ReAct 模式中流式 API 原理，LLM 输出管道化实现工具调用实时截断和文本流式输出
---

ReAct（Reasoning + Acting）模式中，流式 API 本质是 **LLM 输出管道化**：工具调用和文本输出不用等整个响应完成就能实时处理。

## 核心架构

两种实现路线：

### SDK 自动循环（Mastra / AI SDK）

```
LLM Stream → workflowLoopStream → MastraModelOutput → DestructurableOutput
                        ↓
              [text chunk | object | function call]
```

- LLM 输出为 SSE/流式 stream
- `workflowLoopStream` 实时分拣：文本块直接吐出，工具调用截断并执行
- 工具调用的截断点：**LLM 开始生成 tool_call 时**，SDK 检测到后立即触发执行
- `toolCallConcurrency` 支持多工具并行流式执行

### 手动 ReAct 循环（Hermes）

```python
while iteration < max_iterations:
    response = client.chat.completions.create(messages, stream=True)
    for chunk in response:
        if chunk.tool_calls:
            # 流式检测到 tool_calls，截断处理
            tool_call = parse_tool_call(chunk)
            result = handle_function_call(tool_call)
            messages.append(tool_result)
            break
        elif chunk.text:
            yield chunk.text  # 实时输出
```

## 关键机制

| 机制 | 说明 |
|------|------|
| **工具调用截断** | LLM 生成 tool_call 时，stream 被截断，工具立即执行 |
| **流式文本输出** | text chunk 直接 yield 给调用方（UI/终端） |
| **结果注入** | 工具执行完成后注入 messages，触发下一轮 LLM |
| **并行工具** | 多个独立工具可并行流式执行 |

## 对比

| | SDK 自动流式 | 手动 ReAct 流式 |
|---|---|---|
| 工具调用检测 | SDK 内部自动截断 | 遍历 stream chunk |
| 实时性 | 高（SDK 层处理） | 中（chunk 级检测） |
| 定制性 | 低 | 高 |
| 回调支持 | 内置 text/object/function 分流 | 手动注册回调 |

## 对 Aloha 的启示

Aloha 的 ReActLoop 可借鉴：
1. **thinking/reasoning 回调**：流式输出 reasoning 中间步骤
2. **tool_progress 回调**：工具执行时实时反馈进度
3. **预算警告嵌入**：迭代中期在流中嵌入 "budget warning"

## 相关链接

[[agent-loop]] — Agent 循环机制总览
[[mastra-loop-analysis-summary]] — Mastra 完全流式循环
[[hermes-agent-loop-analysis-summary]] — Hermes 手动循环 + 流式回调
