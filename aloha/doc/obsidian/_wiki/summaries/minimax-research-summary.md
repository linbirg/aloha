---
title: MiniMax API Function Call 研究摘要
type: summary
tags: [agent, provider, minimax, tool]
created: 2026-04-06
updated: 2026-04-06
sources: [minimax-research]
summary: MiniMax-M2.7 tool_call_id 规范化（9位 hash）+ reasoning_content 截断 + 思考字段回传要求，解决 invalid params (2013) 错误
---

MiniMax API 与标准 OpenAI 兼容接口的关键差异研究，核心问题为 `tool_call_id` 匹配和 `reasoning_content` 处理。

**tool_call_id 规范化**：MiniMax API 返回长字符串 tool_call_id，但工具执行结果需回传时必须完全匹配。MiniMaxProvider 通过 hash 截取前 9 位作为规范化 ID，适配前端和工具执行层的长度要求。

**MiniMax-M2.7 特性**：原生支持 Interleaved Thinking，每轮 Tool Use 前根据环境返回进行思考并决策下一步。在 SWE、BrowseCamp、xBench 等 Code & Agent Benchmark 达到 SOTA。

**必须回传每一次 Response 的全部信息，尤其是 `thinking/reasoning_details` 字段**，这是 M2.7 推理能力的核心。

[[provider-refactor-plan]] — MiniMaxProvider 与 OpenAIProvider 解耦
[[hermes-agent]] — 工具调用循环参考
