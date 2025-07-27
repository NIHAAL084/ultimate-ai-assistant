"""
Session management utilities for automatic Zep memory integration
"""

from typing import Optional
from google.adk.sessions.session import Session
from .zep_memory_service import ZepMemoryService


class SessionMemoryManager:
    """
    Manages automatic session storage to Zep memory service.
    This class can be used to automatically save sessions to long-term memory.
    """
    
    def __init__(self, memory_service: Optional[ZepMemoryService] = None):
        self.memory_service = memory_service
        
    async def auto_save_session(self, session: Session) -> bool:
        """
        Automatically saves a session to Zep memory if the memory service is available.
        
        Args:
            session: The ADK session to save
            
        Returns:
            bool: True if session was saved successfully, False otherwise
        """
        if not self.memory_service:
            print("⚠️ No memory service available for session saving")
            return False
            
        try:
            # Only save sessions that have meaningful content (user interactions)
            if not session.events or len(session.events) < 2:
                print(f"📝 Session '{session.id}' has insufficient events for memory storage")
                return False
                
            # Debug: Print session structure to understand event format
            print(f"🔍 Session '{session.id}' has {len(session.events)} events")
            
            # Check if session has user messages - now that we manually add them, this should work
            user_messages = [event for event in session.events if event.author.lower() == "user"]
            
            print(f"📊 Found {len(user_messages)} user messages out of {len(session.events)} total events")
            
            if not user_messages:
                print(f"📝 Session '{session.id}' has no user messages, skipping memory storage")
                return False
                
            await self.memory_service.add_session_to_memory(session)
            print(f"✅ Session '{session.id}' automatically saved to Zep memory")
            return True
            
        except Exception as e:
            print(f"💥 Failed to auto-save session '{session.id}' to memory: {e}")
            return False
            
    def is_memory_available(self) -> bool:
        """Check if memory service is available and working"""
        return self.memory_service is not None
