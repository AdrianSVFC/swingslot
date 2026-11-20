"""GOLF-7: instructors register and set up their profile."""
from conftest import get_csrf

from app.db import get_db


def test_instructor_signup_goes_to_profile(auth):
    response = auth.register(name="New Coach", email="coach@example.com", role="instructor")
    assert b"My instructor profile" in response.data


def test_instructor_can_save_profile(client, auth, app):
    auth.register(name="New Coach", email="coach@example.com", role="instructor")
    token = get_csrf(client, "/instructor/profile")
    response = client.post("/instructor/profile", data={
        "csrf_token": token, "location": "Oxford, MS",
        "bio": "Teaching golf for ten years with a focus on beginners.",
        "lesson_types": ["Full Swing", "Putting"], "price": "65",
    }, follow_redirects=True)
    assert b"Your profile was saved." in response.data
    with app.app_context():
        profile = get_db().execute(
            "SELECT p.* FROM instructor_profiles p JOIN users u ON u.id = p.user_id"
            " WHERE u.email = 'coach@example.com'"
        ).fetchone()
        assert profile["location"] == "Oxford, MS"
        assert profile["lesson_types"] == "Full Swing,Putting"
        assert profile["price"] == 65


def test_profile_validation(client, auth):
    auth.register(name="New Coach", email="coach@example.com", role="instructor")
    token = get_csrf(client, "/instructor/profile")
    response = client.post("/instructor/profile", data={
        "csrf_token": token, "location": "", "bio": "short", "price": "5",
    }, follow_redirects=True)
    assert b"Location is required" in response.data
    assert b"Choose at least one lesson type." in response.data
    assert b"Price must be" in response.data


def test_golfer_cannot_open_instructor_profile(client, auth):
    auth.login()
    assert client.get("/instructor/profile").status_code == 403
