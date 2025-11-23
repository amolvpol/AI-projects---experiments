"""
FastAPI application for RAG Policy Assistant.
Provides endpoints for document ingestion and question answering.
"""
import os
import logging
from pathlib import Path
from typing import List
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
import uvicorn

from config import settings
from openai_client import openai_service
from search import search_service
from document_processor import process_document, sanitize_filename

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup application resources."""
    # Startup
    logger.info("Starting RAG Policy Assistant...")
    
    # Create upload directory if it doesn't exist
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(exist_ok=True)
    logger.info(f"Upload directory: {upload_dir}")
    
    # Create search index if it doesn't exist
    try:
        search_service.create_index()
        logger.info("Search index initialized")
    except Exception as e:
        logger.warning(f"Could not initialize search index: {e}")
    
    logger.info("RAG Policy Assistant started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down RAG Policy Assistant...")


# Initialize FastAPI app with lifespan
app = FastAPI(
    title="RAG Policy Assistant",
    description="A FastAPI app that answers questions grounded in enterprise documents using Azure OpenAI and Azure AI Search.",
    version="1.0.0",
    lifespan=lifespan
)


class QuestionRequest(BaseModel):
    """Request model for the /ask endpoint."""
    question: str


class AnswerResponse(BaseModel):
    """Response model for the /ask endpoint."""
    answer: str
    citations: List[dict]


class IngestResponse(BaseModel):
    """Response model for the /ingest endpoint."""
    message: str
    filename: str
    chunks_indexed: int


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "RAG Policy Assistant",
        "version": "1.0.0",
        "endpoints": {
            "/ask": "POST - Ask questions grounded in enterprise documents",
            "/ingest": "POST - Upload and index documents (PDF/TXT)"
        }
    }


@app.post("/ask", response_model=AnswerResponse)
async def ask_question(request: QuestionRequest):
    """
    Answer questions grounded in enterprise documents with citations.
    
    Args:
        request: QuestionRequest with the user's question
        
    Returns:
        AnswerResponse with grounded answer and citations
    """
    try:
        logger.info(f"Received question: {request.question}")
        
        # Generate embedding for the question
        question_embedding = openai_service.get_embedding(request.question)
        
        # Search for relevant documents
        relevant_docs = search_service.search(
            query=request.question,
            query_vector=question_embedding,
            top=5
        )
        
        if not relevant_docs:
            raise HTTPException(
                status_code=404,
                detail="No relevant documents found. Please ingest documents first."
            )
        
        # Generate grounded answer with citations
        result = openai_service.generate_grounded_answer(
            question=request.question,
            context_documents=relevant_docs
        )
        
        logger.info(f"Generated answer with {len(result['citations'])} citations")
        
        return AnswerResponse(
            answer=result["answer"],
            citations=result["citations"]
        )
    
    except Exception as e:
        logger.error(f"Error processing question: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ingest", response_model=IngestResponse)
async def ingest_document(file: UploadFile = File(...)):
    """
    Upload and index documents (PDF or TXT).
    
    Args:
        file: Uploaded document file
        
    Returns:
        IngestResponse with ingestion status
    """
    try:
        # Validate file type
        filename = file.filename
        if not filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        
        # Sanitize filename to prevent path traversal
        safe_filename = sanitize_filename(filename)
        
        ext = os.path.splitext(safe_filename)[1].lower()
        if ext not in ['.pdf', '.txt']:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file format: {ext}. Only PDF and TXT files are supported."
            )
        
        logger.info(f"Ingesting document: {safe_filename}")
        
        # Save uploaded file
        upload_path = Path(settings.upload_dir) / safe_filename
        with open(upload_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Process document into chunks
        document_chunks = process_document(
            file_path=str(upload_path),
            filename=safe_filename
        )
        
        # Generate embeddings for all chunks
        texts = [doc["content"] for doc in document_chunks]
        embeddings = openai_service.get_embeddings_batch(texts)
        
        # Add embeddings to document chunks
        for doc, embedding in zip(document_chunks, embeddings):
            doc["content_vector"] = embedding
        
        # Index documents in Azure AI Search
        search_service.index_documents(document_chunks)
        
        logger.info(f"Successfully indexed {len(document_chunks)} chunks from {safe_filename}")
        
        return IngestResponse(
            message="Document ingested and indexed successfully",
            filename=safe_filename,
            chunks_indexed=len(document_chunks)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error ingesting document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
