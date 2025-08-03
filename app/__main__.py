"""
Entry point for running the app as a module: python -m app
This starts both the main FastAPI server and the A2A server concurrently.
"""

import asyncio
import logging
import subprocess
import uvicorn
from .config import DEFAULT_HOST, DEFAULT_PORT, USE_NGROK_FOR_A2A, NGROK_AUTHTOKEN, NGROK_URL, A2A_PORT, ACTIVATE_A2A_SERVER, A2A_HOST, A2A_SERVER_DEFAULT_USER
from .a2a_server import create_a2a_server

# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Changed from DEBUG to INFO
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Reduce verbosity of specific loggers
logging.getLogger('websockets').setLevel(logging.WARNING)  # Suppress websocket debug logs
logging.getLogger('websockets.client').setLevel(logging.WARNING)  # Suppress websocket client debug logs
logging.getLogger('websockets.server').setLevel(logging.WARNING)  # Suppress websocket server debug logs
logging.getLogger('asyncio').setLevel(logging.WARNING)  # Suppress asyncio debug logs
logging.getLogger('uvicorn').setLevel(logging.INFO)  # Reduce uvicorn verbosity
logging.getLogger('uvicorn.access').setLevel(logging.WARNING)  # Suppress access logs
logging.getLogger('httpx').setLevel(logging.WARNING)  # Suppress HTTP client debug logs
logging.getLogger('httpcore').setLevel(logging.WARNING)  # Suppress HTTP core debug logs
logging.getLogger('mcp').setLevel(logging.WARNING)  # Suppress MCP client debug logs
logging.getLogger('mcp.client').setLevel(logging.WARNING)  # Suppress MCP client logs
logging.getLogger('mcp.client.stdio').setLevel(logging.WARNING)  # Suppress MCP stdio errors
logging.getLogger('anyio').setLevel(logging.WARNING)  # Suppress anyio errors during MCP cleanup

# Enable debug logging for A2A components only
logging.getLogger('a2a').setLevel(logging.DEBUG)
logging.getLogger('a2a.server').setLevel(logging.DEBUG)
logging.getLogger('a2a.server.request_handlers').setLevel(logging.DEBUG)
logging.getLogger('a2a.server.tasks').setLevel(logging.DEBUG)

# Enable asyncio debugging (commented out to reduce verbosity)
# import sys
# if sys.version_info >= (3, 7):
#     import asyncio
#     asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy() if sys.platform == 'win32' else asyncio.DefaultEventLoopPolicy())

# Set asyncio debug mode (commented out to reduce verbosity)
# os.environ['PYTHONASYNCIODEBUG'] = '1'

# Global variable to track ngrok process
ngrok_process = None


