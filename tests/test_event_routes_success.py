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


def test_event_redirects_without_login(client):
    """GET /event/<event> редирект на /login без авторизации"""
    resp = client.get("/event/Test%20Event", follow_redirects=False)
    assert resp.status_code == 302
    assert "/login" in resp.location


def test_finished_event_redirects_without_login(client):
    """GET /finished_event/<event> редирект на /login без авторизации"""
    resp = client.get("/finished_event/Test%20Event", follow_redirects=False)
    assert resp.status_code == 302
    assert "/login" in resp.location


def test_ratings_redirects_without_login(client):
    """GET /ratings редирект на /login без авторизации"""
    resp = client.get("/ratings", follow_redirects=False)
    assert resp.status_code == 302
    assert "/login" in resp.location
