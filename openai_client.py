"""
Azure OpenAI client for embeddings and chat completions.
Uses DefaultAzureCredential with fallback to API key authentication.
"""
from azure.identity import DefaultAzureCredential
from openai import AzureOpenAI
from typing import List, Dict, Any, Optional
import logging

from config import settings

logger = logging.getLogger(__name__)


class OpenAIService:
    """Manages Azure OpenAI operations for embeddings and chat."""
    
    def __init__(self):
        """Initialize the OpenAI Service."""
        self.embedding_deployment = settings.azure_openai_embedding_deployment
        self.chat_deployment = settings.azure_openai_chat_deployment
        self._client = None
    
    @property
    def client(self):
        """Lazy initialization of Azure OpenAI client."""
        if self._client is None:
            # Azure OpenAI client setup
            if settings.azure_openai_api_key:
                logger.info("Using API key authentication for Azure OpenAI")
                self._client = AzureOpenAI(
                    api_key=settings.azure_openai_api_key,
                    api_version=settings.azure_openai_api_version,
                    azure_endpoint=settings.azure_openai_endpoint
                )
            else:
                logger.info("Using DefaultAzureCredential for Azure OpenAI")
                # Get token from DefaultAzureCredential
                credential = DefaultAzureCredential()
                token_provider = credential.get_token("https://cognitiveservices.azure.com/.default")
                
                self._client = AzureOpenAI(
                    api_version=settings.azure_openai_api_version,
                    azure_endpoint=settings.azure_openai_endpoint,
                    azure_ad_token=token_provider.token
                )
        return self._client
    
    def get_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for the given text.
        
        Args:
            text: Input text to embed
            
        Returns:
            Embedding vector as list of floats
        """
        try:
            response = self.client.embeddings.create(
                input=text,
                model=self.embedding_deployment
            )
            embedding = response.data[0].embedding
            logger.info(f"Generated embedding for text of length {len(text)}")
            return embedding
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise
    
    def get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batch.
        
        Args:
            texts: List of input texts to embed
            
        Returns:
            List of embedding vectors
        """
        try:
            response = self.client.embeddings.create(
                input=texts,
                model=self.embedding_deployment
            )
            embeddings = [item.embedding for item in response.data]
            logger.info(f"Generated {len(embeddings)} embeddings")
            return embeddings
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            raise
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> str:
        """
        Generate chat completion response.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens in response
            
        Returns:
            Generated response text
        """
        try:
            response = self.client.chat.completions.create(
                model=self.chat_deployment,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            answer = response.choices[0].message.content
            logger.info(f"Generated chat completion with {len(answer)} characters")
            return answer
        except Exception as e:
            logger.error(f"Failed to generate chat completion: {e}")
            raise
    
    def generate_grounded_answer(
        self,
        question: str,
        context_documents: List[Dict[str, Any]],
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """
        Generate an answer grounded in retrieved documents with citations.
        
        Args:
            question: User's question
            context_documents: Retrieved documents for context
            temperature: Sampling temperature
            
        Returns:
            Dictionary with 'answer' and 'citations'
        """
        # Build context from documents
        context_parts = []
        citations = []
        
        for i, doc in enumerate(context_documents, 1):
            context_parts.append(f"[{i}] Title: {doc['title']}\nSource: {doc['source']}\nContent: {doc['content']}\n")
            citations.append({
                "number": i,
                "title": doc["title"],
                "source": doc["source"],
                "relevance_score": doc.get("score", 0)
            })
        
        context = "\n".join(context_parts)
        
        # Create prompt for grounded answer
        system_prompt = """You are a helpful assistant that answers questions based on the provided enterprise documents.
Your answers must be grounded in the given context. Always cite your sources using [number] notation.
If the context doesn't contain enough information to answer the question, say so clearly.
Be concise but comprehensive in your answers."""
        
        user_prompt = f"""Context from enterprise documents:
{context}

Question: {question}

Please provide a detailed answer based on the context above. Cite sources using [number] notation."""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        answer = self.chat_completion(messages, temperature=temperature, max_tokens=1500)
        
        return {
            "answer": answer,
            "citations": citations
        }


# Global OpenAI service instance
openai_service = OpenAIService()
