# RAG Policy Assistant

A FastAPI-based Retrieval-Augmented Generation (RAG) application for querying policy documents using Azure OpenAI, Azure AI Search, and Azure Blob Storage.

## Features

- FastAPI web application with RESTful API endpoints
- PDF document upload and text extraction
- Integration with Azure OpenAI for chat and embeddings
- Azure AI Search for vector-based document retrieval
- Azure Blob Storage for document persistence
- Environment-based configuration
- Comprehensive test suite

## Prerequisites

- Python 3.8 or higher
- Azure OpenAI account with API access
- Azure AI Search service
- Azure Storage account for blob storage

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd 01-rag-policy-assistant
```

2. Create a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your Azure credentials
```

## Configuration

Set the following environment variables in your `.env` file:

- `AOAI_ENDPOINT`: Azure OpenAI endpoint URL
- `AOAI_KEY`: Azure OpenAI API key
- `CHAT_MODEL`: Chat model deployment name (default: gpt-4o-mini)
- `EMBED_MODEL`: Embedding model deployment name (default: text-embedding-3-large)
- `AI_SEARCH_ENDPOINT`: Azure AI Search endpoint URL
- `AI_SEARCH_KEY`: Azure AI Search API key
- `AZURE_STORAGE_CONNECTION_STRING`: Azure Storage connection string
- `LOG_LEVEL`: Logging level (INFO, DEBUG, WARNING, ERROR)

## Running the Application

Start the development server:
```bash
uvicorn app:app --reload
```

The API will be available at `http://localhost:8000`.

View the interactive API documentation at `http://localhost:8000/docs`.

## Running Tests

Execute the test suite:
```bash
pytest
```

Run tests with coverage:
```bash
pytest --cov=. --cov-report=html
```

## Project Structure

```
01-rag-policy-assistant/
├── app.py                 # Main FastAPI application
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── .env.example          # Environment variable template
├── .gitignore           # Git ignore patterns
├── tests/               # Test directory
│   ├── __init__.py
│   └── test_app.py      # Application tests
└── data/                # Data storage directory
```

## API Endpoints

- `GET /`: Health check endpoint
- `POST /upload-policy`: Upload and index a PDF policy document
- `POST /ask-policy`: Ask questions about policy documents using RAG
- `GET /docs`: Interactive API documentation (Swagger UI)
- `GET /redoc`: Alternative API documentation (ReDoc)

### Upload Policy Document

Upload a PDF file to be processed, stored, and indexed for querying.

**Endpoint:** `POST /upload-policy`

**Request:**
- Content-Type: multipart/form-data
- Body: file (PDF file)

**Response:**
```json
{
  "message": "Policy document uploaded and indexed",
  "document_id": "uuid"
}
```

### Ask Policy Question

Query the indexed policy documents using RAG.

**Endpoint:** `POST /ask-policy`

**Request:**
```json
{
  "question": "What is the policy on remote work?"
}
```

**Response:**
```json
{
  "answer": "According to the policy...",
  "sources": ["doc1", "doc2"]
}
```

## Development

This project uses:
- **FastAPI** for the web framework
- **Uvicorn** as the ASGI server
- **Azure OpenAI** for LLM capabilities
- **Azure AI Search** for vector search
- **Azure Blob Storage** for document storage
- **PyMuPDF** for PDF text extraction
- **Pydantic** for data validation
- **pytest** for testing

## License

[Specify your license here]

## Contributing

[Add contribution guidelines here]
