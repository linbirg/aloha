# AI SDK 工具调用循环机制深度分析

## 一、核心概念

### 1.1 自动工具调用循环

AI SDK 的工具调用循环是**内置的、声明式的**，开发者只需：
1. 定义工具（包含 description、inputSchema、execute）
2. 配置停止条件（stopWhen）
3. 调用 generateText/streamText/agent.generate()

SDK 自动处理：
- 工具调用检测
- 参数验证
- 工具执行
- 结果注入
- 循环判断

---

## 二、两种实现方式

### 2.1 generateText/generateObject 方式

```typescript
import { generateText, tool, stepCountIs, hasToolCall } from 'ai';
import { z } from 'zod';

// 定义工具
const weatherTool = tool({
  description: '获取指定位置的天气',
  inputSchema: z.object({
    location: z.string().describe('要查询的位置'),
  }),
  execute: async ({ location }) => {
    // 实际执行逻辑
    return { temperature: 25, condition: '晴' };
  },
});

// 调用
const result = await generateText({
  model: openai('gpt-4o'),
  tools: { weather: weatherTool },
  stopWhen: stepCountIs(5),  // 最多 5 步
  prompt: '北京天气怎么样？',
});

// result 包含
console.log(result.text);       // 最终文本
console.log(result.steps);      // 所有步骤
console.log(result.toolCalls); // 工具调用历史
```

### 2.2 ToolLoopAgent 方式

```typescript
import { ToolLoopAgent, stepCountIs } from 'ai';

const agent = new ToolLoopAgent({
  model: openai('gpt-4o'),
  tools: { /* 工具定义 */ },
  stopWhen: stepCountIs(20),  // 默认 20 步
});

const result = await agent.generate({
  prompt: '分析数据并生成报告',
});
```

---

## 三、停止条件系统

### 3.1 内置停止条件

```typescript
import { stepCountIs, hasToolCall, stopAtAny, stopAtAll } from 'ai';

// 1. 基于步数
stopWhen: stepCountIs(5)

// 2. 基于工具调用
stopWhen: hasToolCall('finalAnswer')

// 3. 组合条件
stopWhen: stopAtAny([
  stepCountIs(10),
  hasToolCall('finalAnswer')
])
```

### 3.2 步骤对象结构

```typescript
interface Step {
  toolCalls: ToolCall[];      // 本步工具调用
  toolResults: ToolResult[];   // 工具执行结果
  text?: string;             // 本步产生的文本
  finishReason: 'stop' | 'length' | 'tool-calls';
}
```

---

## 四、工作流程详解

### 4.1 单步流程

```
1. generateText() 调用
   ↓
2. 模型生成 → 检测工具调用
   ↓
3. 无工具调用 → 返回 text
   ↓
4. 有工具调用 → 验证参数
   ↓
5. 执行工具 → 获取结果
   ↓
6. 注入结果到消息列表
   ↓
7. 检查 stopWhen 条件
   ↓
8. 条件满足 → 返回结果
   ↓
9. 条件不满足 → 循环到步骤 2
```

### 4.2 消息转换

```typescript
// 内部消息格式转换
// 工具调用 → assistant 消息 + tool 消息
{
  role: 'assistant',
  content: '...',
  toolCalls: [
    { id: 'call_xxx', name: 'weather', input: { location: '北京' } }
  ]
}

// 工具结果 → tool 消息
{
  role: 'tool',
  toolCallId: 'call_xxx',
  content: '{"temperature": 25, "condition": "晴"}'
}
```

---

## 五、Python 实现参考

### 5.1 Pydantic AI 方式

```python
from pydantic_ai import Agent

agent = Agent(
    model='openai:gpt-4o',
    tools=[...],  # 工具列表
)

# 自动循环
result = agent.run_sync('北京天气怎么样？')

# 或者流式
async for chunk in agent.run('北京天气怎么样？'):
    print(chunk)
```

### 5.2 标准 ReAct 实现（如果要自己实现）

```python
class ReActAgent:
    def __init__(
        self,
        model: LLMModel,
        tools: list[Tool],
        max_steps: int = 10
    ):
        self.model = model
        self.tools = {t.name: t for t in tools}
        self.max_steps = max_steps
    
    async def run(self, prompt: str) -> str:
        messages = [Message(role='user', content=prompt)]
        
        for step in range(self.max_steps):
            # 1. 调用模型
            response = await self.model.chat(messages)
            
            # 2. 检查是否有工具调用
            if not response.tool_calls:
                messages.append(response)
                return response.content
            
            # 3. 执行工具
            for tool_call in response.tool_calls:
                tool = self.tools[tool_call.name]
                result = await tool.execute(tool_call.args)
                
                # 4. 添加工具结果
                messages.append(Message(
                    role='tool',
                    tool_call_id=tool_call.id,
                    content=json.dumps(result)
                ))
        
        return "达到最大步数限制"
```

---

## 六、最佳实践

### 6.1 工具定义

```typescript
// ✅ 好的工具定义
const weather = tool({
  description: '获取指定位置的当前天气',
  inputSchema: z.object({
    location: z.string().describe('城市名称，如"北京"'),
  }),
  execute: async ({ location }) => {
    // 实现
    return result;
  },
});

// ❌ 不好的工具定义
const weather = tool({
  inputSchema: z.object({ loc: z.string() }),  // 没有 description
  execute: async ({ loc }) => { ... },
});
```

### 6.2 停止条件选择

| 场景 | 推荐条件 |
|------|----------|
| 简单任务 | stepCountIs(3-5) |
| 复杂任务 | stepCountIs(10-20) |
| 特定工具 | hasToolCall('finalAnswer') |
| 双重保障 | stopAtAny([stepCountIs(20), hasToolCall('finalAnswer')]) |

### 6.3 错误处理

```typescript
try {
  const result = await generateText({
    model: openai('gpt-4o'),
    tools: { ... },
    stopWhen: stepCountIs(10),
    prompt: prompt,
  });
} catch (error) {
  if (error instanceof MaxStepsExceededError) {
    // 处理最大步数超出
  }
  // 其他错误处理
}
```

---

## 七、与手动实现对比

### 7.1 AI SDK 方式 vs 手动实现

| 方面 | AI SDK | 手动实现 |
|------|--------|----------|
| 代码量 | 少（声明式） | 多（流程控制） |
| 错误处理 | 内置 | 需自己实现 |
| 流式支持 | 原生 | 需自己实现 |
| 状态管理 | 自动 | 需自己管理 |
| 定制性 | 中 | 高 |

### 7.2 适用场景

```typescript
// AI SDK 适合：
- 快速开发
- 标准工具调用场景
- 不需要深度定制

// 手动实现适合：
- 需要自定义循环逻辑
- 需要细粒度控制
- 特殊停止条件
- 复杂状态管理
```

---

## 八、总结

AI SDK 的工具调用循环是一个**声明式、自动循环**的系统：

### 核心要素

1. **工具定义**：description + inputSchema + execute
2. **停止条件**：stepCountIs + hasToolCall + 组合
3. **循环机制**：自动检测 → 执行 → 注入 → 判断

### 设计模式

- **声明式**：告诉 SDK 要什么，不是怎么做
- **内置循环**：自动处理步骤迭代
- **状态管理**：steps 数组保存完整历史

### 对 Aloha 的启示

如果要实现类似机制：
1. 抽象出 Tool 定义（description、schema、execute）
2. 实现停止条件系统
3. 构建自动循环逻辑
4. 维护步骤历史状态