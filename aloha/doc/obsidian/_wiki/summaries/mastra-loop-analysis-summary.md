---
title: Mastra 循环分析摘要
type: summary
tags: [loop, streaming, workflow]
created: 2026-04-06
updated: 2026-04-06
sources: [mastra-loop-analysis]
summary: Mastra 基于 AI SDK 的完全流式循环设计，多模型路由和可观测性集成
---

Mastra 循环基于 Vercel AI SDK 的**完全流式**设计，核心是 `workflowLoopStream` 流式处理 + `MastraModelOutput` 输出封装。

**设计哲学**：依赖成熟 AI SDK 处理核心逻辑 → 专注应用层功能（工作流、记忆、部署）→ 适合快速构建应用，不太适合深度定制。

[[agent-loop]] — 概念页
