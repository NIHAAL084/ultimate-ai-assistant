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
