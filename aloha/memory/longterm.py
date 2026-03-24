"""LongTerm Memory - 长期记忆

存储跨会话的信息和知识。
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class MemoryItem:
    """记忆条目"""
    id: str
    content: str
    created_at: datetime = field(default_factory=datetime.now)
    accessed_at: datetime = field(default_factory=datetime.now)
    access_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


class LongTermMemory:
    """长期记忆管理器

    简单的基于内存的实现，后续可扩展为向量数据库存储。
    """

    def __init__(self):
        self._memories: dict[str, MemoryItem] = {}

    def add(self, id: str, content: str, metadata: dict[str, Any] | None = None) -> None:
        """添加记忆"""
        self._memories[id] = MemoryItem(
            id=id,
            content=content,
            metadata=metadata or {},
        )

    def get(self, id: str) -> MemoryItem | None:
        """获取记忆"""
        item = self._memories.get(id)
        if item:
            item.accessed_at = datetime.now()
            item.access_count += 1
        return item

    def search(self, query: str, limit: int = 5) -> list[MemoryItem]:
        """搜索记忆（简单实现，后续可改为向量搜索）"""
        # 简单实现：基于关键词匹配
        results = []
        query_lower = query.lower()
        for item in self._memories.values():
            if query_lower in item.content.lower():
                results.append(item)
                if len(results) >= limit:
                    break
        return results

    def delete(self, id: str) -> bool:
        """删除记忆"""
        if id in self._memories:
            del self._memories[id]
            return True
        return False

    def all(self) -> list[MemoryItem]:
        """获取所有记忆"""
        return list(self._memories.values())

    def clear(self) -> None:
        """清空所有记忆"""
        self._memories.clear()

    def __len__(self) -> int:
        return len(self._memories)
