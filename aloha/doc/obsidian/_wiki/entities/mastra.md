---
title: Mastra
type: entity
tags: [agent, framework, typescript, workflow]
created: 2026-04-06
updated: 2026-04-06
sources: [mastra-analysis, mastra-loop-analysis]
summary: Gatsby 团队打造的全栈 AI 应用框架，以工作流引擎和多层次记忆系统著称
---

Mastra 是 Gatsby 团队背后开发的开源 AI Agent 框架，GitHub 22.5k stars，定位为**从原型到生产的完整 AI 应用框架**。

## 核心特性

- **Model Routing**：40+ 供应商统一接口（OpenAI、Anthropic、Gemini 等）
- **多层次记忆**：Working Memory + Observational Memory + Semantic Recall + Conversation History
- **Workflows 图引擎**：编排复杂多步骤流程，支持暂停/恢复
- **Human-in-the-loop**：暂停等待用户输入或批准
- **MCP Servers**：Model Context Protocol 服务器
- **Evals**：内置评估系统
- **多平台部署**：React、Next.js、Node.js、Cloudflare Workers、Vercel Edge

## 记忆系统

| 类型 | 说明 |
|------|------|
| Working Memory | LLM 当前可用的活跃上下文 |
| Observational Memory | 主动观察用户行为并从中学习 |
| Semantic Recall | 基于向量相似度检索历史 |
| Conversation History | 会话级消息存储 |

## 技术架构

**循环机制**：依赖 Vercel AI SDK 的自动工具调用循环（而非手动 ReAct）。

**存储后端**：SQLite、PostgreSQL、MySQL、Cloudflare D1 + 向量存储（Pinecone、Qdrant）。

## 与 Hermes 对比

| 特性 | Mastra | Hermes |
|------|--------|--------|
| 循环方式 | AI SDK 自动 | 手动 ReAct |
| 流式处理 | 原生 | 手动实现 |
| 工作流引擎 | ✅ 图引擎 | ❌ |
| 用户建模 | ❌ | Honcho |
| 定制性 | 中 | 高 |
| 框架类型 | 全栈应用框架 | Agent |

## 对 Aloha 的启示

1. **处理器模式**：输入/输出处理器抽象（可借鉴 ContextBuilder）
2. **存储接口**：统一存储后端抽象
3. **工作流引擎**：图结构流程控制

## 相关链接

[[mastra-loop-analysis-summary]] — Agent 循环实现
[[hermes-agent-analysis-summary]] — Hermes Agent 对比
[[ai-sdk-tool-loop-analysis-summary]] — AI SDK 工具调用循环
