---
title: LLM Wiki Log
description: 时间线日志，记录所有 ingest/compile/query/lint 操作
---

# LLM Wiki 操作日志

> append-only，按时间倒序

## [2026-04-06] 目录重组 + compile + lint（第三次）

**目录重组**：`sources/` 下散落的 .md 研究文件已迁入 `agent-research/` 子目录；原 `doc/design/` 和 `obsidian/design/` 合并为 `sources/design/`；新增 `winpowershell/`（配置文件，不纳入 registry）。

**registry.md 重建**：路径前缀更新（`agent-research/`、`design/`）；新增 3 篇 pending（`agent-research.md`、`minimax-research.md`、`nanobot-research.md`）；新增 4 篇 pending（`reactloop-test-plan.md`、`security-tools-design.md`、`security-tools-impl-plan.md`、`web-ui-design.md`）；4 篇 doc_ 前缀冲突版本保留为 pending。

**lint**：扫描所有 wiki 跨引用，断链数 0。`[[BUDGET WARNING]]` 和 `[[xxx-analysis]]` 仅出现于 log.md 文字说明中，非真实引用。

**compile 新增摘要**（7 篇）：
- `agent-research-summary` — Anthropic 双轨 Agent + ClawTeam 多 Agent 编排
- `minimax-research-summary` — MiniMax tool_call_id 规范化 + reasoning_content
- `nanobot-research-summary` — Aloha vs NanoBot 对比
- `reactloop-test-plan-summary` — ReActLoop 测试计划
- `security-tools-design-summary` — 安全工具三层架构设计
- `security-tools-impl-plan-summary` — 四阶段实现计划
- `web-ui-design-summary` — Vue 3 前端设计规格

**index.md 更新**：统计更新为 Raw Sources 35 篇、Wiki 页面 59 篇、编译率 97%；新增标签：nanobot、test、vue；研究主题覆盖新增"多 Agent 系统"。

## [2026-04-06] compile + lint（第二次）

**lint 断链修复**：扫描所有 wiki 页面跨引用，发现 2 处 `[[BUDGET WARNING]]` 断链（位于 `agent-loop.md`、`react-streaming.md`），已修复为普通文本。

**compile 新增编译**：
- 2 篇 pending 摘要：`hermes-agent-loop-analysis-summary`、`llm-wiki-blog-building-journey-summary`
- 6 篇新概念（来自 `design/` 目录）：`sse-approval-system`、`tool-approval-system`、`session-management-design`、`provider-refactor-plan`、`llm-wiki-skill-plan`、`websocket-approval-plan`

**registry.md 创建**：`design/` 目录 10 篇文档已录入 registry，6 篇标记 compiled，4 篇标记 pending（doc_ 前缀重复版本）。

**index.md 更新**：统计改为 Raw Sources 27 篇、Wiki 页面 53 篇、编译率 88%；新增标签：security、design、ui、provider、minimax、refactor、knowledge-management、skill。

## [2026-04-06] query 系统化

阶段三实现：
- `/llm-wiki status` 仪表盘可用：Raw Sources 17 篇（17 compiled / 1 pending）、Wiki 页面 58 篇、断链 0
- SKILL.md 更新：query 命令详细流程（6 步 + 回填判断标准 4 条 + 查询优先级 3 级）
- query 回填机制验证成功（ReAct 流式 API → [[react-streaming]] 概念页）

## [2026-04-06] lint

`/llm-wiki lint` 健康检查报告：

**断链修复**：扫描发现 11 个实体/概念页引用了 source 文件名（而非 summary 文件名），已全部修复
- `[[xxx-analysis]]` → `[[xxx-analysis-summary]]`
- 影响页面：hermes-agent、mastra、pi-mono、ai-sdk、memory-system、llm-wiki-pattern、skills-system、opencode、agent-loop

**tags/ 补全**：补建 15 个 tag 页（session、tool、honcho、fork、compact、analysis、claude-code、obsidian、nous-research、yaml、search、farzapedia、manual、practice、user-model）

**index.md 验证**：全部 32 个 tag 索引页已确认存在，无断链

## [2026-04-06] auto-tagging

阶段二实现：扫描所有 Wiki 页面 tags，生成 29 个标签索引页（tags/）。

**新增 tags/ 索引页**：agent、memory、loop、streaming、wiki、typescript、python、skills、react、sqlite、fts5、framework、opencode、karpathy、workflow、sdk、jsonl、session、tool

**index.md 更新**：tags/ 部分从"暂无"替换为完整的标签索引表

## [2026-04-06] query + file

**问题**：ReAct 模式中的流式 API 原理是什么？

**回答**：ReAct 流式 API 本质是 LLM 输出管道化。两种路线：SDK 自动循环（Mastra）通过 `workflowLoopStream` 实时分拣，LLM 生成 tool_call 时截断立即执行；手动 ReAct（Hermes）遍历 stream chunk 检测 tool_calls 后截断处理。关键机制：工具调用截断、文本流式输出、结果注入、并行工具支持。

**回填**：已创建 [[react-streaming]] 概念页

## [2026-04-06] compile

首次批量编译：
- 16 篇 Raw Sources → 27 篇 Wiki 页面
- 实体页：hermes-agent、mastra、pi-mono、ai-sdk、opencode
- 概念页：llm-wiki-pattern、agent-loop、memory-system、skills-system
- 摘要页：16 篇（每篇 source 一份摘要）
- registry.md：16 篇全部标记 compiled
- 编译率：100%

## [2026-04-06] init

初始化 LLM Wiki：
- 创建 `_raw/sources/` 目录，迁入 16 篇 Raw Sources
- 创建 `_wiki/` 目录结构（entities/, concepts/, summaries/, tags/）
- 初始化 registry.md，16 篇全部标记 pending
