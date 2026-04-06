---
title: Hermes FTS5 分析摘要
type: summary
tags: [fts5, search, sqlite, memory]
created: 2026-04-06
updated: 2026-04-06
sources: [hermes-agent-fts5-analysis]
summary: Hermes Agent 的 SQLite FTS5 全文搜索实现，触发器自动同步 + 6步查询清理 + WAL 并发优化
---

Hermes Agent 使用 SQLite FTS5 实现生产级全文搜索，通过触发器保持 FTS5 索引与消息表自动同步，WAL 模式支持高并发写入。

**关键设计**：content sync 方式 + 6 步查询清理（防 FTS5 语法注入）+ 应用层随机 jitter 重试（避免 SQLite convoy 效应）。

[[memory-system]] — 概念页
