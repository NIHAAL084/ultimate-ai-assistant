from google.adk.agents import Agent

from google.adk.tools import google_search
from .tools import get_current_time


root_agent = Agent(
    # A unique name for the agent.
    name="assistant",
    model="gemini-2.0-flash-exp",
    description="Agent to help with online search.",
    instruction=f"""
    You are an ai assistant that can perform various tasks 
    using online search. You can answer questions, provide information, and assist with tasks by searching the web.
    

    Important:
    - Be super concise in your responses and only return the information requested (not extra information).
    - NEVER show the raw response from a tool_outputs. Instead, use the information to answer the question.
    - NEVER show ```tool_outputs...``` in your response.

    Today's date is {get_current_time()}.
    """,
    tools=[
        google_search,
    ],
)
