"""
Sub-Agents Module

This module provides specialized AI agents for specific domains:
- Calendar Agent: Google Calendar management via MCP
- Task Management Agent: Todoist task and project management via MCP

Each sub-agent is designed to handle specific workflows while maintaining
the same high-quality interaction patterns as the main assistant.
"""

from .calendar_agent import calendar_agent, create_calendar_agent, CALENDAR_PROMPT
from .task_management_agent import task_management_agent, create_task_management_agent, TASK_MANAGEMENT_PROMPT

__all__ = [
    "calendar_agent",
    "create_calendar_agent",
    "CALENDAR_PROMPT", 
    "task_management_agent",
    "create_task_management_agent",
    "TASK_MANAGEMENT_PROMPT"
]
