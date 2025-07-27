# Ultimate AI Assistant

A powerful AI assistant built with Google ADK (Agent Development Kit) that provides web search, document processing, and image analysis capabilities through a live WebSocket interface with dynamic datetime context.

## ✨ Features

### 🔍 Web Search

- Integrated Google Search functionality for real-time information retrieval

### 📄 Document Processing

- **Unified Document Processing**: Single `process_document_tool` handles PDF, DOCX, and TXT files with automatic format detection
- **PDF Support**: Extract text and tables with OCR fallback for scanned documents
- **DOCX Support**: Extract text and tables from Microsoft Word documents  
- **TXT Support**: Multi-encoding text file processing with comprehensive statistics
- **Smart File Management**: Automatic file registration and cleanup with versioning

### 🖼️ Image Analysis

- **Native Vision Capabilities**: Leverages Gemini 2.0 Flash's built-in vision
- **Supported Formats**: JPG, JPEG, PNG, GIF, WebP, BMP, TIFF
- **Advanced Features**: Object detection, scene analysis, OCR, chart/graph analysis
- **No Additional Tools Required**: Direct image processing through model capabilities

### 🔄 Live Streaming Interface

- Real-time WebSocket communication with dynamic datetime context
- Audio and text input support with PCM audio streaming
- File upload with drag-and-drop interface
- Streaming responses with turn management and interruption handling
- **Deterministic Session IDs**: Consistent user sessions via USER_ID hash
- **Persistent Context**: Same user reconnects to same session automatically

### 🛠️ Tools Architecture

- **Unified Document Tool**: Single `process_document_tool` for all document types
- **Silent File Registration**: Automatic file discovery with `register_uploaded_files_tool`
- **File Inventory**: View available files with `list_available_user_files_tool`
- **Modular Design**: Clean separation of concerns with proper `__init__.py` exports
- **Enhanced Error Handling**: Structured logging and graceful failure recovery

### ⏰ Dynamic Context

- **Real-time Datetime**: Agent always knows the current date and time
- **Context Awareness**: Dynamic prompt generation with current temporal information

## 📁 Project Structure

```
ultimate-ai-assistant/
├── app/
│   ├── __main__.py               # Module entry point (python -m app)
│   ├── main.py                   # FastAPI server and WebSocket handling
│   ├── config.py                 # Centralized configuration settings
│   ├── assistant/
│   │   ├── __init__.py
│   │   ├── agent.py              # Main agent with dynamic datetime
│   │   ├── tools/
│   │   │   ├── __init__.py       # Unified tool exports
│   │   │   ├── document_tools.py # Unified document processing (refined)
│   │   │   └── file_tools.py     # File registration and listing
│   │   └── utils/
│   │       └── data_extractor.py # Core extraction functions
│   ├── static/                   # Frontend assets with dithered background
│   └── uploads/                  # Temporary file storage
├── tests/
│   └── test_data_extractor.py    # Test suite for data extraction
├── pyproject.toml                # UV project configuration
├── uv.lock                       # UV lockfile
├── .env                          # Environment variables
└── README.md                     # This file
```

## Installation

### Prerequisites

- Python 3.9 or higher
- uv package manager (recommended) or pip

### Quick Start with UV (Recommended)

1. **Clone the repository**:

   ```bash
   git clone <repository-url>
   cd ultimate-ai-assistant
   ```

2. **Install with UV**:

   ```bash
   # UV will automatically create venv and install dependencies
   uv sync
   ```

3. **Set up environment variables**:
   Create a `.env` file in the root directory:

   ```env
   GOOGLE_API_KEY=your_gemini_api_key_here
   ```

