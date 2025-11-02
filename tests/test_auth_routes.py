import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from ltta import app


@pytest.fixture
def client():
    app.config.update(TESTING=True)
    with app.test_client() as client:
        yield client


def test_login_post_invalid(client):
    """POST /login с неверными данными не падает (обычно редирект на /login)"""
    resp = client.post("/login", data={"username": "nope", "password": "wrong"})
    assert resp.status_code in (200, 302)


def test_logout_requires_login(client):
    """GET /logout без авторизации редиректит на /login"""
    resp = client.get("/logout", follow_redirects=False)
    assert resp.status_code == 302
    assert "/login" in resp.location


def test_404_handler(client):
    """Несуществующий маршрут возвращает 404"""
    resp = client.get("/absolutely_non_existing_route_xyz")
    assert resp.status_code == 404
