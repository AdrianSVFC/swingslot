"""GOLF-22: instructors add and remove available time slots."""
from datetime import date, timedelta

from conftest import get_csrf

from app.db import get_db

TOMORROW = (date.today() + timedelta(days=1)).isoformat()


def add_slot(client, day=TOMORROW, time="10:00"):
    token = get_csrf(client, "/instructor/slots/")
    return client.post("/instructor/slots/", data={"csrf_token": token, "date": day, "time": time},
                       follow_redirects=True)


def test_instructor_adds_slot(client, auth):
    auth.login(email="mark@swingslot.demo")
    response = add_slot(client, time="06:15")
    assert b"Time slot added." in response.data
    assert b"6:15 AM" in response.data


def test_duplicate_and_past_slots_rejected(client, auth):
    auth.login(email="mark@swingslot.demo")
    add_slot(client, time="06:15")
    assert b"already have a slot" in add_slot(client, time="06:15").data
    assert b"in the future" in add_slot(client, day="2020-01-01").data


def test_instructor_removes_open_slot(client, auth, app):
    auth.login(email="mark@swingslot.demo")
    add_slot(client, time="06:15")
    with app.app_context():
        slot_id = get_db().execute(
            "SELECT id FROM time_slots WHERE starts_at = ?", (f"{TOMORROW}T06:15",)
        ).fetchone()["id"]
    token = get_csrf(client, "/instructor/slots/")
    response = client.post(f"/instructor/slots/{slot_id}/delete", data={"csrf_token": token},
                           follow_redirects=True)
    assert b"Time slot removed." in response.data


def test_cannot_remove_another_instructors_slot(client, auth, app):
    with app.app_context():
        slot_id = get_db().execute(
            "SELECT s.id FROM time_slots s JOIN users u ON u.id = s.instructor_id"
            " WHERE u.email = 'laura@swingslot.demo' LIMIT 1"
        ).fetchone()["id"]
    auth.login(email="mark@swingslot.demo")
    token = get_csrf(client, "/instructor/slots/")
    assert client.post(f"/instructor/slots/{slot_id}/delete", data={"csrf_token": token}).status_code == 404


def test_golfer_cannot_manage_slots(client, auth):
    auth.login()
    assert client.get("/instructor/slots/").status_code == 403
