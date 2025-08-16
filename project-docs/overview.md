# GraphRAG Web Platform - Огляд проєкту

## Мета проєкту
Створити повнофункціональну веб-платформу для роботи з GraphRAG, що дозволяє:
- Завантажувати та індексувати документи
- Візуалізувати граф знань
- Проводити інтерактивний чат з документами в режимах local/global

## Основні компоненти

### 1. Backend (FastAPI)
- REST API для управління файлами та запитами
- Інтеграція з GraphRAG для індексації
- Підключення до OpenAI GPT-5 API
- Обробка streaming відповідей

### 2. Frontend (Next.js + React)
- Інтерфейс завантаження файлів
- Візуалізація графа (Cytoscape.js/D3.js)
- Чат-інтерфейс з режимами local/global
- Відображення результатів індексації

### 3. GraphRAG Integration
- Використання GPT-5 для reasoning
- Text-embedding-3-large для ембеддингів
- Збереження результатів індексації

### 4. Infrastructure
- Docker Compose для локального розгортання
- Systemd сервіси для production
- Ubuntu Server deployment

## Цільова аудиторія
Користувачі, які хочуть аналізувати великі документи та отримувати інсайти через граф знань.

## Технічний стек
- **Backend**: Python, FastAPI, GraphRAG, OpenAI API
- **Frontend**: Next.js, React, Tailwind CSS, Cytoscape.js
- **Infrastructure**: Docker, Ubuntu, systemd
- **База даних**: JSON файли для метаданих, файлова система для документів
