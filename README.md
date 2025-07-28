# Ultimate AI Assistant

A powerful AI assistant built with Google ADK (Agent Development Kit) that provides web search, document processing, image analysis, and specialized sub-agents through a live WebSocket interface with persistent memory.

## ✨ Key Features

- **🔍 Web Search**: Real-time Google Search integration
- **📄 Document Processing**: Unified PDF, DOCX, and TXT processing with OCR
- **🖼️ Image Analysis**: Native Gemini 2.0 Flash vision capabilities
- **🔄 Live Streaming**: Real-time WebSocket interface with audio support
- **🧠 Persistent Memory**: Zep-powered long-term conversation memory
- **🤖 Sub-Agents**: Specialized agents for Calendar and Task Management
- **⏰ Dynamic Context**: Always knows current date and time
- **👥 Multi-User Support**: User-specific environment configurations

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Node.js and npm (for sub-agents)
- API keys for Google AI and Zep Memory Service

### Installation

```bash
# Clone and setup
git clone <repository-url>
cd ultimate-ai-assistant

# Install with UV (recommended)
curl -LsSf https://astral.sh/uv/install.sh | sh
uv sync

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Run the application
uv run python -m app
```

Open [http://localhost:8000](http://localhost:8000) to start using the assistant.

## 📋 Core Capabilities

### Document Processing

Single tool handles all document types with automatic format detection, OCR fallback, and table extraction.

### Memory System

- **Cross-Session Memory**: Remembers conversations across browser sessions
- **Knowledge Graphs**: Builds semantic relationships between interactions
- **Smart Recall**: Retrieves relevant context from past conversations

### Sub-Agents

- **Calendar Agent**: Google Calendar management via MCP
- **Task Management**: Todoist integration for task and project management

### Streaming Interface

Real-time communication with turn management, interruption support, and audio streaming.

## 📚 Documentation

For detailed information, see the `documentation/` folder:

- **[Installation Guide](documentation/installation.md)**: Complete setup instructions
- **[Architecture Overview](documentation/architecture.md)**: System design and components
- **[Sub-Agents Guide](documentation/sub-agents.md)**: Calendar and task management agents
- **[User Environment](documentation/user-environment.md)**: Multi-user configuration system

## 🏗️ Project Structure

```
ultimate-ai-assistant/
├── app/
│   ├── main.py                   # FastAPI server and WebSocket handling
│   ├── config.py                 # Configuration settings
│   ├── user_env.py              # User environment management
│   └── assistant/
│       ├── agent.py             # Main agent with memory integration
│       ├── tools/               # Document and file processing tools
│       ├── sub_agents/          # Specialized external service agents
│       └── utils/               # Core utilities and memory service
├── documentation/               # Comprehensive documentation
├── environments/               # User-specific environment files
├── static/                     # Frontend interface
└── manage_users.py            # User environment management CLI
```

## 🔧 Configuration

### Environment Variables

Main `.env` file contains shared API keys:

- `GOOGLE_API_KEY`: Google AI API key
- `ZEP_API_KEY`: Zep memory service API key

User-specific configurations in `environments/.env.{username}`:

- `GOOGLE_OAUTH_CREDENTIALS`: Google Calendar OAuth
- `TODOIST_API_TOKEN`: Todoist API token

See [User Environment Guide](documentation/user-environment.md) for detailed setup.

## 🛠️ Development

Built with modern Python tooling:

- **UV Package Manager**: Fast dependency management
- **FastAPI**: High-performance async web framework
- **Google ADK**: Agent Development Kit for AI agents
- **Zep Memory**: Vector-based conversation memory
- **MCP Protocol**: Model Context Protocol for external integrations

## 📖 API Reference

- **Health Check**: `GET /health`
- **WebSocket**: `WS /ws` - Main chat interface
- **File Upload**: `POST /upload` - Document processing
- **Static Files**: `/` - Frontend interface

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

- Check the [documentation](documentation/) for detailed guides
- Review [architecture overview](documentation/architecture.md) for system understanding
- See [troubleshooting](documentation/installation.md#troubleshooting) for common issues
