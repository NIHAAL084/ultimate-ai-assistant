
# ZORA - Ultimate AI Assistant 🤖

**ZORA** is a sophisticated multi-modal AI assistant powered by Google's latest Gemini 2.0 Flash model and Agent Development Kit (ADK). It combines the conversational abilities of ChatGPT with advanced voice interaction, persistent memory, and real-world integrations for calendar and task management.

## 🎯 What Makes ZORA Different

Unlike simple chatbots, ZORA is designed as a **complete AI companion** that:

- **Remembers everything** across conversations using advanced knowledge graphs
- **Speaks and listens** with real-time voice interaction
- **Actually helps** with your calendar, tasks, and documents
- **Switches modes seamlessly** between text and voice without interruption
- **Supports multiple users** with isolated environments and credentials

---

## 🛠️ Why MCP Servers Had To Be Modified

### Google Calendar MCP (`@nihaal084/google-calendar-mcp`)

The original Google Calendar MCP server did **not** support user-specific token file paths. This meant that all users would share the same token file, making true multi-user support impossible and creating security risks. The modified version adds support for the `GOOGLE_CALENDAR_MCP_TOKEN_PATH` environment variable, so each user's tokens are stored in their own file (e.g., `calendar_credentials/credentials_{user_id}.json`).

### Todoist MCP (`@nihaal084/todoist-mcp-server`)

The original Todoist MCP server was **not fully compatible with Google ADK** due to stricter input/output validation requirements. For example, it used integers (e.g., `priority: 4`) where ADK expects strings (e.g., `priority: "4"`). This mismatch caused runtime errors under ADK’s strict schema enforcement.

The updated server addresses these issues and improves overall robustness with:

- **ADK-compatible schema formatting**  
  Converts integer fields (e.g., `priority`) to strings to satisfy ADK’s validation.
- **Improved error handling and logging**  
  Captures and surfaces errors in a structured way for easier debugging.

---

## ✨ Core Capabilities

### 💬 **Intelligent Conversation**

- **Gemini 2.0 Flash Model**: Google AI with superior reasoning and multimodal understanding
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
- **`gmail_tool`**: AgentTool wrapper around Gmail Agent (connects to Gmail MCP server)

#### **Tool Orchestration**

The primary agent intelligently decides which tools to use based on user requests:

- **Memory queries** → `load_memory` tool automatically searches past conversations
- **Calendar requests** → `calendar_tool` agent handles Google Calendar operations
- **Task management** → `task_management_tool` agent handles Todoist operations
- **Email management** → `gmail_tool` agent handles Gmail operations
- **Document questions** → `process_document_tool` analyzes uploaded files
- **Current information** → `google_search` provides real-time web results

### 🤖 **Specialized Agents**

ZORA implements an **Agent-as-Tool** architecture where specialized sub-agents are integrated as tools within the primary agent. Each sub-agent connects to dedicated MCP (Model Context Protocol) servers for external service integration:

#### **Calendar Agent** (Google Calendar)

- **MCP Server**: `@nihaal084/google-calendar-mcp` - Custom Google Calendar MCP server with user-specific token path support
- **Agent-as-Tool Integration**: Wrapped as an `AgentTool` and included in the primary agent's toolset
- **User-Specific Configuration**: Each user's OAuth credentials and tokens stored in isolated `calendar_credentials/` folder
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

#### **Gmail Agent** (Gmail)

- **MCP Server**: `@gongrzhe/server-gmail-autoauth-mcp` - Advanced Gmail MCP server with auto-authentication
- **Agent-as-Tool Integration**: Wrapped as specialized email management tool within primary agent
- **User-Specific Configuration**: Uses Google OAuth credentials (same as Calendar agent)
- **Capabilities**:
  - **Email Management**: Send, draft, read, search, and delete emails
  - **Attachment Support**: Send and download file attachments with proper handling
  - **Advanced Search**: Gmail search syntax with filters (sender, date, keywords, attachments)
  - **Label Management**: Create, update, delete labels; organize emails efficiently
  - **Batch Operations**: Process multiple emails simultaneously for efficiency
  - **Format Support**: Plain text, HTML, and multipart emails
  - **Natural Language**: *"Send John the project report with budget spreadsheet attached"*

#### **Technical Implementation**

```python
# Primary agent creates sub-agents as tools
calendar_agent = create_calendar_agent(user_id=user_id)
calendar_tool = AgentTool(agent=calendar_agent)

task_management_agent = create_task_management_agent(user_id=user_id)  
task_management_tool = AgentTool(agent=task_management_agent)

gmail_agent = create_gmail_agent(user_id=user_id)
gmail_tool = AgentTool(agent=gmail_agent)

# Sub-agents included in primary agent's toolset
return Agent(
    name="assistant",
    tools=[
        google_search,
        load_memory,
        process_document_tool,
        calendar_tool,        # Calendar agent as tool
        task_management_tool, # Task agent as tool
        gmail_tool           # Gmail agent as tool
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

#### **Email Management**

```conversation
You: "Send an email to sarah@company.com about the project deadline extension"
ZORA: "I'll help you send that email. What would you like to say about the deadline extension?"

You: "Tell her we need 2 more weeks due to additional requirements"
ZORA: "Email sent to sarah@company.com with subject 'Project Deadline Extension Request' 
      explaining the need for 2 additional weeks due to new requirements."

You: "Check if I have any emails about the quarterly budget from last week"
ZORA: "I found 3 emails about the quarterly budget from last week. The most recent 
      is from your manager with the final budget approval and a spreadsheet attachment."
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

## 🛠️ Advanced Setup: Calendar, Tasks & Email

For full productivity features, set up ZORA to manage your actual calendar, tasks, and email:

### Prerequisites for Advanced Features

```bash
# Install Node.js MCP servers (one-time setup)
npm install -g @nihaal084/google-calendar-mcp
npm install -g @nihaal084/todoist-mcp-server
npm install -g @gongrzhe/server-gmail-autoauth-mcp

# Note: If you get permission errors, you may need to use sudo:
# sudo npm install -g @gongrzhe/server-gmail-autoauth-mcp
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

4. **Set Up Gmail** (Uses same Google OAuth as Calendar):
   - Gmail integration automatically uses your Google OAuth credentials
   - Enable Gmail API in your Google Cloud Console (same project as Calendar)
   - First Gmail authentication will be handled automatically by the MCP server

5. **Register with ZORA**:
   - On ZORA's homepage, click "Register New User"
   - Enter a username (letters, numbers, hyphens only)
   - Upload your Google OAuth JSON file (enables both Calendar and Gmail)
   - Enter your Todoist API token
   - Click "Register"

### Advanced Voice Commands (After Setup)

```voice
# Calendar Commands
"What's on my calendar tomorrow?"
"Schedule a team meeting for Friday at 2 PM"
"Move my 3 PM meeting to 4 PM"

# Task Management Commands
"Add a high-priority task to review the quarterly report"
"Show me all tasks due this week"
"Mark the grocery shopping task as complete"

# Email Commands
"Send an email to john@company.com about the project update"
"Read my latest emails from my manager"
"Search for emails about the quarterly budget from last week"
"Send the project report to the team with the budget spreadsheet attached"
"Check if I have any unread emails with attachments"
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
├── AgentTool(task_agent)         # Task sub-agent as tool
└── AgentTool(gmail_agent)        # Gmail sub-agent as tool

# Sub-Agent MCP Connections
Calendar Agent → MCPToolset → @cocal/google-calendar-mcp server
Task Agent → MCPToolset → @nihaal084/todoist-mcp-server
Gmail Agent → MCPToolset → @gongrzhe/server-gmail-autoauth-mcp server
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

