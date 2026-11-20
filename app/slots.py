"""Instructors add and remove the time slots golfers can book (GOLF-22)."""
from datetime import datetime

from flask import Blueprint, abort, flash, g, redirect, render_template, request, url_for

from .auth import role_required
from .db import get_db

bp = Blueprint("slots", __name__, url_prefix="/instructor/slots")


def parse_slot(date_text, time_text):
    """Turn the form's date and time into "YYYY-MM-DDTHH:MM", or raise ValueError."""
    starts = datetime.strptime(f"{date_text} {time_text}", "%Y-%m-%d %H:%M")
    if starts <= datetime.now():
        raise ValueError("past")
    return starts.strftime("%Y-%m-%dT%H:%M")


@bp.route("/", methods=("GET", "POST"))
@role_required("instructor")
def manage():
    db = get_db()
    if request.method == "POST":
        try:
            starts_at = parse_slot(request.form.get("date", ""), request.form.get("time", ""))
        except ValueError:
            flash("Choose a valid date and time in the future.", "danger")
        else:
            exists = db.execute(
                "SELECT 1 FROM time_slots WHERE instructor_id = ? AND starts_at = ?",
                (g.user["id"], starts_at),
            ).fetchone()
            if exists:
                flash("You already have a slot at that time.", "warning")
            else:
                db.execute(
                    "INSERT INTO time_slots (instructor_id, starts_at) VALUES (?, ?)",
                    (g.user["id"], starts_at),
                )
                db.commit()
                flash("Time slot added.", "success")
        return redirect(url_for("slots.manage"))

    now = datetime.now().strftime("%Y-%m-%dT%H:%M")
    slots = db.execute(
        "SELECT s.id, s.starts_at, u.name AS student_name"
        " FROM time_slots s"
        " LEFT JOIN bookings b ON b.slot_id = s.id"
        " LEFT JOIN users u ON u.id = b.student_id"
        " WHERE s.instructor_id = ? AND s.starts_at > ?"
        " ORDER BY s.starts_at",
        (g.user["id"], now),
    ).fetchall()
    return render_template("instructors/slots.html", slots=slots)


@bp.route("/<int:slot_id>/delete", methods=("POST",))
@role_required("instructor")
def delete(slot_id):
    db = get_db()
    slot = db.execute(
        "SELECT s.*, b.id AS booking_id FROM time_slots s"
        " LEFT JOIN bookings b ON b.slot_id = s.id WHERE s.id = ?",
        (slot_id,),
    ).fetchone()
    if slot is None or slot["instructor_id"] != g.user["id"]:
        abort(404)
    if slot["booking_id"] is not None:
        flash("This slot is already booked, so it can't be removed.", "warning")
    else:
        db.execute("DELETE FROM time_slots WHERE id = ?", (slot_id,))
        db.commit()
        flash("Time slot removed.", "info")
    return redirect(url_for("slots.manage"))
