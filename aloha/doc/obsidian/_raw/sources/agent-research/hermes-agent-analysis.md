---
title: Hermes Agent 深度分析报告
date: 2026-03-31
tags:
  - AI-Agent
  - Hermes
  - NousResearch
  - memory-system
---

# Hermes Agent 深度分析报告

## 一、项目概述

**GitHub**: https://github.com/NousResearch/hermes-agent
**Stars**: 18.7k
**语言**: Python (92.5%)
**描述**: "The agent that grows with you" - 自我进化的 AI Agent

### 核心定位

> The self-improving AI agent built by Nous Research. It's the only agent with a built-in learning loop — it creates skills from experience, improves them during use, nudges itself to persist knowledge, searches its own past conversations, and builds a deepening model of who you are across sessions.

---

## 二、设计理念

### 1. 核心哲学

| 理念 | 说明 |
|------|------|
| **自我进化** | Agent 从经验中学习，创建和改进技能 |
| **持续记忆** | 跨会话持久化知识，构建用户模型 |
| **低成本运行** | 可以在 $5 VPS 或 serverless 上运行 |
| **多平台接入** | Telegram, Discord, Slack, WhatsApp, Signal, Email |

### 2. 关键技术特性

从 README 提取的核心特性：

| 特性 | 说明 |
|------|------|
| **终端界面** | 完整 TUI，多行编辑，斜杠命令自动完成，流式工具输出 |
| **多渠道消息** | Telegram, Discord, Slack, WhatsApp, Signal, CLI |
| **闭环学习** | Agent 自主创建技能，技能在使用中自我改进 |
| **FTS5 会话搜索** | 跨会话回忆，LLM 摘要 |
| **定时任务** | 内置 cron 调度器，自然语言配置 |
| **子代理委托** | 并行工作流，RPC 调用工具 |
| **六种终端后端** | local, Docker, SSH, Daytona, Singularity, Modal |

---

## 三、核心架构

### 项目结构

```
hermes-agent/
├── agent/              # Agent 核心逻辑
├── acp_adapter/       # ACP 协议适配器
├── acp_registry/      # ACP 注册表
├── cron/              # 定时任务
├── docs/              # 文档
├── docker/            # Docker 配置
├── assets/            # 资源文件
└── .plans/            # 规划文档
```

### 终端后端支持

| 后端 | 说明 |
|------|------|
| local | 本地运行 |
| Docker | Docker 容器 |
| SSH | 远程 SSH |
| Daytona | Serverless |
| Singularity | HPC 容器 |
| Modal | Serverless 函数 |

---

## 四、记忆系统（核心重点）

### 1. 记忆系统概述

Hermes Agent 的记忆系统是其最核心的特色，README 中明确提到：

> **A closed learning loop** — Agent-curated memory with periodic nudges. Autonomous skill creation after complex tasks. Skills self-improve during use. FTS5 session search with LLM summarization for cross-session recall. Honcho dialectic user modeling.

### 2. 记忆系统组件

| 组件 | 功能 |
|------|------|
| **Agent-curated memory** | Agent 自主管理的记忆 |
| **Periodic nudges** | 定期提醒持久化知识 |
| **Autonomous skill creation** | 复杂任务后自动创建技能 |
| **Skills self-improve** | 技能在使用中自我改进 |
| **FTS5 session search** | 全文搜索会话历史 |
| **LLM summarization** | LLM 摘要跨会话回忆 |
| **Honcho user modeling** | 用户画像建模 |

### 3. 记忆类型

从文档结构可见，Hermes 包含以下记忆类型：

#### 3.1 持久记忆（Persistent Memory）
- 跨会话持久化
- 用户偏好学习
- 项目上下文

#### 3.2 程序记忆（Procedural Memory）
- 技能系统
- 工具使用模式
- 工作流程

#### 3.3 会话记忆（Session Memory）
- 当前会话消息
- 上下文管理
- 压缩机制

