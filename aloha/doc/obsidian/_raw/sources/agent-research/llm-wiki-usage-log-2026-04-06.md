# LLM Wiki 使用过程记录

> **日期**：2026-04-06
> **类型**：使用过程记录
> **标签**：llm-wiki, usage-log, compile, query, file-back

---

## 操作一：首次批量编译（/llm-wiki compile）

**时间**：2026-04-06
**操作**：`/llm-wiki compile`

### 执行过程

1. 读取 `_raw/registry.md`，获取所有 pending 状态文件（16 篇）
2. 读取全部 16 篇 Raw Sources 原始文档
3. 按实体→概念→摘要顺序生成 Wiki 页面
4. 更新 `registry.md` 标记所有文件为 compiled
5. 更新 `_wiki/index.md` 全局索引
6. 追加 `_wiki/log.md` 操作记录

### 编译结果

| 类型 | 数量 | 详情 |
|------|------|------|
| 实体页 | 5 | hermes-agent、mastra、pi-mono、ai-sdk、opencode |
| 概念页 | 4 | llm-wiki-pattern、agent-loop、memory-system、skills-system |
| 摘要页 | 16 | 每篇 source 一份摘要 |
| index + log | 2 | 全局索引 + 操作日志 |
| **合计** | **27** | |

**Raw Sources 详情**：

| 文件 | 状态 |
|------|------|
| ai-sdk-tool-loop-analysis.md | compiled |
| hermes-agent-analysis.md | compiled |
| hermes-agent-fts5-analysis.md | compiled |
| hermes-agent-loop-analysis.md | compiled |
| hermes-honcho-analysis.md | compiled |
| hermes-memory-system-analysis.md | compiled |
| llm-wiki-analysis-deep-dive.md | compiled |
| llm-wiki-claude-code-obsidian-practice.md | compiled |
| llm-wiki-karpathy-analysis.md | compiled |
| llm-wiki-space-economy-karpathy-practice.md | compiled |
| mastra-analysis.md | compiled |
| mastra-loop-analysis.md | compiled |
| opencode-user-manual.md | compiled |
| pi-mono-memory-system-code-analysis.md | compiled |
| pi-mono-session-management-analysis.md | compiled |
| pi-mono-skills-analysis.md | compiled |

**编译率**：100%

---

## 操作二：查询 ReAct 流式 API 原理（/llm-wiki query）

**时间**：2026-04-06
**问题**：react模式中的流式api的原理是什么

### 查询过程

1. 读取 `_wiki/index.md` 定位相关页面
2. 定位到 `[[agent-loop]]` 概念页
3. 读取 `agent-loop.md`、`hermes-agent-loop-analysis-summary.md`、`mastra-loop-analysis-summary.md`
4. 补充读取 `mastra-loop-analysis.md` 原文获取流式架构细节

### 回答内容

ReAct 模式中流式 API 本质是 **LLM 输出管道化**：

**SDK 自动循环（Mastra / AI SDK）**：
```
LLM Stream → workflowLoopStream → MastraModelOutput → DestructurableOutput
                        ↓
              [text chunk | object | function call]
```
- `workflowLoopStream` 实时分拣：文本块直接吐出，工具调用截断并执行
- 截断点：LLM 开始生成 tool_call 时，SDK 检测到后立即触发执行

**手动 ReAct 循环（Hermes）**：
```python
while iteration < max_iterations:
    response = client.chat.completions.create(messages, stream=True)
    for chunk in response:
        if chunk.tool_calls:
            tool_call = parse_tool_call(chunk)
            result = handle_function_call(tool_call)
            messages.append(tool_result)
            break
        elif chunk.text:
            yield chunk.text
```

**关键机制**：

| 机制 | 说明 |
|------|------|
| 工具调用截断 | LLM 生成 tool_call 时，stream 被截断，工具立即执行 |
| 流式文本输出 | text chunk 直接 yield 给调用方（UI/终端） |
| 结果注入 | 工具执行完成后注入 messages，触发下一轮 LLM |
| 并行工具 | toolCallConcurrency 支持多工具并行流式执行 |

### 回填判断

自动判断值得回填（多源综合 + 新洞见 + 长期参考价值）→ 询问用户确认 → 用户确认写入

---

## 操作三：回填（/llm-wiki file）

**时间**：2026-04-06
**触发**：query 后用户确认回填

### 回填内容

新增 `_wiki/concepts/react-streaming.md`，包含：

- **标题**：ReAct 流式机制
- **type**：concept
- **tags**：[react, streaming, agent, loop]
- **sources**：mastra-loop-analysis、hermes-agent-loop-analysis、ai-sdk-tool-loop-analysis
- **summary**：ReAct 模式中流式 API 原理，LLM 输出管道化实现工具调用实时截断和文本流式输出
- **正文**：核心架构（SDK 自动 vs 手动）+ 关键机制表格 + 对比 + 对 Aloha 启示
- **相关链接**：指向 agent-loop、mastra-loop-analysis-summary、hermes-agent-loop-analysis-summary

### 更新文件

1. `_wiki/concepts/react-streaming.md` — 新建
2. `_wiki/index.md` — 更新统计（28篇）、新增概念页条目、更新研究主题覆盖
3. `_wiki/log.md` — 追加 query + file 操作记录

---

## 飞轮验证

从 27 篇到 28 篇，**不是靠新增 Raw Sources，而是靠 query 过程中的综合回答**。

这验证了 Karpathy LLM Wiki 的核心飞轮：
> 每次探索都在沉淀，越用越厚

---

## 附录：目录结构快照

```
_raw/
  registry.md              ← compiled 100%
  sources/                  ← 16 篇原始文档

_wiki/
  index.md                  ← 28 篇页面
  log.md                    ← 3 条记录（init, compile, query+file）
  entities/                 ← 5 篇
    hermes-agent.md
    mastra.md
    pi-mono.md
    ai-sdk.md
    opencode.md
  concepts/                 ← 5 篇
    llm-wiki-pattern.md
    agent-loop.md
    memory-system.md
    skills-system.md
    react-streaming.md      ← 本次新增
  summaries/                ← 16 篇
```
