"""Lesson notes: after a lesson the instructor writes what was worked on (GOLF-48, GOLF-50).

Only the instructor who taught the lesson can write notes, and only the golfer and that
instructor can read them (GOLF-51). Anyone else gets a 404, so lesson ids can't be probed.
"""
from datetime import datetime

from flask import Blueprint, abort, flash, g, redirect, render_template, request, url_for

from .auth import login_required, role_required
from .db import get_db

bp = Blueprint("notes", __name__, url_prefix="/lessons")

MIN_NOTES_LENGTH = 10
MAX_NOTES_LENGTH = 2000


def get_lesson(booking_id):
    """Load one booked lesson with both people and its notes (or None)."""
    return get_db().execute(
        "SELECT b.id AS booking_id, b.student_id, s.instructor_id, s.starts_at,"
        " st.name AS student_name, ins.name AS instructor_name,"
        " ln.notes, ln.updated_at AS notes_updated_at"
        " FROM bookings b JOIN time_slots s ON s.id = b.slot_id"
        " JOIN users st ON st.id = b.student_id"
        " JOIN users ins ON ins.id = s.instructor_id"
        " LEFT JOIN lesson_notes ln ON ln.booking_id = b.id"
        " WHERE b.id = ?",
        (booking_id,),
    ).fetchone()


def has_started(lesson):
    return lesson["starts_at"] <= datetime.now().strftime("%Y-%m-%dT%H:%M")


@bp.route("/<int:booking_id>")
@login_required
def detail(booking_id):
    """The lesson and its notes, for the golfer or the instructor of that lesson."""
    lesson = get_lesson(booking_id)
    if lesson is None or g.user["id"] not in (lesson["student_id"], lesson["instructor_id"]):
        abort(404)
    return render_template("lessons/detail.html", lesson=lesson, started=has_started(lesson))


@bp.route("/<int:booking_id>/notes", methods=("GET", "POST"))
@role_required("instructor")
def edit(booking_id):
    """Add or edit notes; only after the lesson has started."""
    lesson = get_lesson(booking_id)
    if lesson is None or lesson["instructor_id"] != g.user["id"]:
        abort(404)
    if not has_started(lesson):
        flash("You can add notes once the lesson has started.", "warning")
        return redirect(url_for("notes.detail", booking_id=booking_id))

    notes = lesson["notes"] or ""
    if request.method == "POST":
        notes = request.form.get("notes", "").strip()
        if not MIN_NOTES_LENGTH <= len(notes) <= MAX_NOTES_LENGTH:
            flash(f"Notes must be between {MIN_NOTES_LENGTH} and {MAX_NOTES_LENGTH} characters.", "danger")
        else:
            db = get_db()
            db.execute(
                "INSERT INTO lesson_notes (booking_id, notes) VALUES (?, ?)"
                " ON CONFLICT(booking_id) DO UPDATE SET notes = excluded.notes,"
                " updated_at = CURRENT_TIMESTAMP",
                (booking_id, notes),
            )
            db.commit()
            flash(f"Lesson notes saved. {lesson['student_name']} can read them now.", "success")
            return redirect(url_for("notes.detail", booking_id=booking_id))

    return render_template("lessons/notes_form.html", lesson=lesson, notes=notes,
                           min_length=MIN_NOTES_LENGTH, max_length=MAX_NOTES_LENGTH)
