"""
Refined document processing tools for the AI assistant

This module provides unified document processing capabilities with improved
error handling, type safety, and modular design.
"""

import os
import tempfile
import traceback
from enum import Enum
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import logging

from google.adk.tools import FunctionTool
from google.adk.tools.tool_context import ToolContext

from ..utils.data_extractor import extract_universal_pdf_data, extract_docx_data


# Configure logging
logger = logging.getLogger(__name__)


class DocumentType(Enum):
    """Supported document types"""
    PDF = "pdf"
    DOCX = "docx"
    DOC = "doc"
    TXT = "txt"


class ProcessingResult:
    """Structured result for document processing"""
    
    def __init__(self, filename: str, artifact_name: str):
        self.filename = filename
        self.artifact_name = artifact_name
        self.status = "pending"
        self.error: Optional[str] = None
        self.content: List[Dict[str, Any]] = []
        self.metadata: Dict[str, Any] = {}
    
    def set_success(self, content: List[Dict[str, Any]], metadata: Optional[Dict[str, Any]] = None):
        """Mark processing as successful"""
        self.status = "success"
        self.content = content
        self.metadata = metadata or {}
    
    def set_error(self, error: str):
        """Mark processing as failed"""
        self.status = "error"
        self.error = error
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format"""
        result = {
            "filename": self.filename,
            "artifact_name": self.artifact_name,
            "status": self.status
        }
        
        if self.error:
            result["error"] = self.error
        else:
            result["content"] = self.content
            result.update(self.metadata)
        
        return result


class DocumentProcessor:
    """Base class for document processing with common functionality"""
    
    SUPPORTED_EXTENSIONS = {
        DocumentType.PDF: [".pdf"],
        DocumentType.DOCX: [".docx", ".doc"],
        DocumentType.TXT: [".txt"]
    }
    
    def __init__(self, tool_context: ToolContext):
        self.tool_context = tool_context
        self.temp_files: List[str] = []
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cleanup temporary files"""
        await self.cleanup()
    
    async def cleanup(self):
        """Clean up any temporary files created during processing"""
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
                    logger.debug(f"Cleaned up temporary file: {temp_file}")
            except Exception as e:
                logger.warning(f"Could not delete temp file {temp_file}: {e}")
        self.temp_files.clear()
    
    @staticmethod
    def detect_document_type(filename: str) -> Optional[DocumentType]:
        """Detect document type from filename extension"""
        if not filename or '.' not in filename:
            return None
        
        extension = f".{filename.lower().split('.')[-1]}"
        
        for doc_type, extensions in DocumentProcessor.SUPPORTED_EXTENSIONS.items():
            if extension in extensions:
                return doc_type
        
        return None
    
    @staticmethod
    def get_supported_extensions() -> List[str]:
        """Get list of all supported file extensions"""
        extensions = []
        for ext_list in DocumentProcessor.SUPPORTED_EXTENSIONS.values():
            extensions.extend(ext_list)
        return extensions
    
    async def find_artifact(self, filename: str) -> Tuple[Optional[Any], Optional[str]]:
        """
        Find artifact by filename with fallback matching
        
        Returns:
            Tuple of (artifact, artifact_name) or (None, None) if not found
        """
        logger.debug(f"Searching for artifact: {filename}")
        
        try:
            available_artifacts = await self.tool_context.list_artifacts()
            logger.debug(f"Available artifacts: {available_artifacts}")
        except Exception as e:
            logger.error(f"Error listing artifacts: {e}")
            return None, None
        
        # Try exact match first
        if filename in available_artifacts:
            try:
                artifact = await self.tool_context.load_artifact(filename)
                logger.debug(f"Found exact match: {filename}")
                return artifact, filename
            except Exception as e:
                logger.error(f"Error loading artifact '{filename}': {e}")
        
        # Try partial matches
        matching_artifacts = [
            name for name in available_artifacts 
            if filename.lower() in name.lower() or name.lower() in filename.lower()
        ]
        
        for artifact_name in matching_artifacts:
            try:
                artifact = await self.tool_context.load_artifact(artifact_name)
                logger.debug(f"Found partial match: {artifact_name}")
                return artifact, artifact_name
            except Exception as e:
                logger.error(f"Error loading artifact '{artifact_name}': {e}")
                continue
        
        logger.warning(f"No matching artifact found for: {filename}")
        return None, None
    
    async def prepare_file_path(self, artifact: Any, artifact_name: str) -> Optional[str]:
        """
        Prepare file path from artifact, handling both inline data and file references
        
        Returns:
            File path or None if preparation failed
        """
        if not artifact:
            logger.error(f"Artifact '{artifact_name}' is None")
            return None
        
        # Handle inline data
        if hasattr(artifact, 'inline_data') and artifact.inline_data and artifact.inline_data.data:
            try:
                # Determine file extension for temp file
                extension = Path(artifact_name).suffix or '.tmp'
                
                with tempfile.NamedTemporaryFile(suffix=extension, delete=False) as temp_file:
                    temp_file.write(artifact.inline_data.data)
                    temp_file_path = temp_file.name
                
                self.temp_files.append(temp_file_path)
                logger.debug(f"Created temporary file: {temp_file_path}")
                return temp_file_path
                
            except Exception as e:
                logger.error(f"Error creating temporary file: {e}")
                return None
        
        # Handle file path reference
        elif hasattr(artifact, 'text') and artifact.text:
            file_path = artifact.text.strip()
            if os.path.exists(file_path):
                logger.debug(f"Using file path reference: {file_path}")
                return file_path
            else:
                logger.error(f"Referenced file does not exist: {file_path}")
                return None
        
        # Handle direct content for text files
        elif hasattr(artifact, 'text') and artifact.text:
            return artifact.text  # Return content directly for text processing
        
        logger.error(f"Artifact '{artifact_name}' contains no usable data")
        return None
    
    async def process_pdf(self, filename: str) -> ProcessingResult:
        """Process PDF document"""
        logger.info(f"Processing PDF: {filename}")
        result = ProcessingResult(filename, "")
        
        try:
            artifact, artifact_name = await self.find_artifact(filename)
            if not artifact:
                result.set_error(f"PDF file '{filename}' not found")
                return result
            
            result.artifact_name = artifact_name
            file_path = await self.prepare_file_path(artifact, artifact_name)
            
            if not file_path or not os.path.exists(file_path):
                result.set_error(f"Could not access PDF file: {filename}")
                return result
            
            # Extract PDF data
            pdf_data = extract_universal_pdf_data(file_path)
            logger.info(f"Extracted {len(pdf_data)} pages from PDF")
            
            # Format content
            content = []
            for page_data in pdf_data:
                page_info = {
                    "page_number": page_data["page_number"],
                    "text": page_data["text"],
                    "char_count": len(page_data["text"]),
                    "tables_count": len(page_data["tables"]),
                    "tables": page_data["tables"]
                }
                content.append(page_info)
            
            # Set metadata
            metadata = {
                "total_pages": len(pdf_data),
                "total_characters": sum(len(page["text"]) for page in pdf_data),
                "total_tables": sum(len(page["tables"]) for page in pdf_data)
            }
            
            result.set_success(content, metadata)
            logger.info(f"Successfully processed PDF: {filename}")
            
        except Exception as e:
            error_msg = f"Failed to process PDF '{filename}': {str(e)}"
            logger.error(f"{error_msg}\n{traceback.format_exc()}")
            result.set_error(error_msg)
        
        return result
    
    async def process_docx(self, filename: str) -> ProcessingResult:
        """Process DOCX document"""
        logger.info(f"Processing DOCX: {filename}")
        result = ProcessingResult(filename, "")
        
        try:
            artifact, artifact_name = await self.find_artifact(filename)
            if not artifact:
                result.set_error(f"DOCX file '{filename}' not found")
                return result
            
            result.artifact_name = artifact_name
            file_path = await self.prepare_file_path(artifact, artifact_name)
            
            if not file_path or not os.path.exists(file_path):
                result.set_error(f"Could not access DOCX file: {filename}")
                return result
            
            # Extract DOCX data
            docx_data = extract_docx_data(file_path)
            logger.info(f"Extracted DOCX content: {len(docx_data.get('text', ''))} chars, {len(docx_data.get('tables', []))} tables")
            
            # Format content
            content = [{
                "text": docx_data["text"],
                "char_count": len(docx_data["text"]),
                "tables_count": len(docx_data["tables"]),
                "tables": docx_data["tables"]
            }]
            
            # Set metadata
            metadata = {
                "total_characters": len(docx_data["text"]),
                "total_tables": len(docx_data["tables"])
            }
            
            result.set_success(content, metadata)
            logger.info(f"Successfully processed DOCX: {filename}")
            
        except Exception as e:
            error_msg = f"Failed to process DOCX '{filename}': {str(e)}"
            logger.error(f"{error_msg}\n{traceback.format_exc()}")
            result.set_error(error_msg)
        
        return result
    
    async def process_txt(self, filename: str) -> ProcessingResult:
        """Process TXT document"""
        logger.info(f"Processing TXT: {filename}")
        result = ProcessingResult(filename, "")
        
        try:
            artifact, artifact_name = await self.find_artifact(filename)
            if not artifact:
                result.set_error(f"TXT file '{filename}' not found")
                return result
            
            result.artifact_name = artifact_name
            
            # Handle text content
            content_text = ""
            
            # Try to get content from artifact
            if hasattr(artifact, 'inline_data') and artifact.inline_data and artifact.inline_data.data:
                try:
                    # Try different encodings
                    for encoding in ['utf-8', 'latin-1', 'cp1252']:
                        try:
                            content_text = artifact.inline_data.data.decode(encoding)
                            logger.debug(f"Successfully decoded with {encoding}")
                            break
                        except UnicodeDecodeError:
                            continue
                    else:
                        result.set_error("Could not decode text content with any supported encoding")
                        return result
                except Exception as e:
                    result.set_error(f"Error extracting text content: {str(e)}")
                    return result
            
            elif hasattr(artifact, 'text') and artifact.text:
                # Check if it's a file path or direct content
                text_content = artifact.text.strip()
                if os.path.exists(text_content):
                    # It's a file path
                    try:
                        with open(text_content, 'r', encoding='utf-8') as f:
                            content_text = f.read()
                    except UnicodeDecodeError:
                        # Try with different encoding
                        with open(text_content, 'r', encoding='latin-1') as f:
                            content_text = f.read()
                else:
                    # It's direct content
                    content_text = text_content
            
            if not content_text:
                result.set_error(f"Could not extract text content from '{filename}'")
                return result
            
            # Format content
            lines = content_text.split('\n')
            content = [{
                "text": content_text,
                "char_count": len(content_text),
                "line_count": len(lines),
                "word_count": len(content_text.split())
            }]
            
            # Set metadata
            metadata = {
                "total_characters": len(content_text),
                "total_lines": len(lines),
                "total_words": len(content_text.split())
            }
            
            result.set_success(content, metadata)
            logger.info(f"Successfully processed TXT: {filename}")
            
        except Exception as e:
            error_msg = f"Failed to process TXT '{filename}': {str(e)}"
            logger.error(f"{error_msg}\n{traceback.format_exc()}")
            result.set_error(error_msg)
        
        return result
    
    async def process_document(self, filename: str) -> Dict[str, Any]:
        """
        Unified document processing with automatic type detection
        
        Args:
            filename: Name of the document to process
            
        Returns:
            Dictionary with processing results
        """
        logger.info(f"Starting document processing: {filename}")
        
        # Detect document type
        doc_type = self.detect_document_type(filename)
        if not doc_type:
            supported = ", ".join(self.get_supported_extensions())
            return {
                "error": f"Unsupported document type for '{filename}'. Supported types: {supported}"
            }
        
        logger.info(f"Detected document type: {doc_type.value}")
        
        # Route to appropriate processor
        try:
            if doc_type == DocumentType.PDF:
                result = await self.process_pdf(filename)
            elif doc_type in [DocumentType.DOCX, DocumentType.DOC]:
                result = await self.process_docx(filename)
            elif doc_type == DocumentType.TXT:
                result = await self.process_txt(filename)
            else:
                return {"error": f"Handler not implemented for document type: {doc_type.value}"}
            
            return result.to_dict()
            
        except Exception as e:
            error_msg = f"Document processing failed for '{filename}': {str(e)}"
            logger.error(f"{error_msg}\n{traceback.format_exc()}")
            return {"error": error_msg}


# Async function wrappers for the FunctionTool
async def process_document_function(filename: str, tool_context: ToolContext) -> Dict[str, Any]:
    """
    Process any document (PDF, DOCX, TXT) with automatic format detection.
    
    This unified document processing tool automatically detects the file type based on 
    the file extension and routes to the appropriate processor. Extracts text content,
    tables, and metadata from documents.
    
    Supported formats:
    - PDF: Extracts text and tables with OCR fallback for scanned documents
    - DOCX/DOC: Extracts text and tables from Microsoft Word documents
    - TXT: Processes plain text files with multi-encoding support
    
    Args:
        filename: The name of the document file to process
        tool_context: The ToolContext for accessing artifacts
        
    Returns:
        A dictionary containing:
        - filename: Original filename
        - status: "success" or "error"
        - content: List of extracted content (pages/sections)
        - metadata: Document statistics and information
        - error: Error message if processing failed
    """
    async with DocumentProcessor(tool_context) as processor:
        return await processor.process_document(filename)


# Create FunctionTool instances
process_document_tool = FunctionTool(func=process_document_function)
