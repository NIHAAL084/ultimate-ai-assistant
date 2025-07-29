# ZORA - Ultimate AI Assistant 🤖

**ZORA** is a sophisticated multi-modal AI assistant powered by Google's latest Gemini 2.0 Flash model and Agent Development Kit (ADK). It combines the conversational abilities of ChatGPT with advanced voice interaction, persistent memory, and real-world integrations for calendar and task management.

## 🎯 What Makes ZORA Different

Unlike simple chatbots, ZORA is designed as a **complete AI companion** that:

- **Remembers everything** across conversations using advanced knowledge graphs
- **Speaks and listens** with real-time voice interaction
- **Actually helps** with your calendar, tasks, and documents
- **Switches modes seamlessly** between text and voice without interruption
- **Supports multiple users** with isolated environments and credentials

## ✨ Core Capabilities

### 💬 **Intelligent Conversation**

- **Gemini 2.0 Flash Model**: Latest Google AI with superior reasoning and multimodal understanding
- **Persistent Memory**: Remembers conversations across sessions using Zep's knowledge graph technology
- **Context Awareness**: Always knows the current date/time and maintains conversation context
- **Multi-User Support**: Each user gets isolated memory and conversation history

### 🎤 **Advanced Voice Features**

- **Real-Time Audio**: Native Web Audio API with 16kHz PCM streaming
- **Seamless Mode Switching**: Toggle between text and voice without losing context
- **Multiple Voice Options**: Choose from 8 distinct AI voices (Puck, Charon, Kore, Fenrir, Aoede, Leda, Orus, Zephyr)
- **Low Latency**: Sub-100ms audio processing for natural conversation flow
- **AudioWorklet Processing**: Dedicated audio threads for optimal performance

### 📄 **Document Intelligence**

- **Unified Processing**: Single tool handles PDF, DOCX, TXT, and image files
- **OCR Capabilities**: Extracts text from scanned documents and images
- **Table Extraction**: Intelligently parses structured data from documents
- **Visual Analysis**: Native vision capabilities for image understanding
- **Drag-and-Drop Interface**: Simple file upload with immediate processing

### 🛠️ **Primary Agent Toolset**

The primary agent has access to these specialized tools:

#### **Core Tools**

- **`google_search`**: Real-time web search for current information
- **`load_memory`**: Searches Zep knowledge graph for relevant past conversations
- **`process_document_tool`**: Unified PDF/DOCX/TXT/image processing with OCR
- **`register_uploaded_files_tool`**: Automatically discovers and registers user files
- **`list_available_user_files_tool`**: Lists all files available for processing

#### **Agent-as-Tool Sub-Agents**

- **`calendar_tool`**: AgentTool wrapper around Calendar Agent (connects to Google Calendar MCP server)
- **`task_management_tool`**: AgentTool wrapper around Task Management Agent (connects to Todoist MCP server)

#### **Tool Orchestration**

The primary agent intelligently decides which tools to use based on user requests:

- **Memory queries** → `load_memory` tool automatically searches past conversations
- **Calendar requests** → `calendar_tool` agent handles Google Calendar operations
- **Task management** → `task_management_tool` agent handles Todoist operations
- **Document questions** → `process_document_tool` analyzes uploaded files
- **Current information** → `google_search` provides real-time web results

### 🤖 **Specialized Agents**

ZORA implements an **Agent-as-Tool** architecture where specialized sub-agents are integrated as tools within the primary agent. Each sub-agent connects to dedicated MCP (Model Context Protocol) servers for external service integration:

#### **Calendar Agent** (Google Calendar)

- **MCP Server**: `@cocal/google-calendar-mcp` - Specialized Node.js server for Google Calendar API
- **Agent-as-Tool Integration**: Wrapped as an `AgentTool` and included in the primary agent's toolset
- **User-Specific Configuration**: Each user's OAuth credentials loaded from their environment file
- **Capabilities**:
  - Multi-calendar management (personal, work, shared calendars)
  - Natural language scheduling: *"Schedule a meeting with John tomorrow at 2 PM"*
  - Availability checking across all calendars
  - Event creation, modification, and deletion
  - Recurring event management
  - Smart conflict detection

#### **Task Management Agent** (Todoist)

- **MCP Server**: `@nihaal084/todoist-mcp-server` - Custom Gemini-compatible Todoist server
- **Agent-as-Tool Integration**: Deployed as specialized agent tool within primary agent
- **User-Specific Configuration**: Individual Todoist API tokens from user environment
- **Capabilities**:
  - Natural language task creation: *"Add buy groceries to my high-priority list"*
  - Smart due date parsing: "tomorrow", "next week", "Friday at 3 PM"
  - Project organization and task categorization
  - Completion tracking and progress monitoring
  - Search and filtering across all tasks

