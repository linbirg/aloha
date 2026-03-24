# Aloha 安装指南

## 环境要求

- Python 3.10+
- pip

## 安装步骤

### 1. 克隆项目

```bash
git clone https://github.com/your-repo/aloha.git
cd aloha
```

### 2. 安装依赖

```bash
pip install -r aloha/requirements.txt
```

### 3. 配置 API Key

在 `~/.aloha/` 目录下创建 `.env` 文件：

```bash
mkdir -p ~/.aloha
```

创建 `~/.aloha/.env` 文件：

```bash
# MiniMax API 配置
OPENAI_API_KEY=your-actual-api-key-here
OPENAI_BASE_URL=https://api.minimaxi.com/v1
MODEL=MiniMax-M2.7
```

或创建 `~/.aloha/config.toml` 配置文件：

```toml
[providers.openai]
api_key = "your-actual-api-key-here"
base_url = "https://api.minimaxi.com/v1"
default_model = "MiniMax-M2.7"
```

### 4. 运行测试

```bash
cd aloha
python -m pytest aloha/test/test_agent.py -v
```

### 5. 启动交互式 Chat

```bash
python -m aloha chat
```

或发送单条消息：

```bash
python -m aloha say "你好"
```

## 项目结构

```
aloha/
├── __init__.py          # 项目入口
├── __main__.py          # 命令行入口
├── agent/               # Agent 核心模块
│   ├── base.py         # Agent 基类
│   └── loop.py         # AgentLoop 主循环
├── bus/                 # 消息总线
├── config/              # 配置系统
│   └── schema.py       # Pydantic 配置模型
├── examples/            # 示例代码
├── lib/                 # 工具库
│   └── logger.py       # 日志模块
├── memory/              # 记忆系统
│   ├── session.py      # 会话记忆
│   └── longterm.py     # 长期记忆
├── providers/           # LLM 提供者
│   ├── base.py        # Provider 基类
│   └── openai_provider.py
├── skills/             # 技能系统
│   └── loader.py
├── test/               # 测试用例
└── tools/              # 工具系统
```

## 配置说明

详细配置说明请参阅 [config.md](config.md)。

## 常见问题

### Q: 如何切换不同的 LLM Provider？

修改 `~/.aloha/.env` 文件：

```bash
# 使用 OpenAI
OPENAI_API_KEY=sk-...
OPENAI_BASE_URL=https://api.openai.com/v1
MODEL=gpt-4o-mini

# 使用 Anthropic
OPENAI_API_KEY=sk-ant-...
OPENAI_BASE_URL=https://api.anthropic.com
MODEL=claude-3-5-sonnet-20241022
```

### Q: 日志在哪里查看？

日志默认输出到 stderr。如需保存到文件，可在代码中配置：

```python
from aloha.lib.logger import _logger
_logger.set_log_file(open("aloha.log", "a"))
```

### Q: 如何添加自定义工具？

```python
from aloha.tools import BaseTool
from aloha.tools.base import ToolResult

class MyTool(BaseTool):
    def __init__(self):
        super().__init__(name="mytool", description="我的工具")
    
    async def execute(self, **kwargs) -> ToolResult:
        # 实现你的工具逻辑
        return ToolResult(success=True, content="结果")

agent.add_tool(MyTool())
```
