# LLM Wiki 模式分析

> **来源**：Andrej Karpathy - [LLM Wiki (GitHub Gist)](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)
> **日期**：2026-04
> **标签**：knowledge-management, llm, rag, karpathy, wiki, obsidian, agents

---

## 核心思想

传统 RAG（检索增强生成）的问题：**每次提问，LLM 都从零查找相关片段，没有积累，没有复合效应**。问一个需要综合五份文档的细微问题，LLM 必须每次重新找到并拼凑相关片段。没有什么是被构建起来的。

Karpathy 的思路：**让 LLM 增量构建和维护一个持久的 Wiki**，作为用户与原始资料之间的中间层。当加入新资料时，LLM 不是只索引存储，而是读取 → 提取关键信息 → 整合到现有 Wiki，更新相关页面、标注矛盾、补充交叉引用。

**关键洞察**：Wiki 是**持久复利的知识产物**，不是每次查询重新推导。交叉引用已经存在，矛盾已被标注，综合已反映所有已读资料。Wiki 随着每份加入的资料和每个问题变得越发丰富。

---

## 三层架构

```
┌─────────────────────────────────────────────────────┐
│  Raw Sources（原始资料）                              │
│  Articles, Papers, Images, Data Files               │
│  不可变，LLM 只读不写，Source of Truth               │
└──────────────────────┬──────────────────────────────┘
                       │ LLM reads
                       ▼
┌─────────────────────────────────────────────────────┐
│  Wiki（LLM 全权维护的 Markdown 文件集合）           │
│  摘要页、实体页、概念页、对比页、索引页              │
│  LLM 创建/更新页面、维护交叉引用、保持一致性          │
└──────────────────────┬──────────────────────────────┘
                       │ LLM reads/writes
                       ▼
┌─────────────────────────────────────────────────────┐
│  Schema（CLAUDE.md / AGENTS.md）                     │
│  告诉 LLM Wiki 结构、规范、工作流                     │
│  LLM Wiki 维护者的行为准则配置文件                    │
└─────────────────────────────────────────────────────┘
```

| 层级 | 说明 |
|------|------|
| **Raw Sources** | 原始资料（articles、papers、图片、数据文件），**不可变**，LLM 只读不写 |
| **Wiki** | LLM 全权维护的 markdown 文件集合（摘要页、实体页、概念页、对比页、索引页）。LLM 创建、更新，维护所有交叉引用 |
| **Schema** | CLAUDE.md / AGENTS.md 类的配置文档，告诉 LLM Wiki 结构、规范，工作流（ingest / query / lint）。这是关键配置文件 |

---

## 三种操作

### Ingest（摄入新资料）

流程：
1. 用户将新资料放入 raw collection
2. LLM 读取资料
3. 与用户讨论关键要点
4. 在 Wiki 中写摘要页
5. 更新索引（index.md）
6. 更新相关实体页和概念页（可能触及 10-15 个 Wiki 页面）
7. 向日志追加条目（log.md）

Karpathy 偏好一次 ingest 一份资料，保持参与度。但也可以批量 ingest，监督更少。

### Query（查询）

流程：
1. 用户提问
2. LLM 搜索相关页面（先读 index.md 找入口）
3. 阅读相关页面
4. 综合回答（带引用）

**重要洞察**：好的回答可以重新存回 Wiki 作为新页面。比较分析、发现的有趣联系——这些有价值的输出不应该消失在对话历史里。这样探索结果也像 ingest 的资料一样复合积累。

回答形式可以多样化：markdown 页面、对比表格、幻灯片（Marp）、图表（matplotlib）。

### Lint（健康检查）

定期让 LLM 检查 Wiki 健康状况：
- 页面间的矛盾
- 被新资料替代的过时声明
- 没有入站链接的孤立页面
- 被提及但没有独立页面的重要概念
- 缺失的交叉引用
- 可以通过网络搜索填补的数据空白

LLM 擅长建议新问题和寻找新资料来源。

---

## 两个特殊文件

### index.md（内容导向）

- Wiki 的目录，每个页面一条记录：链接 + 一句话摘要 + 可选元数据（日期、来源数量）
- 按分类组织（实体、概念、来源等）
- **LLM 每次 ingest 更新**
- 回答问题时，LLM **先读 index 找相关页面，再深入阅读**

在中等规模（~100 资料、数百页面）下效果出乎意料地好，**无需 embedding-based RAG 基础设施**。

### log.md（时间导向）

- Append-only 时间线日志
- 记录 ingest / query / lint 的时间和内容
- 固定前缀格式：`## [2026-04-02] ingest | Article Title`
- 可用简单 Unix 工具解析：`grep "^## \[" log.md | tail -5` 查看最近 5 条
- 帮助 LLM 理解最近做了什么

---

## 工具链

