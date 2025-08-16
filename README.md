# GraphRAG Web Platform

Повнофункціональна веб-платформа для роботи з графами знань на основі GraphRAG, OpenAI GPT-5 та text-embedding-3-large.

## 🌟 Особливості

- **Завантаження файлів**: Підтримка TXT, PDF, DOCX з автоматичною індексацією
- **Інтерактивний граф**: Візуалізація сутностей, зв'язків та спільнот
- **Розумний чат**: Local/Global режими з streaming відповідями
- **Realtime статус**: Відстеження прогресу індексації у реальному часі
- **Масштабованість**: Docker та systemd варіанти розгортання

## 🏗️ Архітектура

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

## 🚀 Швидкий старт

### Варіант 1: Docker Compose (Рекомендований)

1. **Клонування репозиторію**
```bash
git clone <repository-url>
cd graphrag-web-platform
```

2. **Налаштування змінних середовища**
```bash
cp env.example .env
# Відредагуйте .env файл та додайте свій OpenAI API key
```

3. **Збірка frontend**
```bash
cd frontend
npm install
npm run build
cd ..
```

4. **Запуск**
```bash
chmod +x scripts/deploy.sh
./scripts/deploy.sh production
```

### Варіант 2: Ubuntu Server (Production)

1. **Автоматичне встановлення**
```bash
chmod +x scripts/setup.sh
sudo ./scripts/setup.sh
```

2. **Налаштування**
```bash
sudo nano /opt/graphrag-web-platform/.env
# Додайте свій OpenAI API key
sudo systemctl restart graphrag-backend graphrag-frontend
```

## 📋 Системні вимоги

### Мінімальні
- **OS**: Ubuntu 20.04+ / Docker
- **RAM**: 4GB
- **CPU**: 2 cores
- **Диск**: 20GB вільного місця
- **Python**: 3.11+
- **Node.js**: 18+

### Рекомендовані
- **RAM**: 8GB+
- **CPU**: 4+ cores
- **Диск**: 100GB+ SSD
- **Мережа**: Стабільне з'єднання з інтернетом

## 🔧 Конфігурація

### Environment змінні (.env)

```bash
# OpenAI Configuration
OPENAI_API_KEY=sk-your-openai-api-key-here
GRAPHRAG_LLM_MODEL=gpt-4o-2024-11-20
GRAPHRAG_EMBEDDING_MODEL=text-embedding-3-large
GRAPHRAG_REASONING_EFFORT=high
GRAPHRAG_MAX_COMPLETION_TOKENS=4096

# Application Configuration
UPLOAD_MAX_SIZE=104857600  # 100MB
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=http://localhost:3000

# Worker Configuration
WORKER_THREADS=4
MAX_CONCURRENT_INDEXING=3
```

### GraphRAG налаштування (config/settings.yml)

```yaml
llm:
  api_key: ${OPENAI_API_KEY}
  type: openai_chat
  model: gpt-4o-2024-11-20
  reasoning_effort: high
  max_tokens: 4096

embeddings:
  api_key: ${OPENAI_API_KEY}
  type: openai_embedding
  model: text-embedding-3-large
  dimensions: 3072

chunks:
  size: 1200
  overlap: 100
```

## 📁 Структура проєкту

```
graphrag-web-platform/
├── backend/                    # FastAPI Backend
│   ├── app/
│   │   ├── main.py            # Головний додаток
│   │   ├── api/               # API endpoints
│   │   ├── models/            # Pydantic моделі
│   │   ├── services/          # Бізнес-логіка
│   │   └── utils/             # Утиліти
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                  # Next.js Frontend
│   ├── src/
│   │   ├── app/               # App Router
│   │   ├── components/        # React компоненти
│   │   └── lib/               # Утиліти та API
│   ├── package.json
│   └── Dockerfile
├── config/                    # Конфігурація
│   └── settings.yml          # GraphRAG налаштування
├── scripts/                   # Скрипти
│   ├── setup.sh              # Автоматичне встановлення
│   ├── deploy.sh             # Деплоймент
│   └── backup.sh             # Резервні копії
├── systemd/                   # Systemd сервіси
├── nginx/                     # Nginx конфігурація
├── data/                      # Дані (створюється автоматично)
│   ├── uploads/               # Завантажені файли
│   ├── output/               # GraphRAG результати
│   ├── metadata/             # Метадані
│   └── cache/                # Кеш
└── docker-compose.yml
```

## 🔌 API Endpoints

### Файли
- `POST /api/files/upload` - Завантаження файлу
- `GET /api/files` - Список файлів
- `GET /api/files/{file_id}` - Інформація про файл
- `DELETE /api/files/{file_id}` - Видалення файлу
- `POST /api/files/{file_id}/reindex` - Переіндексація

