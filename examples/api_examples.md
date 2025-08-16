# API Examples для GraphRAG Web Platform

Цей файл містить приклади використання REST API для всіх основних функцій платформи.

## Базова URL
```
http://localhost:8000  # Development
https://your-domain.com  # Production
```

## Автентифікація
На данний момент API не потребує автентифікації. У production варіанті рекомендується додати JWT токени.

---

## 📁 Управління файлами

### Завантаження файлу
```bash
curl -X POST "http://localhost:8000/api/files/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/your/document.pdf"
```

**Відповідь:**
```json
{
  "file_id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "document.pdf",
  "size": 1048576,
  "status": "uploaded",
  "upload_date": "2024-01-15T10:30:00Z",
  "message": "File uploaded successfully. Indexing started."
}
```

### Отримання списку файлів
```bash
curl -X GET "http://localhost:8000/api/files?page=1&per_page=20&status=completed"
```

**Відповідь:**
```json
{
  "files": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "filename": "document_550e8400.pdf",
      "original_filename": "document.pdf",
      "size": 1048576,
      "content_type": "application/pdf",
      "upload_date": "2024-01-15T10:30:00Z",
      "status": "completed",
      "chunks_count": 25,
      "entities_count": 150,
      "relationships_count": 89,
      "communities_count": 12,
      "file_path": "/app/data/uploads/document_550e8400.pdf",
      "output_path": "/app/data/output/550e8400"
    }
  ],
  "total": 1,
  "page": 1,
  "per_page": 20
}
```

### Отримання інформації про файл
```bash
curl -X GET "http://localhost:8000/api/files/550e8400-e29b-41d4-a716-446655440000"
```

### Видалення файлу
```bash
curl -X DELETE "http://localhost:8000/api/files/550e8400-e29b-41d4-a716-446655440000"
```

**Відповідь:**
```json
{
  "file_id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "document.pdf",
  "deleted": true,
  "message": "File deleted successfully"
}
```

### Переіндексація файлу
```bash
curl -X POST "http://localhost:8000/api/files/550e8400-e29b-41d4-a716-446655440000/reindex"
```

---

## 🔄 Статус індексації

### Статус індексації конкретного файлу
```bash
curl -X GET "http://localhost:8000/api/indexing/status/550e8400-e29b-41d4-a716-446655440000"
```

**Відповідь:**
```json
{
  "file_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "indexing",
  "current_step": "entity_extraction",
  "progress_percentage": 65.0,
  "estimated_remaining": 180,
  "started_at": "2024-01-15T10:30:15Z"
}
```

### Статус всіх індексацій
```bash
curl -X GET "http://localhost:8000/api/indexing/status"
```

**Відповідь:**
```json
{
  "statuses": [
    {
      "file_id": "550e8400-e29b-41d4-a716-446655440000",
      "filename": "document.pdf",
      "status": "completed",
      "progress_percentage": 100.0,
      "entities_count": 150,
      "relationships_count": 89
    }
  ],
  "total": 1,
  "active_indexing": 0,
  "completed": 1,
  "errors": 0
}
```

### Скасування індексації
```bash
curl -X DELETE "http://localhost:8000/api/indexing/cancel/550e8400-e29b-41d4-a716-446655440000"
```

### Повтор індексації після помилки
```bash
curl -X POST "http://localhost:8000/api/indexing/retry/550e8400-e29b-41d4-a716-446655440000"
```

---

## 💬 Чат з документами

### Звичайний запит (не streaming)
```bash
curl -X POST "http://localhost:8000/api/chat/query" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Які основні теми обговорюються в документі?",
    "mode": "local",
    "file_ids": ["550e8400-e29b-41d4-a716-446655440000"],
    "stream": false
  }'
```

**Відповідь:**
```json
{
  "message_id": "msg_123456789",
  "response": "На основі аналізу документа, основними темами є:\n\n1. **Штучний інтелект** - розглядаються сучасні підходи до машинного навчання\n2. **Обробка природної мови** - методи аналізу тексту\n3. **Граф знань** - структурування інформації у вигляді графів\n\nКожна тема детально розкривається з практичними прикладами.",
  "mode": "local",
  "sources": [
    {
      "file_id": "550e8400-e29b-41d4-a716-446655440000",
      "filename": "document.pdf",
      "chunk_id": "chunk_001",
      "relevance_score": 0.95
    }
  ],
  "processing_time": 2.45,
  "conversation_id": "conv_987654321"
}
```

