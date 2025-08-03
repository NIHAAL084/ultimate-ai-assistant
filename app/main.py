import asyncio
import base64
import json
import logging
import os
import warnings
import uuid
import shutil
from pathlib import Path
from typing import AsyncIterable, Dict

from dotenv import load_dotenv

# Suppress various warnings
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")
warnings.filterwarnings("ignore", message=".*BaseAuthenticatedTool.*experimental.*")
warnings.filterwarnings("ignore", message=".*auth_config.*auth_scheme.*missing.*")

# Configure logging to reduce MCP tool verbosity
logging.getLogger("google.adk.tools.mcp_tool").setLevel(logging.ERROR)
# Suppress MCP-related asyncio errors during shutdown
logging.getLogger("mcp").setLevel(logging.WARNING)
logging.getLogger("mcp.client").setLevel(logging.WARNING)
logging.getLogger("mcp.client.stdio").setLevel(logging.WARNING)

# Set up logger for this module
logger = logging.getLogger(__name__)
# logging.getLogger("google.adk").setLevel(logging.WARNING)

from fastapi import FastAPI, Query, WebSocket, UploadFile, File, HTTPException, Request, Form
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.websockets import WebSocketDisconnect
from pydantic import BaseModel
from typing import Optional
from google.adk.agents import LiveRequestQueue
from google.adk.agents.run_config import RunConfig
from google.adk.events.event import Event
from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.adk.artifacts import InMemoryArtifactService
from google.genai import types
from .assistant.agent import create_agent
from .assistant.utils.zep_memory_service import ZepMemoryService
from .assistant.utils.session_memory_manager import SessionMemoryManager
from .config import APP_NAME, DEFAULT_VOICE, USER_DATA_LOCATION
from .database import get_database
from .credentials import DatabaseCredentialsManager, ensure_user_data_directories

# Pydantic models
class UserLoginRequest(BaseModel):
    user_id: str
    password: str

class UserRegistrationRequest(BaseModel):
    user_id: str
    password: str
    password_confirm: str
    location: str  # Required field
    todoist_api_token: Optional[str] = None
    oauth_credentials_filename: Optional[str] = None  # filename of the uploaded credentials file

class UserUpdateRequest(BaseModel):
    user_id: str
    current_password: str
    new_password: Optional[str] = None
    password_confirm: Optional[str] = None
    location: Optional[str] = None
    todoist_api_token: Optional[str] = None
    oauth_credentials_filename: Optional[str] = None

#
# ADK Streaming
#

# Load environment variables from .env file
load_dotenv()

# Session and artifact services
# Note: Using random session IDs - ZepMemoryService handles persistence across sessions
session_service = InMemorySessionService()
artifact_service = InMemoryArtifactService()

# Initialize Zep Memory Service
try:
    memory_service = ZepMemoryService()
    session_memory_manager = SessionMemoryManager(memory_service)
    print("✅ ZepMemoryService and SessionMemoryManager initialized successfully")
except Exception as e:
    print(f"⚠️ Failed to initialize ZepMemoryService: {e}")
    memory_service = None
    session_memory_manager = SessionMemoryManager(None)

# Create upload directory
UPLOAD_DIR = Path(__file__).parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# Ensure user data directories exist
ensure_user_data_directories()

# Coordination event for function call completion
function_call_completed = asyncio.Event()


