"""
JARVIS Tool Registry
Maintains registered tools, exports OpenAI/OpenRouter function-calling schemas,
dispatches executions with parameter validation, and logs actions.
"""

from __future__ import annotations
from typing import Dict, Any, List, Optional
from app.tools.base import BaseTool, ToolResult
from app.storage.database import db
from app.security.guardrails import SecurityGuardrails

# Tool imports
from app.tools.filesystem_tools import (
    CreateFolderTool, CreateFileTool, ReadFileTool, ListDirectoryTool, CreateProjectStructureTool, OpenFolderTool
)
from app.tools.system_tools import (
    LaunchApplicationTool, OpenUrlTool, CloseApplicationTool, SystemControlTool
)
from app.tools.time_tools import (
    GetTimeTool, GetDateTool, CalculateTimeUntilTool
)
from app.scheduler.timer_manager import (
    SetTimerTool, SetReminderTool, ListRemindersTool, CancelReminderTool
)
from app.integrations.weather.weather_client import GetWeatherTool
from app.integrations.news.news_client import GetNewsTool
from app.integrations.youtube.youtube_client import SearchYouTubeTool
from app.integrations.whatsapp.whatsapp_desktop import (
    WhatsAppDraftTool, WhatsAppSendConfirmedTool, WhatsAppOpenTool
)
from app.integrations.email.gmail_client import (
    GmailUnreadTool, GmailDraftTool, GmailSendConfirmedTool
)
from app.browser.playwright_controller import (
    WebSearchTool, BrowserNavigateTool
)


class ToolRegistry:
    """Central registry of all available JARVIS capabilities."""

    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        self._register_default_tools()

    def register(self, tool: BaseTool):
        self._tools[tool.name] = tool

    def get_tool(self, name: str) -> Optional[BaseTool]:
        return self._tools.get(name)

    def list_tools(self) -> List[BaseTool]:
        return list(self._tools.values())

    def get_openai_tools_schema(self) -> List[Dict[str, Any]]:
        """Format tools for OpenAI / OpenRouter function calling API."""
        schemas = []
        for tool in self._tools.values():
            schemas.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters_schema
                }
            })
        return schemas

    def execute_tool(self, name: str, arguments: Dict[str, Any]) -> ToolResult:
        """Safely execute a tool with error handling and task logging."""
        if SecurityGuardrails.is_stopped():
            return ToolResult(success=False, message="Operation halted by Emergency Stop.")

        tool = self.get_tool(name)
        if not tool:
            return ToolResult(success=False, message=f"Unknown tool '{name}'.")

        # Log start
        task_id = db.log_task(task_name=name, intent=f"Execute {name}", status="executing", details=arguments)

        try:
            result = tool.execute(**arguments)
            status = "completed" if result.success else "failed"
            if result.requires_confirmation:
                status = "awaiting_confirmation"

            db.update_task_status(task_id, status=status, details={
                "args": arguments,
                "result_message": result.message,
                "success": result.success
            })
            return result
        except Exception as e:
            err_msg = f"Error executing tool '{name}': {str(e)}"
            db.update_task_status(task_id, status="failed", details={"error": err_msg})
            return ToolResult(success=False, message=err_msg)

    def _register_default_tools(self):
        # Filesystem
        self.register(CreateFolderTool())
        self.register(CreateFileTool())
        self.register(ReadFileTool())
        self.register(ListDirectoryTool())
        self.register(CreateProjectStructureTool())
        self.register(OpenFolderTool())

        # System
        self.register(LaunchApplicationTool())
        self.register(OpenUrlTool())
        self.register(CloseApplicationTool())
        self.register(SystemControlTool())

        # Time
        self.register(GetTimeTool())
        self.register(GetDateTool())
        self.register(CalculateTimeUntilTool())

        # Scheduler
        self.register(SetTimerTool())
        self.register(SetReminderTool())
        self.register(ListRemindersTool())
        self.register(CancelReminderTool())

        # Integrations
        self.register(GetWeatherTool())
        self.register(GetNewsTool())
        self.register(SearchYouTubeTool())

        # WhatsApp Desktop
        self.register(WhatsAppOpenTool())
        self.register(WhatsAppDraftTool())
        self.register(WhatsAppSendConfirmedTool())

        # Gmail
        self.register(GmailUnreadTool())
        self.register(GmailDraftTool())
        self.register(GmailSendConfirmedTool())

        # Browser
        self.register(WebSearchTool())
        self.register(BrowserNavigateTool())


registry = ToolRegistry()
