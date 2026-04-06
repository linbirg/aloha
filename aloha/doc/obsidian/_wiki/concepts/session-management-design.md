---
title: Session 管理功能设计
type: concept
tags: [agent, session, memory, design]
created: 2026-04-06
updated: 2026-04-06
sources: [session-management-design]
summary: 以 Session 为单位的资源管理：SQLite 元数据+文件系统资源、继承/覆盖配置、运行时 Agent 实例隔离
---

以会话（Session）为单位的资源管理功能，参考 ChatGPT 网页版用户体验。

## 目标

- 随时新建会话
- 每个会话拥有独立的 agent.md、skills、prompt 配置
- 支持会话级别的 memory.md 和 history.md

## 设计原则

- **混合存储**：Session 元数据存储在 SQLite，资源文件存储在文件系统
- **继承/覆盖**：支持全局默认配置，Session 可选择覆盖部分配置
- **运行时隔离**：每个 Session 对应独立的 Agent 实例，确保数据隔离

## 目录结构

```
~/.aloha/
├── sessions/              # Session 根目录
│   ├── default/          # default session
│   │   ├── agent.md
│   │   ├── memory.md
│   │   ├── history.md
│   │   └── skills/
│   └── {session_id}/
│       ├── agent.md       # 可覆盖全局 agent.md
│       ├── memory.md
│       ├── history.md
│       └── skills/
└── sessions.db            # Session 元数据（SQLite）
```

## 与记忆系统的关系

- `SessionMemory` 管理单会话消息历史
- `LongTermMemory` 提供跨会话持久化
- Session 级别的 `memory.md` 由 LongTermMemory 驱动，提供知识积累

[[hermes-agent]] — Hermes SessionDB FTS5 三层记忆架构
[[pi-mono]] — Pi-mono 的 JSONL 树形会话管理
[[memory-system]] — Agent 记忆系统总览
