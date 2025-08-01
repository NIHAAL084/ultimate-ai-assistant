from google.adk.agents import Agent
from google.adk.tools import google_search, load_memory
from google.adk.tools.agent_tool import AgentTool
from .tools import process_document_tool, register_uploaded_files_tool, list_available_user_files_tool
from .tools.a2a_tools import list_available_agents, send_message_to_agent, get_agent_capabilities, discover_new_agents
from .prompt import PRIMARY_ASSISTANT_PROMPT
from .sub_agents import create_calendar_agent, create_task_management_agent, create_gmail_agent
from datetime import datetime


from typing import Optional


def create_agent(user_id: Optional[str] = None) -> Agent:
    """Create agent with dynamic datetime in the instruction and user-specific sub-agents"""
    current_time = datetime.now().strftime("%A, %B %d, %Y at %I:%M %p")
    
    # Combine base prompt with current time context
    dynamic_prompt = f"""Current Date and Time: {current_time}

{PRIMARY_ASSISTANT_PROMPT}

Important: Always use the current date and time information provided above for context when handling time-sensitive requests, scheduling, or understanding relative time references."""
    
    # Create AgentTools for sub-agents with user-specific configuration
    calendar_agent = create_calendar_agent(user_id=user_id)
    calendar_tool = AgentTool(agent=calendar_agent)
    
    task_management_agent = create_task_management_agent(user_id=user_id)  
    task_management_tool = AgentTool(agent=task_management_agent)
    
    gmail_agent = create_gmail_agent(user_id=user_id)
    gmail_tool = AgentTool(agent=gmail_agent)
    
    return Agent(
        name="assistant",
        model="gemini-live-2.5-flash-preview",
        description="Agent to help with online search, document processing, image analysis, and remembering past conversations.",
        instruction=dynamic_prompt,
        tools=[
            google_search,
            load_memory,
            process_document_tool,
            register_uploaded_files_tool,
            list_available_user_files_tool,
            calendar_tool,
            task_management_tool,
            gmail_tool,
            # A2A client tools for communicating with other agents
            list_available_agents,
            send_message_to_agent,
            get_agent_capabilities,
            discover_new_agents,
        ],
    )
