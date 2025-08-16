# Dockerfile для Backend
FROM python:3.11-slim

# Встановлення системних залежностей
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    pkg-config \
    libhdf5-dev \
    libssl-dev \
    libffi-dev \
    libxml2-dev \
    libxslt1-dev \
    zlib1g-dev \
    libjpeg-dev \
    libpng-dev \
    && rm -rf /var/lib/apt/lists/*

# Встановлення робочої директорії
WORKDIR /app

# Створення необхідних директорій
RUN mkdir -p /app/data/uploads \
    /app/data/output \
    /app/data/metadata \
    /app/data/cache \
    /app/logs \
    /app/config

# Копіювання файлів requirements
COPY requirements.txt .

# Встановлення Python залежностей
RUN pip install --no-cache-dir --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt

# Копіювання коду додатку
COPY . .

# Встановлення прав доступу
RUN chmod -R 755 /app/data /app/logs /app/config

# Створення користувача для безпеки
RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN chown -R appuser:appuser /app

# Експозиція порту
EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Змінні середовища для Python
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Переключення на unprivileged користувача
USER appuser

# Команда запуску
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
