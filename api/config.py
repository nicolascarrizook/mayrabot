"""
Configuration for the Nutrition Bot API
"""

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings"""
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = True
    api_workers: int = 1
    
    # CORS
    cors_origins: List[str] = ["*"]
    
    # OpenAI Configuration
    openai_api_key: str
    openai_model: str = "gpt-4-turbo-preview"
    openai_temperature: float = 0.7
    openai_max_tokens: int = 4000
    
    # ChromaDB Configuration
    chroma_persist_directory: str = "./chroma_db"
    chroma_collection_name: str = "nutrition_recipes"
    
    # Redis Configuration
    redis_host: str = "redis"
    redis_port: int = 6379
    redis_db: int = 0
    redis_decode_responses: bool = True
    
    # PDF Generation
    pdf_output_directory: str = "./generated_pdfs"
    pdf_template_directory: str = "./pdf_templates"
    
    # Nutritional Method Configuration
    default_meals_per_day: int = 4
    default_days_per_plan: int = 7
    calories_per_exchange: dict = {
        "lacteos": 80,
        "frutas": 60,
        "cereales": 80,
        "proteinas": 75,
        "grasas": 45,
        "vegetales": 25
    }
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields from .env


# Create settings instance
settings = Settings()