#### 3.4 用户模型（User Model）
- Honcho dialectic 用户建模
- 用户画像
- 交互模式学习

### 4. 记忆命令

从 CLI 命令参考：

| 命令 | 功能 |
|------|------|
| `/memory` | 管理记忆 |
| `/compress` | 压缩上下文 |
| `/usage` | 检查 token 使用 |
| `/insights` | 会话洞察 |
| `/skills` | 浏览技能 |
| `/new` | 新会话 |

---

## 五、技能系统

### 1. 技能创建

- **自主创建**: 复杂任务后自动创建技能
- **自我改进**: 技能在使用中不断优化
- **agentskills.io 兼容**: 符合开放标准

### 2. 技能类型

| 类型 | 说明 |
|------|------|
| User Skills | 用户创建的技能 |
| Built-in Skills | 内置技能 |
| Skills Hub | 技能市场 |

---

## 六、与 pi-mono 对比

### 架构对比

| 特性 | Hermes Agent | pi-mono |
|------|--------------|---------|
| **语言** | Python | TypeScript |
| **Stars** | 18.7k | 28k |
| **记忆系统** | 完整闭环学习 | 会话存储 |
| **技能系统** | 自主创建+改进 | 静态技能 |
| **用户模型** | Honcho 建模 | 无 |
| **多渠道** | 6+ 平台 | 基础 |
| **自我进化** | ✅ | ❌ |

### 记忆系统对比

| 特性 | Hermes | pi-mono |
|------|--------|---------|
| **长期记忆** | ✅ brain.jsonl + vault | 可选扩展 |
| **用户画像** | ✅ Honcho | ❌ |
| **技能进化** | ✅ 自主创建/改进 | ❌ |
| **会话搜索** | ✅ FTS5 | ❌ |
| **定期提醒** | ✅ nudges | ❌ |

---

## 七、对 Aloha 的启示

### 1. 记忆系统设计

Hermes 的记忆系统是到目前为止分析的所有 Agent 中最完善的。Aloha 可以借鉴：

```
建议的 Aloha 记忆架构：
├── session_memory     # 会话记忆（当前）
├── longterm_memory    # 长期记忆（跨会话）
├── user_model         # 用户画像
└── skills_memory      # 技能进化
```

### 2. 关键功能优先级

| 功能 | 优先级 | 说明 |
|------|--------|------|
| FTS5 会话搜索 | 高 | 跨会话回忆 |
| 用户建模 | 中 | Honcho 集成 |
| 技能进化 | 中 | 自主创建技能 |
| 定期提醒 | 中 | nudges 机制 |

### 3. 技术实现建议

```python
# 推荐实现
class HermesLikeMemory:
    def __init__(self):
        self.session = SessionMemory()      # 会话
        self.longterm = LongTermMemory()    # 长期
        self.user_model = UserModel()       # 用户画像
        self.skills = SkillsMemory()         # 技能
    
    def periodic_nudge(self):
        """定期提醒持久化"""
        
    def create_skill(self, task):
        """自主创建技能"""
        
    def improve_skill(self, skill):
        """技能自我改进"""
        
    def search_sessions(self, query):
        """FTS5 会话搜索"""
```

---

## 八、参考资料

- [Hermes Agent GitHub](https://github.com/NousResearch/hermes-agent)
- [官方文档](https://hermes-agent.nousresearch.com/docs/)
- [Discord 社区](https://discord.gg/NousResearch)
- [Skills Hub](https://agentskills.io)

---

## 九、总结

Hermes Agent 是目前功能最完整的开源 AI Agent 之一，其记忆系统设计代表了行业的领先实践：

1. **闭环学习**: Agent 不仅存储记忆，还能主动创建和改进技能
2. **用户建模**: 通过 Honcho 实现个性化的用户画像
3. **跨会话回忆**: FTS5 搜索 + LLM 摘要实现历史回忆
4. **成本优化**: 支持 serverless 部署，低成本运行

对于 Aloha 来说，Hermes 的记忆系统设计是最值得借鉴的实现方案。
