"""Golfer profile: handicap, level and goals (GOLF-17, GOLF-18, GOLF-19).

AI-generated: written with Claude (Anthropic) and reviewed before merging (see README > AI tool usage).

Instructors see this information next to each booked lesson (GOLF-20), so they know
the golfer's level before the lesson starts.
"""
from flask import Blueprint, flash, g, redirect, render_template, request, url_for

from .auth import role_required
from .db import get_db

bp = Blueprint("golfers", __name__, url_prefix="/golfer")

LEVELS = ["Beginner", "Intermediate", "Advanced"]
MAX_HANDICAP = 54      # highest handicap allowed by the World Handicap System
MAX_GOALS_LENGTH = 500


def parse_handicap(text):
    """'' -> None (no handicap yet), '18.4' -> 18.4. Raises ValueError if out of range."""
    text = (text or "").strip().replace(",", ".")
    if not text:
        return None
    value = round(float(text), 1)
    if not 0 <= value <= MAX_HANDICAP:
        raise ValueError("out of range")
    return value


def validate_profile(form):
    """Return (errors, cleaned_values) for the golfer profile form."""
    errors = []
    handicap = None
    try:
        handicap = parse_handicap(form.get("handicap"))
    except ValueError:
        errors.append(f"Handicap must be a number between 0 and {MAX_HANDICAP} (or leave it empty).")
    level = form.get("level", "")
    if level not in LEVELS:
        errors.append("Choose your level.")
    goals = form.get("goals", "").strip()
    if len(goals) > MAX_GOALS_LENGTH:
        errors.append(f"Goals can be at most {MAX_GOALS_LENGTH} characters.")
    return errors, {"handicap": handicap, "level": level, "goals": goals}


@bp.route("/profile", methods=("GET", "POST"))
@role_required("student")
def profile():
    db = get_db()
    current = db.execute(
        "SELECT handicap, level, goals FROM student_profiles WHERE user_id = ?", (g.user["id"],)
    ).fetchone()

    if request.method == "POST":
        errors, values = validate_profile(request.form)
        if not errors:
            db.execute(
                "INSERT INTO student_profiles (user_id, handicap, level, goals) VALUES (?, ?, ?, ?)"
                " ON CONFLICT(user_id) DO UPDATE SET handicap = excluded.handicap,"
                " level = excluded.level, goals = excluded.goals, updated_at = CURRENT_TIMESTAMP",
                (g.user["id"], values["handicap"], values["level"], values["goals"]),
            )
            db.commit()
            flash("Your golfer profile was saved. Your instructors will see it with your bookings.", "success")
            return redirect(url_for("golfers.profile"))
        for message in errors:
            flash(message, "danger")
        # Show what the golfer typed so they can fix it
        current = {"handicap": request.form.get("handicap", ""), "level": request.form.get("level", ""),
                   "goals": request.form.get("goals", "")}

    return render_template("golfers/profile.html", profile=current, levels=LEVELS,
                           max_handicap=MAX_HANDICAP, max_goals=MAX_GOALS_LENGTH)