async def start_agent_session(session_id, user_id=None):
    """
    Starts an agent session
    
    Always uses AUDIO modality to provide both audio output and text transcription.
    Client-side handles whether to play audio or just display text.
    """

    # Require user_id for authentication
    if not user_id:
        raise ValueError("user_id is required for authentication")
    
    # Normalize user_id to lowercase for consistency
    effective_user_id = user_id.lower().strip()

    try:
        # Create user-specific agent
        user_agent = create_agent(user_id=effective_user_id, model_id="gemini-live-2.5-flash-preview")

        # Create a Session
        session = await session_service.create_session(
            app_name=APP_NAME,
            user_id=effective_user_id,
            session_id=session_id,
        )

        # Create a Runner
        runner = Runner(
            app_name=APP_NAME,
            agent=user_agent,
            session_service=session_service,
            artifact_service=artifact_service,
            memory_service=memory_service,  # Add Zep memory service
        )

        # Always use AUDIO modality, and include both output and input transcription
        modality = types.Modality.AUDIO
        speech_config = types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=DEFAULT_VOICE)
            ),
            language_code="en-IN",  # Default language for audio output
        )
        config = {
            "response_modalities": [modality],
            "speech_config": speech_config,
            "output_audio_transcription": {},  # Always get both audio and text
            "input_audio_transcription": {},   # Show transcript of audio input
        }
        run_config = RunConfig(**config)

        # Create a LiveRequestQueue for this session
        live_request_queue = LiveRequestQueue()

        # Start agent session
        live_events = runner.run_live(
            session=session,
            live_request_queue=live_request_queue,
            run_config=run_config,
        )
        
        print(f"✅ Agent session started successfully for user {effective_user_id}, session {session_id}")
        return live_events, live_request_queue, session
        
    except Exception as e:
        print(f"❌ Failed to start agent session for user {effective_user_id}, session {session_id}: {e}")
        raise ValueError(f"Could not start session: {e}")


async def agent_to_client_messaging(
    websocket: WebSocket, live_events: AsyncIterable[Event | None], session
):
    """Agent to client communication"""
    
    try:
        # Buffer for accumulating audio input transcription parts and full text
        pending_user_parts: list[str] = []
        pending_user_text = ""
        while True:
            async for event in live_events:
                if event is None:
                    continue

                # If the turn complete or interrupted, flush any buffered user text and send completion
                if event.turn_complete or event.interrupted:
                    # Flush buffered user transcription if still pending
                    if pending_user_text:
                        user_msg = {
                            "mime_type": "text/plain",
                            "data": pending_user_text,
                            "role": "user",
                            "is_audio_input": True
                        }
                        await websocket.send_text(json.dumps(user_msg))
                        print(f"[AGENT TO CLIENT]: buffered audio transcription on turn_complete: {pending_user_text}")
                        pending_user_text = ""
                    message = {
                        "turn_complete": event.turn_complete,
                        "interrupted": event.interrupted,
                    }
                    await websocket.send_text(json.dumps(message))
                    print(f"[AGENT TO CLIENT]: {message}")
                    continue

                # Read the Content and its first Part
                part = event.content and event.content.parts and event.content.parts[0]
                if not part:
                    continue

                # Make sure we have a valid Part
                if not isinstance(part, types.Part):
                    continue

                # Buffer any input audio transcription parts until sending as one message
                if event.content and getattr(event.content, 'role', None) == "user" and part.text:
                    # Collect each chunk for later removal from session
                    pending_user_parts.append(part.text)
                    pending_user_text += part.text
                    # Do not send fragmented transcripts to client
                    continue

                # Only send text if it's a partial model response (streaming)
                if event.content and getattr(event.content, 'role', None) != "user" and part.text and event.partial:
                    # If we have buffered user transcription, send it once before model response
                    if pending_user_text:
                        # Remove partial transcription events from session
                        session.events[:] = [e for e in session.events if not (
                            e.author == "user" and e.content.parts and e.content.parts[0].text in pending_user_parts
                        )]
                        # Append single consolidated user event for memory
                        full_content = types.Content(role="user", parts=[types.Part(text=pending_user_text)])
                        session.events.append(Event(author="user", content=full_content))
                        # Send consolidated transcription to client
                        user_msg = {
                            "mime_type": "text/plain",
                            "data": pending_user_text,
                            "role": "user",
                            "is_audio_input": True
                        }
                        await websocket.send_text(json.dumps(user_msg))
                        print(f"[AGENT TO CLIENT]: buffered audio transcription: {pending_user_text}")
                        # Reset buffers
                        pending_user_text = ""
                        pending_user_parts.clear()
                    # Send model partial response
                    message = {
                        "mime_type": "text/plain",
                        "data": part.text,
                        "role": "model",
                    }
                    await websocket.send_text(json.dumps(message))
                    print(f"[AGENT TO CLIENT]: text/plain (partial model): {part.text}")

                # If it's audio, send Base64 encoded audio data
                is_audio = (
                    part.inline_data
                    and part.inline_data.mime_type
                    and part.inline_data.mime_type.startswith("audio/pcm")
                )
                if is_audio:
                    audio_data = part.inline_data and part.inline_data.data
                    if audio_data:
                        message = {
                            "mime_type": "audio/pcm",
                            "data": base64.b64encode(audio_data).decode("ascii"),
                            "role": "model",
                        }
                        await websocket.send_text(json.dumps(message))
                        print(f"[AGENT TO CLIENT]: audio/pcm: {len(audio_data)} bytes.")
                        
    except Exception as e:
        # Handle WebSocket disconnect and other connection errors
        if isinstance(e, WebSocketDisconnect):
            print(f"Client disconnected from WebSocket during agent-to-client messaging: {e}")
        else:
            print(f"Error in agent-to-client messaging: {e}")
        return


