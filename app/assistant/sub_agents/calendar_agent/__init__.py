"""
Calendar Agent - Google Calendar MCP Server Integration

This module provides a specialized agent for managing Google Calendar events
using the official Google Calendar MCP server by nspady.
"""

from .agent import create_calendar_agent
from .prompt import CALENDAR_PROMPT

__all__ = ["create_calendar_agent", "CALENDAR_PROMPT"]
