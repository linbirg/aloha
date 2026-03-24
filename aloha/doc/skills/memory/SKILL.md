---
name: memory
description: Roo Code 记忆功能 - 自动记住代码风格、技术栈和项目结构
---

# Memory Skill

## 概述

Roo Code 记忆功能，帮助 AI 记住代码风格、技术栈和项目偏好，提升代码生成的准确性。

## 功能特性

1. **自动记忆** - 分析代码文件时自动提取特征
2. **跨会话持久化** - 长期记忆跨会话保存
3. **手动指令** - 通过指令控制记忆操作

## 触发方式

### 手动指令

在对话中输入以下指令：

| 指令 | 功能 |
|------|------|
| `/memory show` | 显示当前所有记忆 |
| `/memory show longterm` | 仅显示长期记忆 |
| `/memory show session` | 仅显示会话记忆 |
| `/memory clear` | 清除会话记忆 |
| `/memory save` | 将会话记忆合并到长期记忆 |
| `/memory analyze <文件路径>` | 分析指定文件并更新记忆 |
| `/memory status` | 显示记忆状态和配置 |

### 自动触发

当配置启用时，以下情况会自动更新记忆：
- 用户保存代码文件后

## 记忆内容

### 长期记忆 (`.roo/memory/longterm.md`)

- 代码风格偏好（命名规范、缩进、注释）
- 技术栈（语言、框架、库）
- 项目结构
- 用户偏好

### 会话记忆 (`.roo/memory/session.md`)

- 本次会话分析的文件特征
- 临时备注
- 会话结束后可选合并到长期记忆

## 配置文件

位置: `~/.roo/skills/memory/config.yaml`（用户目录）

```yaml
memory:
  # 记忆文件路径（用户目录）
  longterm_path: "~/.roo/skills/memory/longterm.md"
  session_path: "~/.roo/skills/memory/session.md"

  # 自动功能开关
  auto_load: true   # 新对话开始时自动加载记忆
  auto_save: true   # 文件变更时自动更新记忆

  # 忽略的文件模式
  ignore_patterns:
    - "*.min.js"
    - "*.pyc"
    - "__pycache__"
    - "node_modules"
    - ".git"
```

## 使用示例

### 首次使用

```
用户: 分析这个项目的代码风格
AI:   正在分析项目代码...
      发现：
      - 语言：Python
      - 缩进：4 空格
      - 命名：snake_case
      - 框架：Django, NumPy
      已保存到会话记忆
```

### 后续对话

```
用户: 帮我写一个函数
AI:   根据记忆，您的代码风格偏好：
      - 使用 snake_case 命名
      - 4 空格缩进
      - 带中文注释
      开始生成代码...
```

### 手动保存

```
用户: /memory save
AI:   将会话记忆已合并到长期记忆
```

## 注意事项

1. 记忆文件保存在工作空间的 `.roo/memory/` 目录
2. 敏感信息不会被自动记录
3. 可通过编辑 Markdown 文件手动调整记忆内容

## 技术实现

- **存储**: Markdown 文件
- **分析器**: 支持 30+ 编程语言
- **自动检测**: 缩进风格、命名规范、导入语句、框架识别
