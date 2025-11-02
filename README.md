# Документация по развёртыванию LTTA

*(Flask + Gunicorn + Nginx + Docker/Compose + GitHub Actions)*

Эта инструкция покрывает полный путь: подготовка сервера, настройка Nginx, сборка образа и публикация в GHCR, автодеплой через GitHub Actions, а также ручной запуск через Docker Compose. В конце — разделы по БД, логам, откату и типовым проблемам.

---

## Содержание

* [1) Предварительные требования](#1-предварительные-требования)
* [2) Подготовка директорий на сервере](#2-подготовка-директорий-на-сервере)
* [3) Nginx: конфигурация и активация](#3-nginx-конфигурация-и-активация)
* [4) Переменные окружения и секреты](#4-переменные-окружения-и-секреты)

  * [4.1. Подключение к MariaDB](#41-подключение-к-mariadb)
  * [4.2. Файлы конфигурации](#42-файлы-конфигурации)
* [5) Docker Compose (прод-запуск)](#5-docker-compose-прод-запуск)
* [6) CI/CD через GitHub Actions](#6-cicd-через-github-actions)

  * [6.1. Секреты репозитория](#61-секреты-репозитория)
  * [6.2. Workflow](#62-workflow)
* [7) База данных (MariaDB)](#7-база-данных-mariadb)

  * [7.1. Установка](#71-установка)
  * [7.2. Создание БД и пользователя](#72-создание-бд-и-пользователя)
  * [7.3. Таблицы](#73-таблицы)
* [8) Проверка работоспособности](#8-проверка-работоспособности)
* [9) Логи и мониторинг](#9-логи-и-мониторинг)
* [10) Обновление приложения](#10-обновление-приложения)

  * [10.1. Через CI/CD](#101-через-cicd)
  * [10.2. Ручной деплой](#102-ручной-деплой)
* [11) Откат версии (rollback)](#11-откат-версии-rollback)
* [12) Безопасность и лучшие практики](#12-безопасность-и-лучшие-практики)
* [13) Альтернативы и варианты](#13-альтернативы-и-варианты)
* [14) Типичные проблемы](#14-типичные-проблемы)
* [15) Короткий чек-лист](#15-короткий-чек-лист)

---

## 1) Предварительные требования

**На сервере (Linux, например Ubuntu 22.04):**

```bash
# Docker + Compose v2
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
# перезайдите в сессию
docker compose version

# Nginx
sudo apt-get update && sudo apt-get install -y nginx
```

**В репозитории:**

* `Dockerfile`, `.dockerignore`, `docker-compose.yml`
* `.github/workflows/deploy.yml`
* Исходники приложения, включая `wsgi.py` с `app` (экземпляр Flask)
* `requirements.txt` (включая `gunicorn`)

**GHCR (GitHub Container Registry):**

* Личный токен (PAT) с правами **write:packages** → `GHCR_TOKEN`.

---

## 2) Подготовка директорий на сервере

```bash
sudo mkdir -p /var/www/ltta/{run,logs,static}
# если выносите артефакты наружу:
# sudo mkdir -p /var/www/ltta/{event_cards,user_cards}
sudo chown -R $USER:$USER /var/www/ltta
```

> `run/` — для Unix-сокета `ltta.sock`.
> `logs/` — для логов приложения.
> `static/` — чтобы Nginx отдавал статику напрямую.

---

## 3) Nginx: конфигурация и активация

**/etc/nginx/sites-available/ltta.conf**

```nginx
server {
    listen 80;
    server_name your.domain.tld;  # замените на домен/IPv4

    location /static/ {
        alias /var/www/ltta/static/;
        access_log off;
        expires 7d;
        add_header Cache-Control "public";
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/var/www/ltta/run/ltta.sock;
        proxy_read_timeout 90;
        client_max_body_size 25m;

        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

**Активация:**

```bash
sudo ln -s /etc/nginx/sites-available/ltta.conf /etc/nginx/sites-enabled/ltta.conf
sudo nginx -t
sudo systemctl reload nginx
```

---

## 4) Переменные окружения и секреты

### 4.1. Подключение к MariaDB

Формат DSN:

```
mariadb://USERNAME:PASSWORD@HOST:3306/DBNAME
```

Пример:

```
mariadb://ltta:strong_ltta_password@127.0.0.1:3306/ltta
```

### 4.2. Файлы конфигурации

Рекомендуется монтировать `conf.json` и `passwords.json` с хоста:

```yaml
# в docker-compose.yml → services.web.volumes
- /var/www/ltta/conf.json:/app/conf.json:ro
- /var/www/ltta/passwords.json:/app/passwords.json:ro
```

---

## 5) Docker Compose (прод-запуск)

**docker-compose.yml (на сервере):**

```yaml
name: ltta
services:
  web:
    image: ghcr.io/OWNER/REPO:ltta-${GITHUB_SHA:-latest}
    container_name: ltta_web
    restart: always
    volumes:
      - /var/www/ltta/run:/run/gunicorn
      - /var/www/ltta/logs:/app/logs
      - /var/www/ltta/static:/app/static:ro
      # при необходимости:
      # - /var/www/ltta/conf.json:/app/conf.json:ro
      # - /var/www/ltta/passwords.json:/app/passwords.json:ro
      # - /var/www/ltta/event_cards:/app/event_cards
      # - /var/www/ltta/user_cards:/app/user_cards
    environment:
      - FLASK_ENV=production
      - DATABASE_URL=mariadb://ltta:strong_ltta_password@127.0.0.1:3306/ltta
    # ports:
    #   - "8000:8000"   # если перейдёте на TCP-бинд
```

**Ручной старт/обновление:**

```bash
echo "$GHCR_TOKEN" | docker login ghcr.io -u GITHUB_USER --password-stdin
cd /var/www/ltta
docker compose pull
docker compose up -d
docker ps --filter "name=ltta_web"
```

---

## 6) CI/CD через GitHub Actions

### 6.1. Секреты репозитория

Добавьте в **Settings → Secrets and variables → Actions**:

* `GHCR_TOKEN` — PAT с правами **write:packages**
* `SSH_HOST` — адрес сервера
* `SSH_USER` — пользователь (в группе `docker`)
* `SSH_PRIVATE_KEY` — приватный ключ для SSH

### 6.2. Workflow

**.github/workflows/deploy.yml**

```yaml
name: Deploy LTTA

on:
  push:
    branches: [ "main" ]
  workflow_dispatch:

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ghcr.io/${{ github.repository }}
  CONTAINER_TAG: ltta-${{ github.sha }}

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Log in to GHCR
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GHCR_TOKEN }}

      - name: Build and push image
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: |
            ${{ env.IMAGE_NAME }}:${{ env.CONTAINER_TAG }}
            ${{ env.IMAGE_NAME }}:latest
          cache-from: type=registry,ref=${{ env.IMAGE_NAME }}:latest
          cache-to: type=inline

      - name: Upload docker-compose.yml
        uses: appleboy/scp-action@v0.1.7
        with:
          host: ${{ secrets.SSH_HOST }}
          username: ${{ secrets.SSH_USER }}
          key: ${{ secrets.SSH_PRIVATE_KEY }}
          source: "docker-compose.yml"
          target: "/var/www/ltta"

      - name: Deploy on server
        uses: appleboy/ssh-action@v1.1.0
        with:
          host: ${{ secrets.SSH_HOST }}
          username: ${{ secrets.SSH_USER }}
          key: ${{ secrets.SSH_PRIVATE_KEY }}
          script: |
            set -e
            cd /var/www/ltta

            if grep -q "ltta-\${GITHUB_SHA:-latest}" docker-compose.yml; then
              sed -i "s|ltta-\${GITHUB_SHA:-latest}|${{ env.CONTAINER_TAG }}|g" docker-compose.yml
            fi

            echo "${{ secrets.GHCR_TOKEN }}" | docker login ${{ env.REGISTRY }} -u ${{ github.actor }} --password-stdin

            docker compose pull
            docker compose up -d

            if command -v nginx >/dev/null 2>&1; then
              sudo nginx -t && sudo systemctl reload nginx || true
            fi

            docker ps --filter "name=ltta_web"
```

---

## 7) База данных (MariaDB)

### 7.1. Установка

```bash
sudo apt-get install -y mariadb-server
sudo systemctl enable --now mariadb
```

### 7.2. Создание БД и пользователя

```sql
CREATE DATABASE ltta;
CREATE USER 'ltta'@'localhost' IDENTIFIED BY 'strong_ltta_password';
GRANT ALL PRIVILEGES ON ltta.* TO 'ltta'@'localhost';
FLUSH PRIVILEGES;
```

### 7.3. Таблицы

```sql
CREATE TABLE users (
  username TEXT, name TEXT, surname TEXT, email VARCHAR(50), password TEXT,
  rating FLOAT, role VARCHAR(20), grade TINYINT, faculty VARCHAR(50),
  avatar TEXT, id TEXT
);

CREATE TABLE events (
  type TEXT, title TEXT, datetime TEXT, content TEXT, image TEXT,
  participants TEXT, id TEXT
);

CREATE TABLE finished_events (
  type TEXT, title TEXT, datetime TEXT, content TEXT, image TEXT,
  participants TEXT, id TEXT, winners TEXT
);

CREATE TABLE codes (
  email VARCHAR(50), code TEXT, datetime TEXT, name TEXT, surname TEXT,
  grade TINYINT, faculty VARCHAR(50), username TEXT, password TEXT
);

CREATE TABLE matches (
  id TEXT, player1 TEXT, player2 TEXT, winner TEXT, score TEXT
);
```

> При первом развёртывании создайте структуру БД и проверьте строку подключения.

---

## 8) Проверка работоспособности

```bash
# контейнер
docker ps --filter "name=ltta_web"

# сокет
ls -l /var/www/ltta/run/ltta.sock

# логи контейнера (Gunicorn stdout/stderr)
docker logs -f ltta_web

# nginx
curl -I http://your.domain.tld/
sudo nginx -t
```

Если **502 Bad Gateway**:

* Проверьте, что сокет существует и путь совпадает в Nginx и в volume.
* Убедитесь, что Gunicorn биндится на `/run/gunicorn/ltta.sock`.

---

## 9) Логи и мониторинг

* Приложение (файл): `/var/www/ltta/logs/logs.txt`
* Контейнер (stdout/stderr):

  ```bash
  docker logs -f ltta_web
  ```
* Nginx:

  ```
  /var/log/nginx/access.log
  /var/log/nginx/error.log
  ```

---

## 10) Обновление приложения

### 10.1. Через CI/CD

Коммит в `main` запускает сборку образа, пуш в GHCR и автоприменение на сервере.
Проверка:

```bash
docker ps --filter "name=ltta_web"
docker logs --tail 200 ltta_web
```

### 10.2. Ручной деплой

```bash
# локально
docker build -t ghcr.io/OWNER/REPO:ltta-LOCAL .
echo "$GHCR_TOKEN" | docker login ghcr.io -u GITHUB_USER --password-stdin
docker push ghcr.io/OWNER/REPO:ltta-LOCAL

# сервер
cd /var/www/ltta
sed -i 's|ltta-${GITHUB_SHA:-latest}|ltta-LOCAL|g' docker-compose.yml
echo "$GHCR_TOKEN" | docker login ghcr.io -u GITHUB_USER --password-stdin
docker compose pull
docker compose up -d
```

---

## 11) Откат версии (rollback)

1. Найдите нужный тег образа в GHCR (в UI GitHub → Packages).
2. Подставьте его в `docker-compose.yml` (например, `ltta-<old_sha>`), затем:

```bash
docker compose pull
docker compose up -d
```

3. Проверьте работоспособность.

---

## 12) Безопасность и лучшие практики

* Секреты хранить в переменных окружения/volume, **не в репозитории**.
* HTTPS:

  ```bash
  sudo apt-get install -y certbot python3-certbot-nginx
  sudo certbot --nginx -d your.domain.tld
  ```
* Лимиты загрузок: `client_max_body_size` уже указан.
* Мониторинг: healthcheck или `/health` и внешний аптайм-мониторинг.
* Ротация логов: logrotate для `/var/www/ltta/logs`.

---

## 13) Альтернативы и варианты

**TCP вместо сокета:**

* В `Dockerfile`:

  ```dockerfile
  CMD gunicorn --bind 0.0.0.0:8000 --workers=3 --timeout=60 wsgi:app
  ```
* В `docker-compose.yml`:

  ```yaml
  ports:
    - "8000:8000"
  ```
* В Nginx:

  ```nginx
  proxy_pass http://127.0.0.1:8000;
  ```

**MariaDB в Docker:** добавьте сервис БД и соединяйтесь по имени сервиса (например, `db:3306`). Не забудьте volume для данных.

---

## 14) Типичные проблемы

* **502 Bad Gateway** — нет сокета/не совпадает путь/права → проверьте volume и `proxy_pass`.
* **Нет соединения с БД** — проверьте `DATABASE_URL`, права пользователя MariaDB, доступ `localhost/127.0.0.1`.
* **Статика не отдаётся** — проверьте `alias /var/www/ltta/static/` и монтирование `/app/static:ro`.
* **Actions не может задеплоить** — `SSH_USER` должен быть в группе `docker`.
* **На сервере не тянется образ из GHCR** — выполните `docker login ghcr.io` с `GHCR_TOKEN`.

---

## 15) Короткий чек-лист

1. Установить Docker/Compose и Nginx
2. Создать `/var/www/ltta/{run,logs,static}`
3. Прописать и активировать конфиг Nginx
4. Настроить MariaDB (БД/пользователь/таблицы)
5. Добавить Secrets (`GHCR_TOKEN`, `SSH_HOST`, `SSH_USER`, `SSH_PRIVATE_KEY`)
6. Запушить в `main` → дождаться успешного workflow
7. Проверить сайт и логи

---

**Готово.** Если понадобятся варианты под systemd без Docker, миграции БД при старте или автогенерация таблиц — добавьте соответствующие шаги в `ENTRYPOINT`/`CMD` и workflow.
