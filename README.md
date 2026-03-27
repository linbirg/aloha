# Aloha - 轻量级 AI Agent 框架

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

一个轻量级、安全可控的 Python AI Agent 框架，参照 nanobot 架构设计，支持会话管理、技能扩展和灵活的资源组织。

## 动机与背景

在探索 AI Agent 的过程中，我们对比了多个开源方案：

| 方案 | 特点 | 不足 |
|------|------|------|
| **OpenClaw** | 功能完整，生态丰富 | 过于笨重，学习成本高 |
| **Nanobot** | 轻量简洁 | 只有基础功能，扩展性不足 |
| **OpenFang** | 折中方案 | 非 Python 实现，代码阅读和社区受众受限 |

**Aloha** 的目标是：采用 Python 实现轻量级 Agent，在保持轻量的基础上，更贴合个人使用场景，更安全可控。总体希望按照HARNESS的范式，通过构造安全可控契合用户需求的前后环境配合大模型，力图解决核心难题：

- 连续性:多次对话、多session无缝衔接
- 完成度幻觉
- 可恢复性：万一崩溃，能查原因，能回来接着干
- 可控制性：权限审批，风险操作提醒，日志完整

## 核心特性

### 1. 会话/任务式管理

- 以会话（Session）或任务（Task）为单位组织资源
- 支持随时新建会话，像网页版 AI 一样方便
- 每个会话拥有独立的：agent.md、skills、prompt 内容
- 支持会话级别的 memory.md、history.md

### 2. 分层式 Skills 管理

```
skills/
├── system/          # 系统级技能（安全、审查等，默认启用）
├── builtin/         # 内置自带技能
├── session_xxx/     # 会话私有技能
└── plugins/         # 额外安装的技能
```

- **系统级技能**：安全审查类，默认安装，可配置黑名单
- **会话级技能**：按任务需求选择安装
- **always_skills.txt**：始终激活的技能列表
- 支持动态加载，按需启用

### 3. 灵活的 Prompt 体系

支持多级 prompt 文件，按顺序拼接构建 system prompt：

```
SOUL.md   → 核心价值观/灵魂
AGENT.md  → Agent 角色定义
RULES.md  → 行为规则/约束
SYSTEM.md → 系统级指令
USER.md   → 用户自定义
```

- **系统级**：全局通用
- **会话级**：可覆盖系统级，按任务特性定制

### 4. 记忆管理

- **SessionMemory**：会话级短期记忆，管理消息历史
- **LongTermMemory**：长期记忆持久化（规划中）

### 5. 工具与插件

- **系统工具**：内置基础工具
- **插件机制**：支持扩展自定义工具

### 6. 权限与安全

- 参照 RooCode 的授权管理思路
- 安全审查类技能默认启用
- 支持技能黑名单机制

## 项目结构

```
aloha/
├── agent/           # Agent 核心逻辑
│   ├── base.py      # Agent 基类
│   └── loop.py      # Agent 主循环
├── bus/             # 消息总线
├── config/          # 配置管理
├── memory/          # 记忆管理
│   ├── session.py  # 会话记忆
│   └── longterm.py # 长期记忆
├── prompts/         # Prompt 加载器
├── providers/       # LLM 提供商
├── skills/          # 技能加载器
├── tools/           # 工具系统
└── templates/       # 默认 Prompt 模板
    └── prompts/
        ├── SOUL.md
        ├── AGENT.md
        ├── RULES.md
        ├── SYSTEM.md
        └── USER.md
```

## 快速开始

### 安装

```bash
pip install -r requirements.txt
```

### 基本使用

```python
from aloha import ReactAgent
from aloha.providers import OpenAIProvider
from aloha.bus import MessageBus

# 初始化
provider = OpenAIProvider(api_key="your-key", model="gpt-4o-mini")
bus = MessageBus()
agent = ReactAgent(bus, provider)

# 运行
asyncio.run(agent.run())
```

### 使用 Skills

```python
from aloha.skills import SkillsLoader

loader = SkillsLoader()
skills = loader.list_skills()

# 加载特定技能
skill_content = loader.load_skill("brainstorming")
```

## 配置说明

配置文件位于 `~/.aloha/config.toml`，主要配置项：

```toml
[provider]
api_key = "your-api-key"
model = "gpt-4o-mini"

[agent]
max_iterations = 40
temperature = 0.1

[workspace]
path = "~/.aloha/workspace"
```

## 开发指南

- 遵循 PEP 8 + 项目目录结构约定
- snake_case 命名，无缩写
- 导入顺序：标准库 → 第三方 → 本地模块
- 分层清晰：views → services → models/repositories

## 未来规划

- [ ] 完善会话管理界面
- [ ] 长期记忆持久化
- [ ] 技能市场/插件市场
- [ ] 权限控制系统增强
- [ ] Web UI 支持

## 参考项目

- [nanobot](https://github.com/nanobot) - 轻量级 Agent 架构
- [OpenClaw](https://github.com/openclaw) - 功能完整的 Agent 框架
- [OpenFang](https://github.com/openfang) - Agent 思想启发
- [RooCode](https://roo.code) - 权限管理参考

## 许可证

MIT License