| 工具 | 用途 |
|------|------|
| **Obsidian Web Clipper** | 浏览器插件，将网页文章转 markdown，快速将资料加入 raw collection |
| **Obsidian Graph View** | 查看 Wiki 全局结构：什么连接什么，哪些是 hub 页面，哪些是孤立页面 |
| **qmd** | 本地 Markdown 搜索引擎（BM25 + 向量搜索 + LLM 重排），提供 CLI 和 MCP Server |
| **Marp** | 基于 markdown 的幻灯片格式，Obsidian 有插件，可直接从 Wiki 内容生成演示 |
| **Dataview** | Obsidian 插件，对 YAML frontmatter 运行查询，生成动态表格和列表 |
| **Git** | Wiki 就是 git 仓库，自带版本历史、分支和协作功能 |
| **本地图片下载** | Obsidian 设置 → Files and links → 固定附件目录（如 `raw/assets/`）；热键绑定"下载当前文件附件"（如 `Ctrl+Shift+D`）。LLM 无法原生一次读完含 inline 图片的 markdown，解决方法：先让 LLM 读文本，再单独查看部分或全部图片获取额外上下文 |

---

## 为什么有效

**人类放弃维护 Wiki 的原因**：维护成本增长快过价值增长。

LLM 的优势：
- 不会疲倦
- 不会忘记更新交叉引用
- 一次可以修改 15 个文件

| 角色 | 职责 |
|------|------|
| **人类** | 筛选资料、引导分析方向、提出好问题、思考含义 |
| **LLM** | 总结、交叉引用、归档、日志记录等一切苦力活 |

维护成本接近零 → Wiki 得以持续维护。

---

## 与 Vannevar Bush Memex 的联系

这个思路在精神上与 Vannevar Bush 的 **Memex**（1945）相关——一个个人策划的知识库，文档之间有关联轨迹。 Bush's 的愿景更接近这个模式（私有、主动策划、文档之间的连接和文档本身一样有价值），而非后来 Web 变成的样子。他无法解决的是：**谁来维护**。LLM 接手了这部分。

---

## 应用场景

| 场景 | 说明 |
|------|------|
| **个人成长** | 追踪目标、健康、心理学、自我提升——归档日志条目、文章、播客笔记，随时间构建个人结构化图景 |
| **研究** | 数周或数月深入一个主题——阅读论文、文章、报告，逐步构建包含演进论题的全面 Wiki |
| **读书** | 逐章归档，构建角色、主题、情节线以及它们如何连接的页面。最终拥有丰富的配套 Wiki（类似 Tolkien Gateway 粉丝 Wiki——数千个互联页面，由志愿者社区多年构建）。LLM 可以个人方式做同样的事 |
| **业务/团队** | 由 LLM 维护的内部 Wiki，来源包括 Slack 讨论、会议记录、项目文档、客户电话。可能有 humans-in-the-loop 审查更新 |
| **竞争分析、尽职调查、旅行规划、课程笔记、爱好深入** | 任何随时间积累知识、想要组织化而非分散化的场景 |

---

## 对 Aloha Agent 的潜在关联

### 1. Memory 系统的共鸣

Aloha Agent 的 Memory 系统：
- **Session Memory**：会话级积累
- **LongTerm Memory**：长期知识积累

LLM Wiki 模式的"复合积累"思路与其高度一致。Wiki 的 `index.md` 相当于 LongTerm Memory 的索引，`log.md` 相当于会话历史的时间线。

**探索方向**：能否让 Aloha Agent 的 LongTerm Memory 也实现持久复合的知识积累？而不是每次会话从零开始？

### 2. Skills Loader 的共鸣

Aloha 的 Skill 本质上也是一种 Wiki-like 结构化知识：
- `SOUL.md`：Agent 灵魂定义
- `RULES.md`：行为规则
- `AGENTS.md`：Agent 配置

Skill 的 Schema 文件和 LLM Wiki 的 Schema 层在思想上相通。

**探索方向**：Skill 能否引入 LLM Wiki 的 ingest/query/lint 模式？让 Skill 也随使用复合进化？

### 3. 工具注册表

Aloha 的工具注册表 + Schema 可以看作是 Wiki Schema 在工具层面的体现。

---

## 核心引用

> The tedious part of maintaining a knowledge base is not the reading or the thinking — it's the bookkeeping. Updating cross-references, keeping summaries current, noting when new data contradicts old claims, maintaining consistency across dozens of pages. **Humans abandon wikis because the maintenance burden grows faster than the value.** LLMs don't get bored, don't forget to update a cross-reference, and can touch 15 files in one pass. **The wiki stays maintained because the cost of maintenance is near zero.**
>
> The human's job is to curate sources, direct the analysis, ask good questions, and think about what it all means. **The LLM's job is everything else.**
