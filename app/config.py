"""
Configuration settings for the Ultimate AI Assistant
"""

import os
from pathlib import Path
from dotenv import load_dotenv  # type: ignore
from typing import List, Optional

# Load environment variables from .env file
load_dotenv()

# Application Configuration
APP_NAME = "ZORA"

# User Data Configuration
# Location where user-specific data (credentials, tokens, etc.) is stored
USER_DATA_LOCATION = str(Path(__file__).parent.parent / "user_data")

# Server Configuration
DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 8001

# A2A Server Configuration
ACTIVATE_A2A_SERVER = True
A2A_HOST = "0.0.0.0"  # Bind to all interfaces for ngrok
A2A_PORT = 80  # Use port 80 for ngrok
A2A_SERVER_DEFAULT_USER = "test"

# Ngrok Configuration
USE_NGROK_FOR_A2A = True  # Set to True to automatically start ngrok for A2A server
NGROK_URL = os.getenv("NGROK_URL")
NGROK_AUTHTOKEN = os.getenv("NGROK_AUTHTOKEN")

# Audio Configuration
DEFAULT_VOICE = "Aoede"  # Laomedeia, Kore, Aoede, Leda, and Zephyr

# A2A Agent Configuration
# A2A Agent URLs for discovery and connection

A2A_AGENT_URLS: List[Optional[str]] = [
    NGROK_URL,  # Our own A2A server accessible via ngrok
    "http://localhost:10002",  # Example: Test agent or Karley's scheduling agent
    "http://localhost:10004",  # Example: Another local agent
    "http://localhost:10005",  # Example: Research or utility agent
]

# A2A Discovery and Connection Settings
A2A_DISCOVERY_ENABLED = True
A2A_CONNECTION_TIMEOUT = 30  # seconds
A2A_RETRY_ATTEMPTS = 3