# Gmail Agent MCP Configuration
MCPToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command="uv",
            args=["run", "npx", "@gongrzhe/server-gmail-autoauth-mcp"],
            env={
                "GMAIL_OAUTH_PATH": user_oauth_path,
                "GMAIL_CREDENTIALS_PATH": user_credentials_path
            },
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
├── app/                           # Python backend application
│   ├── __init__.py                # Marks app as a Python package
│   ├── __main__.py                # Run app as a module (python -m app)
│   ├── main.py                    # FastAPI server, API endpoints, WebSocket
│   ├── config.py                  # App/server/voice configuration constants
│   ├── user_env.py                # User-specific environment and credential management
│   ├── static/                    # Frontend (HTML/JS/CSS)
│   │   ├── index.html             # Main web UI for ZORA
│   │   └── js/                    # Frontend JavaScript modules
│   │       ├── app.js                     # Main UI logic, WebSocket, state
│   │       ├── audio-player.js            # Audio playback (browser AudioWorklet)
│   │       ├── audio-recorder.js          # Microphone capture (browser AudioWorklet)
│   │       ├── dither-background.js       # Animated background visual effect
│   │       ├── pcm-player-processor.js    # AudioWorklet: PCM audio playback processor
│   │       └── pcm-recorder-processor.js  # AudioWorklet: PCM audio recording processor
│   ├── uploads/                   # Temporary file upload storage (usually empty)
│   └── assistant/                 # Core AI agent system and tools
│       ├── __init__.py            # Marks assistant as a Python package
│       ├── agent.py               # Main agent creation, prompt, sub-agent wiring
│       ├── prompt.py              # System prompt and instructions for the agent
│       ├── tools/                 # Custom agent tools
│       │   ├── __init__.py
│       │   ├── document_tools.py          # Unified PDF/DOCX/TXT/image processing, OCR
│       │   └── file_tools.py              # File upload/registration utilities
│       ├── sub_agents/            # Specialized sub-agents for external services
│       │   ├── __init__.py
│       │   ├── calendar_agent/            # Google Calendar agent (MCP integration)
│       │   │   ├── __init__.py
│       │   │   ├── agent.py               # Calendar agent logic
│       │   │   └── prompt.py              # Calendar agent prompt
│       │   ├── gmail_agent/               # Gmail agent (MCP integration)
│       │   │   ├── __init__.py
│       │   │   ├── agent.py               # Gmail agent logic
│       │   │   └── prompt.py              # Gmail agent prompt
│       │   └── task_management_agent/     # Todoist agent (MCP integration)
│       │       ├── __init__.py
│       │       ├── agent.py               # Todoist agent logic
│       │       └── prompt.py              # Todoist agent prompt
│       └── utils/                 # Utility modules for memory, extraction, etc.
│           ├── data_extractor.py           # PDF/image/docx data extraction (OCR, parsing)
│           ├── session_memory_manager.py   # Session-to-memory (Zep) management
│           └── zep_memory_service.py       # Zep memory service integration
├── user_data/                     # User-specific environment and credentials
│   ├── .env.{username}            # Per-user environment variables (API keys, tokens)
│   ├── .env.template              # Template for new user env files
│   ├── credentials/               # Google OAuth credentials (per user)
│   │   └── credentials_{username}.json
│   ├── gmail_credentials/         # Gmail OAuth tokens (per user)
│   │   └── credentials_{username}.json
│   └── calendar_credentials/      # Calendar OAuth tokens (per user)
│       └── credentials_{username}.json
├── tests/                         # Python test suite
│   └── test_data_extractor.py     # Tests for data extraction utilities
├── manage_users.py                # CLI for user environment setup/validation
├── pyproject.toml                 # Python dependencies and project metadata
├── uv.lock                        # Locked dependency versions for UV
├── .env.example                   # Example environment file
├── .python-version                # Python version requirement
├── screenshots/                   # (Empty) For UI screenshots
└── README.md                      # Project documentation
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
| `/setup-gmail-auth` | POST | Set up Gmail authentication for existing user |
| `/setup-calendar-auth` | POST | Set up Calendar authentication for existing user |
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
├── .env.johndoe                     # User's API tokens and environment
├── .env.alice                       # Another user's environment
├── .env.template                    # Template for new users
├── credentials/                     # OAuth credentials files
│   ├── gcp-oauth.keys.json         # Google OAuth credentials
│   └── credentials_johndoe.json    # User-specific copies
├── gmail_credentials/               # User-specific Gmail tokens
│   ├── credentials_johndoe.json    # Gmail authentication tokens
│   └── credentials_alice.json      # Another user's Gmail tokens
└── calendar_credentials/            # User-specific Calendar tokens
    ├── credentials_johndoe.json    # Calendar authentication tokens
    └── credentials_alice.json      # Another user's Calendar tokens
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
- **MCP servers**: Install Node.js packages globally: `npm install -g @nihaal084/google-calendar-mcp @nihaal084/todoist-mcp-server`
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
# Install with development dependencies
uv sync --extra dev

# Run with auto-reload for development
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8001

# Run tests with coverage
uv run pytest

# Check code formatting
uv run black app/ tests/

# Sort imports
uv run isort app/ tests/

# Type checking
uv run mypy app/

# Run all quality checks
uv run pre-commit run --all-files
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

# Install in development mode with dev dependencies
uv sync --extra dev

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
  - `@nihaal084/google-calendar-mcp`: Custom fork with user-specific token path support
  - `@nihaal084/todoist-mcp-server`: Custom Gemini-compatible Todoist integration
  - `@gongrzhe/server-gmail-autoauth-mcp`: Gmail MCP server with auto-authentication
- **Open Source Community**: For the tools and libraries that make this possible

---

**Ready to experience the future of AI interaction?**

🎤 **Try the voice features** - click the microphone and have a natural conversation  
📅 **Connect your calendar** - let ZORA actually help with your schedule  
🧠 **Build memory** - watch ZORA learn and remember your preferences over time  

*ZORA isn't just another chatbot - it's your AI companion that actually gets things done.*
