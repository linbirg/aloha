---
title: LLM Wiki Index
description: 全局索引，所有 Wiki 页面的入口
---

# LLM Wiki 全局索引

> 最后更新：2026-04-06

## 统计

- Raw Sources：35 篇（agent-research/ 21 篇 + design/ 14 篇）
- Wiki 页面：59 篇（entities/ 5 + concepts/ 11 + summaries/ 31 + tags/ 44）
- 编译率：97%（34/35 compiled，4 pending 均为 doc_ 前缀冲突版本）

## 实体（entities/）

| 页面 | 摘要 |
|------|------|
| [[hermes-agent]] | NousResearch 出品的自我进化 AI Agent，闭环学习记忆系统 |
| [[mastra]] | Gatsby 团队的全栈 AI 应用框架，工作流引擎 + 多层次记忆 |
| [[pi-mono]] | 轻量级 TypeScript Agent 框架，JSONL 树形会话管理 |
| [[ai-sdk]] | Vercel 出品的 AI SDK，声明式自动工具调用循环 |
| [[opencode]] | 开源 AI 编程助手，Skills 系统 + Agent 架构 |

## 概念（concepts/）

| 页面 | 摘要 |
|------|------|
| [[llm-wiki-pattern]] | Karpathy 提出的知识管理模式，持久 Wiki 实现知识复合积累 |
| [[agent-loop]] | Agent 执行核心循环，SDK 自动循环 vs 手动 ReAct 循环 |
| [[react-streaming]] | ReAct 模式中流式 API 原理，工具调用截断和文本流式输出 |
| [[memory-system]] | Agent 记忆系统设计，会话/长期/用户建模多层架构 |
| [[skills-system]] | Skills 行为规范模块，SKILL.md 标准化格式 |
| [[sse-approval-system]] | SSE 实时审批推送：EventManager + ApprovalManager + 前端 EventSource |
| [[tool-approval-system]] | 工具审批两层层 Allow List 模式：PermissionChecker + ShellTool |
| [[session-management-design]] | Session 管理：SQLite 元数据 + 文件系统资源、继承覆盖配置 |
| [[provider-refactor-plan]] | Provider 重构：MiniMax/OpenAI 解耦，MiniMax 只处理 ID normalization |
| [[llm-wiki-skill-plan]] | LLM Wiki Skill 五阶段实现：ingest/compile/query/lint/status |
| [[websocket-approval-plan]] | WebSocket 双向通信方案（SSE 备选）：thinking 推送、批量审批 |

## 摘要（summaries/）

| 页面 | 来源 |
|------|------|
| [[ai-sdk-tool-loop-analysis-summary]] | agent-research/ai-sdk-tool-loop-analysis.md |
| [[hermes-agent-analysis-summary]] | agent-research/hermes-agent-analysis.md |
| [[hermes-agent-fts5-analysis-summary]] | agent-research/hermes-agent-fts5-analysis.md |
| [[hermes-agent-loop-analysis-summary]] | agent-research/hermes-agent-loop-analysis.md |
| [[hermes-honcho-analysis-summary]] | agent-research/hermes-honcho-analysis.md |
| [[hermes-memory-system-analysis-summary]] | agent-research/hermes-memory-system-analysis.md |
| [[llm-wiki-analysis-deep-dive-summary]] | agent-research/llm-wiki-analysis-deep-dive.md |
| [[llm-wiki-blog-building-journey-summary]] | agent-research/llm-wiki-blog-building-journey.md |
| [[llm-wiki-claude-code-obsidian-practice-summary]] | agent-research/llm-wiki-claude-code-obsidian-practice.md |
| [[llm-wiki-karpathy-analysis-summary]] | agent-research/llm-wiki-karpathy-analysis.md |
| [[llm-wiki-space-economy-karpathy-practice-summary]] | agent-research/llm-wiki-space-economy-karpathy-practice.md |
| [[mastra-analysis-summary]] | agent-research/mastra-analysis.md |
| [[mastra-loop-analysis-summary]] | agent-research/mastra-loop-analysis.md |
| [[opencode-user-manual-summary]] | agent-research/opencode-user-manual.md |
| [[pi-mono-memory-system-code-analysis-summary]] | agent-research/pi-mono-memory-system-code-analysis.md |
| [[pi-mono-session-management-analysis-summary]] | agent-research/pi-mono-session-management-analysis.md |
| [[pi-mono-skills-analysis-summary]] | agent-research/pi-mono-skills-analysis.md |
| [[agent-research-summary]] | agent-research/agent-research.md |
| [[minimax-research-summary]] | agent-research/minimax-research.md |
| [[nanobot-research-summary]] | agent-research/nanobot-research.md |
| [[reactloop-test-plan-summary]] | design/reactloop-test-plan.md |
| [[security-tools-design-summary]] | design/security-tools-design.md |
| [[security-tools-impl-plan-summary]] | design/security-tools-impl-plan.md |
| [[web-ui-design-summary]] | design/web-ui-design.md |

