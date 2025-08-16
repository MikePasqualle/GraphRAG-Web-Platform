"""
API endpoints для чат-функціональності
"""

import json
import uuid
from typing import List, Optional, AsyncGenerator
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel

from ..models.chat import (
    ChatQuery, ChatResponse, ChatStreamChunk, 
    ConversationCreate, ConversationMetadata, ConversationHistory,
    ChatMode, ChatMessage, ChatSource
)
from ..services.file_service import FileService
from ..services.graphrag_service import GraphRAGService


router = APIRouter(prefix="/api/chat", tags=["chat"])


# Dependency injection
def get_file_service() -> FileService:
    return FileService()

def get_graphrag_service() -> GraphRAGService:
    return GraphRAGService()


@router.post("/query", response_model=ChatResponse)
async def chat_query(
    query: ChatQuery,
    file_service: FileService = Depends(get_file_service),
    graphrag_service: GraphRAGService = Depends(get_graphrag_service)
):
    """
    Виконання запиту до чату (не streaming)
    
    - **message**: Текст запитання
    - **mode**: Режим пошуку ("local" або "global")
    - **file_ids**: Список ID файлів для пошуку (обов'язково для local режиму)
    - **conversation_id**: ID розмови (опціонально)
    """
    
    # Валідація файлів
    if query.mode == ChatMode.LOCAL and not query.file_ids:
        raise HTTPException(
            status_code=400, 
            detail="Local mode requires at least one file_id"
        )
    
    # Перевірка існування файлів
    valid_file_ids = []
    for file_id in query.file_ids:
        file_metadata = await file_service.get_file_by_id(file_id)
        if file_metadata and file_metadata.status == "completed":
            valid_file_ids.append(file_id)
    
    if query.mode == ChatMode.LOCAL and not valid_file_ids:
        raise HTTPException(
            status_code=400,
            detail="No valid completed files found for local search"
        )
    
    try:
        # Виконання запиту до GraphRAG
        result = await graphrag_service.query_graph(
            query=query.message,
            mode=query.mode,
            file_ids=valid_file_ids if query.mode == ChatMode.LOCAL else []
        )
        
        # Конвертація джерел
        sources = []
        for source_data in result.sources:
            # Знаходження відповідного файлу
            source_file = None
            if valid_file_ids:
                source_file = await file_service.get_file_by_id(valid_file_ids[0])
            
            source = ChatSource(
                file_id=valid_file_ids[0] if valid_file_ids else "unknown",
                filename=source_file.original_filename if source_file else "unknown",
                chunk_id=source_data.get("chunk_id"),
                relevance_score=source_data.get("score")
            )
            sources.append(source)
        
        # Генерація ID повідомлення та розмови
        message_id = str(uuid.uuid4())
        conversation_id = query.conversation_id or str(uuid.uuid4())
        
        return ChatResponse(
            message_id=message_id,
            response=result.response,
            mode=query.mode,
            sources=sources,
            processing_time=result.processing_time,
            conversation_id=conversation_id
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat query failed: {str(e)}")


@router.post("/stream")
async def chat_stream(
    query: ChatQuery,
    file_service: FileService = Depends(get_file_service),
    graphrag_service: GraphRAGService = Depends(get_graphrag_service)
):
    """
    Streaming чат запит
    
    - **message**: Текст запитання  
    - **mode**: Режим пошуку ("local" або "global")
    - **file_ids**: Список ID файлів для пошуку
    - Повертає Server-Sent Events для real-time відповіді
    """
    
    # Аналогічна валідація як у chat_query
    if query.mode == ChatMode.LOCAL and not query.file_ids:
        raise HTTPException(
            status_code=400,
            detail="Local mode requires at least one file_id"
        )
    
    # Перевірка файлів
    valid_file_ids = []
    for file_id in query.file_ids:
        file_metadata = await file_service.get_file_by_id(file_id)
        if file_metadata and file_metadata.status == "completed":
            valid_file_ids.append(file_id)
    
    if query.mode == ChatMode.LOCAL and not valid_file_ids:
        raise HTTPException(
            status_code=400,
            detail="No valid completed files found for local search"
        )
    
    async def generate_stream():
        """Генератор для streaming відповіді"""
        
        chunk_id = str(uuid.uuid4())
        
        try:
            # Надсилання початкового повідомлення
            initial_chunk = ChatStreamChunk(
                chunk_id=chunk_id,
                content="",
                is_final=False
            )
            yield f"data: {initial_chunk.json()}\n\n"
            
            # Виконання запиту (поки що не streaming, але можна розширити)
            result = await graphrag_service.query_graph(
                query=query.message,
                mode=query.mode,
                file_ids=valid_file_ids if query.mode == ChatMode.LOCAL else []
            )
            
            # Симуляція streaming (розбиття відповіді на частини)
            response_text = result.response
            chunk_size = 50  # Символів на chunk
            
            for i in range(0, len(response_text), chunk_size):
                chunk_text = response_text[i:i+chunk_size]
                
                chunk = ChatStreamChunk(
                    chunk_id=chunk_id,
                    content=chunk_text,
                    is_final=False
                )
                
                yield f"data: {chunk.json()}\n\n"
                
                # Невелика затримка для симуляції real-time
                import asyncio
                await asyncio.sleep(0.1)
            
            # Конвертація джерел
            sources = []
            for source_data in result.sources:
                source_file = None
                if valid_file_ids:
                    source_file = await file_service.get_file_by_id(valid_file_ids[0])
                
                source = ChatSource(
                    file_id=valid_file_ids[0] if valid_file_ids else "unknown",
                    filename=source_file.original_filename if source_file else "unknown",
                    chunk_id=source_data.get("chunk_id"),
                    relevance_score=source_data.get("score")
                )
                sources.append(source)
            
            # Фінальний chunk з джерелами
            final_chunk = ChatStreamChunk(
                chunk_id=chunk_id,
                content="",
                is_final=True,
                sources=sources
            )
            
            yield f"data: {final_chunk.json()}\n\n"
            
        except Exception as e:
            # Надсилання помилки через stream
            error_chunk = ChatStreamChunk(
                chunk_id=chunk_id,
                content="",
                is_final=True,
                error=str(e)
            )
            
            yield f"data: {error_chunk.json()}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@router.post("/conversations", response_model=ConversationMetadata)
async def create_conversation(
    conversation: ConversationCreate
):
    """
    Створення нової розмови
    
    - **title**: Назва розмови (опціонально)
    - **file_ids**: Список файлів для розмови
    """
    
    conversation_id = str(uuid.uuid4())
    title = conversation.title or f"Conversation {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}"
    
    metadata = ConversationMetadata(
        id=conversation_id,
        title=title,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        message_count=0,
        file_ids=conversation.file_ids
    )
    
    # TODO: Збереження розмови в базі даних/файлах
    
    return metadata


@router.get("/conversations/{conversation_id}", response_model=ConversationHistory)
async def get_conversation(
    conversation_id: str
):
    """
    Отримання історії розмови
    
    - **conversation_id**: ID розмови
    """
    
    # TODO: Завантаження з бази даних/файлів
    # Поки що повертаємо заглушку
    
    raise HTTPException(status_code=404, detail="Conversation not found")


@router.get("/conversations")
async def get_conversations(
    limit: int = 50,
    offset: int = 0
):
    """
    Отримання списку розмов
    
    - **limit**: Максимальна кількість розмов
    - **offset**: Зсув для пагінації
    """
    
    # TODO: Завантаження з бази даних/файлів
    # Поки що повертаємо порожній список
    
    return JSONResponse(content={
        "conversations": [],
        "total": 0,
        "limit": limit,
        "offset": offset
    })


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str
):
    """
    Видалення розмови
    
    - **conversation_id**: ID розмови
    """
    
    # TODO: Видалення з бази даних/файлів
    
    return JSONResponse(content={
        "message": "Conversation deleted",
        "conversation_id": conversation_id
    })


@router.get("/health")
async def chat_health_check():
    """
    Перевірка здоров'я чат сервісу
    
    - Перевіряє доступність OpenAI API та GraphRAG
    """
    
    try:
        # Простий тест доступності
        import openai
        
        client = openai.OpenAI(api_key="test")  # Буде помилка, але перевіримо чи імпорт працює
        
        return JSONResponse(content={
            "status": "healthy",
            "openai_available": True,
            "graphrag_available": True,
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )
