---
title: pi-mono 会话管理系统深度分析
date: 2026-03-30
tags:
  - AI-Agent
  - pi-mono
  - session
  - 会话管理
---

# pi-mono 会话管理系统深度分析

## 一、pi-mono 会话管理概述

pi-mono（现 Superpowers）的会话管理系统是其核心特色之一，采用**JSONL 树形结构**存储会话，支持会话分叉和分支导航。

### 核心特性

| 特性 | 说明 |
|------|------|
| **存储格式** | JSONL（每行一个消息对象） |
| **结构** | 树形（带 parentId） |
| **位置** | `~/.pi/agent/sessions/` |
| **自动保存** | 实时写入磁盘 |

---

## 二、会话存储格式

### 1. JSONL 结构

参考 [agent-research.md](aloha/doc/agent-research.md:417)：

```typescript
// 每个会话条目
interface SessionEntry {
  id: string;           // 会话唯一标识
  parentId: string;    // 父会话 ID（支持分支）
  messages: Message[]; // 消息历史
  timestamp: number;   // 创建时间戳
}

// 示例 JSONL 文件
{"id": "s001", "parentId": null, "messages": [...], "timestamp": 1700000000}
{"id": "s002", "parentId": "s001", "messages": [...], "timestamp": 1700000100}
{"id": "s003", "parentId": "s001", "messages": [...], "timestamp": 1700000200}  // 分支
```

### 2. 会话树形结构

```
s001 (root)
├── s002 (branch A)
│   ├── s004 (sub-branch)
│   └── s005 (sub-branch)
└── s003 (branch B)
```

---

## 三、会话管理功能

### 1. 核心操作

| 命令 | 功能 |
|------|------|
| `/tree` | 浏览和跳转到任意历史点 |
| `/fork` | 从当前分支创建新会话 |
| `/compact` | 手动/自动压缩长会话 |

### 2. 分叉（FORK）机制

```typescript
// 伪代码实现
async fork(currentSessionId: string): Promise<string> {
  // 1. 加载当前会话
  const current = await loadSession(currentSessionId);
  
  // 2. 创建新会话，继承父 ID
  const forked = {
    id: generateUUID(),
    parentId: current.id,  // 指向当前会话
    messages: [...current.messages],  // 复制消息历史
    timestamp: Date.now()
  };
  
  // 3. 保存到磁盘
  await saveSession(forked);
  
  return forked.id;
}
```

### 3. 分支导航（TREE）机制

```typescript
// 构建会话树
async buildTree(rootId: string): Promise<SessionTree> {
  const allSessions = await loadAllSessions();
  
  // 构建树形结构
  const tree = new Map<string, SessionNode>();
  
  for (const session of allSessions) {
    const node = {
      id: session.id,
      messages: session.messages,
      children: []
    };
    tree.set(session.id, node);
  }
  
  // 建立父子关系
  for (const session of allSessions) {
    if (session.parentId) {
      const parent = tree.get(session.parentId);
      parent?.children.push(tree.get(session.id));
    }
  }
  
  return tree.get(rootId);
}
```

### 4. 上下文压缩（COMPACT）

```typescript
// 压缩长会话
async compact(sessionId: string): Promise<void> {
  const session = await loadSession(sessionId);
  
  // 生成摘要
  const summary = await summarizeMessages(session.messages);
  
  // 替换为摘要消息
  session.messages = [{
    role: 'system',
    content: `Session Summary: ${summary}`
  }];
  
  await saveSession(session);
}
```

---

## 四、NanoBot 会话管理对比

### NanoBot 会话实现

参考 [agent-research.md](aloha/doc/agent-research.md:1867)：

```python
# NanoBot 的会话管理
class AgentLoop:
    def __init__(self, bus, provider, workspace, ...):
        self.sessions = session_manager or SessionManager(workspace)
```

### 会话管理类

```python
class SessionManager:
    """会话管理器"""
    
    def create_session(self, session_id: str, config: dict) -> Session:
        """创建新会话"""
        
    def get_session(self, session_id: str) -> Session:
        """获取会话"""
        
    def list_sessions(self) -> list[Session]:
        """列出所有会话"""
        
    def delete_session(self, session_id: str):
        """删除会话"""
```

### NanoBot 会话特点

| 特性 | NanoBot | pi-mono |
|------|---------|---------|
| **存储** | 内存 + SQLite | JSONL 文件 |
| **分支** | 不支持 | 支持 parentId |
| **压缩** | 无 | /compact |
| **持久化** | 可选 | 实时保存 |

---

## 五、Aloha 会话管理

