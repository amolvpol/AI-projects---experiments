"""
RAG Policy Assistant - FastAPI Application

A Retrieval-Augmented Generation application for querying policy documents
using Azure OpenAI, Azure AI Search, and Azure Blob Storage.
"""

import os
import logging
import uuid
from typing import Optional, List
from contextlib import asynccontextmanager

<<<<<<< HEAD
from fastapi import FastAPI, HTTPException, UploadFile, File
=======
from fastapi import FastAPI, HTTPException
>>>>>>> 1fb6c7b69250ea7d387b6dc6725b996864fbbdf5
from pydantic import BaseModel, Field
from dotenv import load_dotenv

import fitz  # PyMuPDF
from openai import AzureOpenAI
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SimpleField,
    SearchableField,
    SearchFieldDataType,
    VectorSearch,
    VectorSearchProfile,
    HnswAlgorithmConfiguration
)
from azure.search.documents.models import VectorizedQuery
from azure.storage.blob import BlobServiceClient
from azure.core.credentials import AzureKeyCredential

# Load environment variables
load_dotenv()

# Configure logging
log_level = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(
    level=getattr(logging, log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Pydantic models
class HealthResponse(BaseModel):
    status: str = Field(..., description="Application status")
    message: str = Field(..., description="Status message")

class UploadResponse(BaseModel):
    message: str
    document_id: str

class AskRequest(BaseModel):
    question: str = Field(..., min_length=1)

class AskResponse(BaseModel):
    answer: str
    sources: List[str]

# Application configuration
class Config:
    def __init__(self):
        self.aoai_endpoint = os.getenv("AOAI_ENDPOINT")
        self.aoai_key = os.getenv("AOAI_KEY")
        self.chat_model = os.getenv("CHAT_MODEL", "gpt-4o-mini")
        self.embed_model = os.getenv("EMBED_MODEL", "text-embedding-3-large")
        self.ai_search_endpoint = os.getenv("AI_SEARCH_ENDPOINT")
        self.ai_search_key = os.getenv("AI_SEARCH_KEY")
        self.azure_storage_connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        self.index_name = "policy-documents"
        self.container_name = "policy-pdfs"

    def validate(self):
        required = [self.aoai_endpoint, self.aoai_key, self.ai_search_endpoint, self.ai_search_key, self.azure_storage_connection_string]
        return all(required)

# Global config
config = Config()

# Global clients
aoai_client = None
search_client = None
blob_service_client = None

def create_search_index():
    """Create the search index if it doesn't exist"""
    index_client = SearchIndexClient(endpoint=config.ai_search_endpoint, credential=AzureKeyCredential(config.ai_search_key))
    
    fields = [
        SimpleField(name="id", type=SearchFieldDataType.String, key=True),
        SimpleField(name="document_id", type=SearchFieldDataType.String),
        SimpleField(name="chunk_id", type=SearchFieldDataType.Int32),
        SearchableField(name="text", type=SearchFieldDataType.String),
        SearchField(
            name="embedding",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            searchable=True,
            vector_search_dimensions=3072,  # for text-embedding-3-large
            vector_search_profile_name="my-vector-profile"
        )
    ]
    
    vector_search = VectorSearch(
        profiles=[VectorSearchProfile(name="my-vector-profile", algorithm_configuration_name="my-algorithms-config")],
        algorithms=[HnswAlgorithmConfiguration(name="my-algorithms-config")]
    )
    
    index = SearchIndex(name=config.index_name, fields=fields, vector_search=vector_search)
    
    try:
        index_client.create_index(index)
        logger.info(f"Created search index: {config.index_name}")
    except Exception as e:
        if "already exists" in str(e).lower():
            logger.info(f"Search index {config.index_name} already exists")
        else:
            logger.error(f"Error creating search index: {e}")
            raise

def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract text from PDF bytes"""
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    return text

def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """Chunk text into smaller pieces"""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - overlap
        if start >= len(text):
            break
    return chunks

def generate_embedding(text: str) -> List[float]:
    """Generate embedding for text"""
    response = aoai_client.embeddings.create(input=text, model=config.embed_model)
    return response.data[0].embedding

@asynccontextmanager
async def lifespan(app: FastAPI):
    global aoai_client, search_client, blob_service_client
    logger.info("Starting RAG Policy Assistant")
    if not config.validate():
        logger.error("Configuration incomplete")
        raise RuntimeError("Configuration incomplete")
    
    aoai_client = AzureOpenAI(api_key=config.aoai_key, api_version="2024-02-01", azure_endpoint=config.aoai_endpoint)
    search_client = SearchClient(endpoint=config.ai_search_endpoint, index_name=config.index_name, credential=AzureKeyCredential(config.ai_search_key))
    blob_service_client = BlobServiceClient.from_connection_string(config.azure_storage_connection_string)
    
    create_search_index()
    
    # Create blob container if not exists
    try:
        blob_service_client.create_container(config.container_name)
    except:
        pass
    
    yield
    logger.info("Shutting down")

app = FastAPI(title="RAG Policy Assistant", lifespan=lifespan)

@app.get("/", response_model=HealthResponse)
async def health_check():
    return HealthResponse(status="healthy", message="RAG Policy Assistant is running")

@app.post("/upload-policy", response_model=UploadResponse)
async def upload_policy(file: UploadFile = File(...)):
    try:
        if not file.filename.endswith('.pdf'):
            raise HTTPException(400, "Only PDF files are supported")
        
        file_bytes = await file.read()
        text = extract_text_from_pdf(file_bytes)
        
        document_id = str(uuid.uuid4())
        
        # Upload PDF to blob
        blob_client = blob_service_client.get_blob_client(container=config.container_name, blob=f"{document_id}.pdf")
        blob_client.upload_blob(file_bytes, overwrite=True)
        
        # Chunk and index
        chunks = chunk_text(text)
        documents = []
        for i, chunk in enumerate(chunks):
            embedding = generate_embedding(chunk)
            documents.append({
                "id": f"{document_id}_{i}",
                "document_id": document_id,
                "chunk_id": i,
                "text": chunk,
                "embedding": embedding
            })
        
        search_client.upload_documents(documents)
        
        return UploadResponse(message="Policy document uploaded and indexed", document_id=document_id)
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(500, str(e))

@app.post("/ask-policy", response_model=AskResponse)
async def ask_policy(request: AskRequest):
    try:
        query_embedding = generate_embedding(request.question)
        
        vector_query = VectorizedQuery(vector=query_embedding, k_nearest_neighbors=5, fields="embedding")
        results = search_client.search(search_text="", vector_queries=[vector_query])
        
        context = ""
        sources = []
        for result in results:
            context += result["text"] + "\n"
            sources.append(result["document_id"])
        
        prompt = f"Context:\n{context}\n\nQuestion: {request.question}\n\nAnswer based on the context:"
        
        response = aoai_client.chat.completions.create(
            model=config.chat_model,
            messages=[{"role": "user", "content": prompt}]
        )
        
        answer = response.choices[0].message.content
        
        return AskResponse(answer=answer, sources=list(set(sources)))
    except Exception as e:
        logger.error(f"Query error: {e}")
        raise HTTPException(500, str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
