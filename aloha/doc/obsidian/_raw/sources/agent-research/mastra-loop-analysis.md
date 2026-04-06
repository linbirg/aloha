# Mastra Agent 核心循环实现分析

## 一、核心循环架构

### 1.1 循环入口函数

**文件**: `packages/core/src/loop/loop.ts`

```typescript
export function loop<Tools extends ToolSet = ToolSet, OUTPUT = undefined>({
  resumeContext,
  models,
  logger,
  runId,
  idGenerator,
  messageList,
  includeRawChunks,
  modelSettings,
  tools,
  _internal,
  outputProcessors,
  returnScorerData,
  requireToolApproval,
  agentId,
  toolCallConcurrency,
  ...rest
}: LoopOptions<Tools, OUTPUT>)
```

**核心特性**:
- 接收 `models` 数组（支持多模型路由）
- 接收 `tools` 工具集
- 支持 `resumeContext` 恢复执行
- 返回流式输出

### 1.2 循环实现流程

```typescript
// 1. 验证模型
if (models.length === 0 || !models[0]) {
  throw new MastraError({...})
}

// 2. 创建内部上下文
const internalToUse: StreamInternal = {
  now: _internal?.now || (() => Date.now()),
  generateId: _internal?.generateId || (() => generateId()),
  memory: _internal?.memory,
  threadId: _internal?.threadId,
  // ...
}

// 3. 构建工作流属性
const workflowLoopProps: LoopRun<Tools, OUTPUT> = {
  resumeContext,
  models,
  runId: runIdToUse,
  messageList,
  tools,
  modelSettings,
  // ...
}

// 4. 创建工作流流
const baseStream = workflowLoopStream(workflowLoopProps)

// 5. 应用追踪转换
const stream = rest.modelSpanTracker?.wrapStream(baseStream) ?? baseStream

// 6. 创建模型输出
modelOutput = new MastraModelOutput({
  model: { ... },
  stream,
  messageList,
  // ...
})

// 7. 返回可解构输出
return createDestructurableOutput(modelOutput)
```

---

## 二、流式逻辑实现

### 2.1 流式架构

Mastra 采用**完全流式**设计：

```
LLM Stream → ModelOutput → DestructurableOutput
                ↓
         [text, object, function calls]
```

### 2.2 流式组件

| 组件                           | 位置                         | 职责       |
| ---------------------------- | -------------------------- | -------- |
| `workflowLoopStream`         | `loop/workflows/stream.ts` | 核心工作流循环流 |
| `MastraModelOutput`          | `stream/base/output.ts`    | 模型输出封装   |
| `createDestructurableOutput` | `stream/base/output.ts`    | 返回可消费输出  |

### 2.3 流式输出类型

从测试文件可以看出支持多种流式输出：

```typescript
// 测试用例
textStreamTests()      // 文本流
fullStreamTests()      // 完整流（含工具调用）
streamObjectTests()    // 对象流
resultObjectTests()   // 结果对象
```

### 2.4 工具调用循环

```typescript
// 核心标志：
- toolCallStreaming    // 工具调用流式处理
- toolCallConcurrency   // 工具调用并发控制
- requireToolApproval  // 需要工具批准
```

---

## 三、ReAct 模式实现

### 3.1 循环终止条件

基于 AI SDK v4/v5/v6 的内置循环机制：

```typescript
// AI SDK 的 generateText/generateObject 自动处理：
// 1. 模型产生文本 → 返回
// 2. 模型产生工具调用 → 执行工具 → 循环
// 3. 模型产生 stop → 返回
```

### 3.2 消息列表管理

```typescript
// packages/core/src/agent/message-list/
messageList: MessageList  // 管理对话历史
```

**消息列表功能**:
- 消息格式转换
- 消息合并
- 状态跟踪
- 流式输出适配

---

## 四、与 Aloha 对比

### 4.1 架构差异

| 特性   | Mastra    | Aloha         |
| ---- | --------- | ------------- |
| 循环引擎 | AI SDK 内置 | 自定义 ReActLoop |
| 流式处理 | 原生流式      | 手动流式          |
| 工具调用 | 自动循环      | 手动执行          |
| 模型支持 | 多模型路由     | 单模型           |

### 4.2 代码风格

```typescript
// Mastra - 流式优先
const result = await agent.run({ messages: [...] })
// 返回值已经是流式结果

// Aloha - 分步执行
const response = await self._call_llm(messages)
if tool_calls:
    await self._execute_tools(tool_calls)
```

---

## 五、关键设计决策

### 5.1 依赖 AI SDK

Mastra 依赖 Vercel AI SDK 处理核心循环，这意味着：
- ✅ 自动工具调用循环
- ✅ 流式输出内置
- ✅ 多模型支持
- ❌ 定制化受限

### 5.2 可观测性集成

```typescript
// 内置追踪
modelSpanTracker?.wrapStream(baseStream)

// 可观测性上下文
const observabilityContext = createObservabilityContext(
  rest.modelSpanTracker?.getTracingContext()
)
```

### 5.3 状态序列化

```typescript
// 支持暂停/恢复
serializeStreamState()
deserializeStreamState(state)
```

---

## 六、总结

### Mastra 循环特点

1. **完全流式** - 基于 AI SDK 的原生流式处理
2. **声明式** - 通过配置声明工具和模型
3. **自动循环** - AI SDK 自动处理工具调用循环
4. **可恢复** - 支持暂停和恢复执行
5. **多模型** - 内置模型路由支持

### 对比 Hermes

| 特性   | Mastra    | Hermes   |
| ---- | --------- | -------- |
| 循环方式 | AI SDK 自动 | 手动 ReAct |
| 流式   | 原生        | 手动实现     |
| 工具调用 | 自动        | 手动       |
| 复杂度  | 低         | 高        |
| 定制性  | 中         | 高        |

### 启示

Mastra 的设计哲学是"少做多"：
- 依赖成熟的 AI SDK 处理核心逻辑
- 专注于应用层功能（工作流、记忆、部署）
- 适合快速构建应用，不太适合深度定制