# 我用 OpenCode Skill 复现了 Karpathy 的 LLM Wiki 知识库

**日期**：2026-04-06
**标签**：knowledge-management, llm, wiki, opencode, skills, agent, 知识管理
**开源地址**：https://gitee.com/linbirg/llm-wiki

---

## 动机：笔记不是给人翻的，是给 AI 用的

这是一个老问题了。

我们都在用 Obsidian、Notion、Roam——笔记软件买了一堆，文件夹越建越深，但最后真正翻出来再用的内容，少得可怜。

原因很简单：**维护太累了**。人既要当知识的生产者，又要当知识的整理者，两件事完全不在同一个思维模式里。写的时候在创作，整理的时候在分类——每次切换都是一次认知税。

我一直想找一个解法，直到今年四月看到 Karpathy 的那条长帖。

但更根本的问题是：**我们做个人知识库，从一开始目的就错了。**

我们以为知识库是"第二大脑"，是给人翻的。但实际上，人翻自己笔记的频率远低于预期——真正需要从知识库里提取信息的时候，更可能的场景是**有一个 AI 在帮你做事，你需要它懂你的知识**。

所以，建立可增长的持久知识库，**真正的目的不是给人看，而是给 AI 看和使用**。当 AI 读你积累的资料、理解你的研究脉络、在你的知识库里做推理和联想，这才是知识库真正发挥价值的方式。

---

## 思路：人不碰 Wiki，Wiki 是 LLM 的领地

Karpathy 的思路出奇简单，核心就一句话：**人不碰 wiki**。

Wiki 是 LLM 的领地，人只负责两件事：**投喂原料**和**提出好问题**。

这不是"用 AI 帮你整理笔记"，而是**彻底换位——让 LLM 成为知识库的唯一维护者**，采集、编译、索引、查询、回填、自检，全部自动化。

### 和 RAG 的本质区别

传统 RAG（Retrieval-Augmented Generation）的模式是：

```
上传文档 → 提问 → 检索相关片段 → LLM 生成回答 → 结束
```

每次问答都是独立的，知识不会因为问答而积累。你问一次，模型做一次，下次换个问法，可能还要重新检索一遍。

LLM Wiki 的模式是：

```
Raw Sources（只读）→ Wiki（LLM 维护）→ Schema（行为准则）
    ↓
提问 → 先查 Wiki（已整理过的结构化知识）→ 回答
    ↓
有价值的回答 → 回填到 Wiki → Wiki 持续生长
```

**先编译，再查询**。编译一次，后面反复查。

### 五个关键机制

Karpathy 在 gist 里描述了五个核心机制：

**1. raw/wiki 分离**

原始资料放进 `raw/`，只读不改。LLM 读取后"编译"成结构化的 Wiki 文章——每份资料一篇摘要，提取概念写成独立文章，互相做双向链接，自动分类。

**2. 索引替代 RAG**

不需要向量数据库。一个 `index.md` 文件列出所有文章的路径和一句话摘要，LLM 读一遍就知道该去翻哪篇。

在小规模（<500 篇）下，这比 RAG 更轻、更准、零基础设施成本。

**3. 查询结果回填（飞轮核心）**

这是最关键的设计。每次查询的回答，如果质量够高，就**存回 Wiki**。

这意味着知识库**不只靠丢新资料增长，也靠问问题增长**。从 13 篇到 27 篇，不是靠喂新文章，而是靠问好问题。

**4. 增量编译**

一个 `registry.md` 跟踪每份原始文件的编译状态。新文件进来只编译新增的，不用重建整个 Wiki。

**5. 自动 Lint（健康检查）**

定期让 LLM 通读全库，找矛盾数据、补缺失环节、发现新的关联文章候选。这是人做不到、但 LLM 天然擅长的维护工作。

---

## 方案概要

我把 Karpathy 的方法用 OpenCode Skill 落地了。整个系统的架构如下：

