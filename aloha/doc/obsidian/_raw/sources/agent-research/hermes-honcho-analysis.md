# Hermes Agent Honcho 用户建模系统分析

## 一、Honcho 概述

### 1.1 官方定义

> Honcho: 官方 DX 优化的 Python SDK for Honcho
> 
> "conversational memory platform" - 对话记忆平台
> 
> 提供多party交互中管理peers、sessions和对话上下文的工具，使高级对话AI应用具有持久记忆和"心理理论"(theory-of-mind)能力。

### 1.2 在 Hermes 中的角色

Hermes 将 Honcho 集成作为**用户建模**的核心组件：
- 追踪用户偏好、行为模式
- 维护用户"画像"(Personas)
- 提供 AI 心理理论支持

---

## 二、代码架构分析

### 2.1 核心数据结构

```python
@dataclass
class HonchoSession:
    """由 Honcho 支持的会话"""
    key: str                    # channel:chat_id
    user_peer_id: str           # Honcho peer ID for the user
    assistant_peer_id: str      # Honcho peer ID for the assistant
    honcho_session_id: str      # Honcho session ID
    messages: list[dict[str, Any]]  # 本地消息缓存
    created_at: datetime
    updated_at: datetime
    metadata: dict[str, Any]
```

### 2.2 会话管理器

```python
class HonchoSessionManager:
    """
    管理使用 Honcho 的会话
    """
    def __init__(
        self,
        honcho: Honcho | None = None,
        context_tokens: int | None = None,
        config: Any | None = None,
    ):
        self._honcho = honcho
        self._context_tokens = context_tokens
        self._cache: dict[str, HonchoSession] = {}
        self._peers_cache: dict[str, Any] = {}
        self._sessions_cache: dict[str, Any] = {}
```

### 2.3 核心功能

| 方法                        | 功能              |
| ------------------------- | --------------- |
| `add_message()`           | 添加消息到本地缓存       |
| `get_history()`           | 获取 LLM 上下文的历史消息 |
| `create_session()`        | 创建新会话           |
| `create_or_get_peer()`    | 获取或创建用户/助手peer  |
| `seed_ai_identity()`      | 从文本内容播种AI身份     |
| `get_ai_representation()` | 获取AI的当前表征       |

---

## 三、关键实现逻辑

### 3.1 消息缓存与同步

```python
def add_message(self, role: str, content: str, **kwargs) -> None:
    """添加消息到本地缓存"""
    msg = {
        "role": role,
        "content": content,
        "timestamp": datetime.now().isoformat(),
        **kwargs,
    }
    self.messages.append(msg)
    self.updated_at = datetime.now()
```

**设计特点**：
- 本地缓存 + 异步写入 Honcho 云端
- 支持配置写入频率 (`write_frequency`)

### 3.2 创建会话流程

```python
async def create_session(
    self,
    session_key: str,
    user_id: str,
    assistant_id: str = "hermes",
) -> HonchoSession:
    """创建新会话"""
    # 1. 获取或创建 user peer
    user_peer = await self._create_or_get_peer(user_id, "user")
    
    # 2. 获取或创建 assistant peer
    assistant_peer = await self._create_or_get_peer(assistant_id, "assistant")
    
    # 3. 在 Honcho 云端创建会话
    honcho_session = self._honcho.sessions.create(
        peer_ids=[user_peer.id, assistant_peer.id],
    )
    
    # 4. 返回本地会话对象
    return HonchoSession(...)
```

### 3.3 用户建模机制

**AI 身份播种 (Seed AI Identity)**:
```python
def seed_ai_identity(
    self,
    session_key: str,
    content: str,
    source: str = "manual"
) -> bool:
    """从文本内容播种AI的Honcho表征"""
    wrapped = f"""<ai_identity_seed>
<source>{source}</source>

{content.strip()}
</ai_identity_seed>"""
    honcho_session.add_messages([assistant_peer.message(wrapped)])
    return True
```

**获取用户表征**:
```python
def get_ai_representation(self, session_key: str) -> dict[str, str]:
    """获取AI的当前Honcho表征"""
    session = self._cache.get(session_key)
    honcho_session = self._sessions_cache.get(session.honcho_session_id)
    
    ctx = honcho_session.context(
        summary=False,
        tokens=self._context_tokens,
        peer_target=session.assistant_peer_id,
        peer_perspective=session.user_peer_id,
    )
    
    return {
        "representation": ctx.peer_representation or "",
        "card": "\n".join(ctx.peer_card) if isinstance(ctx.peer_card, list) else str(ctx.peer_card),
    }
```

