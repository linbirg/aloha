# AI Agent 架构设计与安全控制研究

本文档包含两部分内容：
1. Anthropic 关于长时间运行 Agent 的有效架构设计
2. AI Agent 可控制性、权限审批与风险操作提醒的实现方案

---

# 第一部分：长时间运行 Agent 的有效架构设计（Anthropic）

## 文章概述

本文由 Anthropic 工程团队撰写，探讨了如何构建能够跨多个上下文窗口持续工作的 AI Agent 系统。文章提出了一个双轨解决方案：**初始化 Agent（Initializer Agent）** 和 **编码 Agent（Coding Agent）**，并详细阐述了四种常见的失败模式及其对应的解决策略。

## 核心挑战

长时间运行的 Agent 面临两个关键问题：

1. **功能过度膨胀**：Agent 倾向于一次性完成整个任务，导致在实现中途耗尽上下文窗口，下一个会话不得不面对半完成且缺乏文档的代码
2. **过早声明完成**：项目进行到一定阶段后，Agent 会误认为工作已完成而过早退出

这些问题的根源在于上下文窗口的局限性——大多数复杂项目无法在单个窗口内完成。

## 双轨解决方案

- **初始化 Agent**：在首次运行时负责搭建环境基础，创建 init.sh 启动脚本、生成 claude-progress.txt 进度日志文件、初始化 git 仓库并完成首次提交
- **编码 Agent**：在每个后续会话中执行增量式开发，每次只专注于完成一个功能，同时确保代码库处于可合并的整洁状态

这种设计灵感来源于真实软件工程团队的工作模式——每个新工程师都需要快速了解项目当前状态。

## 四种失败模式与解决方案

| 问题 | 初始化 Agent 行为 | 编码 Agent 行为 |
|------|------------------|----------------|
| Agent 过早宣布项目完成 | 建立功能列表文件 | 阅读功能列表，每次只做一个功能 |
| 环境处于有 bug 或未记录的状态 | 创建 git 仓库和进度文件 | 开始时读取进度文件和 git 提交日志，结束时写入提交和进度更新 |
| Agent 过早标记功能为完成 | 建立功能列表文件 | 自我验证所有功能，谨慎标记为"通过" |
| Agent 花时间研究如何运行应用 | 编写 init.sh 脚本 | 开始时读取 init.sh |

### 关键实践

1. **Feature List**：初始化 Agent 创建详细的 feature_list.json 文件，使用 JSON 格式（相比 Markdown，模型更不容易随意修改）
2. **增量进度**：编码 Agent 每次只做一个功能，通过 git 提交和 progress.txt 追踪进度
3. **端到端测试**：使用 Puppeteer MCP 等浏览器自动化工具进行真实的用户操作验证
4. **环境启动**：init.sh 脚本确保每个新会话能够快速启动开发环境并进行基础验证

### 未来方向

文章指出当前方案针对全栈 Web 开发进行了优化，未来可能扩展到科学研究、金融建模等其他领域。同时也探讨了是否需要引入专门的测试 Agent、QA Agent 或代码清理 Agent 来进一步提升系统效果。

---

# 第二部分：AI Agent 可控制性、权限审批与风险操作提醒 - 实现方案研究

根据百度搜索结果，以下是当前业界在 AI Agent 安全控制方面的主流实现方案：

## 一、核心安全挑战

1. **权限边界失控**：当 Agent 具备自动调用系统能力时，权限一旦失控，风险可能迅速升级为数据安全或系统安全事件
2. **提示词注入**：攻击者通过恶意提示词操控 Agent 行为
3. **误操作**：Agent 在自主决策过程中可能产生非预期的高风险操作
4. **插件投毒**：第三方插件可能包含恶意代码

## 二、主流实现方案

### 1. A2AS 安全框架

首个针对 AI Agent 全生命周期设计的系统性安全方案，核心特点：

- **五维防护体系**：身份可信、权限可控、行为可审计、风险可隔离、应急可自愈
- **平衡自主安全与业务效能**：破解"自主决策与安全管控"的核心矛盾

### 2. 认证、授权与行为审计体系

在企业级多智能体协作系统中构建：

- **身份认证机制**：确保 Agent 身份可信
- **精细化权限控制**：基于 RBAC 的角色权限管理，实现权限最小化原则
- **可追踪的行为审计链**：记录所有操作行为，支持事后溯源

### 3. 腾讯云 AI Agent 安全网关

作为企业 AI 智能体规模化落地的安全基座：

- **全链路防护**：从 token 消耗治理、内容安全防护到行为审计
- **智能策略引擎**：实时监测 AI 交互意图与资源消耗
- **精准拦截**：有效收敛智能体风险边界

### 4. 沙箱与最小权限实战方案

核心安全对策包括：

- **执行环境隔离**：将 Agent 限定在隔离环境中运行
- **最小权限原则**：仅授予完成任务所需的最小权限集合
- **严格审计**：记录所有操作行为
- **白名单控制**：仅允许预设的安全操作

### 5. 国内合规指南要点

- **全生命周期安全管控**：覆盖部署、运行、退役各阶段
- **法规框架**：依据《网络安全法》等安全管理规范
- **核心风险防控**：权限滥用、数据泄露、算法失控、操作溯源难

