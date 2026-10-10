# Launchpad

Launchpad is a placement-preparation dashboard for college students. This project retains its existing single-page interface and adds a Flask API with SQLite persistence for browser-session profiles, roadmap tasks, objective assessments, interview practice, achievements, and resume data.

## Features

- Existing Launchpad dashboard, DSA/Web/Aptitude learning hub, roadmap, resume UI, and responsive layout.
- Flask JSON APIs, SQLite tables with foreign keys and constraints, and parameterized SQL.
- Browser-session-bound demo profiles (not password authentication).
- Server-scored six-question DSA/Web/Aptitude skill check.
- Server-saved roadmap task completion and progress summaries.
- Server-selected and server-scored rule-based mock interviews for supported questions.
- Resume/profile autosave to SQLite; achievements include server-awarded milestones.
- CSRF token checks for state-changing API calls, same-origin request checks, size limits, and input validation.

The interview evaluator is a transparent keyword-coverage checklist, not an AI model. No third-party AI credentials or provider are configured.

## Technology and architecture

- Python 3.10+ with Flask
- SQLite (database defaults to `instance/launchpad.sqlite3`)
- Existing frontend assets at project root (`index.html`, `learning-data.js`, `interview-engine.js`)
- Automated API tests use a separate temporary SQLite database for every test run.

The app serves the existing `index.html` from Flask; it does not maintain a second template copy. Open the page through Flask to enable backend persistence and server-side scoring. Opening `index.html` directly as `file://` is a local-only fallback; API-backed features require the Flask server.

## Database tables

- `students`: profile fields and timestamps
- `learning_tasks`: seeded roadmap tasks and completion state
- `assessments`: server-calculated score history and submitted answer selections
- `interview_sessions`: role/category/difficulty, question IDs, status, and server-calculated result
- `interview_answers`: submitted text, evaluation score, and feedback
- `achievements`: idempotently awarded server milestones
- `resumes`: objective, education, skills, project/certification lists, and student-supplied achievements

SQLite initializes these tables at application startup. Live databases and the `instance/` directory are excluded from Git.

## Install and run on Windows

Open PowerShell in the project folder:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python app.py
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000). Keep the terminal window open while using the app. To stop the local server, press `Ctrl+C`.

If PowerShell blocks virtual-environment activation, run the app without activating it:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

For an existing `.env`, replace the placeholder `LAUNCHPAD_SECRET_KEY` with a private random value. Generate one with:

```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

For another local port, set `$env:PORT = "8000"` before `python app.py`, then open `http://127.0.0.1:8000`.

## API routes

All API responses are JSON. Mutating requests require the CSRF token returned by `GET /api/health` in the `X-CSRF-Token` header.

| Method | Route | Purpose |
| --- | --- | --- |
| GET | `/api/health` | Health and per-browser CSRF token |
| GET, POST | `/api/profile` | Read or create/update the profile bound to this browser session |
| GET | `/api/progress` | Calculate actual saved task, assessment, and interview progress |
| GET | `/api/roadmap` | Return seeded tasks and the first pending recommendation |
| GET | `/api/recommendations` | Rank next roadmap topics from saved task/assessment/interview evidence |
| POST | `/api/tasks/<task_id>/complete` | Idempotently complete a student's roadmap task |
| GET, POST | `/api/assessments` | Read question/options and history; submit selections for server scoring |
| GET, POST | `/api/interviews` | List saved sessions or create a server-selected interview |
| GET | `/api/interviews/<session_id>` | Read an interview belonging to the current browser session |
| POST | `/api/interviews/<session_id>/answers` | Save and score one answer on the server |
| POST | `/api/interviews/<session_id>/complete` | Finalize and persist the server-calculated interview score |
| GET | `/api/achievements` | Read actual server-awarded milestones |
| GET, PUT | `/api/resume` | Read or update validated resume details |
| POST | `/api/session/logout` | Clear this browser's server-side profile association |

The internal student ID is never accepted as authorization. Resource queries are scoped to the signed Flask session. There is no user-password or email-verification system: the profile selector is still a demo convenience, not secure authentication. Anyone with access to the same browser session can act as that browser's student.

## Recommendations and scoring

- Progress is calculated as completed seeded tasks divided by the 24 seeded roadmap tasks; the browser's percentage is not accepted by the API.
- Skill-check scores are calculated from the selected options and answer keys retained in `app.py`. The API ignores any client-supplied score.
- Interview evaluation is `100 × matched question-specific concepts / total question-specific concepts`, rounded to the nearest integer. Feedback returns matched/missing concepts, a suggested answer outline, and a revision topic. This heuristic can mis-score paraphrases and should be treated as practice feedback, not a hiring assessment.
- Recommendations calculate per-skill evidence as 50% completed roadmap tasks, 20% latest objective assessment, and 30% interview feedback; unavailable evidence is omitted and remaining weights renormalized. Role-related skills get a five-point sort tie-break. The API returns the next pending roadmap topic, difficulty, and estimated time using the saved study-hours target.
- No synthetic historical chart/activity records are generated.

## Tests

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Tests create and delete an isolated temporary SQLite database. They cover initialization, profile validation/persistence, browser-session access isolation, CSRF, task completion, server scoring, interview answer/result persistence, duplicate submission, achievements, and resume validation.

## Security and limitations

- Run behind HTTPS in production, set a long random `LAUNCHPAD_SECRET_KEY`, and set `FLASK_ENV=production`. Production mode refuses to start without a configured secret and turns off Flask debug mode.
- Use a production WSGI server and a persistent private disk for SQLite when deploying; do not use Flask's development server as an internet-facing server.
- There is no real login/authentication, password hashing, email verification, account recovery, or multi-user authorization. Browser sessions isolate anonymous profiles, but this does not protect against a person with access to the same browser/device.
- Existing long-form learning/mock-test question data in `learning-data.js` still includes answers in public frontend assets; do not use it as a secure/proctored assessment. The six-question skill check and interview answer evaluation are server-checked.
- Uploaded documents remain in browser IndexedDB and are not uploaded to Flask. Resume PDF creation uses browser print/save-as-PDF; no server PDF dependency is used.
- Only the seeded questions/tasks are included. The bank and adaptive recommendation system are an initial implementation, not comprehensive placement coverage.
- SQLite is appropriate for local/small deployments; use an external database, backups, rate limiting, monitoring, and an authentication provider before handling real student data at scale.

## GitHub and public deployment

No Git repository was present when this project was inspected. These are instructions only; nothing has been pushed:

```powershell
git init
git add .
git status
git commit -m "Add Launchpad Flask backend"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/YOUR-REPOSITORY.git
git push -u origin main
```

Before pushing, confirm `.env`, `instance/`, and any private documents are not staged. For public hosting, push the code to your own repository, choose a Python host with persistent storage, configure `LAUNCHPAD_SECRET_KEY` and `FLASK_ENV=production` as host environment variables, set a production WSGI start command such as `gunicorn 'app:create_app()'` (add Gunicorn to the deployment dependencies if the host requires it), attach a persistent disk for `LAUNCHPAD_DATABASE`, enable HTTPS, and verify the hosted health route. This project has **not** been publicly deployed.
