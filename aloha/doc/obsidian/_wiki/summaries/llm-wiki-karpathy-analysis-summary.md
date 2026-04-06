---
title: LLM Wiki Karpathy 分析摘要
type: summary
tags: [wiki, karpathy, knowledge]
created: 2026-04-06
updated: 2026-04-06
sources: [llm-wiki-karpathy-analysis]
summary: Karpathy LLM Wiki 核心思想：三层架构（Raw/Wiki/Schema）、Ingest/Query/Lint 三操作、飞轮复利效应
---

Karpathy 的 LLM Wiki 模式核心：**人不碰 wiki**，Wiki 是 LLM 的领地。

**三层**：Raw Sources（只读）+ Wiki（LLM 维护）+ Schema（CLAUDE.md/AGENTS.md 行为准则）。

**五个机制**：raw/wiki 分离 + 索引替代 RAG + Query 回填飞轮 + 增量编译 + 自动 Lint。

[[llm-wiki-pattern]] — 概念页