## 三、关键技术措施

| 措施 | 说明 |
|------|------|
| 权限分级 | 将操作分为只读、执行、审批等多个级别 |
| 审批工作流 | 高风险操作需人工审批后才能执行 |
| 实时监控 | 监测 Agent 行为模式，识别异常操作 |
| 熔断机制 | 检测到风险行为时自动暂停并告警 |
| 审计日志 | 完整记录所有操作，支持合规审计 |

## 四、总结

当前业界主要通过以下方式实现 Agent 可控制性：

1. **身份认证**：确保 Agent 身份可信
2. **权限控制**：基于最小权限原则的精细化授权
3. **行为审计**：完整记录并可追溯所有操作
4. **风险隔离**：通过沙箱等技术限制 Agent 活动范围
# 第三部分：AI Agent 连续性保障 - 多次对话、多 Session 无缝衔接实现方案

根据百度搜索结果，关于 AI Agent 在保障连续性（多次对话、多 session 无缝衔接）方面的实现方案和思考如下：

## 一、核心挑战

1. **上下文丢失**：每个新 session 开始时，Agent 没有之前对话的记忆
2. **状态断裂**：长时间运行任务需要跨多个上下文窗口保持工作连续性
3. **记忆丧失**：Agent 容易"失忆"，无法记住之前交互的关键信息

## 二、主流实现方案

### 1. 状态管理（Session 管理系统）

通过维护一个状态对象来存储对话相关信息：

- 用户偏好设置
- 历史对话内容
- 关键变量和参数

```python
class ChatSession:
    def __init__(self):
        self.state = {}
        self.history = []
```

### 2. 对话状态跟踪（Dialogue State Tracking）

AI Agent 通过分析用户输入，结合当前对话状态，更新状态信息并生成合适的回复。例如酒店预订场景：
- 用户说"我想预订酒店" → 记录意图为"酒店预订"
- 用户说"在上海" → 更新状态为"地点:上海"

### 3. LangChain 记忆组件

LangChain 提供了多种记忆机制来实现多轮对话：

- **ConversationBufferMemory**：保存完整对话历史
- **MessagesPlaceholder**：将历史消息注入 prompt
- 通过 `agent_kwargs` 参数传递聊天历史

```python
memory = ConversationBufferMemory(
    memory_key="chat_history", 
    return_messages=True
)
```

### 4. Session 持久化存储

- **SQLiteSession**：本地文件存储对话状态
- **OpenAIConversationsSession**：使用 OpenAI API 存储状态
- 支持会话恢复和跨设备同步

### 5. Microsoft Agent Framework

通过 `agent.GetNewThread()` 创建新对话线程，后续交互传入相同 thread 对象实现连续对话：

```csharp
AgentThread thread = agent.GetNewThread();
// 后续每次交互传入同一 thread 对象
await agent.RunAsync(userInput, thread);
```

## 三、关键技术措施

| 技术 | 说明 |
|------|------|
| 记忆模块 | 保存短期/长期记忆，支持上下文注入 |
| 状态跟踪 | 维护对话状态（如意图、实体、槽位） |
| 上下文压缩 | 对话历史过长时进行摘要压缩 |
| Session 隔离 | 多用户/多会话环境下的独立状态管理 |
| 流式响应 | 实时显示回复，提升交互体验 |

## 四、与 Anthropic 方案的结合

结合之前 Anthropic 的双轨解决方案，其通过以下方式实现跨多个上下文窗口的工作连续性：

- **claude-progress.txt**：进度日志文件，记录已完成工作
- **Git 提交历史**：通过版本控制系统追踪代码变更
- **Feature list 状态追踪**：维护功能列表，明确工作进度

这种方式特别适合长时间运行的编码任务，让不同 session 的 Agent 能够快速了解项目当前状态。

## 五、未来思考

- **多 Agent 架构下的记忆共享**：多个 Agent 之间如何共享和同步记忆
- **个性化记忆**：不同用户有不同的记忆需求，定制化记忆策略
- **主动记忆**：Agent 主动记录重要信息而非被动存储
- **记忆检索**：高效地从大量历史记录中检索相关信息

---

# 第四部分：rho 项目研究 - 基于 Pi 的持久运行 AI 代理

## 项目概述

**GitHub**: https://github.com/mikeyobrien/rho
**Stars**: 335 | **Language**: TypeScript | **License**: MIT

