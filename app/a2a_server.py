"""
A2A Server setup for ZORA Assistant.
This allows other agents to communicate with ZORA using the Agent-to-Agent protocol.
"""

import logging
import os
from typing import Optional, Dict, Any

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)
from google.adk.artifacts import InMemoryArtifactService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

from .a2a_agent_executor import ZoraAgentExecutor
from .assistant.agent import create_agent
from .assistant.utils.zep_memory_service import ZepMemoryService
from .config import APP_NAME, A2A_SERVER_DEFAULT_USER, NGROK_URL, ACTIVATE_A2A_SERVER, A2A_HOST, A2A_PORT

logger = logging.getLogger(__name__)


def create_a2a_server(host: str = "localhost", port: int = 10003, user_id: Optional[str] = None) -> A2AStarletteApplication:
    """
    Creates an A2A server for ZORA Assistant.
    
    Args:
        host: Host to bind the A2A server to
        port: Port to bind the A2A server to
        user_id: User ID for the A2A server agent context
        
    Returns:
        A2AStarletteApplication instance ready to serve
    """
    # Use provided user_id or fall back to config default
    if user_id is None:
        user_id = A2A_SERVER_DEFAULT_USER
        
    logger.info(f"Creating A2A server for ZORA on {host}:{port} with user_id: {user_id}")
    
    try:
        # Define agent capabilities
        capabilities = AgentCapabilities(streaming=True)
        
        # Define agent skills
        skills = [
            AgentSkill(
                id="web_search",
                name="Web Search & Research",
                description="Search the web for information and provide detailed research.",
                tags=["search", "research", "web"],
                examples=["Search for the latest news about AI", "Research quantum computing"],
            ),
            AgentSkill(
                id="document_processing",
                name="Document Analysis",
                description="Process, analyze and extract information from documents and images.",
                tags=["documents", "analysis", "ocr"],
                examples=["Analyze this PDF document", "Extract text from this image"],
            ),
            AgentSkill(
                id="task_management",
                name="Task & Project Management",
                description="Manage tasks, projects, and to-do lists using Todoist integration.",
                tags=["tasks", "productivity", "todoist"],
                examples=["Add a task to my project", "Show my upcoming deadlines"],
            ),
            AgentSkill(
                id="calendar_management",
                name="Calendar Management",
                description="Manage calendar events, scheduling, and availability using Google Calendar.",
                tags=["calendar", "scheduling", "events"],
                examples=["Schedule a meeting for tomorrow", "Check my availability next week"],
            ),
            AgentSkill(
                id="email_management",
                name="Email Management",
                description="Read, compose, and manage emails using Gmail integration.",
                tags=["email", "gmail", "communication"],
                examples=["Check my latest emails", "Send an email to John"],
            ),
            AgentSkill(
                id="memory_retrieval",
                name="Conversation Memory",
                description="Access and recall information from previous conversations and interactions.",
                tags=["memory", "history", "context"],
                examples=["What did we discuss yesterday?", "Remember my project preferences"],
            ),
        ]
        
        # Create agent card
        agent_card = AgentCard(
            name="ZORA Assistant",
            description="ZORA is a comprehensive AI assistant with voice interaction, persistent memory, and real-world integrations including web search, document processing, task management, calendar, and email.",
            url=NGROK_URL,
            version="1.0.0",
            defaultInputModes=["text/plain"],
            defaultOutputModes=["text/plain"],
            capabilities=capabilities,
            skills=skills,
        )

        # Create ADK agent with configured user for A2A requests
        adk_agent = create_agent(user_id=user_id)
        
        # Initialize memory service
        try:
            memory_service = ZepMemoryService()
            logger.info("✅ ZepMemoryService initialized for A2A server")
        except Exception as e:
            logger.warning(f"⚠️ Failed to initialize ZepMemoryService for A2A server: {e}")
            memory_service = None
        
        # Create runner
        runner = Runner(
            app_name=APP_NAME,
            agent=adk_agent,
            artifact_service=InMemoryArtifactService(),
            session_service=InMemorySessionService(),
            memory_service=memory_service,
        )
        
        # Create agent executor
        agent_executor = ZoraAgentExecutor(runner)

        # Create request handler
        request_handler = DefaultRequestHandler(
            agent_executor=agent_executor,
            task_store=InMemoryTaskStore(),
        )
        
        # Create A2A server
        server = A2AStarletteApplication(
            agent_card=agent_card, 
            http_handler=request_handler
        )
        
        logger.info(f"✅ A2A server created successfully for ZORA on {host}:{port}")
        return server
        
    except Exception as e:
        logger.error(f"💥 Failed to create A2A server: {e}")
        raise


def get_a2a_config() -> Dict[str, Any]:
    """Get A2A server configuration from environment variables."""
    return {
        "enabled": os.getenv("ACTIVATE_A2A_SERVER", str(ACTIVATE_A2A_SERVER)).lower() == "true",
        "host": os.getenv("A2A_HOST", "0.0.0.0"),
        "port": int(os.getenv("A2A_PORT", "80")),
        "user_id": os.getenv("A2A_SERVER_USER_ID", A2A_SERVER_DEFAULT_USER),
    }
