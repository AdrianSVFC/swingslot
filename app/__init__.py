"""SwingSlot application factory."""
import os
import secrets
from datetime import datetime
from pathlib import Path

from flask import Flask, abort, current_app, render_template, request, session

LESSON_TYPES = ["Full Swing", "Short Game", "Putting", "Junior Golf", "Course Strategy"]


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-only-change-me"),
        DATABASE=os.environ.get("DATABASE_PATH", str(Path(app.instance_path) / "swingslot.sqlite")),
        SEED_DEMO_DATA=os.environ.get("SEED_DEMO_DATA", "1") == "1",
        CSRF_ENABLED=True,
    )
    if test_config:
        app.config.update(test_config)

    from . import db
    db.init_app(app)
    db.ensure_db(app)

    # One blueprint per feature / Jira user story
    from . import auth
    app.register_blueprint(auth.bp)         # GOLF-2, GOLF-12: accounts

    register_csrf(app)

    @app.template_filter("nice_time")
    def nice_time(iso_text):
        """'2026-11-24T09:00' -> 'Tue, Nov 24 · 9:00 AM'"""
        dt = datetime.strptime(iso_text, "%Y-%m-%dT%H:%M")
        hour = dt.hour % 12 or 12
        return f"{dt:%a, %b} {dt.day} · {hour}:{dt:%M} {'AM' if dt.hour < 12 else 'PM'}"

    @app.context_processor
    def template_helpers():
        # has_endpoint() lets base.html show nav links only for features that exist
        return {
            "has_endpoint": lambda name: name in current_app.view_functions,
            "lesson_types": LESSON_TYPES,
        }

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/health")
    def health():
        return {"status": "ok"}

    @app.errorhandler(403)
    def forbidden(_error):
        return render_template("error.html", code=403, message="You don't have access to that page."), 403

    @app.errorhandler(404)
    def not_found(_error):
        return render_template("error.html", code=404, message="Page not found."), 404

    return app


def register_csrf(app):
    """Simple CSRF protection: every POST form must send the token stored in the session."""

    def csrf_token():
        if "_csrf" not in session:
            session["_csrf"] = secrets.token_hex(16)
        return session["_csrf"]

    app.jinja_env.globals["csrf_token"] = csrf_token

    @app.before_request
    def check_csrf():
        if request.method == "POST" and app.config.get("CSRF_ENABLED", True):
            sent = request.form.get("csrf_token")
            if not sent or sent != session.get("_csrf"):
                abort(400, "Invalid or missing CSRF token.")
