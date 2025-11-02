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


def test_profile_redirects_without_login(client):
    """GET /profile редирект на /login без авторизации"""
    resp = client.get("/profile", follow_redirects=False)
    assert resp.status_code == 302
    assert "/login" in resp.location


def test_events_redirects_without_login(client):
    """GET /events редирект на /login без авторизации"""
    resp = client.get("/events", follow_redirects=False)
    assert resp.status_code == 302
    assert "/login" in resp.location


def test_members_redirects_without_login(client):
    """GET /members редирект на /login без авторизации"""
    resp = client.get("/members", follow_redirects=False)
    assert resp.status_code == 302
    assert "/login" in resp.location
