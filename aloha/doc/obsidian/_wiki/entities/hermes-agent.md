---
title: Hermes Agent
type: entity
tags: [agent, memory, python, nous-research]
created: 2026-04-06
updated: 2026-04-06
sources: [hermes-agent-analysis, hermes-agent-loop-analysis, hermes-agent-fts5-analysis, hermes-honcho-analysis, hermes-memory-system-analysis]
summary: NousResearch 出品的自我进化 AI Agent，以闭环学习记忆系统著称，支持多平台接入
---

Hermes Agent 是 NousResearch 开发的开源 AI Agent，GitHub 18.7k stars，号称"**The agent that grows with you**"。

## 核心特性

- **闭环学习**：Agent 自主创建技能，技能在使用中自我改进，定期 nudges 提醒持久化知识
- **记忆系统**：三层记忆（SessionDB FTS5 + Honcho 用户建模 + JSONL legacy）
- **多平台接入**：Telegram、Discord、Slack、WhatsApp、Signal、Email、CLI
- **FTS5 会话搜索**：SQLite FTS5 全文搜索，支持跨会话回忆
- **子代理委托**：并行工作流，RPC 调用工具
- **低成本运行**：支持 $5 VPS 或 serverless 部署

## 技术架构

**循环机制**：手动 ReAct 循环（而非 AI SDK 自动循环），max_iterations=90，支持并行工具执行。

**记忆系统分层**：

```
Agent Context
    ↓
ContextCompressor（上下文压缩）
    ↓
Honcho（用户画像 + 心理理论）
    ↓
SessionDB FTS5（SQLite + 全文搜索）
    ↓
JSONL（legacy 兼容）
```

**工具系统**：`handle_function_call()` 手动执行工具，支持流式回调（tool_progress / thinking / reasoning）。

## 与 pi-mono / Mastra 对比

| 特性 | Hermes | pi-mono | Mastra |
|------|--------|---------|--------|
| 语言 | Python | TypeScript | TypeScript |
| 记忆系统 | 完整闭环 | 会话存储 | 4种类型 |
| 用户建模 | Honcho | 无 | 无 |
| 循环方式 | 手动 ReAct | 未知 | AI SDK 自动 |
| 工作流 | 无 | 无 | 图引擎 |
| 自我进化 | ✅ | ❌ | ❌ |

## 对 Aloha 的启示

1. **FTS5 会话搜索**（高优先级）：跨会话回忆能力
2. **用户建模**（中优先级）：Honcho 风格的 persona 建模
3. **技能进化**（中优先级）：自主创建和改进技能
4. **定期 nudges**（中优先级）：主动提醒持久化

## 相关链接

[[hermes-memory-system-analysis-summary]] — 记忆系统分工与存储方案
[[hermes-agent-loop-analysis-summary]] — Agent 循环逻辑
[[hermes-agent-fts5-analysis-summary]] — FTS5 全文搜索实现
[[hermes-honcho-analysis-summary]] — Honcho 用户建模
[[mastra-analysis-summary]] — Mastra 全栈框架对比
[[pi-mono-skills-analysis-summary]] — pi-mono Skills 系统
