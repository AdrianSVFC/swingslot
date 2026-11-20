"""Instructor profile set-up and editing (GOLF-7)."""
from flask import Blueprint, flash, g, redirect, render_template, request, url_for

from . import LESSON_TYPES
from .auth import role_required
from .db import get_db

bp = Blueprint("instructors", __name__, url_prefix="/instructor")


def validate_profile(form):
    errors = []
    if not form.get("location", "").strip():
        errors.append("Location is required so golfers can find you.")
    if len(form.get("bio", "").strip()) < 20:
        errors.append("Write a short bio (at least 20 characters).")
    chosen = form.getlist("lesson_types")
    if not chosen or any(t not in LESSON_TYPES for t in chosen):
        errors.append("Choose at least one lesson type.")
    try:
        price = int(form.get("price", ""))
        if not 10 <= price <= 500:
            raise ValueError
    except ValueError:
        errors.append("Price must be a whole number between 10 and 500.")
    return errors


@bp.route("/profile", methods=("GET", "POST"))
@role_required("instructor")
def profile():
    db = get_db()
    current = db.execute(
        "SELECT * FROM instructor_profiles WHERE user_id = ?", (g.user["id"],)
    ).fetchone()

    if request.method == "POST":
        errors = validate_profile(request.form)
        if not errors:
            db.execute(
                "INSERT INTO instructor_profiles (user_id, location, bio, lesson_types, price)"
                " VALUES (?, ?, ?, ?, ?)"
                " ON CONFLICT(user_id) DO UPDATE SET location = excluded.location,"
                " bio = excluded.bio, lesson_types = excluded.lesson_types, price = excluded.price",
                (g.user["id"], request.form["location"].strip(), request.form["bio"].strip(),
                 ",".join(request.form.getlist("lesson_types")), int(request.form["price"])),
            )
            db.commit()
            flash("Your profile was saved.", "success")
            return redirect(url_for("instructors.profile"))
        for message in errors:
            flash(message, "danger")
        current = {
            "location": request.form.get("location", ""),
            "bio": request.form.get("bio", ""),
            "lesson_types": ",".join(request.form.getlist("lesson_types")),
            "price": request.form.get("price", ""),
        }

    selected = (current["lesson_types"].split(",") if current and current["lesson_types"] else [])
    return render_template("instructors/profile.html", profile=current, selected=selected)
