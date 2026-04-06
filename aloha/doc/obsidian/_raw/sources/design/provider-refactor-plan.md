# Provider 重构设计方案

**日期**：2026-04-04
**版本**：v1.0
**状态**：已完成

---

## 1. 概述

### 1.1 重构目标

将 MiniMaxProvider 和 OpenAIProvider 解耦，使：
- `OpenAIProvider` — 纯 OpenAI 兼容实现，不知道 MiniMax 存在
- `MiniMaxProvider` — 只处理 MiniMax 特有逻辑

### 1.2 设计决策

| 项目 | 决策 |
|------|------|
| BaseProvider | **非抽象**，提供默认实现 |
| reasoning_split | **完全移除**，不在 OpenAIProvider 中出现 |
| 向后兼容 | **不需要**，同步修改受影响代码 |
| extract_thinking 返回值 | `str \| None` |

---

## 2. 架构设计

### 2.1 重构前架构

```
BaseProvider (抽象)
    ↑
    │
OpenAIProvider (包含 reasoning_split、reasoning_content 等 MiniMax 逻辑)
    ↑
    │
MiniMaxProvider (添加更多 MiniMax 逻辑)
```

**问题**：
- `OpenAIProvider` 包含 `reasoning_split: bool = False`（MiniMax 专用）
- `OpenAIProvider._convert_message()` 添加 `reasoning_content`（MiniMax 专用）
- 双重添加 `reasoning_content`（OpenAIProvider 第60行 + MiniMaxProvider 第109行）

### 2.2 重构后架构

```
BaseProvider (非抽象基类)
├── convert_message(msg) → dict  (默认实现)
├── extract_thinking(raw_msg) → str | None  (默认返回 None)
└── chat(), chat_with_tools() (抽象方法)
    ↑
    │
OpenAIProvider (BaseProvider 子类)
├── client: AsyncOpenAI
├── convert_message(): 纯 OpenAI 格式（调用 super()）
├── extract_thinking(): 标准 thinking 字段
└── chat(): 纯 OpenAI 逻辑（无 reasoning_split）
    ↑
    │
MiniMaxProvider (OpenAIProvider 子类)
├── _id_map: dict[str, str] = {}  (可重置)
├── _normalize_tool_call_id(): 幂等
├── _get_normalized_id(): 带缓存的规范化
├── reset_id_map(): 幂等
├── convert_message(): + tool_call_id 规范化
├── extract_thinking(): reasoning_content
└── chat(): + reasoning_split via extra_body
```

---

## 3. 核心设计

### 3.1 BaseProvider — 钩子方法

```python
class BaseProvider(ABC):
    def convert_message(self, msg: Message) -> dict[str, Any]:
        """转换 Message 为 API 请求格式（子类可覆盖）"""
        result = {"role": msg.role, "content": msg.content}
        if msg.name:
            result["name"] = msg.name
        if msg.tool_call_id:
            result["tool_call_id"] = msg.tool_call_id
        return result

    def extract_thinking(self, raw_msg) -> str | None:
        """从 API 响应中提取 thinking（子类可覆盖）
        
        默认实现返回 None。
        """
        return None
```

### 3.2 OpenAIProvider — 纯 OpenAI 实现

```python
class OpenAIProvider(BaseProvider):
    def extract_thinking(self, raw_msg) -> str | None:
        """只处理标准 thinking 字段"""
        return getattr(raw_msg, "thinking", None)

    async def chat(self, messages, model=None, ...):
        params = {
            "model": model,
            "messages": [self.convert_message(m) for m in messages],
            ...
        }
        # 无 reasoning_split，无 extra_body
        resp = await self.client.chat.completions.create(**params)
        ...
```

### 3.3 MiniMaxProvider — MiniMax 特有逻辑

```python
class MiniMaxProvider(OpenAIProvider):
    def __init__(self, ...):
        super().__init__(...)
        self._id_map: dict[str, str] = {}

    @staticmethod
    def _normalize_tool_call_id(tool_call_id: str) -> str:
        """幂等：相同输入 → 相同输出"""
        if len(tool_call_id) == 9 and tool_call_id.isalnum():
            return tool_call_id
        return hashlib.sha1(tool_call_id.encode()).hexdigest()[:9]

    def _get_normalized_id(self, original_id: str) -> str:
        """带缓存的规范化"""
        if original_id not in self._id_map:
            self._id_map[original_id] = self._normalize_tool_call_id(original_id)
        return self._id_map[original_id]

    def reset_id_map(self) -> None:
        """幂等操作"""
        self._id_map.clear()

    def convert_message(self, msg: Message) -> dict[str, Any]:
        """转换 + MiniMax 特有处理"""
        result = super().convert_message(msg)

        # tool_call_id 规范化
        if msg.role == "tool" and msg.tool_call_id:
            result["tool_call_id"] = self._get_normalized_id(msg.tool_call_id)

        # assistant tool_calls 规范化
        if msg.role == "assistant" and msg.tool_calls:
            result["tool_calls"] = [
                {
                    "id": self._get_normalized_id(tc.id),
                    "type": "function",
                    "function": {...}
                }
                for tc in msg.tool_calls
            ]

        # reasoning_content
        if msg.thinking:
            result["reasoning_content"] = msg.thinking

        return result

    def extract_thinking(self, raw_msg) -> str | None:
        """提取 reasoning_content"""
        return (
            getattr(raw_msg, "reasoning_content", None) or
            getattr(raw_msg, "reasoning_details", None) or
            getattr(raw_msg, "thinking", None)
        )

    async def chat(self, messages, ...):
        params = {...}

        # MiniMax 特有：reasoning_split
        if not tools:
            params["extra_body"] = {"reasoning_split": True}

        resp = await self.client.chat.completions.create(**params)
        ...
```

