"""
Сервіс для інтеграції з GraphRAG
Управління індексацією та запитами до графу знань
"""

import os
import json
import asyncio
import tempfile
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional, AsyncGenerator
import pandas as pd
import networkx as nx

from graphrag.query.indexer_adapters import read_indexer_entities, read_indexer_relationships
from graphrag.query.llm.oai.chat_openai import ChatOpenAI
from graphrag.query.llm.oai.embedding import OpenAIEmbedding
from graphrag.query.structured_search.global_search.community_context import GlobalCommunityContext
from graphrag.query.structured_search.global_search.search import GlobalSearch
from graphrag.query.structured_search.local_search.mixed_context import LocalSearchMixedContext
from graphrag.query.structured_search.local_search.search import LocalSearch

from ..config import settings, GRAPHRAG_CONFIG
from ..models.file import FileMetadata, IndexingProgress
from ..models.chat import ChatMode, GraphRAGQueryResult
from ..models.graph import GraphData, Entity, Relationship, Community, TextChunk


class GraphRAGService:
    """Сервіс для роботи з GraphRAG"""
    
    def __init__(self):
        self.output_dir = Path(settings.output_dir)
        self.cache_dir = Path(settings.cache_dir)
        
        # Налаштування OpenAI клієнтів
        self.llm = ChatOpenAI(
            api_key=settings.openai_api_key,
            model=settings.graphrag_llm_model,
            api_base="https://api.openai.com/v1",
            max_tokens=settings.graphrag_max_completion_tokens,
            temperature=0.1
        )
        
        self.embeddings = OpenAIEmbedding(
            api_key=settings.openai_api_key,
            api_base="https://api.openai.com/v1",
            model=settings.graphrag_embedding_model,
            dimensions=3072
        )
        
    async def start_indexing(self, file_metadata: FileMetadata) -> IndexingProgress:
        """
        Запуск індексації файлу через GraphRAG
        
        Args:
            file_metadata: Метадані файлу для індексації
            
        Returns:
            IndexingProgress: Початковий статус індексації
        """
        
        progress = IndexingProgress(
            file_id=file_metadata.id,
            status="indexing",
            current_step="preparing",
            progress_percentage=0.0,
            started_at=datetime.utcnow()
        )
        
        # Запуск фонового завдання індексації
        asyncio.create_task(self._run_indexing_pipeline(file_metadata, progress))
        
        return progress
    
    async def get_indexing_status(self, file_id: str) -> Optional[IndexingProgress]:
        """
        Отримання статусу індексації
        
        Args:
            file_id: ID файлу
            
        Returns:
            IndexingProgress або None
        """
        
        # Завантаження статусу з файлу або кешу
        status_file = self.cache_dir / f"indexing_status_{file_id}.json"
        
        if status_file.exists():
            try:
                with open(status_file, 'r') as f:
                    data = json.load(f)
                    return IndexingProgress(**data)
            except:
                pass
        
        return None
    
    async def query_graph(
        self, 
        query: str, 
        mode: ChatMode, 
        file_ids: List[str]
    ) -> GraphRAGQueryResult:
        """
        Виконання запиту до графу знань
        
        Args:
            query: Текст запиту
            mode: Режим пошуку (local/global)
            file_ids: Список ID файлів для пошуку
            
        Returns:
            GraphRAGQueryResult: Результат запиту
        """
        
        start_time = datetime.utcnow()
        
        try:
            if mode == ChatMode.LOCAL:
                result = await self._local_search(query, file_ids)
            else:
                result = await self._global_search(query, file_ids)
                
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            return GraphRAGQueryResult(
                response=result["response"],
                context_data=result.get("context", {}),
                sources=result.get("sources", []),
                processing_time=processing_time,
                mode=mode
            )
            
        except Exception as e:
            raise Exception(f"Error querying graph: {str(e)}")
    
    async def get_graph_data(self, file_ids: List[str]) -> GraphData:
        """
        Отримання даних графу для візуалізації
        
        Args:
            file_ids: Список ID файлів
            
        Returns:
            GraphData: Дані графу для візуалізації
        """
        
        entities = []
        relationships = []
        communities = []
        chunks = []
        
        for file_id in file_ids:
            file_output_dir = self.output_dir / file_id / "artifacts"
            
            if not file_output_dir.exists():
                continue
            
            # Завантаження сутностей
            entities_file = file_output_dir / "create_final_entities.parquet"
            if entities_file.exists():
                df_entities = pd.read_parquet(entities_file)
                for _, row in df_entities.iterrows():
                    entity = Entity(
                        id=str(row.get('id', '')),
                        name=row.get('name', ''),
                        type=row.get('type', 'unknown'),
                        description=row.get('description', ''),
                        degree=int(row.get('degree', 0)),
                        community_id=str(row.get('community', '')) if 'community' in row else None
                    )
                    entities.append(entity)
            
            # Завантаження зв'язків
            relationships_file = file_output_dir / "create_final_relationships.parquet"
            if relationships_file.exists():
                df_relationships = pd.read_parquet(relationships_file)
                for _, row in df_relationships.iterrows():
                    relationship = Relationship(
                        id=str(row.get('id', '')),
                        source_id=str(row.get('source', '')),
                        target_id=str(row.get('target', '')),
                        relationship_type=row.get('description', 'related'),
                        description=row.get('description', ''),
                        weight=float(row.get('weight', 1.0))
                    )
                    relationships.append(relationship)
            
            # Завантаження спільнот
            communities_file = file_output_dir / "create_final_communities.parquet"
            if communities_file.exists():
                df_communities = pd.read_parquet(communities_file)
                for _, row in df_communities.iterrows():
                    community = Community(
                        id=str(row.get('id', '')),
                        title=row.get('title', ''),
                        description=row.get('full_content', ''),
                        level=int(row.get('level', 0)),
                        size=int(row.get('size', 0))
                    )
                    communities.append(community)
            
            # Завантаження чанків
            chunks_file = file_output_dir / "create_final_text_units.parquet"
            if chunks_file.exists():
                df_chunks = pd.read_parquet(chunks_file)
                for _, row in df_chunks.iterrows():
                    chunk = TextChunk(
                        id=str(row.get('id', '')),
                        text=row.get('text', ''),
                        file_id=file_id,
                        start_index=int(row.get('n_tokens', 0)),
                        end_index=int(row.get('n_tokens', 0))
                    )
                    chunks.append(chunk)
        
        return GraphData(
            entities=entities,
            relationships=relationships,
            communities=communities,
            chunks=chunks,
            generated_at=datetime.utcnow()
        )
    
    async def _run_indexing_pipeline(
        self, 
        file_metadata: FileMetadata, 
        progress: IndexingProgress
    ):
        """
        Виконання повного pipeline індексації GraphRAG
        """
        
        file_output_dir = self.output_dir / file_metadata.id
        file_output_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Підготовка конфігурації
            await self._update_progress(progress, "preparing", 5.0)
            
            config_file = await self._create_config_file(file_metadata, file_output_dir)
            
            # Копіювання файлу в робочий каталог
            await self._update_progress(progress, "copying_file", 10.0)
            
            input_dir = file_output_dir / "input"
            input_dir.mkdir(exist_ok=True)
            
            # Копіюємо файл у каталог input з розширенням .txt
            input_file = input_dir / f"{file_metadata.id}.txt"
            
            # Витягуємо текст з файлу та зберігаємо як .txt
            from .file_service import FileService
            file_service = FileService()
            text_content = await file_service.extract_text_content(file_metadata)
            
            with open(input_file, 'w', encoding='utf-8') as f:
                f.write(text_content)
            
            # Запуск GraphRAG indexing
            await self._update_progress(progress, "chunking", 20.0)
            
            cmd = [
                "python", "-m", "graphrag.index",
                "--root", str(file_output_dir),
                "--config", str(config_file)
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(file_output_dir)
            )
            
            # Моніторинг прогресу
            await self._monitor_indexing_process(process, progress)
            
            # Перевірка результатів
            await self._update_progress(progress, "finalizing", 95.0)
            
            artifacts_dir = file_output_dir / "output" / "artifacts"
            if artifacts_dir.exists():
                # Підрахунок статистики
                stats = await self._calculate_indexing_stats(artifacts_dir)
                
                progress.status = "completed"
                progress.progress_percentage = 100.0
                progress.completed_at = datetime.utcnow()
                
                # Оновлення метаданих файлу
                from .file_service import FileService
                file_service = FileService()
                await file_service.update_file_status(
                    file_metadata.id,
                    "completed",
                    output_path=str(file_output_dir),
                    **stats
                )
            else:
                raise Exception("Indexing completed but no artifacts found")
                
        except Exception as e:
            progress.status = "error"
            progress.error_message = str(e)
            
            # Оновлення статусу файлу
            from .file_service import FileService
            file_service = FileService()
            await file_service.update_file_status(
                file_metadata.id,
                "error",
                error_message=str(e)
            )
        
        finally:
            await self._save_progress(progress)
    
    async def _create_config_file(self, file_metadata: FileMetadata, output_dir: Path) -> Path:
        """Створення конфігураційного файлу GraphRAG"""
        
        config = {
            "llm": {
                "api_key": settings.openai_api_key,
                "type": "openai_chat",
                "model": settings.graphrag_llm_model,
                "max_tokens": settings.graphrag_max_completion_tokens,
                "temperature": 0.1,
                "reasoning_effort": settings.graphrag_reasoning_effort
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
            "input": {
                "type": "file",
                "file_type": "text",
                "base_dir": "./input",
                "file_encoding": "utf-8",
                "file_pattern": ".*\\.txt$"
            },
            "storage": {
                "type": "file",
                "base_dir": "./output"
            },
            "cache": {
                "type": "file",
                "base_dir": "./cache"
            },
            "reporting": {
                "type": "file",
                "base_dir": "./output/reports"
            }
        }
        
        config_file = output_dir / "settings.yml"
        
        import yaml
        with open(config_file, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
        
        return config_file
    
    async def _monitor_indexing_process(self, process, progress: IndexingProgress):
        """Моніторинг процесу індексації"""
        
        step_progress = {
            "chunking": 30.0,
            "entity_extraction": 60.0,
            "relationship_extraction": 80.0,
            "community_detection": 90.0
        }
        
        current_step = "chunking"
        
        while True:
            try:
                line = await asyncio.wait_for(
                    process.stdout.readline(), 
                    timeout=1.0
                )
                
                if not line:
                    break
                    
                line_str = line.decode().strip()
                
                # Аналіз виводу для визначення поточного кроку
                if "entity" in line_str.lower():
                    current_step = "entity_extraction"
                elif "relationship" in line_str.lower():
                    current_step = "relationship_extraction"
                elif "community" in line_str.lower():
                    current_step = "community_detection"
                
                if current_step in step_progress:
                    await self._update_progress(
                        progress, 
                        current_step, 
                        step_progress[current_step]
                    )
                
            except asyncio.TimeoutError:
                # Перевірка чи процес ще працює
                if process.returncode is not None:
                    break
                continue
        
        # Чекаємо завершення процесу
        return_code = await process.wait()
        
        if return_code != 0:
            stderr = await process.stderr.read()
            error_msg = stderr.decode() if stderr else "Unknown error"
            raise Exception(f"GraphRAG indexing failed: {error_msg}")
    
    async def _calculate_indexing_stats(self, artifacts_dir: Path) -> Dict[str, int]:
        """Підрахунок статистики після індексації"""
        
        stats = {
            "chunks_count": 0,
            "entities_count": 0,
            "relationships_count": 0,
            "communities_count": 0
        }
        
        try:
            # Підрахунок сутностей
            entities_file = artifacts_dir / "create_final_entities.parquet"
            if entities_file.exists():
                df = pd.read_parquet(entities_file)
                stats["entities_count"] = len(df)
            
            # Підрахунок зв'язків
            relationships_file = artifacts_dir / "create_final_relationships.parquet"
            if relationships_file.exists():
                df = pd.read_parquet(relationships_file)
                stats["relationships_count"] = len(df)
            
            # Підрахунок спільнот
            communities_file = artifacts_dir / "create_final_communities.parquet"
            if communities_file.exists():
                df = pd.read_parquet(communities_file)
                stats["communities_count"] = len(df)
            
            # Підрахунок чанків
            chunks_file = artifacts_dir / "create_final_text_units.parquet"
            if chunks_file.exists():
                df = pd.read_parquet(chunks_file)
                stats["chunks_count"] = len(df)
                
        except Exception as e:
            print(f"Error calculating stats: {e}")
        
        return stats
    
    async def _local_search(self, query: str, file_ids: List[str]) -> Dict[str, Any]:
        """Локальний пошук по графу"""
        
        # Завантаження даних для локального пошуку
        all_entities = []
        all_relationships = []
        all_text_units = []
        
        for file_id in file_ids:
            artifacts_dir = self.output_dir / file_id / "output" / "artifacts"
            
            if not artifacts_dir.exists():
                continue
                
            # Завантаження сутностей
            entities_file = artifacts_dir / "create_final_entities.parquet"
            if entities_file.exists():
                entities_df = pd.read_parquet(entities_file)
                all_entities.append(entities_df)
            
            # Завантаження зв'язків  
            relationships_file = artifacts_dir / "create_final_relationships.parquet"
            if relationships_file.exists():
                relationships_df = pd.read_parquet(relationships_file)
                all_relationships.append(relationships_df)
            
            # Завантаження текстових одиниць
            text_units_file = artifacts_dir / "create_final_text_units.parquet"
            if text_units_file.exists():
                text_units_df = pd.read_parquet(text_units_file)
                all_text_units.append(text_units_df)
        
        if not all_entities:
            return {"response": "No indexed data found for the specified files.", "sources": []}
        
        # Об'єднання даних
        entities_df = pd.concat(all_entities, ignore_index=True)
        relationships_df = pd.concat(all_relationships, ignore_index=True) if all_relationships else pd.DataFrame()
        text_units_df = pd.concat(all_text_units, ignore_index=True) if all_text_units else pd.DataFrame()
        
        # Створення контексту для локального пошуку
        context_builder = LocalSearchMixedContext(
            community_reports=pd.DataFrame(),  # Порожній для простоти
            text_units=text_units_df,
            entities=entities_df,
            relationships=relationships_df,
            entity_text_embeddings=pd.DataFrame(),  # Додамо пізніше якщо потрібно
            embedding_vectorstore_key="text",
            text_embedder=self.embeddings,
            token_encoder=None
        )
        
        # Виконання локального пошуку
        local_search_engine = LocalSearch(
            llm=self.llm,
            context_builder=context_builder,
            token_encoder=None,
            response_type="multiple paragraphs"
        )
        
        result = await local_search_engine.asearch(query)
        
        return {
            "response": result.response,
            "context": result.context_data,
            "sources": self._extract_sources_from_context(result.context_data)
        }
    
    async def _global_search(self, query: str, file_ids: List[str]) -> Dict[str, Any]:
        """Глобальний пошук по графу"""
        
        # Завантаження даних для глобального пошуку
        all_communities = []
        all_entities = []
        
        for file_id in file_ids:
            artifacts_dir = self.output_dir / file_id / "output" / "artifacts"
            
            if not artifacts_dir.exists():
                continue
            
            # Завантаження спільнот
            communities_file = artifacts_dir / "create_final_community_reports.parquet"
            if communities_file.exists():
                communities_df = pd.read_parquet(communities_file)
                all_communities.append(communities_df)
            
            # Завантаження сутностей
            entities_file = artifacts_dir / "create_final_entities.parquet"
            if entities_file.exists():
                entities_df = pd.read_parquet(entities_file)
                all_entities.append(entities_df)
        
        if not all_communities:
            return {"response": "No community data found for global search.", "sources": []}
        
        # Об'єднання даних
        communities_df = pd.concat(all_communities, ignore_index=True)
        entities_df = pd.concat(all_entities, ignore_index=True) if all_entities else pd.DataFrame()
        
        # Створення контексту для глобального пошуку
        context_builder = GlobalCommunityContext(
            community_reports=communities_df,
            entities=entities_df,
            token_encoder=None
        )
        
        # Виконання глобального пошуку
        global_search_engine = GlobalSearch(
            llm=self.llm,
            context_builder=context_builder,
            token_encoder=None,
            max_data_tokens=12000,
            map_llm_params={
                "max_tokens": 1000,
                "temperature": 0.1
            },
            reduce_llm_params={
                "max_tokens": 2000,
                "temperature": 0.1
            }
        )
        
        result = await global_search_engine.asearch(query)
        
        return {
            "response": result.response,
            "context": result.context_data,
            "sources": self._extract_sources_from_context(result.context_data)
        }
    
    def _extract_sources_from_context(self, context_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Витягування джерел з контексту"""
        sources = []
        
        # Це залежить від структури context_data з GraphRAG
        # Адаптуємо під реальну структуру
        if isinstance(context_data, dict):
            for key, value in context_data.items():
                if "source" in key.lower() or "chunk" in key.lower():
                    sources.append({
                        "type": key,
                        "content": str(value)[:200] + "..." if len(str(value)) > 200 else str(value)
                    })
        
        return sources
    
    async def _update_progress(self, progress: IndexingProgress, step: str, percentage: float):
        """Оновлення прогресу індексації"""
        progress.current_step = step
        progress.progress_percentage = percentage
        await self._save_progress(progress)
    
    async def _save_progress(self, progress: IndexingProgress):
        """Збереження прогресу в файл"""
        status_file = self.cache_dir / f"indexing_status_{progress.file_id}.json"
        
        with open(status_file, 'w') as f:
            json.dump(progress.dict(), f, indent=2, default=str)
