# Aloha ReActLoop vs NanoBot AgentLoop 实现对比

## 一、整体架构对比

| 特性 | Aloha ReActLoop | NanoBot AgentLoop |
|------|-----------------|-------------------|
| **核心定位** | 轻量级 ReAct Agent 主循环 | 超轻量级 OpenClaw Python 实现 |
| **代码规模** | ~255 行 (loop.py) | 更精简 (核心逻辑) |
| **架构模式** | 单体设计 | 模块化设计 (多子模块) |

---

## 二、核心流程对比

### Aloha ReActLoop 流程

```
process(user_input)
  ├─ 清空思考日志
  ├─ 添加用户消息到 session_memory
  ├─ 构建消息列表 (_build_messages)
  ├─ 调用 LLM (provider.chat_with_tools)
  ├─ 处理响应 (_handle_response)
  │   ├─ 添加助手消息
  │   └─ 工具调用循环 (最多 5 次)
  │       ├─ 执行工具 (_execute_tool)
  │       └─ 再次调用 LLM
  └─ 返回最终响应
```

### NanoBot AgentLoop 流程

```
AgentLoop (核心处理引擎)
  ├─ 接收消息 (bus)
  ├─ 构建上下文 (历史 + 内存 + skills)
  ├─ 调用 LLM
  ├─ 执行工具调用
  └─ 发送响应
```

---

## 三、关键实现差异

### 1. 消息构建

**Aloha** (`_build_messages` in `aloha/agent/loop.py`):
```python
def _build_messages(self) -> list[Message]:
    messages = []
    if self.system_prompt:
        messages.append(Message(role="system", content=self.system_prompt))
    messages.extend(self.session_memory.get_messages())
    return messages
```

**NanoBot**:
- 更复杂的上下文构建 (历史 + 内存 + skills)
- 支持 `ContextBuilder` 模块

### 2. 工具执行循环

**Aloha** (`_handle_response` in `aloha/agent/loop.py`):
```python
while response.tool_calls and iteration < max_iterations:
    for tool_call in response.tool_calls:
        await self._execute_tool(tool_call)
    # 再次调用 LLM
    response = await self.provider.chat_with_tools(...)
```

- 最大 5 次工具调用迭代
- 工具执行失败时不添加工具消息

**NanoBot**:
- 使用 `AgentRunner` 执行工具
- 支持更灵活的迭代控制

### 3. 安全机制

**Aloha** (`ToolWrapper` in `aloha/agent/wrapper.py`):
- `PermissionChecker` - 权限检查
- `Approver` - 审批流程
- `SecurityConfig` - 安全配置
- 白名单/黑名单控制

**NanoBot**:
- 依赖容器化隔离 (Docker)
- 基础工具级别的权限控制

### 4. 工具注册

**Aloha** (`ToolRegistry` in `aloha/agent/tools.py`):
- `BaseTool` 基类
- 同步/异步工具支持

**NanoBot**:
- 更完整的工具 schema 生成
- 参数类型转换和验证

---

## 四、NanoBot 特有的功能

| 模块 | 说明 |
|------|------|
| **Skills** | 技能系统 (github, weather, tmux 等) |
| **Channels** | 12+ 消息渠道 (Telegram, Discord, Slack, 微信等) |
| **Providers** | 多 LLM 提供商支持 (Anthropic, OpenAI, Ollama 等) |
| **Memory** | 持久化内存管理 |
| **Hooks** | 生命周期钩子 (on_start, on_message, on_tool_call 等) |
| **Subagent** | 后台任务执行 |
| **Cron** | 定时任务 |
| **Heartbeat** | 主动唤醒机制 |

---

## 五、总结

| 维度 | Aloha | NanoBot |
|------|-------|---------|
| **轻量化** | ✅ 更轻量 | ✅ 超轻量 (代码量少 99%) |
| **安全性** | ✅ Python 层安全控制 | ✅ 容器级隔离 |
| **扩展性** | 基础工具注册 | 完整的 Skills/Extensions |
| **多渠道** | 基础 | 12+ 渠道支持 |
| **多提供商** | OpenAI/MiniMax | 8+ 提供商 |
| **生产级** | 适合原型 | 生产级完善 |

**建议**：
- 如果需要快速原型，Aloha 更简单
- 如果需要生产级功能，参考 NanoBot 的模块化设计