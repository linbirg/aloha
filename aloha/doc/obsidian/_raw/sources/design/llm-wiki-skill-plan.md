# LLM Wiki Skill 实现方案

**日期**：2026-04-06
**版本**：v3.0
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
~/.config/opencode/skills/llm-wiki/         ← OpenCode Skill（触发入口）
└── SKILL.md                                  ← 包含完整 schema + 所有 sub-command 定义

/mnt/d/work/linbirg/aloha-agent/aloha/doc/obsidian/  ← Aloha 工作区（Wiki 存储）
├── _raw/                                   ← 官方 Raw Sources 根目录
│   ├── sources/                            ← 原始资料（append-only）
│   │   └── ...
│   └── registry.md                         ← 编译状态追踪（pending/compiled/error）
│
└── _wiki/                                  ← LLM Wiki 层（LLM 全权维护）
    ├── index.md                             ← 全局索引
    ├── log.md                              ← 时间线日志
    ├── entities/                            ← 实体页
    │   └── ...
    ├── concepts/                            ← 概念页
    │   └── ...
    ├── summaries/                          ← 摘要页
    │   └── ...
    └── tags/                               ← 标签索引
        └── ...
```

**目录约定**：
- `_raw/sources/` 为官方 Raw Sources 目录，**append-only**，LLM 只读不写
- `_wiki/` 为 LLM 生成内容，LLM 全权创建/修改/删除
- `registry.md` 记录每个 source 的编译状态，支持增量编译

---

## 3. Raw Sources vs Wiki 层划分

| 层级 | 路径 | 操作规则 |
|------|------|---------|
| **Raw Sources** | `_raw/sources/` | **append-only**，LLM 只读不写 |
| **Wiki 层** | `_wiki/` | LLM 全权读写 |

**维护原则**：
- `_raw/sources/` 只追加，源文件永不修改/删除
- `registry.md` 追踪编译状态，ingest 新文件标记 `pending`，compile 成功标记 `compiled`
- 初次部署时，AI-Agent-Research 迁移至 `_raw/sources/`

---

## 4. 命令设计（Slash 命令优先）

所有操作均为 **指令型**：LLM 读取 SKILL.md 后，通过文件工具操作 `_wiki/`，无需注册独立 Tool。

### 4.1 命令列表

| 命令 | 作用 |
|------|------|
| `/llm-wiki ingest <path>` | 将文件/目录/URL 登记到 `_raw/sources/`，registry.md 标记 pending |
| `/llm-wiki compile` | 将所有 pending 状态的文件编译为 wiki 页面 |
| `/llm-wiki query <question>` | 跨 wiki 综合回答，自动判断是否值得回填并请求确认 |
| `/llm-wiki status` | 仪表盘：文章数、编译率、pending 文件、断链数 |
| `/llm-wiki lint` | 健康检查：断链修复、矛盾检测、stale 摘要更新 |
| `/llm-wiki log` | 查看最近 ingest/query/lint 记录 |

### 4.2 Ingest 命令

```
用户：/llm-wiki ingest <path>
    ↓
1. 解析 path（文件/目录/URL）
2. 复制/下载到 _raw/sources/
3. 更新 registry.md，标记为 pending
4. 追加 log.md
    ↓
输出：已登记的文件列表 + pending 数量
```

### 4.3 Compile 命令

```
用户：/llm-wiki compile
    ↓
1. 读取 registry.md，获取所有 pending 文件
2. 逐个读取 source 内容
3. 提取实体 → 生成/更新 entities/{name}.md
4. 提取概念 → 生成/更新 concepts/{name}.md
5. 生成摘要 → 生成/更新 summaries/{name}.md
6. 自动打标签（写入 frontmatter）
7. 自动建立双向链接（[[page-name]]）
8. 更新 _wiki/index.md
9. registry.md 对应文件标记 compiled
10. 追加 log.md
    ↓
输出：已编译/失败的源文件列表
```

**增量编译**：只处理 registry.md 中状态为 `pending` 的文件，不重复编译已 `compiled` 的文件。

### 4.4 Query 命令（含回填判断）

```
用户：/llm-wiki query <question>
    ↓
1. 读取 _wiki/index.md（了解 Wiki 全貌）
2. 定位相关实体/概念页（优先读摘要判断相关性）
3. 综合多页面内容生成回答（带 [[引用]]）
4. 自动判断回答是否值得回填：
   - 是 → 询问用户确认，确认后写入对应类型页面 + 更新 index.md
   - 否 → 直接输出回答
    ↓
输出：综合回答 + 相关页面引用 + 可选回填确认
```

**回填判断标准**（LLM 自主判断）：
- 回答包含多源综合（>1 个 wiki 页面引用）
- 回答包含新洞见（非简单摘录，有 LLM 推理）
- 回答有长期参考价值

### 4.5 Lint 命令

```
用户：/llm-wiki lint
    ↓
1. 扫描所有 [[链接]]，检测断链 → 自动补建缺失页面或移除失效引用
2. 交叉检查矛盾声明（同一实体在不同页面的描述是否一致）
3. 检测无出站链接的孤立页面 → 建议关联
4. 检测 stale 摘要（source 已更新但摘要未同步）
5. 清理 index.md 失效引用
6. 报告到 log.md
    ↓
输出：健康报告 + 已修复项 + 待确认项
```

---

## 5. Schema 设计（内联于 SKILL.md）

### 5.1 Frontmatter 规范

每个 Wiki 页面必须包含 YAML frontmatter：

```yaml
---
title: 项目名称
type: entity | concept | summary
tags: [agent, memory, llm]
created: 2026-04-06
updated: 2026-04-06
sources: [source-file-1, source-file-2]
summary: 一句话描述，不超过 50 字
---
```

### 5.2 页面结构规范

1. **摘要**（必须）：页面顶部 1-2 段，概括核心内容
2. **正文**：详细展开
3. **关联**：底部 `## 相关链接` 章节，链接相关实体/概念页

