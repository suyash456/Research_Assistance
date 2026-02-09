"""Configuration management for Research Assistant."""
import os
from pathlib import Path
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Load environment variables
load_dotenv()

class Settings(BaseSettings):
    """Application settings."""

    # API Keys
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")

    # Neo4j Configuration
    neo4j_uri: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user: str = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password: str = os.getenv("NEO4J_PASSWORD", "password")

    # Paths
    vector_store_path: str = os.getenv("VECTOR_STORE_PATH", "./data/vectorstore")
    pdf_upload_path: str = os.getenv("PDF_UPLOAD_PATH", "./data/pdfs")

    # Processing Configuration
    chunk_size: int = int(os.getenv("CHUNK_SIZE", "1000"))
    chunk_overlap: int = int(os.getenv("CHUNK_OVERLAP", "200"))

    # Model Configuration
    model_name: str = "gpt-4"
    embedding_model: str = "text-embedding-ada-002"
    temperature: float = 0.0

    class Config:
        env_file = ".env"
        case_sensitive = False

# Create settings instance
settings = Settings()

# Ensure directories exist
Path(settings.vector_store_path).mkdir(parents=True, exist_ok=True)
Path(settings.pdf_upload_path).mkdir(parents=True, exist_ok=True)
