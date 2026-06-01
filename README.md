# SmartPlan — AI-Powered Lesson Planning

> Generate lesson plans, worksheets, quizzes, presentations, and revision materials in seconds — powered by AI.

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.2-black?logo=flask)](https://flask.palletsprojects.com)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen)](https://github.com/fadizaza/SmartPlan_Generator/pulls)

---

## What is SmartPlan?

SmartPlan helps educators create comprehensive teaching materials in one click. Built by teachers, for teachers.

- **Assessment Questions** — MCQs, short answer, true/false, fill-in-the-blank, matching
- **Worksheets** — Custom activities at any difficulty level
- **Lesson Plans** — Structured, outcome-aligned plans
- **Presentations** — PowerPoint decks with auto-sized content
- **Revision Materials** — Summaries and study guides

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python, Flask, SQLAlchemy |
| Frontend | HTML, CSS, JavaScript, Bootstrap 5 |
| AI | Google Gemini, Mistral AI |
| Documents | python-docx, python-pptx |
| Auth | Flask-Login |

---

## Quick Start

```bash
# Clone
git clone https://github.com/fadizaza/SmartPlan_Generator.git
cd SmartPlan_Generator

# Virtual environment
python -m venv venv
source venv/bin/activate    # Linux/Mac
venv\Scripts\activate       # Windows

# Install dependencies
pip install -r requirements.txt

# Set up your API keys
cp .env.example .env        # Then edit .env with your keys

# Initialize the database
python init_db.py

# Run
python app.py
```

Open **http://127.0.0.1:5000** — default login: `admin` / `password123`

---

## Project Structure

```
├── app.py                  # Flask routes and logic
├── lesson_generation.py    # AI integration & document generation
├── models.py               # User model (SQLAlchemy)
├── web_utils.py            # Helper utilities
├── utils.py                # File/content utilities
├── templates/              # Jinja2 HTML templates
├── static/                 # JS, CSS assets
├── outputFiles/            # Generated files (per user)
├── .env.example            # Template for environment variables
└── requirements.txt
```

---

## Contributing

All contributions welcome — docs, tests, features, bug fixes, UI/UX.

### Ideas to get started

- [ ] Add PDF export support
- [ ] Add dark mode theme
- [ ] Translate UI to other languages
- [ ] Add image generation for slides
- [ ] Add bulk import of student rosters
- [ ] Improve worksheet activity variety
- [ ] Write unit tests
- [ ] Docker production setup
- [ ] Add API rate limiting
- [ ] Build a REST API for LMS integration

### Guidelines

1. Fork the repo and create a branch: `git checkout -b feature/your-idea`
2. Make your changes
3. Run the app and verify it works
4. Open a pull request

---

## Deployment

**PythonAnywhere** (easiest): upload files, configure WSGI to `app.py`.

**Docker**: the included `Dockerfile` builds a container-ready image.

---

## License

MIT — use it, modify it, share it.

---

## Credits

Originally built for ACTVET (Abu Dhabi Center for Technical and Vocational Education and Training). Converted from a desktop Tkinter app to a web application.
