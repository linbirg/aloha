---
name: llm-wiki
description: LLM Wiki 模式，自动维护 Obsidian 研究资料知识库
---

# LLM Wiki Skill

以 OpenCode 为引擎，自动维护 `doc/obsidian/` 下的知识库。

## Wiki 根目录

在对话中告诉用户 Wiki 根目录的位置（例如 `/path/to/your/obsidian-vault/`）。所有命令均基于此根目录操作。

## 目录结构

```
_raw/                          ← Raw Sources（append-only，LLM 只读不写）
  sources/                     ← 原始资料文件
  registry.md                  ← 编译状态追踪（pending / compiled / error）

_wiki/                         ← LLM Wiki（LLM 全权维护）
  index.md                     ← 全局索引
  log.md                       ← 时间线日志
  entities/                    ← 实体页
  concepts/                    ← 概念页
  summaries/                   ← 摘要页
  tags/                        ← 标签索引
```

## Slash 命令

| 命令 | 作用 |
|------|------|
| `/llm-wiki ingest <path>` | 将文件/目录/URL 登记到 `_raw/sources/`，registry 标记 pending |
| `/llm-wiki compile` | 将所有 pending 文件编译为 wiki 页面 |
| `/llm-wiki query <question>` | 跨 wiki 综合回答，自动判断是否值得回填 |
| `/llm-wiki status` | 仪表盘：文章数、编译率、pending 文件、断链数 |
| `/llm-wiki lint` | 健康检查：断链修复、矛盾检测、stale 摘要更新 |
| `/llm-wiki log` | 查看最近 ingest/query/lint 记录 |

---

## Schema：Wiki 页面规范

### Frontmatter（必须）

```yaml
---
title: 名称
type: entity | concept | summary
tags: [tag1, tag2]
created: YYYY-MM-DD
updated: YYYY-MM-DD
sources: [source-file-1]
summary: 不超过 50 字
---
```

### 页面结构

1. **摘要**（必须）：顶部 1-2 段，概括核心内容
2. **正文**：详细展开
3. **关联**：底部 `## 相关链接`，用 `[[page-name]]` 双向链接

### 命名约定

| 类型 | 格式 | 示例 |
|------|------|------|
| 实体页 | `entities/{name}.md` | `entities/hermes.md` |
| 概念页 | `concepts/{name}.md` | `concepts/tool-call-loop.md` |
| 摘要页 | `summaries/{name}-summary.md` | `summaries/hermes-summary.md` |
| 标签页 | `tags/{tag}.md` | `tags/agent.md` |

### Auto-tagging

LLM 根据内容自动判断标签，写入 frontmatter，不人工确认。

常用标签：`agent` `memory` `llm` `tool` `skill` `security` `ui` `design`

### Cross-reference

- 每个实体/概念页至少 2 个出站 `[[链接]]`
- 放在 `## 相关链接` 章节

---

## 命令详细说明

### /llm-wiki ingest

```
1. 解析 path（文件/目录/URL）
2. 复制/下载到 _raw/sources/
3. registry.md 新增条目，状态为 pending
4. log.md 追加：## [YYYY-MM-DD] ingest: <文件名>
```

### /llm-wiki compile

```
1. 读取 registry.md，获取所有 pending 文件
2. 逐个读取 source 内容
3. 提取实体 → 创建/更新 entities/{name}.md
4. 提取概念 → 创建/更新 concepts/{name}.md
5. 生成摘要 → 创建/更新 summaries/{name}-summary.md
6. 自动打标签（写入 frontmatter 的 tags: 字段）
7. 自动建立 [[双向链接]]（在 ## 相关链接 章节）
8. 扫描所有用到的 tag：
   - tag 页已存在 → 更新内容（追加引用）
   - tag 页不存在 → 创建 tags/{tag}.md
9. 更新 _wiki/index.md（统计、实体、概念、摘要、标签全部更新）
10. registry.md 对应文件标记 compiled
11. log.md 追加：## [YYYY-MM-DD] compile: <文件列表>
```

### /llm-wiki query

**标准流程**：

```
1. 读取 _wiki/index.md（了解 Wiki 全貌和主题覆盖）
2. 分析问题，确定涉及哪些领域/标签
3. 根据 index.md 定位相关实体/概念页（优先读摘要判断相关性）
4. 读取选中的实体/概念页正文
5. 综合回答（带 [[引用]]）
6. 判断是否值得回填：
   - 多源综合（引用 ≥2 个 wiki 页面）
   - 新洞见（非简单摘录，有 LLM 推理）
   - 长期参考价值
   → 同时满足 → 询问用户确认
   → 确认后：
      a. 确定页面类型（entity / concept / summary）
      b. 写入对应目录
      c. 在相关页面的 ## 相关链接 中追加 [[新页面]]
      d. 更新 tags/{tag}.md（追加引用）
      e. 更新 _wiki/index.md（追加条目）
      f. 更新 _wiki/log.md（## [date] query + file: <问题摘要>）
7. 输出回答 + 相关 [[引用]]
```

**查询优先级**：
- 主题覆盖表（index.md 最底部）→ 快速定位相关实体
- 标签页（tags/{tag}.md）→ 按标签聚合的页面列表
- 摘要页（summaries/）→ 先读摘要判断是否值得深入

**回填判断标准**（同时满足 ≥2 条）：
- 引用了 ≥2 个 wiki 页面（多源综合）
- 包含 LLM 推理而非简单摘录（新洞见）
- 回答有长期参考价值（不是一次性答案）
- 与现有 wiki 页面不重复

### /llm-wiki lint

```
1. 扫描所有 [[链接]]，检测断链 → 修复或移除
   - 常见错误：链接指向 source 文件名（如 xxx.md）而非 wiki 页面名（如 xxx-summary.md）
2. 交叉检查矛盾声明（同一实体在不同页面的描述是否一致）
3. 检测孤立页面（无任何页面引用）→ 建议关联
4. 检测 stale 摘要（source 已更新但摘要未同步）
5. 扫描 index.md 中引用的所有 tags/ 页是否存在，不存在则补建
6. 更新 _wiki/index.md（同步最新统计）
7. log.md 追加：## [YYYY-MM-DD] lint: <报告摘要>
```

### /llm-wiki status

输出仪表盘：
- Raw Sources 总数 + compiled 数量 + pending 数量
- Wiki 页面数（entities / concepts / summaries / tags）
- 编译率
- 断链数

### /llm-wiki log

读取 `_wiki/log.md`，输出最近 10 条记录。

---

## registry.md 格式

```yaml
---
title: Raw Sources Registry
description: 追踪 Raw Sources 编译状态
---

| 文件 | 状态 | 登记时间 | 编译时间 |
|------|------|---------|---------|
| file.md | pending | 2026-04-06 | - |
```

---

## frontmatter

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
