"""Shared pytest fixtures: a fresh app + database for every test."""
import re

import pytest

from app import create_app


@pytest.fixture
def app(tmp_path):
    app = create_app({
        "TESTING": True,
        "DATABASE": str(tmp_path / "test.sqlite"),
        "SEED_DEMO_DATA": True,
        "SECRET_KEY": "test",
    })
    yield app


@pytest.fixture
def client(app):
    return app.test_client()


def get_csrf(client, path="/auth/login"):
    """Load a page and return the CSRF token from its form."""
    html = client.get(path).get_data(as_text=True)
    return re.search(r'name="csrf_token" value="([^"]+)"', html).group(1)


class AuthActions:
    def __init__(self, client):
        self.client = client

    def register(self, name="Test Golfer", email="test@example.com", password="password123", role="student"):
        token = get_csrf(self.client, "/auth/register")
        return self.client.post("/auth/register", data={
            "csrf_token": token, "name": name, "email": email,
            "password": password, "confirm": password, "role": role,
        }, follow_redirects=True)

    def login(self, email="golfer@swingslot.demo", password="swingslot123"):
        token = get_csrf(self.client)
        return self.client.post("/auth/login", data={
            "csrf_token": token, "email": email, "password": password,
        }, follow_redirects=True)

    def logout(self):
        token = get_csrf(self.client, "/")
        return self.client.post("/auth/logout", data={"csrf_token": token}, follow_redirects=True)


@pytest.fixture
def auth(client):
    return AuthActions(client)
