"""
API endpoints для управління файлами
"""

from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query, BackgroundTasks
from fastapi.responses import JSONResponse

from ..models.file import (
    FileMetadata, FileUploadResponse, FileListResponse, 
    FileDeleteResponse, FileStatsResponse, IndexingProgress
)
from ..services.file_service import FileService
from ..services.graphrag_service import GraphRAGService


router = APIRouter(prefix="/api/files", tags=["files"])

# Dependency injection
def get_file_service() -> FileService:
    return FileService()

def get_graphrag_service() -> GraphRAGService:
    return GraphRAGService()


@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    file_service: FileService = Depends(get_file_service),
    graphrag_service: GraphRAGService = Depends(get_graphrag_service)
):
    """
    Завантаження файлу та автоматичний запуск індексації
    
    - **file**: Файл для завантаження (TXT, PDF, DOCX)
    - Автоматично запускає індексацію після успішного завантаження
    """
    
    try:
        # Завантаження файлу
        file_metadata = await file_service.upload_file(file)
        
        # Запуск індексації у фоновому режимі
        background_tasks.add_task(
            _start_indexing_background,
            file_metadata.id,
            graphrag_service
        )
        
        return FileUploadResponse(
            file_id=file_metadata.id,
            filename=file_metadata.original_filename,
            size=file_metadata.size,
            status=file_metadata.status,
            upload_date=file_metadata.upload_date,
            message="File uploaded successfully. Indexing started."
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=FileListResponse)
async def get_files(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Optional[str] = Query(None, description="Filter by status"),
    file_service: FileService = Depends(get_file_service)
):
    """
    Отримання списку файлів з пагінацією
    
    - **page**: Номер сторінки (від 1)
    - **per_page**: Кількість файлів на сторінку (1-100)
    - **status**: Фільтр по статусу (uploaded, indexing, completed, error)
    """
    
    try:
        result = await file_service.get_file_list(
            page=page,
            per_page=per_page,
            status_filter=status
        )
        
        return FileListResponse(
            files=result["files"],
            total=result["total"],
            page=result["page"],
            per_page=result["per_page"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{file_id}", response_model=FileMetadata)
async def get_file(
    file_id: str,
    file_service: FileService = Depends(get_file_service)
):
    """
    Отримання інформації про конкретний файл
    
    - **file_id**: Унікальний ідентифікатор файлу
    """
    
    file_metadata = await file_service.get_file_by_id(file_id)
    
    if not file_metadata:
        raise HTTPException(status_code=404, detail="File not found")
    
    return file_metadata


@router.delete("/{file_id}", response_model=FileDeleteResponse)
async def delete_file(
    file_id: str,
    file_service: FileService = Depends(get_file_service)
):
    """
    Видалення файлу та всіх пов'язаних даних
    
    - **file_id**: Унікальний ідентифікатор файлу
    - Видаляє файл, метадані та результати індексації
    """
    
    # Отримання інформації про файл перед видаленням
    file_metadata = await file_service.get_file_by_id(file_id)
    
    if not file_metadata:
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        success = await file_service.delete_file(file_id)
        
        if success:
            return FileDeleteResponse(
                file_id=file_id,
                filename=file_metadata.original_filename,
                deleted=True,
                message="File deleted successfully"
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to delete file")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{file_id}/stats", response_model=FileStatsResponse)
async def get_file_stats(
    file_id: str,
    file_service: FileService = Depends(get_file_service)
):
    """
    Отримання статистики файлу після індексації
    
    - **file_id**: Унікальний ідентифікатор файлу
    - Повертає кількість чанків, сутностей, зв'язків і спільнот
    """
    
    file_metadata = await file_service.get_file_by_id(file_id)
    
    if not file_metadata:
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileStatsResponse(
        file_id=file_metadata.id,
        filename=file_metadata.original_filename,
        status=file_metadata.status,
        chunks_count=file_metadata.chunks_count or 0,
        entities_count=file_metadata.entities_count or 0,
        relationships_count=file_metadata.relationships_count or 0,
        communities_count=file_metadata.communities_count or 0,
        error_message=file_metadata.error_message
    )


@router.post("/{file_id}/reindex")
async def reindex_file(
    file_id: str,
    background_tasks: BackgroundTasks,
    file_service: FileService = Depends(get_file_service),
    graphrag_service: GraphRAGService = Depends(get_graphrag_service)
):
    """
    Повторна індексація файлу
    
    - **file_id**: Унікальний ідентифікатор файлу
    - Запускає індексацію заново, навіть якщо файл вже був індексований
    """
    
    file_metadata = await file_service.get_file_by_id(file_id)
    
    if not file_metadata:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Оновлення статусу на "indexing"
    await file_service.update_file_status(
        file_id, 
        "indexing",
        error_message=None
    )
    
    # Запуск індексації у фоновому режимі
    background_tasks.add_task(
        _start_indexing_background,
        file_id,
        graphrag_service
    )
    
    return JSONResponse(
        content={
            "message": "Reindexing started",
            "file_id": file_id,
            "status": "indexing"
        }
    )


# Допоміжні функції

async def _start_indexing_background(file_id: str, graphrag_service: GraphRAGService):
    """
    Фонове завдання для запуску індексації
    """
    
    try:
        # Отримання метаданих файлу
        file_service = FileService()
        file_metadata = await file_service.get_file_by_id(file_id)
        
        if not file_metadata:
            raise Exception("File not found")
        
        # Оновлення статусу на "indexing"
        await file_service.update_file_status(file_id, "indexing")
        
        # Запуск індексації
        progress = await graphrag_service.start_indexing(file_metadata)
        
        # Логування початку індексації
        print(f"Indexing started for file {file_id}: {file_metadata.original_filename}")
        
    except Exception as e:
        # Обробка помилок
        print(f"Error starting indexing for file {file_id}: {str(e)}")
        
        try:
            file_service = FileService()
            await file_service.update_file_status(
                file_id, 
                "error",
                error_message=str(e)
            )
        except:
            pass
