---
title: pi-mono Skills 系统分析摘要
type: summary
tags: [pi-mono, skills, yaml]
created: 2026-04-06
updated: 2026-04-06
sources: [pi-mono-skills-analysis]
summary: pi-mono Skills 系统完整分析，SKILL.md YAML frontmatter + 递归发现 + 优先级覆盖 + Git 更新检查
---

pi-mono Skills 系统比 OpenCode 更完善：YAML frontmatter 标准化元数据 + 递归目录扫描（maxDepth=3）+ 优先级覆盖（项目 > 个人 > superpowers）+ `use_skill`/`find_skills` 工具集成。

**与 Aloha 对比**：Aloha SkillsLoader 缺少 YAML 支持、优先级覆盖、Git 更新检查和专用工具集成。

[[skills-system]] — 概念页
