---
title: pi-mono 记忆系统代码实现深度分析
date: 2026-03-30
tags:
  - AI-Agent
  - pi-mono
  - memory
  - 源代码分析
---

# pi-mono 记忆系统代码实现深度分析

## 一、pi-mono 记忆系统概述

pi-mono（现更名为 Superpowers）作为 OpenClaw 的核心基础项目，其"记忆系统"与传统 AI Agent 有本质区别。pi-mono **没有显式的记忆模块**，而是通过**会话管理系统**实现上下文持久化。

### 核心设计理念

| 理念 | 说明 |
|------|------|
| **极简核心** | 不包含复杂记忆机制，通过扩展实现 |
| **会话即存储** | 每个会话是一个 JSONL 文件 |
| **树形结构** | 支持分支和会话分叉 |
| **上下文压缩** | 手动/自动压缩长会话 |

---

## 二、会话存储机制

### 1. 存储格式

参考 [agent-research.md](aloha/doc/agent-research.md:416)：

```typescript
// 会话存储格式
interface SessionEntry {
  id: string;           // 会话 ID
  parentId: string;    // 父会话 ID（用于分支）
  messages: Message[]; // 消息历史
  timestamp: number;    // 时间戳
}
```

**存储位置**: `~/.pi/agent/sessions/`

### 2. 存储特点

| 特性 | 实现 |
|------|------|
| **格式** | JSONL（每行一个 JSON 对象） |
| **结构** | 树形（带 parentId） |
| **自动保存** | 实时写入磁盘 |
| **持久化** | 跨会话保持 |

---

## 三、会话管理功能

### 1. 核心操作

```typescript
// 伪代码实现
class SessionManager {
  // 会话分叉 - 从当前分支创建新会话
  async fork(sessionId: string): Promise<string> {
    const parent = await this.loadSession(sessionId);
    const newSession = {
      id: generateId(),
      parentId: parent.id,  // 指向父会话
      messages: [],
      timestamp: Date.now()
    };
    await this.saveSession(newSession);
    return newSession.id;
  }

  // 分支导航 - 跳转到任意历史点
  async tree(): Promise<SessionTree> {
    // 递归构建会话树
    return this.buildTree(rootSessionId);
  }

  // 上下文压缩 - 压缩长会话
  async compact(sessionId: string): Promise<void> {
    const session = await this.loadSession(sessionId);
    const summary = await this.summarize(session.messages);
    session.messages = [{ role: 'system', content: summary }];
    await this.saveSession(session);
  }
}
```

### 2. 分支导航

```bash
# /tree - 在原地浏览和跳转到任意历史点
# /fork - 从当前分支创建新会话
# /compact - 手动或自动压缩长会话
```

---

## 四、与传统记忆系统的对比

### pi-mono 的"记忆"实现

| 传统记忆系统 | pi-mono 实现 |
|-------------|--------------|
| 短期记忆 | session.messages（内存/磁盘） |
| 长期记忆 | 无（需要扩展实现） |
| 记忆检索 | 通过会话 ID 直接加载 |
| 上下文压缩 | `/compact` 手动压缩 |

### 代码实现位置

pi-mono 的会话管理主要在 `pi-agent-core` 中：

```typescript
// pi-agent-core 中的状态管理
interface AgentState {
  systemPrompt: string;
  model: Model<any>;
  thinkingLevel: ThinkingLevel;
  tools: AgentTool<any>[];
  messages: AgentMessage[];  // 核心：消息列表即"记忆"
  isStreaming: boolean;
  streamMessage: AgentMessage | null;
  pendingToolCalls: Set<string>;
  error?: string;
}
```

---

## 五、扩展实现记忆系统

由于 pi-mono 核心不包含复杂记忆，用户可通过扩展实现。

### 1. 扩展点

```typescript
// 通过扩展添加记忆功能
export default function (pi: ExtensionAPI) {
  // 注册记忆工具
  pi.registerTool({
    name: "remember",
    description: "Save information to memory",
    parameters: Type.Object({ key: Type.String(), value: Type.String() }),
    execute: async (id, params) => {
      await pi.getExtension('memory').set(params.key, params.value);
    }
  });

  // 注册记忆检索工具
  pi.registerTool({
    name: "recall",
    description: "Retrieve information from memory",
    parameters: Type.Object({ key: Type.String() }),
    execute: async (id, params) => {
      return await pi.getExtension('memory').get(params.key);
    }
  });
}
```

### 2. 第三方扩展

rho 项目基于 pi-mono 扩展了完整的记忆系统：

```
rho/brain/
├── brain.jsonl    # 结构化记忆
└── vault/         # Markdown 知识图谱
```

---

## 六、上下文管理机制

### 1. 消息转换流程

```
AgentMessage[] → transformContext() → AgentMessage[] → convertToLlm() → Message[] → LLM
                (optional)                              (required)
```

### 2. transformContext

```typescript
// 上下文剪枝和压缩
transformContext: async (messages, signal) => {
  // 移除旧消息
  // 注入外部上下文
  return pruneOldMessages(messages);
}
```

### 3. convertToLlm

```typescript
// 桥接 AgentMessage 到 LLM Message
convertToLlm: (messages) => {
  // 过滤 UI-only 消息
  // 转换自定义类型
  return messages.filter(m => ['user', 'assistant', 'toolResult'].includes(m.role));
}
```

---

## 七、与 rho 记忆系统对比

| 特性        | pi-mono       | rho                 |
| --------- | ------------- | ------------------- |
| **会话存储**  | JSONL 树形结构    | JSONL + vault       |
| **长期记忆**  | 无（需扩展）        | brain.jsonl + vault |
| **上下文压缩** | 手动/自动         | 定期刷新                |
| **持久化**   | 实时保存          | 每次心跳验证              |
| **扩展机制**  | Extension API | 自定义                 |

### rho 扩展实现

rho 在 pi-mono 基础上添加了：

```python
# rho 的 brain.jsonl 格式
{"type": "identity", "name": "用户", ...}
{"type": "preference", "key": "language", "value": "Python"}
{"type": "task", "name": "当前任务", "status": "进行中"}

# vault 知识图谱
vault/
├── projects/
├── context/
└── history/
```

---

## 八、总结与启示

### pi-mono 记忆系统特点

1. **极简设计** - 核心不包含复杂记忆机制
2. **会话驱动** - 通过会话管理实现上下文持久化
3. **可扩展性** - 通过扩展添加记忆功能
4. **上下文压缩** - 支持手动/自动压缩

### 对 Aloha 的启示

| 借鉴点 | 说明 |
|--------|------|
| **JSONL 存储** | 简单的会话持久化格式 |
| **树形分支** | 支持会话分叉和导航 |
| **上下文压缩** | 定期压缩旧会话 |
| **扩展机制** | 通过扩展添加记忆功能 |

### 推荐实现方案

```
Aloha 记忆系统：
1. 会话记忆 → SessionMemory（内存）
2. 长期记忆 → brain.jsonl（磁盘）
3. 知识图谱 → vault/（Markdown）
4. 上下文压缩 → transformContext hook
```

---

## 九、参考资料

- [pi-mono GitHub](https://github.com/badlogic/pi-mono)
- [pi-agent-core 文档](aloha/doc/agent-research.md:820)
- [会话管理设计](aloha/doc/agent-research.md:416)