```
OpenCode（运行引擎）
    ↓ 读取 SKILL.md
~/.config/opencode/skills/llm-wiki/
└── SKILL.md    ← 定义所有操作规范

工作目录/
├── _raw/                      ← 原始资料（append-only）
│   ├── sources/               ← 原始文档
│   └── registry.md            ← 编译状态追踪
│
└── _wiki/                    ← LLM 全权维护
    ├── index.md              ← 全局索引（先读这个）
    ├── log.md                ← append-only 操作日志
    ├── entities/              ← 实体页（项目、产品、技术栈）
    ├── concepts/             ← 概念页（设计模式、架构思想）
    ├── summaries/            ← 摘要页（每篇 source 对应一篇）
    └── tags/                 ← 标签索引（按标签聚合页面）
```

### 六个命令

| 命令 | 作用 |
|------|------|
| `/llm-wiki ingest <path>` | 登记新资料到 Raw Sources |
| `/llm-wiki compile` | 增量编译为 Wiki 页面 |
| `/llm-wiki query <question>` | 综合回答，自动判断是否回填 |
| `/llm-wiki status` | 仪表盘 |
| `/llm-wiki lint` | 健康检查 + 断链修复 |
| `/llm-wiki log` | 查看操作记录 |

### Wiki 页面规范

每篇 Wiki 页面包含 YAML frontmatter：

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

内容三段式：摘要（必须）→ 正文 → `## 相关链接`（双向链接）。

---

## 使用实例

下面是我用它构建 AI Agent 研究知识库的全过程记录。

### Step 1：初始化

我有 16 篇关于 AI Agent 的研究笔记，分布在各个目录里。首先创建目录结构，把所有原始文档迁入 `_raw/sources/`：

```
_raw/
  registry.md          ← 16 篇全部标记 pending
  sources/             ← 16 篇原始文档

_wiki/
  index.md              ← 空
  log.md                ← 初始化记录
  entities/             ← 空
  concepts/             ← 空
  summaries/            ← 空
  tags/                 ← 空
```

### Step 2：首次编译（/llm-wiki compile）

执行 `/llm-wiki compile`，LLM 完成了以下工作：

1. 读取全部 16 篇原始文档
2. 提取实体 → 生成 5 篇实体页（hermes-agent、mastra、pi-mono、ai-sdk、opencode）
3. 提取概念 → 生成 4 篇概念页（llm-wiki-pattern、agent-loop、memory-system、skills-system）
4. 生成 16 篇摘要页（每篇 source 一篇摘要）
5. 自动打标签（写入 frontmatter 的 tags 字段）
6. 自动建立双向链接（在 `## 相关链接` 章节）
7. 更新全局索引 index.md

**编译结果**：16 篇原始文档 → 27 篇 Wiki 页面，编译率 100%。

### Step 3：第一次查询

我问了第一个问题：**"react模式中的流式api的原理是什么"**

LLM 的处理流程：

1. 读 `index.md`，定位到 `[[agent-loop]]` 概念页
2. 读 `agent-loop.md`、`hermes-agent-loop-analysis-summary.md`、`mastra-loop-analysis-summary.md`
3. 综合回答，带 `[[引用]]`

回答内容涵盖了 SDK 自动循环（Mastra 的 `workflowLoopStream` 实时分拣）和手动 ReAct 循环（Hermes 遍历 stream chunk）两种路线的对比，关键机制包括工具调用截断、流式文本输出、结果注入、并行工具支持。

### Step 4：回填验证

LLM 自动判断这个回答值得回填——因为它引用了 3 个 Wiki 页面，包含 LLM 推理而非简单摘录，且有长期参考价值。

询问我确认后，写入了 `concepts/react-streaming.md`。

**飞轮验证**：从 27 篇到 28 篇——**不是靠新增资料，而是靠问问题**。

### Step 5：健康检查（/llm-wiki lint）

