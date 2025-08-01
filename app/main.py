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
logging.getLogger("google.adk").setLevel(logging.WARNING)

from fastapi import FastAPI, Query, WebSocket, UploadFile, File, HTTPException, Request, Form
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
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
from .config import APP_NAME, DEFAULT_VOICE
from .user_env import UserEnvironmentManager

# Pydantic models
class UserValidationRequest(BaseModel):
    user_id: str

class UserRegistrationRequest(BaseModel):
    user_id: str
    todoist_api_token: str
    oauth_credentials_filename: str  # filename of the uploaded credentials file

class UserUpdateRequest(BaseModel):
    user_id: str
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

    # Create user-specific agent
    user_agent = create_agent(user_id=effective_user_id)

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
    return live_events, live_request_queue, session


async def agent_to_client_messaging(
    websocket: WebSocket, live_events: AsyncIterable[Event | None], session
):
    """Agent to client communication"""
    
    # Buffer for accumulating audio input transcription
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
                pending_user_text += part.text
                # Do not send fragmented transcripts
                continue

            # Only send text if it's a partial model response (streaming)
            if event.content and getattr(event.content, 'role', None) != "user" and part.text and event.partial:
                # If we have buffered user transcription, send it once before model response
                if pending_user_text:
                    user_msg = {
                        "mime_type": "text/plain",
                        "data": pending_user_text,
                        "role": "user",
                        "is_audio_input": True
                    }
                    await websocket.send_text(json.dumps(user_msg))
                    print(f"[AGENT TO CLIENT]: buffered audio transcription: {pending_user_text}")
                    pending_user_text = ""
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


async def client_to_agent_messaging(
    websocket: WebSocket, live_request_queue: LiveRequestQueue, session
):
    """Client to agent communication"""
    while True:
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


@app.post("/validate-user")
async def validate_user(request: UserValidationRequest):
    """Validate if a user ID has a corresponding environment file"""
    try:
        user_id = request.user_id.strip().lower()
        
        # Try to create a UserEnvironmentManager instance for this user
        try:
            user_env = UserEnvironmentManager(user_id)
            # Check if the user-specific environment file exists
            if user_env.user_env_file.exists():
                return {
                    "valid": True,
                    "message": f"User {user_id} validated successfully"
                }
            else:
                return {
                    "valid": False,
                    "message": "Unregistered user. Please contact administrator."
                }
        except Exception as e:
            print(f"Error validating user {user_id}: {e}")
            return {
                "valid": False,
                "message": "Error validating user. Please try again."
            }
            
    except Exception as e:
        print(f"User validation error: {e}")
        raise HTTPException(status_code=400, detail="Invalid request")


@app.post("/register-user")
async def register_user(request: UserRegistrationRequest):
    """Register a new user with their credentials"""
    try:
        user_id = request.user_id.lower().strip()
        
        # Check if user already exists
        if UserEnvironmentManager.check_user_exists(user_id):
            return {
                "success": False,
                "message": "User ID already in use"
            }
        
        # Validate inputs
        if not request.todoist_api_token or not request.oauth_credentials_filename:
            return {
                "success": False,
                "message": "All fields are required for registration"
            }
        
        # Create credentials path
        credentials_path = f"user_data/credentials/{request.oauth_credentials_filename}"
        
        # Create user environment manager and environment file
        user_env = UserEnvironmentManager(user_id)
        user_env.create_user_env_file(request.todoist_api_token, credentials_path)
        
        # Create a fresh UserEnvironmentManager instance to ensure environment is loaded
        user_env_fresh = UserEnvironmentManager(user_id)
        
        # Set up Gmail authentication automatically
        print(f"Setting up Gmail authentication for user {user_id}...")
        
        # Debug: Check environment variables
        print(f"Debug: Checking OAuth credentials for user {user_id}")
        oauth_creds = user_env_fresh.get_env_var("GOOGLE_OAUTH_CREDENTIALS")
        print(f"Debug: OAuth credentials found: {oauth_creds}")
        
        gmail_result = user_env_fresh.setup_gmail_authentication()
        print(f"Debug: Gmail result: {gmail_result}")
        
        # Set up Calendar authentication automatically
        print(f"Setting up Calendar authentication for user {user_id}...")
        calendar_result = user_env_fresh.setup_calendar_authentication()
        print(f"Debug: Calendar result: {calendar_result}")
        
        # Determine overall success
        gmail_success = gmail_result["success"]
        calendar_success = calendar_result["success"]
        
        if gmail_success and calendar_success:
            print(f"Gmail and Calendar authentication setup successful for user {user_id}")
            return {
                "success": True,
                "message": f"User {user_id} registered successfully with Gmail and Calendar authentication configured",
                "gmail_setup": True,
                "calendar_setup": True
            }
        elif gmail_success:
            print(f"Gmail authentication setup successful but Calendar setup failed for user {user_id}: {calendar_result['message']}")
            return {
                "success": True,
                "message": f"User {user_id} registered successfully with Gmail authentication configured. Calendar setup failed: {calendar_result['message']}",
                "gmail_setup": True,
                "calendar_setup": False,
                "calendar_error": calendar_result["message"]
            }
        elif calendar_success:
            print(f"Calendar authentication setup successful but Gmail setup failed for user {user_id}: {gmail_result['message']}")
            return {
                "success": True,
                "message": f"User {user_id} registered successfully with Calendar authentication configured. Gmail setup failed: {gmail_result['message']}",
                "gmail_setup": False,
                "calendar_setup": True,
                "gmail_error": gmail_result["message"]
            }
        else:
            print(f"Both Gmail and Calendar authentication setup failed for user {user_id}")
            return {
                "success": True,
                "message": f"User {user_id} registered successfully, but both Gmail and Calendar authentication setup failed",
                "gmail_setup": False,
                "calendar_setup": False,
                "gmail_error": gmail_result["message"],
                "calendar_error": calendar_result["message"]
            }
        
    except Exception as e:
        print(f"Error registering user: {e}")
        return {
            "success": False,
            "message": "Error registering user. Please try again."
        }


