---
title: pi-mono (Superpowers)
type: entity
tags: [agent, typescript, session, skills]
created: 2026-04-06
updated: 2026-04-06
sources: [pi-mono-skills-analysis, pi-mono-session-management-analysis, pi-mono-memory-system-code-analysis]
summary: 轻量级 TypeScript Agent 框架，以 JSONL 树形会话管理和 Skills 系统著称
---

pi-mono（现更名为 Superpowers）是 OpenClaw 的核心基础项目，GitHub 28k stars，定位为**轻量级 Agent 框架**。

## 核心特性

- **极简核心**：不包含复杂记忆机制，通过扩展实现
- **会话树形结构**：JSONL 存储，支持分叉（fork）和分支导航
- **Skills 系统**：标准化 SKILL.md + 优先级覆盖机制（项目 > 个人 > superpowers）
- **上下文压缩**：`/compact` 手动/自动压缩长会话
- **多平台支持**：OpenCode、Claude Code、Codex 通用

## 会话管理系统

**存储格式**：JSONL，每行一个会话对象，带 parentId 支持树形分支。

```
s001 (root)
├── s002 (branch A)
│   ├── s004
│   └── s005
└── s003 (branch B)
```

**核心命令**：`/tree` 浏览跳转、`/fork` 分叉创建、`/compact` 上下文压缩。

## Skills 系统

SKILL.md 使用 YAML frontmatter 标准化元数据：

```yaml
---
name: skill-name
description: Use when [condition] - [what it does]
---
```

**路径优先级**：`.project/.opencode/skills/` > `~/.config/opencode/skills/` > `~/.config/opencode/superpowers/skills/`

支持 `superpowers:skill-name` 命名空间前缀。

## 与 Aloha 对比

| 特性 | pi-mono | Aloha |
|------|---------|-------|
| 语言 | TypeScript | Python |
| 会话存储 | JSONL 树形 | SQLite + 文件 |
| 分支 | ✅ | ❌ |
| 压缩 | ✅ | ❌ |
| Skills | 完整系统 | 简单加载器 |
| 扩展机制 | Extension API | 无 |

## 对 Aloha 的启示

1. **JSONL 存储**：简单的会话持久化格式
2. **上下文压缩**：transformContext hook
3. **Skills 优先级**：支持多层覆盖

## 相关链接

[[pi-mono-session-management-analysis-summary]] — 会话管理系统
[[pi-mono-skills-analysis-summary]] — Skills 加载逻辑
[[pi-mono-memory-system-code-analysis-summary]] — 记忆系统代码分析