async def client_to_agent_messaging(
    websocket: WebSocket, live_request_queue: LiveRequestQueue, session
):
    """Client to agent communication"""
    try:
        while True:
            try:
                message_json = await websocket.receive_text()
                message = json.loads(message_json)
                mime_type = message["mime_type"]
                data = message.get("data", "")
                role = message.get("role", "user")

                # Handle messages - no mode switching needed since we always use AUDIO modality
                if mime_type == "text/plain":
                    # Send just the user text - agent will automatically check for uploaded files
                    part = types.Part(text=data or "")
                    content = types.Content(role=role, parts=[part])
                    live_request_queue.send_content(content=content)
                    print(f"[CLIENT TO AGENT] Sent text: {data}")
                    # Add user event to session for memory storage
                    user_event = Event(
                        author="user",
                        content=content
                    )
                    session.events.append(user_event)
                    print(f"📝 Added user event to session: {data}")
                elif mime_type == "audio/pcm":
                    # Send audio data
                    decoded_data = base64.b64decode(data)
                    # Send the audio data - ADK will handle transcription if input_audio_transcription is enabled
                    live_request_queue.send_realtime(
                        types.Blob(data=decoded_data, mime_type=mime_type)
                    )
                    print(f"[CLIENT TO AGENT]: audio/pcm: {len(decoded_data)} bytes")
                else:
                    raise ValueError(f"Mime type not supported: {mime_type}")
            except json.JSONDecodeError as e:
                print(f"Invalid JSON received from client: {e}")
                continue
            except Exception as e:
                print(f"Error processing message from client: {e}")
                continue
                
    except Exception as e:
        # Handle WebSocket disconnect and other connection errors
        if isinstance(e, WebSocketDisconnect):
            print(f"Client disconnected from WebSocket: {e}")
        else:
            print(f"Error in client-to-agent messaging: {e}")
        return


#
# FastAPI web app
#

app = FastAPI()

STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
async def root():
    """Serves the index.html"""
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


@app.get("/config")
async def get_config():
    """Get client configuration"""
    return {
        "app_name": APP_NAME
    }


@app.post("/login")
async def login_user(request: UserLoginRequest):
    """Authenticate user with password"""
    try:
        user_id = request.user_id.strip().lower()
        password = request.password
        
        # Validate inputs
        if not user_id or not password:
            return {
                "success": False,
                "message": "User ID and password are required"
            }
        
        db = get_database()
        
        # Authenticate user
        if db.authenticate_user(user_id, password):
            return {
                "success": True,
                "message": f"User {user_id} authenticated successfully",
                "user_id": user_id
            }
        else:
            return {
                "success": False,
                "message": "Invalid user ID or password"
            }
            
    except Exception as e:
        logger.error(f"Error during login: {e}")
        return {
            "success": False,
            "message": "Login failed. Please try again."
        }


