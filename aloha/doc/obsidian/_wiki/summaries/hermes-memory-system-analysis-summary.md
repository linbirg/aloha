---
title: Hermes 记忆系统分析摘要
type: summary
tags: [memory, sqlite, fts5, jsonl]
created: 2026-04-06
updated: 2026-04-06
sources: [hermes-memory-system-analysis]
summary: Hermes 的 SQLite+JSONL 双轨存储策略、FTS5 vs JSONL 功能/性能对比及对 Aloha 的启示
---

Hermes 采用 **SQLite + JSONL 双轨并行** 存储策略：SQLite 负责搜索和并发（FTS5 + WAL），JSONL 负责 legacy 兼容和导出。

**核心权衡**：搜索场景 FTS5 比 JSONL 快 100 倍；加载场景 JSONL 略快；JSONL 优先加载数据更完整的一方（防截断）。

[[memory-system]] — 概念页
