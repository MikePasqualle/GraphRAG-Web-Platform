"""
Головний файл FastAPI додатку
GraphRAG Web Platform Backend
"""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from .config import settings, LOGGING_CONFIG
from .api import files, indexing, chat, graph


# Налаштування логування
logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle manager для FastAPI додатку
    Виконує налаштування при старті та очищення при зупинці
    """
    
    # Startup
    logger.info("Starting GraphRAG Web Platform Backend...")
    
    # Створення необхідних каталогів
    directories = [
        settings.upload_dir,
        settings.output_dir, 
        settings.metadata_dir,
        settings.cache_dir,
        Path(settings.log_file).parent
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        logger.info(f"Ensured directory exists: {directory}")
    
    # Перевірка налаштувань OpenAI
    if not settings.openai_api_key or settings.openai_api_key == "sk-your-openai-api-key-here":
        logger.warning("OpenAI API key not configured properly!")
    
    logger.info("Backend startup completed")
    
    yield
    
    # Shutdown
    logger.info("Shutting down GraphRAG Web Platform Backend...")


# Створення FastAPI додатку
app = FastAPI(
    title="GraphRAG Web Platform API",
    description="""
    API для GraphRAG Web Platform - системи для роботи з графами знань.
    
    ## Основні функції:
    - Завантаження та індексація документів
    - Генерація графів знань за допомогою GraphRAG
    - Чат з документами (local/global режими)
    - Візуалізація та експорт графів
    
    ## Технології:
    - GraphRAG для створення графів знань
    - OpenAI GPT-5 для reasoning
    - Text-embedding-3-large для ембеддингів
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None
)


# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


# Middleware для логування запитів
@app.middleware("http")
async def log_requests(request, call_next):
    """Логування всіх HTTP запитів"""
    
    import time
    
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    
    logger.info(
        f"{request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Time: {process_time:.3f}s"
    )
    
    return response


# Підключення роутерів
app.include_router(files.router)
app.include_router(indexing.router)
app.include_router(chat.router)
app.include_router(graph.router)


# Статичні файли (якщо потрібно)
if Path("static").exists():
    app.mount("/static", StaticFiles(directory="static"), name="static")


# Root endpoint
@app.get("/")
async def root():
    """
    Кореневий endpoint з інформацією про API
    """
    return JSONResponse(content={
        "name": "GraphRAG Web Platform API",
        "version": "1.0.0",
        "description": "API для роботи з графами знань",
        "status": "operational",
        "endpoints": {
            "files": "/api/files - Управління файлами",
            "indexing": "/api/indexing - Статус індексації", 
            "chat": "/api/chat - Чат з документами",
            "graph": "/api/graph - Робота з графом",
            "docs": "/docs - API документація"
        },
        "config": {
            "environment": settings.environment,
            "debug": settings.debug,
            "graphrag_model": settings.graphrag_llm_model,
            "embedding_model": settings.graphrag_embedding_model
        }
    })


# Health check endpoint
@app.get("/health")
async def health_check():
    """
    Перевірка здоров'я системи
    """
    
    try:
        # Перевірка доступності каталогів
        directories_status = {}
        directories = [
            ("upload", settings.upload_dir),
            ("output", settings.output_dir),
            ("metadata", settings.metadata_dir),
            ("cache", settings.cache_dir)
        ]
        
        for name, directory in directories:
            path = Path(directory)
            directories_status[name] = {
                "exists": path.exists(),
                "writable": path.exists() and os.access(path, os.W_OK),
                "path": str(path)
            }
        
        # Перевірка OpenAI API (базова)
        openai_status = {
            "api_key_configured": bool(
                settings.openai_api_key and 
                settings.openai_api_key != "sk-your-openai-api-key-here"
            ),
            "model": settings.graphrag_llm_model,
            "embedding_model": settings.graphrag_embedding_model
        }
        
        # Загальний статус
        is_healthy = (
            all(d["exists"] and d["writable"] for d in directories_status.values()) and
            openai_status["api_key_configured"]
        )
        
        status_code = 200 if is_healthy else 503
        
        return JSONResponse(
            status_code=status_code,
            content={
                "status": "healthy" if is_healthy else "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "directories": directories_status,
                "openai": openai_status,
                "version": "1.0.0"
            }
        )
        
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )


# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Обробник 404 помилок"""
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": f"Endpoint {request.url.path} not found",
            "path": request.url.path
        }
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """Обробник 500 помилок"""
    logger.error(f"Internal server error: {str(exc)}")
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred" if not settings.debug else str(exc)
        }
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Обробник HTTP помилок"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code
        }
    )


# Додаткові імпорти для health check
import os
from datetime import datetime


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