rho 是一个持久运行（always-on）的个人 AI 助手，基于 [pi coding agent](https://github.com/badlogic/pi-mono) 构建。

### 核心特点

- **持续运行**：后台守护进程，不是一次性对话
- **持久记忆**：跨会话保持上下文（brain.jsonl + vault 知识图谱）
- **主动心跳**：默认每 30 分钟一次自动检查，可配置
- **多平台支持**：macOS、Linux、Android（Termux）、iOS（SSH）

---

## 项目结构

```
rho/
├── cli/              # 命令行接口和守护进程编排
├── extensions/      # 运行时工具/模块（按 pi 规则加载）
├── skills/          # 便携式 Markdown 运行手册
├── platforms/       # 平台特定安装/能力
├── web/             # 浏览器 UI + RPC 桥接（无构建分离）
├── brain/           # 记忆系统（brain.jsonl）
├── vault/           # Markdown 知识图谱
└── configs/         # 配置文件
```

---

## 核心理念（十大原则）

### 1. 新鲜上下文即可靠性（Fresh Context Is Reliability）
每次检查开始时读取 brain.jsonl，重新验证状态，计划后再行动。不要假设持久化是完美的。

### 2. 背压优于规定（Backpressure Over Prescription）
不要微观管理"怎么做"，而是创建拒绝坏工作的门控（测试、验证、清晰的通过/失败标准）。

### 3. 计划是可消耗的（The Plan Is Disposable）
重新生成计划很便宜。永远不要坚持坏计划。

### 4. 磁盘即状态（Disk Is State）
文件是真相。brain 是会话间的连续性。

### 5. 用信号引导而非脚本（Steer With Signals, Not Scripts）
当某事失败时，添加一个学习、测试或行为条目。

### 6. 让 Agent 自主（Let Agent Agent）
用户坐在循环上调音，而不是指挥。像调吉他一样调整，而不是指挥。

---

## 核心系统设计

### 1. 记忆系统（Brain + Vault）

- **brain.jsonl**：结构化记忆，存储身份、行为偏好、活跃任务
- **vault/**：Markdown 知识图谱
- 会话开始时自动读取 brain.jsonl 获取上下文

### 2. 心跳机制（Heartbeat）

- 默认每 30 分钟一次主动检查
- `/rho now` - 立即触发检查
- `/rho interval 30m` - 设置间隔
- `/rho enable/disable` - 开关心跳

### 3. 多渠道接入

| 渠道 | 说明 |
|------|------|
| CLI | `rho ...` 命令 |
| Web UI | 内置浏览器工作空间（无构建） |
| Telegram | 允许名单 + 审核流程 |
| Email | agent 邮箱 name@rhobot.dev |

### 4. Web UI 设计（无构建分离）

服务端（Hono）：
- `web/*.ts` - 服务端/运行时代码

浏览器：
- `web/public/js/*.js` - 直接服务，无需打包器

特性：
- 实时流响应 + WebSocket 推送
- 空闲感知（标签页隐藏时暂停轮询）
- 渲染节流（150ms 防抖）
- Session 元数据缓存（按 mtime 避免重复读取）

---

## 安全与所有权模型

- **记忆本地存储**：`~/.rho/brain/brain.jsonl`
- **配置本地存储**：`~/.rho/init.toml`, `~/.rho/packages.toml`
- **提供商自有**：`rho login` 通过 pi 认证
- **Telegram 控制**：允许名单 + 提及审核
- **Email 控制**：发件人控制 + 出口策略限制

无需托管 rho 记忆后端。

---

## 与 Aloha 对比分析

| 特性 | rho | Aloha |
|------|-----|-------|
| **持久运行** | 守护进程 + 心跳 | 需要手动触发 |
| **记忆系统** | brain.jsonl + vault 知识图谱 | 基础 session memory |
| **多渠道** | CLI + Web + Telegram + Email | 当前主要是 Gradio UI |
| **安全模型** | 本地优先 + 权限控制 | 审批回调机制 |
| **平台** | 跨平台（移动端支持） | 主要是桌面 |
| **心跳机制** | 主动定期检查 | 被动响应 |
| **无构建 UI** | Hono + 直接 serving 前端 | Gradio |

---

## 可借鉴设计

### 1. 心跳机制
- 实现定期自动检查，不只是被动响应
- 支持配置间隔和立即触发

### 2. 结构化记忆（brain.jsonl）
- 持久上下文存储
- 会话开始时自动加载
- 支持增量和查询

### 3. 多渠道接入
- Telegram/Email 集成
- 允许名单 + 审核机制

### 4. 无构建 Web UI
- Hono 路由 + 直接 serving 前端
- 轻量级高性能方案

### 5. 背压设计
- 用测试/验证门控而非硬编码规则
- "计划可消耗"理念 - 快速迭代

---

# 第五部分：pi-mono 项目研究 - AI Agent 工具包

## 项目概述

**GitHub**: https://github.com/badlogic/pi-mono
**Stars**: 28,309 | **Forks**: 2,997 | **Language**: TypeScript

> Pi 是 OpenClaw 的基础项目，是一个极简的终端编码工具包。

## 核心定位

> **"Adapt pi to your workflows, not the other way around"**
> 
> 让 pi 适应你的工作流程，而不是反过来。

Pi 发行强大的默认值但跳过子代理、计划模式等功能。你可以要求 pi 构建你想要的，或安装匹配你工作流的第三方 pi 包。

## 包结构

| 包 | 说明 |
|---|------|
| **@mariozechner/pi-ai** | 统一多提供商 LLM API（OpenAI, Anthropic, Google 等） |
| **@mariozechner/pi-agent-core** | Agent 运行时，包含工具调用和状态管理 |
| **@mariozechner/pi-coding-agent** | 交互式编码 agent CLI |
| **@mariozechner/pi-mom** | Slack 机器人，将消息委托给 pi 编码 agent |
| **@mariozechner/pi-tui** | 终端 UI 库，带差分渲染 |
| **@mariozechner/pi-web-ui** | AI 聊天界面的 Web 组件 |
| **@mariozechner/pi-pods** | GPU pods 上管理 vLLM 部署的 CLI |

---

## 核心设计理念

### 1. 极简核心，扩展优先

Pi 故意不包含某些功能，而是通过扩展机制让用户自己实现：

| 故意不包含 | 替代方案 |
|-----------|----------|
| **MCP** | 用 Skills（带 README 的 CLI 工具），或构建扩展添加 MCP 支持 |
| **Sub-agents** | 通过 tmux 启动 pi 实例，或用扩展构建 |
| **Permission popups** | 在容器中运行，或用扩展构建确认流程 |
| **Plan mode** | 写计划到文件，或用扩展构建 |
| **Built-in to-dos** | 用 TODO.md 文件，或用扩展构建 |
| **Background bash** | 使用 tmux（完全可观察、直接交互） |

### 2. 四种运行模式

1. **Interactive** - 交互式终端模式
2. **Print/JSON** - 非交互式输出模式
3. **RPC** - 进程集成的 RPC 模式
4. **SDK** - 嵌入到自己应用的 SDK

### 3. 会话管理

- **存储格式**: JSONL 文件，带树形结构（每个条目有 `id` 和 `parentId`）
- **自动保存**: 保存到 `~/.pi/agent/sessions/`
- **分支导航**: `/tree` 在原地浏览和跳转到任意历史点
- **会话分叉**: `/fork` 从当前分支创建新会话
- **上下文压缩**: `/compact` 手动或自动压缩长会话

### 4. 扩展机制

#### Extensions（扩展）
TypeScript 模块，扩展 pi 的能力：
```typescript
export default function (pi: ExtensionAPI) {
  pi.registerTool({ name: "deploy", ... });
  pi.registerCommand("stats", { ... });
  pi.on("tool_call", async (event, ctx) => { ... });
}
```

**可用扩展点**:
- 自定义工具（或完全替换内置工具）
- 子代理和计划模式
- 自定义压缩和摘要
- 权限门控和路径保护
- 自定义编辑器和 UI 组件
- 状态行、页眉、页脚
- Git 检查点和自动提交
- SSH 和沙箱执行
- MCP 服务器集成
- 让 pi 看起来像 Claude Code
- 游戏（Doom 都能运行）

#### Skills（技能）
按 [Agent Skills 标准](https://agentskills.io) 的按需能力包：
```markdown
# My Skill
Use this skill when the user asks about X.

## Steps
1. Do this
2. Then that
```
通过 `/skill:name` 调用，或让 agent 自动加载。

#### Prompt Templates（提示模板）
可复用的 Markdown 提示，通过 `/name` 展开。

#### Themes（主题）
内置：`dark`、`light`，支持热重载。

#### Pi Packages
通过 npm 或 git 打包和分享扩展、技能、提示、主题。

---

## 内置工具

默认提供四个工具：`read`、`write`、`edit`、`bash`

```
--tools <list>     # 启用特定工具（默认: read,bash,edit,write）
--no-tools         # 禁用所有内置工具（扩展工具仍然有效）

可用: read, bash, edit, write, grep, find, ls
```

---

## 与 Aloha 对比

| 特性 | pi | Aloha |
|------|-----|-------|
| **架构** | Monorepo，多包结构 | 单体 Python 项目 |
| **语言** | TypeScript | Python |
| **UI** | TUI (pi-tui) + Web UI | Gradio |
| **扩展** | 完整的 Extension/Skill/Prompt/Theme 系统 | 基础工具注册 |
| **会话** | JSONL 树形结构 + 分支 + 压缩 | 基础 session memory |
| **无 MCP** | 用 Skills 替代 | 自己的工具系统 |
| **安全** | 依赖扩展实现 | 审批回调机制 |
| **多提供商** | 统一 API（支持 15+ 提供商） | 主要支持 OpenAI/MiniMax |
| **Stars** | 28,309 | N/A（自研） |

---

## 可借鉴设计

### 1. Monorepo 架构
- 将核心功能拆分为独立包：ai、agent、coding-agent、tui、web-ui
- 便于独立开发和版本管理

### 2. 统一 LLM API
- `pi-ai` 包提供统一的多提供商接口
- 支持 15+ 提供商（Anthropic, OpenAI, Google, Azure, etc.）

### 3. 扩展机制
- 完整的 Extension API（工具、命令、事件、UI）
- Skill 系统（按需加载的能力包）
- 热重载支持

### 4. 会话管理
- JSONL 树形结构存储
- 分支导航和分叉
- 上下文压缩（手动 + 自动）

### 5. "不包含" 哲学
- 核心保持极简
- 功能通过扩展实现
- 不强制用户接受预定义工作流

### 6. 集成示例
- 参考 OpenClaw 作为 SDK 集成示例

---

# 第五点五部分：pi-web-ui 技术方案详解

## 概述

`@mariozechner/pi-web-ui` 是基于 [mini-lit](https://github.com/badlogic/mini-lit) Web 组件和 Tailwind CSS v4 构建的可复用 Web UI 组件库。

## 技术栈

| 技术 | 说明 |
|------|------|
| **mini-lit** | 轻量级 Web 组件库（自定义） |
| **Tailwind CSS v4** | CSS 框架 |
| **IndexedDB** | 本地存储后端 |
| **TypeScript** | 开发语言 |

## 核心特性

1. **Chat UI** - 完整的聊天界面，支持消息历史、流式响应、工具执行
2. **Tools** - JavaScript REPL、文档提取、Artifacts（HTML, SVG, Markdown 等）
3. **Attachments** - PDF, DOCX, XLSX, PPTX, 图片的预览和文本提取
4. **Artifacts** - 交互式 HTML, SVG, Markdown，带沙箱执行
5. **Storage** - IndexedDB -backed 存储（会话、API keys、设置）
6. **CORS Proxy** - 浏览器环境自动代理
7. **Custom Providers** - 支持 Ollama, LM Studio, vLLM, OpenAI 兼容 API

## 架构

```
┌─────────────────────────────────────────────────────┐
│                    ChatPanel                        │
│  ┌─────────────────────┐  ┌─────────────────────┐   │
│  │   AgentInterface    │  │   ArtifactsPanel    │   │
│  │  (messages, input)  │  │  (HTML, SVG, MD)    │   │
│  └─────────────────────┘  └─────────────────────┘   │
└─────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────┐
│              Agent (from pi-agent-core)             │
│  - State management (messages, model, tools)        │
│  - Event emission (agent_start, message_update, ...)│
│  - Tool execution                                   │
└─────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────┐
│                   AppStorage                        │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐             │
│  │ Settings │ │ Provider │ │ Sessions │             │
│  │  Store   │ │Keys Store│ │  Store   │             │
│  └──────────┘ └──────────┘ └──────────┘             │
│                     │                               │
│              IndexedDBStorageBackend                │
└─────────────────────────────────────────────────────┘
```

## 核心组件

### 1. ChatPanel

高级聊天界面，内置 artifacts panel：

```typescript
const chatPanel = new ChatPanel();
await chatPanel.setAgent(agent, {
  onApiKeyRequired: async (provider) => ApiKeyPromptDialog.prompt(provider),
  onBeforeSend: async () => { /* ... */ },
  onCostClick: () => { /* ... */ },
  sandboxUrlProvider: () => chrome.runtime.getURL('sandbox.html'),
  toolsFactory: (agent, agentInterface, artifactsPanel, runtimeProvidersFactory) => {
    const replTool = createJavaScriptReplTool();
    return [replTool];
  },
});
```

### 2. AgentInterface

低级聊天接口，用于自定义布局：

```typescript
const chat = document.createElement('agent-interface') as AgentInterface;
chat.session = agent;
chat.enableAttachments = true;
chat.enableModelSelector = true;
chat.enableThinkingSelector = true;
```

### 3. Agent（来自 pi-agent-core）

Agent 核心类，负责状态管理和事件发射：

```typescript
const agent = new Agent({
  initialState: {
    model: getModel('anthropic', 'claude-sonnet-4-5-20250929'),
    systemPrompt: 'You are helpful.',
    thinkingLevel: 'off',
    messages: [],
    tools: [],
  },
  convertToLlm: defaultConvertToLlm,
});

