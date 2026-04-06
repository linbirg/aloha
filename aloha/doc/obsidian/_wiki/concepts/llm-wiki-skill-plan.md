---
title: LLM Wiki Skill 实现方案
type: concept
tags: [wiki, opencode, skill, knowledge-management]
created: 2026-04-06
updated: 2026-04-06
sources: [llm-wiki-skill-plan]
summary: OpenCode LLM Wiki Skill 五阶段实现方案：Raw Sources 管理、compile 编译流程、query 查询回填、lint 健康检查、registry 状态追踪
---

用 OpenCode Skill 实现 LLM Wiki 模式，以 OpenCode 为引擎自动维护 Obsidian 研究资料知识库。

## 核心原则

- 多文档关联、标签管理完全由 LLM 自动完成，无需人工确认
- 渐进式披露：index + 页面摘要，支持先读摘要再深入详情
- Raw Sources 和 Wiki 输出共存于 `doc/obsidian/` 目录
- 附录：append-only，LLM 只读不写；Wiki：LLM 全权维护

## 五阶段实现

| 阶段 | 命令 | 内容 |
|------|------|------|
| 1. ingest | `/llm-wiki ingest <path>` | 登记 source 到 `_raw/sources/`，registry 标记 pending |
| 2. compile | `/llm-wiki compile` | pending sources → entities/concepts/summaries，自动打标签建双向链接 |
| 3. query | `/llm-wiki query <q>` | 跨 wiki 回答，满足条件则回填新建页面 |
| 4. lint | `/llm-wiki lint` | 断链修复、矛盾检测、stale 摘要更新 |
| 5. status | `/llm-wiki status` | 仪表盘：编译率、断链数、pending 数量 |

## 目录结构

```
_raw/sources/         ← 原始资料（append-only）
  registry.md         ← 编译状态追踪
_wiki/
  index.md            ← 全局索引
  log.md              ← 时间线日志
  entities/           ← 实体页
  concepts/           ← 概念页
  summaries/          ← 摘要页
  tags/               ← 标签索引
```

## 回填飞轮

query 回答同时满足：引用 ≥2 wiki 页面 + 含 LLM 推理 + 长期参考价值 → 询问用户确认后自动回填。知识在 query→回填→再 query 循环中不断沉淀。

[[llm-wiki-pattern]] — LLM Wiki 原始模式
[[llm-wiki-blog-building-journey-summary]] — 实践复现
