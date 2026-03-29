# MiniMax API Function Call 研究

## 1. 问题背景

### 1.1 错误现象
- 错误信息: `invalid params, tool result's tool id(xxx) not found (2013)`
- 触发条件: 工具调用后再次调用 LLM 时
- 原因: MiniMax API 要求 tool_call_id 必须与首次返回的完全匹配

---

## 2. MiniMax 官方文档核心内容

> 文档来源: https://platform.minimaxi.com/docs/guides/text-m2-function-call
> 提取时间: 2025年

### 2.1 MiniMax-M2.7 特性

```
MiniMax-M2.7 是一款 Agentic Model，具备优秀的工具使用 (Tool Use) 能力。

M2.7 原生支持 Interleaved Thinking。它能够在每轮 Tool Use 前，根据环境或工具的返回 (Output) 进行思考，并决策下一步行动。

这种能力使其在长程、复杂任务中表现出色，并在 SWE、BrowseCamp、xBench 等 Code & Agent Benchmark 上达到了 SOTA 水平。
```

### 2.2 核心原则

**回传每一次模型Response的全部信息，尤其是其中的思考字段(thinking/reasoning_details)**

### 2.3 响应参数说明

工具使用响应中的关键字段：
- `thinking/reasoning_details`: 模型的思考（thinking）
- `text/content`: 模型输出的文本
- `tool_calls`: 模型决定调用工具
  - `function.name`: 被调用的工具名称
  - `function.arguments`: 工具调用参数（JSON 格式字符串）
  - `id`: 工具调用的唯一标识符

### 2.4 特别注意（关键！）

```
在多轮 Function Call 对话中，必须将完整的模型返回（即 assistant 消息）添加到对话历史，以保持思维链的连续性：

- OpenAI SDK: 将完整的 response_message 对象（包含 tool_calls 字段）添加到消息历史
- 原生的OpenAI API 的 MiniMax-M2.7 模型 content 字段会包含 <think> 标签内容，需要完整保留
- 在 Interleaved Thinking 友好格式中，通过启用额外的参数( reasoning_split=True )，模型思考内容通过 reasoning_details 字段单独提供，同样需要完整保留
- Anthropic SDK: 将完整的 response.content （包含 thinking/text/tool_use 等所有块）添加到消息历史
```

### 2.5 tool 消息格式（官方示例）

```python
# 3. 执行工具并返回结果
messages.append({
    "role": "tool",
    "tool_call_id": tool_call.id,  # 必须与 tool_calls 中的 id 完全匹配
    "content": "24℃, sunny"  # 实际应用中这里应该调用真实的天气API
})
```

---

## 3. Nanobot 参考实现

### 3.1 ID 规范化方案

Nanobot 在 [`openai_compat_provider.py`](aloha/doc/nanobot/nanobot/providers/openai_compat_provider.py:186) 中实现了 `_normalize_tool_call_id` 方法：

```python
@staticmethod
def _normalize_tool_call_id(tool_call_id: Any) -> Any:
    """Normalize to a provider-safe 9-char alphanumeric form."""
    if not isinstance(tool_call_id, str):
        return tool_call_id
    if len(tool_call_id) == 9 and tool_call_id.isalnum():
        return tool_call_id
    return hashlib.sha1(tool_call_id.encode()).hexdigest()[:9]
```

### 3.2 消息净化

```python
def _sanitize_messages(self, messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Strip non-standard keys, normalize tool_call IDs."""
    sanitized = LLMProvider._sanitize_request_messages(messages, _ALLOWED_MSG_KEYS)
    id_map: dict[str, str] = {}

    def map_id(value: Any) -> Any:
        if not isinstance(value, str):
            return value
        return id_map.setdefault(value, self._normalize_tool_call_id(value))

    for clean in sanitized:
        # 规范化 tool_calls 中的 id
        if isinstance(clean.get("tool_calls"), list):
            normalized = []
            for tc in clean["tool_calls"]:
                tc_clean = dict(tc)
                tc_clean["id"] = map_id(tc_clean.get("id"))
                normalized.append(tc_clean)
            clean["tool_calls"] = normalized
        # 规范化 tool 消息的 tool_call_id
        if "tool_call_id" in clean and clean["tool_call_id"]:
            clean["tool_call_id"] = map_id(clean["tool_call_id"])
    return sanitized
```

