import asyncio
import base64
import json
import logging
import os
import warnings
import uuid
import shutil
from pathlib import Path
from typing import AsyncIterable

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


async def start_agent_session(session_id, user_id=None, is_audio=False):
    """Starts an agent session"""

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

    # Set response modality using enum string values
    modality = types.Modality.AUDIO if is_audio else types.Modality.TEXT

    # Create speech config with voice settings
    speech_config = types.SpeechConfig(
        voice_config=types.VoiceConfig(
            # Puck, Charon, Kore, Fenrir, Aoede, Leda, Orus, and Zephyr
            prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=DEFAULT_VOICE)
        )
    )

    # Create run config with basic settings
    config = {"response_modalities": [modality], "speech_config": speech_config}

    # Add output_audio_transcription when audio is enabled to get both audio and text
    if is_audio:
        config["output_audio_transcription"] = {}

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
    websocket: WebSocket, live_events: AsyncIterable[Event | None]
):
    """Agent to client communication"""
    while True:
        async for event in live_events:
            if event is None:
                continue

            # If the turn complete or interrupted, send it
            if event.turn_complete or event.interrupted:
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

            # Only send text if it's a partial response (streaming)
            # Skip the final complete message to avoid duplication
            if part.text and event.partial:
                message = {
                    "mime_type": "text/plain",
                    "data": part.text,
                    "role": "model",
                }
                await websocket.send_text(json.dumps(message))
                print(f"[AGENT TO CLIENT]: text/plain: {part.text}")

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
    # Keep track of current mode
    is_audio_mode = False
    
    while True:
        message_json = await websocket.receive_text()
        message = json.loads(message_json)
        mime_type = message["mime_type"]
        data = message.get("data", "")
        role = message.get("role", "user")

        # Handle mode change messages
        if mime_type == "application/mode-change":
            new_mode = message.get("mode", "text")
            is_audio_mode = (new_mode == "audio")
            
            # Acknowledge the mode change
            response = {
                "mime_type": "application/mode-change-ack",
                "mode": new_mode,
                "success": True
            }
            await websocket.send_text(json.dumps(response))
            print(f"[MODE CHANGE] Changed to {new_mode} mode")
            continue

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

            # Send the audio data - note that ActivityStart/End and transcription
            # handling is done automatically by the ADK when input_audio_transcription
            # is enabled in the config
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
        
        return {
            "success": True,
            "message": f"User {user_id} registered successfully"
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
    is_audio: str = Query(...),
    user_id: str = Query(None),
):
    """Client websocket endpoint"""

    # Wait for client connection
    await websocket.accept()
    print(f"Client #{session_id} connected, audio mode: {is_audio}, user: {user_id or 'default'}")

    # Start agent session with user_id
    live_events, live_request_queue, session = await start_agent_session(
        session_id, user_id, is_audio == "true"
    )

    # Start tasks
    agent_to_client_task = asyncio.create_task(
        agent_to_client_messaging(websocket, live_events)
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
