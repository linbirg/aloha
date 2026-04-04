# Aloha WebSocket 实时通信 + 审批流程实施方案

**日期**：2026-04-04
**版本**：v1.0
**状态**：已确认，待开发

---

## 1. 概述

### 1.1 目标

实现基于 WebSocket 的前后端双向通信，支持：
1. 工具调用的人工审批流程（阻塞等待）
2. 实时推送 thinking 和工具调用过程
3. 批量审批功能

### 1.2 设计决策

| 项目 | 决策 |
|------|------|
| WebSocket URL | `/api/ws/chat` |
| HTTP API | 保留，不替换 |
| 审批超时 | 无超时限制 |
| 写文件审批 | 显示文件路径，特别提醒危险操作 |
| 批量审批 | 支持多工具/多文件一次性审批 |
| thinking 显示 | 工具调用审批**全部完成后**再显示 |
| MiniMax ID 规范化 | 保留 `_id_map` 机制，tool_call_id 规范化为 9 位 |

---

## 2. 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                        前端 (Vue)                            │
├─────────────────────────────────────────────────────────────┤
│  WebSocketClient (单连接)                                   │
│  ├── 发送: user_message, approve, reject                   │
│  ├── 接收: thinking, tool_call, tool_result, final         │
│  └── 自动重连                                              │
│                                                              │
│  ChatView.vue                                               │
│  ├── pendingApprovals 审批队列                             │
│  ├── thinking 内容（审批完成后显示）                         │
│  └── message 列表                                          │
└─────────────────────────────────────────────────────────────┘
                           ▲ WebSocket
                           │
┌─────────────────────────────────────────────────────────────┐
│                     后端 (FastAPI + WebSocket)               │
├─────────────────────────────────────────────────────────────┤
│  ws://localhost:8000/api/ws/chat                           │
│                                                              │
│  ConnectionManager                                          │
│  ├── 存储 WebSocket 连接                                   │
│  ├── pending_futures 等待审批结果                          │
│  └── resolve_approval() 解除阻塞                           │
│                                                              │
│  StreamingReActLoop                                         │
│  ├── 继承 ReActLoop，复用 _call_llm()                      │
│  ├── MiniMax ID 规范化已处理                               │
│  └── _wait_approval() 阻塞等待                            │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. WebSocket 消息协议

### 3.1 前端 → 后端

```json
// 1. 用户发送消息
{ "type": "user_message", "id": "msg-001", "content": "帮我分析这个项目" }

// 2. 批准单个审批
{ "type": "approve", "approval_id": "appr-001" }

// 3. 拒绝单个审批
{ "type": "reject", "approval_id": "appr-001" }

// 4. 批量批准
{ "type": "approve_batch", "approval_ids": ["appr-001", "appr-002"] }

// 5. 批量拒绝
{ "type": "reject_batch", "approval_ids": ["appr-001", "appr-002"] }
```

### 3.2 后端 → 前端

```json
// 1. 需要审批
{ 
  "type": "approval_required", 
  "data": {
    "approval": {
      "id": "appr-001",
      "tool_name": "file",
      "action": "write",
      "arguments": { "path": "/home/user/main.ts", "content": "..." },
      "risk_level": "high",
      "risk_color": "#ef4444",
      "description": "写入文件: /home/user/main.ts",
      "resource": "/home/user/main.ts",
      "batch_id": null
    }
  }
}

// 2. 工具执行结果
{ "type": "tool_result", "data": { "id": "appr-001", "success": true, "content": "写入成功" } }

// 3. Thinking 内容（审批完成后）
{ "type": "thinking", "data": { "content": "用户想要...\n我将先..." } }

// 4. 最终消息
{ 
  "type": "message", 
  "data": {
    "message": {
      "id": "msg-assistant-001",
      "role": "assistant",
      "content": "这是一个很好的项目...",
      "timestamp": 1743849600000
    }
  }
}

// 5. 错误
{ "type": "error", "data": { "message": "工具执行被拒绝" } }
```

---

## 4. 文件变更清单

### 4.1 后端新增文件

| 文件 | 说明 |
|------|------|
| `aloha/agent/events.py` | 事件类型定义（ApprovalRequest 等） |
| `aloha/agent/approval_manager.py` | 审批管理器（Future + 存储） |
| `aloha/web/service/connection_manager.py` | WebSocket 连接管理 |

### 4.2 后端修改文件

| 文件 | 修改内容 |
|------|----------|
| `aloha/agent/loop.py` | 新增 `StreamingReActLoop` 类，继承原 `ReActLoop` |
| `aloha/web/service/api.py` | 新增 WebSocket 端点 `/api/ws/chat` |

