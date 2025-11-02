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


def test_index_page(client):
    """Главная страница отвечает"""
    resp = client.get("/")
    assert resp.status_code == 200


def test_login_get(client):
    """GET /login открывается"""
    resp = client.get("/login")
    assert resp.status_code == 200


def test_registration_get(client):
    """GET /registration открывается"""
    resp = client.get("/registration")
    assert resp.status_code == 200


def test_help_page(client):
    """GET /help открывается"""
    resp = client.get("/help")
    assert resp.status_code == 200
