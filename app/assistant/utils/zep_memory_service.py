"""
ZepMemoryService implementation for ADK integration with Zep long-term memory.
Based on the tutorial from adk_memory_zep.ipynb
"""

import os
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from typing_extensions import override

# Google ADK components
from google.adk.sessions.session import Session
from google.adk.memory.base_memory_service import BaseMemoryService, MemoryEntry, SearchMemoryResponse
from google.genai import types

# Zep client library
from zep_cloud.client import Zep
from zep_cloud.types import Message
from zep_cloud.errors import NotFoundError, ConflictError


class ZepMemoryService(BaseMemoryService):
    """
    A memory service implementation that uses Zep as the backend for storing
    and retrieving conversation history and knowledge graph insights.
    """

    def __init__(self, zep_config: Optional[Dict[str, Any]] = None) -> None:
        """
        Initializes the ZepMemoryService.

        Args:
            zep_config: Optional dictionary containing Zep configuration
                        (e.g., 'api_key', 'zep_url').
        """
        config = zep_config or {}
        api_key = config.get("api_key") or os.getenv("ZEP_API_KEY")
        zep_url = config.get("zep_url")

        if not api_key:
            raise ValueError(
                "Zep API key is required. Pass via zep_config or ZEP_API_KEY env var."
            )

        print(f"Initializing ZepMemoryService...")
        try:
            self.client = Zep(api_key=api_key, base_url=zep_url)
            print(f"✅ Successfully initialized Zep client.")
        except Exception as e:
            print(f"💥 Failed to initialize Zep client or connect to Zep: {e}")
            raise

    def _ensure_user_exists(self, user_id: str) -> None:
        """
        Checks if a user exists in Zep. If not, creates the user.
        This is important as Zep sessions are associated with users.
        """
        try:
            self.client.user.get(user_id)
        except NotFoundError:
            try:
                self.client.user.add(user_id=user_id)
                print(f"User '{user_id}' created in Zep.")
            except ConflictError:
                print(f"User '{user_id}' was created by another process concurrently.")
            except Exception as e:
                print(f"💥 Error creating user '{user_id}' in Zep: {e}")

    def _map_role(self, author: str) -> str:
        """
        Maps ADK author names (typically 'user' or the agent's name)
        to Zep's `RoleType` (e.g., 'user', 'assistant').
        """
        author_lower = author.lower()
        if author_lower == "user":
            return "user"
        else:
            return "assistant"

    @override
    async def add_session_to_memory(self, session: Session) -> None:
        """
        Adds all relevant events from an ADK Session to Zep memory.
        This involves creating Zep messages from ADK events.
        """
        print(f"\n💾 Adding session '{session.id}' for user '{session.user_id}' to Zep memory...")

        if not session.events:
            print(f"No events in session '{session.id}' to add to memory. Skipping.")
            return

        # Ensure the user exists in Zep before adding session data
        self._ensure_user_exists(session.user_id)

        zep_messages = []
        for event in session.events:
            # We only store events that have textual content
            if not event.content or not event.content.parts:
                continue
            text_parts = [p.text for p in event.content.parts if p.text]
            if not text_parts:
                continue
            content = " ".join(text_parts).replace("\n", " ").strip()
            if not content: # Skip empty content
                continue

            role = self._map_role(event.author)
            # Store ADK-specific IDs in Zep message metadata for traceability
            metadata = {
                "adk_session_id": str(session.id),
                "adk_event_id": str(event.id),
                "adk_invocation_id": str(event.invocation_id) if event.invocation_id else None,
                "adk_branch": str(event.branch) if event.branch else None,
                "adk_author": event.author,
            }

            # Zep expects ISO format timestamps with timezone
            dt_meta = datetime.fromtimestamp(event.timestamp, tz=timezone.utc)
            created_at_iso = dt_meta.isoformat(timespec='microseconds')

            zep_messages.append(
                Message(
                    role_type=role,
                    content=content,
                    metadata=metadata,
                    created_at=created_at_iso,
                )
            )

        if zep_messages:
            try:
                # Ensure the session exists in Zep
                self.client.memory.add_session(
                    user_id=session.user_id,
                    session_id=session.id,
                )

                # Zep has a limit of 30 messages per batch, so we need to process in chunks
                batch_size = 30
                total_messages = len(zep_messages)
                
                print(f"Adding {total_messages} messages to Zep session '{session.id}' in batches of {batch_size}...")
                
                for i in range(0, total_messages, batch_size):
                    batch = zep_messages[i:i + batch_size]
                    batch_num = (i // batch_size) + 1
                    total_batches = (total_messages + batch_size - 1) // batch_size
                    
                    print(f"Processing batch {batch_num}/{total_batches} ({len(batch)} messages)...")
                    
                    self.client.memory.add(
                        session_id=session.id, # Use ADK session ID as Zep session ID
                        messages=batch
                    )
                    
                print(f"✅ Successfully added all {total_messages} messages from session '{session.id}' to Zep memory.")
            except Exception as e:
                print(f"💥 Unexpected error adding memory to Zep for session {session.id}: {e}")
                raise
        else:
            print(f"No processable messages found in ADK session '{session.id}' for Zep.")

    @override
    async def search_memory(
        self, *, app_name: str, user_id: str, query: str
    ) -> SearchMemoryResponse:
        """
        Searches Zep's knowledge graph for memories relevant to the user's query.
        ADK's `load_memory` tool will call this method.
        """
        print(f"\n🔍 Searching Zep graph memory for user '{user_id}' (app: '{app_name}') with query: '{query}'")
        try:
            # Zep graph search parameters (can be customized)
            limit = 5 # Number of relevant facts/edges to retrieve
            # `scope` can be "edges", "nodes", "facts", or "summary_and_facts"
            # "edges" often gives good conversational context. "facts" are more atomic.
            scope = "edges"

            # Ensure user exists before searching (though graph search is user-scoped, good practice)
            self._ensure_user_exists(user_id)

            graph_search_response = self.client.graph.search(
                user_id=user_id,
                query=query,
                limit=limit,
                scope=scope,
            )

            memory_results = []

            if graph_search_response:
                for edge in graph_search_response.edges:
                    # An "edge" in Zep's graph often represents a relationship or a summarized interaction.
                    # The `edge.fact` field usually contains the textual representation.
                    if not edge.fact:
                        continue

                    # ADK expects content in its `types.Content` format.
                    content_text = f"Relevant past information: {edge.fact}"
                    content = types.Content(parts=[types.Part(text=content_text)])

                    memory_results.append(
                        MemoryEntry(
                            content=content,
                            author="system",
                            timestamp=edge.created_at
                        )
                    )
                print(f"Processed {len(memory_results)} results for ADK.")
            else:
                print("No relevant edges found in Zep graph for this query.")

            return SearchMemoryResponse(memories=memory_results)

        except NotFoundError:
            print(f"User '{user_id}' not found during Zep memory search (should have been created).")
            return SearchMemoryResponse(memories=[])
        except Exception as e:
            print(f"💥 Error searching Zep memory for user '{user_id}': {e}")
            return SearchMemoryResponse(memories=[])