@app.post("/register-user")
async def register_user(request: UserRegistrationRequest):
    """Register a new user with their credentials"""
    try:
        user_id = request.user_id.lower().strip()
        password = request.password
        password_confirm = request.password_confirm
        location = request.location
        todoist_api_token = request.todoist_api_token
        oauth_credentials_filename = request.oauth_credentials_filename
        
        # Validate inputs - require Todoist and OAuth for registration
        if not user_id or not password or not location:
            return {
                "success": False,
                "message": "User ID, password, and location are required"
            }
        
        if not todoist_api_token:
            return {
                "success": False,
                "message": "Todoist API Token is required for registration"
            }
        
        if not oauth_credentials_filename:
            return {
                "success": False,
                "message": "Google OAuth Credentials file is required for registration"
            }
        
        if password != password_confirm:
            return {
                "success": False,
                "message": "Passwords do not match"
            }
        
        if len(password) < 8:
            return {
                "success": False,
                "message": "Password must be at least 8 characters long"
            }
        
        db = get_database()
        
        # Check if user already exists
        if db.user_exists(user_id):
            return {
                "success": False,
                "message": "User ID already in use"
            }
        
        # Create credentials path if OAuth file provided
        credentials_path = None
        if oauth_credentials_filename:
            user_data_path = Path(USER_DATA_LOCATION)
            credentials_dir = user_data_path / "credentials"
            credentials_path = str(credentials_dir / oauth_credentials_filename)
        
        # Create user in database
        success = db.create_user(
            user_id=user_id,
            password=password,
            location=location,
            todoist_api_token=todoist_api_token,
            google_oauth_credentials_path=credentials_path
        )
        
        if not success:
            return {
                "success": False,
                "message": "Failed to create user account"
            }
        
        # Set up authentication for Google services
        credentials_manager = DatabaseCredentialsManager(user_id)
        auth_results = []
        
        # Set up Gmail authentication
        try:
            gmail_result = credentials_manager.setup_gmail_authentication()
            auth_results.append(f"Gmail: {gmail_result['message']}")
            if not gmail_result['success']:
                logger.warning(f"Gmail auth failed for {user_id}: {gmail_result['message']}")
        except Exception as e:
            logger.error(f"Gmail authentication error for {user_id}: {e}")
            auth_results.append(f"Gmail: Authentication failed - {str(e)}")
        
        # Set up Calendar authentication
        try:
            calendar_result = credentials_manager.setup_calendar_authentication()
            auth_results.append(f"Calendar: {calendar_result['message']}")
            if not calendar_result['success']:
                logger.warning(f"Calendar auth failed for {user_id}: {calendar_result['message']}")
        except Exception as e:
            logger.error(f"Calendar authentication error for {user_id}: {e}")
            auth_results.append(f"Calendar: Authentication failed - {str(e)}")
        
        return {
            "success": True,
            "message": f"User {user_id} registered successfully",
            "auth_details": auth_results
        }
        
    except Exception as e:
        logger.error(f"Error registering user: {e}")
        return {
            "success": False,
            "message": "Error registering user. Please try again."
        }


