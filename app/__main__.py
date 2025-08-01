"""
Entry point for running the app as a module: python -m app
This starts both the main FastAPI server and the A2A server concurrently.
"""

import asyncio
import logging
import uvicorn
from .config import DEFAULT_HOST, DEFAULT_PORT
from .a2a_server import create_a2a_server, get_a2a_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def run_fastapi_server():
    """Run the main FastAPI server."""
    logger.info(f"Starting FastAPI server on {DEFAULT_HOST}:{DEFAULT_PORT}")
    config = uvicorn.Config(
        "app.main:app", 
        host=DEFAULT_HOST, 
        port=DEFAULT_PORT, 
        reload=False,  # Disable reload for concurrent execution
        log_level="info"
    )
    server = uvicorn.Server(config)
    await server.serve()


async def run_a2a_server():
    """Run the A2A server."""
    try:
        a2a_config = get_a2a_config()
        
        # Check if A2A server is enabled
        if not a2a_config["enabled"]:
            logger.info("⚠️ A2A server is disabled - skipping startup")
            return
        
        host = a2a_config["host"]
        port = a2a_config["port"]
        user_id = a2a_config["user_id"]
        
        logger.info(f"Starting A2A server on {host}:{port}")
        
        # Create A2A server
        a2a_app = create_a2a_server(host=host, port=port, user_id=user_id)
        
        # Run A2A server
        config = uvicorn.Config(
            a2a_app.build(),
            host=host,
            port=port,
            reload=False,
            log_level="info"
        )
        server = uvicorn.Server(config)
        await server.serve()
        
    except Exception as e:
        logger.error(f"Failed to start A2A server: {e}")
        raise


async def main():
    """Run both servers concurrently."""
    logger.info("🚀 Starting ZORA Ultimate AI Assistant")
    logger.info("🌐 FastAPI Server: Web interface and voice chat")
    
    # Check if A2A server should be started
    a2a_config = get_a2a_config()
    a2a_enabled = a2a_config["enabled"]
    
    if a2a_enabled:
        logger.info("🤖 A2A Server: Agent-to-Agent communication")
    else:
        logger.info("⚠️ A2A Server: Disabled (ACTIVATE_A2A_SERVER=False)")
    
    try:
        # Prepare server tasks
        server_tasks = [run_fastapi_server()]
        
        # Only add A2A server if enabled
        if a2a_enabled:
            server_tasks.append(run_a2a_server())
        
        # Run servers concurrently
        await asyncio.gather(*server_tasks, return_exceptions=True)
    except KeyboardInterrupt:
        logger.info("👋 Shutting down servers...")
    except Exception as e:
        logger.error(f"💥 Error running servers: {e}")
        raise


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Application stopped by user")
    except Exception as e:
        logger.error(f"💥 Failed to start application: {e}")
        exit(1)