@app.post("/update-user")
async def update_user(request: UserUpdateRequest):
    """Update existing user credentials"""
    try:
        user_id = request.user_id.lower().strip()
        
        # Check if user exists
        if not UserEnvironmentManager.check_user_exists(user_id):
            return {
                "success": False,
                "message": "User not found"
            }
        
        # Validate that at least one field is provided for update
        if not request.todoist_api_token and not request.oauth_credentials_filename:
            return {
                "success": False,
                "message": "At least one field must be provided for update"
            }
        
        # Create credentials path if provided
        credentials_path = None
        if request.oauth_credentials_filename:
            credentials_path = f"user_data/credentials/{request.oauth_credentials_filename}"
        
        # Update user environment
        user_env = UserEnvironmentManager(user_id)
        user_env.update_user_env_file(request.todoist_api_token, credentials_path)
        
        return {
            "success": True,
            "message": f"User {user_id} updated successfully"
        }
        
    except Exception as e:
        print(f"Error updating user: {e}")
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
        
        # Check if user exists
        if not UserEnvironmentManager.check_user_exists(user_id):
            return {
                "success": False,
                "message": "User not found"
            }
        
        user_env = UserEnvironmentManager(user_id)
        
        # Set up Gmail authentication
        print(f"Setting up Gmail authentication for user {user_id}...")
        gmail_result = user_env.setup_gmail_authentication()
        
        return {
            "success": gmail_result["success"],
            "message": gmail_result["message"]
        }
        
    except Exception as e:
        print(f"Error setting up Gmail authentication: {e}")
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
        
        # Check if user exists
        if not UserEnvironmentManager.check_user_exists(user_id):
            return {
                "success": False,
                "message": "User not found"
            }
        
        user_env = UserEnvironmentManager(user_id)
        
        # Set up Calendar authentication
        print(f"Setting up Calendar authentication for user {user_id}...")
        calendar_result = user_env.setup_calendar_authentication()
        
        return {
            "success": calendar_result["success"],
            "message": calendar_result["message"]
        }
        
    except Exception as e:
        print(f"Error setting up Calendar authentication: {e}")
        return {
            "success": False,
            "message": "Error setting up Calendar authentication. Please try again."
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
        credentials_path = Path(__file__).parent.parent / "user_data" / "credentials" / credentials_filename
        
        # Ensure credentials directory exists
        credentials_path.parent.mkdir(exist_ok=True)
        
        # Save file
        with open(credentials_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        return {
            "success": True,
            "filename": credentials_filename,
            "message": "Credentials file uploaded successfully"
        }
        
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

    # Wait for client connection
    await websocket.accept()
    print(f"Client #{session_id} connected, user: {user_id or 'default'}")

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
        await asyncio.gather(agent_to_client_task, client_to_agent_task)
    except Exception as e:
        # Handle WebSocket disconnections gracefully
        print(f"WebSocket connection ended for client #{session_id}: {e}")
    finally:
        # Always try to save session on disconnect, regardless of how the connection ended
        print(f"Client #{session_id} disconnected")
        
        # Automatically save session to Zep memory on disconnect
        try:
            if session and session_memory_manager:
                await session_memory_manager.auto_save_session(session)
                print(f"💾 Session {session_id} processing complete for memory storage")
            else:
                print(f"⚠️ Session {session_id} not available or no memory manager available")
        except Exception as e:
            print(f"⚠️ Failed to save session {session_id} to memory on disconnect: {e}")
