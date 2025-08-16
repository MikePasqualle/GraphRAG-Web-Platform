# Changelog

Всі важливі зміни у цьому проєкті будуть документуватися у цьому файлі.

Формат базується на [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
і цей проєкт дотримується [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2024-01-15

### Додано
- **Backend (FastAPI)**
  - REST API для управління файлами
  - Інтеграція з GraphRAG для індексації документів
  - Підтримка OpenAI GPT-5 та text-embedding-3-large
  - Streaming чат з документами (local/global режими)
  - Експорт графів у різних форматах
  - Background задачі для індексації
  - Health check endpoints
  - Комплексна система логування

- **Frontend (Next.js + React)**
  - Інтерактивний веб-інтерфейс
  - Drag & drop завантаження файлів
  - Візуалізація графів з Cytoscape.js
  - Real-time чат з streaming відповідями
  - Відстеження статусу індексації
  - Responsive дизайн з Tailwind CSS
  - Підтримка темної теми

- **GraphRAG інтеграція**
  - Автоматична індексація TXT, PDF, DOCX файлів
  - Витягування сутностей та зв'язків
  - Виявлення спільнот
  - Підтримка reasoning з GPT-5
  - Оптимізовані налаштування для українською мови

- **Інфраструктура**
  - Docker Compose для локального розгортання
  - Systemd сервіси для production
  - Nginx reverse proxy з SSL
  - Автоматичні скрипти встановлення
  - Система резервного копіювання

- **Безпека**
  - CORS налаштування
  - Rate limiting
  - Валідація файлів
  - SSL/TLS підтримка
  - Безпечні headers

- **Документація**
  - Повна API документація
  - Приклади використання
  - Інструкції з розгортання
  - Troubleshooting гайд

### Технічні деталі
- **Backend**: Python 3.11+, FastAPI, GraphRAG, OpenAI API
- **Frontend**: Next.js 14, React 18, TypeScript, Tailwind CSS
- **Database**: JSON файли для метаданих
- **Caching**: Redis для background задач
- **Deployment**: Docker, systemd, nginx

### Підтримувані формати файлів
- Plain text (.txt)
- PDF documents (.pdf)
- Microsoft Word (.docx)

### API Endpoints
- `POST /api/files/upload` - Завантаження файлу
- `GET /api/files` - Список файлів
- `GET /api/indexing/status/{file_id}` - Статус індексації
- `POST /api/chat/query` - Чат запити
- `POST /api/chat/stream` - Streaming чат
- `GET /api/graph/data` - Дані графу
- `POST /api/graph/export` - Експорт графу

### Системні вимоги
- **Мінімальні**: 4GB RAM, 2 CPU cores, 20GB диск
- **Рекомендовані**: 8GB+ RAM, 4+ CPU cores, 100GB+ SSD
- **OS**: Ubuntu 20.04+, Docker підтримка
- **Network**: Стабільне підключення до інтернету для OpenAI API

---

## [Unreleased]

### Заплановано
- Багатокористувацька підтримка з автентифікацією
- Розширена аналітика та метрики
- Підтримка додаткових форматів файлів
- API для інтеграції з іншими системами
- Покращена візуалізація графів
- Мобільна оптимізація

### В розробці
- Система користувачів та ролей
- Advanced пошук по графу
- Экспорт у додаткові формати
- Інтеграція з векторними базами даних
- Kubernetes deployment
- CI/CD pipeline

---

## Типи змін
- `Added` для нових функцій
- `Changed` для змін у існуючій функціональності
- `Deprecated` для функцій, які будуть видалені
- `Removed` для видалених функцій
- `Fixed` для виправлення багів
- `Security` для виправлень безпеки
