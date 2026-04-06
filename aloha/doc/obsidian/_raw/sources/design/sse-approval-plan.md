# Aloha SSE 实时审批通知系统实施方案

**日期**：2026-04-04
**版本**：v1.0
**状态**：已确认，待开发

---

## 1. 概述

### 1.1 目标

基于 SSE（Server-Sent Events）实现后端 → 前端的实时审批通知推送，支持：
1. 工具调用的人工审批流程（审批队列 + 5 分钟超时）
2. 幂等性保障（防止重复审批）
3. 前端自动重连机制

### 1.2 设计决策

| 项目 | 决策 |
|------|------|
| SSE URL | `/api/events?session_id=xxx` |
| HTTP API | 保留，不替换 |
| 审批超时 | 5 分钟 |
| 审批队列 | 必须，同一 session 一次只处理一个 pending 审批 |
| 幂等性 | 必须，基于 `approval_id` + `approved_at` 时间戳 |
| 写入文件审批 | 显示文件路径，特别提醒危险操作 |
| thinking 显示 | 工具调用审批**全部完成后**再显示 |
| MiniMax ID 规范化 | 保留现有 9 位 `tool_call_id` 哈希逻辑 |

---

## 2. 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                        前端 (Vue)                            │
├─────────────────────────────────────────────────────────────┤
│  EventSource (/api/events?session_id=xxx)                   │
│  ├── 接收: approval_required, approval_completed,           │
│  │        approval_timeout, heartbeat                        │
│  └── 自动重连（5次），显示警告                               │
│                                                              │
│  ChatView.vue                                               │
│  ├── pendingApprovals 审批队列（一次一个）                   │
│  ├── useApprovalEvents() 事件订阅                           │
│  └── ToolApprovalCard 审批卡片                               │
└─────────────────────────────────────────────────────────────┘
                            ▲ SSE
                            │
┌─────────────────────────────────────────────────────────────┐
│                     后端 (FastAPI)                           │
├─────────────────────────────────────────────────────────────┤
│  GET /api/events?session_id=xxx                            │
│                                                              │
│  EventManager（内存 Map: session_id → [SSE writers]）        │
│  ├── add_client(session_id, writer)                         │
│  ├── remove_client(session_id, writer)                      │
│  ├── publish(session_id, event_name, data)                  │
│  └── 多 writer 支持（多标签页）                              │
│                                                              │
│  ApprovalManager                                            │
│  ├── pending 审批队列（FIFO）                               │
│  ├── resolved 幂等记录 {id + approved_at}                    │
│  ├── wait(approval_id) 异步等待                             │
│  └── resolve(approval_id, decision) 解除阻塞                 │
│                                                              │
│  ReActLoop（改造）                                          │
│  ├── _call_llm() → Response                                 │
│  ├── _group_by_risk() → 分组                                │
│  └── _wait_approval() 阻塞等待                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. SSE 事件协议

### 3.1 后端 → 前端事件

```json
// 1. 需要审批（approval_required）
event: approval_required
data: {
  "approval": {
    "id": "appr-001",
    "tool_name": "file",
    "action": "write",
    "arguments": { "path": "/home/user/main.ts", "content": "..." },
    "risk_level": "high",
    "risk_color": "#ef4444",
    "description": "写入文件: /home/user/main.ts",
    "resource": "/home/user/main.ts",
    "timeout": 300
  },
  "queue_position": 1,
  "queue_total": 1
}

// 2. 审批完成（approval_completed）
event: approval_completed
data: {
  "approval_id": "appr-001",
  "decision": "approved",
  "reason": null,
  "approved_at": 1743849600000
}

// 3. 审批超时（approval_timeout）
event: approval_timeout
data: {
  "approval_id": "appr-001",
  "timeout": 300
}

// 4. 心跳保活（heartbeat）
event: heartbeat
data: {
  "timestamp": 1743849600000
}

// 5. thinking 内容（approval_completed 之后）
event: thinking
data: {
  "content": "用户想要...\n我将先..."
}

// 6. 最终消息（message）
event: message
data: {
  "message": {
    "id": "msg-assistant-001",
    "role": "assistant",
    "content": "这是一个很好的项目...",
    "timestamp": 1743849600000
  }
}

// 7. 工具执行结果（tool_result）
event: tool_result
data: {
  "tool_call_id": "appr-001",
  "success": true,
  "content": "写入成功"
}

// 8. 错误（error）
event: error
data: {
  "message": "工具执行被拒绝"
}
```

### 3.2 前端 → 后端（HTTP POST）

```json
// 1. 审批响应
POST /api/approvals/{approval_id}
Body: { "decision": "approved" | "rejected", "reason"?: string }
```

---

## 4. 文件变更清单

### 4.1 后端新增文件

| 文件 | 说明 |
|------|------|
| `aloha/agent/events.py` | 事件类型定义（ApprovalRequest 等） |
| `aloha/web/service/events.py` | EventManager（SSE 连接 + 事件发布） |
| `aloha/agent/approval_manager.py` | ApprovalManager（审批队列 + 幂等记录） |

### 4.2 后端修改文件

| 文件 | 修改内容 |
|------|----------|
| `aloha/agent/loop.py` | 新增 `StreamingReActLoop`，继承原 `ReActLoop`，集成事件发布 |
| `aloha/security/approver.py` | 改造为支持异步 Future 等待（非轮询） |
| `aloha/web/service/api.py` | 新增 `GET /api/events` SSE 端点 + `POST /api/approvals/{id}` 审批接口 |

