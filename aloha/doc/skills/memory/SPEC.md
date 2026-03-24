# Roo Code 记忆功能 Skill 设计文档

## 概述

为 Roo Code 创建记忆功能 Skill，支持自动记忆代码风格、技术栈和项目结构。

## 需求汇总

| 需求项 | 选择 |
|--------|------|
| 存储方式 | Markdown 文件 |
| 持久化范围 | 当前会话 + 长期记忆（跨会话） |
| 调用方式 | 自动记忆（分析代码时自动提取） |
| 记忆内容 | 代码风格、技术栈、项目结构 |
| 存储位置 | 用户目录 ~/.roo/skills/memory/ |

## 触发规则

1. **自动加载**：新对话开始时自动读取长期记忆并显示
2. **自动更新**：用户每次保存代码文件后，自动分析并更新记忆
3. **手动指令**：
   - `/memory show` - 显示当前记忆
   - `/memory clear` - 清除会话记忆
   - `/memory save` - 将会话记忆合并到长期记忆

## 文件结构

```
~/.roo/skills/memory/
├── session.md      # 当前会话记忆（重启后清除）
├── longterm.md    # 长期记忆（跨会话持久化）
└── config.yaml    # 记忆配置
```

## 记忆内容模板

### session.md
```markdown
# 会话记忆 - [时间戳]

## 本次分析的代码特征
- 文件：[文件名]
- 语言：[语言类型]
- 风格：[观察到的风格]

## 临时备注
-
```

### longterm.md
```markdown
# 长期记忆

## 代码风格
- 命名规范：[snake_case / camelCase / PascalCase]
- 缩进：[2空格 / 4空格 / Tab]
- 注释风格：[中文 / 英文 / 无]
- 其他：

## 技术栈
- 编程语言：[Python / JavaScript / ...]
- 框架：[Django / React / ...]
- 库：[requests / lodash / ...]
- 工具：[pytest / jest / ...]

## 项目结构
- 入口文件：
- 模块组织：
- 配置文件：
- 目录结构：
  ```
  .
  ├── src/
  ├── tests/
  └── ...
  ```

## 用户偏好
- 测试框架：
- 代码规范：
- 其他：
```

## 实现方式

### Skill 结构
```
C:\Users\linbirg\.roo\skills\memory\
├── SKILL.md        # Skill 定义文件
└── scripts/
    ├── __init__.py
    ├── memory.py   # 记忆处理核心逻辑
    └── analyzer.py # 代码分析器
```

### 核心功能

1. **加载记忆** (`load_memory`)
   - 读取 `~/.roo/skills/memory/longterm.md`
   - 读取 `~/.roo/skills/memory/session.md`
   - 合并并显示给用户

2. **分析代码** (`analyze_code`)
   - 分析文件扩展名确定语言
   - 检测缩进风格（空格数/tab）
   - 检测命名规范
   - 提取 import 语句确定技术栈
   - 分析目录结构

3. **保存记忆** (`save_memory`)
   - 更新 session.md
   - 合并到 longterm.md

4. **手动指令**
   - `/memory show` → 调用 load_memory
   - `/memory clear` → 清空 session.md
   - `/memory save` → 合并会话到长期

## 配置 (config.yaml)

```yaml
memory:
  # 长期记忆文件路径
  longterm_path: ".roo/memory/longterm.md"
  # 会话记忆文件路径
  session_path: ".roo/memory/session.md"
  # 是否自动加载记忆
  auto_load: true
  # 是否自动保存
  auto_save: true
  # 忽略的文件模式
  ignore_patterns:
    - "*.min.js"
    - "*.pyc"
    - "__pycache__"
    - "node_modules"
```

## 待实现

- [ ] 创建 Skill 目录结构
- [ ] 实现 memory.py 核心逻辑
- [ ] 实现 analyzer.py 代码分析器
- [ ] 编写 SKILL.md 定义文件
- [ ] 创建初始配置文件

## 风险与限制

1. **准确性**：自动分析可能不完全准确，需要用户确认
2. **性能**：每次保存都分析可能影响性能，可通过配置调整
3. **冲突**：多用户同时编辑时可能存在冲突风险（当前版本不考虑）
