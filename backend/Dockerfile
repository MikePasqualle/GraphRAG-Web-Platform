# Dockerfile для Backend
FROM python:3.11-slim

# Встановлення системних залежностей
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*

# Встановлення робочої директорії
WORKDIR /app

# Копіювання файлів requirements
COPY requirements.txt .

# Встановлення Python залежностей
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Копіювання коду додатку
COPY . .

# Створення необхідних директорій
RUN mkdir -p /app/data/uploads \
    /app/data/output \
    /app/data/metadata \
    /app/data/cache \
    /app/logs

# Встановлення прав доступу
RUN chmod -R 755 /app/data /app/logs

# Експозиція порту
EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Змінна середовища для Python
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Команда запуску
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
