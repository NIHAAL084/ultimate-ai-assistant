import asyncio
import logging
from collections.abc import AsyncGenerator

from a2a.server.agent_execution import AgentExecutor
from a2a.server.agent_execution.context import RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import (
    FilePart,
    FileWithBytes,
    FileWithUri,
    Part,
    TaskState,
    TextPart,
    UnsupportedOperationError,
)
from a2a.utils.errors import ServerError
from google.adk import Runner
from google.adk.events import Event
from google.genai import types

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class ZoraAgentExecutor(AgentExecutor):
    """An AgentExecutor that runs ZORA's ADK-based Assistant."""

    def __init__(self, runner: Runner):
        self.runner = runner
        self._running_sessions = {}
        logger.info("🚀 ZoraAgentExecutor initialized")

    def _run_agent(
        self, session_id, new_message: types.Content, user_id: str = "a2a_client"
    ) -> AsyncGenerator[Event, None]:
        return self.runner.run_async(
            session_id=session_id, user_id=user_id, new_message=new_message
        )

    async def _process_request(
        self,
        new_message: types.Content,
        session_id: str,
        task_updater: TaskUpdater,
        user_id: str = "a2a_client",
    ) -> None:
        try:
            session_obj = await self._upsert_session(session_id, user_id)
            session_id = session_obj.id
            logger.info(f"📍 Processing request for session: {session_id}")

            event_count = 0
            async for event in self._run_agent(session_id, new_message, user_id):
                event_count += 1
                logger.info(f"🔄 Processing ADK event #{event_count}: author={event.author}, has_content={event.content is not None}, final={event.is_final_response()}")
                
                # Log event content details
                if event.content:
                    logger.debug(f"Event content parts: {len(event.content.parts) if event.content.parts else 0}")
                    if event.content.parts:
                        for i, part in enumerate(event.content.parts):
                            if hasattr(part, 'text') and part.text:
                                logger.debug(f"Part {i}: text='{part.text[:100]}...'")
                            else:
                                logger.debug(f"Part {i}: type={type(part)}")
                
                if event.is_final_response():
                    parts = convert_genai_parts_to_a2a(
                        event.content.parts if event.content and event.content.parts else []
                    )
                    logger.info(f"✅ Final response with {len(parts)} parts")
                    if len(parts) == 0:
                        logger.warning("⚠️ Final response has no parts! Creating default response.")
                        # Create a default text response if no parts are returned
                        from a2a.types import TextPart, Part
                        default_part = Part(root=TextPart(text="I'm sorry, I couldn't generate a proper response. Please try again."))
                        parts = [default_part]
                    else:
                        for i, p in enumerate(parts):
                            if hasattr(p.root, 'text'):
                                logger.debug(f"Response part {i}: {p.root.text[:100]}...")
                            else:
                                logger.debug(f"Response part {i}: {type(p.root)}")
                    
                    task_updater.add_artifact(parts)
                    task_updater.complete()
                    break
                    
                if not event.get_function_calls():
                    logger.info("📤 Intermediate response update")
                    task_updater.update_status(
                        TaskState.working,
                        message=task_updater.new_agent_message(
                            convert_genai_parts_to_a2a(
                                event.content.parts
                                if event.content and event.content.parts
                                else []
                            ),
                        ),
                    )
                else:
                    logger.info(f"🔧 Function call event: {[call.name for call in event.get_function_calls()]}")
                    task_updater.update_status(
                        TaskState.working,
                        message=task_updater.new_agent_message(
                            convert_genai_parts_to_a2a(
                                event.content.parts
                                if event.content and event.content.parts
                                else []
                            ),
                        ),
                    )
                    
            if event_count == 0:
                logger.warning("⚠️ No events received from agent runner")
                task_updater.update_status(
                    TaskState.failed,
                    message="No response generated from agent"
                )
                
        except Exception as e:
            logger.error(f"💥 Error in _process_request: {str(e)}", exc_info=True)
            raise

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        logger.info("🚀 A2A Agent Executor: Starting execute method")
        logger.info(f"📋 Context: task_id={context.task_id}, context_id={context.context_id}")
        logger.info(f"📝 Message parts: {len(context.message.parts) if context.message else 0}")
        
        if not context.task_id or not context.context_id:
            logger.error("❌ Missing task_id or context_id")
            raise ValueError("RequestContext must have task_id and context_id")
        if not context.message:
            logger.error("❌ Missing message in context")
            raise ValueError("RequestContext must have a message")

        logger.info("📤 Creating TaskUpdater and submitting task")
        updater = TaskUpdater(event_queue, context.task_id, context.context_id)
        
        try:
            
            updater.submit()
            if not context.current_task:
                logger.info("📤 Submitting new task to store")
                updater.submit()
            logger.info("📤 Starting work")
            updater.start_work()
            
            # Use a default user_id for A2A requests, or extract from context if available
            user_id = getattr(context, 'user_id', 'a2a_client')
            logger.info(f"👤 Using user_id: {user_id}")
            
            logger.info("🔄 Converting A2A parts to GenAI format")
            genai_parts = convert_a2a_parts_to_genai(context.message.parts)
            logger.info(f"🔄 Converted {len(genai_parts)} parts")
            
            logger.info("🎯 Starting _process_request")
            await self._process_request(
                types.UserContent(parts=genai_parts),
                context.context_id,
                updater,
                user_id,
            )
            
            logger.info("🎯 Completed A2A request processing successfully")
            
        except Exception as e:
            logger.error(f"💥 Error during A2A request processing: {str(e)}", exc_info=True)
            # Ensure we send an error response to the client
            updater.update_status(
                TaskState.failed,
                message=f"Error processing request: {str(e)}"
            )
            raise

    async def cancel(self, context: RequestContext, event_queue: EventQueue):
        raise ServerError(error=UnsupportedOperationError())

    async def _upsert_session(self, session_id: str, user_id: str = "a2a_client"):
        session = await self.runner.session_service.get_session(
            app_name=self.runner.app_name, user_id=user_id, session_id=session_id
        )
        if session is None:
            session = await self.runner.session_service.create_session(
                app_name=self.runner.app_name,
                user_id=user_id,
                session_id=session_id,
            )
        if session is None:
            raise RuntimeError(f"Failed to get or create session: {session_id}")
        return session


