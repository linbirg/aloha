---
title: 用 OpenCode Skill 复现 LLM Wiki 知识库
type: summary
tags: [wiki, knowledge-management, opencode, llm]
created: 2026-04-06
updated: 2026-04-06
sources: [llm-wiki-blog-building-journey]
summary: 博客复现 Karpathy LLM Wiki 模式的全过程：动机（知识给人 vs 给 AI 用）、三層架构（Raw→Wiki→Schema）、回填飞轮机制
---

用 OpenCode Skill 完整复现了 Karpathy 的 LLM Wiki 知识库模式，核心解决"笔记维护累人"问题。

**核心理念**：人不碰 Wiki，Wiki 是 LLM 的领地。知识库不是给人翻的，是给 AI 看的——当 AI 在你的知识库里导航、理解、推理，才是系统真正发挥价值的时候。

**三层架构**：Raw Sources（不可变原始资料）→ Wiki（LLM 生成的 .md 文件，双向链接）→ Schema（AGENTS.md/CLAUDE.md 行为规则）。

**回填飞轮**：query 回答质量够高则自动存回 Wiki，下次查询时新页面成为检索对象，知识在循环里不断沉淀。

**技术实现**：纯 Markdown，无数据库，状态分散在各页面 frontmatter + `registry.md`。compile 后自动跑 lint 修复时序依赖导致的占位链接问题。

[[llm-wiki-pattern]] — 概念页
