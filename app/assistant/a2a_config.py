"""
A2A Configuration for ZORA Assistant.
Manages configuration for Agent-to-Agent communication.
"""

import os
from typing import List

# Import ngrok URL from main config
from ..config import NGROK_URL


def get_a2a_agent_urls() -> List[str]:
    """
    Get list of A2A agent URLs to discover and connect to.
    Can be configured via environment variables.
    
    Returns:
        List of agent URLs to connect to
    """
    # Check for environment variable with comma-separated URLs
    env_urls = os.getenv("A2A_AGENT_URLS", "")
    if env_urls:
        return [url.strip() for url in env_urls.split(",") if url.strip()]
    
    # Default URLs - includes our own ngrok endpoint and example agents
    default_urls = [
        NGROK_URL,  # Our own A2A server accessible via ngrok (https://gecko-pleased-grossly.ngrok-free.app)
        "http://localhost:10002",  # Example: Test agent or Karley's scheduling agent
        "http://localhost:10004",  # Example: Another local agent
        "http://localhost:10005",  # Example: Research or utility agent
    ]
    
    return default_urls


def get_a2a_discovery_enabled() -> bool:
    """Check if automatic A2A agent discovery is enabled."""
    return os.getenv("A2A_DISCOVERY_ENABLED", "true").lower() == "true"


def get_a2a_connection_timeout() -> int:
    """Get timeout for A2A connections in seconds."""
    return int(os.getenv("A2A_CONNECTION_TIMEOUT", "30"))


def get_a2a_retry_attempts() -> int:
    """Get number of retry attempts for A2A connections."""
    return int(os.getenv("A2A_RETRY_ATTEMPTS", "3"))