def convert_a2a_parts_to_genai(parts: list[Part]) -> list[types.Part]:
    """Convert a list of A2A Part types into a list of Google Gen AI Part types."""
    return [convert_a2a_part_to_genai(part) for part in parts]


def convert_a2a_part_to_genai(part: Part) -> types.Part:
    """Convert a single A2A Part type into a Google Gen AI Part type."""
    root = part.root
    if isinstance(root, TextPart):
        return types.Part(text=root.text)
    if isinstance(root, FilePart):
        if isinstance(root.file, FileWithUri):
            return types.Part(
                file_data=types.FileData(
                    file_uri=root.file.uri, mime_type=root.file.mimeType
                )
            )
        if isinstance(root.file, FileWithBytes):
            return types.Part(
                inline_data=types.Blob(
                    data=root.file.bytes.encode("utf-8"),
                    mime_type=root.file.mimeType or "application/octet-stream",
                )
            )
        raise ValueError(f"Unsupported file type: {type(root.file)}")
    raise ValueError(f"Unsupported part type: {type(part)}")


def convert_genai_parts_to_a2a(parts: list[types.Part]) -> list[Part]:
    """Convert a list of Google Gen AI Part types into a list of A2A Part types."""
    return [
        convert_genai_part_to_a2a(part)
        for part in parts
        if (part.text or part.file_data or part.inline_data)
    ]


def convert_genai_part_to_a2a(part: types.Part) -> Part:
    """Convert a single Google Gen AI Part type into an A2A Part type."""
    if part.text:
        return Part(root=TextPart(text=part.text))
    if part.file_data:
        if not part.file_data.file_uri:
            raise ValueError("File URI is missing")
        return Part(
            root=FilePart(
                file=FileWithUri(
                    uri=part.file_data.file_uri,
                    mimeType=part.file_data.mime_type,
                )
            )
        )
    if part.inline_data:
        if not part.inline_data.data:
            raise ValueError("Inline data is missing")
        return Part(
            root=FilePart(
                file=FileWithBytes(
                    bytes=part.inline_data.data.decode("utf-8"),
                    mimeType=part.inline_data.mime_type,
                )
            )
        )
    raise ValueError(f"Unsupported part type: {part}")
