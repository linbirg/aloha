---
title: AI Agent 安全工具与权限控制系统设计方案摘要
type: summary
tags: [security, tool, agent, design]
created: 2026-04-06
updated: 2026-04-06
sources: [security-tools-design]
summary: 操作级权限粒度、同步阻塞审批、三层架构（工具层→安全层→Agent层）、FileTool/ShellTool/WebTool 白名单设计
---

AI Agent 基础工具与权限控制系统的设计文档，核心理念是**权限粒度细化到操作级别**。

**三层架构**：
- **工具层**（tools/）：FileTool（目录白名单）、ShellTool（命令白名单 + 模式黑名单）、WebTool（域名白名单 + 速率限制）
- **安全层**（security/）：PermissionChecker（风险评估）、Approver（用户审批）、AuditLogger（审计日志）
- **集成层**（wrapper/）：ToolWrapper 拦截所有工具调用

**审批流程**：同步阻塞，Agent 调用工具时暂停等待用户批准/拒绝，低风险自动放行，高风险必须人工确认。

**已实现**：FileTool、ShellTool（rm 已在双层白名单放行）、WebTool、PermissionChecker、Approver、ToolWrapper。

[[tool-approval-system]] — 两层层 Allow List 根本原因分析
[[sse-approval-system]] — SSE 实时审批推送实现
