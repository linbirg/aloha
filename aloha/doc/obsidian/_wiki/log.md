---
title: LLM Wiki Log
description: 时间线日志，记录所有 ingest/compile/query/lint 操作
---

# LLM Wiki 操作日志

> append-only，按时间倒序

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
