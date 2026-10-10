import json
import math
import os
import secrets
import sqlite3
import sys
import uuid
from datetime import datetime, timezone
from functools import wraps
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, g, jsonify, request, send_from_directory, session

from database import connect, decode_json, initialize_database


ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")
TASKS = {
    "dsa": [
        ("Programming foundations", "Variables, loops, functions, and complexity", 35),
        ("Arrays & strings", "Traverse, search, and transform common sequences", 40),
        ("Hash maps & sets", "Use lookups to improve problem-solving time", 40),
        ("Two pointers", "Solve pair and range problems efficiently", 35),
        ("Stacks & queues", "Model ordered and first-in-first-out data", 40),
        ("Linked lists", "Build, traverse, and reverse linked structures", 40),
        ("Trees & recursion", "Practice traversal and recursive reasoning", 45),
        ("Graphs & interview patterns", "Apply BFS, DFS, and mixed patterns", 50),
    ],
    "web": [
        ("HTML & the web", "Create accessible semantic page structure", 35),
        ("CSS foundations", "Style typography, spacing, and responsive layouts", 40),
        ("JavaScript basics", "Use variables, functions, events, and the DOM", 45),
        ("Responsive components", "Build reusable interfaces for every screen", 45),
        ("APIs & async JavaScript", "Fetch, load, and display remote data", 45),
        ("State & forms", "Validate inputs and build interactive flows", 45),
        ("Build a portfolio project", "Ship a complete project and write its README", 60),
        ("Deploy & polish", "Deploy, test, and present your work", 45),
    ],
    "aptitude": [
        ("Number sense", "Build confidence with arithmetic and estimation", 25),
        ("Ratios & percentages", "Practice proportions, discounts, and change", 30),
        ("Averages & mixtures", "Solve common quantitative reasoning questions", 30),
        ("Time, speed & work", "Learn efficient approaches to rate problems", 35),
        ("Profit, loss & interest", "Work through business-math essentials", 30),
        ("Logical reasoning", "Practice patterns, arrangements, and deductions", 35),
        ("Data interpretation", "Read charts and reason from the numbers", 35),
        ("Timed mixed practice", "Complete a short mock set and review errors", 40),
    ],
}

ASSESSMENT_BANK = {
    "programming": [
        ("programming-complexity", "A loop visits each item in a list once. What is its time complexity?", ["O(1)", "O(log n)", "O(n)", "O(n²)"], 2, "The loop visits n items once, so the running time is O(n)."),
        ("programming-stack", "Which data structure is commonly used to manage nested function calls?", ["Queue", "Stack", "Hash map", "Graph"], 1, "Function calls are pushed and returned in last-in, first-out order."),
    ],
    "dsa": [
        ("dsa-stack", "Which structure is usually used to manage function calls?", ["Queue", "Stack", "Hash map", "Graph"], 1, "Function calls return in last-in, first-out order."),
        ("dsa-binary", "What is the time complexity of binary search on a sorted array?", ["O(1)", "O(log n)", "O(n)", "O(n²)"], 1, "Each comparison discards half the sorted search space."),
    ],
    "web": [
        ("web-nav", "Which HTML element best describes a group of main site navigation links?", ["<div>", "<nav>", "<span>", "<footer>"], 1, "The nav element represents a section of navigation links."),
        ("web-grid", "Which CSS layout is designed for a two-dimensional row-and-column grid?", ["Flexbox", "Grid", "Float", "Inline"], 1, "CSS Grid is designed for two-dimensional row-and-column layouts."),
    ],
    "aptitude": [
        ("apt-discount", "A product priced at 800 is discounted by 25%. What is the sale price?", ["200", "575", "600", "625"], 2, "25% of 800 is 200; 800 - 200 = 600."),
        ("apt-work", "If 3 workers finish a task in 12 days, how many days would 6 equally productive workers take?", ["3", "6", "9", "24"], 1, "Doubling workers halves the time: 12 × 3 / 6 = 6 days."),
    ],
}

