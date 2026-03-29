"""MiniMax 专用 Provider 实现

参照 Nanobot 的方案，使用 hash 将 tool_call_id 规范化为固定长度。
关键点：在整个会话中保持 ID 映射的一致性。
"""

import hashlib
import json
from typing import Any

from aloha.providers.base import Message, Response, ToolCall
from aloha.providers.openai_provider import OpenAIProvider
from aloha.lib import logger


class MiniMaxProvider(OpenAIProvider):
    """MiniMax 专用 Provider
    
    特性:
    - 规范化 tool_call_id 为固定 9 位字母数字
    - 使用 ID 映射确保同一 ID 在会话中保持一致
    - 正确处理 assistant 消息中的 tool_calls
    """
    
    def __init__(
        self,
        api_key: str,
        default_model: str = "MiniMax-M2.7",
        base_url: str | None = "https://api.minimaxi.com/v1",
        temperature: float = 0.1,
        max_tokens: int = 8192,
    ):
        super().__init__(
            api_key=api_key,
            default_model=default_model,
            base_url=base_url,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        # ID 映射表，确保同一 ID 在整个会话中保持一致
        self._id_map: dict[str, str] = {}
        logger.LOG_INFO("[MiniMaxProvider] Initialized with ID normalization")
    
    @staticmethod
    def _normalize_tool_call_id(tool_call_id: str) -> str:
        """规范化 tool_call_id 为固定 9 位字母数字
        
        参照 Nanobot 实现：使用 SHA1 hash 将任意长度的 ID 规范化为 9 位。
        """
        if not tool_call_id:
            return tool_call_id
        # 已经是 9 位字母数字则保持不变
        if len(tool_call_id) == 9 and tool_call_id.isalnum():
            return tool_call_id
        # 否则 hash 为 9 位
        return hashlib.sha1(tool_call_id.encode()).hexdigest()[:9]
    
    def _get_normalized_id(self, original_id: str) -> str:
        """获取规范化后的 ID，建立映射确保一致性
        
        使用 id_map 确保同一个原始 ID 在整个会话中映射到相同的规范化 ID。
        """
        if original_id not in self._id_map:
            normalized = self._normalize_tool_call_id(original_id)
            self._id_map[original_id] = normalized
            logger.LOG_DEBUG(f"[MiniMaxProvider] ID mapping: {original_id[:20]}... -> {normalized}")
        return self._id_map[original_id]
    
    def reset_id_map(self) -> None:
        """重置 ID 映射表（在新会话开始时调用）"""
        self._id_map.clear()
        logger.LOG_DEBUG("[MiniMaxProvider] ID mapping reset")
    
    def _convert_message(self, msg: Message) -> dict[str, Any]:
        """转换 Message 为 API 格式，规范化 tool_call_id
        
        关键处理：
        1. tool 消息的 tool_call_id 需要规范化
        2. assistant 消息的 tool_calls 中的 id 需要规范化
        """
        result = super()._convert_message(msg)
        
        # 处理 tool 消息的 tool_call_id
        if msg.role == "tool" and msg.tool_call_id:
            normalized_id = self._get_normalized_id(msg.tool_call_id)
            result["tool_call_id"] = normalized_id
            logger.LOG_DEBUG(f"[MiniMaxProvider] Tool message normalized ID: {normalized_id}")
        
        # 处理 assistant 消息的 tool_calls
        if msg.role == "assistant" and msg.tool_calls:
            normalized_tool_calls = []
            for tc in msg.tool_calls:
                normalized_id = self._get_normalized_id(tc.id)
                normalized_tool_calls.append({
                    "id": normalized_id,
                    "type": "function",
                    "function": {
                        "name": tc.name,
                        "arguments": json.dumps(tc.arguments) if isinstance(tc.arguments, dict) else tc.arguments,
                    }
                })
            result["tool_calls"] = normalized_tool_calls
            logger.LOG_DEBUG(f"[MiniMaxProvider] Assistant message normalized {len(msg.tool_calls)} tool_calls")
        
        return result