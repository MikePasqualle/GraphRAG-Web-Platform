"""
API endpoints для управління індексацією
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse

from ..models.file import IndexingProgress
from ..services.file_service import FileService
from ..services.graphrag_service import GraphRAGService


router = APIRouter(prefix="/api/indexing", tags=["indexing"])


# Dependency injection
def get_file_service() -> FileService:
    return FileService()

def get_graphrag_service() -> GraphRAGService:
    return GraphRAGService()


@router.get("/status/{file_id}", response_model=IndexingProgress)
async def get_indexing_status(
    file_id: str,
    graphrag_service: GraphRAGService = Depends(get_graphrag_service),
    file_service: FileService = Depends(get_file_service)
):
    """
    Отримання статусу індексації файлу
    
    - **file_id**: Унікальний ідентифікатор файлу
    - Повертає поточний прогрес індексації, поточний крок і відсоток виконання
    """
    
    # Перевірка існування файлу
    file_metadata = await file_service.get_file_by_id(file_id)
    if not file_metadata:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Отримання статусу індексації
    progress = await graphrag_service.get_indexing_status(file_id)
    
    if not progress:
        # Якщо статус індексації не знайдено, створюємо базовий на основі статусу файлу
        from datetime import datetime
        
        if file_metadata.status == "uploaded":
            progress = IndexingProgress(
                file_id=file_id,
                status="uploaded",
                current_step="waiting",
                progress_percentage=0.0
            )
        elif file_metadata.status == "completed":
            progress = IndexingProgress(
                file_id=file_id,
                status="completed",
                current_step="finished",
                progress_percentage=100.0,
                completed_at=datetime.utcnow()
            )
        elif file_metadata.status == "error":
            progress = IndexingProgress(
                file_id=file_id,
                status="error",
                current_step="failed",
                progress_percentage=0.0,
                error_message=file_metadata.error_message
            )
        else:
            progress = IndexingProgress(
                file_id=file_id,
                status="unknown",
                current_step="unknown",
                progress_percentage=0.0
            )
    
    return progress


@router.get("/status")
async def get_all_indexing_statuses(
    graphrag_service: GraphRAGService = Depends(get_graphrag_service),
    file_service: FileService = Depends(get_file_service)
):
    """
    Отримання статусу індексації всіх файлів
    
    - Повертає список всіх файлів з їх статусами індексації
    """
    
    try:
        # Отримання всіх файлів
        files_result = await file_service.get_file_list(page=1, per_page=1000)
        all_files = files_result["files"]
        
        statuses = []
        
        for file_metadata in all_files:
            # Отримання детального статусу індексації
            progress = await graphrag_service.get_indexing_status(file_metadata.id)
            
            if not progress:
                # Створення базового статусу
                from datetime import datetime
                
                progress = IndexingProgress(
                    file_id=file_metadata.id,
                    status=file_metadata.status,
                    current_step="unknown",
                    progress_percentage=100.0 if file_metadata.status == "completed" else 0.0
                )
            
            # Додавання метаданих файлу
            status_data = progress.dict()
            status_data.update({
                "filename": file_metadata.original_filename,
                "file_size": file_metadata.size,
                "upload_date": file_metadata.upload_date,
                "chunks_count": file_metadata.chunks_count,
                "entities_count": file_metadata.entities_count,
                "relationships_count": file_metadata.relationships_count,
                "communities_count": file_metadata.communities_count
            })
            
            statuses.append(status_data)
        
        # Сортування за датою завантаження (новіші спочатку)
        statuses.sort(key=lambda x: x.get("upload_date", ""), reverse=True)
        
        return JSONResponse(content={
            "statuses": statuses,
            "total": len(statuses),
            "active_indexing": len([s for s in statuses if s["status"] == "indexing"]),
            "completed": len([s for s in statuses if s["status"] == "completed"]),
            "errors": len([s for s in statuses if s["status"] == "error"])
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/cancel/{file_id}")
async def cancel_indexing(
    file_id: str,
    file_service: FileService = Depends(get_file_service)
):
    """
    Скасування індексації файлу
    
    - **file_id**: Унікальний ідентифікатор файлу
    - Зупиняє процес індексації та відмічає файл як скасований
    """
    
    # Перевірка існування файлу
    file_metadata = await file_service.get_file_by_id(file_id)
    if not file_metadata:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Перевірка чи файл в процесі індексації
    if file_metadata.status != "indexing":
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot cancel indexing. File status: {file_metadata.status}"
        )
    
    try:
        # Оновлення статусу файлу
        await file_service.update_file_status(
            file_id,
            "cancelled",
            error_message="Indexing cancelled by user"
        )
        
        # TODO: Реальне зупинення процесу індексації
        # Це потребує додаткової реалізації для керування фоновими процесами
        
        return JSONResponse(content={
            "message": "Indexing cancelled",
            "file_id": file_id,
            "status": "cancelled"
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/retry/{file_id}")
async def retry_indexing(
    file_id: str,
    file_service: FileService = Depends(get_file_service),
    graphrag_service: GraphRAGService = Depends(get_graphrag_service)
):
    """
    Повторна спроба індексації файлу після помилки
    
    - **file_id**: Унікальний ідентифікатор файлу
    - Перезапускає індексацію для файлів зі статусом "error"
    """
    
    # Перевірка існування файлу
    file_metadata = await file_service.get_file_by_id(file_id)
    if not file_metadata:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Перевірка чи файл має статус помилки
    if file_metadata.status not in ["error", "cancelled"]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot retry indexing. File status: {file_metadata.status}"
        )
    
    try:
        # Оновлення статусу на "indexing"
        await file_service.update_file_status(
            file_id,
            "indexing",
            error_message=None
        )
        
        # Запуск індексації
        progress = await graphrag_service.start_indexing(file_metadata)
        
        return JSONResponse(content={
            "message": "Indexing restarted",
            "file_id": file_id,
            "status": "indexing",
            "progress": progress.dict()
        })
        
    except Exception as e:
        # Повернення статусу помилки у разі невдачі
        await file_service.update_file_status(
            file_id,
            "error",
            error_message=str(e)
        )
        
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/queue")
async def get_indexing_queue(
    file_service: FileService = Depends(get_file_service)
):
    """
    Отримання черги індексації
    
    - Повертає список файлів що очікують на індексацію або в процесі індексації
    """
    
    try:
        # Отримання файлів зі статусами "uploaded" та "indexing"
        files_result = await file_service.get_file_list(page=1, per_page=1000)
        all_files = files_result["files"]
        
        queue_files = [
            file for file in all_files 
            if file.status in ["uploaded", "indexing"]
        ]
        
        # Сортування: спочатку файли в процесі індексації, потім по даті завантаження
        queue_files.sort(key=lambda x: (
            x.status != "indexing",  # False (indexing) йде перед True (uploaded)
            x.upload_date
        ))
        
        return JSONResponse(content={
            "queue": [
                {
                    "file_id": file.id,
                    "filename": file.original_filename,
                    "status": file.status,
                    "upload_date": file.upload_date,
                    "size": file.size
                }
                for file in queue_files
            ],
            "total_in_queue": len(queue_files),
            "indexing_count": len([f for f in queue_files if f.status == "indexing"]),
            "waiting_count": len([f for f in queue_files if f.status == "uploaded"])
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
