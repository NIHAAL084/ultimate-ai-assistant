# Ultimate AI Assistant

A powerful AI assistant built with Google ADK (Agent Development Kit) that provides web search, document processing, and image analysis capabilities through a live WebSocket interface.

## Features

### 🔍 Web Search

- Integrated Google Search functionality for real-time information retrieval

### 📄 Document Processing

- **PDF Processing**: Extract text and tables from PDFs with OCR support for scanned documents
- **DOCX Processing**: Extract text and tables from Microsoft Word documents
- **TXT Processing**: Read and process plain text files
- **Automatic File Registration**: Uploaded files are automatically registered as artifacts

### 🖼️ Image Analysis

- **Native Vision Capabilities**: Leverages Gemini's built-in vision for image analysis
- **Supported Formats**: JPG, JPEG, PNG, GIF, WebP, BMP
- **Features**: Object detection, scene analysis, text recognition (OCR), chart/graph analysis

### 🔄 Live Streaming Interface

- Real-time WebSocket communication
- Audio and text input support
- File upload with drag-and-drop
- Streaming responses

## Project Structure

```
ultimate-ai-assistant/
├── app/
│   ├── assistant/
│   │   ├── agent.py              # Main agent configuration
│   │   ├── tools/
│   │   │   ├── document_tools.py # PDF, DOCX, TXT processing tools
│   │   │   └── file_tools.py     # File registration and cleanup
│   │   └── utils/
│   │       └── data_extractor.py # Core extraction functions
│   ├── static/                   # Frontend assets
│   ├── uploads/                  # Temporary file storage
│   └── main.py                   # FastAPI server and WebSocket handling
├── tests/
│   └── test_data_extractor.py    # Test suite for data extraction
└── requirements.txt              # Python dependencies
```

## Installation

1. **Clone the repository**:

   ```bash
   git clone <repository-url>
   cd ultimate-ai-assistant
   ```

2. **Create virtual environment**:

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   Create a `.env` file in the root directory:

   ```env
   GOOGLE_API_KEY=your_gemini_api_key_here
   ```

5. **Install system dependencies** (for OCR):
   - **macOS**: `brew install tesseract`
   - **Ubuntu**: `sudo apt-get install tesseract-ocr`
   - **Windows**: Download from [GitHub](https://github.com/UB-Mannheim/tesseract/wiki)

## Usage

### Starting the Server

```bash
# Navigate to project directory
cd ultimate-ai-assistant

# Activate virtual environment
source .venv/bin/activate

# Start the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The application will be available at `http://localhost:8000`

### Using the Interface

1. **Upload Files**: Drag and drop or select files (PDF, DOCX, TXT, images)
2. **Ask Questions**: Type questions about uploaded files or general queries
3. **Get Responses**: Receive streaming responses with document analysis and web search results

### Example Interactions

- **Document Analysis**: "Analyze the uploaded resume and summarize the key qualifications"
- **Image Description**: "Describe what you see in this image"
- **Web Search**: "What are the latest developments in AI?"
- **Combined Query**: "Based on the uploaded report, search for recent news on this topic"

## Testing

Run the data extraction tests:

```bash
# Navigate to the tests directory
cd tests

# Run the test suite
python test_data_extractor.py
```

The test suite will verify:

- PDF text and table extraction
- DOCX content processing
- File handling and cleanup

## API Endpoints

### HTTP Endpoints

- `GET /` - Serve the main interface
- `POST /upload` - File upload endpoint
- `GET /static/*` - Static file serving

### WebSocket Endpoints

- `WS /ws/{session_id}?is_audio=false` - Main WebSocket connection for text
- `WS /ws/{session_id}?is_audio=true` - WebSocket connection with audio support

## Configuration

### Agent Configuration

The main agent is configured in `app/assistant/agent.py` with:

- **Model**: `gemini-2.0-flash-exp`
- **Tools**: Web search, document processing, file registration
- **Instructions**: Automatic file registration and processing guidance

### File Processing

- **Temporary Storage**: Files uploaded to `/uploads` folder
- **Artifact Registration**: Files automatically registered and cleaned up
- **Version Control**: Same filename uploads create new artifact versions

## Architecture

### Core Components

1. **FastAPI Server** (`main.py`)
   - WebSocket handling for live communication
   - File upload and serving
   - Session management

2. **ADK Agent** (`agent.py`)
   - Google ADK integration
   - Tool orchestration
   - Response generation

3. **Document Tools** (`document_tools.py`)
   - PDF processing with OCR fallback
   - DOCX text and table extraction
   - TXT file reading

4. **Data Extractor** (`data_extractor.py`)
   - Universal PDF extraction with pdfplumber and PyMuPDF
   - DOCX processing with python-docx
   - OCR integration with pytesseract

### Data Flow

1. **File Upload** → Temporary storage → Artifact registration → Cleanup
2. **User Query** → Agent processing → Tool execution → Response streaming
3. **Document Analysis** → Content extraction → Structured response
4. **Image Analysis** → Native vision processing → Description generation

## Dependencies

### Core Framework

- **google-adk**: Google Agent Development Kit
- **fastapi**: Web framework
- **uvicorn**: ASGI server

### Document Processing

- **pdfplumber**: PDF text and table extraction
- **PyMuPDF**: PDF rendering and OCR support
- **python-docx**: DOCX document processing
- **pytesseract**: OCR text recognition

### Additional

- **Pillow**: Image processing
- **websockets**: WebSocket communication
- **python-dotenv**: Environment variable management

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