### 5.3 命名约定

| 类型 | 命名格式 | 示例 |
|------|---------|------|
| 实体页 | `{name}.md` | `hermes.md` |
| 概念页 | `{concept-name}.md` | `tool-call-loop.md` |
| 摘要页 | `{name}-summary.md` | `hermes-summary.md` |
| 标签页 | `{tag-name}.md` | `agent.md` |

### 5.4 Auto-tagging 规范

LLM 根据内容自动判断标签，写入 frontmatter 的 `tags` 字段，不人工确认。

常用标签：`agent` `memory` `llm` `tool` `skill` `security` `ui` `design`

### 5.5 Auto Cross-reference 规范

- 在 `## 相关链接` 章节使用 Obsidian 双向链接语法：`[[page-name]]`
- 每个实体/概念页至少 2 个出站链接

---

## 6. OpenCode Skill 结构

```
~/.config/opencode/skills/llm-wiki/
└── SKILL.md    ← 唯一文件，包含完整入口 + schema
```

---

## 7. registry.md 结构

```yaml
---
title: Raw Sources Registry
description: 追踪 Raw Sources 的编译状态
---

## 状态说明

- pending：待编译
- compiled：已编译为 wiki 页面
- error：编译失败，需检查

## 文件列表

| 文件 | 状态 | 登记时间 | 编译时间 |
|------|------|---------|---------|
| llm-wiki-karpathy-analysis.md | compiled | 2026-04-06 | 2026-04-06 |
| llm-wiki-space-economy-karpathy-practice.md | pending | 2026-04-06 | - |
```

---

## 8. 实现路径（分阶段）

### 阶段一：基础框架（MVP）

**目标**：`/llm-wiki ingest` + `/llm-wiki compile` 能跑通

1. 创建 `~/.config/opencode/skills/llm-wiki/` 目录
2. 编写 `SKILL.md`（所有 sub-command 定义 + 内联 schema）
3. 初始化 `_raw/sources/` + `registry.md` + `_wiki/` 目录结构
4. 实现 `/llm-wiki ingest`（登记 + 复制文件 + 更新 registry + 追加 log）
5. 实现 `/llm-wiki compile`（增量编译 source → wiki）
6. 验证：ingest 现有文档，compile 生成 wiki 页面

### 阶段二：Auto-tagging + Cross-reference

**目标**：compile 时自动打标签 + 建立双向链接

1. 实现 auto-tagging（LLM 自动判断标签，写入 frontmatter）
2. 实现 auto cross-reference（使用 `[[links]]` 语法）
3. 实现 `tags/` 标签索引页自动生成

### 阶段三：Query 模式（含回填）

**目标**：`/llm-wiki query` 能综合多个 Wiki 页面回答 + 自动回填判断

1. 实现 `/llm-wiki query`
2. 优先读摘要判断相关性
3. 实现回填自动判断 + 确认机制
4. 实现 `/llm-wiki status` 仪表盘

### 阶段四：Lint 健康检查

**目标**：`/llm-wiki lint` 能检测并修复断链、矛盾、stale 摘要

1. 实现 `/llm-wiki lint`
2. 孤立页面检测 + 自动修复链接
3. 实现 `/llm-wiki log` 查看记录

### 阶段五：多格式支持

**目标**：支持 PDF、网页文章作为 Raw Sources

1. PDF 读取（提取文本）
2. 网页 URL（抓取转 MD）
3. 预处理脚本集成（PDF/Excel/图片 OCR/Word）

---

## 9. 关键技术决策

| 决策项 | 方案 | 理由 |
|--------|------|------|
| Skill 路径 | `~/.config/opencode/skills/llm-wiki/` | OpenCode 原生 skills 目录 |
| Schema 位置 | 内联 SKILL.md | SkillsLoader 只加载 SKILL.md |
| 操作形态 | 指令型 | LLM 读 SKILL.md 后用文件工具执行，无需注册 Tool |
| 触发方式 | Slash 命令优先 | 明确、无歧义、符合 OpenCode 惯例 |
| ingest/compile | 分开 | 支持先登记（ingest）再编译（compile），便于批量操作 |
| query 回填 | 内置于 query | query 时自动判断 + 用户确认，无需独立 file 命令 |
| Lint 触发 | 按需触发 | 暂不实现定时，简化复杂度 |
| Raw 目录 | `_raw/sources/` | append-only，与 Wiki 清晰隔离 |
| 编译状态追踪 | `registry.md` | 支持增量编译，不重复处理已编译 source |
| frontmatter | YAML | Obsidian 原生支持 |

---

## 10. 测试验证

| 阶段 | 测试内容 |
|------|---------|
| 阶段一 | ingest → compile，验证 entities + summaries + index + registry 正确 |
| 阶段二 | ingest 两篇关联文档，验证 auto-tag + cross-reference 正确 |
| 阶段三 | query 跨多个实体的问题，验证回答有引用 + 回填判断正确 |
| 阶段四 | 运行 lint，验证断链被修复 |
| 阶段五 | ingest PDF + 网页 URL，验证多格式支持 |

---

## 11. 已确认决策清单

- [x] Skill 路径：`~/.config/opencode/skills/llm-wiki/`
- [x] Schema 位置：内联到 SKILL.md
- [x] Lint 触发：按需触发
- [x] 操作形态：指令型
- [x] 触发方式：Slash 命令优先
- [x] ingest/compile：分开
- [x] query 回填：内置于 query
- [x] Raw 目录：`_raw/sources/`
- [x] AI-Agent-Research：迁移到 `_raw/sources/`