#### **Technical Implementation**

```python
# Primary agent creates sub-agents as tools
calendar_agent = create_calendar_agent(user_id=user_id)
calendar_tool = AgentTool(agent=calendar_agent)

task_management_agent = create_task_management_agent(user_id=user_id)  
task_management_tool = AgentTool(agent=task_management_agent)

# Sub-agents included in primary agent's toolset
return Agent(
    name="assistant",
    tools=[
        google_search,
        load_memory,
        process_document_tool,
        calendar_tool,        # Calendar agent as tool
        task_management_tool  # Task agent as tool
    ]
)
```

Each sub-agent runs its own MCP server process with user-specific environment variables, ensuring complete isolation between users while providing specialized functionality to the primary conversational agent.

### 🧠 **Memory System**

ZORA uses Zep Cloud's advanced memory service with knowledge graph technology for persistent conversation memory:

#### **How Memory Works**

- **Knowledge Graph Storage**: Conversations stored as semantic nodes and edges in Zep's graph database
- **Automatic Session Saving**: When you disconnect, your entire conversation is automatically saved to Zep
- **Smart Memory Search**: ZORA uses the `load_memory` tool to search past conversations when you ask about previous topics
- **Cross-Session Persistence**: Conversations remembered across browser restarts, days, and even weeks
- **User Isolation**: Each user's memory is completely separate and private

#### **Memory Search Process**

```python
# When you ask about something from the past, ZORA:
1. Detects reference to previous conversation
2. Automatically calls load_memory tool with your query
3. Searches Zep's knowledge graph for relevant "edges" (relationships/facts)
4. Retrieves up to 5 most relevant pieces of context
5. Incorporates that information naturally in the response
```

#### **When Memory is Saved**

- **Session End**: Complete conversation saved when WebSocket disconnects
- **Automatic Processing**: Session converted to knowledge graph nodes and relationships
- **Background Operation**: Memory saving happens automatically without user intervention
- **Error Handling**: Robust error handling ensures memory isn't lost due to network issues

#### **Example Memory Retrieval**

```conversation
[Day 1]
You: "I'm working on a machine learning project about image classification"
ZORA: "That sounds interesting! I'll remember this..."

[Day 3 - New conversation]
You: "Can you help me with my project?"
ZORA: [Automatically searches memory] "Of course! I remember you're working 
      on an image classification machine learning project. What specific 
      aspect would you like help with?"
```

## 🚀 Quick Start Guide

### Prerequisites

- **Python 3.11+** (check with `python --version`)
- **Modern Browser** (Chrome recommended for best audio performance)
- **Microphone** (for voice features)
- **Internet Connection** (for AI services and memory)

### 1. Installation (2 minutes)

```bash
# Clone the repository
git clone <your-repository-url>
cd ultimate-ai-assistant

# Install UV package manager (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install all dependencies
uv sync
```

### 2. Get Required API Keys

#### Google AI API Key (Required)