async def setup_ngrok():
    """Set up ngrok for A2A server if enabled."""
    global ngrok_process
    
    if not USE_NGROK_FOR_A2A:
        logger.info("⚠️ Ngrok for A2A server is disabled")
        return False
    
    if not NGROK_AUTHTOKEN:
        logger.error("❌ NGROK_AUTHTOKEN not found in environment variables")
        logger.error("   Please set NGROK_AUTHTOKEN in your .env file")
        return False
    
    if not NGROK_URL:
        logger.error("❌ NGROK_URL not found in environment variables")
        logger.error("   Please set NGROK_URL in your .env file")
        return False
    
    try:
        # Add ngrok authtoken
        logger.info("🔐 Configuring ngrok authtoken...")
        subprocess.run([
            "ngrok", "config", "add-authtoken", NGROK_AUTHTOKEN
        ], check=True, capture_output=True, text=True)
        logger.info("✅ Ngrok authtoken configured successfully")
        
        # Start ngrok tunnel
        logger.info(f"🌐 Starting ngrok tunnel: {NGROK_URL} -> localhost:{A2A_PORT}")
        ngrok_process = subprocess.Popen([
            "ngrok", "http", f"--url={NGROK_URL}", str(A2A_PORT)
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Give ngrok a moment to start
        await asyncio.sleep(3)
        
        # Check if ngrok process is still running
        if ngrok_process.poll() is None:
            logger.info(f"✅ Ngrok tunnel started successfully: {NGROK_URL}")
            return True
        else:
            # Get error output
            _, stderr = ngrok_process.communicate()
            logger.error(f"❌ Ngrok failed to start: {stderr}")
            ngrok_process = None
            return False
            
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Failed to configure ngrok: {e}")
        return False
    except FileNotFoundError:
        logger.error("❌ Ngrok not found. Please install ngrok first:")
        logger.error("   brew install ngrok  # macOS")
        logger.error("   or download from https://ngrok.com/download")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error setting up ngrok: {e}")
        return False


async def cleanup_ngrok():
    """Clean up ngrok process."""
    global ngrok_process
    
    if ngrok_process:
        logger.info("🛑 Stopping ngrok tunnel...")
        try:
            ngrok_process.terminate()
            await asyncio.sleep(2)
            if ngrok_process.poll() is None:
                ngrok_process.kill()
            logger.info("✅ Ngrok tunnel stopped")
        except Exception as e:
            logger.error(f"⚠️ Error stopping ngrok: {e}")
        finally:
            ngrok_process = None


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
        # Check if A2A server is enabled
        if not ACTIVATE_A2A_SERVER:
            logger.info("⚠️ A2A server is disabled - skipping startup")
            return
        
        # Use config values directly (already loaded from environment via config.py)
        host = A2A_HOST
        port = A2A_PORT
        user_id = A2A_SERVER_DEFAULT_USER
        
        logger.info(f"Starting A2A server on {host}:{port}")
        
        # Create A2A server
        a2a_app = create_a2a_server(host=host, port=port, user_id=user_id)
        
        # Check if server was actually created (could be None if disabled)
        if a2a_app is None:
            logger.info("⚠️ A2A server creation returned None - server disabled")
            return
        
        # Run A2A server
        config = uvicorn.Config(
            a2a_app,  # a2a_app is already the built Starlette app
            host=host,
            port=port,
            reload=False,
            log_level="info"  # Changed from debug to info
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
    a2a_enabled = ACTIVATE_A2A_SERVER
    
    if a2a_enabled:
        logger.info("🤖 A2A Server: Agent-to-Agent communication")
    else:
        logger.info("⚠️ A2A Server: Disabled (ACTIVATE_A2A_SERVER=False)")
    
    # Set up ngrok if A2A server is enabled and ngrok is requested
    ngrok_success = False
    if a2a_enabled and USE_NGROK_FOR_A2A:
        ngrok_success = await setup_ngrok()
        if not ngrok_success:
            logger.warning("⚠️ Ngrok setup failed, continuing without ngrok")
    
    try:
        # Prepare server tasks
        server_tasks = [run_fastapi_server()]
        
        # Only add A2A server if enabled
        if a2a_enabled:
            server_tasks.append(run_a2a_server())
        
        # Run servers concurrently
        results = await asyncio.gather(*server_tasks, return_exceptions=True)
        
        # Check for any exceptions in the results
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Server {i} failed with exception: {result}")
                
    except KeyboardInterrupt:
        logger.info("👋 Shutting down servers...")
        # Clean up ngrok
        await cleanup_ngrok()
        # Give a moment for cleanup
        await asyncio.sleep(1.0)
    except Exception as e:
        logger.error(f"💥 Error running servers: {e}")
        # Clean up ngrok
        await cleanup_ngrok()
        raise
    finally:
        # Ensure ngrok is cleaned up
        await cleanup_ngrok()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Application stopped by user")
    except Exception as e:
        logger.error(f"💥 Failed to start application: {e}")
        # Ensure ngrok cleanup even on startup failure
        if ngrok_process:
            try:
                ngrok_process.terminate()
            except:
                pass
        exit(1)
