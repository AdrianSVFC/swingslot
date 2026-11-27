"""GOLF-37: golfers cancel a booked lesson (24-hour rule) and instructors see the cancellation.

Tests written with help from Claude (AI).
"""
from datetime import datetime, timedelta

from conftest import get_csrf

from app.bookings import can_cancel
from app.db import get_db


def book_slot_days_ahead(client, app, days=3, email="mark@swingslot.demo"):
    """Book the first open slot that starts at least `days` days from now.

    Returns (slot_id, instructor_id, booking_id). The golfer must already be logged in.
    """
    after = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%dT%H:%M")
    with app.app_context():
        slot = get_db().execute(
            "SELECT s.id, s.instructor_id FROM time_slots s JOIN users u ON u.id = s.instructor_id"
            " WHERE u.email = ? AND s.starts_at > ? ORDER BY s.starts_at LIMIT 1",
            (email, after),
        ).fetchone()
    token = get_csrf(client, f"/instructors/{slot['instructor_id']}")
    client.post(f"/book/{slot['id']}", data={"csrf_token": token})
    with app.app_context():
        booking = get_db().execute("SELECT id FROM bookings WHERE slot_id = ?", (slot["id"],)).fetchone()
    return slot["id"], slot["instructor_id"], booking["id"]


def cancel(client, booking_id):
    token = get_csrf(client, "/dashboard")
    return client.post(f"/bookings/{booking_id}/cancel", data={"csrf_token": token}, follow_redirects=True)


def test_can_cancel_rule():
    now = datetime(2026, 12, 1, 10, 0)
    assert can_cancel("2026-12-02T10:00", now)        # exactly 24 hours before: allowed
    assert not can_cancel("2026-12-02T09:59", now)    # 23h59m before: too late
    assert not can_cancel("2026-11-30T10:00", now)    # past lesson


def test_dashboard_shows_cancel_button(client, auth, app):
    auth.login()
    _, _, booking_id = book_slot_days_ahead(client, app)
    page = client.get("/dashboard").get_data(as_text=True)
    assert f'action="/bookings/{booking_id}/cancel"' in page
    assert "return confirm(" in page


def test_golfer_cancels_and_slot_reopens(client, auth, app):
    auth.login()
    slot_id, instructor_id, booking_id = book_slot_days_ahead(client, app)
    response = cancel(client, booking_id)
    assert b"Lesson cancelled" in response.data
    assert b"Upcoming lessons (0)" in response.data
    # The slot can be booked again
    page = client.get(f"/instructors/{instructor_id}").get_data(as_text=True)
    assert f'action="/book/{slot_id}"' in page


def test_cannot_cancel_within_24_hours(client, auth, app):
    auth.login()
    _, _, booking_id = book_slot_days_ahead(client, app)
    soon = (datetime.now() + timedelta(hours=5)).strftime("%Y-%m-%dT%H:07")
    with app.app_context():
        db = get_db()
        db.execute(
            "UPDATE time_slots SET starts_at = ? WHERE id = (SELECT slot_id FROM bookings WHERE id = ?)",
            (soon, booking_id),
        )
        db.commit()
    response = cancel(client, booking_id)
    assert b"more than 24 hours before" in response.data
    assert b"Upcoming lessons (1)" in response.data
    assert b"Starts in less than 24 h" in response.data


def test_cannot_cancel_someone_elses_booking(client, auth, app):
    auth.login()
    _, _, booking_id = book_slot_days_ahead(client, app)
    auth.logout()
    auth.register(email="other@example.com")
    token = get_csrf(client, "/dashboard")
    response = client.post(f"/bookings/{booking_id}/cancel", data={"csrf_token": token})
    assert response.status_code == 404


def test_instructor_cannot_use_cancel_route(client, auth, app):
    auth.login()
    _, _, booking_id = book_slot_days_ahead(client, app)
    auth.logout()
    auth.login(email="mark@swingslot.demo")
    token = get_csrf(client, "/dashboard")
    assert client.post(f"/bookings/{booking_id}/cancel", data={"csrf_token": token}).status_code == 403


def test_instructor_sees_cancellation(client, auth, app):
    auth.login()
    _, _, booking_id = book_slot_days_ahead(client, app)
    cancel(client, booking_id)
    auth.logout()
    auth.login(email="mark@swingslot.demo")
    response = client.get("/dashboard")
    assert b"Recent cancellations (1)" in response.data
    assert b"Demo Golfer" in response.data
