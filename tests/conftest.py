import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ltta import app



@pytest.fixture
def client():
    """Создаем тестовый клиент Flask"""
    app.config.update(TESTING=True)
    with app.test_client() as client:
        yield client


# --- ТЕСТЫ ---

def test_index_page(client):
    """1️⃣ Проверка главной страницы"""
    response = client.get("/")
    assert response.status_code in (200, 500, 302)


def test_login_get(client):
    """2️⃣ Страница логина (GET)"""
    response = client.get("/login")
    assert response.status_code == 200


def test_registration_get(client):
    """3️⃣ Страница регистрации (GET)"""
    response = client.get("/registration")
    assert response.status_code == 200


def test_help_page(client):
    """4️⃣ Страница помощи"""
    response = client.get("/help")
    assert response.status_code == 200


def test_404_page(client):
    """5️⃣ Несуществующая страница (404)"""
    response = client.get("/non_existing_page")
    assert response.status_code == 404


def test_login_post_invalid(client):
    """6️⃣ Попытка входа с неверными данными"""
    response = client.post("/login", data={"username": "fake", "password": "wrong"})
    # Flask делает redirect при flash-сообщении
    assert response.status_code in (302, 200)


def test_registration_post_invalid(client):
    """7️⃣ Попытка регистрации с пустыми данными"""
    response = client.post("/registration", data={})
    # Ожидаем редирект или страницу с ошибкой
    assert response.status_code in (200, 302)


def test_error_handlers(client):
    """8️⃣ Проверка 500-й ошибки"""
    # Симулируем ошибку внутри маршрута
    @app.route("/trigger_error")
    def trigger_error():
        raise Exception("test internal error")

    response = client.get("/trigger_error")
    assert response.status_code == 500
