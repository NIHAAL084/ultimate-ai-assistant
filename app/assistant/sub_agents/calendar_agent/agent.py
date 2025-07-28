from datetime import datetime
from google.adk.agents.llm_agent import Agent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters

from .prompt import CALENDAR_PROMPT

# Import user environment manager with correct path
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))
from app.user_env import get_user_env_var

# ---- Google Calendar MCP Server ----
# Using official Google Calendar MCP server by nspady
# https://github.com/nspady/google-calendar-mcp

GOOGLE_OAUTH_CREDENTIALS = get_user_env_var("GOOGLE_OAUTH_CREDENTIALS")
if GOOGLE_OAUTH_CREDENTIALS is None:
    print("⚠️ GOOGLE_OAUTH_CREDENTIALS not set - Calendar agent will have limited functionality")

# Environment variables for Google Calendar MCP server
GOOGLE_CALENDAR_ENV = {}
if GOOGLE_OAUTH_CREDENTIALS:
    GOOGLE_CALENDAR_ENV["GOOGLE_OAUTH_CREDENTIALS"] = GOOGLE_OAUTH_CREDENTIALS

# Optional: Custom token storage location
GOOGLE_CALENDAR_MCP_TOKEN_PATH = get_user_env_var("GOOGLE_CALENDAR_MCP_TOKEN_PATH")
if GOOGLE_CALENDAR_MCP_TOKEN_PATH:
    GOOGLE_CALENDAR_ENV["GOOGLE_CALENDAR_MCP_TOKEN_PATH"] = GOOGLE_CALENDAR_MCP_TOKEN_PATH

def create_calendar_agent():
    """Create calendar agent with dynamic current time context."""
    current_time = datetime.now().strftime("%A, %B %d, %Y at %I:%M %p")
    
    # Combine base prompt with current time context
    dynamic_prompt = f"""Current Date and Time: {current_time}

{CALENDAR_PROMPT}

Important: Always use the current date and time information provided above for context when scheduling, searching, or managing calendar events. When users refer to relative dates like "today", "tomorrow", "next week", calculate them based on the current date and time provided."""

    return Agent(
        model="gemini-2.0-flash",
        name="Calendar_Agent",
        instruction=dynamic_prompt,
        tools=[
            MCPToolset(
                connection_params=StdioServerParameters(
                    command="npx",
                    args=["@cocal/google-calendar-mcp"],
                    env=GOOGLE_CALENDAR_ENV,
                )
            ),
        ],
    )

# Create the agent instance
calendar_agent = create_calendar_agent()
