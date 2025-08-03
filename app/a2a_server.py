"""
A2A Server setup for ZORA Assistant.
This allows other agents to communicate with ZORA using the Agent-to-Agent protocol.
"""

import logging
from typing import Optional

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
from starlette.applications import Starlette
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
import time

from .a2a_agent_executor import ZoraAgentExecutor
from .assistant.agent import create_agent  # type: ignore
from .assistant.utils.zep_memory_service import ZepMemoryService
from .config import APP_NAME, A2A_SERVER_DEFAULT_USER, NGROK_URL, ACTIVATE_A2A_SERVER
from typing import Optional

logger = logging.getLogger(__name__)
# Reduced logging level from DEBUG to INFO to reduce verbosity
logger.setLevel(logging.INFO)


def create_a2a_server(host: str = "localhost", port: int = 10003, user_id: Optional[str] = None) -> Optional[Starlette]:
    """
    Creates an A2A server for ZORA Assistant.
    
    Args:
        host: Host to bind the A2A server to
        port: Port to bind the A2A server to
        user_id: User ID for the A2A server agent context
        
    Returns:
        Starlette application instance ready to serve, or None if disabled
    """
    # Check if A2A server is enabled
    if not ACTIVATE_A2A_SERVER:
        logger.info("🚫 A2A server is disabled by configuration")
        return None
        
    # Use provided user_id or fall back to config default
    if user_id is None:
        user_id = A2A_SERVER_DEFAULT_USER
        
    logger.info(f"🚀 Creating A2A server for ZORA on {host}:{port} with user_id: {user_id}")
    
    try:
        # Define agent capabilities - disable streaming for now to ensure completion
        capabilities = AgentCapabilities(streaming=False)
        
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
        
        # Create agent card - following the sample patterns
        agent_card = AgentCard(
            name="ZORA Assistant",
            description="ZORA is a comprehensive AI assistant with voice interaction, persistent memory, and real-world integrations including web search, document processing, task management, calendar, and email.",
            url=NGROK_URL if NGROK_URL is not None else "",
            version="1.0.0",
            default_input_modes=["text/plain"],
            default_output_modes=["text/plain"],
            capabilities=capabilities,
            skills=skills,
        )

        # Create ADK agent with configured user for A2A requests
        adk_agent = create_agent(user_id=user_id, model_id="gemini-2.0-flash")  # type: ignore
        
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
            agent=adk_agent,  # type: ignore
            artifact_service=InMemoryArtifactService(),
            session_service=InMemorySessionService(),
            memory_service=memory_service,
        )
        
        # Create agent executor
        agent_executor = ZoraAgentExecutor(runner)
        logger.info("✅ Created ZoraAgentExecutor")

        # Create task store - following the sample patterns
        task_store = InMemoryTaskStore()
        logger.info("✅ Created InMemoryTaskStore")

        # Create request handler - following sample patterns (no queue_manager needed)
        logger.info("🎯 Creating DefaultRequestHandler with detailed logging")
        logger.info(f"   - agent_executor type: {type(agent_executor)}")
        logger.info(f"   - task_store type: {type(task_store)}")
        
        # Use DefaultRequestHandler directly (no extra logging)
        request_handler = DefaultRequestHandler(
            agent_executor=agent_executor,
            task_store=task_store,
        )
        logger.info("✅ Created DefaultRequestHandler")
        
        # Test if the request handler is properly configured
        logger.info(f"   - handler.agent_executor: {hasattr(request_handler, 'agent_executor')}")
        logger.info(f"   - handler.task_store: {hasattr(request_handler, 'task_store')}")

        # Create A2A application - following sample patterns
        logger.info("🎯 Creating A2AStarletteApplication")
        server = A2AStarletteApplication(
            agent_card=agent_card,
            http_handler=request_handler,
        )
        
        # Add detailed request logging middleware
        class DetailedLoggingMiddleware(BaseHTTPMiddleware):
            async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
                start_time = time.time()
                logger.info(f"📥 Incoming {request.method} request to {request.url.path}")
                logger.info(f"   - URL: {request.url}")
                logger.info(f"   - Headers: {dict(request.headers)}")
                # Log JSON body for POST requests
                if request.method == "POST":
                    try:
                        body = await request.json()
                        logger.info(f"   - Body JSON: {body}")
                    except Exception:
                        logger.info("   - Body JSON: <could not parse>")
                # Proceed to next handler
                response = await call_next(request)
                process_time = time.time() - start_time
                logger.info(f"📤 Completed {request.method} {request.url.path} - Status: {response.status_code} - Time: {process_time:.3f}s")
                return response

        starlette_app = server.build()
        starlette_app.add_middleware(DetailedLoggingMiddleware)
        
        logger.info("✅ A2AStarletteApplication created successfully with logging middleware")
        
        logger.info(f"✅ A2A server created successfully for ZORA on {host}:{port}")
        return starlette_app
        
    except Exception as e:
        logger.error(f"💥 Failed to create A2A server: {e}")
        raise
