---
title: Vercel AI SDK
type: entity
tags: [sdk, typescript, tool, framework]
created: 2026-04-06
updated: 2026-04-06
sources: [ai-sdk-tool-loop-analysis, mastra-loop-analysis]
summary: Vercel 出品的 AI 应用 SDK，内置声明式自动工具调用循环
---

Vercel AI SDK（又称 AI SDK）是 Vercel 推出的 AI 应用开发 SDK，核心特性是**声明式自动工具调用循环**。

## 核心特性

- **内置工具调用循环**：声明式配置，SDK 自动处理检测→执行→注入→判断
- **多种循环停止条件**：`stepCountIs(n)`、`hasToolCall()`、`stopAtAny()` 组合
- **流式输出原生支持**：`streamText`/`generateText` 返回流式结果
- **多模型支持**：统一接口接入 40+ 模型

## 工具定义

```typescript
const weather = tool({
  description: '获取指定位置的天气',
  inputSchema: z.object({ location: z.string() }),
  execute: async ({ location }) => { return { temperature: 25 }; },
});
```

## 循环机制

```
generateText() → 模型生成 → 检测工具调用
    ↓
无工具调用 → 返回 text
    ↓
有工具调用 → 验证参数 → 执行工具 → 注入结果
    ↓
检查 stopWhen → 条件满足 → 返回
    ↓
条件不满足 → 循环回到模型生成
```

## 与 Mastra / Hermes 对比

| 特性 | AI SDK | Mastra | Hermes |
|------|--------|--------|--------|
| 循环方式 | SDK 自动 | SDK 自动 | 手动 ReAct |
| 停止条件 | 内置 | AI SDK | max_iterations |
| 流式支持 | 原生 | 原生 | 手动回调 |
| 错误处理 | 内置重试 | 内置 | 手动 |

## 对 Aloha 的启示

1. **声明式工具定义**：description + inputSchema + execute 三要素
2. **停止条件系统**：可借鉴 Aloha 的 max_iterations 机制
3. **状态管理**：steps 数组保存完整工具调用历史

## 相关链接

[[ai-sdk-tool-loop-analysis-summary]] — 工具调用循环深度分析
[[mastra-loop-analysis-summary]] — Mastra 循环实现（依赖 AI SDK）
[[hermes-agent-loop-analysis-summary]] — Hermes 手动循环对比
