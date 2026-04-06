---
title: 工具审批系统两层层 Allow List 模式
type: concept
tags: [security, tool, agent, design]
created: 2026-04-06
updated: 2026-04-06
sources: [tool-approval-system-analysis]
summary: 发现 Aloha 工具审批双层独立 Allow List 模式：PermissionChecker（security 层）+ ShellTool._is_safe_command（tool 层），需同时放行命令
---

Aloha 的工具安全审批系统存在**两层独立的 Allow List**，同时放行才能让命令通过。

## 错误现象

`rm` 命令在 `api.py` 的 `ShellTool(allowed_commands=[..., 'rm'])` 中已添加，仍被拒绝并报 `Permission denied: Command 'rm' not in allowed list`。

## 根本原因：双层 Allow List

| 层级 | 文件 | 检查点 | 默认列表 |
|------|------|--------|---------|
| 安全策略层 | `security/policy.py` | `PermissionChecker.check()` | `SecurityConfig.shell_allowed_commands` |
| 工具执行层 | `tools/shell_tool.py` | `ShellTool._is_safe_command()` | `ShellTool.allowed_commands` |

`ToolWrapper.wrapper.py:72` 调用 `checker.check()` 先行拦截，在进入 Approver 审批流程之前已被拒绝。两层均需添加目标命令才能放行。

## 安全流

```
ToolWrapper (wrapper.py)
  └── PermissionChecker.check()        ← 第一层：白名单 + 风险评估
       └── Approver.request()           ← 第二层：MEDIUM/HIGH 用户审批
            ├── auto_approve (LOW)      ← 同步直接返回
            └── wait() (MEDIUM/HIGH)   ← 阻塞等待用户决策
```

## 修复方法

需同时在两层添加命令（如 `rm`）：
- `security/policy.py`：`SecurityConfig.shell_allowed_commands` 默认列表
- `tools/shell_tool.py`：`ShellTool.allowed_commands` 默认列表

[[hermes-agent]] — 参考 Hermes 的安全设计
[[agent-loop]] — 参考 ReAct 循环中的工具调用
