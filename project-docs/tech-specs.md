# Технічні специфікації

## Архітектура системи

### Загальна архітектура
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend       │    │   GraphRAG      │
│   (Next.js)     │◄──►│   (FastAPI)      │◄──►│   Processing    │
│                 │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │                         │
                              ▼                         ▼
                       ┌──────────────────┐    ┌─────────────────┐
                       │   File Storage   │    │   OpenAI API    │
                       │   (Local FS)     │    │   (GPT-5)       │
                       └──────────────────┘    └─────────────────┘
```

## Backend (FastAPI)

### Технічний стек
- **Python**: 3.11+
- **FastAPI**: 0.104+
- **GraphRAG**: Latest
- **OpenAI**: 1.0+
- **Uvicorn**: ASGI server
- **Pydantic**: Валідація даних

### Структура API

#### Endpoints
1. **POST /api/files/upload** - Завантаження файлів
2. **POST /api/indexing/start** - Запуск індексації
3. **GET /api/indexing/status/{task_id}** - Статус індексації
4. **POST /api/chat/query** - Виконання запитів
5. **GET /api/graph/data** - Отримання даних графа
6. **GET /api/files** - Список файлів
7. **DELETE /api/files/{file_id}** - Видалення файлу

#### Моделі даних
```python
# Модель файлу
class FileMetadata(BaseModel):
    id: str
    filename: str
    size: int
    upload_date: datetime
    status: str  # uploaded, indexing, completed, error

# Модель запиту чату
class ChatQuery(BaseModel):
    message: str
    mode: str  # local, global
    file_ids: List[str]

# Модель відповіді
class ChatResponse(BaseModel):
    response: str
    sources: List[str]
    mode: str
```

### Обробка фонових завдань
- **Celery** або **FastAPI BackgroundTasks** для індексації
- **Redis** для черги завдань (опціонально)
- **WebSocket** для real-time оновлень

## Frontend (Next.js)

### Технічний стек
- **Next.js**: 14+
- **React**: 18+
- **TypeScript**: 5+
- **Tailwind CSS**: 3+
- **Cytoscape.js**: Візуалізація графа
- **Socket.io-client**: Real-time комунікація

### Компоненти
1. **FileUpload** - Завантаження файлів
2. **IndexingStatus** - Статус індексації
3. **ChatInterface** - Чат з документами
4. **GraphVisualization** - Візуалізація графа
5. **FileList** - Список файлів
6. **ChunkViewer** - Перегляд чанків

### Стан додатку
```typescript
interface AppState {
  files: FileMetadata[];
  currentChat: ChatMessage[];
  graphData: GraphData;
  indexingStatus: Record<string, IndexingStatus>;
}
```

## GraphRAG Integration

### Конфігурація
```yaml
# settings.yml
llm:
  provider: openai_chat
  model: gpt-4o-2024-11-20
  api_key: ${OPENAI_API_KEY}
  reasoning_effort: high
  max_completion_tokens: 4096

embeddings:
  provider: openai_embedding
  model: text-embedding-3-large
  api_key: ${OPENAI_API_KEY}

chunking:
  size: 1200
  overlap: 100

entity_extraction:
  max_gleanings: 1

community_reports:
  max_length: 2000
```

### Структура даних
```
output/
├── artifacts/
│   ├── entities.parquet
│   ├── relationships.parquet
│   ├── chunks.parquet
│   └── community_reports.parquet
└── graphs/
    └── graph.graphml
```

## База даних

### Файлова система
```
data/
├── uploads/           # Завантажені файли
├── output/           # Результати GraphRAG
├── metadata/         # JSON метадані
└── cache/           # Кешовані результати
```

### Метадані (JSON)
```json
{
  "files": {
    "file_id": {
      "filename": "document.pdf",
      "path": "uploads/file_id.pdf",
      "size": 1024000,
      "upload_date": "2024-01-01T00:00:00Z",
      "status": "completed",
      "graph_path": "output/file_id/",
      "chunks_count": 150,
      "entities_count": 200,
      "relationships_count": 300
    }
  }
}
```

## Безпека

### API Security
- **CORS** налаштування
- **Rate limiting** для endpoints
- **File validation** (тип, розмір)
- **Input sanitization**

### Environment Variables
```bash
OPENAI_API_KEY=sk-...
UPLOAD_MAX_SIZE=104857600  # 100MB
GRAPHRAG_THREADS=4
LOG_LEVEL=INFO
```

## Моніторинг та логування

### Структура логів
```python
import logging

# Налаштування логування
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
```

### Метрики
- Час обробки запитів
- Кількість файлів в обробці
- Використання пам'яті
- Помилки API
