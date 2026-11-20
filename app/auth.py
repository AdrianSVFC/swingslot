"""Accounts: register, log in, log out (GOLF-2, GOLF-7 registration, GOLF-12)."""
import functools
import re

from flask import (Blueprint, abort, current_app, flash, g, redirect, render_template,
                   request, session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash

from .db import get_db

bp = Blueprint("auth", __name__, url_prefix="/auth")

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MIN_PASSWORD = 8


@bp.before_app_request
def load_logged_in_user():
    """Put the logged-in user (or None) in g.user for every request."""
    user_id = session.get("user_id")
    g.user = None
    if user_id is not None:
        g.user = get_db().execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()


def login_required(view):
    @functools.wraps(view)
    def wrapped(**kwargs):
        if g.user is None:
            flash("Please log in first.", "warning")
            return redirect(url_for("auth.login", next=request.path))
        return view(**kwargs)
    return wrapped


def role_required(role):
    """Only allow users with this role (e.g. only instructors can add slots)."""
    def decorator(view):
        @functools.wraps(view)
        @login_required
        def wrapped(**kwargs):
            if g.user["role"] != role:
                abort(403)
            return view(**kwargs)
        return wrapped
    return decorator


def validate_registration(form):
    """Return a list of error messages for the sign-up form."""
    errors = []
    if not form.get("name", "").strip():
        errors.append("Name is required.")
    if not EMAIL_RE.match(form.get("email", "").strip()):
        errors.append("Enter a valid email address.")
    if len(form.get("password", "")) < MIN_PASSWORD:
        errors.append(f"Password must be at least {MIN_PASSWORD} characters.")
    if form.get("password") != form.get("confirm"):
        errors.append("Passwords do not match.")
    if form.get("role") not in ("student", "instructor"):
        errors.append("Choose whether you are a golfer or an instructor.")
    return errors


@bp.route("/register", methods=("GET", "POST"))
def register():
    form = request.form
    if request.method == "POST":
        errors = validate_registration(form)
        db = get_db()
        email = form.get("email", "").strip().lower()
        if not errors and db.execute("SELECT 1 FROM users WHERE email = ?", (email,)).fetchone():
            errors.append("An account with that email already exists.")
        if not errors:
            # GOLF-12: only a salted hash of the password is stored, never the password itself
            cur = db.execute(
                "INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, ?)",
                (form["name"].strip(), email, generate_password_hash(form["password"]), form["role"]),
            )
            if form["role"] == "instructor":
                db.execute("INSERT INTO instructor_profiles (user_id) VALUES (?)", (cur.lastrowid,))
            db.commit()
            session.clear()
            session["user_id"] = cur.lastrowid
            flash("Welcome to SwingSlot! Your account was created.", "success")
            if form["role"] == "instructor" and "instructors.profile" in current_app.view_functions:
                return redirect(url_for("instructors.profile"))
            return redirect(url_for("index"))
        for message in errors:
            flash(message, "danger")
    return render_template("auth/register.html", form=form)


@bp.route("/login", methods=("GET", "POST"))
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        user = get_db().execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        if user is None or not check_password_hash(user["password_hash"], request.form.get("password", "")):
            # Same message for both cases so attackers can't tell which emails exist
            flash("Incorrect email or password.", "danger")
        else:
            session.clear()
            session["user_id"] = user["id"]
            flash(f"Welcome back, {user['name']}!", "success")
            next_url = request.args.get("next", "")
            # Only follow local paths to avoid open redirects
            if next_url.startswith("/") and not next_url.startswith("//"):
                return redirect(next_url)
            return redirect(url_for("index"))
    return render_template("auth/login.html")


@bp.route("/logout", methods=("POST",))
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))