### Індексація
- `GET /api/indexing/status/{file_id}` - Статус індексації
- `GET /api/indexing/status` - Всі статуси
- `DELETE /api/indexing/cancel/{file_id}` - Скасування
- `POST /api/indexing/retry/{file_id}` - Повтор

### Чат
- `POST /api/chat/query` - Звичайний запит
- `POST /api/chat/stream` - Streaming запит
- `GET /api/chat/health` - Health check

### Граф
- `GET /api/graph/data` - Дані графу
- `GET /api/graph/stats/{file_id}` - Статистика
- `POST /api/graph/export` - Експорт
- `POST /api/graph/layout` - Розрахунок layout

## 🖥️ Використання

### 1. Завантаження файлів
- Перейдіть на вкладку "Файли"
- Перетягніть файли або натисніть для вибору
- Файли автоматично почнуть індексуватися

### 2. Перегляд графу
- Виберіть один або кілька файлів
- Перейдіть на вкладку "Граф"
- Використовуйте інструменти для навігації та пошуку

### 3. Чат з документами
- Виберіть файли (для local режиму)
- Перейдіть на вкладку "Чат"
- Виберіть режим (Local/Global)
- Задавайте питання

## 🛠️ Розробка

### Запуск у режимі розробки

1. **Backend**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

2. **Frontend**
```bash
cd frontend
npm install
npm run dev
```

### Тестування

```bash
# Backend тести
cd backend
pytest

# Frontend тести
cd frontend
npm test

# E2E тести
npm run test:e2e
```

## 📊 Моніторинг

### Логи
```bash
# Docker
docker-compose logs -f backend
docker-compose logs -f frontend

# Systemd
journalctl -fu graphrag-backend
journalctl -fu graphrag-frontend
sudo tail -f /opt/graphrag-web-platform/logs/app.log
```

### Метрики
- CPU/Memory usage: `htop`, `docker stats`
- Disk usage: `df -h`
- API health: `curl http://localhost:8000/health`

## 🔒 Безпека

### Рекомендації для production
1. **SSL сертифікати**: Замініть self-signed на валідні
2. **Файрвол**: Налаштуйте ufw або iptables
3. **Оновлення**: Регулярно оновлюйте залежності
4. **Backup**: Налаштуйте автоматичні резервні копії
5. **Моніторинг**: Використовуйте системи моніторингу

### Обмеження
- Максимальний розмір файлу: 100MB
- Підтримувані формати: TXT, PDF, DOCX
- Rate limiting на API endpoints

## 🆘 Вирішення проблем

### Часті проблеми

1. **OpenAI API помилки**
```bash
# Перевірте API key
curl -H "Authorization: Bearer $OPENAI_API_KEY" https://api.openai.com/v1/models
```

2. **Помилки індексації**
```bash
# Перевірте логи
docker-compose logs backend
# Перевірте дисковий простір
df -h
```

3. **Frontend не завантажується**
```bash
# Перевірте збірку
cd frontend && npm run build
# Перевірте порти
netstat -tulpn | grep :3000
```

### Відновлення з backup
```bash
# Розпакування
tar -xzf graphrag_backup_YYYYMMDD_HHMMSS.tar.gz
# Відновлення даних
sudo cp -r backup_data/* /opt/graphrag-web-platform/data/
# Перезапуск сервісів
sudo systemctl restart graphrag-backend graphrag-frontend
```

## 🤝 Внесок у розробку

1. Fork репозиторію
2. Створіть feature branch (`git checkout -b feature/amazing-feature`)
3. Commit зміни (`git commit -m 'Add amazing feature'`)
4. Push до branch (`git push origin feature/amazing-feature`)
5. Створіть Pull Request

## 📄 Ліцензія

Цей проєкт ліцензовано під MIT License - деталі у [LICENSE](LICENSE) файлі.

## 📞 Підтримка

- 📧 Email: support@graphrag-platform.com
- 🐛 Issues: [GitHub Issues](https://github.com/your-repo/issues)
- 📖 Документація: [Wiki](https://github.com/your-repo/wiki)

## 🙏 Подяки

- [GraphRAG](https://github.com/microsoft/graphrag) - Microsoft Research
- [FastAPI](https://fastapi.tiangolo.com/) - Sebastian Ramirez
- [Next.js](https://nextjs.org/) - Vercel
- [OpenAI](https://openai.com/) - API та моделі

---

**GraphRAG Web Platform** - Перетворюйте документи на інтерактивні графи знань! 🚀