### Streaming запит
```bash
curl -X POST "http://localhost:8000/api/chat/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Поясни детальніше про методи машинного навчання",
    "mode": "global",
    "file_ids": [],
    "stream": true
  }'
```

**Відповідь (Server-Sent Events):**
```
data: {"chunk_id": "chunk_001", "content": "Методи машинного", "is_final": false}

data: {"chunk_id": "chunk_001", "content": " навчання можна", "is_final": false}

data: {"chunk_id": "chunk_001", "content": " поділити на кілька", "is_final": false}

data: {"chunk_id": "chunk_001", "content": "", "is_final": true, "sources": [...]}
```

### Створення нової розмови
```bash
curl -X POST "http://localhost:8000/api/chat/conversations" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Аналіз документації",
    "file_ids": ["550e8400-e29b-41d4-a716-446655440000"]
  }'
```

---

## 🕸️ Робота з графом

### Отримання даних графу
```bash
curl -X GET "http://localhost:8000/api/graph/data?file_ids=550e8400-e29b-41d4-a716-446655440000&include_chunks=true"
```

**Відповідь:**
```json
{
  "entities": [
    {
      "id": "entity_001",
      "name": "Штучний інтелект",
      "type": "concept",
      "description": "Галузь комп'ютерних наук",
      "degree": 15,
      "community_id": "community_001",
      "x": 0.5,
      "y": 0.3
    }
  ],
  "relationships": [
    {
      "id": "rel_001",
      "source_id": "entity_001",
      "target_id": "entity_002",
      "relationship_type": "relates_to",
      "description": "пов'язано з",
      "weight": 0.8
    }
  ],
  "communities": [
    {
      "id": "community_001",
      "title": "AI та ML технології",
      "description": "Спільнота сутностей пов'язаних з ШІ",
      "size": 25,
      "entities": ["entity_001", "entity_002"]
    }
  ],
  "chunks": [
    {
      "id": "chunk_001",
      "text": "Штучний інтелект є однією з найважливіших...",
      "file_id": "550e8400-e29b-41d4-a716-446655440000",
      "entities": ["entity_001"]
    }
  ],
  "generated_at": "2024-01-15T12:00:00Z"
}
```

### Статистика графу
```bash
curl -X GET "http://localhost:8000/api/graph/stats/550e8400-e29b-41d4-a716-446655440000"
```

**Відповідь:**
```json
{
  "file_id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "document.pdf",
  "entities_count": 150,
  "relationships_count": 89,
  "communities_count": 12,
  "chunks_count": 25,
  "entity_types": {
    "person": 25,
    "organization": 15,
    "concept": 85,
    "location": 10,
    "technology": 15
  },
  "relationship_types": {
    "relates_to": 45,
    "part_of": 20,
    "works_at": 12,
    "located_in": 8,
    "uses": 4
  },
  "density": 0.0078,
  "average_degree": 1.19
}
```

### Експорт графу
```bash
curl -X POST "http://localhost:8000/api/graph/export" \
  -H "Content-Type: application/json" \
  -d '{
    "file_ids": ["550e8400-e29b-41d4-a716-446655440000"],
    "format": "json",
    "include_embeddings": false,
    "include_chunks": true
  }'
```

**Відповідь:**
```json
{
  "export_id": "export_123456",
  "format": "json",
  "file_url": "/api/graph/download/export_123456",
  "expires_at": "2024-01-16T12:00:00Z",
  "size_bytes": 2048576
}
```

### Розрахунок layout для візуалізації
```bash
curl -X POST "http://localhost:8000/api/graph/layout" \
  -H "Content-Type: application/json" \
  -d '{
    "file_ids": ["550e8400-e29b-41d4-a716-446655440000"],
    "algorithm": "force_directed",
    "iterations": 100,
    "include_communities": true
  }'
```