### 4.3 前端新增文件

| 文件 | 说明 |
|------|------|
| `aloha/web/src/api/websocket.ts` | WebSocket 客户端 |

### 4.4 前端修改文件

| 文件 | 修改内容 |
|------|----------|
| `aloha/web/src/stores/chat.ts` | 集成 WebSocket |
| `aloha/web/src/views/ChatView.vue` | 使用 WebSocket 发送/接收消息 |
| `aloha/web/src/components/ToolApprovalCard.vue` | 适配新协议，支持批量 |

---

## 5. 核心代码逻辑

### 5.1 events.py - 事件定义

```python
@dataclass
class ApprovalRequest:
    id: str
    tool_name: str
    action: str
    arguments: dict
    risk_level: str
    risk_color: str
    description: str
    resource: str
    batch_id: str | None
```

### 5.2 StreamingReActLoop - 流式处理

关键点：
- 继承原 `ReActLoop`，复用 `_call_llm()` 和 `_execute_tool()`
- `_call_llm()` 返回的 `Response` 包含已规范化的 tool_calls（MiniMaxProvider 处理过）
- tool_call.id 直接使用，无需再次规范化
- `_wait_for_approval()` 使用 `ApprovalManager.wait()`

```python
class StreamingReActLoop(ReActLoop):
    def __init__(self, manager: 'ConnectionManager', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._manager = manager
    
    async def process_streaming(self, user_input: str):
        self.session_memory.add_user_message(user_input)
        
        while iteration < self.max_iterations:
            response = await self._call_llm()  # 复用，ID 已规范化
            
            if response.tool_calls:
                groups = self._group_by_risk(response.tool_calls)
                for batch in groups:
                    approval = self._build_approval(batch)
                    await self._manager.emit("approval_required", {"approval": approval})
                    
                    # 阻塞等待审批
                    approved = await self._manager.wait_approval(approval["id"])
                    if not approved:
                        await self._manager.emit("error", {"message": "工具被拒绝"})
                        return
                    
                    # 执行工具
                    for tc in batch:
                        result = await self._execute_tool(tc)
                        await self._manager.emit("tool_result", {...})
            
            if not response.tool_calls:
                break
        
        # 审批完成后，推送 thinking
        if response.thinking:
            await self._manager.emit("thinking", {"content": response.thinking})
        
        # 推送最终消息
        await self._manager.emit("message", {"message": {...}})
```

### 5.3 ConnectionManager - 连接 + 审批管理

```python
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
        self.pending_futures: dict[str, asyncio.Future[bool]] = {}
        self.pending_approvals: dict[str, dict] = {}
    
    async def connect(self, websocket: WebSocket) -> str:
        await websocket.accept()
        client_id = str(uuid.uuid4())
        self.active_connections[client_id] = websocket
        return client_id
    
    async def emit(self, event_type: str, data: dict):
        """广播事件到所有连接"""
        for ws in self.active_connections.values():
            await ws.send_json({"type": event_type, "data": data})
    
    def create_approval(self, approval_id: str) -> asyncio.Future[bool]:
        future = asyncio.Future()
        self.pending_futures[approval_id] = future
        return future
    
    async def wait_approval(self, approval_id: str) -> bool:
        future = self.pending_futures.get(approval_id)
        if not future:
            return False
        return await future
    
    def resolve_approval(self, approval_id: str, approved: bool):
        future = self.pending_futures.pop(approval_id, None)
        if future and not future.done():
            future.set_result(approved)
```

### 5.4 批量审批分组逻辑

```python
def _group_by_risk(self, tool_calls) -> list[list[ToolCall]]:
    """按风险级别分组，高风险单独审批，中低风险可批量"""
    high, medium, low = [], [], []
    
    for tc in tool_calls:
        perm = self._build_permission(tc)
        risk = self.checker.assess_risk(perm)
        if risk == RiskLevel.HIGH:
            high.append(tc)
        elif risk == RiskLevel.MEDIUM:
            medium.append(tc)
        else:
            low.append(tc)
    
    groups = []
    if high: groups.append(high)
    if medium: groups.append(medium)
    if low: groups.append(low)
    return groups
```

### 5.5 文件路径提取（用于展示）

