---
title: Skills 系统
type: concept
tags: [agent, skills, knowledge, opencode]
created: 2026-04-06
updated: 2026-04-06
sources: [pi-mono-skills-analysis, opencode-user-manual]
summary: Skills 是 Agent 的行为规范模块，通过标准化 SKILL.md 实现知识复用
---

Skills 是 Agent 的可复用行为规范模块，通过 SKILL.md 文件定义，Agent 加载后按规范执行特定任务。

## 核心机制

SKILL.md 格式：

```yaml
---
name: skill-name
description: Use when [condition] - [what it does]
---

# Skill Title

## Overview
Skill content...
```

## 路径优先级

| 来源 | 路径 | 优先级 |
|------|------|--------|
| 项目级 | `.project/.opencode/skills/<name>/SKILL.md` | 最高 |
| 全局 | `~/.config/opencode/skills/<name>/SKILL.md` | 中 |
| 内置 | `~/.config/opencode/superpowers/skills/` | 低 |

## 两种技能发现机制

| 系统 | 发现方式 | 工具集成 |
|------|---------|---------|
| OpenCode | 目录遍历 `skills/` → `SKILL.md` | 无独立 Tool |
| pi-mono | 递归扫描（maxDepth=3）+ `use_skill`/`find_skills` Tool | 有专用工具 |

## 两种加载模式

| 模式 | 说明 | 代表 |
|------|------|------|
| 指令型 | SKILL.md 定义行为规范，LLM 读后用文件工具执行 | OpenCode Skills |
| 工具型 | 注册为独立 Tool，LLM 直接调用 | pi-mono |

## LLM Wiki Skill

本文档本身就是 LLM Wiki Skill 的产物，存放在 `~/.config/opencode/skills/llm-wiki/SKILL.md`。

## 对 Aloha 的启示

Aloha 的 SkillsLoader（`aloha/agent/skills.py`）目前是**指令型**，但功能较简单：

- 缺少 YAML frontmatter 支持
- 缺少多优先级覆盖
- 缺少 `always_skills` 自动注入机制（仅 nanobot 版本有）
- 缺少 Git 更新检查

## 相关链接

[[opencode-user-manual-summary]] — OpenCode Skills 系统
[[pi-mono-skills-analysis-summary]] — pi-mono Skills 加载逻辑