// 事件订阅
agent.subscribe((event) => {
  switch (event.type) {
    case 'agent_start':
    case 'agent_end':
    case 'turn_start':
    case 'turn_end':
    case 'message_start':
    case 'message_update': // 流式更新
    case 'message_end':
      break;
  }
});

// 发送消息
await agent.prompt('Hello!');
await agent.prompt({ role: 'user-with-attachments', content: '...', attachments, timestamp: Date.now() });
```

## 存储系统

### IndexedDBStorageBackend

```typescript
const backend = new IndexedDBStorageBackend({
  dbName: 'my-app',
  version: 1,
  stores: [
    settings.getConfig(),
    providerKeys.getConfig(),
    sessions.getConfig(),
    SessionsStore.getMetadataConfig(),
    customProviders.getConfig(),
  ],
});
```

### Store 分类

| Store | 用途 |
|-------|------|
| **SettingsStore** | 键值设置（代理、CORS 等） |
| **ProviderKeysStore** | 各提供商 API keys |
| **SessionsStore** | 聊天会话（支持元数据、分页） |
| **CustomProvidersStore** | 自定义 LLM 提供商 |

## 消息类型

### 1. UserMessageWithAttachments

带附件的用户消息：

```typescript
const message: UserMessageWithAttachments = {
  role: 'user-with-attachments',
  content: 'Analyze this document',
  attachments: [pdfAttachment],
  timestamp: Date.now(),
};
```

### 2. ArtifactMessage

Artifacts 持久化：

```typescript
const artifact: ArtifactMessage = {
  role: 'artifact',
  action: 'create', // or 'update', 'delete'
  filename: 'chart.html',
  content: '<div>...</div>',
  timestamp: new Date().toISOString(),
};
```

### 3. 自定义消息类型

通过声明合并扩展：

```typescript
interface SystemNotification {
  role: 'system-notification';
  message: string;
  level: 'info' | 'warning' | 'error';
  timestamp: string;
}

