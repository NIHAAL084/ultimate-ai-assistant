from datetime import datetime
from google.adk.agents.llm_agent import Agent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters

from .prompt import TASK_MANAGEMENT_PROMPT

# Import user environment manager with correct path
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))
from app.user_env import get_user_env_var

# ---- Todoist MCP Server ----
# Using official Todoist MCP server by abhiz123
# https://github.com/abhiz123/todoist-mcp-server

TODOIST_API_TOKEN = get_user_env_var("TODOIST_API_TOKEN")
if TODOIST_API_TOKEN is None:
    print("⚠️ TODOIST_API_TOKEN not set - Task Management agent will have limited functionality")

# Environment variables for Todoist MCP server
TODOIST_ENV = {}
if TODOIST_API_TOKEN:
    TODOIST_ENV["TODOIST_API_TOKEN"] = TODOIST_API_TOKEN

def create_task_management_agent():
    """Create task management agent with dynamic current time context."""
    current_time = datetime.now().strftime("%A, %B %d, %Y at %I:%M %p")
    
    # Combine base prompt with current time context
    dynamic_prompt = f"""Current Date and Time: {current_time}

{TASK_MANAGEMENT_PROMPT}

Important: Always use the current date and time information provided above for context when creating tasks with due dates, filtering by dates, or understanding time-sensitive requests. When users refer to relative dates like "today", "tomorrow", "next week", calculate them based on the current date and time provided."""

    return Agent(
        model="gemini-2.0-flash",
        name="Task_Management_Agent", 
        instruction=dynamic_prompt,
        tools=[
            MCPToolset(
                connection_params=StdioServerParameters(
                    command="npx",
                    args=["-y", "@abhiz123/todoist-mcp-server"],
                    env=TODOIST_ENV,
                )
            ),
        ],
    )

# Create the agent instance
task_management_agent = create_task_management_agent()
