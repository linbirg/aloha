"""Agent 事件类型定义"""

from dataclasses import dataclass, field
from enum import Enum
import time


class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class ApprovalRequest:
    id: str
    tool_name: str
    action: str
    arguments: dict
    risk_level: RiskLevel
    description: str
    resource: str
    timeout: float = 300
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        risk_color_map = {
            RiskLevel.LOW: "#22c55e",
            RiskLevel.MEDIUM: "#eab308",
            RiskLevel.HIGH: "#ef4444",
        }
        return {
            "id": self.id,
            "tool_name": self.tool_name,
            "action": self.action,
            "arguments": self.arguments,
            "risk_level": self.risk_level.value,
            "risk_color": risk_color_map.get(self.risk_level, "#6b7280"),
            "description": self.description,
            "resource": self.resource,
            "timeout": self.timeout,
        }


@dataclass
class ApprovalDecision:
    approval_id: str
    decision: str
    reason: str | None
    approved_at: float
