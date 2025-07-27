"""
Document processing tools for the AI assistant
"""

from google.adk.tools import FunctionTool
from google.adk.tools.tool_context import ToolContext
from pathlib import Path
import os
from typing import Dict, Any

from ..utils.data_extractor import extract_universal_pdf_data, extract_docx_data


async def process_pdf_function(filename: str, tool_context: ToolContext) -> dict:
    """
    Process a PDF file and extract its content and tables.
    
    Args:
        filename: The name of the PDF file to process
        tool_context: The tool context for accessing artifacts
    
    Returns:
        Dictionary containing the extracted content or error information
    """
    print(f"[PDF TOOL] === PDF PROCESSING START ===")
    print(f"[PDF TOOL] Requested filename: {filename}")
    
    try:
        # Debug: Check session state
        has_files = tool_context.state.get("has_uploaded_files", False)
        file_names = tool_context.state.get("uploaded_file_names", [])
        
        print(f"[PDF TOOL] Session state:")
        print(f"  - has_uploaded_files: {has_files}")
        print(f"  - uploaded_file_names: {file_names}")
        
        # List all available artifacts
        try:
            available_artifacts = await tool_context.list_artifacts()
            print(f"[PDF TOOL] Available artifacts: {available_artifacts}")
        except Exception as e:
            print(f"[PDF TOOL] Error listing artifacts: {e}")
            available_artifacts = []
        
        # Try to find the artifact by exact filename match first
        artifact = None
        artifact_filename = None
        
        # Try exact match
        if filename in available_artifacts:
            artifact_filename = filename
        # Try to find by pattern (uploaded_document_*.pdf)
        elif not artifact_filename:
            for artifact_name in available_artifacts:
                if artifact_name.endswith('.pdf'):
                    print(f"[PDF TOOL] Found PDF artifact: {artifact_name}")
                    artifact_filename = artifact_name
                    break
        # Try to find by user's original filename (case-insensitive)
        elif not artifact_filename:
            filename_lower = filename.lower()
            for artifact_name in available_artifacts:
                if filename_lower in artifact_name.lower() and artifact_name.endswith('.pdf'):
                    print(f"[PDF TOOL] Found PDF artifact by partial match: {artifact_name}")
                    artifact_filename = artifact_name
                    break
        
        if not artifact_filename:
            return {
                "error": f"PDF file '{filename}' not found. Available artifacts: {available_artifacts}"
            }
        
        print(f"[PDF TOOL] Using artifact: {artifact_filename}")
        
        # Try to load the artifact
        try:
            artifact = await tool_context.load_artifact(artifact_filename)
            print(f"[PDF TOOL] Artifact loaded successfully")
            print(f"  - Has inline_data: {artifact.inline_data is not None if artifact else False}")
            print(f"  - Has text: {artifact.text is not None if artifact else False}")
        except Exception as e:
            print(f"[PDF TOOL] Failed to load artifact: {e}")
            return {
                "error": f"Could not load artifact '{artifact_filename}': {str(e)}"
            }
        
        if not artifact:
            return {
                "error": f"Artifact '{artifact_filename}' is None"
            }
        
        # Handle different artifact types
        file_path = None
        temp_file_path = None
        
        if artifact.inline_data and artifact.inline_data.data:
            # Binary data - save to temporary file for processing
            print(f"[PDF TOOL] Processing binary data ({len(artifact.inline_data.data)} bytes)")
            import tempfile
            import os
            
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                temp_file.write(artifact.inline_data.data)
                temp_file_path = temp_file.name
                file_path = temp_file_path
                
        elif artifact.text:
            # File path reference
            file_path = artifact.text
            print(f"[PDF TOOL] Using file path: {file_path}")
        else:
            return {
                "error": f"Artifact '{artifact_filename}' contains no usable data"
            }
        
        # Check if the file exists
        if not os.path.exists(file_path):
            return {"error": f"PDF file does not exist at path: {file_path}"}
        
        print(f"[PDF TOOL] Processing PDF from: {file_path}")
        
        # Process the PDF file
        pdf_data = extract_universal_pdf_data(file_path)
        print(f"[PDF TOOL] Extracted {len(pdf_data)} pages")
        
        # Clean up temporary file if created
        if temp_file_path:
            try:
                os.unlink(temp_file_path)
                print(f"[PDF TOOL] Cleaned up temporary file")
            except Exception as e:
                print(f"[PDF TOOL] Warning: Could not delete temp file: {e}")
        
        # Format the response
        result = {
            "filename": filename,
            "artifact_name": artifact_filename,
            "status": "success",
            "total_pages": len(pdf_data),
            "content": []
        }
        
        for page_data in pdf_data:
            page_info = {
                "page_number": page_data["page_number"],
                "text": page_data["text"],
                "char_count": len(page_data["text"]),
                "tables_count": len(page_data["tables"]),
                "tables": page_data["tables"]
            }
            result["content"].append(page_info)
        
        print(f"[PDF TOOL] === PDF PROCESSING END (SUCCESS) ===")
        return result
        
    except Exception as e:
        print(f"[PDF TOOL ERROR] Exception: {e}")
        import traceback
        print(f"[PDF TOOL ERROR] Traceback: {traceback.format_exc()}")
        return {"error": f"Failed to process PDF file '{filename}': {str(e)}"}


