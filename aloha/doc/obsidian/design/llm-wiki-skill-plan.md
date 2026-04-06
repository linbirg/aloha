# LLM Wiki Skill 实现方案

**日期**：2026-04-06
**版本**：v1.0
**状态**：已确认，待开发

---

## 1. 目标概述

用 OpenCode Skill 实现 LLM Wiki 模式，以 OpenCode 为引擎，自动维护 Obsidian 研究资料的知识库。

**核心原则**：
- 多文档关联、标签管理完全由 LLM 自动完成，无需人工确认
- 渐进式披露：index + 页面摘要，支持先读摘要再深入详情
- Raw Sources 和 Wiki 输出共存于 `doc/obsidian/` 目录

---

## 2. 架构设计

```
doc/obsidian/                          ← Raw Sources + Wiki 共存
├── AI-Agent-Research/                 ← 研究资料（Raw Sources）
│   ├── llm-wiki-karpathy-analysis.md
│   ├── hermes-agent-analysis.md
│   └── mastra-loop-analysis.md
│
├── _wiki/                             ← LLM Wiki 层（生成）
│   ├── index.md                       ← 全局索引
│   ├── log.md                         ← 时间线日志
│   ├── entities/                      ← 实体页
│   │   ├── hermes.md
│   │   ├── mastra.md
│   │   └── pi-mono.md
│   ├── concepts/                      ← 概念页
│   │   ├── tool-call-loop.md
│   │   └── memory-system.md
│   ├── summaries/                    ← 摘要页
│   │   ├── hermes-summary.md
│   │   └── mastra-summary.md
│   └── tags/                          ← 标签索引
│       ├── agent.md
│       └── memory.md
│
└── .llm-wiki/                        ← Wiki 内部元数据
    └── schema.md                      ← Wiki 规范（LLM 的行为准则）
```

**目录约定**：
- `_wiki/` 目录为 LLM 生成，Raw Sources 不放此处
- `.llm-wiki/` 为 Wiki 内部文件（Obsidian 可配置排除）

---

## 3. Raw Sources vs Wiki 层划分

| 层级 | 来源 | LLM 操作 |
|------|------|---------|
| **Raw Sources** | 用户主动存入的研究资料（MD / PDF / 网页） | LLM 只读不写 |
| **Wiki 层** | LLM 根据 Raw Sources 自动生成和维护 | LLM 全权读写 |

---

## 4. Schema 设计（Wiki 行为准则）

文件：`.llm-wiki/schema.md`

### 4.1 Frontmatter 规范

每个 Wiki 页面必须包含 YAML frontmatter：

```yaml
---
title: 项目名称
type: entity | concept | summary
tags: [agent, memory, llm]
created: 2026-04-06
updated: 2026-04-06
sources: [llm-wiki-karpathy-analysis, hermes-agent-analysis]
summary: 一句话描述，不超过 50 字
---
```

### 4.2 页面结构规范

1. **摘要**（必须）：页面顶部 1-2 段，概括核心内容
2. **正文**：详细展开
3. **关联**：底部 `## 相关链接` 章节，链接相关实体/概念页

### 4.3 命名约定

| 类型 | 命名格式 | 示例 |
|------|---------|------|
| 实体页 | `{name}.md` | `hermes.md` |
| 概念页 | `{concept-name}.md` | `tool-call-loop.md` |
| 摘要页 | `{name}-summary.md` | `hermes-summary.md` |
| 标签页 | `{tag-name}.md` | `agent.md` |

### 4.4 Auto-tagging 规范

LLM 根据内容自动判断标签，写入 frontmatter 的 `tags` 字段，不人工确认。

常用标签：`agent` `memory` `llm` `tool` `skill` `security` `ui` `design`

### 4.5 Auto Cross-reference 规范

- 在 `## 相关链接` 章节使用 Obsidian 双向链接语法：`[[page-name]]`
- 每个实体/概念页至少 2 个出站链接

---

## 5. 三种操作

### 5.1 Ingest（新资料存入）

```
用户存入新研究资料（md / pdf / 网页 URL）
    ↓
OpenCode: /llm-wiki ingest <path>
    ↓
1. 读取资料，提取实体和概念
2. 在 entities/ 或 concepts/ 创建/更新页面
3. 生成/更新 summaries/{name}.md
4. 自动打标签（写入 frontmatter + 更新 tags/）
5. 自动建立双向链接（[[page-name]] 语法）
6. 更新 index.md
7. 追加 log.md
    ↓
输出：已创建/更新的页面列表
```

### 5.2 Query（Wiki 查询）

