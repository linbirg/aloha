# Aloha Web UI 设计规格

## 1. Concept & Vision

**定位**: 通用对话助手 - 日常问答、写作、翻译
**设计理念**: 简洁优雅的深色主题，专注于内容本身，减少视觉干扰

**核心体验**:
- 快速开始对话，无需复杂配置
- 清晰展示 AI 思考过程（thinking block）
- **工具调用需用户确认**：高风险操作需人工审批，防止误执行
- 优雅的对话历史管理

## 2. Design Language

### 色彩系统 (Dark Theme - GitHub Style)

```
Primary Background:   #0D1117 (深空黑)
Secondary Background:  #161B22 (炭灰)
Tertiary Background:   #21262D (浅炭灰)
Border:               #30363D (边框灰)
Text Primary:         #E6EDF3 (主文字)
Text Secondary:       #8B949E (次文字)
Text Muted:          #6E7681 (弱文字)
Accent:              #58A6FF (科技蓝)
Accent Hover:        #79C0FF (亮蓝)
Success:             #3FB950 (成功绿)
Warning:             #D29922 (警告黄/待审批)
Error:               #F85149 (错误红)
User Message BG:     #1F2937 (用户消息背景)
AI Message BG:       #161B22 (AI消息背景)
Thinking Block:      #2D333B (思考块背景)
Tool Pending BG:     #3D2E00 (待审批工具背景)
Tool Approved BG:    #1F3A2F (已批准工具背景)
Tool Rejected BG:    #3D1F1F (已拒绝工具背景)
```

### 字体系统

```
Display Font:  "Inter", system-ui, sans-serif (标题)
Body Font:      "Inter", system-ui, sans-serif (正文)
Code Font:      "JetBrains Mono", "Fira Code", monospace (代码/工具)
```

### 间距系统

```
Spacing XS:  4px
Spacing SM:  8px
Spacing MD:  16px
Spacing LG:  24px
Spacing XL:  32px
```

### 圆角系统

```
Radius SM:  4px
Radius MD:  8px
Radius LG:  12px
Radius XL:  16px
```

## 3. Layout Structure

### 整体布局

```
┌────────────────────────────────────────────────────────────┐
│  Header (56px) - 当前对话标题 + 操作按钮                    │
├──────────────┬─────────────────────────────────────────────┤
│              │                                             │
│   Sidebar    │           Main Content                      │
│   (280px)    │                                             │
│              │  ┌─────────────────────────────────────┐  │
│  - Logo      │  │        Messages Area                 │  │
│  - New Chat  │  │                                       │  │
│  - Search    │  │  [User Message]                       │  │
│  - History   │  │  [AI Response + Thinking]             │  │
│              │  │  [Tool Call - Pending Approval]        │  │
│              │  │      [Confirm] [Reject]               │  │
│              │  │  [Tool Call - Approved/Results]        │  │
│              │  │                                       │  │
│  - Settings  │  └─────────────────────────────────────┘  │
│              │                                             │
│              │  ┌─────────────────────────────────────┐  │
│              │  │        Input Area                    │  │
└──────────────┴─────────────────────────────────────────────┘
```

## 4. 核心功能

### 4.1 对话管理

| 功能 | 描述 | 交互 |
|------|------|------|
| 新建对话 | 创建新会话 | 点击按钮，清空消息区 |
| 对话历史 | 列表展示历史会话 | 点击切换，自动加载 |
| 删除对话 | 删除单个会话 | 悬停显示删除按钮 |
| 对话搜索 | 搜索历史消息 | 输入框实时过滤 |

### 4.2 消息展示

| 元素 | 描述 | 样式 |
|------|------|------|
| 用户消息 | 右侧对齐，蓝色背景 | 圆角气泡，右上圆角尖角 |
| AI消息 | 左侧对齐，灰色背景 | 圆角气泡，左上圆角尖角 |
| Thinking | 可折叠的思考过程 | 深色背景，脉冲动画图标 |
| Tool Call (Pending) | **需审批的工具调用** | 橙色边框，显示工具名和参数，**阻塞**，有 Confirm/Reject 按钮 |
| Tool Call (Approved) | 已批准的工具调用 | 绿色边框，显示工具名和执行结果 |
| Tool Call (Rejected) | 已拒绝的工具调用 | 红色边框，显示拒绝原因 |