async def process_docx_function(filename: str, tool_context: ToolContext) -> dict:
    """
    Process a DOCX file and extract its content and tables.
    
    Args:
        filename: The name of the DOCX file to process
        tool_context: The tool context for accessing artifacts
    
    Returns:
        Dictionary containing the extracted content or error information
    """
    print(f"[DOCX TOOL] === DOCX PROCESSING START ===")
    print(f"[DOCX TOOL] Requested filename: {filename}")
    
    try:
        # Debug: Check session state
        has_files = tool_context.state.get("has_uploaded_files", False)
        file_names = tool_context.state.get("uploaded_file_names", [])
        
        print(f"[DOCX TOOL] Session state:")
        print(f"  - has_uploaded_files: {has_files}")
        print(f"  - uploaded_file_names: {file_names}")
        
        # List all available artifacts
        try:
            available_artifacts = await tool_context.list_artifacts()
            print(f"[DOCX TOOL] Available artifacts: {available_artifacts}")
        except Exception as e:
            print(f"[DOCX TOOL] Error listing artifacts: {e}")
            available_artifacts = []
        
        # Try to find the artifact by exact filename match first
        artifact = None
        artifact_filename = None
        
        # Try exact match
        if filename in available_artifacts:
            artifact_filename = filename
        # Try to find by pattern (uploaded_document_*.docx)
        elif not artifact_filename:
            for artifact_name in available_artifacts:
                if artifact_name.endswith('.docx'):
                    print(f"[DOCX TOOL] Found DOCX artifact: {artifact_name}")
                    artifact_filename = artifact_name
                    break
        
        if not artifact_filename:
            return {
                "error": f"DOCX file '{filename}' not found. Available artifacts: {available_artifacts}"
            }
        
        print(f"[DOCX TOOL] Using artifact: {artifact_filename}")
        
        # Try to load the artifact
        try:
            artifact = await tool_context.load_artifact(artifact_filename)
            print(f"[DOCX TOOL] Artifact loaded successfully")
            print(f"  - Has inline_data: {artifact.inline_data is not None if artifact else False}")
            print(f"  - Has text: {artifact.text is not None if artifact else False}")
        except Exception as e:
            print(f"[DOCX TOOL] Failed to load artifact: {e}")
            return {
                "error": f"Could not load artifact '{artifact_filename}': {str(e)}"
            }
        
        if not artifact:
            return {
                "error": f"Artifact '{artifact_filename}' is None"
            }
        
        # Handle different artifact types
        file_path = None
        temp_file_path = None
        
        if artifact.inline_data and artifact.inline_data.data:
            # Binary data - save to temporary file for processing
            print(f"[DOCX TOOL] Processing binary data ({len(artifact.inline_data.data)} bytes)")
            import tempfile
            
            with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as temp_file:
                temp_file.write(artifact.inline_data.data)
                temp_file_path = temp_file.name
                file_path = temp_file_path
                
        elif artifact.text:
            # File path reference
            file_path = artifact.text
            print(f"[DOCX TOOL] Using file path: {file_path}")
        else:
            return {
                "error": f"Artifact '{artifact_filename}' contains no usable data"
            }
        
        # Check if the file exists
        if not os.path.exists(file_path):
            return {"error": f"DOCX file does not exist at path: {file_path}"}
        
        print(f"[DOCX TOOL] Processing DOCX from: {file_path}")
        
        # Process the DOCX file
        docx_data = extract_docx_data(file_path)
        print(f"[DOCX TOOL] Extracted content with {len(docx_data.get('text', ''))} characters and {len(docx_data.get('tables', []))} tables")
        
        # Clean up temporary file if created
        if temp_file_path:
            try:
                os.unlink(temp_file_path)
                print(f"[DOCX TOOL] Cleaned up temporary file")
            except Exception as e:
                print(f"[DOCX TOOL] Warning: Could not delete temp file: {e}")
        
        # Format the response
        result = {
            "filename": filename,
            "artifact_name": artifact_filename,
            "status": "success",
            "content": docx_data["text"],  # Use "text" key from extract_docx_data
            "char_count": len(docx_data["text"]),
            "tables_count": len(docx_data["tables"]),
            "tables": docx_data["tables"]
        }
        
        print(f"[DOCX TOOL] === DOCX PROCESSING END (SUCCESS) ===")
        return result
        
    except Exception as e:
        print(f"[DOCX TOOL ERROR] Exception: {e}")
        import traceback
        print(f"[DOCX TOOL ERROR] Traceback: {traceback.format_exc()}")
        return {"error": f"Failed to process DOCX file '{filename}': {str(e)}"}


