# Aloha Web UI

基于 Vue 3 + TypeScript + Vite 的 Aloha AI 助手 Web 前端界面。

## 技术栈

- **Vue 3** - 渐进式 JavaScript 框架
- **TypeScript** - 类型安全的 JavaScript 超集
- **Vite** - 快速的前端构建工具
- **Pinia** - Vue 状态管理
- **Vue Router** - Vue 路由管理

## 项目结构

```
aloha/web/
├── index.html              # HTML 入口
├── package.json            # 项目配置
├── vite.config.ts          # Vite 配置
├── tsconfig.json           # TypeScript 配置
└── src/
    ├── main.ts             # 应用入口
    ├── App.vue             # 根组件
    ├── router/
    │   └── index.ts        # 路由配置
    ├── stores/
    │   └── chat.ts         # 聊天状态管理
    ├── api/
    │   └── client.ts       # API 客户端
    ├── types/
    │   └── index.ts        # TypeScript 类型定义
    ├── styles/
    │   └── main.css        # 全局样式
    ├── components/
    │   ├── MessageBubble.vue    # 消息气泡组件
    │   ├── ToolApprovalCard.vue # 工具审批卡片组件
    │   ├── ChatInput.vue        # 聊天输入框组件
    │   └── ThinkingPanel.vue    # 思考过程面板组件
    └── views/
        └── ChatView.vue    # 聊天主视图
```

## 开发

### 安装依赖

```bash
cd aloha/web
npm install
```

### 启动开发服务器

```bash
npm run dev
```

访问 http://localhost:5173

### 构建生产版本

```bash
npm run build
```

## 核心功能

### 1. 对话管理
- 发送消息
- 展示 AI 思考过程 (thinking block)
- 消息历史

### 2. 工具审批
- **ToolApprovalCard** - 工具调用审批卡片
  - 显示工具名称、风险级别、参数
  - 确认/拒绝按钮
  - 阻塞执行直到用户决策

### 3. 思考过程
- **ThinkingPanel** - 可折叠的思考过程展示
- **MessageBubble** - 消息气泡中的 thinking 区域

## API 接口

前端通过 `/api` 代理连接后端服务：

| 接口 | 方法 | 描述 |
|------|------|------|
| `/api/status` | GET | 获取系统状态 |
| `/api/chat` | POST | 发送聊天消息 |
| `/api/tool/execute` | POST | 工具审批执行 |
| `/api/history` | GET | 获取历史记录 |
| `/api/health` | GET | 健康检查 |

## 后端 API 服务

需要启动 `aloha/web_api.py` FastAPI 服务：

```bash
cd aloha
pip install fastapi uvicorn
python web_api.py
```

服务运行在 http://localhost:8000

## 设计参考

详细设计文档: [aloha/doc/web-ui-design.md](../doc/web-ui-design.md)

### 设计特点
- 深色主题 (GitHub Style)
- 工具审批流程阻塞式交互
- 思考过程可折叠展示
- 响应式布局