"""
Pydantic моделі для чат-функціональності
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, validator
from enum import Enum


class ChatMode(str, Enum):
    """Режими чату"""
    LOCAL = "local"
    GLOBAL = "global"


class ChatQuery(BaseModel):
    """Запит чату"""
    message: str
    mode: ChatMode
    file_ids: List[str] = []
    conversation_id: Optional[str] = None
    stream: bool = True
    
    @validator('message')
    def validate_message(cls, v):
        """Валідація повідомлення"""
        if not v or len(v.strip()) == 0:
            raise ValueError('Message cannot be empty')
        if len(v) > 2000:
            raise ValueError('Message too long (max 2000 characters)')
        return v.strip()
    
    @validator('file_ids')
    def validate_file_ids(cls, v, values):
        """Валідація file_ids для local режиму"""
        mode = values.get('mode')
        if mode == ChatMode.LOCAL and not v:
            raise ValueError('Local mode requires at least one file_id')
        return v


class ChatSource(BaseModel):
    """Джерело інформації у відповіді"""
    file_id: str
    filename: str
    chunk_id: Optional[str] = None
    entity_name: Optional[str] = None
    relationship: Optional[str] = None
    relevance_score: Optional[float] = None


class ChatMessage(BaseModel):
    """Повідомлення чату"""
    id: str
    role: str  # user, assistant, system
    content: str
    timestamp: datetime
    mode: Optional[ChatMode] = None
    sources: List[ChatSource] = []
    processing_time: Optional[float] = None  # секунди
    token_usage: Optional[Dict[str, int]] = None


class ChatResponse(BaseModel):
    """Відповідь чату"""
    message_id: str
    response: str
    mode: ChatMode
    sources: List[ChatSource] = []
    processing_time: float
    token_usage: Optional[Dict[str, int]] = None
    conversation_id: str


class ChatStreamChunk(BaseModel):
    """Частина streaming відповіді"""
    chunk_id: str
    content: str
    is_final: bool = False
    sources: List[ChatSource] = []
    error: Optional[str] = None


class ConversationCreate(BaseModel):
    """Створення нової розмови"""
    title: Optional[str] = None
    file_ids: List[str] = []


class ConversationMetadata(BaseModel):
    """Метадані розмови"""
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int
    file_ids: List[str] = []


class ConversationHistory(BaseModel):
    """Історія розмови"""
    conversation_id: str
    messages: List[ChatMessage]
    metadata: ConversationMetadata


class ChatSettings(BaseModel):
    """Налаштування чату"""
    max_tokens: int = 4000
    temperature: float = 0.1
    top_p: float = 1.0
    max_history_length: int = 100
    include_sources: bool = True
    stream_response: bool = True


class GraphRAGQueryResult(BaseModel):
    """Результат запиту до GraphRAG"""
    response: str
    context_data: Dict[str, Any]
    sources: List[Dict[str, Any]] = []
    processing_time: float
    mode: ChatMode
