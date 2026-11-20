"""Golfers browse instructors and their open slots (GOLF-27) and book one (GOLF-32)."""
import sqlite3
from datetime import datetime

from flask import (Blueprint, abort, current_app, flash, g, redirect, render_template,
                   request, url_for)

from .auth import role_required
from .db import get_db

bp = Blueprint("bookings", __name__)


def now_iso():
    return datetime.now().strftime("%Y-%m-%dT%H:%M")


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
