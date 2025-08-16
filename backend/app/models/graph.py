"""
Pydantic моделі для графових даних
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime


class Entity(BaseModel):
    """Сутність у графі"""
    id: str
    name: str
    type: str  # person, organization, location, concept, etc.
    description: Optional[str] = None
    degree: int = 0  # кількість зв'язків
    community_id: Optional[str] = None
    
    # Координати для візуалізації
    x: Optional[float] = None
    y: Optional[float] = None
    
    # Додаткові атрибути
    attributes: Dict[str, Any] = {}
    
    # Метадані
    source_chunks: List[str] = []
    confidence_score: Optional[float] = None


class Relationship(BaseModel):
    """Зв'язок між сутностями"""
    id: str
    source_id: str
    target_id: str
    relationship_type: str
    description: Optional[str] = None
    weight: float = 1.0
    
    # Додаткові атрибути
    attributes: Dict[str, Any] = {}
    
    # Метадані
    source_chunks: List[str] = []
    confidence_score: Optional[float] = None


class Community(BaseModel):
    """Спільнота у графі"""
    id: str
    title: str
    description: Optional[str] = None
    level: int = 0
    size: int = 0
    entities: List[str] = []
    
    # Координати центру для візуалізації
    x: Optional[float] = None
    y: Optional[float] = None
    
    # Додаткові атрибути
    attributes: Dict[str, Any] = {}


class TextChunk(BaseModel):
    """Чанк тексту"""
    id: str
    text: str
    file_id: str
    start_index: int
    end_index: int
    
    # Ентітіз у цьому чанку
    entities: List[str] = []
    relationships: List[str] = []
    
    # Embedding (опціонально для візуалізації)
    embedding: Optional[List[float]] = None


class GraphData(BaseModel):
    """Повні дані графу для візуалізації"""
    entities: List[Entity]
    relationships: List[Relationship]
    communities: List[Community]
    chunks: List[TextChunk]
    
    # Метадані графу
    metadata: Dict[str, Any] = {}
    generated_at: datetime


class GraphStats(BaseModel):
    """Статистика графу"""
    file_id: str
    filename: str
    
    # Основні метрики
    entities_count: int
    relationships_count: int
    communities_count: int
    chunks_count: int
    
    # Детальна статистика сутностей
    entity_types: Dict[str, int] = {}  # тип -> кількість
    relationship_types: Dict[str, int] = {}  # тип -> кількість
    
    # Метрики графу
    density: float = 0.0  # щільність графу
    average_degree: float = 0.0  # середня кількість зв'язків на сутність
    clustering_coefficient: float = 0.0
    
    # Найбільші компоненти
    largest_component_size: int = 0
    components_count: int = 0


class GraphExportRequest(BaseModel):
    """Запит на експорт графу"""
    file_ids: List[str]
    format: str = "json"  # json, graphml, gexf
    include_embeddings: bool = False
    include_chunks: bool = True
    filter_entities: Optional[List[str]] = None  # фільтр по типах сутностей


class GraphExportResponse(BaseModel):
    """Відповідь на експорт графу"""
    export_id: str
    format: str
    file_url: str
    expires_at: datetime
    size_bytes: int


class GraphLayoutRequest(BaseModel):
    """Запит на розрахунок layout для візуалізації"""
    file_ids: List[str]
    algorithm: str = "force_directed"  # force_directed, circular, hierarchical
    iterations: int = 100
    include_communities: bool = True


class GraphLayoutResponse(BaseModel):
    """Відповідь з координатами для візуалізації"""
    entities: List[Entity]  # з координатами x, y
    communities: List[Community]  # з координатами центрів
    bounds: Dict[str, float]  # min_x, max_x, min_y, max_y для viewport