## 标签（tags/）

| 标签 | 页面数 |
|------|--------|
| [[tags/agent]] | 9 |
| [[tags/memory]] | 6 |
| [[tags/loop]] | 5 |
| [[tags/wiki]] | 6 |
| [[tags/typescript]] | 4 |
| [[tags/streaming]] | 3 |
| [[tags/python]] | 3 |
| [[tags/skills]] | 5 |
| [[tags/react]] | 3 |
| [[tags/sqlite]] | 2 |
| [[tags/fts5]] | 2 |
| [[tags/framework]] | 3 |
| [[tags/opencode]] | 3 |
| [[tags/karpathy]] | 3 |
| [[tags/workflow]] | 2 |
| [[tags/sdk]] | 2 |
| [[tags/jsonl]] | 3 |
| [[tags/session]] | 4 |
| [[tags/tool]] | 6 |
| [[tags/user-model]] | 1 |
| [[tags/honcho]] | 1 |
| [[tags/fork]] | 1 |
| [[tags/compact]] | 1 |
| [[tags/analysis]] | 1 |
| [[tags/claude-code]] | 1 |
| [[tags/obsidian]] | 1 |
| [[tags/nous-research]] | 1 |
| [[tags/yaml]] | 1 |
| [[tags/search]] | 1 |
| [[tags/farzapedia]] | 1 |
| [[tags/manual]] | 1 |
| [[tags/practice]] | 1 |
| [[tags/security]] | 3 |
| [[tags/design]] | 5 |
| [[tags/ui]] | 3 |
| [[tags/provider]] | 1 |
| [[tags/minimax]] | 1 |
| [[tags/refactor]] | 1 |
| [[tags/knowledge-management]] | 2 |
| [[tags/skill]] | 1 |
| [[tags/nanobot]] | 1 |
| [[tags/test]] | 1 |
| [[tags/vue]] | 1 |

## 研究主题覆盖

| 主题 | 相关实体/概念 |
|------|--------------|
| Agent 循环 | [[agent-loop]] [[react-streaming]] [[hermes-agent]] [[mastra]] [[ai-sdk]] |
| 记忆系统 | [[memory-system]] [[hermes-agent]] [[pi-mono]] [[session-management-design]] |
| Skills 系统 | [[skills-system]] [[opencode]] [[pi-mono]] |
| LLM Wiki | [[llm-wiki-pattern]] [[llm-wiki-skill-plan]] |
| 安全审批 | [[tool-approval-system]] [[sse-approval-system]] [[websocket-approval-plan]] |
| Provider 架构 | [[provider-refactor-plan]] [[opencode]] [[ai-sdk]] [[minimax-research-summary]] |
| 多 Agent 系统 | [[nanobot-research-summary]] [[agent-research-summary]] |
