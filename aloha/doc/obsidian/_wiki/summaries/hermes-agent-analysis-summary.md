---
title: Hermes Agent 分析摘要
type: summary
tags: [agent, memory, python]
created: 2026-04-06
updated: 2026-04-06
sources: [hermes-agent-analysis]
summary: 深度分析 Hermes Agent 的完整闭环记忆系统、三层架构（SessionDB+Honcho+ContextCompressor）及自我进化机制
---

Hermes Agent 是目前功能最完整的开源 AI Agent 之一（18.7k stars），核心理念是"**The agent that grows with you**"。

**最值得借鉴**：三层记忆架构（SessionDB FTS5 + Honcho 用户建模 + ContextCompressor 压缩）+ 90 次迭代手动 ReAct 循环 + 定期 nudges 机制。

[[hermes-agent]] — 实体页
