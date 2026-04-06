# Mastra 开源 Agent 项目分析

## 一、项目概述

### 1.1 基本信息

| 属性 | 值 |
|------|-----|
| **名称** | Mastra |
| **Stars** | 22,494 |
| **Fork** | 1,816 |
| **语言** | TypeScript |
| **团队** | Gatsby 团队背后 |

### 1.2 官方定义

> "Mastra is a framework for building AI-powered applications and agents with a modern TypeScript stack."
> 
> 从原型到生产的完整 AI 应用框架，集成 React、Next.js、Node.js，支持独立部署。

---

## 二、核心特性

### 2.1 主要功能模块

| 模块                     | 说明                                           |
| ---------------------- | -------------------------------------------- |
| **Model Routing**      | 40+ 供应商通过统一接口连接 (OpenAI, Anthropic, Gemini等) |
| **Agents**             | 自主 Agent，使用 LLM 和工具解决开放任务                    |
| **Workflows**          | 图工作流引擎，编排复杂多步骤流程                             |
| **Human-in-the-loop**  | 暂停等待用户输入或批准                                  |
| **Context Management** | 对话历史、数据检索、工作记忆、语义召回                          |
| **MCP Servers**        | Model Context Protocol 服务器                   |
| **Evals**              | 内置评估                                         |
| **Observability**      | 可观测性                                         |

### 2.2 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                      Mastra Core                             │
├─────────────────────────────────────────────────────────────┤
│  Agent     │  Workflows   │  Memory   │  Storage  │  LLM   │
│  (Agent)   │  (Graph)     │  (Memory) │  (SQLite) │  (LLM) │
├─────────────────────────────────────────────────────────────┤
│  Tools     │  MCP        │  RAG      │  Evals    │  Voice │
└─────────────────────────────────────────────────────────────┘
```

---

## 三、核心组件详解

### 3.1 Agent 系统

**文件位置**: `packages/core/src/agent/agent.ts` (196KB)

```typescript
// 核心 Agent 类
export class Agent {
  // 消息处理
  async run(input: RunInput): Promise<RunOutput>
  
  // 流式处理
  async stream(input: StreamInput): Promise<StreamResult>
  async streamLegacy(...): Promise<StreamResult>
  
  // 工具执行
  async executeTool(...): Promise<ToolResult>
}
```

**Agent 特性**:
- 支持 ReAct 模式
- 工具循环执行
- 跟踪和观测能力
- 可配置模型路由

### 3.2 Memory 系统

**文件位置**: `packages/memory/src/index.ts`

```typescript
export class Memory extends MastraMemory {
  // 工作记忆 (Working Memory)
  workingMemory: {
    enabled: boolean;
    template: WorkingMemoryTemplate;
  }
  
  // 观测记忆 (Observational Memory)
  observationalMemory: {
    model: string;
    observation: boolean;
    reflection: boolean;
    retrieval?: {
      vector?: boolean;
      scope?: 'thread' | 'resource';
    }
  }
  
  // 语义召回 (Semantic Recall)
  semanticRecall: {
    threshold?: number;
    scope?: 'thread' | 'resource';
  }
}
```

**记忆类型**:

| 类型                       | 说明                  |
| ------------------------ | ------------------- |
| **Working Memory**       | 工作记忆，LLM 当前可用的活跃上下文 |
| **Observational Memory** | 观测记忆，主动观察用户行为并从中学习  |
| **Semantic Recall**      | 语义召回，基于向量相似度检索历史    |
| **Conversation History** | 对话历史，会话级消息存储        |

### 3.3 Storage 系统

```typescript
// 支持的存储后端
type StorageBackend = 'sqlite' | 'postgres' | 'mysql' | 'cloudflare-d1'

// 存储接口
interface MemoryStorage {
  // 线程管理
  createThread(thread: ThreadInput): Promise<Thread>
  getThreadById(threadId: string): Promise<Thread>
  listThreads(): Promise<Thread[]>
  
  // 消息管理
  createMessage(message: MessageInput): Promise<Message>
  listMessages(threadId: string): Promise<Message[]>
  
  // 向量搜索
  semanticSearch(query: string): Promise<MemoryResult[]>
}
```

### 3.4 Workflows 系统

```typescript
// 工作流构建
const workflow = createWorkflow()
  .then(step1)
  .branch(condition, thenBranch, elseBranch)
  .parallel(stepA, stepB)

// 暂停/恢复
await workflow.suspend()
const result = await workflow.resume()
```

### 3.5 MCP 集成

```typescript
// MCP 服务器创建
import { createMcpServer } from '@mastra/mcp'

