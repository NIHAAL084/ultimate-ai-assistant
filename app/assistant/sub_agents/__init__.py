"""
Sub-Agents Module

This module provides specialized AI agents for specific domains:
- Calendar Agent: Google Calendar management via MCP
- Task Management Agent: Todoist task and project management via MCP
- Gmail Agent: Gmail email management via MCP

Each sub-agent is designed to handle specific workflows while maintaining
the same high-quality interaction patterns as the main assistant.
"""

from .calendar_agent import create_calendar_agent, CALENDAR_PROMPT
from .task_management_agent import create_task_management_agent, TASK_MANAGEMENT_PROMPT
from .gmail_agent import create_gmail_agent

__all__ = [
    "create_calendar_agent",
    "CALENDAR_PROMPT", 
    "create_task_management_agent",
    "TASK_MANAGEMENT_PROMPT",
    "create_gmail_agent"
]
