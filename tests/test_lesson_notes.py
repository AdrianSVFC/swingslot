"""GOLF-48: instructors write notes after a lesson and the golfer can read them (GOLF-51 permissions).

Tests written with help from Claude (AI).
"""
from datetime import datetime, timedelta

from conftest import get_csrf

from app.db import get_db

NOTES = "Worked on grip and alignment.\nPractise 3 x 20 balls with an alignment stick."


def book_lesson(client, auth, app, in_past=True):
    """Demo golfer books Mark's first slot; optionally move it into the past. Returns booking id."""
    auth.login()
    with app.app_context():
        slot = get_db().execute(
            "SELECT s.id, s.instructor_id FROM time_slots s JOIN users u ON u.id = s.instructor_id"
            " WHERE u.email = 'mark@swingslot.demo' ORDER BY s.starts_at LIMIT 1"
        ).fetchone()
    token = get_csrf(client, f"/instructors/{slot['instructor_id']}")
    client.post(f"/book/{slot['id']}", data={"csrf_token": token})
    with app.app_context():
        db = get_db()
        booking_id = db.execute("SELECT id FROM bookings WHERE slot_id = ?", (slot["id"],)).fetchone()["id"]
        if in_past:
            yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M")
            db.execute("UPDATE time_slots SET starts_at = ? WHERE id = ?", (yesterday, slot["id"]))
            db.commit()
    auth.logout()
    return booking_id


def write_notes(client, booking_id, notes=NOTES):
    token = get_csrf(client, f"/lessons/{booking_id}/notes")
    return client.post(f"/lessons/{booking_id}/notes", data={"csrf_token": token, "notes": notes},
                       follow_redirects=True)


def test_instructor_adds_notes_and_golfer_reads_them(client, auth, app):
    booking_id = book_lesson(client, auth, app)
    auth.login(email="mark@swingslot.demo")
    assert b"Add notes" in client.get("/dashboard").data
    response = write_notes(client, booking_id)
    assert b"Lesson notes saved. Demo Golfer can read them now." in response.data
    assert b"Worked on grip and alignment." in response.data
    assert b"Edit notes" in client.get("/dashboard").data
    auth.logout()

    auth.login()
    dashboard = client.get("/dashboard").get_data(as_text=True)
    assert f'href="/lessons/{booking_id}"' in dashboard
    assert "View notes" in dashboard
    page = client.get(f"/lessons/{booking_id}").get_data(as_text=True)
    assert "Practise 3 x 20 balls" in page
    assert "Add notes" not in page  # golfers can't edit


def test_notes_can_be_edited(client, auth, app):
    booking_id = book_lesson(client, auth, app)
    auth.login(email="mark@swingslot.demo")
    write_notes(client, booking_id)
    write_notes(client, booking_id, "Short game today: chipping with a 9 iron.")
    with app.app_context():
        rows = get_db().execute("SELECT notes FROM lesson_notes WHERE booking_id = ?", (booking_id,)).fetchall()
    assert len(rows) == 1
    assert rows[0]["notes"] == "Short game today: chipping with a 9 iron."


def test_notes_validation(client, auth, app):
    booking_id = book_lesson(client, auth, app)
    auth.login(email="mark@swingslot.demo")
    assert b"Notes must be between 10 and 2000 characters." in write_notes(client, booking_id, "short").data
    assert b"Notes must be between" in write_notes(client, booking_id, "x" * 2001).data


def test_cannot_add_notes_before_the_lesson(client, auth, app):
    booking_id = book_lesson(client, auth, app, in_past=False)
    auth.login(email="mark@swingslot.demo")
    response = client.get(f"/lessons/{booking_id}/notes", follow_redirects=True)
    assert b"You can add notes once the lesson has started." in response.data


def test_other_instructor_cannot_write_or_read_notes(client, auth, app):
    booking_id = book_lesson(client, auth, app)
    auth.login(email="laura@swingslot.demo")
    assert client.get(f"/lessons/{booking_id}/notes").status_code == 404
    assert client.get(f"/lessons/{booking_id}").status_code == 404


def test_other_golfer_cannot_read_notes(client, auth, app):
    booking_id = book_lesson(client, auth, app)
    auth.register(email="nosy@example.com")
    assert client.get(f"/lessons/{booking_id}").status_code == 404


def test_golfer_cannot_use_notes_form(client, auth, app):
    booking_id = book_lesson(client, auth, app)
    auth.login()
    assert client.get(f"/lessons/{booking_id}/notes").status_code == 403


def test_notes_are_escaped(client, auth, app):
    booking_id = book_lesson(client, auth, app)
    auth.login(email="mark@swingslot.demo")
    page = write_notes(client, booking_id, "<script>alert('x')</script> great lesson").get_data(as_text=True)
    assert "<script>alert" not in page
    assert "&lt;script&gt;" in page
