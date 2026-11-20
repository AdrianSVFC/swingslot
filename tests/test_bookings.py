"""GOLF-27 / GOLF-32: browse instructors and book an open slot."""
from conftest import get_csrf

from app.db import get_db


def first_open_slot(app, email="laura@swingslot.demo"):
    with app.app_context():
        row = get_db().execute(
            "SELECT s.id, s.instructor_id FROM time_slots s JOIN users u ON u.id = s.instructor_id"
            " WHERE u.email = ? ORDER BY s.starts_at LIMIT 1", (email,)
        ).fetchone()
        return row["id"], row["instructor_id"]


def test_browse_lists_demo_instructors(client):
    response = client.get("/instructors")
    assert response.status_code == 200
    assert b"Laura Mendez" in response.data
    assert b"4 instructor(s) found" in response.data


def test_browse_filters(client):
    response = client.get("/instructors?location=Tupelo%2C+MS")
    assert b"Mark Collins" in response.data
    assert b"Laura Mendez" not in response.data
    response = client.get("/instructors?type=Putting")
    assert b"Sofia Ruiz" in response.data
    assert b"James Porter" not in response.data


def test_detail_shows_open_slots(client, app):
    _, instructor_id = first_open_slot(app)
    response = client.get(f"/instructors/{instructor_id}")
    assert b"Open time slots" in response.data
    assert b"weatherBox" in response.data


def test_golfer_books_slot_and_it_disappears(client, auth, app):
    slot_id, instructor_id = first_open_slot(app)
    auth.login()
    token = get_csrf(client, f"/instructors/{instructor_id}")
    response = client.post(f"/book/{slot_id}", data={"csrf_token": token}, follow_redirects=True)
    assert b"Lesson booked!" in response.data
    page = client.get(f"/instructors/{instructor_id}").get_data(as_text=True)
    assert f'action="/book/{slot_id}"' not in page


def test_slot_cannot_be_booked_twice(client, auth, app):
    slot_id, instructor_id = first_open_slot(app)
    auth.login()
    token = get_csrf(client, f"/instructors/{instructor_id}")
    client.post(f"/book/{slot_id}", data={"csrf_token": token})
    auth.logout()
    auth.register(email="second@example.com")
    token = get_csrf(client, f"/instructors/{instructor_id}")
    response = client.post(f"/book/{slot_id}", data={"csrf_token": token}, follow_redirects=True)
    assert b"just booked by someone else" in response.data


def test_must_log_in_to_book(client, app):
    slot_id, _ = first_open_slot(app)
    token = get_csrf(client)  # visitors see no booking form, so take the token from the login page
    response = client.post(f"/book/{slot_id}", data={"csrf_token": token})
    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]
