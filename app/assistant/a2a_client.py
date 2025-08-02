"""
Remote Agent Connection Manager for ZORA Assistant.
Manages connections to other A2A agents that ZORA can communicate with.
"""

import asyncio
import json
import logging
import uuid
from typing import Any, Dict, List, Optional

import httpx
from a2a.client import A2ACardResolver, A2AClient
from a2a.types import (
    AgentCard,
    MessageSendParams,
    SendMessageRequest,
    SendMessageResponse,
    SendMessageSuccessResponse,
    Task,
)

from .a2a_config import get_a2a_agent_urls, get_a2a_connection_timeout

logger = logging.getLogger(__name__)


class RemoteAgentConnection:
    """A connection to a single remote A2A agent."""

    def __init__(self, agent_card: AgentCard, agent_url: str):
        self.agent_card = agent_card
        self.agent_url = agent_url
        timeout = get_a2a_connection_timeout()
        self._httpx_client = httpx.AsyncClient(timeout=timeout)
        self.agent_client = A2AClient(self._httpx_client, agent_card, url=agent_url)
        logger.info(f"✅ Created connection to {agent_card.name} at {agent_url}")

    async def send_message(self, message_request: SendMessageRequest) -> SendMessageResponse:
        """Send a message to the remote agent."""
        return await self.agent_client.send_message(message_request)

    async def close(self):
        """Close the HTTP client connection."""
        await self._httpx_client.aclose()


class RemoteAgentManager:
    """Manages connections to multiple remote A2A agents."""

    def __init__(self):
        self.connections: Dict[str, RemoteAgentConnection] = {}
        self.agent_cards: Dict[str, AgentCard] = {}
        logger.info("🔗 RemoteAgentManager initialized")

    async def discover_and_connect_agents(self, agent_urls: List[str]) -> None:
        """
        Discover and connect to agents at the given URLs.
        
        Args:
            agent_urls: List of URLs where A2A agents are running
        """
        logger.info(f"🔍 Discovering agents at {len(agent_urls)} URLs...")
        
        async with httpx.AsyncClient(timeout=get_a2a_connection_timeout()) as client:
            for url in agent_urls:
                try:
                    logger.info(f"🔍 Discovering agent at {url}...")
                    card_resolver = A2ACardResolver(client, url)
                    card = await card_resolver.get_agent_card()
                    
                    connection = RemoteAgentConnection(agent_card=card, agent_url=url)
                    self.connections[card.name] = connection
                    self.agent_cards[card.name] = card
                    
                    logger.info(f"✅ Connected to {card.name}: {card.description}")
                    
                except httpx.ConnectError as e:
                    logger.warning(f"⚠️ Failed to connect to agent at {url}: {e}")
                except Exception as e:
                    logger.error(f"💥 Error discovering agent at {url}: {e}")

        logger.info(f"🔗 Connected to {len(self.connections)} agents")

    def get_available_agents(self) -> List[str]:
        """Get list of available agent names."""
        return list(self.connections.keys())

    def get_agent_info(self) -> str:
        """Get formatted information about available agents."""
        if not self.agent_cards:
            return "No remote agents available"
        
        agent_info = []
        for card in self.agent_cards.values():
            info = {
                "name": card.name,
                "description": card.description,
                "skills": [skill.name for skill in card.skills] if card.skills else []
            }
            agent_info.append(json.dumps(info, indent=2))
        
        return "\\n\\n".join(agent_info)

    async def send_message_to_agent(
        self, 
        agent_name: str, 
        message: str, 
        context_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Send a message to a specific agent.
        
        Args:
            agent_name: Name of the agent to send message to
            message: The message text to send
            context_id: Optional context ID for the conversation
            
        Returns:
            List of response parts from the agent
        """
        if agent_name not in self.connections:
            available_agents = ", ".join(self.get_available_agents())
            raise ValueError(
                f"Agent '{agent_name}' not found. Available agents: {available_agents}"
            )

        connection = self.connections[agent_name]
        
        # Generate IDs if not provided
        if not context_id:
            context_id = str(uuid.uuid4())
        message_id = str(uuid.uuid4())

        # Create the message payload - let server generate taskId
        payload = {
            "message": {
                "role": "user",
                "parts": [{"type": "text", "text": message}],
                "messageId": message_id,
                "contextId": context_id,
            },
        }

        message_request = SendMessageRequest(
            id=message_id, 
            params=MessageSendParams.model_validate(payload)
        )

        try:
            logger.info(f"📤 Sending message to {agent_name}: {message[:100]}...")
            send_response: SendMessageResponse = await connection.send_message(message_request)
            
            if not isinstance(send_response.root, SendMessageSuccessResponse) or not isinstance(send_response.root.result, Task):
                logger.warning("Received a non-success or non-task response")
                return []

            # Extract response content
            response_content = send_response.root.model_dump_json(exclude_none=True)
            json_content = json.loads(response_content)

            response_parts = []
            if json_content.get("result", {}).get("artifacts"):
                for artifact in json_content["result"]["artifacts"]:
                    if artifact.get("parts"):
                        response_parts.extend(artifact["parts"])

            logger.info(f"📥 Received {len(response_parts)} response parts from {agent_name}")
            return response_parts

        except Exception as e:
            logger.error(f"💥 Error sending message to {agent_name}: {e}")
            raise

    async def close_all_connections(self):
        """Close all agent connections."""
        logger.info("🔐 Closing all remote agent connections...")
        for connection in self.connections.values():
            try:
                await connection.close()
            except Exception as e:
                logger.warning(f"Warning: Error closing connection: {e}")
        
        self.connections.clear()
        self.agent_cards.clear()
        logger.info("✅ All connections closed")


# Global instance for the agent manager
_remote_agent_manager: Optional[RemoteAgentManager] = None


async def get_remote_agent_manager() -> RemoteAgentManager:
    """Get or create the global remote agent manager."""
    global _remote_agent_manager
    
    if _remote_agent_manager is None:
        _remote_agent_manager = RemoteAgentManager()
        
        # Get A2A agent URLs from configuration
        agent_urls = get_a2a_agent_urls()
        
        try:
            await _remote_agent_manager.discover_and_connect_agents(agent_urls)
        except Exception as e:
            logger.warning(f"⚠️ Failed to discover some agents: {e}")
    
    return _remote_agent_manager
