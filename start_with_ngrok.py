#!/usr/bin/env python3
"""
Startup script for ZORA with ngrok integration.
This script configures ngrok and starts the A2A server.
"""

import asyncio
import subprocess
import time
import signal
import sys
import os
from app.config import NGROK_AUTHTOKEN, NGROK_URL

def setup_ngrok():
    """Configure ngrok with the auth token."""
    print("🔧 Configuring ngrok...")
    try:
        # Add auth token
        result = subprocess.run([
            "ngrok", "config", "add-authtoken", NGROK_AUTHTOKEN
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Ngrok auth token configured successfully")
        else:
            print(f"⚠️ Warning: ngrok auth token configuration: {result.stderr}")
    
    except FileNotFoundError:
        print("❌ Error: ngrok is not installed or not in PATH")
        print("Please install ngrok from https://ngrok.com/download")
        sys.exit(1)

def start_ngrok():
    """Start ngrok tunnel."""
    print(f"🌐 Starting ngrok tunnel to {NGROK_URL}...")
    try:
        # Extract the subdomain from the URL
        subdomain = NGROK_URL.replace("https://", "").replace(".ngrok-free.app", "")
        
        # Start ngrok
        ngrok_process = subprocess.Popen([
            "ngrok", "http", "--url=" + NGROK_URL, "80"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        print("✅ Ngrok tunnel started")
        print(f"🔗 Public URL: {NGROK_URL}")
        
        return ngrok_process
    
    except Exception as e:
        print(f"❌ Error starting ngrok: {e}")
        sys.exit(1)

async def start_zora():
    """Start the ZORA application."""
    print("🚀 Starting ZORA Ultimate AI Assistant...")
    from app.__main__ import main
    await main()

def signal_handler(sig, frame, ngrok_process):
    """Handle shutdown signals."""
    print("\n🛑 Shutting down...")
    if ngrok_process:
        ngrok_process.terminate()
        print("✅ Ngrok tunnel stopped")
    sys.exit(0)

async def main():
    """Main function to start everything."""
    # Setup ngrok
    setup_ngrok()
    
    # Start ngrok tunnel
    ngrok_process = start_ngrok()
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, lambda s, f: signal_handler(s, f, ngrok_process))
    signal.signal(signal.SIGTERM, lambda s, f: signal_handler(s, f, ngrok_process))
    
    # Wait a moment for ngrok to establish the tunnel
    print("⏳ Waiting for ngrok tunnel to establish...")
    time.sleep(3)
    
    try:
        # Start ZORA
        await start_zora()
    except KeyboardInterrupt:
        signal_handler(signal.SIGINT, None, ngrok_process)
    except Exception as e:
        print(f"❌ Error starting ZORA: {e}")
        if ngrok_process:
            ngrok_process.terminate()
        sys.exit(1)

if __name__ == "__main__":
    print("=" * 60)
    print("🌟 ZORA Ultimate AI Assistant with Ngrok")
    print("=" * 60)
    
    asyncio.run(main())