4. **Install system dependencies** (for OCR):
   - **macOS**: `brew install tesseract`
   - **Ubuntu**: `sudo apt-get install tesseract-ocr`
   - **Windows**: Download from [GitHub](https://github.com/UB-Mannheim/tesseract/wiki)

### Alternative Installation with Pip

1. **Clone and setup virtual environment**:

   ```bash
   git clone <repository-url>
   cd ultimate-ai-assistant
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Configuration

Before starting, review and modify `app/config.py` to customize:

- **APP_NAME**: Application identifier (default: "ZORA")
- **USER_ID**: Default user (affects session ID generation)
- **DEFAULT_HOST/PORT**: Server address settings
- **DEFAULT_VOICE**: Audio response voice selection

### Starting the Server

#### Method 1: Python Module (Development) - Uses config.py settings

```bash
# With UV (recommended)
uv run python -m app


```

#### Method 2: Standard FastAPI (Production) - Manual configuration

```bash
# With UV
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8001

```

The application will be available at:

- **Standard**: `http://localhost:8000`
- **Module mode**: `http://localhost:8001`

### Using the Interface

1. **Upload Files**: Drag and drop or select files (PDF, DOCX, TXT, images)
2. **Automatic Processing**: Files are silently registered and processed automatically
3. **Ask Questions**: Type questions about uploaded files or general queries
4. **Get Responses**: Receive streaming responses with document analysis and web search results
5. **File Management**: Use "What files do I have?" to see available documents

### Example Interactions

- **Document Analysis**: "Analyze the uploaded resume and summarize the key qualifications"
- **Image Description**: "Describe what you see in this image and extract any text"
- **Web Search**: "What are the latest developments in AI technology?"
- **Combined Query**: "Based on the uploaded report, search for recent news on this topic"
- **File Inventory**: "What files do I have available?" or "Show me my uploaded documents"
- **Multi-format**: "Process all my uploaded documents and create a summary"

## Agent Behavior

### File Handling Protocol

- **Silent Registration**: Files are automatically registered without user notification
- **Always Fresh**: File list is updated before every file operation
- **Smart Discovery**: Automatic detection and registration of newly uploaded files
- **Version Management**: New uploads of same filename create new artifact versions

### Dynamic Context

- **Current Time**: Agent always knows the exact current date and time
- **Contextual Responses**: Time-aware responses and scheduling capabilities
- **Fresh Information**: Web search results are always current

## Testing

### Running Tests

```bash
# With UV (recommended)
uv run python tests/test_data_extractor.py

# With standard Python
cd tests && python test_data_extractor.py
```

### Test Coverage

The test suite verifies:

- **PDF Processing**: Text and table extraction from various PDF types
- **DOCX Processing**: Content extraction from Word documents
- **File Handling**: Proper artifact registration and cleanup
- **Error Handling**: Graceful failure and recovery mechanisms
- **Multi-format Support**: Cross-format compatibility testing

### Validation

Test your installation:

```bash
# Check syntax validation
uv run python -m py_compile app/assistant/agent.py
uv run python -m py_compile app/assistant/tools/document_tools.py
uv run python -m py_compile app/assistant/tools/file_tools.py

# Test module import
uv run python -c "from app.assistant.tools import process_document_tool; print('✅ Tools imported successfully')"
```

## API Endpoints

### HTTP Endpoints

- `GET /` - Serve the main interface
- `POST /upload` - File upload endpoint
- `GET /static/*` - Static file serving

### WebSocket Endpoints

- `WS /ws/{session_id}?is_audio=false` - Main WebSocket connection for text
- `WS /ws/{session_id}?is_audio=true` - WebSocket connection with audio support

## Configuration

### Centralized Configuration

All application settings are centralized in `app/config.py`:

```python
# Application Configuration
APP_NAME = "ZORA"           # Agent application name
USER_ID = "NIHAAL"          # Default user identifier

# Server Configuration  
DEFAULT_HOST = "0.0.0.0"    # Server host address
DEFAULT_PORT = 8001         # Server port number

# Audio Configuration
DEFAULT_VOICE = "Puck"      # Voice for audio responses
```

### Session Management

- **Deterministic Session IDs**: Generated from SHA-256 hash of USER_ID
- **Consistent Sessions**: Same user always gets the same session ID
- **No Memory Service Dependency**: User sessions persist through deterministic IDs
- **Frontend Integration**: Client fetches USER_ID from `/config` endpoint

### Agent Configuration

The main agent is configured in `app/assistant/agent.py` with:

- **Model**: `gemini-2.0-flash-exp`
- **Tools**: Web search, document processing, file registration
- **Instructions**: Automatic file registration and processing guidance
- **Dynamic Context**: Real-time datetime injection

### File Processing

- **Temporary Storage**: Files uploaded to `/uploads` folder
- **Artifact Registration**: Files automatically registered and cleaned up
- **Version Control**: Same filename uploads create new artifact versions

## Architecture

### Core Components

1. **FastAPI Server** (`main.py`)
   - WebSocket handling for live communication with turn management
   - File upload and serving with original filename preservation
   - Session management with in-memory services
   - Audio/text streaming with PCM support

2. **ADK Agent** (`agent.py`)
   - Google ADK integration with Gemini 2.0 Flash
   - Dynamic datetime context injection
   - Tool orchestration with automatic file registration
   - Native vision capabilities for image analysis

3. **Unified Document Tools** (`document_tools.py`)
   - **Refined Architecture**: Object-oriented design with `DocumentProcessor` class
   - **Single Entry Point**: `process_document_tool` with automatic format detection
   - **Type Safety**: Full type hints and structured error handling
   - **Resource Management**: Automatic cleanup with context managers
   - **Enhanced Logging**: Structured logging with proper error context
   - **Modular Processing**: Separate methods for PDF, DOCX, and TXT processing
   - **Metadata Extraction**: Comprehensive document statistics and information

4. **File Management Tools** (`file_tools.py`)
   - **Silent Registration**: `register_uploaded_files_tool` for automatic file discovery
   - **Inventory Management**: `list_available_user_files_tool` for file listing
   - **Multi-format Support**: Handles documents and images with proper MIME types
   - **Version Control**: Automatic artifact versioning for duplicate filenames

5. **Data Extractor** (`data_extractor.py`)
   - Universal PDF extraction with pdfplumber and PyMuPDF fallback
   - DOCX processing with python-docx
   - OCR integration with pytesseract for scanned documents
   - Robust encoding detection for text files

6. **Module Entry Point** (`__main__.py`)
   - Alternative startup method with `python -m app`
   - Proper import string handling for uvicorn reload support
   - Development-friendly configuration

### Data Flow

1. **File Upload** → Temporary storage → Silent artifact registration → Automatic cleanup
2. **User Query** → Dynamic datetime injection → Agent processing → Tool execution → Streaming response
3. **Document Analysis** → Format detection → Content extraction → Structured response with metadata
4. **Image Analysis** → Native vision processing → Direct description generation (no separate tools)
5. **File Discovery** → Automatic scanning → Registration → Inventory update → User access

### Tool Workflow

```
User Interaction
    ↓
Register Uploaded Files (Silent)
    ↓
Process User Query
    ↓
Route to Appropriate Tool:
├── Document Processing → Auto-detect format → Extract content
├── Image Analysis → Native vision → Direct processing
└── Web Search → Real-time results → Formatted response
    ↓
Stream Response to User
```

## Dependencies

### Core Framework

- **google-adk**: Google Agent Development Kit for AI agent development
- **fastapi**: Modern web framework for building APIs
- **uvicorn**: ASGI server for production deployment

### Document Processing

- **pdfplumber**: Advanced PDF text and table extraction
- **PyMuPDF**: PDF rendering and OCR support
- **python-docx**: Microsoft Word document processing
- **pytesseract**: OCR text recognition for scanned documents

### Development & Management

- **uv**: Fast Python package installer and dependency manager
- **Pillow**: Image processing and manipulation
- **websockets**: WebSocket communication protocol
- **python-dotenv**: Environment variable management

### Optional Enhancements

- **tesseract**: System-level OCR engine (required for scanned PDFs)

## Recent Improvements

### v2.0 Updates

- ✅ **Unified Document Processing**: Single tool handles all document types
- ✅ **Silent File Management**: Automatic registration without user notification
- ✅ **Dynamic Datetime Context**: Real-time temporal awareness
- ✅ **Enhanced Error Handling**: Structured logging and graceful failures
- ✅ **Type Safety**: Complete type hints throughout codebase
- ✅ **Module Entry Point**: Support for `python -m app` execution
- ✅ **Improved Architecture**: Object-oriented design with proper separation
- ✅ **Native Vision**: Direct image processing without separate tools
- ✅ **Centralized Configuration**: All settings in `config.py` with consistent imports
- ✅ **Deterministic Sessions**: Hash-based session IDs for persistent user context

### Architecture Refinements

- **Reduced Tool Count**: From 5 tools to 3 essential tools
- **Better Import Structure**: Unified `__init__.py` exports
- **Enhanced Documentation**: Comprehensive function docstrings
- **Automatic Resource Management**: Context managers for cleanup
- **Configuration Management**: Single source of truth for all settings
- **Session Persistence**: Reliable user session continuity

## Development Guide

### Setup Instructions

1. Clone the repository:

```bash
git clone <repository-url>
cd ultimate-ai-assistant
```

2. Install dependencies with uv (recommended):

```bash
uv install
uv sync
```

3. Set up environment variables:

```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Run tests:

```bash
uv run python -m pytest
```

### Code Standards

- **Type Safety**: All functions must include type hints
- **Documentation**: Comprehensive docstrings for all public APIs
- **Error Handling**: Structured exceptions with logging
- **Testing**: Unit tests for new features and bug fixes

### Pull Request Process

1. Create feature branch from `main`
2. Implement changes with tests
3. Update documentation if needed
4. Submit PR with descriptive title and summary

## License Information

MIT License - see LICENSE file for details

## Getting Help

For questions or issues:

- 📧 Create an issue on GitHub
- 📝 Check existing documentation
- 🔍 Review test examples in `/tests`

---

*Built with ❤️ using Google ADK and modern Python practices*

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:

1. Check the test suite in `tests/test_data_extractor.py`
2. Review the agent configuration in `app/assistant/agent.py`
3. Check server logs for debugging information
