# RAG Policy Assistant

A FastAPI application that answers questions grounded in enterprise documents using Azure OpenAI and Azure AI Search. This application provides a Retrieval-Augmented Generation (RAG) system for policy documents and enterprise knowledge bases.

## Features

- **Question Answering** (`POST /ask`): Ask questions and get grounded answers with citations from indexed documents
- **Document Ingestion** (`POST /ingest`): Upload and index PDF or TXT documents for retrieval
- **Azure Integration**: Uses Azure OpenAI for embeddings and chat, Azure AI Search for vector search
- **Secure Authentication**: Uses `DefaultAzureCredential` for Azure services with fallback to API keys
- **Hybrid Search**: Combines text search and vector search for optimal retrieval
- **Citation Support**: Provides source citations with relevance scores

## Architecture

- **Embeddings**: `text-embedding-3-large` (configurable via env)
- **Chat Model**: `gpt-4o-mini` (configurable via env)
- **Vector Search**: Azure AI Search with HNSW algorithm
- **Document Processing**: Automatic chunking with overlap for better retrieval

## Prerequisites

- Python 3.8+
- Azure OpenAI service with deployed models
- Azure AI Search service
- Azure credentials (managed identity or API keys)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/amolvpol/AI-projects---experiments.git
cd AI-projects---experiments
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your Azure credentials and endpoints
```

## Configuration

Create a `.env` file based on `.env.example`:

```env
# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key-here  # Optional if using DefaultAzureCredential
AZURE_OPENAI_API_VERSION=2024-08-01-preview
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-3-large
AZURE_OPENAI_CHAT_DEPLOYMENT=gpt-4o-mini

# Azure AI Search Configuration
AZURE_SEARCH_ENDPOINT=https://your-search-service.search.windows.net
AZURE_SEARCH_API_KEY=your-search-api-key-here  # Optional if using DefaultAzureCredential
AZURE_SEARCH_INDEX_NAME=policy-documents

# Application Configuration
UPLOAD_DIR=uploads
```

### Authentication Options

The application supports two authentication methods:

1. **DefaultAzureCredential** (Recommended): 
   - Automatically uses managed identity, Azure CLI, or environment-based credentials
   - No need to set API keys in environment variables
   - Set `AZURE_SEARCH_API_KEY` and `AZURE_OPENAI_API_KEY` to empty or omit them

2. **API Key Authentication** (Fallback):
   - Set `AZURE_SEARCH_API_KEY` and `AZURE_OPENAI_API_KEY` in `.env`
   - Useful for local development or when managed identity is not available

## Usage

### Start the Server

```bash
python main.py
```

Or with uvicorn directly:
```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

### API Documentation

Once the server is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Endpoints

#### 1. Root - GET /
Get API information and available endpoints.

```bash
curl http://localhost:8000/
```

#### 2. Ingest Documents - POST /ingest

Upload and index documents (PDF or TXT files).

```bash
curl -X POST http://localhost:8000/ingest \
  -F "file=@/path/to/document.pdf"
```

**Response:**
```json
{
  "message": "Document ingested and indexed successfully",
  "filename": "document.pdf",
  "chunks_indexed": 5
}
```

#### 3. Ask Questions - POST /ask

Ask questions and get grounded answers with citations.

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the vacation policy?"}'
```

**Response:**
```json
{
  "answer": "According to the company policy [1], employees are entitled to 15 days of paid vacation per year...",
  "citations": [
    {
      "number": 1,
      "title": "employee-handbook.pdf",
      "source": "employee-handbook.pdf",
      "relevance_score": 0.89
    }
  ]
}
```

#### 4. Health Check - GET /health

Check if the service is running.

```bash
curl http://localhost:8000/health
```

## Project Structure

```
.
├── main.py                 # FastAPI application and endpoints
├── config.py              # Configuration management with pydantic-settings
├── openai_client.py       # Azure OpenAI client for embeddings and chat
├── search.py              # Azure AI Search client for indexing and retrieval
├── document_processor.py  # Document processing utilities
├── requirements.txt       # Python dependencies
├── .env.example          # Example environment configuration
├── .gitignore            # Git ignore patterns
└── README.md             # This file
```

## Development

### Adding New Document Types

To support additional document formats, extend the `process_document` function in `document_processor.py`:

```python
elif ext == '.docx':
    text = extract_text_from_docx(file_path)
```

### Customizing Chunk Size

Adjust chunk size and overlap in the `/ingest` endpoint or in `document_processor.py`:

```python
document_chunks = process_document(
    file_path=str(upload_path),
    filename=filename,
    chunk_size=1500,  # Increase chunk size
    overlap=300       # Increase overlap
)
```

### Changing Models

Update the model deployments in `.env`:

```env
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002
AZURE_OPENAI_CHAT_DEPLOYMENT=gpt-4
```

## Troubleshooting

### Authentication Issues

If you encounter authentication errors:

1. For DefaultAzureCredential: Ensure you're logged in with Azure CLI (`az login`)
2. For API keys: Verify the keys are correctly set in `.env`
3. Check that your Azure resources have the correct permissions

### Index Creation Issues

If the search index fails to create:

1. Verify your Azure AI Search endpoint and credentials
2. Ensure your search service tier supports vector search
3. Check the logs for specific error messages

### Embedding Dimension Mismatch

If you change the embedding model, update the vector dimensions in `search.py`:

```python
search_service.create_index(vector_dimensions=1536)  # For ada-002
```

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
