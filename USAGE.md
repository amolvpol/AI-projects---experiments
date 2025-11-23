# Usage Examples

This document provides practical examples of using the RAG Policy Assistant API.

## Prerequisites

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment variables in `.env`:
```bash
cp .env.example .env
# Edit .env with your Azure credentials
```

3. Start the server:
```bash
python main.py
```

The API will be available at `http://localhost:8000`

## Example 1: Ingesting Documents

### Upload a PDF Document

```bash
curl -X POST http://localhost:8000/ingest \
  -F "file=@company-handbook.pdf"
```

**Response:**
```json
{
  "message": "Document ingested and indexed successfully",
  "filename": "company-handbook.pdf",
  "chunks_indexed": 15
}
```

### Upload a Text Document

```bash
curl -X POST http://localhost:8000/ingest \
  -F "file=@policy-document.txt"
```

## Example 2: Asking Questions

### Simple Question

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the company vacation policy?"
  }'
```

**Response:**
```json
{
  "answer": "According to the employee handbook [1], full-time employees are entitled to 15 days of paid vacation per year. Vacation days accrue monthly at a rate of 1.25 days per month [1]. Employees must request vacation at least two weeks in advance through the HR portal [2].",
  "citations": [
    {
      "number": 1,
      "title": "company-handbook.pdf",
      "source": "company-handbook.pdf",
      "relevance_score": 0.89
    },
    {
      "number": 2,
      "title": "hr-procedures.pdf",
      "source": "hr-procedures.pdf",
      "relevance_score": 0.76
    }
  ]
}
```

### Complex Question

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "How do I submit an expense report for a business trip?"
  }'
```

## Example 3: Using Python Client

```python
import requests

# Base URL
BASE_URL = "http://localhost:8000"

# 1. Ingest a document
def ingest_document(file_path):
    with open(file_path, 'rb') as f:
        files = {'file': f}
        response = requests.post(f"{BASE_URL}/ingest", files=files)
        return response.json()

# 2. Ask a question
def ask_question(question):
    response = requests.post(
        f"{BASE_URL}/ask",
        json={"question": question}
    )
    return response.json()

# Usage
result = ingest_document("employee-handbook.pdf")
print(f"Indexed {result['chunks_indexed']} chunks")

answer = ask_question("What is the remote work policy?")
print(f"\nAnswer: {answer['answer']}")
print(f"\nCitations:")
for citation in answer['citations']:
    print(f"  [{citation['number']}] {citation['source']} (score: {citation['relevance_score']:.2f})")
```

## Example 4: Batch Document Ingestion

```bash
# Ingest multiple documents
for file in documents/*.pdf; do
  echo "Ingesting $file..."
  curl -X POST http://localhost:8000/ingest -F "file=@$file"
  echo ""
done
```

## Example 5: Interactive Q&A Session

```python
import requests

BASE_URL = "http://localhost:8000"

def chat():
    print("RAG Policy Assistant - Interactive Mode")
    print("Type 'exit' to quit\n")
    
    while True:
        question = input("Question: ")
        if question.lower() == 'exit':
            break
        
        response = requests.post(
            f"{BASE_URL}/ask",
            json={"question": question}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"\nAnswer: {data['answer']}\n")
            print("Sources:")
            for citation in data['citations']:
                print(f"  - {citation['source']}")
            print()
        else:
            print(f"Error: {response.json()['detail']}\n")

if __name__ == "__main__":
    chat()
```

## Example 6: Health Check

```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy"
}
```

## Error Handling

### No Documents Ingested

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the policy?"}'
```

**Response (404):**
```json
{
  "detail": "No relevant documents found. Please ingest documents first."
}
```

### Unsupported File Format

```bash
curl -X POST http://localhost:8000/ingest \
  -F "file=@document.docx"
```

**Response (400):**
```json
{
  "detail": "Unsupported file format: .docx. Only PDF and TXT files are supported."
}
```

## API Documentation

Visit the interactive API documentation:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Tips

1. **Document Chunking**: Large documents are automatically split into chunks for better retrieval. The default chunk size is 1000 characters with 200 characters overlap.

2. **Hybrid Search**: The system uses both text matching and vector similarity for optimal results.

3. **Citations**: Always check the citations to verify the source of information in the answers.

4. **Rate Limiting**: For production use, consider implementing rate limiting on the API endpoints.

5. **Document Updates**: To update a document, re-upload it with the same filename. The system will create a new set of chunks with unique IDs.
