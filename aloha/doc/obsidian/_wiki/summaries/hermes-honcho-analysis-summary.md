---
title: Hermes Honcho 分析摘要
type: summary
tags: [honcho, user-model, memory]
created: 2026-04-06
updated: 2026-04-06
sources: [hermes-honcho-analysis]
summary: Hermes 通过 Honcho SDK 实现用户画像和心理理论，seed_ai_identity + 分层配置（instance/global/env）
---

Honcho 是 Hermes Agent 的用户建模核心组件，提供对话记忆平台能力，支持 AI 身份播种（seed_ai_identity）和用户表征提取。

**设计亮点**：本地缓存 + 异步云端同步 + 多层级配置（instance > global > env）+ 三种记忆模式（hybrid/honcho/context）。

[[memory-system]] — 概念页