declare module '@mariozechner/pi-agent-core' {
  interface CustomAgentMessages {
    'system-notification': SystemNotification;
  }
}

registerMessageRenderer('system-notification', {
  render: (msg) => html`<div class="alert">${msg.message}</div>`,
});
```

## 内置工具

### 1. JavaScript REPL

沙箱环境执行 JavaScript：

```typescript
const replTool = createJavaScriptReplTool();
replTool.runtimeProvidersFactory = () => [
  new AttachmentsRuntimeProvider(attachments),
  new ArtifactsRuntimeProvider(artifactsPanel, agent, true),
];
agent.setTools([replTool]);
```

### 2. Extract Document

从 URL 提取文档文本：

```typescript
const extractTool = createExtractDocumentTool();
extractTool.corsProxyUrl = 'https://corsproxy.io/?';
agent.setTools([extractTool]);
```

### 3. Artifacts Tool

内置于 ArtifactsPanel，支持：HTML, SVG, Markdown, text, JSON, images, PDF, DOCX, XLSX

## 附件支持

```typescript
import { loadAttachment, type Attachment } from '@mariozechner/pi-web-ui';

// 支持：File, URL, ArrayBuffer
const attachment = await loadAttachment(file);
const attachment = await loadAttachment('https://example.com/doc.pdf');
const attachment = await loadAttachment(arrayBuffer, 'document.pdf');

