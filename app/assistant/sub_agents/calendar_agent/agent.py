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

from .prompt import CALENDAR_PROMPT

# Import user environment manager with correct path
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))
from app.user_env import UserEnvironmentManager


def get_calendar_env_for_user(user_id: Optional[str] = None) -> Dict[str, str]:
    """Get calendar environment variables for a specific user."""
    if user_id:
        try:
            # Normalize user_id to lowercase
            normalized_user_id = user_id.lower().strip()
            user_env = UserEnvironmentManager(normalized_user_id)
            google_oauth_credentials = user_env.get_env_var("GOOGLE_OAUTH_CREDENTIALS")
            
            # Resolve relative paths to absolute paths
            if google_oauth_credentials and not os.path.isabs(google_oauth_credentials):
                # Get the project root directory (ultimate-ai-assistant)
                project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
                google_oauth_credentials = os.path.join(project_root, google_oauth_credentials)
                
        except Exception:
            # Fall back to None if user-specific environment is not available
            google_oauth_credentials = None
    else:
        # No user_id provided, use None
        google_oauth_credentials = None
    
    if google_oauth_credentials is None:
        print(f"⚠️ GOOGLE_OAUTH_CREDENTIALS not set for user {user_id or 'default'} - Calendar agent will have limited functionality")
    
    # Environment variables for Google Calendar MCP server
    calendar_env: Dict[str, str] = {}
    if google_oauth_credentials:
        calendar_env["GOOGLE_OAUTH_CREDENTIALS"] = google_oauth_credentials
    
    return calendar_env


def create_calendar_agent(user_id: Optional[str] = None) -> Agent:
    """Create calendar agent with dynamic current time context and user-specific environment."""
    current_time = datetime.now().strftime("%A, %B %d, %Y at %I:%M %p")
    
    # Get user-specific calendar environment
    calendar_env = get_calendar_env_for_user(user_id)
    
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
                connection_params=StdioConnectionParams(
                    server_params=StdioServerParameters(
                        command="uv",
                        args=["run", "npx", "@cocal/google-calendar-mcp"],
                        env=calendar_env,
                    ),
                    timeout=60.0,
                )
            ),
        ],
    )

# Agent creation function available for dynamic instantiation
 