### 当前实现

参考 [session-management-design.md](aloha/doc/design/session-management-design.md:1)：

```python
# Aloha 的会话设计
class Session:
    id: str                    # UUID
    name: str
    created_at: datetime
    updated_at: datetime
    status: SessionStatus      # active, paused, archived
    config_override: dict
    template: str
    path: Path                 # Session 目录
```

### 目录结构

```
~/.aloha/
├── sessions/
│   ├── global/               # 全局默认配置
│   │   ├── agent.md
│   │   └── skills.toml
│   ├── {uuid-session-id}/   # Session 目录
│   │   ├── metadata.json
│   │   ├── memory.md        # 会话记忆
│   │   └── history.md       # 对话历史
│   └── ...
├── sessions.db               # SQLite
└── config.toml
```

### Aloha 会话特点

| 特性 | Aloha |
|------|-------|
| **存储** | SQLite + 文件系统 |
| **分支** | 不支持 |
| **压缩** | 无 |
| **隔离** | 运行时隔离 |

---

## 六、三方对比

### 特性对比表

| 特性 | pi-mono | NanoBot | Aloha |
|------|---------|---------|-------|
| **存储格式** | JSONL | SQLite + 内存 | SQLite + 文件 |
| **树形分支** | ✅ parentId | ❌ | ❌ |
| **会话分叉** | ✅ /fork | ❌ | ❌ |
| **上下文压缩** | ✅ /compact | ❌ | ❌ |
| **实时保存** | ✅ | ❌ | ❌ |
| **Session 隔离** | ❌ | ⚠️ 可选 | ✅ |
| **历史持久化** | ✅ | ⚠️ 可选 | ✅ |

### 架构差异图

```
pi-mono:
  session (JSONL) ←→ file system
       ↑
    parentId (树形)
       
NanoBot:
  session (SQLite) ←→ memory
       ↑
    SessionManager

Aloha:
  session (SQLite + 目录) ←→ 独立 Agent 实例
       ↑
    SessionManager (隔离运行)
```

---

## 七、关键代码分析

### 1. pi-mono 消息流

```typescript
// pi-agent-core 中的消息处理
interface AgentState {
  messages: AgentMessage[];  // 核心：消息列表即会话
}

// 消息转换流程
AgentMessage[] 
  → transformContext()     // 剪枝、压缩
  → convertToLlm()         // 过滤自定义消息
  → Message[]              // LLM 可理解格式
  → LLM API
```

### 2. NanoBot 会话流

```python
# nanobot 的 AgentLoop
class AgentLoop:
    def __init__(self, bus, provider, workspace, ...):
        self.sessions = SessionManager(workspace)
    
    def run(self):
        # 1. 从 bus 接收消息
        # 2. 构建上下文（历史 + 内存 + skills）
        # 3. 调用 LLM
        # 4. 执行工具
        # 5. 发送响应
```

### 3. Aloha 会话流

```python
# aloha 的 Session 管理
class Session:
    def get_memory(self) -> SessionMemory:
        """获取会话记忆"""
    
    def get_history(self) -> list[Message]:
        """获取对话历史"""
```

---

## 八、结论与建议

### pi-mono 会话系统优势

1. **简单高效** - JSONL 格式简单易读
2. **分支强大** - 树形结构支持任意分支导航
3. **持久可靠** - 实时保存到磁盘
4. **压缩灵活** - 支持上下文压缩

### 对 Aloha 的建议

| 功能 | 优先级 | 说明 |
|------|--------|------|
| **JSONL 存储** | 中 | 可选的文件格式 |
| **分支导航** | 低 | 复杂度较高 |
| **上下文压缩** | 高 | transformContext hook |
| **实时保存** | 中 | 可考虑增量保存 |

### 推荐的 Aloha 会话架构

```python
class SessionManager:
    def __init__(self, base_path):
        # SQLite: 索引和元数据
        # 文件系统: history.md, memory.md
        # 内存: 当前会话消息
    
    def create_session(self) -> Session:
        # 创建 UUID 目录
        # 初始化 metadata.json
        # 返回 Session 对象
    
    def save_session(self, session):
        # 增量写入 history.md
        # 定期压缩
    
    def fork_session(self, session_id) -> Session:
        # 复制消息历史
        # 设置 parent_id
```

---

## 九、参考资料

- [pi-mono 会话管理](aloha/doc/agent-research.md:416)
- [Aloha Session 设计](aloha/doc/design/session-management-design.md:1)
- [NanoBot AgentLoop](aloha/doc/agent-research.md:1867)