**核心思想**:
- 使用 hash 将长/复杂 ID 规范化为统一长度
- 建立 ID 映射表确保同一 ID 在整个会话中保持一致

### 3.3 工具结果消息构建

在 [`runner.py`](aloha/doc/nanobot/nanobot/agent/runner.py:129) 中：
```python
for tool_call, result in zip(response.tool_calls, results):
    messages.append({
        "role": "tool",
        "tool_call_id": tool_call.id,
        "name": tool_call.name,
        "content": str(result),
    })
```

---

## 4. Aloha 现有实现分析

### 4.1 代码结构

```
aloha/
├── agent/
│   ├── loop.py          # ReActLoop 主循环
│   ├── base.py          # Agent 基类
│   └── wrapper.py       # ToolWrapper
├── providers/
│   ├── base.py          # 基类定义
│   │   - Message (role, content, name, tool_call_id)
│   │   - ToolCall (id, name, arguments)
│   │   - Response (content, tool_calls)
│   └── openai_provider.py  # OpenAI 兼容 Provider
└── memory/
    └── session.py        # SessionMemory
```

### 4.2 当前流程 (有问题)

```python
# aloha/agent/loop.py:85-101
async def process(self, user_input: str) -> str:
    while iteration < self.max_iterations:
        # 1. 调用 LLM
        response = await self._call_llm()
        
        # 2. 检查工具调用
        if not response.tool_calls:
            break
            
        # 3. 执行工具
        await self._execute_all_tools(response.tool_calls)
        
        # 4. 临时绕过：直接 break，不再次调用 LLM
        # 问题：再次调用 LLM 会报 tool_call_id 不匹配
        break
```

### 4.3 消息处理

```python
# aloha/memory/session.py:46-59
def get_messages(self) -> list[Message]:
    for m in self.messages:
        msg = Message(
            role=m.role,
            content=m.content,
            tool_call_id=m.metadata.get("tool_call_id") if m.role == "tool" else None,
        )
        if m.role == "tool" and m.metadata.get("tool_name"):
            msg.name = m.metadata["tool_name"]
```

### 4.4 Provider 实现

```python
# aloha/providers/openai_provider.py:42-60
def _convert_message(self, msg: Message) -> dict:
    result = {
        "role": msg.role,
        "content": msg.content,
    }
    if msg.name:
        result["name"] = msg.name
    if msg.tool_call_id:
        result["tool_call_id"] = msg.tool_call_id  # 保持原始值
    return result
```

### 4.5 工具执行与消息添加

```python
# aloha/agent/loop.py:156-161
# 统一添加工具消息到 session
self.session_memory.add_message(
    role="tool",
    content=content,
    metadata={
        "tool_call_id": tool_call.id,
        "tool_name": tool_call.name,
    },
)
```

---

## 5. 差异对比

| 方面 | MiniMax 要求 | Aloha 当前实现 | 状态 |
|------|-------------|----------------|------|
| Tool 定义格式 | 标准 OpenAI tools 数组 | 已实现 | ✅ |
| Tool Call ID | 必须完全匹配 | 保持原始 ID | ⚠️ |
| 二次调用 LLM | 需正确的 tool_call_id | 当前直接 break | ❌ |
| 工具结果消息 | 需包含 tool_call_id, name, content | SessionMemory 已实现 | ✅ |
| 并行工具调用 | 支持 | 支持 | ✅ |
| ID 规范化 | 需确保一致性 | 无规范化 | ❌ |
| 完整 Response 回传 | 必须保留完整 assistant 消息 | 仅保存 content | ❌ |