### 4.3 工具调用审批流程（核心特性）

```
AI 请求工具调用
      ↓
检测工具风险级别
      ↓
┌─────────────────┐
│ 低风险 (auto)    │ → 自动执行 → 显示执行结果
├─────────────────┤
│ 中/高风险 (需确认)│ → 显示审批卡片 → 等待用户点击
│                  │     ↓
│            ┌────┴────┐
│            ↓         ↓
│       [确认]     [拒绝]
│            ↓         ↓
│        执行       标记拒绝
│            ↓         ↓
│        返回结果   返回拒绝原因
└─────────────────┘
```

### 4.4 Tool Call 审批卡片组件

```
┌─────────────────────────────────────────────────────────┐
│ 🔧 工具调用请求 - shell.exec                            │
├─────────────────────────────────────────────────────────┤
│ 风险级别: ⚠️ 中等                                        │
│                                                         │
│ 操作: 执行命令行命令                                     │
│ 参数:                                                   │
│   command: "rm -rf /tmp/test"                           │
│                                                         │
│ 预估影响: 将删除指定目录下的所有文件                     │
├─────────────────────────────────────────────────────────┤
│           [✅ 确认执行]      [❌ 拒绝]                 │
└─────────────────────────────────────────────────────────┘
```

### 4.5 输入区域

| 元素 | 描述 |
|------|------|
| Textarea | 自动扩展高度，最大200px |
| Send Button | 蓝色圆形按钮，禁用状态灰色 |
| 快捷键 | Enter发送，Shift+Enter换行 |

### 4.6 状态处理

| 状态 | UI处理 |
|------|--------|
| Empty State | 显示欢迎语和快捷建议 |
| Loading | 三个跳动的圆点动画 |
| Tool Pending | 橙色边框 + Confirm/Reject 按钮，**阻止后续流程** |
| Error | 红色提示框，显示错误信息 |
| Success | 绿色短暂提示 |

## 5. Component Inventory

### 5.1 Sidebar

```
.st-sidebar
  .st-logo          # Logo "ALOHA"
  .st-new-chat      # 新建对话按钮
  .st-search        # 搜索框
  .st-conversations  # 对话列表
    .st-conv-item    # 单个对话项 (default/hover/active)
  .st-footer         # 底部设置
```

### 5.2 ChatHeader

```
.ch-header
  .ch-title          # 当前对话标题
  .ch-actions        # 操作按钮组
```

### 5.3 MessageBubble

```
.msg
  .msg-avatar        # 头像 "U" / "AI"
  .msg-content        # 消息内容容器
    .msg-thinking     # 思考块（可选）
    .msg-tool         # 工具调用块（可选）
    .msg-text         # 文本内容
```

### 5.4 ToolApprovalCard (核心组件)

```
.tac                          # Tool Approval Card
  .tac-header
    .tac-icon                 # 🔧 图标
    .tac-title                # 工具名称
    .tac-risk                 # 风险级别标签
  .tac-body
    .tac-operation           # 操作描述
    .tac-params              # 参数列表
    .tac-impact              # 预估影响
  .tac-actions
    .tac-confirm             # ✅ 确认执行按钮
    .tac-reject              # ❌ 拒绝按钮
  .tac-status                # pending/approved/rejected
```

### 5.5 InputArea

```
.ia
  .ia-container      # 输入框容器
  .ia-textarea        # 文本输入框
  .ia-send            # 发送按钮
```

### 5.6 States

| Component | States |
|-----------|--------|
| Conv Item | default, hover, active |
| Send Btn | default, hover, disabled, loading |
| Message | loading, error |
| Thinking | collapsed, expanded |
| **ToolApprovalCard** | **pending (阻塞), approved, rejected** |