自动运行的 lint 发现了问题：编译阶段有些链接指向了 source 文件名（如 `[[xxx-analysis]]`）而非 summary 文件名（如 `[[xxx-analysis-summary]]`），共 11 处，全部自动修复。

同时发现 tag 索引页不完整——index.md 引用了 32 个标签，但 tag 页只创建了 17 个。LLM 自动补建了另外 15 个（session、tool、honcho、fork、compact、analysis 等）。

**lint 后**：断链 0，Wiki 页面 46 篇（5 实体 + 5 概念 + 16 摘要 + 32 tags + index + log）。

### 最终状态

```
Raw Sources：17 篇（16 篇 compiled + 1 篇 meta）
Wiki 页面：46 篇
编译率：100%
断链：0
操作日志：5 条（init → compile → query+file → auto-tagging → lint）
```

---

## 回填飞轮的真正价值

复盘整个过程，最有价值的不是 compile，而是 **query + file-back**。

compile 把 16 篇文档变成了 27 篇 Wiki。看起来很多，但本质上只是把原文换了个格式重写了一遍。

真正让知识库"活"起来的，是那次 query——LLM 把散落在多个页面里的流式 API 实现细节综合在一起，生成了一篇在原始文档里根本不存在的新文章。这篇文章来自 LLM 的推理，不是来自任何一篇原始资料的直接摘录。

这才是 Karpathy 所说的复利：**知识不只被检索，还会被回写、被校验、被慢慢积累**。

---

## 技术实现细节

### 为什么用 OpenCode Skill

OpenCode 的 Skills 机制天然适合这个场景——SKILL.md 本身就是一个标准化操作手册，定义了 ingest/compile/query/lint 的完整流程规范，OpenCode 加载后按规范执行。

整个系统没有一行 Python 代码，全部靠 OpenCode 读懂 SKILL.md 后用文件工具操作 Markdown 文件。

### 为什么不用数据库

纯 Markdown 文件，无数据库依赖。每个 Wiki 页面的结构通过 YAML frontmatter 定义，Obsidian 原生支持双向链接，整个系统的状态分散在各页面的 frontmatter 和 `registry.md` 里。

`registry.md` 是编译状态的核心——每篇 source 标记 pending/compiled/error，增量编译时只处理 pending 的文件。

### 为什么断链难以完全避免

编译阶段生成的实体页/概念页引用了同批次生成的 summary 页面，但 summary 页面的文件名是在 compile 过程中才能确定的。这个时序依赖导致第一批编译时，实体页只能先写一个占位链接，后续 lint 才能修掉。这是 LLM Wiki 在当前指令型架构下的固有限制——解决思路是 compile 后自动跑一遍 lint。

---

## 总结

LLM Wiki 解决了一个具体问题：**让知识随着使用而增长，而不是随着时间而消散**。

实现不复杂：一份 SKILL.md 定义规范，一个 `_raw/` 放原料，一个 `_wiki/` 让 LLM 自由发挥，几个 Markdown 文件记录状态。

最核心的设计是**回填飞轮**：query 的回答如果质量够高，就存回 Wiki。下一次查询时，这个新页面就成了被检索的对象。知识在这个循环里不断沉淀、不断生长。

人从整理者的角色里彻底解放出来，专注于提问。

**但更重要的是，这套知识库从一开始就不是为人建的，是为 AI 建的。** Obsidian 里的 Graph View 是给人看的；LLM Wiki 里的 index.md + summaries + concepts，是给 AI 看的。AI 在你的知识库里导航、理解、推理，才是这套系统的核心价值。

---

## 开源地址

**https://gitee.com/linbirg/llm-wiki**

---

## 参考资料

- [Karpathy - LLM Wiki gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)
- [Farzapedia - x.com/FarzaTV](https://x.com/FarzaTV/status/2040563939797504467)
- [As We May Think - Vannevar Bush, 1945](https://www.theatlantic.com/magazine/archive/1945/07/as-we-may-think/303881/)