```python
def extract_resource(tool_name: str, arguments: dict) -> str:
    """从工具参数中提取资源路径"""
    if tool_name == "file":
        return arguments.get("path", str(arguments))
    elif tool_name == "shell":
        cmd = arguments.get("command", "")
        return cmd.split()[1] if len(cmd.split()) > 1 else cmd
    elif tool_name == "web":
        return arguments.get("url", "")
    return str(arguments)

def build_description(tool_name: str, arguments: dict, resources: list[str]) -> str:
    """构建审批描述"""
    if len(resources) == 1:
        return f"{tool_name}: {resources[0]}"
    elif len(resources) <= 5:
        return f"{tool_name}: {len(resources)} 个文件\n" + "\n".join(resources)
    else:
        return f"{tool_name}: {len(resources)} 个文件\n" + \
               "\n".join(resources[:3]) + f"\n... 等 {len(resources)} 个"
```

---

## 6. 前端实现

### 6.1 WebSocket 客户端 (websocket.ts)

```typescript
class WebSocketClient {
  private ws: WebSocket | null = null
  
  connect() {
    this.ws = new WebSocket('/api/ws/chat')
    
    this.ws.onopen = () => console.log('WebSocket connected')
    
    this.ws.onmessage = (event) => {
      const msg = JSON.parse(event.data)
      
      switch (msg.type) {
        case 'approval_required':
          chatStore.addPendingApproval(msg.data.approval)
          break
        case 'tool_result':
          chatStore.removePendingApproval(msg.data.id)
          break
        case 'thinking':
          chatStore.setThinking(msg.data.content)
          break
        case 'message':
          chatStore.addMessage(msg.data.message)
          chatStore.setLoading(false)
          break
        case 'error':
          chatStore.setError(msg.data.message)
          break
      }
    }
  }
  
  send(data: object) {
    this.ws?.send(JSON.stringify(data))
  }
  
  approve(id: string) { this.send({ type: 'approve', approval_id: id }) }
  reject(id: string) { this.send({ type: 'reject', approval_id: id }) }
  approveBatch(ids: string[]) { this.send({ type: 'approve_batch', approval_ids: ids }) }
  rejectBatch(ids: string[]) { this.send({ type: 'reject_batch', approval_ids: ids }) }
}
```

---

## 7. 审批 UI 效果

### 7.1 单个文件审批

```
┌──────────────────────────────────────────────────────────┐
│ 🔧 tool: file                                           │
│ 📁 risk: HIGH                                           │
│ 路径: /home/user/project/src/main.ts                    │
├──────────────────────────────────────────────────────────┤
│              [✕ 拒绝]    [✓ 批准]                       │
└──────────────────────────────────────────────────────────┘
```

### 7.2 批量文件审批

```
┌──────────────────────────────────────────────────────────┐
│ ⏸️ 待审批: 文件写入操作 (3 个文件)                       │
│ 🔧 tool: file | 📁 risk: HIGH                          │
├──────────────────────────────────────────────────────────┤
│ 📄 /home/user/project/src/main.ts                        │
│ 📄 /home/user/project/src/utils.ts                       │
│ 📄 /home/user/project/src/config.ts                      │
├──────────────────────────────────────────────────────────┤
│        [✕ 全部拒绝]    [✓ 全部批准]                      │
└──────────────────────────────────────────────────────────┘
```

---

## 8. 执行顺序

### 8.1 第一阶段：后端基础设施

1. `aloha/agent/events.py` - 事件类型定义
2. `aloha/agent/approval_manager.py` - 审批管理器
3. `aloha/web/service/connection_manager.py` - 连接管理

### 8.2 第二阶段：后端核心

4. `aloha/agent/streaming_loop.py` - 流式 Agent
5. `aloha/web/service/api.py` - 新增 WebSocket 端点

### 8.3 第三阶段：前端

6. `aloha/web/src/api/websocket.ts` - WebSocket 客户端
7. `aloha/web/src/stores/chat.ts` - 集成 WebSocket
8. `aloha/web/src/views/ChatView.vue` - 使用 WebSocket
9. `aloha/web/src/components/ToolApprovalCard.vue` - 适配新协议

---

## 9. 注意事项

### 9.1 MiniMax Provider 兼容性

`MiniMaxProvider` 对 tool_call_id 有特殊处理：
- `_normalize_tool_call_id()` 将 ID 规范化为 9 位
- `_id_map` 保持同一 ID 在会话中的一致性
- `StreamingReActLoop` 直接使用 `Response.tool_calls` 中的 ID，无需再次规范化

### 9.2 WebSocket 重连

前端应实现自动重连机制：
- 连接断开时自动尝试重连
- 重连成功后重新订阅

### 9.3 错误处理

- 工具执行失败应推送 error 事件
- 连接异常断开应有提示
- 审批被拒绝应有明确反馈
