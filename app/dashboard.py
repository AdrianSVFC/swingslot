"""Dashboard of upcoming and past lessons for golfers and instructors (GOLF-42)."""
from datetime import datetime

from flask import Blueprint, g, render_template

from .auth import login_required
from .db import get_db

bp = Blueprint("dashboard", __name__)


@bp.route("/dashboard")
@login_required
def home():
    db = get_db()
    now = datetime.now().strftime("%Y-%m-%dT%H:%M")
    cancellations = None

    if g.user["role"] == "student":
        lessons = db.execute(
            "SELECT b.id AS booking_id, s.starts_at, u.id AS other_id, u.name AS other_name,"
            " p.location, p.price, NULL AS handicap, NULL AS level, NULL AS goals"
            " FROM bookings b JOIN time_slots s ON s.id = b.slot_id"
            " JOIN users u ON u.id = s.instructor_id"
            " LEFT JOIN instructor_profiles p ON p.user_id = u.id"
            " WHERE b.student_id = ? ORDER BY s.starts_at",
            (g.user["id"],),
        ).fetchall()
        open_slots = None
    else:
        lessons = db.execute(
            "SELECT b.id AS booking_id, s.starts_at, u.id AS other_id, u.name AS other_name,"
            " NULL AS location, NULL AS price, sp.handicap, sp.level, sp.goals"
            " FROM bookings b JOIN time_slots s ON s.id = b.slot_id"
            " JOIN users u ON u.id = b.student_id"
            # GOLF-20: show the golfer's handicap, level and goals to the instructor
            " LEFT JOIN student_profiles sp ON sp.user_id = b.student_id"
            " WHERE s.instructor_id = ? ORDER BY s.starts_at",
            (g.user["id"],),
        ).fetchall()
        open_slots = db.execute(
            "SELECT COUNT(*) FROM time_slots s LEFT JOIN bookings b ON b.slot_id = s.id"
            " WHERE s.instructor_id = ? AND s.starts_at > ? AND b.id IS NULL",
            (g.user["id"], now),
        ).fetchone()[0]
        # GOLF-41: the most recent lessons golfers cancelled with this instructor
        cancellations = db.execute(
            "SELECT c.starts_at, c.cancelled_at, u.name AS student_name"
            " FROM cancellations c JOIN users u ON u.id = c.student_id"
            " WHERE c.instructor_id = ? ORDER BY c.cancelled_at DESC, c.id DESC LIMIT 5",
            (g.user["id"],),
        ).fetchall()

    upcoming = [l for l in lessons if l["starts_at"] > now]
    past = [l for l in lessons if l["starts_at"] <= now][::-1]  # most recent first
    return render_template("dashboard.html", upcoming=upcoming, past=past,
                           open_slots=open_slots, cancellations=cancellations)
