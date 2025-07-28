from google.adk.agents import Agent
from google.adk.tools import google_search, load_memory
from google.adk.tools.agent_tool import AgentTool
from .tools import process_document_tool, register_uploaded_files_tool, list_available_user_files_tool
from .prompt import PRIMARY_ASSISTANT_PROMPT
from .sub_agents import calendar_agent, task_management_agent
from datetime import datetime


def create_agent() -> Agent:
    """Create agent with dynamic datetime in the instruction"""
    current_time = datetime.now().strftime("%A, %B %d, %Y at %I:%M %p")
    
    # Combine base prompt with current time context
    dynamic_prompt = f"""Current Date and Time: {current_time}

{PRIMARY_ASSISTANT_PROMPT}

Important: Always use the current date and time information provided above for context when handling time-sensitive requests, scheduling, or understanding relative time references."""
    
    # Create AgentTools for sub-agents
    calendar_tool = AgentTool(agent=calendar_agent)
    task_management_tool = AgentTool(agent=task_management_agent)
    
    return Agent(
        name="assistant",
        model="gemini-2.0-flash-exp",
        description="Agent to help with online search, document processing, image analysis, and remembering past conversations.",
        instruction=dynamic_prompt,
        tools=[
            google_search,
            load_memory,
            process_document_tool,
            register_uploaded_files_tool,
            list_available_user_files_tool,
            calendar_tool,
            task_management_tool
        ],
    )


# Create the agent instance
root_agent = create_agent()
