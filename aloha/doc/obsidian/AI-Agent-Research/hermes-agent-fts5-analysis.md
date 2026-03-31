# Hermes Agent FTS5 会话搜索实现分析

## 概述

Hermes Agent 使用 SQLite 的 FTS5 (Full-Text Search 5) 模块实现会话消息的全文搜索功能。这是其记忆系统的核心组件，替换了之前基于每会话 JSONL 文件的方法。

## 核心设计

### 1. 数据库架构

**两张主要表：**
- `sessions` - 会话元数据
- `messages` - 消息内容

**FTS5 虚拟表：**
```sql
CREATE VIRTUAL TABLE messages_fts USING fts5(
    content,
    content=messages,
    content_rowid=id
);
```

关键特性：
- `content=messages` - 使用 content sync 方式，FTS5 表与 messages 表同步
- `content_rowid=id` - 将 messages 表的 id 作为 FTS5 的 rowid

### 2. 触发器实现自动同步

```sql
CREATE TRIGGER messages_fts_insert AFTER INSERT ON messages BEGIN
    INSERT INTO messages_fts(rowid, content) VALUES (new.id, new.content);
END;

CREATE TRIGGER messages_fts_delete AFTER DELETE ON messages BEGIN
    INSERT INTO messages_fts(messages_fts, rowid, content) VALUES('delete', old.id, old.content);
END;

CREATE TRIGGER messages_fts_update AFTER UPDATE ON messages BEGIN
    INSERT INTO messages_fts(messages_fts, rowid, content) VALUES('delete', old.id, old.content);
    INSERT INTO messages_fts(rowid, content) VALUES (new.id, new.content);
END;
```

三个触发器分别处理 INSERT、DELETE、UPDATE 操作，确保 FTS5 索引与 messages 表始终保持同步。

### 3. 查询清理 (Query Sanitization)

FTS5 有自己的查询语法，特殊字符如 `"`, `(`, `)`, `+`, `*`, `{`, `}` 有特殊含义。直接传入用户输入可能导致 `sqlite3.OperationalError`。

**清理策略 (6步)：**

1. **保留引用的短语**：提取并保护配对的引号短语
   ```python
   sanitized = re.sub(r'"[^"]*"', _preserve_quoted, query)
   ```

2. **移除 FTS5 特殊字符**：
   ```python
   sanitized = re.sub(r'[+{}()\"^]', " ", sanitized)
   ```

3. **折叠重复的星号**：
   ```python
   sanitized = re.sub(r"\*+", "*", sanitized)
   sanitized = re.sub(r"(^|\s)\*", r"\1", sanitized)
   ```

4. **移除悬空的布尔运算符**：
   ```python
   sanitized = re.sub(r"(?i)^(AND|OR|NOT)\b\s*", "", sanitized.strip())
   sanitized = re.sub(r"(?i)\s+(AND|OR|NOT)\s*$", "", sanitized.strip())
   ```

5. **用引号包裹带连字符的词**（如 `chat-send`）：
   ```python
   sanitized = re.sub(r"\b(\w+(?:-\w+)+)\b", r'"\1"', sanitized)
   ```

6. **恢复保留的引号短语**

### 4. 搜索函数实现

```python
def search_messages(
    self,
    query: str,
    source_filter: List[str] = None,
    exclude_sources: List[str] = None,
    role_filter: List[str] = None,
    limit: int = 20,
    offset: int = 0,
) -> List[Dict[str, Any]]:
```

**支持 FTS5 查询语法：**
- 简单关键词: `"docker deployment"`
- 短语: `'"exact phrase"'`
- 布尔: `"docker OR kubernetes"`, `"python NOT java"`
- 前缀: `"deploy*"`

**查询构建：**
```python
sql = f"""
    SELECT
        m.id,
        m.session_id,
        m.role,
        snippet(messages_fts, 0, '>>>', '<<<', '...', 40) AS snippet,
        m.content,
        m.timestamp,
        m.tool_name,
        s.source,
        s.model,
        s.started_at AS session_started
    FROM messages_fts
    JOIN messages m ON m.id = messages_fts.rowid
    JOIN sessions s ON s.id = m.session_id
    WHERE messages_fts MATCH ?
    ORDER BY rank
    LIMIT ? OFFSET ?
"""
```

**关键特性：**
- 使用 `snippet()` 函数返回带有标记的文本片段
- 支持多种过滤条件（source, role）
- 自动返回上下文消息（每条匹配前后各1条）

### 5. 并发与性能优化

**WAL 模式 (Write-Ahead Logging)：**
```python
self._conn.execute("PRAGMA journal_mode=WAL")
```

**写竞争处理：**
- 短超时 (1s) + 应用层随机 jitter 重试
- 避免 SQLite 内置确定性退避导致的 convoy 效应

```python
_WRITE_MAX_RETRIES = 15
_WRITE_RETRY_MIN_S = 0.020   # 20ms
_WRITE_RETRY_MAX_S = 0.150   # 150ms
```

**定期 WAL checkpoint：**
```python
if self._write_count % self._CHECKPOINT_EVERY_N_WRITES == 0:
    self._try_wal_checkpoint()
```

### 6. 会话标题系统

Hermes 实现了基于标题的会话管理：
- 标题唯一性约束
- 标题继承链 (`title #2`, `title #3`)
- 标题解析和搜索

## 与其他系统的对比

| 特性 | Hermes | pi-mono | Aloha |
|------|--------|---------|-------|
| 存储方式 | SQLite | JSONL | 内存 + JSONL |
| 全文搜索 | FTS5 | 无 | 无 |
| 会话继承 | parent_session_id | parentId | 无 |
| 并发支持 | WAL 模式 | 单文件 | 内存 |
| 消息过滤 | 丰富 | 基础 | 无 |

## 总结

Hermes Agent 的 FTS5 实现是一个生产级的全文搜索方案：

1. **自动化同步**：触发器确保 FTS5 索引始终与消息表同步
2. **安全清理**：严格的查询清理防止 SQL 注入和语法错误
3. **高性能**：WAL 模式 + 应用层重试优化高并发场景
4. **丰富功能**：snippet、上下文、多种过滤条件

这个设计对于需要长期记忆和高效搜索的 AI Agent 系统具有重要参考价值。
