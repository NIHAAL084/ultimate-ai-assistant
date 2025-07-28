# Architecture Overview

## System Architecture

The Ultimate AI Assistant is built using Google's Agent Development Kit (ADK) with a modular, extensible architecture that supports real-time streaming, persistent memory, and specialized sub-agents.

### Core Components

#### Main Application (`app/main.py`)

- **FastAPI Server**: Handles HTTP requests and WebSocket connections
- **WebSocket Interface**: Real-time bidirectional communication
- **Session Management**: Random session IDs with memory persistence
- **File Upload**: Drag-and-drop file processing with temporary storage

#### Agent System (`app/assistant/`)

- **Root Agent**: Main conversational AI with dynamic context
- **Sub-Agents**: Specialized agents for external service integration
- **Tool Architecture**: Modular tool system with unified exports
- **Memory Integration**: Zep-powered long-term conversation memory

#### Memory System

- **ZepMemoryService**: Long-term memory with knowledge graphs
- **SessionMemoryManager**: Automatic session persistence
- **Cross-Session Continuity**: Remember user context across conversations

### Data Flow

```
User Input → WebSocket → Root Agent → Tools/Sub-Agents → External Services
                ↓                           ↓
            Session Storage            Memory Service (Zep)
                ↓                           ↓
            Response Stream ← Agent Response ← Knowledge Graph
```

### Tool System

#### Document Processing

- **Unified Tool**: Single `process_document_tool` for all formats
- **Format Detection**: Automatic PDF, DOCX, TXT recognition
- **OCR Fallback**: Handles scanned documents
- **Table Extraction**: Structured data from documents

#### File Management

- **Auto-Registration**: Silent file discovery system
- **Inventory Management**: Track available user files
- **Cleanup**: Automatic temporary file handling

#### Web Search

- **Google Integration**: Real-time information retrieval
- **Context Integration**: Search results integrated into conversations

### Memory Architecture

#### Zep Integration

- **Knowledge Graphs**: Semantic relationship building
- **Conversation History**: Persistent across sessions
- **Memory Search**: Retrieve relevant past interactions
- **Automatic Storage**: Sessions saved on disconnect

#### Session Management

- **Random IDs**: Each conversation gets unique identifier
- **Isolation**: Browser sessions represent separate conversations
- **Persistence**: User context maintained across sessions

### Sub-Agent Integration

#### Agent-as-Tool Pattern

- **Tool Registration**: Sub-agents registered as callable tools
- **Dynamic Context**: Current time and user context injection
- **MCP Protocol**: External service communication via Model Context Protocol
- **User-Specific Config**: Individual API credentials per user

#### Available Sub-Agents

- **Calendar Agent**: Google Calendar integration via MCP
- **Task Management**: Todoist integration via MCP
- **Extensible**: Framework for adding new specialized agents

### Security & Configuration

#### Environment Management

- **Main Environment**: Shared API keys (Google AI, Zep)
- **User-Specific**: Individual service tokens per user
- **Priority Loading**: User configs override defaults
- **Template System**: Easy user onboarding

#### File Handling

- **Temporary Storage**: Secure file upload handling
- **Format Validation**: Type checking and security scanning
- **Cleanup**: Automatic temporary file removal

### Scalability Features

#### Streaming Interface

- **Real-Time**: WebSocket-based communication
- **Turn Management**: Proper conversation flow handling
- **Interruption Support**: User can interrupt ongoing responses
- **Audio Streaming**: PCM audio input support

#### Modular Design

- **Clean Separation**: Tools, agents, and utilities properly separated
- **Easy Extension**: Add new tools and agents without core changes
- **Error Isolation**: Failures in one component don't affect others

### Development Architecture

#### Project Structure

```
app/
├── main.py                    # FastAPI server & WebSocket
├── config.py                  # Centralized configuration
├── user_env.py               # User environment management
├── assistant/
│   ├── agent.py              # Root agent with memory
│   ├── tools/                # Tool implementations
│   ├── sub_agents/           # Specialized agents
│   └── utils/                # Core utilities
└── static/                   # Frontend assets
```

#### Build System

- **UV Package Manager**: Fast dependency resolution
- **pyproject.toml**: Modern Python project configuration
- **Lock Files**: Reproducible dependency management

### Performance Considerations

#### Memory Management

- **Persistent Storage**: Zep handles long-term memory off-heap
- **Session Cleanup**: Automatic cleanup of inactive sessions
- **File Cleanup**: Temporary files removed after processing

#### Streaming Optimization

- **Chunked Responses**: Large responses streamed in chunks
- **Non-Blocking**: Async/await throughout for non-blocking I/O
- **Connection Management**: Proper WebSocket lifecycle handling

### Future Extensibility

#### Plugin System

- **MCP Integration**: Easy addition of new external services
- **Tool Framework**: Standardized tool development pattern
- **Agent Framework**: Consistent sub-agent development

#### API Evolution

- **Versioned Endpoints**: Support for API evolution
- **Backward Compatibility**: Maintain compatibility across versions
- **Feature Flags**: Gradual rollout of new capabilities
