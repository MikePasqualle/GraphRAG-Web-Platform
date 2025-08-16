"""
Конфігурація додатку
Налаштування для GraphRAG Web Platform
"""

import os
from pathlib import Path
from typing import List, Optional

from pydantic import BaseSettings, validator


class Settings(BaseSettings):
    """Налаштування додатку з environment змінних"""
    
    # OpenAI Configuration
    openai_api_key: str
    graphrag_llm_model: str = "gpt-4o-2024-11-20"
    graphrag_embedding_model: str = "text-embedding-3-large"
    graphrag_reasoning_effort: str = "high"
    graphrag_max_completion_tokens: int = 4096
    
    # Application Configuration
    upload_max_size: int = 104857600  # 100MB
    upload_dir: str = "./data/uploads"
    output_dir: str = "./data/output"
    metadata_dir: str = "./data/metadata"
    cache_dir: str = "./data/cache"
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    
    # Worker Configuration
    worker_threads: int = 4
    max_concurrent_indexing: int = 3
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "./logs/app.log"
    
    # Security
    secret_key: str = "your-secret-key-here-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Redis (optional)
    redis_url: Optional[str] = None
    
    # Environment
    environment: str = "development"
    debug: bool = True
    
    @validator('cors_origins', pre=True)
    def parse_cors_origins(cls, v: str) -> List[str]:
        """Парсинг CORS origins з строки"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',')]
        return v
    
    @validator('upload_dir', 'output_dir', 'metadata_dir', 'cache_dir', 'log_file', pre=True)
    def create_directories(cls, v: str) -> str:
        """Створення каталогів якщо вони не існують"""
        path = Path(v)
        if str(path).endswith('.log'):
            # Для файлу логу створюємо батьківський каталог
            path.parent.mkdir(parents=True, exist_ok=True)
        else:
            # Для каталогів створюємо сам каталог
            path.mkdir(parents=True, exist_ok=True)
        return str(path)
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Глобальний екземпляр налаштувань
settings = Settings()

# Шляхи до важливих файлів
SETTINGS_YAML_PATH = Path("config/settings.yml")
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Налаштування GraphRAG
GRAPHRAG_CONFIG = {
    "llm": {
        "api_key": settings.openai_api_key,
        "type": "openai_chat",
        "model": settings.graphrag_llm_model,
        "max_tokens": settings.graphrag_max_completion_tokens,
        "reasoning_effort": settings.graphrag_reasoning_effort,
        "temperature": 0.1
    },
    "embeddings": {
        "api_key": settings.openai_api_key,
        "type": "openai_embedding", 
        "model": settings.graphrag_embedding_model,
        "dimensions": 3072
    },
    "chunks": {
        "size": 1200,
        "overlap": 100
    },
    "entity_extraction": {
        "max_gleanings": 1
    },
    "input": {
        "base_dir": settings.upload_dir
    },
    "storage": {
        "base_dir": settings.output_dir
    },
    "cache": {
        "base_dir": settings.cache_dir
    }
}

# Налаштування логування
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
    },
    "handlers": {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
        "file": {
            "formatter": "default",
            "class": "logging.FileHandler",
            "filename": settings.log_file,
        },
    },
    "root": {
        "level": settings.log_level,
        "handlers": ["default", "file"],
    },
}

# Підтримувані типи файлів
SUPPORTED_FILE_TYPES = {
    'text/plain': ['.txt'],
    'application/pdf': ['.pdf'],
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
    'application/msword': ['.doc']
}

# Статуси обробки файлів
FILE_STATUS = {
    'UPLOADED': 'uploaded',
    'INDEXING': 'indexing',
    'COMPLETED': 'completed',
    'ERROR': 'error',
    'CANCELLED': 'cancelled'
}
