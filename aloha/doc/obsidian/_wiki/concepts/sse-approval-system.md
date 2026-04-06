---
title: SSE 实时审批通知系统
type: concept
tags: [agent, security, streaming, ui, design]
created: 2026-04-06
updated: 2026-04-06
sources: [sse-approval-plan]
summary: Aloha SSE 实时审批推送实现：EventManager 发布订阅、ApprovalManager 队列+幂等+5min超时、前端 EventSource 自动重连
---

基于 SSE（Server-Sent Events）实现后端 → 前端的实时审批通知推送，支持工具审批队列、幂等性保障、前端自动重连。

## 核心组件

| 组件 | 文件 | 职责 |
|------|------|------|
| `EventManager` | `web/service/events.py` | SSE 客户端注册、session 级队列、publish 发布 |
| `ApprovalManager` | `agent/approval_manager.py` | 审批队列、幂等（`_resolved` set）、5min 超时 |
| `StreamingReActLoop` | `agent/loop.py` | 端到端流式，事件发布到 EventManager |
| SSE Endpoint | `web/service/api.py` | `GET /api/events?session_id=xxx` |

## SSE 事件流

```
StreamingReActLoop
  → EventManager.publish("approval_required", ApprovalRequest)
  → SSE → 前端 ToolApprovalCard
  → 用户点击审批 → POST /api/approvals/{id}
  → ApprovalManager.resolve()
  → StreamingReActLoop 继续执行
```

## 事件类型

| 事件 | 内容 | 说明 |
|------|------|------|
| `heartbeat` | `{timestamp}` | 保活心跳（每 2 秒）|
| `approval_required` | `ApprovalRequest` | 需要用户审批 |
| `tool_result` | `{tool_call_id, success, content}` | 工具执行结果 |
| `approval_completed` | `{approval_id, decision}` | 审批已完成 |
| `thinking` | `{content}` | LLM thinking 增量（追加模式）|
| `message` | `{message}` | 最终助手消息 |

## 前端集成

- `stores/events.ts`：EventSource 状态管理（connection/reconnecting/disconnected），自动重连
- `composables/useApprovalEvents.ts`：SSE 事件订阅（thinking 追加模式、message finalize）
- `ChatView.vue`：实时 thinking 展示在最后一条助手消息

[[tool-approval-system]] — 工具审批两层层 Allow List
[[react-streaming]] — 流式 API 原理