// 支持格式：PDF, DOCX, XLSX, PPTX, images, text files
```

## 对话框

| 对话框 | 用途 |
|--------|------|
| **SettingsDialog** | 设置（提供商、代理、API keys） |
| **SessionListDialog** | 会话列表浏览和选择 |
| **ApiKeyPromptDialog** | API key 提示输入 |
| **ModelSelector** | 模型选择 |

## 国际化

```typescript
import { i18n, setLanguage, translations } from '@mariozechner/pi-web-ui';

translations.de = {
  'Loading...': 'Laden...',
  'No sessions yet': 'Noch keine Sitzungen',
};

setLanguage('de');
console.log(i18n('Loading...')); // "Laden..."
```

## 与 Aloha 对比

| 特性 | pi-web-ui | Aloha (Gradio) |
|------|-----------|----------------|
| **架构** | 模块化 Web 组件 | 整体 Gradio 块 |
| **状态管理** | pi-agent-core 统一管理 | 自定义 session memory |
| **存储** | IndexedDB 本地存储 | 无持久化 |
| **UI 组件** | mini-lit 自定义 | Gradio 内置 |
| **流式响应** | 事件驱动 | Gradio 内置 |
| **样式** | Tailwind CSS | Gradio 主题 |
| **扩展性** | 完整的消息/工具/渲染器扩展 | 基础工具注册 |

## 可借鉴设计

1. **事件驱动的流式更新** - Agent 事件订阅模式
2. **IndexedDB 本地存储** - 会话持久化
3. **模块化组件** - ChatPanel / AgentInterface / ArtifactsPanel 分离
4. **附件处理** - 统一的附件加载和预览
5. **自定义消息类型** - 声明合并扩展机制
6. **工具渲染器** - 可插拔的工具 UI

---

# 第六部分：pi-agent-core 技术方案详解

## 概述

`@mariozechner/pi-agent-core` 是基于 `@mariozechner/pi-ai` 构建的带状态管理的 Agent，包含工具执行和事件流。

## 核心概念

### AgentMessage vs LLM Message

- **AgentMessage**：灵活的类型，支持标准 LLM 消息（user, assistant, toolResult）和自定义消息类型
- **LLM Message**：LLM 只理解 user, assistant, toolResult
- **convertToLlm**：桥接函数，在每次 LLM 调用前过滤和转换消息

### 消息流程

```
AgentMessage[] → transformContext() → AgentMessage[] → convertToLlm() → Message[] → LLM
                    (optional)                           (required)
