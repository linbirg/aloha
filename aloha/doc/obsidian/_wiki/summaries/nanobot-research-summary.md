---
title: Aloha ReActLoop vs NanoBot AgentLoop 对比摘要
type: summary
tags: [agent, loop, nanobot, react]
created: 2026-04-06
updated: 2026-04-06
sources: [nanobot-research]
summary: Aloha 轻量级 ReActLoop vs NanoBot 超轻量 AgentLoop：架构、流程、工具注册、Provider 对比；NanoBot 在多渠道/多 Provider 上更完善
---

Aloha 与 NanoBot（OpenClaw Python 实现）的详细对比分析。

**架构对比**：Aloha 为单体设计（约 255 行 loop.py），NanoBot 为模块化设计（Skills/Channels/Providers/Memory/Hooks 等子模块）。

**核心流程**：Aloha 手动 ReAct 循环，NanoBot 也有类似的工具调用循环，但 NanoBot 支持更多消息渠道（12+：Telegram、Discord、Slack、微信等）和 Provider（8+）。

**NanoBot 特有功能**：Skills 系统、生命周期 Hooks（on_start/on_message/on_tool_call）、Subagent 后台任务、Cron 定时任务、Heartbeat 主动唤醒机制。

**总结**：Aloha 适合原型和轻量级场景，NanoBot 生产级完善但更复杂。对 Aloha 的启示：可借鉴 NanoBot 的 Skills 系统和 Hook 机制增强扩展性。

[[agent-loop]] — Agent 循环机制
[[hermes-agent]] — Hermes 参考
