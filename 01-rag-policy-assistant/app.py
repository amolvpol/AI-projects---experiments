"""
RAG Policy Assistant - FastAPI Application

A Retrieval-Augmented Generation application for querying policy documents
using Azure OpenAI and Azure AI Search.
"""

import os
import logging
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
log_level = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(
    level=getattr(logging, log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Pydantic models for request/response validation
class HealthResponse(BaseModel):
    """Health check response model"""
    status: str = Field(..., description="Application status")
    message: str = Field(..., description="Status message")


class QueryRequest(BaseModel):
    """Query request model"""
    query: str = Field(..., description="User query", min_length=1)
    max_results: Optional[int] = Field(5, description="Maximum number of results", ge=1, le=20)


class QueryResponse(BaseModel):
    """Query response model"""
    query: str = Field(..., description="Original query")
    answer: str = Field(..., description="Generated answer")
    sources: list = Field(default_factory=list, description="Source documents")


# Application configuration
class Config:
    """Application configuration from environment variables"""
    def __init__(self):
        self.aoai_endpoint = os.getenv("AOAI_ENDPOINT")
        self.aoai_key = os.getenv("AOAI_KEY")
        self.chat_model = os.getenv("CHAT_MODEL", "gpt-4o-mini")
        self.embed_model = os.getenv("EMBED_MODEL", "text-embedding-3-large")
        self.ai_search_endpoint = os.getenv("AI_SEARCH_ENDPOINT")
        self.ai_search_key = os.getenv("AI_SEARCH_KEY")
        
    def validate(self):
        """Validate required configuration"""
        required_vars = [
            "aoai_endpoint",
            "aoai_key",
            "ai_search_endpoint",
            "ai_search_key"
        ]
        missing = [var for var in required_vars if not getattr(self, var)]
        if missing:
            logger.warning(f"Missing configuration: {', '.join(missing)}")
            return False
        return True


# Global configuration instance
config = Config()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("Starting RAG Policy Assistant application")
    config.validate()
    yield
    logger.info("Shutting down RAG Policy Assistant application")


# Initialize FastAPI application
app = FastAPI(
    title="RAG Policy Assistant",
    description="A Retrieval-Augmented Generation application for querying policy documents",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint
    
    Returns the application status and a welcome message.
    """
    return HealthResponse(
        status="healthy",
        message="RAG Policy Assistant is running"
    )


@app.post("/query", response_model=QueryResponse)
async def query_policies(request: QueryRequest):
    """
    Query policy documents
    
    Process a user query and return relevant information from policy documents
    using RAG (Retrieval-Augmented Generation).
    
    Args:
        request: Query request containing the user's question
        
    Returns:
        QueryResponse with the generated answer and source documents
        
    Raises:
        HTTPException: If the query processing fails
    """
    try:
        logger.info(f"Processing query: {request.query}")
        
        # Validate configuration
        if not config.validate():
            raise HTTPException(
                status_code=500,
                detail="Application configuration is incomplete. Please check environment variables."
            )
        
        # TODO: Implement RAG logic
        # 1. Generate embeddings for the query
        # 2. Search Azure AI Search for relevant documents
        # 3. Generate answer using Azure OpenAI with retrieved context
        
        # Placeholder response
        return QueryResponse(
            query=request.query,
            answer="This is a placeholder response. RAG implementation is pending.",
            sources=[]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while processing your query: {str(e)}"
        )


@app.get("/config")
async def get_config():
    """
    Get application configuration status
    
    Returns information about the current configuration without exposing secrets.
    """
    return {
        "aoai_endpoint_configured": bool(config.aoai_endpoint),
        "aoai_key_configured": bool(config.aoai_key),
        "chat_model": config.chat_model,
        "embed_model": config.embed_model,
        "ai_search_endpoint_configured": bool(config.ai_search_endpoint),
        "ai_search_key_configured": bool(config.ai_search_key),
        "configuration_valid": config.validate()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
