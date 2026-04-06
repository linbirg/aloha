# OpenCode 使用手册

## 目录

1. [概述](#概述)
2. [安装](#安装)
3. [快速开始](#快速开始)
4. [配置](#配置)
5. [TUI 界面](#tui-界面)
6. [命令行工具](#命令行工具)
7. [Agent 系统](#agent-系统)
8. [Skills 技能系统](#skills-技能系统)
9. [自定义命令](#自定义命令)
10. [Provider 配置](#provider-配置)
11. [主题配置](#主题配置)
12. [权限管理](#权限管理)
13. [会话共享](#会话共享)
14. [环境变量](#环境变量)
15. [常见问题](#常见问题)

---

## 概述

OpenCode 是一个开源的 AI 编程助手，支持 75+ LLM providers，包括 Claude、GPT、Gemini 等。支持多种使用方式：终端界面(TUI)、命令行、Web、IDE 扩展。

**特点**：
- 多 provider 支持
- 多 session 管理
- Git 集成（undo/redo）
- 自定义 Agent 和 Skills
- 权限审批系统
- 会话共享

---

## 安装

### Linux/macOS

```bash
curl -fsSL https://opencode.ai/install | bash
```

或使用 npm/bun/pnpm：

```bash
npm install -g opencode-ai
# 或
bun install -g opencode-ai
# 或
pnpm install -g opencode-ai
```

### Homebrew

```bash
brew install anomalyco/tap/opencode
```

### Windows

推荐使用 WSL 以获得最佳体验。

```powershell
# Chocolatey
choco install opencode

# Scoop
scoop install opencode

# NPM
npm install -g opencode-ai
```

---

## 快速开始

### 1. 连接 Provider

运行 OpenCode 后，使用 `/connect` 命令连接 LLM provider：

```
/connect
```

选择你想要的 provider（OpenCode Zen、Anthropic、OpenAI 等），输入 API key。

### 2. 初始化项目

进入项目目录并运行：

```bash
cd /path/to/project
opencode
/init
```

这会分析项目结构并创建 `AGENTS.md` 文件。

### 3. 开始对话

直接在 TUI 中输入你的问题或任务：

```
解释这段代码的作用 @src/auth/login.ts
```

使用 `@` 引用文件，使用 `!` 运行 shell 命令。

---

## 配置

### 配置文件位置

配置文件按优先级从低到高排列：

1. **远程配置** (`.well-known/opencode`) - 组织默认配置
2. **全局配置** (`~/.config/opencode/opencode.json`) - 用户偏好
3. **自定义配置** (`OPENCODE_CONFIG` 环境变量)
4. **项目配置** (`opencode.json` 在项目根目录)
5. **`.opencode` 目录** - agents、commands、plugins
6. **内联配置** (`OPENCODE_CONFIG_CONTENT` 环境变量)

### 配置格式

支持 JSON 和 JSONC（带注释的 JSON）：

```jsonc
{
  "$schema": "https://opencode.ai/config.json",
  "model": "anthropic/claude-sonnet-4-5",
  "autoupdate": true,
  "server": {
    "port": 4096
  }
}
```

### 常用配置项

| 配置项 | 说明 |
|--------|------|
| `model` | 默认使用的模型，格式：`provider/model` |
| `small_model` | 轻量任务用的模型 |
| `autoupdate` | 自动更新（默认 true） |
| `share` | 共享模式：`manual`、`auto`、`disabled` |
| `snapshot` | 是否启用快照（默认 true，用于 undo/redo） |
| `default_agent` | 默认 agent：`build` 或 `plan` |

### TUI 配置

TUI 专用配置放在 `~/.config/opencode/tui.json`：

```json
{
  "$schema": "https://opencode.ai/tui.json",
  "theme": "tokyonight",
  "scroll_speed": 3,
  "diff_style": "auto"
}
```

---

## TUI 界面

### 基本操作

启动 TUI：

```bash
opencode
# 或指定目录
opencode /path/to/project
```

### 文件引用

使用 `@` 模糊搜索并引用文件：

```
How is auth handled in @packages/functions/src/api/index.ts?
```

### Bash 命令

以 `!` 开头执行 shell 命令：

```
!ls -la
!git status
```

### 常用命令

| 命令          | 说明             | 快捷键        |
| ----------- | -------------- | ---------- |
| `/connect`  | 添加 provider    |            |
| `/init`     | 初始化项目          | `Ctrl+x i` |
| `/help`     | 显示帮助           | `Ctrl+x h` |
| `/new`      | 新会话            | `Ctrl+x n` |
| `/undo`     | 撤销上条消息及更改      | `Ctrl+x u` |
| `/redo`     | 重做             | `Ctrl+x r` |
| `/share`    | 共享会话           | `Ctrl+x s` |
| `/compact`  | 压缩会话上下文        | `Ctrl+x c` |
| `/models`   | 列出可用模型         | `Ctrl+x m` |
| `/themes`   | 切换主题           | `Ctrl+x t` |
| `/sessions` | 会话管理           | `Ctrl+x l` |
| `/export`   | 导出会话为 Markdown | `Ctrl+x x` |
| `/editor`   | 使用外部编辑器        | `Ctrl+x e` |

### Agent 切换

按 `Tab` 键在 Build 和 Plan agent 之间切换。

### 文件导航

在子 agent 创建的会话中：
- `session_child_first`（默认 `Leader+Down`）进入第一个子会话
- `session_child_cycle`（默认 `Right`）循环到下一个子会话
- `session_parent`（默认 `Up`）返回父会话

---

## 命令行工具

### 基本命令

```bash
opencode                           # 启动 TUI
opencode run "你的问题"            # 非交互模式
opencode run --continue            # 继续上次会话
opencode serve                     # 启动 API 服务器
opencode web                       # 启动 Web 界面
```

### 子命令

```bash
# Agent 管理
opencode agent list                # 列出所有 agent
opencode agent create              # 创建新 agent

# Auth 管理
opencode auth login                # 登录 provider
opencode auth list                 # 列出已登录 provider
opencode auth logout               # 登出

# MCP 服务器
opencode mcp add                   # 添加 MCP 服务器
opencode mcp list                  # 列出 MCP 服务器

# 会话管理
opencode session list             # 列出所有会话
opencode stats                     # 显示 token 使用统计

# 模型
opencode models                    # 列出可用模型
opencode models anthropic          # 列出特定 provider 的模型
```

### 全局选项

```bash
opencode --help                    # 显示帮助
opencode --version                 # 显示版本
opencode --print-logs              # 打印日志到 stderr
```

---

## Agent 系统

### Agent 类型

1. **Primary Agent** - 主要交互 agent
   - `build`：默认 agent，所有工具可用
   - `plan`：受限 agent，仅分析不修改

2. **Subagent** - 子 agent
   - `general`：通用任务执行
   - `explore`：快速代码探索（只读）

### 切换 Agent

- Primary Agent：按 `Tab` 键
- Subagent：在消息中 `@mention`

```
@explore 搜索这个函数的定义
```

### 自定义 Agent

通过 JSON 配置：

```json
{
  "agent": {
    "code-reviewer": {
      "description": "代码审查 agent",
      "mode": "subagent",
      "model": "anthropic/claude-sonnet-4-5",
      "prompt": "你是一个代码审查员...",
      "tools": {
        "write": false,
        "edit": false
      }
    }
  }
}
```

或通过 Markdown 文件（`~/.config/opencode/agents/review.md`）：

```markdown
---
description: 代码审查 agent
mode: subagent
tools:
  write: false
  edit: false
  bash: false
---
你是一个代码审查员。专注于：
- 代码质量和最佳实践
- 潜在的 bug 和边界情况
- 性能影响
```

### Agent 选项

| 选项 | 说明 |
|------|------|
| `description` | Agent 描述（必填） |
| `mode` | `primary`、`subagent`、`all` |
| `model` | 使用的模型 |
| `prompt` | 系统提示词文件 |
| `temperature` | 随机性（0.0-1.0） |
| `steps` | 最大迭代次数 |
| `permission` | 权限配置 |
| `hidden` | 隐藏子 agent（不在 @ 补全中显示） |

---

## Skills 技能系统

Skills 允许你定义可复用的行为规范，agent 可以按需加载。

### 文件位置

```
~/.config/opencode/skills/<name>/SKILL.md    # 全局
.opencode/skills/<name>/SKILL.md            # 项目级
~/.claude/skills/<name>/SKILL.md            # Claude 兼容
.agents/skills/<name>/SKILL.md              # Agent 兼容
```

### SKILL.md 格式

```markdown
---
name: git-release
description: 创建一致的发布和变更日志
license: MIT
compatibility: opencode
metadata:
  audience: maintainers
  workflow: github
---

## 何时使用

当准备标签发布时使用此技能。

## 我做什么

- 从合并的 PR 草拟发布说明
- 建议版本号升级
- 提供可粘贴的 `gh release create` 命令
```

### 命名规则

- 1-64 个字符
- 小写字母和数字，单个连字符分隔
- 不以 `-` 开头或结尾
- 不含连续 `--`

### 权限配置

```json
{
  "permission": {
    "skill": {
      "*": "allow",
      "pr-review": "allow",
      "internal-*": "deny",
      "experimental-*": "ask"
    }
  }
}
```

权限级别：`allow`（直接加载）、`deny`（隐藏）、`ask`（需批准）

### 禁用 Skill 工具

```json
{
  "agent": {
    "plan": {
      "tools": {
        "skill": false
      }
    }
  }
}
```

---

## 自定义命令

### 创建命令文件

创建 `.opencode/commands/test.md`：

```markdown
---
description: 运行测试并显示覆盖率
agent: build
model: anthropic/claude-3-5-sonnet-20241022
---

运行完整测试套件并显示覆盖率报告。
关注失败的测试并建议修复。
```

使用：`/test`

### 参数传递

使用 `$ARGUMENTS` 传递所有参数：

```markdown
---
description: 创建新组件
---
创建名为 $ARGUMENTS 的 React 组件
```

使用：`/component Button`

单个参数：`$1`、`$2`、`$3`...

### Shell 输出注入

使用 `` !`command` `` 注入命令输出：

```markdown
---
description: 分析测试覆盖率
---
当前测试结果：
!`npm test`

基于这些结果，建议提高覆盖率的改进。
```

### 配置文件定义

```json
{
  "command": {
    "test": {
      "template": "运行完整测试套件...",
      "description": "运行测试并显示覆盖率",
      "agent": "build"
    }
  }
}
```

---

## Provider 配置

### 支持的 Providers

75+ providers，包括：
- **云服务**：Anthropic、OpenAI、Google Vertex、Azure OpenAI
- **开源**：Ollama、LM Studio、llama.cpp
- **代理**：OpenRouter、Cloudflare AI Gateway、Vercel AI Gateway
- **国内**：MiniMax、Moonshot AI、DeepSeek、Z.AI

### 连接 Provider

```bash
/connect
```

或通过环境变量：

```bash
export ANTHROPIC_API_KEY=sk-xxx
export OPENAI_API_KEY=sk-xxx
```

### 自定义 Provider

添加 OpenAI 兼容 provider：

```json
{
  "provider": {
    "custom": {
      "npm": "@ai-sdk/openai-compatible",
      "name": "Custom Provider",
      "options": {
        "baseURL": "https://api.custom.com/v1"
      },
      "models": {
        "my-model": {
          "name": "My Model"
        }
      }
    }
  }
}
```

### 模型选择

```bash
/models                          # 列出所有模型
/models anthropic                # 列出特定 provider 的模型
/models --refresh                 # 刷新模型列表
```

### 默认模型

```json
{
  "model": "anthropic/claude-sonnet-4-5",
  "small_model": "anthropic/claude-haiku-4-5"
}
```

---

## 主题配置

### TUI 主题

在 `tui.json` 中设置：

```json
{
  "theme": "tokyonight"
}
```

可用主题：`opencode`、`tokyonight`、`catppuccin`、`github-dark` 等。

列出可用主题：

```bash
/themes
```

---

## 权限管理

### 权限级别

| 级别 | 说明 |
|------|------|
| `allow` | 允许所有操作，无需批准 |
| `ask` | 执行前请求用户批准 |
| `deny` | 禁用该工具 |

### 配置示例

全局配置：

```json
{
  "permission": {
    "edit": "ask",
    "bash": "ask"
  }
}
```

按 Agent 覆盖：

```json
{
  "agent": {
    "build": {
      "permission": {
        "edit": "allow"
      }
    }
  }
}
```

Bash 命令权限：

```json
{
  "permission": {
    "bash": {
      "*": "ask",
      "git status *": "allow",
      "git push": "ask"
    }
  }
}
```

---

## 会话共享

### 共享模式

```json
{
  "share": "manual"    // 默认，手动共享
  // "share": "auto"   // 自动共享所有新会话
  // "share": "disabled" // 禁用共享
}
```

### 共享会话

```bash
/share              # 生成共享链接并复制到剪贴板
/unshare            # 取消共享
```

### 隐私建议

- 只共享不包含敏感信息的会话
- 共享前检查会话内容
- 协作完成后及时取消共享
- 敏感项目建议禁用共享

---

## 环境变量

| 变量 | 说明 |
|------|------|
| `OPENCODE_CONFIG` | 自定义配置文件路径 |
| `OPENCODE_TUI_CONFIG` | 自定义 TUI 配置文件路径 |
| `OPENCODE_CONFIG_DIR` | 自定义配置目录 |
| `OPENCODE_CONFIG_CONTENT` | 内联 JSON 配置内容 |
| `OPENCODE_AUTO_SHARE` | 自动共享会话 |
| `OPENCODE_DISABLE_AUTOUPDATE` | 禁用自动更新 |
| `OPENCODE_DISABLE_PRUNE` | 禁用旧数据清理 |
| `OPENCODE_SERVER_PASSWORD` | API 服务器密码 |
| `OPENCODE_PERMISSION` | 内联权限配置 JSON |

### 实验性变量

| 变量 | 说明 |
|------|------|
| `OPENCODE_EXPERIMENTAL` | 启用所有实验性功能 |
| `OPENCODE_EXPERIMENTAL_ICON_DISCOVERY` | 启用图标发现 |
| `OPENCODE_EXPERIMENTAL_FILEWATCHER` | 启用文件监视器 |

---

## 常见问题

### Q: 如何禁用快照系统？

快照系统用于 undo/redo。在大仓库或有很多子模块的项目中会很慢。

```json
{
  "snapshot": false
}
```

**注意**：禁用后无法通过 UI 回滚更改。

### Q: 如何让 agent 只分析不修改？

使用 Plan agent（按 `Tab` 切换），或创建只读 agent：

```json
{
  "agent": {
    "read-only": {
      "mode": "subagent",
      "tools": {
        "write": false,
        "edit": false,
        "bash": false
      }
    }
  }
}
```

### Q: 如何使用本地模型？

配置 Ollama 或 llama.cpp：

```json
{
  "provider": {
    "ollama": {
      "npm": "@ai-sdk/openai-compatible",
      "options": {
        "baseURL": "http://localhost:11434/v1"
      },
      "models": {
        "llama2": {
          "name": "Llama 2"
        }
      }
    }
  }
}
```

### Q: 如何调试问题？

启用日志输出：

```bash
opencode --print-logs --log-level DEBUG
```

### Q: 如何升级 OpenCode？

```bash
opencode upgrade              # 升级到最新版本
opencode upgrade v0.1.48      # 升级到指定版本
```

### Q: 如何卸载？

```bash
opencode uninstall            # 卸载
opencode uninstall --keep-config   # 保留配置
opencode uninstall --dry-run       # 预览但不执行
```

---

## 附录

### 推荐模型

以下模型在代码生成和工具调用方面表现出色：

- GPT 5.2 / GPT 5.1 Codex
- Claude Opus 4.5 / Claude Sonnet 4.5
- MiniMax M2.1
- Gemini 3 Pro

### 相关资源

- [官网](https://opencode.ai)
- [GitHub](https://github.com/anomalyco/opencode)
- [文档](https://opencode.ai/docs)
- [Discord](https://opencode.ai/discord)