```
用户提问
    ↓
OpenCode: /llm-wiki query <question>
    ↓
1. 读取 index.md（了解 Wiki 全貌）
2. 定位相关实体/概念页（优先读摘要判断相关性）
3. 综合多页面内容回答（带引用）
4. 可选：将优质回答存为新的 Wiki 页面
    ↓
输出：综合回答 + 相关页面引用
```

### 5.3 Lint（健康检查）

```
定时触发 / 手动触发
    ↓
OpenCode: /llm-wiki lint
    ↓
1. 扫描孤立页面，建立关联
2. 检查矛盾声明
3. 更新 stale 摘要
4. 清理 index.md 失效引用
5. 报告到 log.md
    ↓
输出：健康报告 + 修复操作
```

---

## 6. OpenCode Skill 结构

```
aloha/skills/llm-wiki/
├── SKILL.md           ← Skill 入口
├── README.md          ← 使用说明
└── schema.md         ← Wiki 规范（LLM 行为准则）
```

**SKILL.md 核心内容**：

```markdown
# LLM Wiki Skill

## 触发方式

- `/llm-wiki ingest <path>` — 摄入新资料
- `/llm-wiki query <question>` — 在 Wiki 上回答问题
- `/llm-wiki lint` — 健康检查
- `/llm-wiki status` — 查看 Wiki 状态

## Wiki 根目录

`doc/obsidian/`

详细规范见同级目录下的 `schema.md`。
```

---

## 7. 实现路径（分阶段）

### 阶段一：基础框架（MVP）

**目标**：能用 `/llm-wiki ingest` 摄入一份 MD 研究资料，生成 Wiki 页面

1. 创建 `aloha/skills/llm-wiki/` 目录结构
2. 编写 `SKILL.md`（入口定义）
3. 编写 `schema.md`（Wiki 规范）
4. 实现 `/llm-wiki ingest`：
   - 读取 MD 文件
   - 提取实体（项目名、技术栈）
   - 生成 `entities/{name}.md`
   - 生成 `summaries/{name}.md`
   - 更新 `index.md`
   - 追加 `log.md`
5. 验证：手动 ingest 一篇现有文档（`llm-wiki-karpathy-analysis.md`）

### 阶段二：Auto-tagging + Cross-reference

**目标**：Ingest 时自动打标签 + 建立双向链接

1. 实现 auto-tagging（LLM 自动判断标签，写入 frontmatter）
2. 实现 auto cross-reference（使用 `[[links]]` 语法）
3. 实现 `tags/` 标签索引页自动生成

### 阶段三：Query 模式

**目标**：`/llm-wiki query` 能综合多个 Wiki 页面回答问题

1. 实现 `/llm-wiki query`
2. 优先读摘要判断相关性
3. 支持将优质回答存为新 Wiki 页面

### 阶段四：Lint 定期整理

**目标**：定期或手动触发 Wiki 健康检查

1. 实现 `/llm-wiki lint`
2. 配置定时触发（OpenCode 定时器 or 系统 cron）
3. 孤立页面检测 + 自动修复链接

### 阶段五：多格式支持

**目标**：支持 PDF、网页文章作为 Raw Sources

1. PDF 读取（提取文本）
2. 网页 URL（抓取转 MD）
3. `_raw/` 目录管理非 MD 原始资料

---

## 8. 关键技术决策

| 决策项 | 方案 | 理由 |
|--------|------|------|
| 搜索方案 | 阶段一用 `index.md` + 简单文本搜索 | 无需额外基础设施，够用 |
| Wiki 目录 | `_wiki/` 子目录隔离生成文件 | 避免污染 Raw Sources |
| 定时任务 | 优先 OpenCode 内置，否则系统 cron | 最简方案优先 |
| frontmatter | 使用 YAML frontmatter | Obsidian 原生支持 |

---

## 9. OpenCode Skill 文件清单

```
aloha/skills/llm-wiki/
├── SKILL.md           ← Skill 入口
├── README.md          ← 使用说明（推荐）
└── schema.md         ← Wiki 规范（必选）
```

---

## 10. 测试验证

| 阶段 | 测试内容 |
|------|---------|
| 阶段一 | ingest 一篇文档，验证 entities + summaries + index + log 正确生成 |
| 阶段二 | ingest 两篇关联文档，验证 auto-tag + cross-reference 正确 |
| 阶段三 | query 跨多个实体的问题，验证回答有引用 |
| 阶段四 | 运行 lint，验证孤立页面被处理 |
| 阶段五 | ingest PDF + 网页 URL，验证多格式支持 |

---

## 11. 待确认事项

- [ ] OpenCode Skill 是否支持嵌套目录结构
- [ ] OpenCode Skill 的系统 prompt 是否支持引用同级其他文件（`schema.md`）
- [ ] OpenCode 定时器是否支持（触发 `/llm-wiki lint` 定期执行）
