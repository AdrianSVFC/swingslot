# SwingSlot ⛳ — Golf Lesson Booking App

SwingSlot is a web application that makes booking golf lessons simple for both golfers and instructors.

## The problem

Many golf instructors still schedule lessons through text messages, phone calls and paper calendars. That leads to double bookings, missed lessons and lost notes about each student's progress. SwingSlot gives instructors one place to publish their availability and gives golfers a quick way to find and book an open time slot. After each lesson, AI turns the instructor's notes into a summary and a practice plan.

## Target users

- **Golf instructors** (independent coaches and club pros) who need to manage their schedule and keep track of their students.
- **Golfers of every level** who want to book lessons easily and remember what they worked on.

## Core features (planned)

1. **Accounts & profiles**: sign up and log in as a student or an instructor. Instructor profiles show bio, location, lesson types and prices.
2. **Instructor availability**: instructors add and remove open time slots.
3. **Booking & dashboard**: students browse instructors, book or cancel lessons, and see upcoming and past lessons.
4. **AI lesson insights**: the instructor's lesson notes become a clear summary and a weekly practice plan for the student.

## Planned technology stack

| Layer | Technology |
|---|---|
| Frontend | HTML, CSS, JavaScript, Jinja2 templates |
| Backend | Python 3, Flask, Flask-Login, Flask-WTF |
| Database | SQLite (development), PostgreSQL (production), SQLAlchemy ORM |
| AI | OpenAI API (lesson summaries and practice plans) |
| Deployment | Render |
| Tools | Git and GitHub, Jira (Scrum), Confluence |

## Planned project structure

```
swingslot/
├── app/
│   ├── __init__.py        # app factory
│   ├── models.py          # User, InstructorProfile, TimeSlot, Booking, LessonNote
│   ├── auth/              # register, login, logout
│   ├── booking/           # availability, browse, book, cancel, dashboards
│   ├── ai/                # summary and practice-plan generation
│   ├── templates/
│   └── static/            # css, js
├── tests/
├── requirements.txt
├── .env.example
└── run.py
```

## Getting started (will be completed during development)

```bash
git clone https://github.com/AdrianSVFC/swingslot.git
cd swingslot
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # add SECRET_KEY and OPENAI_API_KEY
flask run
```

## Roadmap

- **Sprint 1: MVP (end of Unit 12)**: accounts, instructor availability, browse and book lessons, dashboards, deploy to Render.
- **Sprint 2: Final App (end of Unit 14)**: profile editing, cancellations, AI lesson summaries and practice plans, lesson history, polish.

## Project management

- Jira board: https://swingslot-project.atlassian.net/jira/software/c/projects/GOLF/boards/2/backlog
- Confluence space: https://swingslot-project.atlassian.net/wiki/spaces/SWING/overview

## Status

🚧 Planning phase. Development starts in Sprint 1.
