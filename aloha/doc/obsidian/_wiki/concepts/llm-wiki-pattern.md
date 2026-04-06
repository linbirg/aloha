---
title: LLM Wiki 模式
type: concept
tags: [knowledge-management, wiki, llm, agent, memory]
created: 2026-04-06
updated: 2026-04-06
sources: [llm-wiki-karpathy-analysis, llm-wiki-space-economy-karpathy-practice, llm-wiki-analysis-deep-dive, llm-wiki-claude-code-obsidian-practice]
summary: Karpathy 提出的知识管理模式，通过 LLM 维护持久 Wiki 实现知识复合积累
---

LLM Wiki 是 Andrej Karpathy 提出的知识管理模式：让 LLM 作为知识库的唯一维护者，实现持久复利的知识积累。

## 核心思想

传统 RAG 每次提问都从零查找，没有积累。LLM Wiki 的思路是：**先把资料整理成一层持续存在的 Wiki，再查询**。

核心原则：**人不碰 wiki**。Wiki 是 LLM 的领地，人只负责"投喂原料"和"提出好问题"。

## 三层架构

```
Raw Sources（只读）→ Wiki（LLM 维护）→ Schema（行为准则）
```

| 层级 | 说明 |
|------|------|
| **Raw Sources** | 原始资料（articles、papers），不可变，LLM 只读 |
| **Wiki** | LLM 全权维护的 MD 文件集合（摘要、实体、概念、对比、索引） |
| **Schema** | 告诉 LLM wiki 怎么组织、怎么 ingest/query/lint |

## 两种特殊文件

| 文件 | 作用 |
|------|------|
| `index.md` | 内容导向目录（按类别列页面 + 一句话摘要），LLM 回答时先读这个定位 |
| `log.md` | 时间导向日志（append-only），记录 ingest/query/lint 操作 |

## 三个操作

| 操作 | 说明 |
|------|------|
| **Ingest** | 读取原始资料 → 生成摘要 → 更新索引 → 追加日志 |
| **Query** | 先读 index.md → 定位相关页 → 综合回答 → 可选回填 |
| **Lint** | 定期检查断链、矛盾、孤立页面、stale 声明 |

## 飞轮效应

Query 的结果可以回填到 Wiki，使知识库**不只靠丢新资料增长，也靠问问题增长**。

## 对 Aloha 的启示

LLM Wiki 的"复合积累"思路与 Aloha 的 LongTerm Memory 设计高度一致：index.md 相当于 LongTerm Memory 索引，log.md 相当于会话历史时间线。

## 相关链接

[[hermes-agent-analysis-summary]] — Hermes 记忆系统
[[pi-mono-memory-system-code-analysis-summary]] — pi-mono 记忆系统
