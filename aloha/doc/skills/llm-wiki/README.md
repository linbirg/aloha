# llm-wiki

以 OpenCode 为引擎的 LLM Wiki 知识管理系统。

受 [Karpathy 的 LLM Wiki 模式](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) 启发，用 OpenCode Skill 实现——让 LLM 作为知识库的唯一维护者，人只负责"投喂原料"和"提出好问题"。

## 核心思想

```
Raw Sources（只读）→ Wiki（LLM 维护）→ Schema（行为规范）
```

- **人不碰 Wiki**：Wiki 是 LLM 的领地，人只读不写
- **先编译再查询**：把资料整理成结构化 Wiki，再也不用每次从零发现知识
- **回填飞轮**：Query 的回答可以沉淀回 Wiki，知识越问越多

## 快速开始

### 1. 安装

将 `SKILL.md` 放入 OpenCode Skills 目录：

```bash
mkdir -p ~/.config/opencode/skills/llm-wiki/
# 将本仓库的 SKILL.md 复制到上述目录
```

### 2. 初始化 Wiki 目录

在任意目录下创建 `_raw/` 和 `_wiki/` 结构：

```
doc/obsidian/
├── _raw/
│   ├── sources/          ← 原始资料（append-only）
│   └── registry.md       ← 编译状态追踪
└── _wiki/
    ├── index.md          ← 全局索引
    ├── log.md            ← 时间线日志
    ├── entities/         ← 实体页
    ├── concepts/         ← 概念页
    ├── summaries/        ← 摘要页
    └── tags/             ← 标签索引
```

### 3. 投入 Raw Sources

将 Markdown 文章、网页 URL、PDF 文件放入 `_raw/sources/`。

### 4. 编译为 Wiki

```
/llm-wiki ingest <path>    # 登记新资料
/llm-wiki compile           # 编译为 Wiki 页面
```

LLM 自动：
- 提取实体 → `entities/{name}.md`
- 提取概念 → `concepts/{name}.md`
- 生成摘要 → `summaries/{name}-summary.md`
- 自动打标签 + 建立双向链接
- 生成/更新 `tags/` 索引页

### 5. 查询知识库

```
/llm-wiki query <你的问题>
```

LLM 先读 `index.md` 定位相关页面，再综合回答。优质回答会自动建议回填，确认后写入 Wiki。

### 6. 健康检查

```
/llm-wiki lint    # 修复断链、检测矛盾、清理孤立页面
/llm-wiki status  # 查看仪表盘
/llm-wiki log    # 查看操作记录
```

## 命令参考

| 命令 | 说明 |
|------|------|
| `/llm-wiki ingest <path>` | 登记文件/目录/URL 到 Raw Sources |
| `/llm-wiki compile` | 将所有 pending 资料编译为 Wiki 页面 |
| `/llm-wiki query <question>` | 跨 Wiki 综合回答，自动判断是否值得回填 |
| `/llm-wiki status` | 显示统计仪表盘 |
| `/llm-wiki lint` | 健康检查：断链修复、矛盾检测、孤立页面处理 |
| `/llm-wiki log` | 查看最近操作记录 |

## 目录结构

```
_wiki/                    ← LLM 全权维护
  index.md              ← 全局索引（先读这个了解 Wiki 全貌）
  log.md                ← append-only 操作日志
  entities/             ← 实体页（项目、产品、技术栈）
  concepts/             ← 概念页（设计模式、架构思想）
  summaries/           ← 摘要页（每篇 Raw Source 对应一篇）
  tags/                 ← 标签索引（按标签聚合页面）

_raw/                   ← Raw Sources（append-only）
  sources/             ← 原始资料文件
  registry.md          ← 编译状态追踪（pending / compiled / error）
```

## Wiki 页面规范

每个 Wiki 页面包含 YAML frontmatter：

```yaml
---
title: 项目名称
type: entity | concept | summary
tags: [agent, memory, llm]
created: 2026-04-06
updated: 2026-04-06
sources: [source-file-1]
summary: 一句话描述，不超过 50 字
---
```

**命名约定**：

| 类型 | 格式 | 示例 |
|------|------|------|
| 实体页 | `entities/{name}.md` | `entities/hermes-agent.md` |
| 概念页 | `concepts/{name}.md` | `concepts/tool-call-loop.md` |
| 摘要页 | `summaries/{name}-summary.md` | `summaries/hermes-agent-analysis-summary.md` |
| 标签页 | `tags/{tag}.md` | `tags/agent.md` |

**双向链接**：在 `## 相关链接` 章节用 `[[page-name]]` 语法建立关联，Obsidian 自动渲染为可点击链接。

## Auto-tagging

LLM 根据内容自动判断标签，写入 frontmatter，不人工确认。常用标签：`agent`、`memory`、`llm`、`tool`、`skill`、`security`。

## 回填飞轮

Query 的回答如果满足以下条件之一，会自动建议回填：

- 多源综合（引用 ≥2 个 Wiki 页面）
- 包含 LLM 推理而非简单摘录
- 有长期参考价值
- 与现有 Wiki 页面不重复

确认后，回答会作为新页面写入 Wiki，使知识库**不只靠丢新资料增长，也靠问问题增长**。

## 与 RAG 的区别

| | 传统 RAG | LLM Wiki |
|--|----------|----------|
| 每次查询 | 从零检索原文 | 已有结构化 Wiki 可查 |
| 积累 | 留在聊天记录里 | 回填到 Wiki 持续沉淀 |
| 知识关联 | 临时发现 | 双向链接固化 |
| 维护 | 人维护 | LLM 自动维护 |

## 技术细节

- **引擎**：OpenCode（支持 75+ LLM providers）
- **存储**：纯 Markdown 文件，无数据库依赖
- **索引**：YAML frontmatter + Obsidian 双向链接
- **增量编译**：通过 `registry.md` 追踪编译状态，不重复处理已编译 source
- **Skill 格式**：标准 OpenCode SKILL.md

## 致谢

- [Karpathy - LLM Wiki gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)
- [Vannevar Bush - As We May Think (1945)](https://www.theatlantic.com/magazine/archive/1945/07/as-we-may-think/303881/)

> "人的角色从'整理者'变成'提问者'。"
