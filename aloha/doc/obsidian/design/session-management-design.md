# Session 管理功能设计文档

**日期**：2026-03-25
**版本**：v1.0

---

## 1. 概述

### 1.1 目标

实现以会话（Session）为单位的资源管理功能，参考 ChatGPT 网页版的用户体验，支持：

- 随时新建会话
- 每个会话拥有独立的 agent.md、skills、prompt 配置
- 支持会话级别的 memory.md 和 history.md

### 1.2 设计原则

- **混合存储**：Session 元数据存储在 SQLite，资源文件存储在文件系统
- **继承/覆盖**：支持全局默认配置，Session 可选择覆盖部分配置
- **运行时隔离**：每个 Session 对应独立的 Agent 实例，确保数据隔离

---

## 2. 目录结构

```
~/.aloha/
├── sessions/                         # Session 根目录
│   ├── global/                      # 全局默认配置（可被 Session 继承/覆盖）
│   │   ├── agent.md                 # 全局 Agent 提示词
│   │   ├── skills.toml              # 全局 Skills 配置
│   │   ├── prompts/                 # 全局 Prompt 模板
│   │   │   ├── SYSTEM.md
│   │   │   ├── USER.md
│   │   │   └── RULES.md
│   │   └── templates/                # Session 模板
│   │       ├── default/             # 默认模板
│   │       └── coding/              # 编程专用模板
│   ├── {uuid-session-id}/           # Session 目录（UUID 命名）
│   │   ├── metadata.json            # Session 元数据
│   │   ├── agent.md                 # 可选，覆盖全局
│   │   ├── skills.toml              # 可选，覆盖全局
│   │   ├── prompts/                 # 可选，扩展全局
│   │   ├── memory.md                # Session 记忆（持久化）
│   │   └── history.md               # 对话历史
│   └── ...
├── sessions.db                      # SQLite：Session 索引、搜索、全局配置
└── config.toml                      # Aloha 全局配置
```

---

## 3. 数据模型

### 3.1 Session 元数据（SQLite）

```sql
CREATE TABLE sessions (
    id TEXT PRIMARY KEY,              -- UUID
    name TEXT NOT NULL,               -- 用户自定义名称
    created_at TEXT NOT NULL,         -- ISO timestamp
    updated_at TEXT NOT NULL,         -- ISO timestamp
    status TEXT NOT NULL DEFAULT 'active',  -- active, paused, archived
    config_override TEXT,             -- JSON: session 级别配置覆盖
    template TEXT DEFAULT 'default', -- 使用的模板
    workspace_path TEXT               -- Session 工作目录
);

CREATE INDEX idx_sessions_status ON sessions(status);
CREATE INDEX idx_sessions_created ON sessions(created_at);
```

### 3.2 Session 类（Python）

```python
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from enum import Enum

class SessionStatus(Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"

@dataclass
class Session:
    id: str                           # UUID
    name: str
    created_at: datetime
    updated_at: datetime
    status: SessionStatus
    config_override: dict | None       # 配置覆盖
    template: str
    path: Path                        # Session 目录路径
    
    # 方法
    def get_agent(self) -> ReactAgent:
        """获取绑定此 Session 的 Agent"""
        
    def get_memory(self) -> SessionMemory:
        """获取 Session 记忆"""
        
    def get_history(self) -> list[Message]:
        """获取对话历史"""
        
    def update(self, name: str = None, status: SessionStatus = None):
        """更新 Session 元数据"""
```

---

## 4. 核心组件

### 4.1 SessionManager