INTERVIEW_BANK = [
    {"id": "fundamentals-complexity", "category": "Programming", "topic": "Programming fundamentals", "difficulty": "Beginner", "prompt": "A loop visits every array item once. Explain its time complexity and why.", "concepts": ["each item", "linear", "o(n)", "input size"], "outline": "The loop performs constant work for each of n items, so its running time is O(n)."},
    {"id": "dsa-arrays", "category": "DSA", "topic": "Arrays", "difficulty": "Beginner", "prompt": "How would you find the largest value in an unsorted integer array in one pass? State the complexity.", "concepts": ["maximum", "largest", "scan", "iterate", "o(n)", "constant space"], "outline": "Initialize the maximum from the first item, scan remaining values and update it. This is O(n) time and O(1) extra space."},
    {"id": "dsa-two-pointers", "category": "DSA", "topic": "Two pointers", "difficulty": "Intermediate", "prompt": "For a sorted array, explain how two pointers find a pair that sums to a target.", "concepts": ["sorted", "left", "right", "sum", "target", "move", "o(n)"], "outline": "Start at both ends; move the left pointer when the sum is too small and the right pointer when it is too large. Each pointer moves at most n times."},
    {"id": "web-html", "category": "Web development", "topic": "Semantic HTML", "difficulty": "Beginner", "prompt": "Why use semantic HTML landmarks instead of generic div elements everywhere?", "concepts": ["meaning", "semantic", "accessibility", "screen reader", "keyboard", "structure"], "outline": "Semantic elements communicate purpose, provide assistive-technology landmarks and native keyboard behavior."},
    {"id": "web-async", "category": "Web development", "topic": "Fetch and async JavaScript", "difficulty": "Intermediate", "prompt": "How should an interface handle loading, HTTP errors, network errors, and successful fetch requests?", "concepts": ["loading", "response.ok", "status", "network", "error", "success", "render"], "outline": "Show loading, check response.ok, render a successful response, and handle network or parsing errors with clear feedback."},
    {"id": "fundamentals-sql", "category": "Database and SQL", "topic": "Relational databases", "difficulty": "Beginner", "prompt": "What is a primary key and why should it be unique and non-null?", "concepts": ["unique", "identify", "row", "not null", "foreign key"], "outline": "A primary key uniquely identifies each row and can be referenced by foreign keys."},
    {"id": "fundamentals-ai", "category": "AI and machine learning fundamentals", "topic": "Model evaluation", "difficulty": "Intermediate", "prompt": "Distinguish training, validation and test data, and describe a risk of repeatedly tuning on the test set.", "concepts": ["training", "fit", "validation", "tune", "test", "unseen", "leak", "overfit"], "outline": "Training fits model parameters, validation supports model selection, and test data gives a final unseen estimate. Repeated test-set tuning leaks information and biases results."},
    {"id": "aptitude-probability", "category": "Aptitude", "topic": "Probability", "difficulty": "Beginner", "prompt": "A fair six-sided die is rolled. What is the probability of an even result? Explain the sample space.", "concepts": ["six", "2, 4, 6", "three", "3/6", "1/2"], "outline": "The even outcomes are 2, 4 and 6: three of six equally likely outcomes, so the probability is 1/2."},
    {"id": "hr-star", "category": "HR and behavioral interviews", "topic": "Behavioral communication", "difficulty": "Beginner", "prompt": "Describe a real challenge you faced while learning or working, what you did, and what you learned.", "concepts": ["situation", "task", "action", "result", "learned", "specific"], "outline": "Use a real example and briefly explain the situation, your responsibility, the specific actions you took and the outcome/learning."},
]
INTERVIEW_CATEGORIES = [
    "Programming", "DSA", "Web development", "Database and SQL",
    "AI and machine learning fundamentals", "Aptitude",
    "HR and behavioral interviews", "Mixed interview",
]


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.update(
        DATABASE=os.environ.get("LAUNCHPAD_DATABASE", str(ROOT / "instance" / "launchpad.sqlite3")),
        SECRET_KEY=os.environ.get("LAUNCHPAD_SECRET_KEY"),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        MAX_CONTENT_LENGTH=64 * 1024,
    )
    if test_config:
        app.config.update(test_config)
    if not app.config["SECRET_KEY"]:
        if os.environ.get("FLASK_ENV") == "production":
            raise RuntimeError("LAUNCHPAD_SECRET_KEY must be set in production.")
        app.config["SECRET_KEY"] = secrets.token_hex(32)
        print("WARNING: using an ephemeral development session key.", file=sys.stderr)
    elif (os.environ.get("FLASK_ENV") == "production" and not app.config.get("TESTING")
          and (len(app.config["SECRET_KEY"]) < 32
               or app.config["SECRET_KEY"] == "replace-with-a-random-secret-before-deployment")):
        raise RuntimeError("Use a private LAUNCHPAD_SECRET_KEY with at least 32 characters in production.")
    secure_cookie = os.environ.get("COOKIE_SECURE")
    if secure_cookie is None:
        secure_cookie = "true" if os.environ.get("FLASK_ENV") == "production" else "false"
    app.config["SESSION_COOKIE_SECURE"] = str(secure_cookie).lower() in ("1", "true", "yes")
    initialize_database(app.config["DATABASE"])

    @app.before_request
    def protect_api_mutations():
        if not request.path.startswith("/api/") or request.method in ("GET", "HEAD", "OPTIONS"):
            return None
        origin = request.headers.get("Origin")
        if origin:
            from urllib.parse import urlsplit
            if urlsplit(origin).netloc != request.host:
                return jsonify(error="Cross-origin request rejected."), 403
        token = session.get("csrf_token")
        if not token or not secrets.compare_digest(token, request.headers.get("X-CSRF-Token", "")):
            return jsonify(error="Missing or invalid CSRF token."), 403
        return None

    @app.teardown_appcontext
    def close_database(_error=None):
        db = g.pop("db", None)
        if db is not None:
            db.close()

    def db():
        if "db" not in g:
            g.db = connect(app.config["DATABASE"])
        return g.db

    def percentage(value):
        return math.floor(value + 0.5)

    def json_body():
        if not request.is_json:
            return None
        value = request.get_json(silent=True)
        return value if isinstance(value, dict) else None

    def current_student_id():
        return session.get("student_id")

    def require_student(function):
        @wraps(function)
        def wrapped(*args, **kwargs):
            student_id = current_student_id()
            if not student_id or not db().execute("SELECT 1 FROM students WHERE id = ?", (student_id,)).fetchone():
                return jsonify(error="Create a profile before using this resource."), 401
            g.student_id = student_id
            return function(*args, **kwargs)
        return wrapped

    def award(student_id, achievement_id, title, detail):
        db().execute(
            "INSERT OR IGNORE INTO achievements (id, student_id, title, detail) VALUES (?, ?, ?, ?)",
            (achievement_id, student_id, title, detail[:500]),
        )

    def seed_tasks(student_id):
        for skill, entries in TASKS.items():
            for index, (title, topic, minutes) in enumerate(entries):
                db().execute(
                    """INSERT OR IGNORE INTO learning_tasks
                       (id, student_id, title, topic, skill, difficulty, estimated_minutes)
                       VALUES (?, ?, ?, ?, ?, 'Beginner', ?)""",
                    (f"{skill}-{index}", student_id, title, topic, skill, minutes),
                )

    def interview_result(row):
        answers = db().execute(
            "SELECT question_id, question, submitted_answer, evaluation_score, feedback_json FROM interview_answers WHERE session_id = ? ORDER BY id",
            (row["id"],),
        ).fetchall()
        return {
            "id": row["id"], "role": row["target_role"], "category": row["category"],
            "difficulty": row["difficulty"], "status": row["status"],
            "score": row["overall_score"], "created_at": row["created_at"],
            "completed_at": row["completed_at"],
            "duration_seconds": row["duration_seconds"],
            "time_limit_seconds": row["time_limit_seconds"],
            "answers": [{
                "question_id": answer["question_id"], "question": answer["question"],
                "answer": answer["submitted_answer"], "score": answer["evaluation_score"],
                "feedback": decode_json(answer["feedback_json"], {}),
            } for answer in answers],
            "question_ids": decode_json(row["question_ids_json"], []),
        }

    @app.get("/")
    def index():
        return send_from_directory(ROOT, "index.html")

    @app.get("/<path:filename>")
    def project_asset(filename):
        if filename.endswith((".js", ".css", ".png", ".svg", ".ico")):
            return send_from_directory(ROOT, filename)
        return jsonify(error="Not found."), 404

    @app.get("/api/health")
    def health():
        session.setdefault("csrf_token", secrets.token_urlsafe(32))
        return jsonify(status="ok", csrf_token=session["csrf_token"], persistence="SQLite")

    @app.get("/api/profile")
    def get_profile():
        student_id = current_student_id()
        row = db().execute("SELECT * FROM students WHERE id = ?", (student_id,)).fetchone() if student_id else None
        if not row:
            return jsonify(profile=None)
        resume = db().execute("SELECT * FROM resumes WHERE student_id = ?", (student_id,)).fetchone()
        return jsonify(profile={
            "name": row["name"], "branch": row["branch"], "semester": row["semester"],
            "cgpa": row["cgpa"], "target_role": row["target_role"],
            "study_hours": row["study_hours"], "created_at": row["created_at"],
            "resume": {
                "career_objective": resume["career_objective"],
                "education": resume["education"],
                "technical_skills": resume["technical_skills"],
                "projects": decode_json(resume["projects_json"], []),
                "certifications": decode_json(resume["certifications_json"], []),
                "achievements": decode_json(resume["achievements_json"], []),
            } if resume else None,
        })

    @app.post("/api/profile")
    def save_profile():
        body = json_body()
        if body is None:
            return jsonify(error="Send a JSON object."), 400
        name = body.get("name")
        branch = body.get("branch", "Not specified")
        role = body.get("target_role", "")
        semester = body.get("semester", 1)
        cgpa = body.get("cgpa")
        hours = body.get("study_hours", 1)
        if not isinstance(name, str) or not name.strip() or len(name.strip()) > 100:
            return jsonify(error="Name is required and must be at most 100 characters."), 400
        if not isinstance(branch, str) or not branch.strip() or len(branch.strip()) > 100:
            return jsonify(error="Branch must be 1–100 characters."), 400
        if not isinstance(role, str) or len(role.strip()) > 100:
            return jsonify(error="Target role must be at most 100 characters."), 400
        if isinstance(semester, bool) or not isinstance(semester, int) or not 1 <= semester <= 12:
            return jsonify(error="Semester must be a whole number from 1 to 12."), 400
        if cgpa is not None and (isinstance(cgpa, bool) or not isinstance(cgpa, (int, float)) or not 0 <= cgpa <= 10):
            return jsonify(error="CGPA must be between 0 and 10 or null."), 400
        if isinstance(hours, bool) or not isinstance(hours, (int, float)) or not 0 < hours <= 12:
            return jsonify(error="Study hours must be greater than 0 and at most 12."), 400
        student_id = current_student_id() or str(uuid.uuid4())
        with db():
            db().execute(
                """INSERT INTO students (id, name, branch, semester, cgpa, target_role, study_hours)
                   VALUES (?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(id) DO UPDATE SET name=excluded.name, branch=excluded.branch,
                   semester=excluded.semester, cgpa=excluded.cgpa, target_role=excluded.target_role,
                   study_hours=excluded.study_hours, updated_at=strftime('%Y-%m-%dT%H:%M:%fZ','now')""",
                (student_id, name.strip(), branch.strip(), semester, cgpa, role.strip(), hours),
            )
            seed_tasks(student_id)
            db().execute("INSERT OR IGNORE INTO resumes (student_id) VALUES (?)", (student_id,))
        session["student_id"] = student_id
        return jsonify(profile={"name": name.strip(), "branch": branch.strip(), "semester": semester, "cgpa": cgpa, "target_role": role.strip(), "study_hours": hours}), 201

    @app.get("/api/progress")
    @require_student
    def progress():
        student_id = g.student_id
        totals = db().execute(
            "SELECT COUNT(*) AS total, SUM(completed) AS completed FROM learning_tasks WHERE student_id = ?",
            (student_id,),
        ).fetchone()
        scores = db().execute(
            """SELECT a.skill, a.score, a.created_at FROM assessments a
               JOIN (SELECT skill, MAX(id) AS latest FROM assessments WHERE student_id = ? GROUP BY skill) last
               ON a.id=last.latest""", (student_id,),
        ).fetchall()
        interview = db().execute(
            "SELECT AVG(overall_score) AS average, COUNT(*) AS count FROM interview_sessions WHERE student_id = ? AND status='completed'",
            (student_id,),
        ).fetchone()
        recent_activity = db().execute(
            """SELECT kind, description, happened_at FROM (
                 SELECT 'learning task' AS kind, title AS description, completed_at AS happened_at
                 FROM learning_tasks WHERE student_id=? AND completed=1
                 UNION ALL
                 SELECT 'assessment', skill || ' skill assessment', created_at
                 FROM assessments WHERE student_id=?
                 UNION ALL
                 SELECT 'interview', target_role || ' interview', completed_at
                 FROM interview_sessions WHERE student_id=? AND status='completed'
               ) WHERE happened_at IS NOT NULL ORDER BY happened_at DESC LIMIT 10""",
            (student_id, student_id, student_id),
        ).fetchall()
        return jsonify(
            overall_progress=percentage(100 * (totals["completed"] or 0) / totals["total"]) if totals["total"] else 0,
            tasks={"completed": totals["completed"] or 0, "pending": totals["total"] - (totals["completed"] or 0)},
            assessments={row["skill"]: {"score": row["score"], "at": row["created_at"]} for row in scores},
            interview={"average_score": percentage(interview["average"]) if interview["average"] is not None else None, "completed_sessions": interview["count"]},
            recent_activity=[dict(row) for row in recent_activity],
        )

    @app.get("/api/roadmap")
    @require_student
    def roadmap():
        rows = db().execute("SELECT * FROM learning_tasks WHERE student_id = ? ORDER BY skill, id", (g.student_id,)).fetchall()
        tasks = [{
            "id": row["id"], "title": row["title"], "topic": row["topic"],
            "skill": row["skill"], "difficulty": row["difficulty"],
            "estimated_minutes": row["estimated_minutes"], "completed": bool(row["completed"]),
            "completed_at": row["completed_at"],
        } for row in rows]
        pending = next((task for task in tasks if not task["completed"]), None)
        return jsonify(tasks=tasks, recommended_next_task=pending)

    @app.get("/api/recommendations")
    @require_student
    def recommendations():
        profile = db().execute("SELECT target_role, study_hours FROM students WHERE id=?", (g.student_id,)).fetchone()
        tasks = db().execute(
            "SELECT * FROM learning_tasks WHERE student_id=? ORDER BY skill, id",
            (g.student_id,),
        ).fetchall()
        assessments = db().execute(
            """SELECT a.skill, a.score FROM assessments a
               JOIN (SELECT skill, MAX(id) AS latest FROM assessments WHERE student_id=? GROUP BY skill) last
               ON a.id=last.latest""", (g.student_id,),
        ).fetchall()
        latest_scores = {row["skill"]: row["score"] for row in assessments}
        interview_rows = db().execute(
            """SELECT a.question_id, a.evaluation_score FROM interview_answers a
               JOIN interview_sessions s ON s.id=a.session_id
               WHERE s.student_id=?""", (g.student_id,),
        ).fetchall()
        question_skills = {
            question["id"]: ("web" if question["category"] == "Web development" else
                             "aptitude" if question["category"] == "Aptitude" else
                             None if question["category"] == "HR and behavioral interviews" else "dsa")
            for question in INTERVIEW_BANK
        }
        interview_values = {"dsa": [], "web": [], "aptitude": []}
        for row in interview_rows:
            skill = question_skills.get(row["question_id"])
            if skill:
                interview_values[skill].append(row["evaluation_score"])
        target_role = profile["target_role"].lower()
        role_skills = (
            {"aptitude", "web"} if "data analyst" in target_role else
            {"dsa", "aptitude"} if "ai" in target_role else
            {"web", "dsa"} if "web" in target_role else
            {"dsa", "web"} if any(term in target_role for term in ("software", "developer", "engineer")) else set()
        )
        output = []
        for skill, display in (("dsa", "DSA"), ("web", "Web development"), ("aptitude", "Aptitude")):
            skill_tasks = [task for task in tasks if task["skill"] == skill]
            completed = sum(bool(task["completed"]) for task in skill_tasks)
            progress_score = percentage(100 * completed / len(skill_tasks)) if skill_tasks else 0
            practice_score = latest_scores.get(skill)
            interview_score = percentage(sum(interview_values[skill]) / len(interview_values[skill])) if interview_values[skill] else None
            factors = [(progress_score, .5)]
            if practice_score is not None:
                factors.append((practice_score, .2))
            if interview_score is not None:
                factors.append((interview_score, .3))
            weight = sum(item[1] for item in factors)
            evidence_score = percentage(sum(value * factor for value, factor in factors) / weight)
            priority = min(100, evidence_score + (5 if skill in role_skills else 0))
            preferred_start = max(0, 2 if evidence_score >= 50 else 0)
            pending = next((task for task in skill_tasks if not task["completed"] and int(task["id"].rsplit("-", 1)[1]) >= preferred_start), None)
            if pending is None:
                pending = next((task for task in skill_tasks if not task["completed"]), None)
            minutes = pending["estimated_minutes"] if pending else 0
            study_minutes = max(15, round(profile["study_hours"] * 60))
            output.append({
                "skill": skill, "label": display, "evidence_score": evidence_score,
                "priority": priority, "progress_score": progress_score,
                "practice_score": practice_score, "interview_score": interview_score,
                "recommended_task": {
                    "id": pending["id"], "topic": pending["topic"], "title": pending["title"],
                    "difficulty": pending["difficulty"], "estimated_minutes": minutes,
                    "estimated_days": max(1, (minutes + study_minutes - 1) // study_minutes),
                } if pending else None,
                "reason": (
                    "Weakest available evidence first; roadmap progress contributes 50%, "
                    "latest objective assessment 20%, and interview practice 30% (missing evidence is reweighted)."
                ),
            })
        output.sort(key=lambda item: (item["priority"], item["evidence_score"]))
        return jsonify(
            recommendations=output[:3],
            scoring={"progress": .5, "assessment": .2, "interview": .3, "missing_evidence": "weights are renormalized"},
        )

    @app.post("/api/tasks/<task_id>/complete")
    @require_student
    def complete_task(task_id):
        if len(task_id) > 20:
            return jsonify(error="Invalid task identifier."), 400
        with db():
            cursor = db().execute(
                """UPDATE learning_tasks SET completed=1,
                   completed_at=COALESCE(completed_at, strftime('%Y-%m-%dT%H:%M:%fZ','now'))
                   WHERE student_id=? AND id=?""", (g.student_id, task_id),
            )
            if cursor.rowcount == 0:
                return jsonify(error="Task not found."), 404
            count = db().execute("SELECT COUNT(*) FROM learning_tasks WHERE student_id=? AND completed=1", (g.student_id,)).fetchone()[0]
            if count == 1:
                award(g.student_id, "first-learning-task", "First learning task", "Completed the first roadmap learning task.")
        return jsonify(task_id=task_id, completed=True), 200

    @app.get("/api/assessments")
    @require_student
    def get_assessments():
        rows = db().execute("SELECT id, skill, score, total, created_at FROM assessments WHERE student_id=? ORDER BY id DESC LIMIT 50", (g.student_id,)).fetchall()
        questions = {skill: [{"id": q[0], "question": q[1], "options": q[2]} for q in values] for skill, values in ASSESSMENT_BANK.items()}
        return jsonify(questions=questions, history=[dict(row) for row in rows])

    @app.post("/api/assessments")
    @require_student
    def submit_assessment():
        body = json_body()
        if (body is None or not isinstance(body.get("skill"), str)
                or body.get("skill") not in ASSESSMENT_BANK or not isinstance(body.get("answers"), list)):
            return jsonify(error="Provide a supported skill and an answers array."), 400
        skill = body["skill"]
        questions = {item[0]: item for item in ASSESSMENT_BANK[skill]}
        answers = body["answers"]
        if not 1 <= len(answers) <= len(questions):
            return jsonify(error="Answer between 1 and the available number of questions."), 400
        seen = set()
        correct = 0
        feedback = []
        for answer in answers:
            if (not isinstance(answer, dict) or not isinstance(answer.get("question_id"), str)
                    or answer.get("question_id") not in questions):
                return jsonify(error="An answer contains an unknown question identifier."), 400
            question_id = answer["question_id"]
            choice = answer.get("selected_option")
            if question_id in seen or isinstance(choice, bool) or not isinstance(choice, int) or not 0 <= choice < 4:
                return jsonify(error="Answers must use unique question IDs and valid option numbers."), 400
            seen.add(question_id)
            item = questions[question_id]
            is_correct = choice == item[3]
            correct += int(is_correct)
            feedback.append({"question_id": question_id, "correct": is_correct, "explanation": item[4]})
        score = percentage(100 * correct / len(answers))
        with db():
            cursor = db().execute(
                "INSERT INTO assessments (student_id, skill, score, total, answers_json) VALUES (?, ?, ?, ?, ?)",
                (g.student_id, skill, score, len(answers), json.dumps(answers)),
            )
            if db().execute("SELECT COUNT(*) FROM assessments WHERE student_id=?", (g.student_id,)).fetchone()[0] == 1:
                award(g.student_id, "first-assessment", "First assessment", "Completed the first server-scored placement assessment.")
        return jsonify(id=cursor.lastrowid, skill=skill, score=score, correct=correct, total=len(answers), feedback=feedback), 201

    @app.get("/api/interviews")
    @require_student
    def list_interviews():
        rows = db().execute("SELECT * FROM interview_sessions WHERE student_id=? ORDER BY created_at DESC LIMIT 100", (g.student_id,)).fetchall()
        return jsonify(sessions=[interview_result(row) for row in rows])

    @app.post("/api/interviews")
    @require_student
    def create_interview():
        body = json_body()
        if body is None:
            return jsonify(error="Send a JSON object."), 400
        role = body.get("target_role")
        category = body.get("category", "Mixed interview")
        difficulty = body.get("difficulty", "Beginner")
        count = body.get("question_count", 5)
        duration = body.get("duration_seconds", 0)
        requested_ids = body.get("question_ids")
        if not isinstance(role, str) or not role.strip() or len(role.strip()) > 100:
            return jsonify(error="A target role of 1–100 characters is required."), 400
        if category not in INTERVIEW_CATEGORIES:
            return jsonify(error="Unsupported interview category."), 400
        if difficulty not in ("Beginner", "Intermediate", "Advanced", "All levels"):
            return jsonify(error="Unsupported interview difficulty."), 400
        if isinstance(count, bool) or not isinstance(count, int) or not 1 <= count <= 15:
            return jsonify(error="Question count must be from 1 to 15."), 400
        if isinstance(duration, bool) or not isinstance(duration, int) or not 0 <= duration <= 7200:
            return jsonify(error="Duration must be 0–7200 seconds."), 400
        allowed = {
            "Programming": {"Programming", "DSA", "Web development", "Database and SQL", "AI and machine learning fundamentals"},
            "DSA": {"DSA"}, "Web development": {"Web development"},
            "Database and SQL": {"Database and SQL"},
            "AI and machine learning fundamentals": {"AI and machine learning fundamentals"},
            "Aptitude": {"Aptitude"}, "HR and behavioral interviews": {"HR and behavioral interviews"},
        }
        pool = [q for q in INTERVIEW_BANK if category == "Mixed interview" or q["category"] in allowed.get(category, set())]
        if difficulty != "All levels":
            pool = [q for q in pool if q["difficulty"] == difficulty]
        if requested_ids is not None:
            known = {question["id"]: question for question in INTERVIEW_BANK}
            if (not isinstance(requested_ids, list) or not requested_ids or len(requested_ids) > 15
                    or any(not isinstance(question_id, str) or question_id not in known for question_id in requested_ids)
                    or len(set(requested_ids)) != len(requested_ids)):
                return jsonify(error="question_ids must be a unique list of supported question identifiers."), 400
            selected = [known[question_id] for question_id in requested_ids]
            if any(question not in pool for question in selected):
                return jsonify(error="A selected question does not match the requested category or difficulty."), 400
        else:
            selected = []
        if not pool:
            return jsonify(error="No questions match these options."), 422
        if not selected:
            import random
            selected = random.SystemRandom().sample(pool, min(count, len(pool)))
        interview_id = str(uuid.uuid4())
        with db():
            db().execute(
                """INSERT INTO interview_sessions
                   (id, student_id, target_role, category, difficulty, question_ids_json, time_limit_seconds)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (interview_id, g.student_id, role.strip(), category, difficulty, json.dumps([q["id"] for q in selected]), duration),
            )
        return jsonify(
            id=interview_id, role=role.strip(), category=category, difficulty=difficulty,
            status="in_progress", time_limit_seconds=duration,
            questions=[{key: question[key] for key in ("id", "category", "topic", "difficulty", "prompt")} for question in selected],
        ), 201

    @app.get("/api/interviews/<session_id>")
    @require_student
    def get_interview(session_id):
        row = db().execute("SELECT * FROM interview_sessions WHERE id=? AND student_id=?", (session_id, g.student_id)).fetchone()
        if not row:
            return jsonify(error="Interview not found."), 404
        return jsonify(session=interview_result(row))

    @app.post("/api/interviews/<session_id>/answers")
    @require_student
    def save_interview_answer(session_id):
        body = json_body()
        if body is None:
            return jsonify(error="Send a JSON object."), 400
        question_id, answer = body.get("question_id"), body.get("answer")
        row = db().execute("SELECT * FROM interview_sessions WHERE id=? AND student_id=?", (session_id, g.student_id)).fetchone()
        if not row:
            return jsonify(error="Interview not found."), 404
        if row["status"] != "in_progress":
            return jsonify(error="This interview has already been completed."), 409
        question = next((item for item in INTERVIEW_BANK if item["id"] == question_id), None)
        if not question or question_id not in decode_json(row["question_ids_json"], []):
            return jsonify(error="Question does not belong to this interview."), 400
        if not isinstance(answer, str) or not answer.strip() or len(answer) > 6000:
            return jsonify(error="Answer must contain 1–6000 characters."), 400
        words = set(__import__("re").findall(r"[a-z0-9+#]+", answer.lower()))
        matched = [concept for concept in question["concepts"] if set(__import__("re").findall(r"[a-z0-9+#]+", concept.lower())).issubset(words)]
        score = percentage(100 * len(matched) / len(question["concepts"]))
        feedback = {
            "method": "rule-based keyword coverage; not AI",
            "strengths": matched,
            "missing": [concept for concept in question["concepts"] if concept not in matched],
            "suggested_answer": question["outline"],
            "outline": question["outline"],
            "revision_topic": question["topic"],
            "nextTopic": question["topic"],
        }
        try:
            with db():
                db().execute(
                    """INSERT INTO interview_answers
                       (session_id, question_id, question, submitted_answer, evaluation_score, feedback_json)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (session_id, question_id, question["prompt"], answer.strip(), score, json.dumps(feedback)),
                )
        except sqlite3.IntegrityError:
            return jsonify(error="An answer for this question was already submitted."), 409
        return jsonify(question_id=question_id, score=score, feedback=feedback), 201

    @app.post("/api/interviews/<session_id>/complete")
    @require_student
    def complete_interview(session_id):
        row = db().execute("SELECT * FROM interview_sessions WHERE id=? AND student_id=?", (session_id, g.student_id)).fetchone()
        if not row:
            return jsonify(error="Interview not found."), 404
        if row["status"] == "completed":
            return jsonify(error="This interview is already completed."), 409
        scores = db().execute("SELECT AVG(evaluation_score) AS score, COUNT(*) AS total FROM interview_answers WHERE session_id=?", (session_id,)).fetchone()
        score = percentage(scores["score"] or 0)
        started_at = datetime.fromisoformat(row["created_at"].replace("Z", "+00:00"))
        elapsed_seconds = max(0, int((datetime.now(timezone.utc) - started_at).total_seconds()))
        if row["time_limit_seconds"]:
            elapsed_seconds = min(elapsed_seconds, row["time_limit_seconds"])
        with db():
            db().execute(
                "UPDATE interview_sessions SET status='completed', overall_score=?, duration_seconds=?, completed_at=? WHERE id=? AND student_id=?",
                (score, elapsed_seconds, datetime.now(timezone.utc).isoformat(), session_id, g.student_id),
            )
            if db().execute("SELECT COUNT(*) FROM interview_sessions WHERE student_id=? AND status='completed'", (g.student_id,)).fetchone()[0] == 1:
                award(g.student_id, "first-mock-interview", "First mock interview", "Completed the first server-scored practice interview.")
        saved = db().execute("SELECT * FROM interview_sessions WHERE id=?", (session_id,)).fetchone()
        return jsonify(session=interview_result(saved)), 200

    @app.get("/api/achievements")
    @require_student
    def get_achievements():
        rows = db().execute("SELECT id, title, detail, awarded_at FROM achievements WHERE student_id=? ORDER BY awarded_at DESC", (g.student_id,)).fetchall()
        return jsonify(achievements=[dict(row) for row in rows])

    @app.get("/api/resume")
    @require_student
    def get_resume():
        row = db().execute("SELECT * FROM resumes WHERE student_id=?", (g.student_id,)).fetchone()
        if not row:
            return jsonify(error="Resume not found."), 404
        return jsonify(resume={
            "career_objective": row["career_objective"], "education": row["education"],
            "technical_skills": row["technical_skills"],
            "projects": decode_json(row["projects_json"], []),
            "certifications": decode_json(row["certifications_json"], []),
            "achievements": decode_json(row["achievements_json"], []),
            "updated_at": row["updated_at"],
        })

    @app.put("/api/resume")
    @require_student
    def update_resume():
        body = json_body()
        if body is None:
            return jsonify(error="Send a JSON object."), 400
        text_fields = ("career_objective", "education", "technical_skills")
        limits = {"career_objective": 1500, "education": 2000, "technical_skills": 1500}
        for key in text_fields:
            value = body.get(key, "")
            if not isinstance(value, str) or len(value) > limits[key]:
                return jsonify(error=f"{key} must be text no longer than {limits[key]} characters."), 400
        arrays = {}
        for key, max_items, max_length in (("projects", 20, 3000), ("certifications", 50, 500)):
            value = body.get(key, [])
            if not isinstance(value, list) or len(value) > max_items or any(not isinstance(item, str) or not item.strip() or len(item) > max_length for item in value):
                return jsonify(error=f"{key} must contain at most {max_items} non-empty text entries (maximum {max_length} characters each)."), 400
            arrays[key] = [item.strip() for item in value]
        achievements = body.get("achievements", [])
        if not isinstance(achievements, list) or len(achievements) > 100:
            return jsonify(error="achievements must be a list of at most 100 entries."), 400
        for item in achievements:
            if not isinstance(item, dict) or any(
                not isinstance(item.get(field, ""), str) or len(item.get(field, "")) > limit
                for field, limit in (("id", 100), ("title", 120), ("issuer", 100), ("date", 20), ("detail", 1000))
            ) or not item.get("title", "").strip():
                return jsonify(error="Each achievement needs a title and bounded text fields."), 400
        with db():
            db().execute(
                """INSERT INTO resumes (student_id, career_objective, education, technical_skills, projects_json, certifications_json, achievements_json)
                   VALUES (?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(student_id) DO UPDATE SET career_objective=excluded.career_objective,
                   education=excluded.education, technical_skills=excluded.technical_skills,
                   projects_json=excluded.projects_json, certifications_json=excluded.certifications_json,
                   achievements_json=excluded.achievements_json,
                   updated_at=strftime('%Y-%m-%dT%H:%M:%fZ','now')""",
                    (g.student_id, body.get("career_objective", ""), body.get("education", ""),
                     body.get("technical_skills", ""), json.dumps(arrays["projects"]), json.dumps(arrays["certifications"]),
                     json.dumps(achievements)),
            )
        return jsonify(saved=True), 200

    @app.post("/api/session/logout")
    def logout():
        session.clear()
        return jsonify(ok=True)

    @app.errorhandler(413)
    def request_too_large(_error):
        return jsonify(error="Request body exceeds the 64 KB limit."), 413

    @app.errorhandler(404)
    def not_found(error):
        if request.path.startswith("/api/"):
            return jsonify(error="API resource not found."), 404
        return error.get_response()

    @app.errorhandler(405)
    def method_not_allowed(error):
        if request.path.startswith("/api/"):
            return jsonify(error="HTTP method is not supported for this API route."), 405
        return error.get_response()

    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error("Unhandled server error: %s", error)
        return jsonify(error="An internal server error occurred."), 500

    return app


if __name__ == "__main__":
    production = os.environ.get("FLASK_ENV") == "production"
    app = create_app()
    app.run(host=os.environ.get("HOST", "127.0.0.1"), port=int(os.environ.get("PORT", "5000")), debug=not production)
