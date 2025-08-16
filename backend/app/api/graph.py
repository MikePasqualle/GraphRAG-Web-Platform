"""
API endpoints для роботи з графом знань
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse, FileResponse
import tempfile
import json
from pathlib import Path

from ..models.graph import (
    GraphData, GraphStats, GraphExportRequest, GraphExportResponse,
    GraphLayoutRequest, GraphLayoutResponse
)
from ..services.file_service import FileService
from ..services.graphrag_service import GraphRAGService


router = APIRouter(prefix="/api/graph", tags=["graph"])


# Dependency injection
def get_file_service() -> FileService:
    return FileService()

def get_graphrag_service() -> GraphRAGService:
    return GraphRAGService()


@router.get("/data", response_model=GraphData)
async def get_graph_data(
    file_ids: List[str] = Query(..., description="List of file IDs to include in graph"),
    include_chunks: bool = Query(True, description="Include text chunks in response"),
    graphrag_service: GraphRAGService = Depends(get_graphrag_service),
    file_service: FileService = Depends(get_file_service)
):
    """
    Отримання даних графу для візуалізації
    
    - **file_ids**: Список ID файлів для включення в граф
    - **include_chunks**: Чи включати текстові чанки в відповідь
    - Повертає сутності, зв'язки, спільноти та чанки тексту
    """
    
    # Валідація файлів
    valid_file_ids = []
    for file_id in file_ids:
        file_metadata = await file_service.get_file_by_id(file_id)
        if file_metadata and file_metadata.status == "completed":
            valid_file_ids.append(file_id)
        elif file_metadata:
            # Файл існує, але не завершено індексацію
            continue
        else:
            raise HTTPException(
                status_code=404, 
                detail=f"File not found: {file_id}"
            )
    
    if not valid_file_ids:
        raise HTTPException(
            status_code=400,
            detail="No valid completed files found"
        )
    
    try:
        # Отримання даних графу
        graph_data = await graphrag_service.get_graph_data(valid_file_ids)
        
        # Видалення чанків якщо не потрібні
        if not include_chunks:
            graph_data.chunks = []
        
        return graph_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting graph data: {str(e)}")


@router.get("/stats/{file_id}", response_model=GraphStats)
async def get_graph_stats(
    file_id: str,
    graphrag_service: GraphRAGService = Depends(get_graphrag_service),
    file_service: FileService = Depends(get_file_service)
):
    """
    Отримання статистики графу для конкретного файлу
    
    - **file_id**: ID файлу
    - Повертає детальну статистику: кількість сутностей, зв'язків, спільнот тощо
    """
    
    # Перевірка існування файлу
    file_metadata = await file_service.get_file_by_id(file_id)
    if not file_metadata:
        raise HTTPException(status_code=404, detail="File not found")
    
    if file_metadata.status != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"File not ready. Status: {file_metadata.status}"
        )
    
    try:
        # Отримання базової статистики з метаданих
        stats = GraphStats(
            file_id=file_id,
            filename=file_metadata.original_filename,
            entities_count=file_metadata.entities_count or 0,
            relationships_count=file_metadata.relationships_count or 0,
            communities_count=file_metadata.communities_count or 0,
            chunks_count=file_metadata.chunks_count or 0
        )
        
        # Додаткова деталізована статистика
        try:
            graph_data = await graphrag_service.get_graph_data([file_id])
            
            # Аналіз типів сутностей
            entity_types = {}
            for entity in graph_data.entities:
                entity_type = entity.type
                entity_types[entity_type] = entity_types.get(entity_type, 0) + 1
            
            # Аналіз типів зв'язків
            relationship_types = {}
            for rel in graph_data.relationships:
                rel_type = rel.relationship_type
                relationship_types[rel_type] = relationship_types.get(rel_type, 0) + 1
            
            # Розрахунок метрик графу
            if graph_data.entities and graph_data.relationships:
                total_nodes = len(graph_data.entities)
                total_edges = len(graph_data.relationships)
                
                # Щільність графу (density = 2*edges / (nodes*(nodes-1)))
                max_edges = total_nodes * (total_nodes - 1)
                density = (2 * total_edges / max_edges) if max_edges > 0 else 0
                
                # Середня кількість зв'язків на вузол
                average_degree = (2 * total_edges / total_nodes) if total_nodes > 0 else 0
                
                stats.entity_types = entity_types
                stats.relationship_types = relationship_types
                stats.density = round(density, 4)
                stats.average_degree = round(average_degree, 2)
            
        except Exception as e:
            # Якщо не вдалося отримати деталізовану статистику, повертаємо базову
            print(f"Warning: Could not get detailed stats for {file_id}: {e}")
        
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting graph stats: {str(e)}")


@router.post("/export", response_model=GraphExportResponse)
async def export_graph(
    request: GraphExportRequest,
    graphrag_service: GraphRAGService = Depends(get_graphrag_service),
    file_service: FileService = Depends(get_file_service)
):
    """
    Експорт графу в різних форматах
    
    - **file_ids**: Список ID файлів для експорту
    - **format**: Формат експорту ("json", "graphml", "gexf")
    - **include_embeddings**: Чи включати ембеддинги
    - **include_chunks**: Чи включати текстові чанки
    - **filter_entities**: Фільтр по типах сутностей
    """
    
    # Валідація файлів
    valid_file_ids = []
    for file_id in request.file_ids:
        file_metadata = await file_service.get_file_by_id(file_id)
        if file_metadata and file_metadata.status == "completed":
            valid_file_ids.append(file_id)
    
    if not valid_file_ids:
        raise HTTPException(
            status_code=400,
            detail="No valid completed files found"
        )
    
    try:
        # Отримання даних графу
        graph_data = await graphrag_service.get_graph_data(valid_file_ids)
        
        # Фільтрація сутностей якщо потрібно
        if request.filter_entities:
            graph_data.entities = [
                entity for entity in graph_data.entities
                if entity.type in request.filter_entities
            ]
            
            # Фільтрація зв'язків відповідно до сутностей
            entity_ids = {entity.id for entity in graph_data.entities}
            graph_data.relationships = [
                rel for rel in graph_data.relationships
                if rel.source_id in entity_ids and rel.target_id in entity_ids
            ]
        
        # Видалення чанків та ембеддингів якщо не потрібні
        if not request.include_chunks:
            graph_data.chunks = []
        
        if not request.include_embeddings:
            for chunk in graph_data.chunks:
                chunk.embedding = None
        
        # Створення тимчасового файлу для експорту
        export_id = f"export_{hash(str(valid_file_ids))}_{request.format}"
        
        if request.format == "json":
            export_data = graph_data.dict()
            filename = f"{export_id}.json"
            
            temp_file = tempfile.NamedTemporaryFile(
                mode='w', 
                suffix='.json', 
                delete=False,
                encoding='utf-8'
            )
            
            json.dump(export_data, temp_file, indent=2, default=str)
            temp_file.close()
            
        elif request.format == "graphml":
            # Конвертація в GraphML
            filename = f"{export_id}.graphml"
            temp_file = tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.graphml',
                delete=False,
                encoding='utf-8'
            )
            
            # Створення NetworkX графу та експорт в GraphML
            import networkx as nx
            
            G = nx.Graph()
            
            # Додавання вузлів
            for entity in graph_data.entities:
                G.add_node(
                    entity.id,
                    name=entity.name,
                    type=entity.type,
                    description=entity.description or "",
                    degree=entity.degree
                )
            
            # Додавання ребер
            for rel in graph_data.relationships:
                G.add_edge(
                    rel.source_id,
                    rel.target_id,
                    relationship=rel.relationship_type,
                    description=rel.description or "",
                    weight=rel.weight
                )
            
            nx.write_graphml(G, temp_file.name)
            temp_file.close()
            
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported export format: {request.format}"
            )
        
        # Розрахунок розміру файлу
        file_size = Path(temp_file.name).stat().st_size
        
        from datetime import datetime, timedelta
        
        return GraphExportResponse(
            export_id=export_id,
            format=request.format,
            file_url=f"/api/graph/download/{export_id}",
            expires_at=datetime.utcnow() + timedelta(hours=24),
            size_bytes=file_size
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting graph: {str(e)}")


@router.get("/download/{export_id}")
async def download_export(export_id: str):
    """
    Завантаження експортованого файлу графу
    
    - **export_id**: ID експорту з попереднього запиту
    """
    
    # Знаходження тимчасового файлу
    # В реальній реалізації потрібно зберігати mapping export_id -> file_path
    
    raise HTTPException(status_code=404, detail="Export file not found or expired")


@router.post("/layout", response_model=GraphLayoutResponse)
async def calculate_graph_layout(
    request: GraphLayoutRequest,
    graphrag_service: GraphRAGService = Depends(get_graphrag_service),
    file_service: FileService = Depends(get_file_service)
):
    """
    Розрахунок координат для візуалізації графу
    
    - **file_ids**: Список ID файлів
    - **algorithm**: Алгоритм layout ("force_directed", "circular", "hierarchical")
    - **iterations**: Кількість ітерацій для алгоритму
    - **include_communities**: Чи включати позиції спільнот
    """
    
    # Валідація файлів
    valid_file_ids = []
    for file_id in request.file_ids:
        file_metadata = await file_service.get_file_by_id(file_id)
        if file_metadata and file_metadata.status == "completed":
            valid_file_ids.append(file_id)
    
    if not valid_file_ids:
        raise HTTPException(
            status_code=400,
            detail="No valid completed files found"
        )
    
    try:
        # Отримання даних графу
        graph_data = await graphrag_service.get_graph_data(valid_file_ids)
        
        if not graph_data.entities:
            raise HTTPException(
                status_code=400,
                detail="No entities found in the specified files"
            )
        
        # Створення NetworkX графу
        import networkx as nx
        import random
        
        G = nx.Graph()
        
        # Додавання вузлів
        for entity in graph_data.entities:
            G.add_node(entity.id, **entity.dict())
        
        # Додавання ребер
        for rel in graph_data.relationships:
            if rel.source_id in G.nodes and rel.target_id in G.nodes:
                G.add_edge(rel.source_id, rel.target_id, weight=rel.weight)
        
        # Розрахунок позицій залежно від алгоритму
        if request.algorithm == "force_directed":
            pos = nx.spring_layout(
                G, 
                iterations=request.iterations,
                seed=42
            )
        elif request.algorithm == "circular":
            pos = nx.circular_layout(G)
        elif request.algorithm == "hierarchical":
            # Спроба створити ієрархічний layout
            try:
                pos = nx.nx_agraph.graphviz_layout(G, prog='dot')
            except:
                # Fallback до spring layout
                pos = nx.spring_layout(G, iterations=request.iterations, seed=42)
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported layout algorithm: {request.algorithm}"
            )
        
        # Оновлення координат у сутностях
        updated_entities = []
        for entity in graph_data.entities:
            if entity.id in pos:
                entity.x = float(pos[entity.id][0])
                entity.y = float(pos[entity.id][1])
            else:
                # Випадкові координати для ізольованих вузлів
                entity.x = random.uniform(-1, 1)
                entity.y = random.uniform(-1, 1)
            
            updated_entities.append(entity)
        
        # Розрахунок позицій спільнот (якщо потрібно)
        updated_communities = []
        if request.include_communities:
            for community in graph_data.communities:
                # Знаходження центру мас сутностей спільноти
                community_entities = [
                    e for e in updated_entities 
                    if e.community_id == community.id
                ]
                
                if community_entities:
                    avg_x = sum(e.x for e in community_entities) / len(community_entities)
                    avg_y = sum(e.y for e in community_entities) / len(community_entities)
                    
                    community.x = avg_x
                    community.y = avg_y
                
                updated_communities.append(community)
        
        # Розрахунок bounds для viewport
        all_x = [e.x for e in updated_entities if e.x is not None]
        all_y = [e.y for e in updated_entities if e.y is not None]
        
        bounds = {
            "min_x": min(all_x) if all_x else -1,
            "max_x": max(all_x) if all_x else 1,
            "min_y": min(all_y) if all_y else -1,
            "max_y": max(all_y) if all_y else 1
        }
        
        return GraphLayoutResponse(
            entities=updated_entities,
            communities=updated_communities,
            bounds=bounds
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating layout: {str(e)}")


@router.get("/search")
async def search_graph(
    query: str = Query(..., description="Search query"),
    file_ids: List[str] = Query(..., description="List of file IDs to search"),
    entity_types: Optional[List[str]] = Query(None, description="Filter by entity types"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of results"),
    graphrag_service: GraphRAGService = Depends(get_graphrag_service),
    file_service: FileService = Depends(get_file_service)
):
    """
    Пошук по графу знань
    
    - **query**: Пошукова фраза
    - **file_ids**: Список ID файлів для пошуку
    - **entity_types**: Фільтр по типах сутностей
    - **limit**: Максимальна кількість результатів
    """
    
    # Валідація файлів
    valid_file_ids = []
    for file_id in file_ids:
        file_metadata = await file_service.get_file_by_id(file_id)
        if file_metadata and file_metadata.status == "completed":
            valid_file_ids.append(file_id)
    
    if not valid_file_ids:
        raise HTTPException(
            status_code=400,
            detail="No valid completed files found"
        )
    
    try:
        # Отримання даних графу
        graph_data = await graphrag_service.get_graph_data(valid_file_ids)
        
        # Простий текстовий пошук по сутностях
        query_lower = query.lower()
        matching_entities = []
        
        for entity in graph_data.entities:
            # Перевірка фільтру типів
            if entity_types and entity.type not in entity_types:
                continue
            
            # Пошук у назві та описі
            score = 0
            if query_lower in entity.name.lower():
                score += 2
            if entity.description and query_lower in entity.description.lower():
                score += 1
            
            if score > 0:
                matching_entities.append({
                    "entity": entity,
                    "score": score
                })
        
        # Сортування за релевантністю
        matching_entities.sort(key=lambda x: x["score"], reverse=True)
        
        # Обмеження результатів
        matching_entities = matching_entities[:limit]
        
        # Знаходження пов'язаних зв'язків
        entity_ids = {item["entity"].id for item in matching_entities}
        related_relationships = [
            rel for rel in graph_data.relationships
            if rel.source_id in entity_ids or rel.target_id in entity_ids
        ]
        
        return JSONResponse(content={
            "query": query,
            "total_matches": len(matching_entities),
            "entities": [
                {
                    **item["entity"].dict(),
                    "relevance_score": item["score"]
                }
                for item in matching_entities
            ],
            "relationships": [rel.dict() for rel in related_relationships],
            "file_ids": valid_file_ids
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching graph: {str(e)}")
