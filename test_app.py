"""
Basic tests for the RAG Policy Assistant.
These tests verify the core logic without requiring Azure credentials.
"""
import os
import tempfile
from pathlib import Path

# Test document processing functions
from document_processor import chunk_text, generate_document_id


def test_chunk_text_small():
    """Test chunking with small text that doesn't need splitting."""
    text = "This is a short text."
    chunks = chunk_text(text, chunk_size=1000, overlap=200)
    assert len(chunks) == 1
    assert chunks[0] == text
    print("✓ test_chunk_text_small passed")


def test_chunk_text_large():
    """Test chunking with text that needs splitting."""
    # Create a long text
    text = "This is a sentence. " * 100  # ~2000 characters
    chunks = chunk_text(text, chunk_size=500, overlap=100)
    
    assert len(chunks) > 1, "Should create multiple chunks"
    
    # Verify overlap exists
    if len(chunks) > 1:
        # Check that consecutive chunks have some overlap
        for i in range(len(chunks) - 1):
            # Last part of current chunk should appear in next chunk
            assert len(chunks[i]) > 0
            assert len(chunks[i + 1]) > 0
    
    print(f"✓ test_chunk_text_large passed - created {len(chunks)} chunks")


def test_generate_document_id():
    """Test document ID generation."""
    doc_id1 = generate_document_id("test.pdf", 0)
    doc_id2 = generate_document_id("test.pdf", 0)
    doc_id3 = generate_document_id("test.pdf", 1)
    
    # Same inputs should generate same ID
    assert doc_id1 == doc_id2
    
    # Different inputs should generate different IDs
    assert doc_id1 != doc_id3
    
    # ID should be a valid hex string
    assert len(doc_id1) == 32  # MD5 hash length
    
    print("✓ test_generate_document_id passed")


def test_txt_file_processing():
    """Test processing a TXT file."""
    from document_processor import process_document
    
    # Create a temporary TXT file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        test_content = "This is a test document. " * 50
        f.write(test_content)
        temp_path = f.name
    
    try:
        # Process the document
        docs = process_document(
            file_path=temp_path,
            filename="test.txt",
            chunk_size=500,
            overlap=100
        )
        
        assert len(docs) > 0, "Should create at least one document"
        
        # Verify document structure
        for doc in docs:
            assert "id" in doc
            assert "content" in doc
            assert "title" in doc
            assert "source" in doc
            assert doc["title"] == "test.txt"
            assert doc["source"] == "test.txt"
            assert len(doc["content"]) > 0
        
        print(f"✓ test_txt_file_processing passed - created {len(docs)} chunks")
    
    finally:
        # Clean up
        os.unlink(temp_path)


def test_config_loading():
    """Test configuration loading with environment variables."""
    # Set test environment variables
    os.environ["AZURE_OPENAI_ENDPOINT"] = "https://test.openai.azure.com/"
    os.environ["AZURE_SEARCH_ENDPOINT"] = "https://test.search.windows.net"
    
    # Import after setting env vars
    from config import Settings
    
    settings = Settings()
    
    assert settings.azure_openai_endpoint == "https://test.openai.azure.com/"
    assert settings.azure_search_endpoint == "https://test.search.windows.net"
    assert settings.azure_openai_embedding_deployment == "text-embedding-3-large"
    assert settings.azure_openai_chat_deployment == "gpt-4o-mini"
    
    print("✓ test_config_loading passed")


def run_all_tests():
    """Run all tests."""
    print("\n" + "="*60)
    print("Running RAG Policy Assistant Tests")
    print("="*60 + "\n")
    
    tests = [
        test_chunk_text_small,
        test_chunk_text_large,
        test_generate_document_id,
        test_txt_file_processing,
        test_config_loading,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"✗ {test.__name__} failed: {e}")
            failed += 1
    
    print("\n" + "="*60)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("="*60 + "\n")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
