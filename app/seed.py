"""Demo data so the deployed MVP has instructors and open slots to browse."""
import os
from datetime import date, datetime, timedelta

from werkzeug.security import generate_password_hash

# Same coaches as the front-end prototype (data/instructors.json).
# days: 0 = Monday ... 6 = Sunday (Python weekday numbers)
DEMO_INSTRUCTORS = [
    {"name": "Laura Mendez", "email": "laura@swingslot.demo", "location": "Seville, Spain",
     "lat": 37.39, "lon": -5.98, "types": "Full Swing,Short Game", "price": 55,
     "bio": "PGA-certified coach who uses launch-monitor data to build simple, repeatable swings.",
     "days": [0, 2, 4], "hours": [9, 11, 16]},
    {"name": "Mark Collins", "email": "mark@swingslot.demo", "location": "Tupelo, MS",
     "lat": 34.26, "lon": -88.70, "types": "Full Swing,Junior Golf", "price": 60,
     "bio": "Former college player who loves working with juniors and new golfers.",
     "days": [1, 3, 5], "hours": [8, 10, 14]},
    {"name": "Sofia Ruiz", "email": "sofia@swingslot.demo", "location": "Seville, Spain",
     "lat": 37.39, "lon": -5.98, "types": "Putting,Short Game", "price": 45,
     "bio": "Short-game specialist focused on putting routines and green reading.",
     "days": [0, 1, 3], "hours": [10, 12, 17]},
    {"name": "James Porter", "email": "james@swingslot.demo", "location": "Memphis, TN",
     "lat": 35.15, "lon": -90.05, "types": "Full Swing,Course Strategy", "price": 75,
     "bio": "Tour-experienced coach who helps low handicappers manage the course and score better.",
     "days": [2, 4, 5], "hours": [9, 13, 15]},
]

DEMO_STUDENT = {"name": "Demo Golfer", "email": "golfer@swingslot.demo"}


def seed_demo_data(db, days_ahead=14):
    """Insert demo instructors, their weekly slots and one demo golfer."""
    password = os.environ.get("DEMO_PASSWORD", "swingslot123")
    pw_hash = generate_password_hash(password)
    today = date.today()

    for coach in DEMO_INSTRUCTORS:
        cur = db.execute(
            "INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, 'instructor')",
            (coach["name"], coach["email"], pw_hash),
        )
        user_id = cur.lastrowid
        db.execute(
            "INSERT INTO instructor_profiles (user_id, location, bio, lesson_types, price, lat, lon)"
            " VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user_id, coach["location"], coach["bio"], coach["types"], coach["price"],
             coach["lat"], coach["lon"]),
        )
        for offset in range(1, days_ahead + 1):
            day = today + timedelta(days=offset)
            if day.weekday() in coach["days"]:
                for hour in coach["hours"]:
                    starts_at = datetime(day.year, day.month, day.day, hour).strftime("%Y-%m-%dT%H:%M")
                    db.execute(
                        "INSERT INTO time_slots (instructor_id, starts_at) VALUES (?, ?)",
                        (user_id, starts_at),
                    )

    db.execute(
        "INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, 'student')",
        (DEMO_STUDENT["name"], DEMO_STUDENT["email"], pw_hash),
    )
    db.commit()
