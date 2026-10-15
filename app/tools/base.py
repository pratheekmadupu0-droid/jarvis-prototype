"""
JARVIS Tool Base Architecture
Defines the Tool interface, result contract, and tool parameter specs.
"""

from __future__ import annotations
from typing import Dict, Any, Callable, Optional
from dataclasses import dataclass, field


@dataclass
class ToolResult:
    """Standardized response from tool execution."""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    requires_confirmation: bool = False
    confirmation_prompt: Optional[str] = None
    confirmation_payload: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "message": self.message,
            "data": self.data or {},
            "requires_confirmation": self.requires_confirmation,
            "confirmation_prompt": self.confirmation_prompt
        }


class BaseTool:
    """Abstract base class for all JARVIS tools."""

    name: str = ""
    description: str = ""
    parameters_schema: Dict[str, Any] = {}

    def execute(self, **kwargs) -> ToolResult:
        raise NotImplementedError("Tools must implement execute()")
