from google.adk.tools import ToolContext
from google.genai import types
from pathlib import Path

async def register_files(tool_context: ToolContext) -> dict:
    """
    Automatically scan the uploads folder and register any files as artifacts.
    Delete files after successful registration.
    When a file with the same name is uploaded, it creates a new version of the artifact.

    Args:
        tool_context: The ToolContext for saving artifacts.

    Returns:
        A dict summarizing saved files and any errors.
    """
    # Get the uploads directory path
    uploads_dir = Path(__file__).parent.parent.parent / "uploads"
    
    if not uploads_dir.exists():
        return {"registered_files": [], "message": "No uploads directory found"}
    
    # Scan for all files in uploads directory
    uploaded_files = list(uploads_dir.glob("*"))
    uploaded_files = [f for f in uploaded_files if f.is_file()]
    
    if not uploaded_files:
        return {"registered_files": [], "message": "No files found in uploads directory"}
    
    saved = []
    for file_path in uploaded_files:
        # Use original filename as artifact name
        filename = file_path.name
        entry = {"filename": filename}
        
        try:
            # Read file data
            with open(file_path, "rb") as f:
                data = f.read()
            
            # Determine MIME type based on file extension
            mime_type = "application/octet-stream"  # Default fallback
            suffix = file_path.suffix.lower()
            if suffix == '.pdf':
                mime_type = 'application/pdf'
            elif suffix in ['.doc', '.docx']:
                mime_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            elif suffix == '.txt':
                mime_type = 'text/plain'
            elif suffix in ['.jpg', '.jpeg']:
                mime_type = 'image/jpeg'
            elif suffix == '.png':
                mime_type = 'image/png'
            elif suffix == '.gif':
                mime_type = 'image/gif'
            elif suffix == '.webp':
                mime_type = 'image/webp'
            elif suffix == '.bmp':
                mime_type = 'image/bmp'
            elif suffix == '.tiff':
                mime_type = 'image/tiff'
            
            # Create artifact part
            artifact_part = types.Part.from_bytes(data=data, mime_type=mime_type)
            
            # Save as artifact - if same filename exists, this will create a new version
            version = await tool_context.save_artifact(filename, artifact_part)
            entry["version"] = version
            entry["status"] = "registered"
            
            # Delete the file after successful registration
            file_path.unlink()
            entry["cleanup"] = "deleted"
            
        except Exception as e:
            entry["error"] = str(e)
            entry["status"] = "failed"
        
        saved.append(entry)
    
    return {"registered_files": saved}
 
# Wrap register_files into a FunctionTool
from google.adk.tools import FunctionTool
register_files_tool = FunctionTool(
    func=register_files
)