```

1. **transformContext**：剪枝旧消息，注入外部上下文
2. **convertToLlm**：过滤 UI -only 消息，转换自定义类型

## 事件流

### prompt() 事件序列

```
prompt("Hello")
├─ agent_start
├─ turn_start
├─ message_start   { message: userMessage }      // 你的 prompt
├─ message_end     { message: userMessage }
├─ message_start   { message: assistantMessage } // LLM 开始响应
├─ message_update  { message: partial... }       // 流式片段
├─ message_update  { message: partial... }
├─ message_end     { message: assistantMessage } // 完成响应
├─ turn_end        { message, toolResults: [] }
└─ agent_end       { messages: [...] }
```

### 带工具调用

```
prompt("Read config.json")
├─ agent_start
├─ turn_start
├─ message_start/end  { userMessage }
├─ message_start      { assistantMessage with toolCall }
├─ message_update...
├─ message_end        { assistantMessage }
├─ tool_execution_start  { toolCallId, toolName, args }
├─ tool_execution_update { partialResult }           // 如果工具流式输出
├─ tool_execution_end    { toolCallId, result }
├─ message_start/end  { toolResultMessage }
├─ turn_end           { message, toolResults: [toolResult] }
│
├─ turn_start                                        // 下一轮
├─ message_start      { assistantMessage }           // LLM 响应工具结果
├─ message_update...
├─ message_end
├─ turn_end
└─ agent_end
```

### 工具执行模式

- **parallel**（默认）：按顺序预检工具调用，并发执行允许的工具，按助手顺序发出最终结果
- **sequential**：逐个执行工具调用

### Hooks

- **beforeToolCall**：工具执行前运行，可以阻止执行
- **afterToolCall**：工具执行完成后，最终工具事件发出前运行

### continue() 事件序列

`continue()` 从现有上下文继续，用于错误后重试。最后一条消息必须是 user 或 toolResult（不是 assistant）。

### 事件类型

| 事件 | 说明 |
|------|------|
| `agent_start` | Agent 开始处理 |
| `agent_end` | Agent 完成，包含所有新消息 |
| `turn_start` | 新一轮开始（一次 LLM 调用 + 工具执行） |
| `turn_end` | 轮次完成，包含助手消息和工具结果 |
| `message_start` | 任何消息开始（user, assistant, toolResult） |
| `message_update` | **仅助手。** 包含 `assistantMessageEvent` 带 delta |
| `message_end` | 消息完成 |
| `tool_execution_start` | 工具开始 |
| `tool_execution_update` | 工具流式输出进度 |
| `tool_execution_end` | 工具完成 |

## Agent 选项

```typescript
const agent = new Agent({
  // 初始状态
  initialState: {
    systemPrompt: string,
    model: Model<any>,
    thinkingLevel: "off" | "minimal" | "low" | "medium" | "high" | "xhigh",
    tools: AgentTool<any>[],
    messages: AgentMessage[],
  },

  // 转换 AgentMessage[] 到 LLM Message[]（自定义消息类型必需）
  convertToLlm: (messages) => messages.filter(...),

  // convertToLlm 前转换上下文（用于剪枝、压缩）
  transformContext: async (messages, signal) => pruneOldMessages(messages),

  // 转向模式："one-at-a-time"（默认）或 "all"
  steeringMode: "one-at-a-time",

  // 跟进模式："one-at-a-time"（默认）或 "all"
  followUpMode: "one-at-a-time",

  // 自定义流函数（用于代理后端）
  sessionId: "session-123",

  // 动态 API key 解析（用于过期 OAuth tokens）
  getApiKey: async (provider) => refreshToken(),

  // 工具执行模式："parallel"（默认）或 "sequential"
  toolExecution: "parallel",

  // 预检每个工具调用（在参数验证后）。可以阻止执行。
  beforeToolCall: async ({ toolCall, args, context }) => {
    if (toolCall.name === "bash") {
      return { block: true, reason: "bash is disabled" };
    }
  },

  // 后处理每个工具结果，在最终工具事件发出前。
  afterToolCall: async ({ toolCall, result, isError, context }) => {
    if (!isError) {
      return { details: { ...result.details, audited: true } };
    }
  },

  // 自定义 token-based 提供商的思考预算
  thinkingBudgets: {
    minimal: 128,
    low: 512,
    medium: 1024,
    high: 2048,
  },
});
```

## Agent 状态

```typescript
interface AgentState {
  systemPrompt: string;
  model: Model<any>;
  thinkingLevel: ThinkingLevel;
  tools: AgentTool<any>[];
  messages: AgentMessage[];
  isStreaming: boolean;
  streamMessage: AgentMessage | null;  // 流式期间的当前部分
  pendingToolCalls: Set<string>;
  error?: string;
}
```

## 核心方法

### 提示

```typescript
// 文本提示
await agent.prompt("Hello");

// 带图片
await agent.prompt("What's in this image?", [
  { type: "image", data: base64Data, mimeType: "image/jpeg" }
]);

// 直接使用 AgentMessage
await agent.prompt({ role: "user", content: "Hello", timestamp: Date.now() });

// 从当前上下文继续（最后消息必须是 user 或 toolResult）
await agent.continue();
```

### 状态管理

```typescript
agent.setSystemPrompt("New prompt");
agent.setModel(getModel("openai", "gpt-4o"));
agent.setThinkingLevel("medium");
agent.setTools([myTool]);
agent.setToolExecution("sequential");
agent.setBeforeToolCall(async ({ toolCall }) => undefined);
agent.setAfterToolCall(async ({ toolCall, result }) => undefined);
agent.replaceMessages(newMessages);
agent.appendMessage(message);
agent.clearMessages();
agent.reset();  // 清除一切
```

### 控制

```typescript
agent.abort();           // 取消当前操作
await agent.waitForIdle(); // 等待完成
```

## 转向（Steering）和跟进（Follow-up）

转向消息让你在工具运行时中断 Agent。跟进消息让你在 Agent 停止后排队工作。

```typescript
agent.setSteeringMode("one-at-a-time");
agent.setFollowUpMode("one-at-a-time");

// Agent 运行时
agent.steer({
  role: "user",
  content: "Stop! Do this instead.",
  timestamp: Date.now(),
});

