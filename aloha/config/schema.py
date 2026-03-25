"""Aloha 配置模型定义

使用 Pydantic 进行配置验证，支持从 .env 文件加载环境变量。
"""

from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from pydantic import BaseModel, Field

from aloha.lib import logger


def _load_env() -> None:
    """加载 .env 文件"""
    # 尝试从当前目录和项目根目录加载 .env
    env_paths = [
        Path(".env"),
        Path(__file__).parent.parent / ".env",
        Path.home() / ".aloha" / ".env",
    ]
    for env_path in env_paths:
        if env_path.exists():
            load_dotenv(env_path)
            break


# 初始化时加载 .env
_load_env()


class ProviderConfig(BaseModel):
    """LLM Provider 配置"""
    api_key: str = ""
    base_url: str | None = None
    default_model: str = "gpt-4o-mini"
    temperature: float = 0.1
    max_tokens: int = 8192


class WebSearchConfig(BaseModel):
    """Web Search 工具配置"""
    provider: str = "brave"
    api_key: str = ""
    max_results: int = 5


class ExecToolConfig(BaseModel):
    """执行工具配置"""
    enable: bool = True
    timeout: int = 60
    path_append: str = ""


class ToolsConfig(BaseModel):
    """工具配置"""
    restrict_to_workspace: bool = False
    web: WebSearchConfig | None = None
    exec_config: ExecToolConfig | None = None


class AgentDefaultsConfig(BaseModel):
    """Agent 默认配置"""
    workspace: str = "~/.aloha/workspace"
    model: str = "MiniMax-M2.7"
    provider: str = "auto"
    max_tokens: int = 8192
    context_window_tokens: int = 65536
    temperature: float = 0.1
    max_tool_iterations: int = 40
    reasoning_effort: str | None = None


class AgentsConfig(BaseModel):
    """Agents 配置"""
    defaults: AgentDefaultsConfig = Field(default_factory=AgentDefaultsConfig)


class ProvidersConfig(BaseModel):
    """Providers 配置"""
    openai: ProviderConfig | None = None
    anthropic: ProviderConfig | None = None
    deepseek: ProviderConfig | None = None
    openrouter: ProviderConfig | None = None


class AlohaConfig(BaseModel):
    """Aloha 完整配置"""
    agents: AgentsConfig = Field(default_factory=AgentsConfig)
    providers: ProvidersConfig = Field(default_factory=ProvidersConfig)
    tools: ToolsConfig = Field(default_factory=ToolsConfig)

    @classmethod
    def from_file(cls, path: Path | str) -> "AlohaConfig":
        """从文件加载配置"""
        import json
        import tomli

        path = Path(path)
        # 使用 UTF-8 编码读取
        content = path.read_text(encoding="utf-8")

        if path.suffix == ".json":
            data = json.loads(content)
        elif path.suffix in (".toml",):
            data = tomli.loads(content)
        else:
            raise ValueError(f"Unsupported config format: {path.suffix}")

        return cls(**data)


# 全局配置实例
_config: AlohaConfig | None = None


def _resolve_env_vars(value: Any) -> Any:
    """递归解析配置值中的环境变量引用
    
    支持格式：
    - "VAR_NAME" -> 从环境变量读取
    - "prefix_${VAR_NAME}_suffix" -> 替换环境变量
    """
    import os
    
    if isinstance(value, str):
        # 检查是否是环境变量引用（如 "MINIMAX_API_KEY"）
        if value.startswith("${") and value.endswith("}"):
            var_name = value[2:-1]
            return os.getenv(var_name, value)
        # 检查是否包含环境变量引用（如 "prefix_${VAR}_suffix"）
        elif "$" in value:
            import re
            def replace_env_var(match):
                var_name = match.group(1)
                return os.getenv(var_name, match.group(0))
            return re.sub(r'\$\{([^}]+)\}', replace_env_var, value)
        return value
    elif isinstance(value, dict):
        return {k: _resolve_env_vars(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [_resolve_env_vars(item) for item in value]
    return value


def _resolve_config_env_vars(config: AlohaConfig) -> AlohaConfig:
    """解析配置中的环境变量引用"""
    import os
    import json
    
    # 将 config 转换为 dict
    config_dict = config.model_dump()
    
    # 递归解析环境变量
    resolved_dict = _resolve_env_vars(config_dict)
    
    # 重新创建 config 对象
    return AlohaConfig(**resolved_dict)


def get_config() -> AlohaConfig:
    """获取全局配置实例，自动加载配置文件"""
    global _config
    if _config is None:
        # 尝试加载配置文件
        config_paths = [
            Path.home() / ".aloha" / "config.toml",
            Path.home() / ".aloha" / "config.json",
            Path(__file__).parent.parent / "config.toml",
            Path(__file__).parent.parent / "config.json",
        ]
        for config_path in config_paths:
            if config_path.exists():
                try:
                    _config = AlohaConfig.from_file(config_path)
                    # 解析环境变量
                    _config = _resolve_config_env_vars(_config)
                    logger.LOG_INFO(f"Loaded config from: {config_path}")
                    break
                except Exception as e:
                    logger.LOG_WARNING(f"Failed to load {config_path}: {e}")
        
        if _config is None:
            _config = AlohaConfig()
    
    return _config


def set_config(config: AlohaConfig) -> None:
    """设置全局配置"""
    global _config
    _config = config
