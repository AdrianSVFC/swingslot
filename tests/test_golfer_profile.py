"""GOLF-17: golfers edit their profile (handicap, level, goals); instructors see it (GOLF-20).

Tests written with help from Claude (AI).
"""
import pytest
from conftest import get_csrf

from app.db import get_db
from app.golfers import parse_handicap


def save_profile(client, handicap="12.5", level="Advanced", goals="Lower my handicap below 10."):
    token = get_csrf(client, "/golfer/profile")
    return client.post("/golfer/profile", data={
        "csrf_token": token, "handicap": handicap, "level": level, "goals": goals,
    }, follow_redirects=True)


@pytest.mark.parametrize("text, expected", [("", None), ("18.4", 18.4), ("0", 0.0), ("54", 54.0), ("7,3", 7.3)])
def test_parse_handicap_valid(text, expected):
    assert parse_handicap(text) == expected


@pytest.mark.parametrize("text", ["-1", "54.1", "abc"])
def test_parse_handicap_invalid(text):
    with pytest.raises(ValueError):
        parse_handicap(text)


def test_golfer_saves_profile(client, auth, app):
    auth.register(email="new@example.com")
    response = save_profile(client)
    assert b"Your golfer profile was saved." in response.data
    with app.app_context():
        row = get_db().execute(
            "SELECT sp.* FROM student_profiles sp JOIN users u ON u.id = sp.user_id"
            " WHERE u.email = 'new@example.com'"
        ).fetchone()
    assert row["handicap"] == 12.5
    assert row["level"] == "Advanced"
    assert row["goals"] == "Lower my handicap below 10."


def test_profile_can_be_updated_and_handicap_left_empty(client, auth, app):
    auth.login()  # demo golfer already has a seeded profile
    response = save_profile(client, handicap="", level="Beginner", goals="")
    assert b"Your golfer profile was saved." in response.data
    with app.app_context():
        rows = get_db().execute(
            "SELECT sp.* FROM student_profiles sp JOIN users u ON u.id = sp.user_id"
            " WHERE u.email = 'golfer@swingslot.demo'"
        ).fetchall()
    assert len(rows) == 1  # updated, not duplicated
    assert rows[0]["handicap"] is None
    assert rows[0]["level"] == "Beginner"


def test_profile_validation(client, auth):
    auth.login()
    response = save_profile(client, handicap="70", level="Pro", goals="x" * 501)
    assert b"Handicap must be a number between 0 and 54" in response.data
    assert b"Choose your level." in response.data
    assert b"Goals can be at most 500 characters." in response.data
    assert b"Your golfer profile was saved." not in response.data


def test_nav_shows_my_profile_for_golfers(client, auth):
    auth.login()
    assert b'href="/golfer/profile"' in client.get("/").data


def test_instructor_cannot_open_golfer_profile(client, auth):
    auth.login(email="mark@swingslot.demo")
    assert client.get("/golfer/profile").status_code == 403


def test_instructor_sees_golfer_profile_with_booking(client, auth, app):
    auth.login()
    with app.app_context():
        slot = get_db().execute(
            "SELECT s.id, s.instructor_id FROM time_slots s JOIN users u ON u.id = s.instructor_id"
            " WHERE u.email = 'mark@swingslot.demo' ORDER BY s.starts_at LIMIT 1"
        ).fetchone()
    token = get_csrf(client, f"/instructors/{slot['instructor_id']}")
    client.post(f"/book/{slot['id']}", data={"csrf_token": token})
    auth.logout()
    auth.login(email="mark@swingslot.demo")
    page = client.get("/dashboard").get_data(as_text=True)
    assert "Intermediate · HCP 18.4" in page
    assert "Break 90 this season" in page
