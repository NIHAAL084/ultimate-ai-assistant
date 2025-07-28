"""
Task Management Agent - Todoist MCP Server Integration

This module provides a specialized agent for managing tasks and projects
using the official Todoist MCP server by abhiz123.
"""

from .agent import create_task_management_agent
from .prompt import TASK_MANAGEMENT_PROMPT

__all__ = ["create_task_management_agent", "TASK_MANAGEMENT_PROMPT"]

