from datetime import datetime
import warnings
import logging
from google.adk.agents.llm_agent import Agent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioConnectionParams, StdioServerParameters
from typing import Optional, Dict

# Suppress specific warnings from ADK
warnings.filterwarnings("ignore", message=".*BaseAuthenticatedTool.*experimental.*")
warnings.filterwarnings("ignore", message=".*auth_config.*auth_scheme.*missing.*")

# Reduce logging verbosity for MCP tools
logging.getLogger("google.adk.tools.mcp_tool").setLevel(logging.ERROR)

from .prompt import TASK_MANAGEMENT_PROMPT

# Import user environment manager with correct path
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))
from app.user_env import get_user_env_var, UserEnvironmentManager

# ---- Todoist MCP Server ----
# Using Gemini-compatible Todoist MCP server by nihaal084
# https://github.com/NIHAAL084/todoist-mcp-server
# Fixed version of @abhiz123/todoist-mcp-server with enum type compatibility

def get_task_env_for_user(user_id: Optional[str] = None) -> Dict[str, str]:
    """Get task management environment variables for a specific user."""
    if user_id:
        try:
            # Normalize user_id to lowercase
            normalized_user_id = user_id.lower().strip()
            user_env = UserEnvironmentManager(normalized_user_id)
            todoist_api_token = user_env.get_env_var("TODOIST_API_TOKEN")
        except (ImportError, FileNotFoundError, KeyError):
            # Fall back to None if user-specific environment is not available
            todoist_api_token = None
    else:
        # No user_id provided, use None
        todoist_api_token = None
    
    if todoist_api_token is None:
        print(f"⚠️ TODOIST_API_TOKEN not set for user {user_id or 'default'} - Task Management agent will have limited functionality")

    # Environment variables for Todoist MCP server
    task_env: Dict[str, str] = {}
    if todoist_api_token:
        task_env["TODOIST_API_TOKEN"] = todoist_api_token
    
    return task_env

def create_task_management_agent(user_id: Optional[str] = None) -> Agent:
    """Create task management agent with dynamic current time context and user-specific environment."""
    current_time = datetime.now().strftime("%A, %B %d, %Y at %I:%M %p")
    
    # Get user-specific task environment
    task_env = get_task_env_for_user(user_id)
    
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
                connection_params=StdioConnectionParams(
                    server_params=StdioServerParameters(
                        command="uv",
                        args=["run", "npx", "-y", "@nihaal084/todoist-mcp-server"],
                        env=task_env,
                    ),
                    timeout=60.0,
                )
            ),
        ],
    )

# Agent creation function available for dynamic instantiation
