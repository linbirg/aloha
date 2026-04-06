---
title: WebSocket 实时通信 + 审批流程方案
type: concept
tags: [agent, security, streaming, ui, design]
created: 2026-04-06
updated: 2026-04-06
sources: [websocket-approval-plan]
summary: WebSocket 双向通信方案作为 SSE 的替代，支持 thinking 推送、工具调用过程、批量审批；SSE 方案已实现，WebSocket 为备选
---

基于 WebSocket 的前后端双向通信方案，作为 SSE 的备选，支持 thinking 推送、工具调用过程、批量审批功能。

## 与 SSE 方案的对比

| 特性 | SSE | WebSocket |
|------|-----|----------|
| 方向 | 单向（服务端→客户端）| 双向 |
| 复杂度 | 低 | 高 |
| 前端重连 | 需手动实现 | 原生支持 |
| 审批提交 | HTTP POST | WebSocket 消息 |
| 适用场景 | 简单实时推送 | 复杂双向交互 |

## 核心功能

1. **工具调用的审批流程**：阻塞等待用户决策
2. **实时 thinking 推送**：LLM reasoning 中间步骤
3. **工具调用过程推送**：tool_progress 实时反馈
4. **批量审批**：支持同时审批多个工具调用

## 结论

SSE 方案已实现并投入使用（`sse-approval-plan`），WebSocket 方案作为备选留存，当 SSE 无法满足需求时再切换。

[[sse-approval-system]] — 已实现的 SSE 方案
[[tool-approval-system]] — 工具审批两层层 Allow List
