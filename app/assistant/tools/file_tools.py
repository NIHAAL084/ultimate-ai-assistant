from google.adk.tools import ToolContext
from google.genai import types
from pathlib import Path


async def register_uploaded_files(tool_context: ToolContext) -> dict:
    """
    Automatically scan uploads folder and register any new files as artifacts.
    
    Scans the uploads directory for new files and registers them as artifacts for 
    processing. Supports various file formats including documents (PDF, DOCX, TXT) 
    and images (JPG, PNG, GIF, WebP, BMP, TIFF). Files are automatically deleted 
    from uploads after successful registration.
    
    This tool should be run before any file operations to ensure all uploaded 
    files are available as artifacts for processing.

    Args:
        tool_context: The ToolContext for saving artifacts.

    Returns:
        A dictionary containing:
        - registered_files: List of file registration results
        - message: Status message if no files found
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


async def list_available_user_files(tool_context: ToolContext) -> str:
    """
    List all available artifacts/files that can be processed.
    
    Retrieves and displays a formatted list of all files that have been uploaded
    and registered as artifacts. This includes documents, images, and other files
    that are available for processing or analysis.
    
    IMPORTANT: Always run register_uploaded_files_tool first to ensure the 
    artifact list is up-to-date with any newly uploaded files.
    
    Args:
        tool_context: The ToolContext for accessing artifacts.
        
    Returns:
        A formatted string listing all available files, or a message indicating
        no files are available.
    """
    try:
        available_files = await tool_context.list_artifacts()
        if not available_files:
            return "You have no saved artifacts."
        else:
            # Format the list for the user/LLM
            file_list_str = "\n".join([f"- {fname}" for fname in available_files])
            return f"Here are your available artifacts:\n{file_list_str}"
    except ValueError as e:
        print(f"Error listing artifacts: {e}. Is ArtifactService configured?")
        return "Error: Could not list artifacts."
    except Exception as e:
        print(f"An unexpected error occurred during artifact list: {e}")
        return "Error: An unexpected error occurred while listing artifacts."

 
# Wrap functions into FunctionTools
from google.adk.tools import FunctionTool
register_uploaded_files_tool = FunctionTool(
    func=register_uploaded_files
)

list_available_user_files_tool = FunctionTool(
    func=list_available_user_files
)
