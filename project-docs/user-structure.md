# Структура користувача та проєкту

## Користувацький потік (User Flow)

### 1. Завантаження файлу
```
Користувач → Вибирає файл → Завантажує → Підтверджує → Файл збережено
                ↓
        Автоматично запускається індексація
                ↓
        Відображення прогресу індексації
                ↓
        Завершення - файл готовий до використання
```

### 2. Взаємодія з графом
```
Файл індексовано → Перегляд результатів → Вибір візуалізації → Інтерактивний граф
                        ↓
                Перегляд сутностей та зв'язків
                        ↓
                Детальна інформація про елементи
```

### 3. Чат-сесія
```
Користувач → Вибирає режим (local/global) → Пише запитання → Отримує відповідь
                ↓                              ↓               ↓
        Вибирає файли           Система обробляє    Джерела інформації
                                    через GraphRAG + GPT-5
```

## Структура проєкту

```
graphrag-web-platform/
├── backend/                    # FastAPI Backend
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py            # Головний FastAPI додаток
│   │   ├── config.py          # Налаштування
│   │   ├── api/               # API endpoints
│   │   │   ├── __init__.py
│   │   │   ├── files.py       # Управління файлами
│   │   │   ├── indexing.py    # Індексація
│   │   │   ├── chat.py        # Чат-функціональність
│   │   │   └── graph.py       # Граф API
│   │   ├── models/            # Pydantic моделі
│   │   │   ├── __init__.py
│   │   │   ├── file.py
│   │   │   ├── chat.py
│   │   │   └── graph.py
│   │   ├── services/          # Бізнес-логіка
│   │   │   ├── __init__.py
│   │   │   ├── file_service.py
│   │   │   ├── graphrag_service.py
│   │   │   └── chat_service.py
│   │   └── utils/             # Утиліти
│   │       ├── __init__.py
│   │       ├── file_utils.py
│   │       └── graph_utils.py
│   ├── requirements.txt       # Python залежності
│   ├── Dockerfile
│   └── .env.example
│
├── frontend/                  # Next.js Frontend
│   ├── src/
│   │   ├── app/               # App Router
│   │   │   ├── page.tsx       # Головна сторінка
│   │   │   ├── layout.tsx     # Layout
│   │   │   └── globals.css    # Глобальні стилі
│   │   ├── components/        # React компоненти
│   │   │   ├── ui/            # Базові UI компоненти
│   │   │   │   ├── button.tsx
│   │   │   │   ├── input.tsx
│   │   │   │   └── card.tsx
│   │   │   ├── FileUpload.tsx
│   │   │   ├── ChatInterface.tsx
│   │   │   ├── GraphVisualization.tsx
│   │   │   ├── FileList.tsx
│   │   │   └── IndexingStatus.tsx
│   │   ├── lib/               # Утиліти та API
│   │   │   ├── api.ts         # API клієнт
│   │   │   ├── types.ts       # TypeScript типи
│   │   │   └── utils.ts       # Утиліти
│   │   └── hooks/             # Custom React hooks
│   │       ├── useFiles.ts
│   │       ├── useChat.ts
│   │       └── useGraph.ts
│   ├── public/                # Статичні файли
│   ├── package.json
│   ├── next.config.js
│   ├── tailwind.config.js
│   ├── Dockerfile
│   └── .env.local.example
│
├── data/                      # Дані системи
│   ├── uploads/               # Завантажені файли
│   ├── output/               # GraphRAG результати
│   ├── metadata/             # JSON метадані
│   └── cache/                # Кеш
│
├── config/                    # Конфігурація
│   ├── settings.yml          # GraphRAG налаштування
│   ├── docker-compose.yml    # Docker Compose
│   └── nginx.conf            # Nginx конфігурація
│
├── scripts/                   # Скрипти
│   ├── setup.sh              # Скрипт налаштування
│   ├── deploy.sh             # Скрипт деплойменту
│   └── backup.sh             # Скрипт резервного копіювання
│
├── systemd/                   # Systemd сервіси
│   ├── graphrag-backend.service
│   ├── graphrag-frontend.service
│   └── graphrag-worker.service
│
├── project-docs/              # Документація проєкту
│   ├── overview.md
│   ├── requirements.md
│   ├── tech-specs.md
│   ├── user-structure.md
│   └── timeline.md
│
├── .env.example              # Приклад environment змінних
├── .gitignore
├── README.md
└── docker-compose.yml
```

## Потік даних

### 1. Завантаження файлу
```
Frontend → POST /api/files/upload → Backend → Збереження файлу → Metadata DB
    ↓
Автоматичний запуск індексації через Background Task
    ↓
GraphRAG обробка → Збереження результатів → Оновлення статусу
```

### 2. Отримання даних графа
```
Frontend → GET /api/graph/data → Backend → Читання GraphRAG output
    ↓                               ↓
Обробка в JSON формат ← Парсинг parquet файлів
    ↓
Відправка до Frontend → Візуалізація в Cytoscape.js
```

### 3. Чат-запит
```
Frontend → POST /api/chat/query → Backend → GraphRAG Query Engine
    ↓                               ↓              ↓
WebSocket streaming ← Обробка відповіді ← OpenAI GPT-5 API
    ↓
Real-time відображення в UI
```

## Інтерфейс користувача

### Головна сторінка
```
┌─────────────────────────────────────────────────────┐
│  GraphRAG Web Platform                              │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │
│  │ Завантажити │  │   Граф      │  │    Чат      │ │
│  │   файли     │  │             │  │             │ │
│  └─────────────┘  └─────────────┘  └─────────────┘ │
│                                                     │
│  ┌─────────────────────────────────────────────────┐ │
│  │            Список файлів                       │ │
│  │  [ ] document1.pdf  [Completed] [View Graph]   │ │
│  │  [ ] document2.txt  [Indexing...]  [45%]       │ │
│  └─────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

### Чат-інтерфейс
```
┌─────────────────────────────────────────────────────┐
│  Chat with Documents                                │
├─────────────────────────────────────────────────────┤
│  Mode: [Local] [Global]  Files: [Select...]        │
├─────────────────────────────────────────────────────┤
│                                                     │
│  User: What are the main topics?                    │
│                                                     │
│  Assistant: Based on the documents, the main       │
│  topics include... [Sources: doc1.pdf, doc2.txt]   │
│                                                     │
├─────────────────────────────────────────────────────┤
│  [Type your message here...]              [Send]   │
└─────────────────────────────────────────────────────┘
```