---

## 6. 重构计划

### 6.1 目标

实现完整的 ReAct 循环，使 MiniMax API 能够正确处理工具调用结果。

### 6.2 方案：Provider 适配器模式

创建 MiniMax 专用适配器，继承现有 OpenAIProvider。

#### 6.2.1 架构设计

```
aloha/providers/
├── base.py                    # 保持不变
├── openai_provider.py          # 基础 Provider
└── minimax_provider.py        # MiniMax 专用适配器 (新增)
```

#### 6.2.2 MiniMaxProvider 类

```python
# aloha/providers/minimax_provider.py
import hashlib
from aloha.providers.openai_provider import OpenAIProvider
from aloha.providers.base import Message, Response, ToolCall
import logging

logger = logging.getLogger(__name__)

class MiniMaxProvider(OpenAIProvider):
    """MiniMax 专用 Provider
    
    特性:
    - 规范化 tool_call_id 确保匹配
    - 支持完整的 ReAct 循环
    """
    
    def __init__(self, api_key, default_model, base_url, ...):
        super().__init__(...)
        self._id_map: dict[str, str] = {}
    
    @staticmethod
    def _normalize_tool_call_id(tool_call_id: str) -> str:
        """规范化 tool_call_id 为固定长度"""
        if not tool_call_id:
            return tool_call_id
        # 已经是 9 位字母数字则保持不变
        if len(tool_call_id) == 9 and tool_call_id.isalnum():
            return tool_call_id
        # 否则 hash 为 9 位
        return hashlib.sha1(tool_call_id.encode()).hexdigest()[:9]
    
    def _get_normalized_id(self, original_id: str) -> str:
        """获取规范化后的 ID，建立映射确保一致性"""
        if original_id not in self._id_map:
            self._id_map[original_id] = self._normalize_tool_call_id(original_id)
        return self._id_map[original_id]
    
    def _convert_message(self, msg: Message) -> dict:
        result = super()._convert_message(msg)
        
        # 规范化 tool 消息的 tool_call_id
        if msg.role == "tool" and msg.tool_call_id:
            result["tool_call_id"] = self._get_normalized_id(msg.tool_call_id)
        
        return result
    
    async def chat_with_tools(self, messages, tools, model):
        # 记录请求中的 tool_call_ids
        normalized_ids = set()
        
        # 规范化请求消息中的 tool_call_id
        for msg in messages:
            if hasattr(msg, 'tool_call_id') and msg.tool_call_id:
                normalized_ids.add(self._get_normalized_id(msg.tool_call_id))
        
        # 调用父类方法
        response = await super().chat_with_tools(messages, tools, model)
        
        # 规范化响应中的 tool_call_id
        if response.tool_calls:
            for tc in response.tool_calls:
                original_id = tc.id
                normalized_id = self._get_normalized_id(original_id)
                tc.id = normalized_id
                logger.debug(f"Normalized tool_call_id: {original_id} -> {normalized_id}")
        
        return response
```

#### 6.2.3 Loop 修改

```python
# aloha/agent/loop.py - 修改 process 方法
async def process(self, user_input: str) -> str:
    # 清空思考日志
    self.thought_logs.clear()
    
    # 添加用户消息
    self.session_memory.add_user_message(user_input)
    
    response = None
    
    for iteration in range(1, self.max_iterations + 1):
        # 构建消息
        messages = self._build_messages()
        
        # 调用 LLM
        response = await self._call_llm(messages)
        
        # 检查是否有工具调用
        if not response.tool_calls:
            # 没有工具调用，直接返回结果
            break
        
        # 有工具调用，执行工具
        logger.LOG_DEBUG(f"[process] Iteration {iteration}/{self.max_iterations}, tool_calls: {[tc.id for tc in response.tool_calls]}")
        await self._execute_all_tools(response.tool_calls)
        
        # 继续循环，再次调用 LLM（处理工具结果）
        # 不再使用 break
    
    if iteration >= self.max_iterations:
        logger.LOG_DEBUG(f"[process] Max iterations ({self.max_iterations}) reached")
    
    return response.content if response else ""
```

