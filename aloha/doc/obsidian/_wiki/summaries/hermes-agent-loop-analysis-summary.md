---
title: Hermes Agent 循环分析摘要
type: summary
tags: [loop, react, python]
created: 2026-04-06
updated: 2026-04-06
sources: [hermes-agent-loop-analysis]
summary: Hermes 手动 ReAct 循环实现（max_iterations=90）、并行工具执行、流式回调及错误处理机制
---

Hermes Agent 采用**手动 ReAct 循环**而非 SDK 自动循环，提供更精细的控制能力。

**核心设计**：max_iterations=90 次迭代上限 + handle_function_call() 手动执行工具 + 多种流式回调（tool_progress/thinking/reasoning）+ 预算警告嵌入。

[[agent-loop]] — 概念页
