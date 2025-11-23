"""
Azure AI Search client for indexing and searching documents.
Uses DefaultAzureCredential with fallback to API key authentication.
"""
from azure.identity import DefaultAzureCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SimpleField,
    SearchableField,
    SearchFieldDataType,
    VectorSearch,
    HnswAlgorithmConfiguration,
    VectorSearchProfile,
)
from azure.core.credentials import AzureKeyCredential
from typing import List, Dict, Any, Optional
import logging

from config import settings

logger = logging.getLogger(__name__)


class SearchService:
    """Manages Azure AI Search operations for document indexing and retrieval."""
    
    def __init__(self):
        """Initialize the Search Service with DefaultAzureCredential or API key."""
        self.endpoint = settings.azure_search_endpoint
        self.index_name = settings.azure_search_index_name
        
        # Try DefaultAzureCredential first, fallback to API key
        if settings.azure_search_api_key:
            logger.info("Using API key authentication for Azure AI Search")
            self.credential = AzureKeyCredential(settings.azure_search_api_key)
        else:
            logger.info("Using DefaultAzureCredential for Azure AI Search")
            self.credential = DefaultAzureCredential()
        
        self.index_client = SearchIndexClient(
            endpoint=self.endpoint,
            credential=self.credential
        )
        
        self.search_client = SearchClient(
            endpoint=self.endpoint,
            index_name=self.index_name,
            credential=self.credential
        )
    
    def create_index(self, vector_dimensions: int = 3072):
        """
        Create the search index with vector search capabilities.
        
        Args:
            vector_dimensions: Dimension of embedding vectors (3072 for text-embedding-3-large)
        """
        # Define the index schema
        fields = [
            SimpleField(
                name="id",
                type=SearchFieldDataType.String,
                key=True,
                filterable=True
            ),
            SearchableField(
                name="content",
                type=SearchFieldDataType.String,
                searchable=True
            ),
            SearchableField(
                name="title",
                type=SearchFieldDataType.String,
                searchable=True,
                filterable=True
            ),
            SimpleField(
                name="source",
                type=SearchFieldDataType.String,
                filterable=True,
                facetable=True
            ),
            SearchableField(
                name="content_vector",
                type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                searchable=True,
                vector_search_dimensions=vector_dimensions,
                vector_search_profile_name="vector-config"
            ),
        ]
        
        # Configure vector search
        vector_search = VectorSearch(
            algorithms=[
                HnswAlgorithmConfiguration(
                    name="hnsw-algorithm",
                    parameters={
                        "m": 4,
                        "efConstruction": 400,
                        "efSearch": 500,
                        "metric": "cosine"
                    }
                )
            ],
            profiles=[
                VectorSearchProfile(
                    name="vector-config",
                    algorithm_configuration_name="hnsw-algorithm"
                )
            ]
        )
        
        # Create the index
        index = SearchIndex(
            name=self.index_name,
            fields=fields,
            vector_search=vector_search
        )
        
        try:
            self.index_client.create_or_update_index(index)
            logger.info(f"Search index '{self.index_name}' created/updated successfully")
        except Exception as e:
            logger.error(f"Failed to create search index: {e}")
            raise
    
    def index_documents(self, documents: List[Dict[str, Any]]):
        """
        Index documents in Azure AI Search.
        
        Args:
            documents: List of document dictionaries with id, content, title, source, content_vector
        """
        try:
            result = self.search_client.upload_documents(documents=documents)
            logger.info(f"Indexed {len(documents)} documents")
            return result
        except Exception as e:
            logger.error(f"Failed to index documents: {e}")
            raise
    
    def search(
        self,
        query: str,
        query_vector: Optional[List[float]] = None,
        top: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search for documents using hybrid search (text + vector).
        
        Args:
            query: Search query text
            query_vector: Query embedding vector for vector search
            top: Number of results to return
            
        Returns:
            List of search results with content, title, source, and score
        """
        try:
            if query_vector:
                # Hybrid search with both text and vector
                results = self.search_client.search(
                    search_text=query,
                    vector_queries=[{
                        "vector": query_vector,
                        "k_nearest_neighbors": top,
                        "fields": "content_vector"
                    }],
                    top=top,
                    select=["id", "content", "title", "source"]
                )
            else:
                # Text-only search
                results = self.search_client.search(
                    search_text=query,
                    top=top,
                    select=["id", "content", "title", "source"]
                )
            
            # Convert results to list
            docs = []
            for result in results:
                docs.append({
                    "id": result.get("id"),
                    "content": result.get("content"),
                    "title": result.get("title"),
                    "source": result.get("source"),
                    "score": result.get("@search.score", 0)
                })
            
            logger.info(f"Found {len(docs)} documents for query: {query[:50]}...")
            return docs
        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise


# Global search service instance
search_service = SearchService()