### 6.3 详细实施步骤

#### Phase 1: 创建 MiniMaxProvider (1-2 小时)

- [ ] 创建 `aloha/providers/minimax_provider.py`
- [ ] 继承 OpenAIProvider
- [ ] 实现 _normalize_tool_call_id 静态方法
- [ ] 实现 _get_normalized_id 实例方法（维护 ID 映射）
- [ ] 重写 _convert_message 方法
- [ ] 重写 chat_with_tools 方法
- [ ] 单元测试

#### Phase 2: 修改 Loop (1 小时)

- [ ] 修改 `aloha/agent/loop.py`
- [ ] 移除临时 break
- [ ] 添加错误处理
- [ ] 集成测试

#### Phase 3: 完善与优化 (1-2 小时)

- [ ] 支持并行工具调用
- [ ] 错误恢复机制
- [ ] 日志记录
- [ ] 性能优化
- [ ] 端到端测试

### 6.4 任务清单

```
Task 1: MiniMaxProvider 实现
├── 1.1 创建文件 aloha/providers/minimax_provider.py
├── 1.2 实现 tool_call_id 规范化逻辑
├── 1.3 实现 ID 映射维护
├── 1.4 重写消息转换方法
├── 1.5 添加日志
└── 1.6 单元测试

Task 2: Loop 重构
├── 2.1 修改 process 方法移除 break
├── 2.2 添加异常处理
├── 2.3 添加调试日志
└── 2.4 集成测试

Task 3: 完整 ReAct 循环
├── 3.1 并行工具支持
├── 3.2 错误恢复
├── 3.3 性能优化
└── 3.4 端到端测试
```

---

## 7. 预期结果

重构完成后，Aloha 将能够：

1. ✅ 使用 MiniMax API 进行工具调用
2. ✅ 完整的 ReAct 循环（LLM → 工具 → LLM）
3. ✅ 正确的 tool_call_id 匹配
4. ✅ 并行工具调用支持
5. ✅ 错误恢复机制

---

## 8. 风险与注意事项

1. **API 版本差异**: MiniMax 可能随时更新 API，需保持兼容
2. **速率限制**: 注意 API 调用频率限制
3. **错误处理**: 需要处理各种异常情况
4. **测试**: 需要完整的集成测试覆盖
5. **向后兼容**: 确保不破坏其他 Provider 的使用

---

## 9. 测试计划

### 9.1 单元测试

```python
# test_minimax_provider.py
class TestMiniMaxProvider:
    def test_normalize_tool_call_id(self):
        provider = MiniMaxProvider(...)
        
        # 测试 hash 规范化
        assert provider._normalize_tool_call_id("call_very_long_id_12345") == "abc123def"
        
        # 测试保持不变
        assert provider._normalize_tool_call_id("call12345") == "call12345"
    
    def test_id_mapping_consistency(self):
        provider = MiniMaxProvider(...)
        
        # 同一 ID 应返回相同的规范化结果
        id1 = provider._get_normalized_id("call_abc123")
        id2 = provider._get_normalized_id("call_abc123")
        assert id1 == id2
```

### 9.2 集成测试

```python
# test_minimax_react_loop.py
@pytest.mark.integration
async def test_full_react_loop_with_minimax():
    provider = MiniMaxProvider(
        api_key=os.getenv("MINIMAX_API_KEY"),
        base_url="https://api.minimaxi.com/v1",
        default_model="MiniMax-M2.7",
    )
    
    agent = ReActLoop(provider=provider, ...)
    agent.add_tool(ShellTool(allowed_commands=["dir", "ls"]))
    
    # 执行需要工具调用的请求
    response = await agent.process("列出当前目录文件")
    
    # 验证完整 ReAct 循环工作
    assert response