// Agent 完成后
agent.followUp({
  role: "user",
  content: "Also summarize the result.",
  timestamp: Date.now(),
});
```

检测到转向消息时：
1. 当前助手消息的所有工具调用已完成
2. 转向消息被注入
3. LLM 在下一轮响应

跟进消息只在没有更多工具调用和没有转向消息时检查。如果有排队，则注入并再运行一轮。

## 自定义消息类型

通过声明合并扩展 `AgentMessage`：

```typescript
declare module "@mariozechner/pi-agent-core" {
  interface CustomAgentMessages {
    notification: { role: "notification"; text: string; timestamp: number };
  }
}

// 现在有效
const msg: AgentMessage = { role: "notification", text: "Info", timestamp: Date.now() };
```

在 `convertToLlm` 中处理自定义类型：

```typescript
const agent = new Agent({
  convertToLlm: (messages) => messages.flatMap(m => {
    if (m.role === "notification") return []; // 过滤掉
    return [m];
  }),
});
```

## 工具定义

使用 `AgentTool` 定义工具：

```typescript
import { Type } from "@sinclair/typebox";

const readFileTool: AgentTool = {
  name: "read_file",
  label: "Read File",  // UI 显示
  description: "Read a file's contents",
  parameters: Type.Object({
    path: Type.String({ description: "File path" }),
  }),
  execute: async (toolCallId, params, signal, onUpdate) => {
    const content = await fs.readFile(params.path, "utf-8");

    // 可选：流式输出进度
    onUpdate?.({ content: [{ type: "text", text: "Reading..." }], details: {} });

    return {
      content: [{ type: "text", text: content }],
      details: { path: params.path, size: content.length },
    };
  },
};

agent.setTools([readFileTool]);
```

### 错误处理

**工具失败时抛出错误**，不要返回错误消息作为内容：

```typescript
execute: async (toolCallId, params, signal, onUpdate) => {
  if (!fs.existsSync(params.path)) {
    throw new Error(`File not found: ${params.path}`);
  }
  // 只在成功时返回内容
  return { content: [{ type: "text", text: "..." }] };
}
```

抛出的错误被 Agent 捕获，以 `isError: true` 报告给 LLM 作为工具错误。

## 低级 API

不使用 Agent 类，直接控制：

```typescript
import { agentLoop, agentLoopContinue } from "@mariozechner/pi-agent-core";

const context: AgentContext = {
  systemPrompt: "You are helpful.",
  messages: [],
  tools: [],
};

const config: AgentLoopConfig = {
  model: getModel("openai", "gpt-4o"),
  convertToLlm: (msgs) => msgs.filter(m => ["user", "assistant", "toolResult"].includes(m.role)),
  toolExecution: "parallel",
  beforeToolCall: async ({ toolCall, args, context }) => undefined,
  afterToolCall: async ({ toolCall, result, isError, context }) => undefined,
};

const userMessage = { role: "user", content: "Hello", timestamp: Date.now() };

for await (const event of agentLoop([userMessage], context, config)) {
  console.log(event.type);
}

// 从现有上下文继续
for await (const event of agentLoopContinue(context, config)) {
  console.log(event.type);
}
```

> 注意：这些低级流是观察性的。它们保留事件顺序，但不会等待异步事件处理完成后才继续后续生产阶段。如果需要消息处理作为工具预检的屏障，使用 `Agent` 类而不是原始的 `agentLoop()` 或 `agentLoopContinue()`。

## 与 Aloha 对比

| 特性 | pi-agent-core | Aloha (自定义) |
|------|---------------|----------------|
| **状态管理** | 完整的 AgentState | 基础 session memory |
| **事件系统** | 完整的事件流（11 种事件） | 无 |
| **工具执行** | parallel/sequential + hooks | 基础执行 |
| **消息转换** | convertToLlm 桥接 | 无 |
| **上下文压缩** | transformContext | 无 |
| **转向/跟进** | 内置支持 | 无 |
| **思考级别** | 内置支持 | 无 |
| **错误处理** | 异常统一处理 | 基础 |

## 可借鉴设计

1. **事件驱动架构** - 完整的事件流（agent_start, message_update, tool_execution 等）
2. **AgentMessage 桥接** - convertToLlm 机制支持自定义消息类型
3. **transformContext** - 上下文压缩和剪枝
4. **beforeToolCall/afterToolCall Hooks** - 工具执行前后的拦截
5. **parallel/sequential 执行模式** - 灵活的工具执行策略
6. **Steering/Follow-up** - 运行时的消息注入机制
7. **Thinking Levels** - 内置的思考预算控制
8. **Low-Level API** - agentLoop() 供高级用户使用

---

## 是否适合作为基础？

**作为基础的可能性**：中等

**理由**：

✅ **优势**：
- 成熟的代码结构和扩展机制
- 丰富的多提供商支持
- 大社区（28k+ stars）

⚠️ **挑战**：
- TypeScript → 如果想用 Python 需要重写
- 极简设计意味着很多功能需要自己实现
- 安全控制需要自己构建（pi 不包含）

**建议**：
- 可以借鉴其架构设计理念
- 参考其扩展机制实现 Aloha 的扩展系统
- 会话管理机制可以直接学习
- 不需要完全基于 pi 重写，Aloha 可以保持 Python 路线，吸收其设计思想