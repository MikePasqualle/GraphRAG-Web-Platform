"""
Сервіс для роботи з файлами
Управління завантаженням, збереженням та метаданими файлів
"""

import os
import json
import uuid
import shutil
import aiofiles
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict, Any

from fastapi import UploadFile, HTTPException
from PyPDF2 import PdfReader
from docx import Document
import magic

from ..config import settings, FILE_STATUS, SUPPORTED_FILE_TYPES
from ..models.file import FileMetadata, IndexingProgress


class FileService:
    """Сервіс для управління файлами"""
    
    def __init__(self):
        self.upload_dir = Path(settings.upload_dir)
        self.metadata_dir = Path(settings.metadata_dir)
        self.output_dir = Path(settings.output_dir)
        
        # Створення каталогів
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Файл з метаданими
        self.metadata_file = self.metadata_dir / "files.json"
        
    async def upload_file(self, file: UploadFile) -> FileMetadata:
        """
        Завантаження файлу та збереження метаданих
        
        Args:
            file: UploadFile об'єкт з FastAPI
            
        Returns:
            FileMetadata: Метадані завантаженого файлу
            
        Raises:
            HTTPException: Якщо файл не валідний або сталася помилка
        """
        
        # Валідація файлу
        await self._validate_file(file)
        
        # Генерація унікального ID
        file_id = str(uuid.uuid4())
        
        # Отримання розширення файлу
        file_extension = Path(file.filename).suffix
        stored_filename = f"{file_id}{file_extension}"
        file_path = self.upload_dir / stored_filename
        
        try:
            # Збереження файлу
            async with aiofiles.open(file_path, 'wb') as f:
                content = await file.read()
                await f.write(content)
            
            # Створення метаданих
            file_metadata = FileMetadata(
                id=file_id,
                filename=stored_filename,
                original_filename=file.filename,
                size=len(content),
                content_type=file.content_type,
                upload_date=datetime.utcnow(),
                status=FILE_STATUS['UPLOADED'],
                file_path=str(file_path)
            )
            
            # Збереження метаданих
            await self._save_metadata(file_metadata)
            
            return file_metadata
            
        except Exception as e:
            # Видалення файлу у разі помилки
            if file_path.exists():
                file_path.unlink()
            raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")
    
    async def get_file_list(
        self, 
        page: int = 1, 
        per_page: int = 20,
        status_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Отримання списку файлів з пагінацією
        
        Args:
            page: Номер сторінки
            per_page: Кількість файлів на сторінку
            status_filter: Фільтр по статусу
            
        Returns:
            Dict з файлами та метаданими пагінації
        """
        
        files_data = await self._load_metadata()
        all_files = list(files_data.values())
        
        # Фільтрація по статусу
        if status_filter:
            all_files = [f for f in all_files if f.get('status') == status_filter]
        
        # Сортування по даті завантаження (новіші першими)
        all_files.sort(key=lambda x: x.get('upload_date', ''), reverse=True)
        
        # Пагінація
        total = len(all_files)
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        page_files = all_files[start_idx:end_idx]
        
        # Конвертація у FileMetadata
        files = [FileMetadata(**file_data) for file_data in page_files]
        
        return {
            "files": files,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": (total + per_page - 1) // per_page
        }
    
    async def get_file_by_id(self, file_id: str) -> Optional[FileMetadata]:
        """
        Отримання файлу за ID
        
        Args:
            file_id: Унікальний ідентифікатор файлу
            
        Returns:
            FileMetadata або None якщо файл не знайдено
        """
        
        files_data = await self._load_metadata()
        file_data = files_data.get(file_id)
        
        if file_data:
            return FileMetadata(**file_data)
        return None
    
    async def delete_file(self, file_id: str) -> bool:
        """
        Видалення файлу та всіх пов'язаних даних
        
        Args:
            file_id: Унікальний ідентифікатор файлу
            
        Returns:
            bool: True якщо файл успішно видалено
        """
        
        file_metadata = await self.get_file_by_id(file_id)
        if not file_metadata:
            return False
        
        try:
            # Видалення фізичного файлу
            file_path = Path(file_metadata.file_path)
            if file_path.exists():
                file_path.unlink()
            
            # Видалення output каталогу GraphRAG
            output_path = self.output_dir / file_id
            if output_path.exists():
                shutil.rmtree(output_path)
            
            # Видалення з метаданих
            files_data = await self._load_metadata()
            if file_id in files_data:
                del files_data[file_id]
                await self._save_metadata_dict(files_data)
            
            return True
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error deleting file: {str(e)}")
    
    async def update_file_status(
        self, 
        file_id: str, 
        status: str, 
        **kwargs
    ) -> Optional[FileMetadata]:
        """
        Оновлення статусу файлу та додаткових полів
        
        Args:
            file_id: Унікальний ідентифікатор файлу
            status: Новий статус
            **kwargs: Додаткові поля для оновлення
            
        Returns:
            FileMetadata: Оновлені метадані файлу
        """
        
        files_data = await self._load_metadata()
        if file_id not in files_data:
            return None
        
        # Оновлення статусу та інших полів
        files_data[file_id]['status'] = status
        for key, value in kwargs.items():
            files_data[file_id][key] = value
        
        await self._save_metadata_dict(files_data)
        
        return FileMetadata(**files_data[file_id])
    
    async def extract_text_content(self, file_metadata: FileMetadata) -> str:
        """
        Витягування текстового контенту з файлу
        
        Args:
            file_metadata: Метадані файлу
            
        Returns:
            str: Текстовий контент файлу
        """
        
        file_path = Path(file_metadata.file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        file_extension = file_path.suffix.lower()
        
        try:
            if file_extension == '.txt':
                async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                    return await f.read()
                    
            elif file_extension == '.pdf':
                return await self._extract_pdf_text(file_path)
                
            elif file_extension in ['.docx', '.doc']:
                return await self._extract_docx_text(file_path)
                
            else:
                raise ValueError(f"Unsupported file type: {file_extension}")
                
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error extracting text: {str(e)}")
    
    async def _validate_file(self, file: UploadFile):
        """Валідація завантажуваного файлу"""
        
        # Перевірка розміру
        if file.size and file.size > settings.upload_max_size:
            raise HTTPException(
                status_code=413, 
                detail=f"File too large. Max size: {settings.upload_max_size} bytes"
            )
        
        # Перевірка розширення
        file_extension = Path(file.filename).suffix.lower()
        allowed_extensions = [ext for exts in SUPPORTED_FILE_TYPES.values() for ext in exts]
        
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"File type {file_extension} not supported. Allowed: {allowed_extensions}"
            )
        
        # Перевірка MIME типу (якщо доступно)
        if file.content_type and file.content_type not in SUPPORTED_FILE_TYPES:
            # Спробуємо визначити тип за змістом
            content_preview = await file.read(1024)
            await file.seek(0)  # Повертаємося на початок
            
            try:
                detected_mime = magic.from_buffer(content_preview, mime=True)
                if detected_mime not in SUPPORTED_FILE_TYPES:
                    raise HTTPException(
                        status_code=400,
                        detail=f"File MIME type {detected_mime} not supported"
                    )
            except:
                # Якщо не вдалося визначити тип, продовжуємо
                pass
    
    async def _extract_pdf_text(self, file_path: Path) -> str:
        """Витягування тексту з PDF файлу"""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text.strip()
        except Exception as e:
            raise ValueError(f"Error reading PDF: {str(e)}")
    
    async def _extract_docx_text(self, file_path: Path) -> str:
        """Витягування тексту з DOCX файлу"""
        try:
            doc = Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text.strip()
        except Exception as e:
            raise ValueError(f"Error reading DOCX: {str(e)}")
    
    async def _load_metadata(self) -> Dict[str, Dict]:
        """Завантаження метаданих з файлу"""
        if not self.metadata_file.exists():
            return {}
        
        try:
            async with aiofiles.open(self.metadata_file, 'r') as f:
                content = await f.read()
                return json.loads(content)
        except Exception:
            return {}
    
    async def _save_metadata(self, file_metadata: FileMetadata):
        """Збереження метаданих файлу"""
        files_data = await self._load_metadata()
        files_data[file_metadata.id] = file_metadata.dict()
        await self._save_metadata_dict(files_data)
    
    async def _save_metadata_dict(self, files_data: Dict[str, Dict]):
        """Збереження словника метаданих у файл"""
        async with aiofiles.open(self.metadata_file, 'w') as f:
            await f.write(json.dumps(files_data, indent=2, default=str))