1. Visit [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Click "Create API Key"
3. Copy the key (starts with `AIza...`)

#### Zep Memory API Key (Required)

1. Go to [Zep Cloud](https://www.getzep.com/)
2. Create a free account (includes generous free tier)
3. Copy your API key from the dashboard

### 3. Configure Environment

```bash
# Create your environment file
cp .env.example .env

# Edit .env and add your keys:
GOOGLE_API_KEY=AIza_your_actual_google_key_here
ZEP_API_KEY=your_actual_zep_key_here
```

### 4. Launch ZORA

```bash
# Start the server
uv run python -m app

# Open your browser to:
http://localhost:8001
```

**That's it!** You should see ZORA's interface. Try typing a message or clicking the microphone to start talking.

## 📖 How to Use ZORA

### Basic Conversation

1. **Text**: Type any question or request in the input field
2. **Voice**: Click the microphone button and speak naturally
3. **Files**: Drag and drop documents or images for analysis
4. **Memory**: Reference previous conversations - ZORA remembers everything

### Example Interactions

#### **Simple Questions**

```conversation
You: "What's 15% of 250?"
ZORA: "15% of 250 is 37.5"

You: "Remember that I prefer meetings in the afternoon"
ZORA: "I'll remember your preference for afternoon meetings."
```

#### **Document Analysis**

```conversation
[Upload a PDF contract]
You: "What are the key terms and any potential risks?"
ZORA: "Based on the contract you uploaded, here are the key terms: 
       [detailed analysis with specific clauses and risk assessment]"
```

#### **Voice Commands**

```conversation
[Click microphone]
You: "Schedule a dentist appointment for next Tuesday at 3 PM"
ZORA: [Speaking] "I've scheduled your dentist appointment for Tuesday, 
      January 30th at 3:00 PM. Would you like me to set a reminder?"
```

#### **Memory and Context**

```conversation
[In a previous session]
You: "I'm working on a machine learning project about image classification"

[Days later, in a new session]
You: "Can you help me with my project?"
ZORA: "Of course! I remember you're working on an image classification 
      machine learning project. What specific aspect would you like help with?"
```

## 🛠️ Advanced Setup: Calendar & Tasks

For full productivity features, set up ZORA to manage your actual calendar and tasks:

### Prerequisites for Advanced Features

```bash
# Install Node.js MCP servers (one-time setup)
npm install -g @cocal/google-calendar-mcp
npm install -g @nihaal084/todoist-mcp-server
```

### Setting Up Google Calendar Integration

1. **Create Google Cloud Project**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing one
   - Enable the Google Calendar API

2. **Get OAuth Credentials**:
   - Go to "Credentials" → "Create Credentials" → "OAuth 2.0 Client IDs"
   - Choose "Desktop application"
   - Download the JSON file

3. **Set Up Todoist**:
   - Go to [Todoist](https://todoist.com/) → Settings → Integrations
   - Copy your API token

4. **Register with ZORA**:
   - On ZORA's homepage, click "Register New User"
   - Enter a username (letters, numbers, hyphens only)
   - Upload your Google OAuth JSON file
   - Enter your Todoist API token
   - Click "Register"

### Advanced Voice Commands (After Setup)

```voice
"What's on my calendar tomorrow?"
"Schedule a team meeting for Friday at 2 PM"
"Move my 3 PM meeting to 4 PM"
"Add a high-priority task to review the quarterly report"
"Show me all tasks due this week"
"Mark the grocery shopping task as complete"
```

## 🔧 Technical Architecture

### Backend Stack

- **FastAPI**: High-performance async web framework for HTTP and WebSocket handling
- **Google ADK**: Agent Development Kit for advanced AI agent creation and tool integration
- **Gemini 2.0 Flash**: Latest multimodal AI model with superior reasoning capabilities
- **Zep Memory**: Vector-based conversation memory with automated knowledge graph construction
- **MCP Protocol**: Model Context Protocol for secure external service integrations

### Agent-as-Tool Architecture

```python
# Primary Agent Architecture
Primary Agent (Gemini 2.0 Flash)
├── google_search tool
├── load_memory tool (searches Zep knowledge graph)
├── process_document_tool 
├── AgentTool(calendar_agent)     # Calendar sub-agent as tool
└── AgentTool(task_agent)         # Task sub-agent as tool

# Sub-Agent MCP Connections
Calendar Agent → MCPToolset → @cocal/google-calendar-mcp server
Task Agent → MCPToolset → @nihaal084/todoist-mcp-server
```

### MCP Server Implementation

Each sub-agent connects to dedicated Node.js MCP servers:

```python
# Calendar Agent MCP Configuration
MCPToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command="uv",
            args=["run", "npx", "@cocal/google-calendar-mcp"],
            env={"GOOGLE_OAUTH_CREDENTIALS": user_oauth_path},
        ),
        timeout=60.0,
    )
)

# Task Agent MCP Configuration  
MCPToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command="uv", 
            args=["run", "npx", "-y", "@nihaal084/todoist-mcp-server"],
            env={"TODOIST_API_TOKEN": user_token},
        ),
        timeout=60.0,
    )
)
```

### Memory Service Integration

#### Zep Memory Architecture

```python
# Memory Service Flow
User Message → Primary Agent → load_memory tool → Zep API
                                    ↓
                            Knowledge Graph Search
                                    ↓
                        Relevant Facts Retrieved → Agent Context
                                    ↓
                            Enhanced Response

# Session Storage (on disconnect)
WebSocket Disconnect → Session → ZepMemoryService.add_session_to_memory()
                                        ↓
                                Knowledge Graph Update
                                        ↓
                                Future Search Index
```

#### Memory Search Implementation

When users reference past conversations, ZORA automatically:

1. **Detects Memory Query**: User asks about previous interactions
2. **Calls load_memory Tool**: ADK automatically invokes memory search
3. **Zep Graph Search**: Searches knowledge graph with semantic similarity
4. **Edge Retrieval**: Gets up to 5 most relevant relationship edges
5. **Context Integration**: Incorporates findings into response naturally

### Frontend Technology

- **Vanilla JavaScript**: No heavy frameworks for optimal audio performance
- **Web Audio API**: Native browser audio processing with AudioContext
- **AudioWorklet**: Dedicated audio processing threads for low-latency streaming
- **WebSocket Protocol**: Real-time bidirectional communication with custom message types
- **Drag-and-Drop API**: Modern file upload interface with immediate processing

### Security & Isolation

- **User Environment Isolation**: Each user gets separate `.env.{username}` files
- **OAuth Credential Management**: Google credentials stored per-user in `oauth_credentials/`
- **MCP Process Isolation**: Each sub-agent runs independent MCP server processes
- **Memory Separation**: Zep memory completely isolated by user_id
- **API Key Security**: All sensitive credentials stored in environment variables

## 📁 Project Structure

```directory
ultimate-ai-assistant/
├── app/                           # Main application package
│   ├── __main__.py               # Entry point (python -m app)
│   ├── main.py                   # FastAPI server, WebSocket handling
│   ├── config.py                 # Application settings (port 8001, voices)
│   ├── user_env.py              # Multi-user environment management
│   │
│   ├── static/                   # Frontend web interface
│   │   ├── index.html           # Main application UI
│   │   └── js/                  # JavaScript modules
│   │       ├── app.js                   # Core application logic
│   │       ├── audio-recorder.js        # Audio capture & processing
│   │       ├── audio-player.js          # Audio playback controls
│   │       ├── dither-background.js     # Visual effects
│   │       ├── pcm-recorder-processor.js # PCM audio processing
│   │       └── pcm-player-processor.js  # PCM audio playback
│   │
│   └── assistant/               # AI agent system
│       ├── agent.py             # Main agent creation with dynamic prompts
│       ├── prompt.py            # System prompts and instructions
│       │
│       ├── tools/               # Agent tools and capabilities
│       │   ├── document_tools.py        # PDF/DOCX/TXT processing with OCR
│       │   └── file_tools.py            # File management and registration
│       │
│       ├── sub_agents/          # Specialized external service agents
│       │   ├── calendar_agent/          # Google Calendar MCP integration
│       │   └── task_management_agent/   # Todoist MCP integration
│       │
│       └── utils/               # Core utilities
│           ├── zep_memory_service.py     # Persistent memory integration
│           ├── session_memory_manager.py # Session state management
│           └── data_extractor.py         # Data extraction utilities
│
├── user_data/                   # User-specific configurations
│   ├── .env.{username}         # User environment variables
│   └── oauth_credentials/      # User OAuth JSON files
│
├── tests/                      # Test suite
├── manage_users.py            # User management CLI tool
├── pyproject.toml             # Python dependencies (UV package manager)
├── uv.lock                    # Locked dependency versions
├── .env.example               # Environment template
└── .python-version            # Python 3.11 requirement
```

## 🔌 API Reference

### HTTP Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | Main web interface |
| `/config` | GET | Application configuration |
| `/health` | GET | Server health check |
| `/validate-user` | POST | Check if user exists |
| `/register-user` | POST | Create new user account |
| `/update-user` | POST | Update user credentials |
| `/upload-credentials` | POST | Upload OAuth files |
| `/upload` | POST | Process documents/images |
| `/ws/{session_id}` | WebSocket | Real-time chat interface |

### WebSocket Message Types

#### Mode Switching

```json
{
  "mime_type": "application/mode-change",
  "mode": "audio" | "text"
}
```

#### Audio Data (16kHz PCM)

```json
{
  "mime_type": "audio/pcm",
  "data": "base64_encoded_pcm_audio_data"
}
```

#### Text Messages

```json
{
  "mime_type": "text/plain", 
  "text": "User message content"
}
```

#### File Attachments

```json
{
  "mime_type": "text/plain",
  "text": "User message about files",
  "files": ["filename1.pdf", "filename2.jpg"]
}
```

## 🛠️ User Management Commands

ZORA includes a CLI tool for managing users and their environments:

```bash
# Set up user environment templates
python manage_users.py setup

# List all registered users
python manage_users.py list

# Validate user configuration
python manage_users.py validate --user username

# Switch between users (for testing)
python manage_users.py switch --user username
```

### User Environment Structure

```bash
user_data/
├── .env.johndoe              # User's API tokens
├── .env.alice                # Another user's tokens
└── oauth_credentials/        # OAuth files
    ├── johndoe_credentials.json
    └── alice_credentials.json
```

## 🔧 Troubleshooting

### Common Issues & Solutions

#### **"Can't access microphone"**

- **Browser permissions**: Click the microphone icon in your browser's address bar
- **HTTPS requirement**: In production, microphone access requires HTTPS
- **Browser compatibility**: Use Chrome/Chromium for best audio performance

#### **"API key not working"**

- **No spaces/quotes**: Check `.env` file has `KEY=value` format (no spaces around =)
- **Correct key**: Ensure you copied the complete API key
- **Permissions**: Verify the key has appropriate API access

#### **"Server won't start"**

- **Python version**: Ensure you have Python 3.11+ (`python --version`)
- **Dependencies**: Run `uv sync` to install all required packages
- **Port conflict**: Port 8001 might be in use by another application

#### **"Calendar/tasks not working"**

- **User registration**: You must register a user account first
- **MCP servers**: Install Node.js packages globally: `npm install -g @cocal/google-calendar-mcp @nihaal084/todoist-mcp-server`
- **OAuth setup**: Ensure Google Calendar API is enabled in your Cloud Console
- **File upload**: Verify your OAuth JSON file uploaded successfully

#### **"Memory not persisting"**

- **Zep service**: Check your Zep API key is valid and has quota remaining
- **Internet connection**: Memory requires connection to Zep's cloud service
- **Session isolation**: Each browser session has separate memory (this is intentional)

#### **"Audio quality issues"**

- **Browser choice**: Chrome/Chromium provides best audio performance
- **Network stability**: Poor connection affects real-time audio
- **Microphone quality**: Use a good quality microphone or headset
- **Background noise**: Use in a quiet environment for best results

### Getting Help

1. **Check server logs**: Look at the terminal where you ran `uv run python -m app`
2. **Browser console**: Press F12 → Console tab to see JavaScript errors
3. **Validate environment**: Run `python manage_users.py validate --user yourusername`
4. **Test incrementally**: Start with text chat, then try voice, then advanced features

### Performance Optimization

#### **For Better Audio Performance**

- Use Chrome or Chromium browser
- Close other audio-intensive applications
- Use a wired headset instead of speakers (prevents echo)
- Ensure stable internet connection

#### **For Better Memory Performance**

- Use specific, descriptive language in conversations
- Reference previous topics by name for better context retrieval
- Keep related conversations in the same session when possible

## 🚀 Advanced Features

### Voice Customization

ZORA supports 8 different AI voices. Change the default in `app/config.py`:

```python
DEFAULT_VOICE = "Puck"  # Options: Puck, Charon, Kore, Fenrir, Aoede, Leda, Orus, Zephyr
```

### Custom Prompts

Modify the system behavior by editing `app/assistant/prompt.py`. The agent uses dynamic prompts that include current date/time and user context.

### Multi-User Deployment

For team deployment:

1. Set up user accounts for each team member
2. Each user gets isolated memory and credentials
3. Use environment-specific deployment with proper HTTPS
4. Consider hosting Zep Enterprise for enhanced privacy

### Development Mode

```bash
# Run with auto-reload for development
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001

# Run tests
python -m pytest tests/

# Check code formatting
black app/ tests/
```

## 🤝 Contributing

We welcome contributions! Here's how to get started:

### Development Setup

```bash
# Fork and clone the repository
git clone https://github.com/yourusername/ultimate-ai-assistant.git
cd ultimate-ai-assistant

# Create a development branch
git checkout -b feature/your-feature-name

# Install in development mode
uv sync --dev

# Make your changes and test thoroughly
# Submit a pull request with a clear description
```

### Areas for Contribution

- **Audio Processing**: Enhanced noise cancellation, voice activity detection
- **Memory System**: Better context retrieval, conversation summarization
- **Sub-Agents**: New integrations (Slack, Email, CRM systems)
- **UI/UX**: Better mobile support, accessibility improvements
- **Performance**: Optimization for large-scale deployments
- **Documentation**: Examples, tutorials, best practices

### Code Style

- Follow PEP 8 for Python code
- Use meaningful variable and function names
- Add docstrings for new functions and classes
- Include tests for new features

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Google ADK Team**: For the excellent Agent Development Kit
- **Zep.ai**: For the powerful memory service
- **MCP Server Authors**: For calendar and task management integrations
- **Open Source Community**: For the tools and libraries that make this possible

---

**Ready to experience the future of AI interaction?**

🎤 **Try the voice features** - click the microphone and have a natural conversation  
📅 **Connect your calendar** - let ZORA actually help with your schedule  
🧠 **Build memory** - watch ZORA learn and remember your preferences over time  

*ZORA isn't just another chatbot - it's your AI companion that actually gets things done.*