---

## 4. 幂等性保证

| 函数 | 幂等性 |
|------|--------|
| `_normalize_tool_call_id()` | ✅ 纯函数，相同输入 → 相同输出 |
| `_get_normalized_id()` | ✅ 有记忆化，但不修改外部状态 |
| `reset_id_map()` | ✅ 多次调用结果相同 |
| `convert_message()` | ✅ 相同消息 → 相同输出 |

---

## 5. 文件变更清单

### 5.1 源代码变更

| 文件 | 操作 | 修改内容 |
|------|------|----------|
| `aloha/providers/base.py` | 修改 | 非抽象化，添加 `convert_message()` 和 `extract_thinking()` 默认实现 |
| `aloha/providers/openai_provider.py` | 重写 | 移除 `reasoning_split`，移除 `reasoning_content` 处理 |
| `aloha/providers/minimax_provider.py` | 重写 | 覆盖钩子方法，添加 MiniMax 特有逻辑 |

### 5.2 测试文件变更

| 文件 | 操作 | 说明 |
|------|------|------|
| `aloha/test/providers/__init__.py` | 新增 | 包初始化 |
| `aloha/test/providers/test_base_provider.py` | 新增 | BaseProvider 默认实现测试 (11 tests) |
| `aloha/test/providers/test_openai_provider.py` | 新增 | OpenAIProvider 纯逻辑测试 (17 tests) |
| `aloha/test/providers/test_minimax_provider.py` | 新增 | MiniMaxProvider 特有逻辑测试 (26 tests) |
| `aloha/test/test_agent.py` | 修改 | MockProvider 适配新结构 |
| `aloha/test/test_minimax_provider.py` | 修改 | `_convert_message` → `convert_message` |

---

## 6. 测试结果

```
73 passed, 1 skipped (integration tests require API keys)
```

### 测试覆盖

| 测试类 | 测试数 | 覆盖内容 |
|--------|--------|----------|
| TestBaseProviderConvertMessage | 6 | 默认消息转换 |
| TestBaseProviderExtractThinking | 2 | 默认 thinking 提取 |
| TestOpenAIProviderSeparation | 4 | OpenAI/MiniMax 分离验证 |
| TestOpenAIProviderChat | 2 | reasoning_split 不存在 |
| TestMiniMaxProviderIdNormalization | 6 | ID 规范化、幂等性 |
| TestMiniMaxProviderIdMapping | 4 | ID 映射一致性 |
| TestMiniMaxProviderConvertMessage | 6 | MiniMax 特有转换 |
| TestMiniMaxProviderExtractThinking | 6 | reasoning_content 提取 |
| TestMiniMaxProviderChat | 2 | reasoning_split 发送逻辑 |
| TestMiniMaxProviderSeparation | 4 | MiniMax 特有属性 |
| TestMiniMaxProviderIdempotency | 2 | 幂等性保证 |

---

## 7. 分离验证

### 7.1 OpenAIProvider 不包含 MiniMax 逻辑

```python
provider = OpenAIProvider(api_key="test-key")
assert not hasattr(provider, "reasoning_split")  # ✅
assert not hasattr(provider, "_id_map")  # ✅
assert not hasattr(provider, "_normalize_tool_call_id")  # ✅
```

### 7.2 MiniMaxProvider 包含特有逻辑

```python
provider = MiniMaxProvider(api_key="test-key")
assert hasattr(provider, "_id_map")  # ✅
assert hasattr(provider, "_normalize_tool_call_id")  # ✅
assert hasattr(provider, "reset_id_map")  # ✅
```

---

## 8. 执行记录

1. ✅ 修改 `base.py` — 非抽象化，添加钩子方法
2. ✅ 重写 `openai_provider.py` — 移除 MiniMax 逻辑
3. ✅ 重写 `minimax_provider.py` — 覆盖钩子方法
4. ✅ 创建测试文件
5. ✅ 更新 `test_agent.py` 的 MockProvider
6. ✅ 运行测试验证

---

## 9. 受影响的旧测试修复

| 测试文件 | 问题 | 修复 |
|----------|------|------|
| `test_minimax_provider.py` | 使用 `_convert_message` | 改为 `convert_message` |
