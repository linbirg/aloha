---
title: OpenCode
type: entity
tags: [agent, tool, skills, opencode]
created: 2026-04-06
updated: 2026-04-06
sources: [opencode-user-manual]
summary: 开源 AI 编程助手，支持 75+ LLM providers，以 Skills 系统和 Agent 架构著称
---

OpenCode 是一个开源 AI 编程助手，支持 75+ LLM providers（Claude、GPT、Gemini、MiniMax、DeepSeek 等），是当前 LLM Wiki Skill 的运行引擎。

## 核心特性

- **多 Provider 支持**：75+ 模型统一接入
- **Agent 系统**：Build Agent（默认）和 Plan Agent（只读），支持 Subagent
- **Skills 技能系统**：SKILL.md 标准化格式，支持全局/项目级/Agent 级
- **权限审批系统**：按工具配置 allow/ask/deny
- **Git 集成**：undo/redo 历史
- **多 Session 管理**：会话共享、导出为 Markdown

## Skills 系统

**SKILL.md 格式**：

```yaml
---
name: skill-name
description: Use when [condition] - [what it does]
---
```

**路径**（优先级从高到低）：

```
.project/.opencode/skills/<name>/SKILL.md  # 项目级
~/.config/opencode/skills/<name>/SKILL.md  # 全局
~/.claude/skills/<name>/SKILL.md           # Claude 兼容
.agents/skills/<name>/SKILL.md             # Agent 兼容
```

Skills 可配置 `metadata.always=true` 自动加载到 system prompt。

## 配置系统

```json
{
  "model": "anthropic/claude-sonnet-4-5",
  "permission": { "edit": "ask", "bash": "ask" },
  "share": "manual"
}
```

## 对 Aloha 的关联

- Skills 系统是 LLM Wiki Skill 的实现基础
- Plan Mode / Build Mode 区分与 Aloha 的 agent 模式设计相似
- 权限系统与 Aloha 的 ApprovalManager 可对比

## 相关链接

[[opencode-user-manual-summary]] — 完整使用手册
[[pi-mono-skills-analysis-summary]] — pi-mono Skills 系统对比