```python
from pathlib import Path
import sqlite3

class SessionManager:
    """Session 管理器"""
    
    def __init__(self, base_path: Path = Path("~/.aloha").expanduser()):
        self.base_path = base_path
        self.sessions_path = base_path / "sessions"
        self.db_path = base_path / "sessions.db"
        self._ensure_directories()
        self._init_database()
    
    def _ensure_directories(self):
        """确保目录结构存在"""
        # 创建 sessions 目录
        # 创建 global 目录
        # 创建 templates 目录
    
    def _init_database(self):
        """初始化 SQLite 数据库"""
    
    def create_session(
        self,
        name: str,
        config_override: dict | None = None,
        template: str = "default"
    ) -> Session:
        """创建新 Session"""
        # 生成 UUID
        # 创建 Session 目录
        # 从模板复制文件（如适用）
        # 写入 metadata.json
        # 插入数据库记录
        # 返回 Session 对象
    
    def get_session(self, session_id: str) -> Session | None:
        """获取 Session"""
        # 从数据库查询
        # 返回 Session 对象
    
    def list_sessions(
        self,
        status: SessionStatus | None = None,
        limit: int = 100,
        offset: int = 0
    ) -> list[Session]:
        """列出 Session"""
    
    def delete_session(self, session_id: str):
        """删除 Session（包括物理文件）"""
    
    def archive_session(self, session_id: str):
        """归档 Session"""
    
    def load_config(self, session: Session) -> dict:
        """加载 Session 配置（合并全局 + Session 覆盖）"""
        # 1. 加载 global/defaults/
        # 2. 加载 global/templates/{template}/
        # 3. 加载 session 目录覆盖
        # 返回合并后的配置
```

### 4.2 配置加载优先级

```
配置加载顺序（后者覆盖前者）：
1. global/defaults/agent.md          # 系统默认值
2. global/templates/{template}/    # 模板配置
3. sessions/{id}/agent.md           # Session 级别覆盖
```

### 4.3 Session 与 Agent 绑定

```python
class Session:
    def get_agent(self, provider: BaseProvider) -> ReactAgent:
        """获取绑定此 Session 的 Agent"""
        # 1. 加载合并后的配置
        config = session_manager.load_config(self)
        
        # 2. 创建 ReactAgent 实例
        agent = ReactAgent(
            provider=provider,
            model=config.get("model", "gpt-4o-mini"),
            system_prompt=config.get("agent_md", "").read_text(),
            # ... 其他参数
        )
        
        # 3. 加载 Session 记忆
        agent.session_memory = self._load_memory()
        
        return agent
```

---

## 5. Session 隔离机制

### 5.1 运行时隔离

- 每个 Session 创建独立的 ReactAgent 实例
- Agent 内部维护独立的 SessionMemory
- 不同 Session 的 Agent 不共享内存

### 5.2 工具调用隔离

- 可配置 `restrict_to_workspace: true`
- 工具（如文件读写）只能访问 Session 目录内的文件
- 通过 workspace 路径限制，确保 Agent 只能操作自己 Session 的资源

### 5.3 配置文件隔离

- 每个 Session 有独立的 agent.md、skills.toml
- 配置加载时根据 session_id 加载对应目录的配置
- 全局配置仅作为"默认值"被读取

---

## 6. 使用示例

```python
from aloha.session import SessionManager
from aloha.providers import OpenAIProvider

# 初始化 SessionManager
manager = SessionManager()

# 创建新 Session
session = manager.create_session(
    name="My Coding Session",
    template="coding"
)

# 获取 Agent
provider = OpenAIProvider(api_key="sk-...")
agent = session.get_agent(provider)

# 对话
response = await agent.process("帮我写一个排序算法")

# 获取历史
history = session.get_history()
```

---

## 7. 未来扩展

### 7.1 Session 模板系统

预定义不同类型的 Session：

- `default`：默认配置
- `coding`：编程专用（更多工具权限）
- `writing`：写作专用
- `analysis`：分析专用

### 7.2 多端访问

未来可通过 REST API 或 WebSocket 提供多端访问：

```
GET /api/sessions          # 列出所有 Session
POST /api/sessions         # 创建 Session
GET /api/sessions/{id}     # 获取 Session
DELETE /api/sessions/{id} # 删除 Session
WS /api/sessions/{id}/chat # WebSocket 对话
```

---

## 8. 验收标准

1. ✅ 可以创建、获取、列出、删除 Session
2. ✅ Session 拥有独立的 agent.md、skills、prompt 配置
3. ✅ 支持全局配置继承和 Session 级别覆盖
4. ✅ Session 之间数据隔离
5. ✅ Session 拥有独立的 memory.md 和 history.md
6. ✅ 可通过模板快速创建 Session
7. ✅ SQLite 存储元数据，文件系统存储资源文件