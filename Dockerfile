# ===== Builder =====
FROM python:3.12-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential pkg-config libmariadb-dev-compat libmariadb-dev \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip \
 && pip wheel --no-cache-dir --no-deps -r requirements.txt -w /wheels

FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    libmariadb3 \
 && rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    GUNICORN_CMD_ARGS="--workers=3 --timeout=60 --graceful-timeout=30 --log-level=info"

# отдельный пользователь
RUN useradd -u 10001 -m appuser

WORKDIR /app

# зависимости
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels

# исходники
COPY . /app

# каталоги под сокет и логи
RUN mkdir -p /run/gunicorn /app/logs \
 && chown -R appuser:appuser /run/gunicorn /app/logs

USER appuser

# на всякий: TCP-порт (если Артём захочет биндиться на 0.0.0.0:8000)
EXPOSE 8000

# Предполагается, что в wsgi.py есть переменная app (Flask instance)
CMD gunicorn --bind unix:/run/gunicorn/ltta.sock --umask 007 wsgi:app