async def process_txt_function(filename: str, tool_context: ToolContext) -> dict:
    """
    Process a TXT file and extract its content.
    
    Args:
        filename: The name of the TXT file to process
        tool_context: The tool context for accessing artifacts
    
    Returns:
        Dictionary containing the extracted content or error information
    """
    print(f"[TXT TOOL] === TXT PROCESSING START ===")
    print(f"[TXT TOOL] Requested filename: {filename}")
    
    try:
        # Debug: Check session state
        has_files = tool_context.state.get("has_uploaded_files", False)
        file_names = tool_context.state.get("uploaded_file_names", [])
        
        print(f"[TXT TOOL] Session state:")
        print(f"  - has_uploaded_files: {has_files}")
        print(f"  - uploaded_file_names: {file_names}")
        
        # List all available artifacts
        try:
            available_artifacts = await tool_context.list_artifacts()
            print(f"[TXT TOOL] Available artifacts: {available_artifacts}")
        except Exception as e:
            print(f"[TXT TOOL] Error listing artifacts: {e}")
            available_artifacts = []
        
        # Try to find the artifact by exact filename match first
        artifact = None
        artifact_filename = None
        
        # Try exact match
        if filename in available_artifacts:
            artifact_filename = filename
        # Try to find by pattern (uploaded_document_*.txt)
        elif not artifact_filename:
            for artifact_name in available_artifacts:
                if artifact_name.endswith('.txt'):
                    print(f"[TXT TOOL] Found TXT artifact: {artifact_name}")
                    artifact_filename = artifact_name
                    break
        
        if not artifact_filename:
            return {
                "error": f"TXT file '{filename}' not found. Available artifacts: {available_artifacts}"
            }
        
        print(f"[TXT TOOL] Using artifact: {artifact_filename}")
        
        # Try to load the artifact
        try:
            artifact = await tool_context.load_artifact(artifact_filename)
            print(f"[TXT TOOL] Artifact loaded successfully")
            print(f"  - Has inline_data: {artifact.inline_data is not None if artifact else False}")
            print(f"  - Has text: {artifact.text is not None if artifact else False}")
        except Exception as e:
            print(f"[TXT TOOL] Failed to load artifact: {e}")
            return {
                "error": f"Could not load artifact '{artifact_filename}': {str(e)}"
            }
        
        if not artifact:
            return {
                "error": f"Artifact '{artifact_filename}' is None"
            }
        
        # Handle different artifact types
        content = None
        
        if artifact.inline_data and artifact.inline_data.data:
            # Binary data - decode as text
            print(f"[TXT TOOL] Processing binary data ({len(artifact.inline_data.data)} bytes)")
            try:
                content = artifact.inline_data.data.decode('utf-8')
                print(f"[TXT TOOL] Successfully decoded binary data to text")
            except UnicodeDecodeError:
                try:
                    content = artifact.inline_data.data.decode('latin-1')
                    print(f"[TXT TOOL] Decoded binary data using latin-1")
                except Exception as e:
                    return {
                        "error": f"Could not decode text content: {str(e)}"
                    }
                    
        elif artifact.text:
            # Check if it's a file path or direct text content
            if os.path.exists(artifact.text):
                # File path reference
                file_path = artifact.text
                print(f"[TXT TOOL] Using file path: {file_path}")
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    print(f"[TXT TOOL] Read {len(content)} characters from file")
                except UnicodeDecodeError:
                    try:
                        with open(file_path, 'r', encoding='latin-1') as f:
                            content = f.read()
                        print(f"[TXT TOOL] Read {len(content)} characters from file using latin-1")
                    except Exception as e:
                        return {
                            "error": f"Could not read file '{file_path}': {str(e)}"
                        }
            else:
                # Direct text content
                content = artifact.text
                print(f"[TXT TOOL] Using direct text content ({len(content)} characters)")
        else:
            return {
                "error": f"Artifact '{artifact_filename}' contains no usable data"
            }
        
        if content is None:
            return {
                "error": f"Could not extract content from artifact '{artifact_filename}'"
            }
        
        print(f"[TXT TOOL] Extracted content with {len(content)} characters")
        
        # Format the response
        result = {
            "filename": filename,
            "artifact_name": artifact_filename,
            "status": "success",
            "content": content,
            "char_count": len(content),
            "line_count": len(content.split('\n')) if content else 0
        }
        
        print(f"[TXT TOOL] === TXT PROCESSING END (SUCCESS) ===")
        return result
        
    except Exception as e:
        print(f"[TXT TOOL ERROR] Exception: {e}")
        import traceback
        print(f"[TXT TOOL ERROR] Traceback: {traceback.format_exc()}")
        return {"error": f"Failed to process TXT file '{filename}': {str(e)}"}


# Create FunctionTool instances
process_pdf_tool = FunctionTool(func=process_pdf_function)
process_docx_tool = FunctionTool(func=process_docx_function)
process_txt_tool = FunctionTool(func=process_txt_function)
