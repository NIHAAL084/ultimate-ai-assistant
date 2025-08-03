from datetime import datetime
import warnings
import logging
from google.adk.agents.llm_agent import Agent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioConnectionParams, StdioServerParameters
from typing import Optional, Dict
import os

# Suppress specific warnings from ADK
warnings.filterwarnings("ignore", message=".*BaseAuthenticatedTool.*experimental.*")
warnings.filterwarnings("ignore", message=".*auth_config.*auth_scheme.*missing.*")

# Reduce logging verbosity for MCP tools
logging.getLogger("google.adk.tools.mcp_tool").setLevel(logging.ERROR)
# Suppress MCP-related asyncio errors during shutdown
logging.getLogger("mcp").setLevel(logging.WARNING)
logging.getLogger("mcp.client").setLevel(logging.WARNING)
logging.getLogger("mcp.client.stdio").setLevel(logging.WARNING)

from .prompt import GMAIL_PROMPT

# Import credentials manager
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))
from app.credentials import get_user_env_for_agent


def get_gmail_env_for_user(user_id: Optional[str] = None) -> Dict[str, str]:
    """Get Gmail environment variables for a specific user."""
    if not user_id:
        print(f"⚠️ No user_id provided - Gmail agent will have limited functionality")
        return {}
    
    # Use new credentials system
    gmail_env = get_user_env_for_agent(user_id, 'gmail')
    
    if not gmail_env.get("GMAIL_OAUTH_PATH"):
        print(f"⚠️ GMAIL_OAUTH_PATH not set for user {user_id} - Gmail agent will have limited functionality")

    return gmail_env


def create_gmail_agent(user_id: Optional[str] = None) -> Agent:
    """Create Gmail agent with dynamic current time context and user-specific environment."""
    current_time = datetime.now().strftime("%A, %B %d, %Y at %I:%M %p")
    
    # Get user-specific Gmail environment
    gmail_env = get_gmail_env_for_user(user_id)
    
    # Combine base prompt with current time context
    dynamic_prompt = f"""Current Date and Time: {current_time}

{GMAIL_PROMPT}

Important: Always use the current date and time information provided above for context when working with emails. When users refer to relative dates like "today", "yesterday", "this week", calculate them based on the current date and time provided."""

    return Agent(
        model="gemini-2.5-flash-lite",
        name="Gmail_Agent",
        instruction=dynamic_prompt,
        tools=[
            MCPToolset(
                connection_params=StdioConnectionParams(
                    server_params=StdioServerParameters(
                        command="uv",
                        args=["run", "npx", "@gongrzhe/server-gmail-autoauth-mcp"],
                        env=gmail_env,
                    ),
                    timeout=60.0,
                )
            ),
        ],
    )

# Agent creation function available for dynamic instantiation
