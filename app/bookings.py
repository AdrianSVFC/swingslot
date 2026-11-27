"""Golfers browse instructors (GOLF-27), book a slot (GOLF-32) and cancel a booking (GOLF-37)."""
import sqlite3
from datetime import datetime, timedelta

from flask import (Blueprint, abort, current_app, flash, g, redirect, render_template,
                   request, url_for)

from .auth import role_required
from .db import get_db

bp = Blueprint("bookings", __name__)

# GOLF-39: golfers can cancel up to this many hours before the lesson starts
# (CANCEL_NOTICE_HOURS, can_cancel() and cancel() were AI-generated with Claude)
CANCEL_NOTICE_HOURS = 24


def now_iso():
    return datetime.now().strftime("%Y-%m-%dT%H:%M")


@bp.app_template_global()
def can_cancel(starts_at, now=None):
    """True if a lesson starting at `starts_at` ("YYYY-MM-DDTHH:MM") can still be cancelled.

    Also used in dashboard.html to decide whether to show the Cancel button.
    """
    now = now or datetime.now()
    starts = datetime.strptime(starts_at, "%Y-%m-%dT%H:%M")
    return starts - now >= timedelta(hours=CANCEL_NOTICE_HOURS)


@bp.route("/instructors")
def browse():
    """List instructors with a complete profile, filtered by location and lesson type."""
    db = get_db()
    location = request.args.get("location", "")
    lesson_type = request.args.get("type", "")

    rows = db.execute(
        "SELECT u.id, u.name, p.location, p.bio, p.lesson_types, p.price,"
        " (SELECT COUNT(*) FROM time_slots s LEFT JOIN bookings b ON b.slot_id = s.id"
        "   WHERE s.instructor_id = u.id AND s.starts_at > ? AND b.id IS NULL) AS open_slots"
        " FROM users u JOIN instructor_profiles p ON p.user_id = u.id"
        " WHERE u.role = 'instructor' AND p.location != '' ORDER BY u.name",
        (now_iso(),),
    ).fetchall()

    locations = sorted({r["location"] for r in rows})
    instructors = [
        r for r in rows
        if (not location or r["location"] == location)
        and (not lesson_type or lesson_type in r["lesson_types"].split(","))
    ]
    return render_template(
        "instructors/browse.html", instructors=instructors, locations=locations,
        location=location, lesson_type=lesson_type,
    )


@bp.route("/instructors/<int:instructor_id>")
def detail(instructor_id):
    """One instructor's profile with their open (future, not booked) slots."""
    db = get_db()
    instructor = db.execute(
        "SELECT u.id, u.name, p.* FROM users u JOIN instructor_profiles p ON p.user_id = u.id"
        " WHERE u.id = ? AND u.role = 'instructor'",
        (instructor_id,),
    ).fetchone()
    if instructor is None:
        abort(404)
    slots = db.execute(
        "SELECT s.id, s.starts_at FROM time_slots s LEFT JOIN bookings b ON b.slot_id = s.id"
        " WHERE s.instructor_id = ? AND s.starts_at > ? AND b.id IS NULL ORDER BY s.starts_at",
        (instructor_id, now_iso()),
    ).fetchall()
    return render_template("instructors/detail.html", instructor=instructor, slots=slots)


@bp.route("/book/<int:slot_id>", methods=("POST",))
@role_required("student")
def book(slot_id):
    db = get_db()
    slot = db.execute("SELECT * FROM time_slots WHERE id = ?", (slot_id,)).fetchone()
    if slot is None:
        abort(404)
    if slot["starts_at"] <= now_iso():
        flash("That time has already passed.", "warning")
        return redirect(url_for("bookings.detail", instructor_id=slot["instructor_id"]))
    try:
        db.execute("INSERT INTO bookings (slot_id, student_id) VALUES (?, ?)", (slot_id, g.user["id"]))
        db.commit()
    except sqlite3.IntegrityError:
        # UNIQUE(slot_id) failed: someone else booked it a moment earlier
        flash("Sorry, that slot was just booked by someone else.", "warning")
        return redirect(url_for("bookings.detail", instructor_id=slot["instructor_id"]))
    flash("Lesson booked! You can see it in your dashboard.", "success")
    if "dashboard.home" in current_app.view_functions:
        return redirect(url_for("dashboard.home"))
    return redirect(url_for("bookings.detail", instructor_id=slot["instructor_id"]))


# --- GOLF-37 cancellations: AI-generated with Claude (Anthropic), reviewed before merging ---
@bp.route("/bookings/<int:booking_id>/cancel", methods=("POST",))
@role_required("student")
def cancel(booking_id):
    """GOLF-37: a golfer cancels their own lesson; the slot becomes bookable again."""
    db = get_db()
    booking = db.execute(
        "SELECT b.id, b.student_id, s.starts_at, s.instructor_id"
        " FROM bookings b JOIN time_slots s ON s.id = b.slot_id WHERE b.id = ?",
        (booking_id,),
    ).fetchone()
    # 404 (not 403) for other golfers' bookings, so nobody can find out which bookings exist
    if booking is None or booking["student_id"] != g.user["id"]:
        abort(404)

    if not can_cancel(booking["starts_at"]):
        flash(f"Lessons can only be cancelled more than {CANCEL_NOTICE_HOURS} hours before they start. "
              "Please contact your instructor.", "warning")
    else:
        # GOLF-41: keep a record so the instructor sees the cancellation in their dashboard
        db.execute(
            "INSERT INTO cancellations (instructor_id, student_id, starts_at) VALUES (?, ?, ?)",
            (booking["instructor_id"], g.user["id"], booking["starts_at"]),
        )
        # Deleting the booking frees the slot (UNIQUE(slot_id) no longer blocks it)
        db.execute("DELETE FROM bookings WHERE id = ?", (booking_id,))
        db.commit()
        flash("Lesson cancelled. The time slot is open again for other golfers.", "info")
    return redirect(url_for("dashboard.home"))