const server = createMcpServer({
  name: 'my-server',
  tools: {
    myTool: () => ({ result: 'hello' })
  }
})
```

---

## 四、与 Hermes 对比

### 4.1 特性对比

| 特性        | Mastra      | Hermes         | pi-mono    | Aloha  |
| --------- | ----------- | -------------- | ---------- | ------ |
| **语言**    | TypeScript  | Python         | TypeScript | Python |
| **Stars** | 22.5k       | 18.7k          | 28k        | -      |
| **框架类型**  | 全栈框架        | Agent          | Agent      | Agent  |
| **存储**    | SQLite + 向量 | SQLite + JSONL | JSONL      | 内存     |
| **记忆系统**  | 4种类型        | 3层             | 基础         | 基础     |
| **用户建模**  | 无           | Honcho         | 无          | 无      |
| **工作流**   | 图引擎         | 无              | 无          | 无      |
| **MCP**   | ✅           | ✅              | 部分         | 无      |
| **Evals** | ✅           | 部分             | 无          | 无      |

### 4.2 记忆系统对比

| 特性                   | Mastra | Hermes |
| -------------------- | ------ | ------ |
| Working Memory       | ✅      | 无      |
| Observational Memory | ✅      | 无      |
| Semantic Recall      | ✅      | FTS5   |
| Conversation History | ✅      | ✅      |

---

## 五、代码架构分析

### 5.1 包结构

```
packages/
├── core/              # 核心框架
│   └── src/
│       ├── agent/    # Agent 实现
│       ├── memory/   # 记忆核心
│       ├── storage/  # 存储抽象
│       ├── llm/      # LLM 提供商
│       └── workflows/
├── memory/            # 记忆扩展
├── mcp/               # MCP 服务器
├── rag/               # RAG 实现
├── evals/             # 评估系统
└── voice/             # 语音集成
```

### 5.2 核心设计模式

1. **依赖注入 (DI)**
   ```typescript
   // 通过容器注入依赖
   const agent = new Agent({
     llm: openai('gpt-4'),
     storage: new SQLiteStorage(),
     memory: new Memory({ vector: pinecone() })
   })
   ```

2. **流式处理 (Streaming)**
   ```typescript
   // 支持多种流式输出
   const stream = await agent.stream({
     messages: [{ role: 'user', content: 'Hello' }]
   })
   ```

3. **处理器模式 (Processors)**
   ```typescript
   // 输入/输出处理器
   const agent = new Agent({
     inputProcessor: customInputProcessor,
     outputProcessor: customOutputProcessor
   })
   ```

---

## 六、部署与扩展

### 6.1 部署方式

```typescript
// 1. 独立服务器
const server = mastra.createServer()
server.listen(3000)

// 2. Next.js 集成
// 使用 @mastra/next 集成到 Next.js

// 3. Node.js 集成
// 使用 @mastra/node 集成到 Node.js

// 4. 边缘部署
// Cloudflare Workers, Vercel Edge
```

### 6.2 可扩展性

- **存储后端**: SQLite, PostgreSQL, MySQL, Cloudflare D1
- **向量存储**: Pinecone, Qdrant, Cloudflare Vectorize
- **LLM 提供商**: 40+ 供应商统一接口

---

## 七、优缺点分析

### 7.1 优点

1. **完整堆栈** - 从原型到生产一站式
2. **TypeScript** - 强类型，现代开发体验
3. **工作流** - 强大的流程控制能力
4. **可观测性** - 内置 Evals + 观测
5. **MCP 支持** - 标准化工具协议
6. **多平台部署** - 前端/后端/边缘

### 7.2 缺点

1. **无用户建模** - 缺少类似 Honcho 的功能
2. **Python 缺失** - 仅 TypeScript
3. **复杂性** - 功能多，学习曲线陡峭
4. **企业版限制** - 核心功能需许可

---

## 八、对 Aloha 的启示

### 8.1 可借鉴设计

1. **处理器模式** - 输入/输出处理器抽象
2. **存储接口** - 统一的存储后端抽象
3. **工作流引擎** - 图结构流程控制

### 8.2 技术选型建议

| 场景 | 推荐 |
|------|------|
| TypeScript 项目 | Mastra |
| Python 项目 | Hermes/pi-mono |
| 需要用户建模 | Hermes |
| 需要工作流 | Mastra |
| 简单 Agent | pi-mono/Aloha |

---

## 九、总结

Mastra 是一个**全栈型 AI 应用框架**，由 Gatsby 团队打造，特点是：
- 完整的开发生态（从原型到生产）
- 强大的工作流引擎
- 多层次的记忆系统
- 丰富的集成选项（40+ LLM 供应商）

与 Hermes 相比，Mastra 更偏向应用框架，Hermes 更偏向 Agent 能力。两者代表不同的设计哲学：
- **Mastra**: " Everything for AI apps"
- **Hermes**: "Self-improving Agent"
