---
title: Agent 循环机制
type: concept
tags: [agent, loop, tool, react]
created: 2026-04-06
updated: 2026-04-06
sources: [hermes-agent-loop-analysis, mastra-loop-analysis, ai-sdk-tool-loop-analysis]
summary: Agent 执行的核心循环，两种实现方式：SDK 自动循环 vs 手动 ReAct 循环
---

Agent 循环是 Agent 执行任务的核心机制，两种主要实现方式：**SDK 自动循环**（如 AI SDK、Mastra）和**手动 ReAct 循环**（如 Hermes）。

## 两种循环方式对比

| 特性 | SDK 自动循环 | 手动 ReAct 循环 |
|------|-------------|----------------|
| 控制粒度 | 粗粒度 | 精细 |
| 定制性 | 中 | 高 |
| 实现复杂度 | 低 | 高 |
| 错误处理 | 内置 | 手动 |
| 流式处理 | 原生 | 手动回调 |
| 迭代控制 | stopWhen 声明式 | max_iterations |

## SDK 自动循环

```
generateText() → 模型生成 → SDK 检测工具调用
    ↓
无 tool_calls → 返回 text
    ↓
有 tool_calls → SDK 执行工具 → 注入结果
    ↓
检查 stopWhen → 条件满足 → 返回
    ↓
循环
```

**代表**：Vercel AI SDK、Mastra

## 手动 ReAct 循环

```
while iteration < max_iterations:
    response = client.chat.completions.create(messages)
    if response.tool_calls:
        for tool_call in response.tool_calls:
            result = handle_function_call(tool_call)
            messages.append(tool_result)
    else:
        return response.content
```

**代表**：Hermes Agent（max_iterations=90）

## ReAct 模式

```
Think → Act → Observe → Decision → (继续/停止)
```

Reasoning 和 Acting 交替进行：LLM 先推理下一步工具调用，执行后观察结果，再决定继续还是停止。

## 对 Aloha 的启示

Aloha 的 ReActLoop 属于**手动循环**实现（参考 `hermes-agent-loop-analysis`），可借鉴：

1. **精细迭代控制**：Hermes 的 90 次迭代上限
2. **并行工具执行**：多个独立工具并行调用
3. **流式回调**：thinking / tool_progress 实时反馈
4. **预算警告**：迭代中期嵌入 "budget warning"

## 相关链接

[[ai-sdk-tool-loop-analysis-summary]] — AI SDK 自动循环
[[hermes-agent-loop-analysis-summary]] — Hermes 手动循环
[[mastra-loop-analysis-summary]] — Mastra 循环实现
