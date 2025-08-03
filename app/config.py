"""
Configuration settings for the Ultimate AI Assistant
"""

# Application Configuration
APP_NAME = "ZORA"

# Server Configuration
DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 8001

# A2A Server Configuration
ACTIVATE_A2A_SERVER = True
A2A_HOST = "0.0.0.0"  # Bind to all interfaces for ngrok
A2A_PORT = 80  # Use port 80 for ngrok
A2A_SERVER_DEFAULT_USER = "test"

# Ngrok Configuration
NGROK_URL = "https://gecko-pleased-grossly.ngrok-free.app"
NGROK_AUTHTOKEN = "30gwU7ijCwD6QHk62eCoqhqmFLc_6QPkfkzVkvxGyq9tK6kcx"

# Audio Configuration
DEFAULT_VOICE = "Aoede"  # Laomedeia, Kore, Aoede, Leda, and Zephyr

# A2A Agent Configuration
# A2A Agent URLs for discovery and connection
A2A_AGENT_URLS = [
    NGROK_URL,  # Our own A2A server accessible via ngrok
    "http://localhost:10002",  # Example: Test agent or Karley's scheduling agent
    "http://localhost:10004",  # Example: Another local agent
    "http://localhost:10005",  # Example: Research or utility agent
]

# A2A Discovery and Connection Settings
A2A_DISCOVERY_ENABLED = True
A2A_CONNECTION_TIMEOUT = 30  # seconds
A2A_RETRY_ATTEMPTS = 3
