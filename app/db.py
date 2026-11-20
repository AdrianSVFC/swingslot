"""Database helpers: one SQLite connection per request, plus setup and seeding."""
import sqlite3
from pathlib import Path

import click
from flask import current_app, g


def get_db():
    """Return the SQLite connection for the current request, opening it if needed."""
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row  # rows behave like dicts: row["name"]
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(_error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """Create all tables from schema.sql (this deletes existing data)."""
    schema = Path(__file__).with_name("schema.sql").read_text(encoding="utf-8")
    get_db().executescript(schema)


def ensure_db(app):
    """Create and seed the database the first time the app starts."""
    Path(app.config["DATABASE"]).parent.mkdir(parents=True, exist_ok=True)
    with app.app_context():
        db = get_db()
        exists = db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='users'"
        ).fetchone()
        if not exists:
            init_db()
            if app.config.get("SEED_DEMO_DATA"):
                from .seed import seed_demo_data
                seed_demo_data(db)


@click.command("init-db")
def init_db_command():
    """flask --app app init-db : reset the database and load demo data."""
    from .seed import seed_demo_data
    init_db()
    seed_demo_data(get_db())
    click.echo("Database initialized with demo data.")


def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
