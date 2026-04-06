---
title: pi-mono 会话管理分析摘要
type: summary
tags: [pi-mono, session, fork, compact]
created: 2026-04-06
updated: 2026-04-06
sources: [pi-mono-session-management-analysis]
summary: pi-mono JSONL 树形会话管理，分叉（fork）和分支导航（tree）机制，compact 压缩
---

pi-mono 会话管理的核心是 JSONL 树形结构：`/fork` 从当前分支创建新会话，`/tree` 浏览和跳转任意历史点，`/compact` 压缩长会话为摘要。

**与会话存储**：实时写入磁盘 + parentId 树形关联 + 上下文压缩三位一体实现会话持久化。

[[pi-mono]] — 实体页
