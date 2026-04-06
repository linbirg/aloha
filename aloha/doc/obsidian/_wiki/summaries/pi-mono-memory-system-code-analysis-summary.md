---
title: pi-mono 记忆系统分析摘要
type: summary
tags: [pi-mono, memory, jsonl]
created: 2026-04-06
updated: 2026-04-06
sources: [pi-mono-memory-system-code-analysis]
summary: pi-mono 极简记忆设计，通过 JSONL 会话存储 + Extension API 实现可扩展记忆
---

pi-mono **没有显式记忆模块**，而是通过会话管理系统（JSONL 树形结构）实现上下文持久化，复杂记忆需通过 Extension API 扩展实现。

**核心差异**：传统记忆系统 vs pi-mono 的"会话即存储"——session.messages 即记忆，检索通过会话 ID 直接加载。

[[pi-mono]] — 实体页
