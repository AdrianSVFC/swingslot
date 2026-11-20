"""GOLF-2 / GOLF-12: sign up, log in, secure passwords, log out."""
from app.db import get_db


def test_home_page_loads(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Book your next golf lesson" in response.data


def test_register_creates_account_and_logs_in(client, auth, app):
    response = auth.register()
    assert b"Your account was created" in response.data
    assert b"Log out (Test Golfer)" in response.data
    with app.app_context():
        user = get_db().execute("SELECT * FROM users WHERE email = 'test@example.com'").fetchone()
        assert user["role"] == "student"
        # GOLF-12: the password itself is never stored
        assert user["password_hash"] != "password123"
        assert user["password_hash"].startswith(("scrypt:", "pbkdf2:"))


def test_register_validation(auth):
    response = auth.register(email="not-an-email", password="short")
    assert b"Enter a valid email address." in response.data
    assert b"Password must be at least 8 characters." in response.data


def test_duplicate_email_rejected(auth):
    auth.register()
    auth.logout()
    response = auth.register()
    assert b"already exists" in response.data


def test_login_and_logout(auth):
    response = auth.login()
    assert b"Welcome back, Demo Golfer" in response.data
    response = auth.logout()
    assert b"You have been logged out." in response.data


def test_wrong_password(auth):
    response = auth.login(password="wrong-password")
    assert b"Incorrect email or password." in response.data


def test_post_without_csrf_token_is_rejected(client):
    response = client.post("/auth/login", data={"email": "a@b.co", "password": "x"})
    assert response.status_code == 400
