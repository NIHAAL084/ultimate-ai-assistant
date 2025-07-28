# Installation Guide

## Prerequisites

- Python 3.9 or higher
- uv package manager (recommended) or pip
- Node.js and npm (for MCP servers used by sub-agents)

## Quick Start with UV (Recommended)

### 1. Clone the repository

```bash
git clone <repository-url>
cd ultimate-ai-assistant
```

### 2. Install dependencies with UV

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install project dependencies
uv sync
```

### 3. Environment Setup

Copy the example environment file and configure your API keys:

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

- `GOOGLE_API_KEY`: Your Google AI API key
- `ZEP_API_KEY`: Your Zep memory service API key

### 4. User-Specific Environment (Optional)

If you need user-specific API tokens (for calendar/task management):

```bash
python manage_users.py setup
```

See [User Environment Guide](user-environment.md) for details.

### 5. Run the Application

```bash
uv run python -m app
# or
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Alternative Installation with pip

### 1. Create virtual environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Follow steps 3-5 from UV installation

## Docker Installation (Coming Soon)

Docker support will be added in a future release.

## Verification

Open your browser and navigate to:

- Main interface: <http://localhost:8000>
- Health check: <http://localhost:8000/health>

## Troubleshooting

### Common Issues

1. **Port already in use**: Change the port in the run command
2. **Missing API keys**: Ensure all required keys are set in `.env`
3. **Module not found**: Make sure you're in the correct directory and virtual environment is activated

### Getting Help

- Check the [Configuration Guide](configuration.md)
- Review [User Environment Guide](user-environment.md)
- See [API Documentation](api-reference.md)
