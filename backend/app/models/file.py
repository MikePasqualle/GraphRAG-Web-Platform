"""
Pydantic моделі для роботи з файлами
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, validator
from pathlib import Path


class FileMetadata(BaseModel):
    """Метадані файлу"""
    id: str
    filename: str
    original_filename: str
    size: int
    content_type: str
    upload_date: datetime
    status: str  # uploaded, indexing, completed, error, cancelled
    error_message: Optional[str] = None
    
    # GraphRAG результати
    chunks_count: Optional[int] = None
    entities_count: Optional[int] = None
    relationships_count: Optional[int] = None
    communities_count: Optional[int] = None
    
    # Шляхи до файлів
    file_path: str
    output_path: Optional[str] = None
    
    @validator('filename')
    def validate_filename(cls, v):
        """Валідація імені файлу"""
        if not v or len(v.strip()) == 0:
            raise ValueError('Filename cannot be empty')
        return v.strip()
    
    @validator('size')
    def validate_size(cls, v):
        """Валідація розміру файлу"""
        if v <= 0:
            raise ValueError('File size must be positive')
        return v


class FileUploadRequest(BaseModel):
    """Запит на завантаження файлу"""
    filename: str
    content_type: str
    size: Optional[int] = None
    
    @validator('filename')
    def validate_filename(cls, v):
        """Валідація імені файлу"""
        if not v or len(v.strip()) == 0:
            raise ValueError('Filename cannot be empty')
        
        # Перевірка розширення файлу
        allowed_extensions = ['.txt', '.pdf', '.docx', '.doc']
        file_ext = Path(v).suffix.lower()
        if file_ext not in allowed_extensions:
            raise ValueError(f'File type {file_ext} not supported. Allowed: {allowed_extensions}')
        
        return v.strip()


class FileUploadResponse(BaseModel):
    """Відповідь на завантаження файлу"""
    file_id: str
    filename: str
    size: int
    status: str
    upload_date: datetime
    message: str


class FileListResponse(BaseModel):
    """Список файлів"""
    files: List[FileMetadata]
    total: int
    page: int
    per_page: int


class FileDeleteResponse(BaseModel):
    """Відповідь на видалення файлу"""
    file_id: str
    filename: str
    deleted: bool
    message: str


class FileStatsResponse(BaseModel):
    """Статистика файлу після індексації"""
    file_id: str
    filename: str
    status: str
    chunks_count: int
    entities_count: int
    relationships_count: int
    communities_count: int
    processing_time: Optional[float] = None  # в секундах
    error_message: Optional[str] = None


class IndexingProgress(BaseModel):
    """Прогрес індексації"""
    file_id: str
    status: str  # uploaded, indexing, completed, error
    current_step: str  # chunking, entity_extraction, relationships, communities
    progress_percentage: float  # 0-100
    estimated_remaining: Optional[int] = None  # секунди
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
