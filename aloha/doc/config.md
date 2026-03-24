# Aloha 配置指南

本文档详细介绍 Aloha 的配置系统。

## 配置文件位置

Aloha 会按以下顺序查找 `.env` 文件：

1. 当前目录 `./.env`
2. 项目目录 `aloha/.env`
3. 用户目录 `~/.aloha/.env`

## 环境变量配置

### 必需配置

| 环境变量 | 说明 | 示例 |
|---------|------|------|
| `OPENAI_API_KEY` | OpenAI API Key | `sk-...` |

### 可选配置

| 环境变量 | 说明 | 默认值 |
|---------|------|------|
| `OPENAI_BASE_URL` | API 基础 URL | `https://api.openai.com/v1` |
| `MODEL` | 使用的模型 | `gpt-4o-mini` |

## 配置文件格式

### JSON 格式示例 (`config.json`)

```json
{
  "agents": {
    "defaults": {
      "workspace": "~/.aloha/workspace",
      "model": "gpt-4o-mini",
      "provider": "openai",
      "maxTokens": 8192,
      "contextWindowTokens": 65536,
      "temperature": 0.1,
      "maxToolIterations": 40
    }
  },
  "providers": {
    "openai": {
      "apiKey": "sk-...",
      "baseUrl": "https://api.openai.com/v1",
      "defaultModel": "gpt-4o-mini",
      "temperature": 0.1,
      "maxTokens": 8192
    }
  },
  "tools": {
    "restrictToWorkspace": false,
    "web": {
      "provider": "brave",
      "apiKey": "brave-api-key",
      "maxResults": 5
    },
    "exec": {
      "enable": true,
      "timeout": 60,
      "pathAppend": ""
    }
  }
}
```

### TOML 格式示例 (`config.toml`)

```toml
[agents.defaults]
workspace = "~/.aloha/workspace"
model = "gpt-4o-mini"
provider = "openai"
max_tokens = 8192
context_window_tokens = 65536
temperature = 0.1
max_tool_iterations = 40

[providers.openai]
api_key = "sk-..."
base_url = "https://api.openai.com/v1"
default_model = "gpt-4o-mini"
temperature = 0.1
max_tokens = 8192

[tools]
restrict_to_workspace = false

[tools.web]
provider = "brave"
api_key = "brave-api-key"
max_results = 5

[tools.exec]
enable = true
timeout = 60
path_append = ""
```

## 配置项详解

### Agent 配置 (`agents.defaults`)

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `workspace` | string | `~/.aloha/workspace` | 工作目录路径 |
| `model` | string | `gpt-4o-mini` | 默认使用的模型 |
| `provider` | string | `auto` | LLM 提供者 (`auto`, `openai`, `anthropic`, `deepseek`, `openrouter`) |
| `max_tokens` | int | 8192 | 单次响应最大 token 数 |
| `context_window_tokens` | int | 65536 | 上下文窗口大小 |
| `temperature` | float | 0.1 | 采样温度 (0-2) |
| `max_tool_iterations` | int | 40 | 工具调用最大迭代次数 |
| `reasoning_effort` | string | null | 推理强度 (`low`, `medium`, `high`) |

### Provider 配置

#### OpenAI Provider (`providers.openai`)

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `api_key` | string | - | API Key |
| `base_url` | string | `https://api.openai.com/v1` | API 基础 URL |
| `default_model` | string | `gpt-4o-mini` | 默认模型 |
| `temperature` | float | 0.1 | 采样温度 |
| `max_tokens` | int | 8192 | 最大 token 数 |

#### Anthropic Provider (`providers.anthropic`)

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `api_key` | string | - | Anthropic API Key |
| `base_url` | string | `https://api.anthropic.com` | API 基础 URL |
| `default_model` | string | `claude-3-5-sonnet-20241022` | 默认模型 |

#### DeepSeek Provider (`providers.deepseek`)

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `api_key` | string | - | DeepSeek API Key |
| `base_url` | string | `https://api.deepseek.com` | API 基础 URL |
| `default_model` | string | `deepseek-chat` | 默认模型 |

#### OpenRouter Provider (`providers.openrouter`)

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `api_key` | string | - | OpenRouter API Key |
| `base_url` | string | `https://openrouter.ai/api/v1` | API 基础 URL |

### 工具配置 (`tools`)

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `restrict_to_workspace` | bool | false | 是否限制工具只能访问工作目录 |

#### Web Search (`tools.web`)

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `provider` | string | `brave` | Web 搜索提供者 (`brave`) |
| `api_key` | string | - | 搜索 API Key |
| `max_results` | int | 5 | 最大返回结果数 |

#### Exec (`tools.exec`)

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `enable` | bool | true | 是否启用执行功能 |
| `timeout` | int | 60 | 命令超时时间(秒) |
| `path_append` | string | - | 额外添加到 PATH 的目录 |

## 使用代码加载配置

```python
from aloha.config import get_config, AlohaConfig

# 获取默认配置
config = get_config()

# 从文件加载
config = AlohaConfig.from_file("~/.aloha/config.json")
```

## 优先级

配置优先级（从高到低）：

1. 环境变量（如 `OPENAI_API_KEY`）
2. 配置文件（`config.json` / `config.toml`）
3. 代码默认值
