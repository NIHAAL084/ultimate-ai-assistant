"""
A2A client tools for ZORA Assistant.
These tools allow ZORA to communicate with other A2A agents.
"""

import asyncio
import logging
from typing import List, Optional

from google.adk.tools.tool_context import ToolContext

from ..a2a_client import get_remote_agent_manager

logger = logging.getLogger(__name__)


async def list_available_agents(tool_context: ToolContext) -> str:
    """
    List all available A2A agents that ZORA can communicate with.
    
    Returns:
        A formatted list of available agents with their descriptions and capabilities.
    """
    try:
        manager = await get_remote_agent_manager()
        available_agents = manager.get_available_agents()
        
        if not available_agents:
            return "No A2A agents are currently available for communication."
        
        agent_info = manager.get_agent_info()
        return f"Available A2A agents ({len(available_agents)}):\\n\\n{agent_info}"
        
    except Exception as e:
        logger.error(f"Error listing available agents: {e}")
        return f"Error listing available agents: {str(e)}"


async def send_message_to_agent(
    agent_name: str, 
    message: str,
    tool_context: ToolContext
) -> str:
    """
    Send a message to another A2A agent and get their response.
    
    Args:
        agent_name: The name of the agent to send the message to
        message: The message content to send
        
    Returns:
        The response from the agent, or an error message if the request failed.
    """
    try:
        manager = await get_remote_agent_manager()
        
        # Get conversation context from tool_context if available
        state = tool_context.state if tool_context else {}
        context_id = state.get("a2a_context_id")
        task_id = state.get("a2a_task_id")
        
        logger.info(f"🤖 ZORA sending message to {agent_name}: {message[:100]}...")
        
        response_parts = await manager.send_message_to_agent(
            agent_name=agent_name,
            message=message,
            context_id=context_id,
            task_id=task_id
        )
        
        if not response_parts:
            return f"No response received from {agent_name}."
        
        # Combine all text responses
        response_text = ""
        for part in response_parts:
            if isinstance(part, dict) and part.get("type") == "text":
                response_text += part.get("text", "") + "\\n"
            elif hasattr(part, 'text'):
                response_text += str(part.text) + "\\n"
            else:
                response_text += str(part) + "\\n"
        
        if not response_text.strip():
            return f"Received response from {agent_name} but it contained no text content."
        
        logger.info(f"✅ Received response from {agent_name}")
        return f"Response from {agent_name}:\\n\\n{response_text.strip()}"
        
    except ValueError as e:
        # Agent not found error
        return str(e)
    except Exception as e:
        logger.error(f"Error sending message to {agent_name}: {e}")
        return f"Error communicating with {agent_name}: {str(e)}"


async def get_agent_capabilities(agent_name: str, tool_context: ToolContext) -> str:
    """
    Get detailed information about a specific A2A agent's capabilities.
    
    Args:
        agent_name: The name of the agent to get information about
        
    Returns:
        Detailed information about the agent's capabilities and skills.
    """
    try:
        manager = await get_remote_agent_manager()
        
        if agent_name not in manager.agent_cards:
            available_agents = ", ".join(manager.get_available_agents())
            return f"Agent '{agent_name}' not found. Available agents: {available_agents}"
        
        card = manager.agent_cards[agent_name]
        
        # Format the agent information
        info = f"Agent: {card.name}\\n"
        info += f"Description: {card.description}\\n"
        info += f"URL: {card.url}\\n"
        info += f"Version: {card.version}\\n"
        
        if card.capabilities:
            info += f"Capabilities: Streaming={card.capabilities.streaming}\\n"
        
        if card.skills:
            info += f"\\nSkills ({len(card.skills)}):\\n"
            for skill in card.skills:
                info += f"  • {skill.name}: {skill.description}\\n"
                if skill.examples:
                    info += f"    Examples: {', '.join(skill.examples)}\\n"
        
        return info
        
    except Exception as e:
        logger.error(f"Error getting agent capabilities for {agent_name}: {e}")
        return f"Error getting information about {agent_name}: {str(e)}"


async def discover_new_agents(agent_urls: List[str], tool_context: ToolContext) -> str:
    """
    Discover and connect to new A2A agents at the specified URLs.
    
    Args:
        agent_urls: List of URLs where A2A agents might be running
        
    Returns:
        Status message about the discovery process.
    """
    try:
        manager = await get_remote_agent_manager()
        
        initial_count = len(manager.get_available_agents())
        
        logger.info(f"🔍 Discovering agents at {len(agent_urls)} URLs...")
        await manager.discover_and_connect_agents(agent_urls)
        
        final_count = len(manager.get_available_agents())
        new_agents = final_count - initial_count
        
        if new_agents > 0:
            available_agents = manager.get_available_agents()
            return f"✅ Successfully discovered {new_agents} new agents. Now connected to {final_count} total agents: {', '.join(available_agents)}"
        else:
            return f"No new agents found at the provided URLs. Still connected to {final_count} agents."
            
    except Exception as e:
        logger.error(f"Error discovering new agents: {e}")
        return f"Error discovering new agents: {str(e)}"