@app.post("/update-user")
async def update_user(request: UserUpdateRequest):
    """Update existing user credentials"""
    try:
        user_id = request.user_id.lower().strip()
        current_password = request.current_password
        new_password = request.new_password
        password_confirm = request.password_confirm
        location = request.location
        todoist_api_token = request.todoist_api_token
        oauth_credentials_filename = request.oauth_credentials_filename
        
        # Validate inputs
        if not user_id or not current_password:
            return {
                "success": False,
                "message": "User ID and current password are required"
            }
        
        db = get_database()
        
        # Authenticate user with current password
        if not db.authenticate_user(user_id, current_password):
            return {
                "success": False,
                "message": "Invalid current password"
            }
        
        # Validate new password if provided
        if new_password:
            if new_password != password_confirm:
                return {
                    "success": False,
                    "message": "New passwords do not match"
                }
            
            if len(new_password) < 8:
                return {
                    "success": False,
                    "message": "New password must be at least 8 characters long"
                }
        
        # Prepare credentials path if OAuth file provided
        credentials_path = None
        if oauth_credentials_filename:
            user_data_path = Path(USER_DATA_LOCATION)
            credentials_dir = user_data_path / "credentials"
            credentials_path = str(credentials_dir / oauth_credentials_filename)
        
        # Update user in database
        success = db.update_user(
            user_id=user_id,
            password=new_password,
            location=location,
            todoist_api_token=todoist_api_token,
            google_oauth_credentials_path=credentials_path if oauth_credentials_filename else None
        )
        
        if not success:
            return {
                "success": False,
                "message": "Failed to update user account"
            }
        
        # If OAuth credentials were updated, re-run authentication
        auth_results = []
        if oauth_credentials_filename:
            credentials_manager = DatabaseCredentialsManager(user_id)
            
            # Re-setup Gmail authentication
            try:
                gmail_result = credentials_manager.setup_gmail_authentication()
                auth_results.append(f"Gmail: {gmail_result['message']}")
                if not gmail_result['success']:
                    logger.warning(f"Gmail auth failed for {user_id}: {gmail_result['message']}")
            except Exception as e:
                logger.error(f"Gmail authentication error for {user_id}: {e}")
                auth_results.append(f"Gmail: Authentication failed - {str(e)}")
            
            # Re-setup Calendar authentication
            try:
                calendar_result = credentials_manager.setup_calendar_authentication()
                auth_results.append(f"Calendar: {calendar_result['message']}")
                if not calendar_result['success']:
                    logger.warning(f"Calendar auth failed for {user_id}: {calendar_result['message']}")
            except Exception as e:
                logger.error(f"Calendar authentication error for {user_id}: {e}")
                auth_results.append(f"Calendar: Authentication failed - {str(e)}")
        
        response_data = {
            "success": True,
            "message": f"User {user_id} updated successfully"
        }
        
        if auth_results:
            response_data["auth_details"] = auth_results
        
        return response_data
        
    except Exception as e:
        logger.error(f"Error updating user: {e}")
        return {
            "success": False,
            "message": "Error updating user. Please try again."
        }


@app.post("/setup-gmail-auth")
async def setup_gmail_auth(request: Dict[str, str]):
    """Set up Gmail authentication for an existing user"""
    try:
        user_id = request.get("user_id", "").lower().strip()
        
        if not user_id:
            return {
                "success": False,
                "message": "User ID is required"
            }
        
        # Check if user exists in database
        db = get_database()
        if not db.user_exists(user_id):
            return {
                "success": False,
                "message": "User not found"
            }
        
        # Set up Gmail authentication
        credentials_manager = DatabaseCredentialsManager(user_id)
        result = credentials_manager.setup_gmail_authentication()
        
        return result
        
    except Exception as e:
        logger.error(f"Error setting up Gmail authentication: {e}")
        return {
            "success": False,
            "message": "Error setting up Gmail authentication. Please try again."
        }


@app.post("/setup-calendar-auth")
async def setup_calendar_auth(request: Dict[str, str]):
    """Set up Calendar authentication for an existing user"""
    try:
        user_id = request.get("user_id", "").lower().strip()
        
        if not user_id:
            return {
                "success": False,
                "message": "User ID is required"
            }
        
        # Check if user exists in database
        db = get_database()
        if not db.user_exists(user_id):
            return {
                "success": False,
                "message": "User not found"
            }
        
        # Set up Calendar authentication
        credentials_manager = DatabaseCredentialsManager(user_id)
        result = credentials_manager.setup_calendar_authentication()
        
        return result
        
    except Exception as e:
        logger.error(f"Error setting up Calendar authentication: {e}")
        return {
            "success": False,
            "message": "Error setting up Calendar authentication. Please try again."
        }


@app.post("/check-credentials")
async def check_credentials(request: Dict[str, str]):
    """Check the status of user credentials"""
    try:
        user_id = request.get("user_id", "").lower().strip()
        
        if not user_id:
            return {
                "success": False,
                "message": "User ID is required"
            }
        
        # Check if user exists in database
        db = get_database()
        if not db.user_exists(user_id):
            return {
                "success": False,
                "message": "User not found"
            }
        
        # Check credentials setup
        credentials_manager = DatabaseCredentialsManager(user_id)
        status = credentials_manager.verify_credentials_setup()
        
        return {
            "success": True,
            "credentials_status": status,
            "message": "Credentials status retrieved successfully"
        }
        
    except Exception as e:
        logger.error(f"Error checking credentials: {e}")
        return {
            "success": False,
            "message": "Error checking credentials. Please try again."
        }


