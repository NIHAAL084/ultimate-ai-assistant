"""
Entry point for running the app as a module: python -m app
"""

import uvicorn
from .config import DEFAULT_HOST, DEFAULT_PORT

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app", 
        host=DEFAULT_HOST, 
        port=DEFAULT_PORT, 
        reload=True
    )
