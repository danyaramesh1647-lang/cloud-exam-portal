# ☁️ Cloud Exam Portal

A cloud-based online examination platform built with Flask, PostgreSQL (Neon), and Bootstrap. Supports role-based access for admins and students, timed exams with auto-submission, automatic grading, and exam access via unique join codes.

**Live Demo:** https://cloud-exam-portal.onrender.com

*(Note: hosted on Render's free tier, so the first request after a period of inactivity may take 30-60 seconds to load while the server wakes up.)*

## Features

**For Admins**
- Create exams with custom titles and durations
- Add multiple-choice questions with a designated correct answer
- Edit questions after creation to fix mistakes
- Publish exams to generate a unique 6-character access code
- View all student submissions and scores per exam
- Delete exams (cascades to remove associated questions)

**For Students**
- Register and log in with role-based access
- Join exams using a teacher-provided access code (no public exam browsing)
- Take timed exams with a live countdown and automatic submission when time expires
- View instant results with score, percentage, and pass/fail status
- View full exam history with the option to delete individual attempts

## Tech Stack

- **Backend:** Flask (Python)
- **Database:** PostgreSQL, hosted on [Neon](https://neon.tech)
- **Authentication:** Flask-Login with hashed passwords (Werkzeug)
- **ORM:** SQLAlchemy
- **Frontend:** Bootstrap 5, Bootstrap Icons, custom CSS
- **Deployment:** Render (Gunicorn as the production server)

## Project Structure

```
cloud_exam_portal/
├── app.py                  # Routes and application logic
├── database.py             # SQLAlchemy models
├── requirements.txt        # Python dependencies
├── Procfile                # Render start command
├── templates/               # Jinja2 HTML templates
└── static/
    └── style.css            # Custom styling
```