# Health check endpoint


@app.post("/upload-credentials")
async def upload_credentials(file: UploadFile = File(...), user_id: str = Form(...)):
    """Upload OAuth credentials file for user registration"""
    try:
        if not user_id:
            raise HTTPException(status_code=400, detail="User ID is required")
        
        user_id = user_id.lower().strip()
        
        # Validate file type (should be JSON)
        if not file.filename.endswith('.json'):
            raise HTTPException(status_code=400, detail="Only JSON files are allowed")
        
        # Create filename with user ID
        credentials_filename = f"credentials_{user_id}.json"
        credentials_path = Path(USER_DATA_LOCATION) / "credentials" / credentials_filename
        
        # Ensure credentials directory exists
        credentials_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save file
        with open(credentials_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Update database with file path if user exists
        db = get_database()
        if db.user_exists(user_id):
            success = db.update_user(
                user_id=user_id,
                google_oauth_credentials_path=str(credentials_path)
            )
            if not success:
                logger.warning(f"Failed to update credentials path for existing user {user_id}")
        
        return {
            "success": True,
            "filename": credentials_filename,
            "message": "Credentials file uploaded successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error uploading credentials: {e}")
        raise HTTPException(status_code=500, detail="Error uploading credentials file")


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload endpoint for files"""
    try:
        # Use original filename directly
        file_path = UPLOAD_DIR / file.filename
        
        # Save file to disk with original name
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Return file information
        return {
            "filename": file.filename,
            "original_name": file.filename,
            "content_type": file.content_type,
            "size": file_path.stat().st_size
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {str(e)}")


@app.websocket("/ws/{session_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    session_id: str,
    user_id: str = Query(None),
):
    """Client websocket endpoint"""

    # Validate user authentication before accepting connection
    if not user_id:
        await websocket.close(code=4001, reason="Authentication required")
        return
    
    # Normalize user_id
    user_id = user_id.lower().strip()
    
    # Verify user exists in database
    db = get_database()
    if not db.user_exists(user_id):
        await websocket.close(code=4002, reason="User not found")
        return
    
    # Wait for client connection
    await websocket.accept()
    print(f"Client #{session_id} connected, user: {user_id}")

    try:
        # Start agent session with user_id
        live_events, live_request_queue, session = await start_agent_session(
            session_id, user_id
        )

        # Start tasks
        agent_to_client_task = asyncio.create_task(
            agent_to_client_messaging(websocket, live_events, session)
        )
        client_to_agent_task = asyncio.create_task(
            client_to_agent_messaging(websocket, live_request_queue, session)
        )
        
        try:
            # Wait for either task to complete (or fail)
            done, pending = await asyncio.wait(
                [agent_to_client_task, client_to_agent_task],
                return_when=asyncio.FIRST_COMPLETED,
            )
            
            # Cancel remaining tasks
            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
                    
        except Exception as e:
            print(f"Error in WebSocket tasks for session {session_id}: {e}")
            # Cancel both tasks on error
            agent_to_client_task.cancel()
            client_to_agent_task.cancel()
            try:
                await agent_to_client_task
            except asyncio.CancelledError:
                pass
            try:
                await client_to_agent_task
            except asyncio.CancelledError:
                pass
            
    except Exception as e:
        print(f"Error setting up session {session_id} for user {user_id}: {e}")
        await websocket.close(code=4003, reason="Session setup failed")
        return
    finally:
        print(f"Client #{session_id} disconnected, user: {user_id}")
        
        # Save session to memory service if available
        if memory_service and session:
            try:
                # Use session_memory_manager to save with proper user context
                await session_memory_manager.auto_save_session(session)
                print(f"✅ Session {session_id} saved to Zep memory for user {user_id}")
            except Exception as e:
                # Log the error but don't crash - session conflicts are expected after server restart
                print(f"⚠️ Could not save session to Zep (this is normal after server restart): {e}")
        
        # Clean up WebSocket
        if not websocket.client_state.DISCONNECTED:
            try:
                await websocket.close()
            except Exception as e:
                print(f"Error closing WebSocket: {e}")
