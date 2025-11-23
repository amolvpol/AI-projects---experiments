"""
Document processing utilities for handling PDF and TXT files.
"""
import os
import hashlib
from typing import List, Dict, Any
import logging
from PyPDF2 import PdfReader

logger = logging.getLogger(__name__)


def extract_text_from_pdf(file_path: str) -> str:
    """
    Extract text content from a PDF file.
    
    Args:
        file_path: Path to the PDF file
        
    Returns:
        Extracted text content
    """
    try:
        reader = PdfReader(file_path)
        text_parts = []
        for page in reader.pages:
            text_parts.append(page.extract_text())
        text = "\n".join(text_parts)
        logger.info(f"Extracted {len(text)} characters from PDF: {file_path}")
        return text
    except Exception as e:
        logger.error(f"Failed to extract text from PDF {file_path}: {e}")
        raise


def extract_text_from_txt(file_path: str) -> str:
    """
    Extract text content from a TXT file.
    
    Args:
        file_path: Path to the TXT file
        
    Returns:
        Text content
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        logger.info(f"Read {len(text)} characters from TXT: {file_path}")
        return text
    except Exception as e:
        logger.error(f"Failed to read TXT file {file_path}: {e}")
        raise


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """
    Split text into overlapping chunks for better retrieval.
    
    Args:
        text: Input text to chunk
        chunk_size: Target size of each chunk in characters
        overlap: Number of characters to overlap between chunks
        
    Returns:
        List of text chunks
    """
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        
        # Try to break at a sentence boundary
        if end < len(text):
            # Look for sentence endings in the last 200 characters
            search_start = max(start, end - 200)
            for delimiter in ['. ', '.\n', '! ', '?\n', '? ']:
                last_delimiter = text.rfind(delimiter, search_start, end)
                if last_delimiter != -1:
                    end = last_delimiter + len(delimiter)
                    break
        
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        start = end - overlap if end < len(text) else len(text)
    
    logger.info(f"Split text into {len(chunks)} chunks")
    return chunks


def generate_document_id(filename: str, chunk_index: int) -> str:
    """
    Generate a unique ID for a document chunk.
    
    Args:
        filename: Original filename
        chunk_index: Index of the chunk
        
    Returns:
        Unique document ID
    """
    content = f"{filename}_{chunk_index}"
    doc_id = hashlib.md5(content.encode()).hexdigest()
    return doc_id


def process_document(
    file_path: str,
    filename: str,
    chunk_size: int = 1000,
    overlap: int = 200
) -> List[Dict[str, Any]]:
    """
    Process a document file and prepare it for indexing.
    
    Args:
        file_path: Path to the document file
        filename: Original filename
        chunk_size: Target size of each chunk
        overlap: Overlap between chunks
        
    Returns:
        List of document dictionaries ready for indexing (without embeddings)
    """
    # Extract text based on file extension
    ext = os.path.splitext(filename)[1].lower()
    
    if ext == '.pdf':
        text = extract_text_from_pdf(file_path)
    elif ext == '.txt':
        text = extract_text_from_txt(file_path)
    else:
        raise ValueError(f"Unsupported file format: {ext}")
    
    # Clean the text
    text = text.strip()
    if not text:
        raise ValueError(f"No text content found in file: {filename}")
    
    # Split into chunks
    chunks = chunk_text(text, chunk_size=chunk_size, overlap=overlap)
    
    # Create document objects
    documents = []
    for i, chunk in enumerate(chunks):
        doc = {
            "id": generate_document_id(filename, i),
            "content": chunk,
            "title": filename,
            "source": filename,
            "chunk_index": i
        }
        documents.append(doc)
    
    logger.info(f"Processed document '{filename}' into {len(documents)} chunks")
    return documents