### Пошук по графу
```bash
curl -X GET "http://localhost:8000/api/graph/search?query=штучний%20інтелект&file_ids=550e8400-e29b-41d4-a716-446655440000&limit=10"
```

**Відповідь:**
```json
{
  "query": "штучний інтелект",
  "total_matches": 5,
  "entities": [
    {
      "id": "entity_001",
      "name": "Штучний інтелект",
      "type": "concept",
      "relevance_score": 2.0
    }
  ],
  "relationships": [
    {
      "id": "rel_001",
      "source_id": "entity_001",
      "target_id": "entity_002",
      "relationship_type": "relates_to"
    }
  ],
  "file_ids": ["550e8400-e29b-41d4-a716-446655440000"]
}
```

---

## 🔍 Health Checks

### Backend health
```bash
curl -X GET "http://localhost:8000/health"
```

**Відповідь:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T12:00:00Z",
  "directories": {
    "upload": {"exists": true, "writable": true},
    "output": {"exists": true, "writable": true}
  },
  "openai": {
    "api_key_configured": true,
    "model": "gpt-4o-2024-11-20"
  },
  "version": "1.0.0"
}
```

### Frontend health
```bash
curl -X GET "http://localhost:3000/api/health"
```

### Chat service health
```bash
curl -X GET "http://localhost:8000/api/chat/health"
```

---

## 📝 Приклади використання з Python

```python
import requests
import json

# Базовий URL
BASE_URL = "http://localhost:8000"

# Завантаження файлу
def upload_file(file_path):
    with open(file_path, 'rb') as f:
        files = {'file': f}
        response = requests.post(f"{BASE_URL}/api/files/upload", files=files)
        return response.json()

# Чат запит
def chat_query(message, mode="local", file_ids=[]):
    data = {
        "message": message,
        "mode": mode,
        "file_ids": file_ids,
        "stream": False
    }
    response = requests.post(f"{BASE_URL}/api/chat/query", json=data)
    return response.json()

# Отримання графу
def get_graph_data(file_ids):
    params = {"file_ids": file_ids, "include_chunks": True}
    response = requests.get(f"{BASE_URL}/api/graph/data", params=params)
    return response.json()

# Приклад використання
if __name__ == "__main__":
    # Завантажуємо файл
    upload_result = upload_file("document.pdf")
    file_id = upload_result["file_id"]
    
    # Чекаємо завершення індексації (у реальному коді додайте polling)
    
    # Задаємо питання
    chat_result = chat_query(
        "Які основні теми в документі?", 
        mode="local", 
        file_ids=[file_id]
    )
    print(chat_result["response"])
    
    # Отримуємо граф
    graph_data = get_graph_data([file_id])
    print(f"Entities: {len(graph_data['entities'])}")
```

---

## 📊 Приклади з cURL для тестування

### Швидкий тест всіх endpoints
```bash
#!/bin/bash

# Health check
echo "=== Health Check ==="
curl -s http://localhost:8000/health | jq .

# Upload file (замініть на реальний файл)
echo -e "\n=== Upload File ==="
FILE_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/files/upload" \
  -F "file=@test_document.txt")
echo $FILE_RESPONSE | jq .

# Extract file ID
FILE_ID=$(echo $FILE_RESPONSE | jq -r .file_id)

# Check indexing status
echo -e "\n=== Indexing Status ==="
curl -s "http://localhost:8000/api/indexing/status/$FILE_ID" | jq .

# Chat query (після завершення індексації)
echo -e "\n=== Chat Query ==="
curl -s -X POST "http://localhost:8000/api/chat/query" \
  -H "Content-Type: application/json" \
  -d "{
    \"message\": \"What is this document about?\",
    \"mode\": \"local\",
    \"file_ids\": [\"$FILE_ID\"]
  }" | jq .

# Get graph data
echo -e "\n=== Graph Data ==="
curl -s "http://localhost:8000/api/graph/data?file_ids=$FILE_ID" | jq .entities[0]

echo -e "\n=== Test Complete ==="
```

Збережіть як `test_api.sh`, надайте права виконання (`chmod +x test_api.sh`) та запустіть для тестування всього API.
