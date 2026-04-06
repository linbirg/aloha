---
title: Aloha Web UI 设计规格摘要
type: summary
tags: [ui, agent, design, vue]
created: 2026-04-06
updated: 2026-04-06
sources: [web-ui-design]
summary: 深色主题 Vue 3 前端：ChatView 主视图、ThinkingPanel 折叠块、ToolApprovalCard 审批卡片、Pinia stores + SSE 事件集成
---

Aloha Web 前端完整设计规格，Vue 3 + TypeScript + Vite + Pinia + Vue Router。

**技术栈**：Vue 3（渐进式 JS 框架）、TypeScript（类型安全）、Vite（构建工具）、Pinia（状态管理）、Vue Router（路由）。

**核心组件**：
- `ChatView.vue` — 聊天主视图，SSE 事件集成
- `MessageBubble.vue` — 消息气泡，支持 thinking 折叠展示
- `ThinkingPanel.vue` — 可折叠 thinking 过程面板
- `ToolApprovalCard.vue` — 工具审批卡片（确认/拒绝按钮，阻塞执行）
- `Sidebar.vue` — 可折叠侧边栏，新建对话功能

**SSE 集成**：`stores/events.ts` 管理 EventSource 状态（connection/reconnecting/disconnected），`useApprovalEvents.ts` 订阅审批事件，实现 thinking 追加模式和 message finalize。

[[sse-approval-system]] — SSE 实时推送实现
[[tool-approval-system]] — 工具审批系统
