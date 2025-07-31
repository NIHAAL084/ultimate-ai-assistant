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

from .prompt import GMAIL_PROMPT

# Import user environment manager with correct path
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))
from app.user_env import UserEnvironmentManager


def get_gmail_env_for_user(user_id: Optional[str] = None) -> Dict[str, str]:
    """Get Gmail environment variables for a specific user."""
    if user_id:
        try:
            # Normalize user_id to lowercase
            normalized_user_id = user_id.lower().strip()
            user_env = UserEnvironmentManager(normalized_user_id)
            
            # Gmail MCP Server expects OAuth credentials similar to calendar
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
        print(f"⚠️ GOOGLE_OAUTH_CREDENTIALS not set for user {user_id or 'default'} - Gmail agent will have limited functionality")
    
    # Environment variables for Gmail MCP server
    gmail_env: Dict[str, str] = {}
    if google_oauth_credentials and user_id:
        # Set up user-specific Gmail paths in user_data
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
        user_data_dir = os.path.join(project_root, "user_data")
        gmail_credentials_dir = os.path.join(user_data_dir, "gmail_credentials")
        
        # Ensure the gmail_credentials directory exists
        os.makedirs(gmail_credentials_dir, exist_ok=True)
        
        # Use the OAuth file as the GMAIL_OAUTH_PATH (this is the gcp-oauth.keys.json equivalent)
        gmail_env["GMAIL_OAUTH_PATH"] = google_oauth_credentials
        
        # Set user-specific credentials path
        normalized_user_id = user_id.lower().strip()
        gmail_env["GMAIL_CREDENTIALS_PATH"] = os.path.join(gmail_credentials_dir, f"credentials_{normalized_user_id}.json")
    
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
