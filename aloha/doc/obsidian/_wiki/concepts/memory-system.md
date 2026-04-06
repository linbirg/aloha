---
title: 记忆系统
type: concept
tags: [agent, memory, session, fts5]
created: 2026-04-06
updated: 2026-04-06
sources: [hermes-memory-system-analysis, hermes-agent-fts5-analysis, hermes-honcho-analysis, pi-mono-memory-system-code-analysis, pi-mono-session-management-analysis]
summary: Agent 的记忆系统设计，从会话记忆到长期记忆的多层架构
---

记忆系统是 Agent 跨越会话保持上下文能力的核心组件。各 Agent 实现差异巨大。

## 记忆类型对比

| 类型 | Hermes | Mastra | pi-mono | Aloha（现状） |
|------|--------|--------|---------|--------------|
| 会话记忆 | ✅ SessionDB | ✅ Conversation History | ✅ session.messages | ✅ SessionMemory |
| 长期记忆 | ✅ FTS5 + JSONL | ✅ Semantic Recall | ❌ 需扩展 | ❌ |
| 用户建模 | ✅ Honcho | ❌ | ❌ | ❌ |
| 技能进化 | ✅ 自主创建/改进 | ❌ | ❌ | ❌ |
| 上下文压缩 | ✅ ContextCompressor | ✅ | ✅ /compact | ❌ |

## 存储方案演进

| 方案 | 适用场景 | 代表 |
|------|---------|------|
| 内存 | 简单、单次 | Aloha（当前） |
| JSONL | 简单持久化 | pi-mono |
| SQLite | 需要搜索 | Hermes、Mastra |
| SQLite + FTS5 | 高并发 + 全文搜索 | Hermes |
| 向量存储 | 语义检索 | Mastra |

## FTS5 全文搜索（Hermes）

SQLite FTS5 实现会话历史全文搜索：

```sql
CREATE VIRTUAL TABLE messages_fts USING fts5(
    content,
    content=messages,
    content_rowid=id
);
```

配合触发器自动同步，WAL 模式支持并发写入，6 步查询清理防止 FTS5 语法注入。

**搜索语法**：`"docker OR kubernetes"`、`"deploy*"` 前缀匹配、`'"exact phrase"'` 短语。

## Honcho 用户建模（Hermes）

通过 Honcho SDK 实现用户画像和心理理论：

- `seed_ai_identity()`：从文本播种 AI 表征
- `get_ai_representation()`：获取当前用户表征
- 多层配置：`instance > global > env`

## 会话分叉（pi-mono）

JSONL 树形结构支持会话分叉：

```bash
/fork   # 从当前分支创建新会话
/tree   # 浏览和跳转到任意历史点
/compact # 压缩长会话
```

## 对 Aloha 的启示

| 优先级 | 功能 | 说明 |
|--------|------|------|
| 高 | FTS5 会话搜索 | 跨会话回忆 |
| 中 | SQLite 存储 | 替代内存，提高可靠性 |
| 中 | 上下文压缩 | transformContext hook |
| 低 | 会话分叉 | 复杂度高 |

## 相关链接

[[hermes-memory-system-analysis-summary]] — 记忆系统分工与存储方案
[[hermes-agent-fts5-analysis-summary]] — FTS5 全文搜索实现
[[hermes-honcho-analysis-summary]] — Honcho 用户建模
[[pi-mono-session-management-analysis-summary]] — pi-mono 会话管理