---

## 四、配置系统

### 4.1 多层级配置

```python
# 优先级：本地实例 > 全局 > 环境变量
1. $HERMES_HOME/honcho.json     # 实例本地
2. ~/.honcho/config.json        # 全局
3. 环境变量 (HONCHO_API_KEY, HONCHO_ENVIRONMENT)
```

### 4.2 配置字段

```python
@dataclass
class HonchoClientConfig:
    host: str = "hermes"
    workspace_id: str = "hermes"
    api_key: str | None = None
    environment: str = "production"
    base_url: str | None = None  # 自托管 URL
    
    # 身份配置
    peer_name: str | None = None
    ai_peer: str = "hermes"
    
    # 记忆配置
    enabled: bool = False
    save_messages: bool = True
    memory_mode: str = "hybrid"  # hybrid / honcho / hybrid
```

### 4.3 记忆模式

```python
# memory_mode 解析
VALID_RECALL_MODES = {"hybrid", "context", "tools"}

def _resolve_memory_mode(...):
    # 字符串形式: "hybrid" → {"default": "hybrid"}
    # 对象形式: {"default": "hybrid", "hermes": "honcho"}
```

| 模式        | 说明               |
| --------- | ---------------- |
| `hybrid`  | 本地缓存 + Honcho 云端 |
| `honcho`  | 仅使用 Honcho       |
| `context` | 上下文记忆            |

---

## 五、与其他记忆系统的协作

### 5.1 记忆系统分层

```
┌─────────────────────────────────────────────┐
│           Agent Context                     │
│  (最终输入给 LLM 的完整上下文)                │
├─────────────────────────────────────────────┤
│         ContextCompressor                   │
│          (上下文压缩)                        │
├─────────────────────────────────────────────┤
│     Honcho (用户建模)                        │
│  - 用户画像 (Persona)                        │
│  - 心理理论 (Theory of Mind)                 │
├─────────────────────────────────────────────┤
│       SessionDB + FTS5                      │
│   (SQLite 持久化 + 全文搜索)                  │
├─────────────────────────────────────────────┤
│          JSONL (legacy)                      │
│            (兼容导出)                        │
└─────────────────────────────────────────────┘
```

### 5.2 数据流

1. **消息输入** → SessionManager 缓存
2. **异步写入** → Honcho 云端 + 本地缓存
3. **上下文构建** → SessionDB 获取消息 → Honcho 获取用户画像 → ContextCompressor 压缩
4. **最终输出** → Agent 上下文

---

## 六、与其他系统对比

| 特性 | Hermes Honcho | pi-mono | Aloha |
|------|---------------|---------|-------|
| **用户建模** | ✅ Honcho | ❌ | ❌ |
| **心理理论** | ✅ | ❌ | ❌ |
| **多会话记忆** | ✅ | 基础 | ❌ |
| **跨会话学习** | ✅ 云端 | ❌ | ❌ |
| **本地优先** | 可配置 | JSONL | 内存 |

---

## 七、设计理念

### 7.1 核心理念

1. **对话即用户建模**
   - 每一次对话都是了解用户的机会
   - AI 不仅记住对话，还理解用户的"心智模型"

2. **渐进式学习**
   - 通过 seed_ai_identity 播种初始身份
   - 通过对话持续更新用户表征

3. **隐私优先**
   - 支持本地部署 (self-hosted Honcho)
   - 消息可选择保存或仅本地

### 7.2 技术选型原因

- **使用 Honcho 而非自建**：专业的对话记忆平台，已经实现了 peer/session 抽象
- **云端 + 本地混合**：平衡隐私和功能
- **异步写入**：不阻塞主对话流程

---

## 八、对 Aloha 的启示

### 8.1 可借鉴的设计

1. **本地缓存 + 异步同步**
   - 消息先存本地，立即返回
   - 后台异步同步到云端

2. **Peer 抽象**
   - 区分 user 和 assistant
   - 支持多用户场景

3. **配置分层**
   - 实例配置 > 全局配置 > 环境变量

### 8.2 当前 Aloha 差距

| 能力 | Hermes | Aloha |
|------|--------|-------|
| 用户建模 | Honcho | ❌ |
| 跨会话学习 | 云端 | ❌ |
| 心理理论 | 表征提取 | ❌ |

### 8.3 建议路径

1. **短期**：实现本地消息缓存 (类似 SessionManager)
2. **中期**：引入 SQLite 存储 + FTS5 搜索
3. **长期**：可选集成 Honcho 或自建用户建模
