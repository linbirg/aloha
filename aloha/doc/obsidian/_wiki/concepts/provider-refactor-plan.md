---
title: Provider 重构设计方案
type: concept
tags: [agent, provider, openai, minimax, refactor]
created: 2026-04-06
updated: 2026-04-06
sources: [provider-refactor-plan]
summary: 将 MiniMaxProvider 和 OpenAIProvider 解耦：MiniMaxProvider 只处理 ID normalization（9位 hash tool_call_id），OpenAIProvider 纯 OpenAI 兼容
---

将 MiniMaxProvider 和 OpenAIProvider 解耦，使各自职责清晰。

## 重构目标

- `OpenAIProvider` — 纯 OpenAI 兼容实现，不知道 MiniMax 存在
- `MiniMaxProvider` — 只处理 MiniMax 特有逻辑（如 reasoning_content 截断、ID normalization）

## 关键设计决策

| 项目 | 决策 |
|------|------|
| BaseProvider | 非抽象，提供默认实现 |
| reasoning_split | 完全移除，不在 OpenAIProvider 中出现 |
| 向后兼容 | 不需要，同步修改受影响代码 |
| extract_thinking 返回值 | `str \| None` |

## MiniMax ID Normalization

MiniMax API 返回的 tool_call_id 是长字符串，MiniMaxProvider 通过 hash 截取前 9 位作为规范化 ID，适配前端和工具执行层的 ID 长度要求。

## 与其他 Provider 的关系

当前 Aloha 支持多 Provider：OpenAI、MiniMax、Anthropic、DeepSeek、OpenRouter。BaseProvider 定义统一接口（`chat()`、`chat_with_tools()`），各 Provider 按需重写。

[[opencode]] — OpenCode 的 Provider 架构
[[ai-sdk]] — AI SDK 的多 Provider 路由
