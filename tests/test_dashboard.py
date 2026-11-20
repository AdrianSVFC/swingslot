"""GOLF-42: dashboards with upcoming and past lessons."""
from conftest import get_csrf

from app.db import get_db


def book_first_slot(client, app):
    with app.app_context():
        row = get_db().execute(
            "SELECT s.id, s.instructor_id FROM time_slots s JOIN users u ON u.id = s.instructor_id"
            " WHERE u.email = 'mark@swingslot.demo' ORDER BY s.starts_at LIMIT 1"
        ).fetchone()
    token = get_csrf(client, f"/instructors/{row['instructor_id']}")
    client.post(f"/book/{row['id']}", data={"csrf_token": token})


def test_dashboard_requires_login(client):
    response = client.get("/dashboard")
    assert response.status_code == 302


def test_golfer_sees_booked_lesson(client, auth, app):
    auth.login()
    book_first_slot(client, app)
    response = client.get("/dashboard")
    assert b"Upcoming lessons (1)" in response.data
    assert b"Mark Collins" in response.data


def test_instructor_sees_golfer_and_past_lessons(client, auth, app):
    auth.login()
    book_first_slot(client, app)
    with app.app_context():
        db = get_db()
        # Move one booked lesson into the past to check the "past" list
        db.execute("UPDATE time_slots SET starts_at = '2025-01-10T09:00'"
                   " WHERE id IN (SELECT slot_id FROM bookings)")
        db.commit()
    auth.logout()
    auth.login(email="mark@swingslot.demo")
    response = client.get("/dashboard")
    assert b"Past lessons (1)" in response.data
    assert b"Demo Golfer" in response.data
    assert b"open slot(s)" in response.data
