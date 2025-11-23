"""
Configuration settings for the RAG Policy Assistant.
Uses pydantic-settings for environment variable management.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Azure OpenAI Configuration
    azure_openai_endpoint: str
    azure_openai_api_key: Optional[str] = None
    azure_openai_api_version: str = "2024-08-01-preview"
    azure_openai_embedding_deployment: str = "text-embedding-3-large"
    azure_openai_chat_deployment: str = "gpt-4o-mini"
    
    # Azure AI Search Configuration
    azure_search_endpoint: str
    azure_search_api_key: Optional[str] = None
    azure_search_index_name: str = "policy-documents"
    
    # Application Configuration
    upload_dir: str = "uploads"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


# Global settings instance
settings = Settings()