## 6. Technical Approach

### 框架选择

- **Frontend**: Vue 3 (Composition API) + TypeScript
- **Build Tool**: Vite
- **State**: Pinia
- **CSS**: Scoped CSS + CSS Variables

### 项目结构

```
aloha/web/
  src/
    components/
      Sidebar.vue
      ChatHeader.vue
      MessageBubble.vue
      InputArea.vue
      ThinkingBlock.vue
      ToolApprovalCard.vue    # 核心：工具审批卡片
      ToolResultBlock.vue     # 已执行/已拒绝的结果
    views/
      ChatView.vue
    stores/
      conversation.ts         # Pinia store - 对话状态
      approval.ts            # Pinia store - 审批队列
    styles/
      variables.css          # CSS 变量
      base.css               # 基础样式
    types/
      index.ts               # TypeScript 类型定义
    App.vue
    main.ts
  index.html
  package.json
  vite.config.ts
  tsconfig.json
```

### API 设计

```
POST /api/chat
Request: {
  message: string,
  conversationId?: string
}

Response: {
  content: string,
  thinking?: string,
  toolCalls?: Array<{
    id: string,
    name: string,
    arguments: object,
    riskLevel: "low" | "medium" | "high",
    result?: string,
    status?: "pending" | "approved" | "rejected"
  }>
}

POST /api/approval
Request: {
  toolCallId: string,
  approved: boolean
}

Response: {
  success: boolean,
  result?: string,
  error?: string
}
```

### 审批流程时序

```
1. User 发送消息
2. AI 返回 tool_calls (riskLevel: "medium")
3. 前端渲染 ToolApprovalCard，status=pending
4. UI 进入"等待审批"状态，**暂停**向 AI 发送后续请求
5. User 点击 [确认执行]
   → POST /api/approval { toolCallId, approved: true }
   → 后端执行工具
   → 返回执行结果
   → 前端更新 ToolApprovalCard → status=approved
   → 继续 ReAct 循环，发送 tool result 给 AI
6. OR User 点击 [拒绝]
   → POST /api/approval { toolCallId, approved: false }
   → 后端记录拒绝
   → 前端更新 ToolApprovalCard → status=rejected
   → 返回拒绝原因给 AI
   → AI 决定如何处理（重试或放弃）
```

## 7. Implementation Phases

### Phase 1: 基础布局
- [ ] 项目初始化 (Vite + Vue 3 + TypeScript)
- [ ] CSS 变量定义
- [ ] 布局组件 (Sidebar, Main)
- [ ] 响应式处理

### Phase 2: 核心对话功能
- [ ] 对话状态管理 (Pinia)
- [ ] 消息渲染
- [ ] 输入发送
- [ ] 加载状态

### Phase 3: 工具审批功能（核心）
- [ ] ToolApprovalCard 组件
- [ ] 审批队列状态管理
- [ ] Confirm/Reject 按钮交互
- [ ] **阻塞逻辑**：工具待审批时暂停 ReAct 循环
- [ ] 审批结果反馈给后端

### Phase 4: 增强功能
- [ ] Thinking 展示
- [ ] Tool Result 展示
- [ ] 对话历史（localStorage）
- [ ] 空状态/错误处理

### Phase 5: 完善
- [ ] 键盘快捷键
- [ ] 动画效果
- [ ] 单元测试

## 8. Acceptance Criteria

1. ✅ 侧边栏可折叠/展开
2. ✅ 新建对话功能正常
3. ✅ 消息发送和接收正常
4. ✅ Thinking 块可折叠
5. ✅ **ToolApprovalCard 显示确认/拒绝按钮**
6. ✅ **工具调用阻塞 ReAct 循环直到用户审批**
7. ✅ 审批结果正确传递到后端
8. ✅ 对话历史保存到 localStorage
9. ✅ 响应式布局正常
10. ✅ 加载状态显示
11. ✅ 错误状态处理
12. ✅ 键盘快捷键支持