### 4.3 前端新增文件

| 文件 | 说明 |
|------|------|
| `aloha/web/src/stores/events.ts` | SSE EventSource 状态管理 |
| `aloha/web/src/composables/useApprovalEvents.ts` | 审批事件订阅 composable |

### 4.4 前端修改文件

| 文件 | 修改内容 |
|------|----------|
| `aloha/web/src/views/ChatView.vue` | 集成 SSE 事件订阅 |
| `aloha/web/src/components/ToolApprovalCard.vue` | 支持 SSE 状态（等待中/队列显示/超时） |

### 4.5 新增测试文件

| 文件 | 说明 |
|------|------|
| `aloha/test/web/test_events.py` | EventManager 单元测试 |
| `aloha/test/agent/test_approval_manager.py` | ApprovalManager 单元测试 |
| `aloha/test/agent/test_streaming_loop.py` | StreamingReActLoop 集成测试 |
| `aloha/test/web/test_sse_endpoint.py` | SSE 端点测试 |

---

## 5. 执行顺序

### 第一阶段：后端基础设施
1. `aloha/agent/events.py` - 事件类型定义
2. `aloha/web/service/events.py` - EventManager
3. `aloha/agent/approval_manager.py` - ApprovalManager

### 第二阶段：后端核心
4. `aloha/agent/loop.py` - StreamingReActLoop
5. `aloha/security/approver.py` - Approver 改造
6. `aloha/web/service/api.py` - SSE 端点 + 审批接口

### 第三阶段：前端
7. `aloha/web/src/stores/events.ts` - SSE 状态管理
8. `aloha/web/src/composables/useApprovalEvents.ts` - 事件订阅
9. `aloha/web/src/views/ChatView.vue` - 集成事件订阅
10. `aloha/web/src/components/ToolApprovalCard.vue` - 队列 + 状态支持

### 第四阶段：测试
11. `aloha/test/web/test_events.py`
12. `aloha/test/agent/test_approval_manager.py`
13. `aloha/test/agent/test_streaming_loop.py`
14. `aloha/test/web/test_sse_endpoint.py`

---

## 6. 核心设计要点

### 6.1 审批队列（FIFO）

- `ApprovalManager` 内部用 `asyncio.Queue` 维护队列
- 同一 session 一次只发布一个 `approval_required` 事件
- `queue_position` / `queue_total` 告知前端排队位置

### 6.2 幂等性

- `_resolved: dict[str, ApprovalDecision]` 记录已完成的审批
- `ApprovalDecision` 含 `approved_at` 时间戳
- `enqueue()` 对已 approved 的 ID 直接返回 True（不重复入队）
- `resolve()` 对已存在的 approval_id 返回 False（不重复设置 Future）

### 6.3 5 分钟超时

- `enqueue()` 时启动 `asyncio.Task` 延时任务
- 超时后自动 `resolve(id, "rejected", "timeout")`
- `approval_timeout` 事件推送给前端

### 6.4 前端重连

- `EventSource.onerror` 触发重连，最多 5 次
- 重连中状态：`reconnecting`，显示警告 toast
- 5 次全部失败：`disconnected`，提示手动刷新

### 6.5 SSE 端点

```
GET  /api/events?session_id=xxx  →  text/event-stream
POST /api/approvals/{approval_id}  →  { decision, reason }
```

---

## 7. 事件类型汇总

| 事件名 | 方向 | 说明 |
|--------|------|------|
| `approval_required` | 后端→前端 | 工具需要审批 |
| `approval_completed` | 后端→前端 | 审批完成 |
| `approval_timeout` | 后端→前端 | 5分钟超时 |
| `heartbeat` | 后端→前端 | 每30s保活 |
| `thinking` | 后端→前端 | 思考内容 |
| `message` | 后端→前端 | 最终消息 |
| `tool_result` | 后端→前端 | 工具执行结果 |
| `error` | 后端→前端 | 错误 |

---

## 8. 测试用例设计

### 8.1 EventManager 测试（5 个）

- `test_add_remove_client`
- `test_publish_to_single_client`
- `test_publish_to_multiple_clients_same_session`
- `test_publish_no_client`
- `test_client_count`

### 8.2 ApprovalManager 测试（9 个）

- `test_enqueue_returns_true_first_time`
- `test_enqueue_returns_false_duplicate`
- `test_resolve_approved`
- `test_resolve_rejected`
- `test_resolve_idempotent`
- `test_wait_returns_approved`
- `test_wait_returns_false_on_timeout`
- `test_resolve_approved_wait_returns_true_immediately`
- `test_timeout_task_auto_rejects`

### 8.3 StreamingReActLoop 测试

- `test_approval_emitted_on_high_risk_tool`
- `test_queue_position_updated`
- `test_wait_blocks_until_approval`
- `test_timeout_rejected`
- `test_batch_grouping_by_risk`

### 8.4 SSE 端点测试

- `test_sse_returns_event_stream`
- `test_sse_heartbeat_sent`
- `test_sse_client_cleanup_on_disconnect`

---

## 9. 已知限制

| 限制 | 说明 |
|------|------|
| 多实例 | 当前为内存实现，不支持跨进程 |
| 登录清理 | 暂无 session 管理，后续扩展 |
| 多标签页同步 | 多个 EventSource 可独立连接，状态各自处理 |
