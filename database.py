import json
import sqlite3
from pathlib import Path


def connect(database_path):
    connection = sqlite3.connect(database_path, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 10000")
    return connection


def initialize_database(database_path):
    Path(database_path).parent.mkdir(parents=True, exist_ok=True)
    db = connect(database_path)
    try:
        db.executescript(
            """
            PRAGMA journal_mode = WAL;
            CREATE TABLE IF NOT EXISTS students (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL CHECK(length(name) BETWEEN 1 AND 100),
                branch TEXT NOT NULL CHECK(length(branch) BETWEEN 1 AND 100),
                semester INTEGER NOT NULL CHECK(semester BETWEEN 1 AND 12),
                cgpa REAL CHECK(cgpa IS NULL OR (cgpa >= 0 AND cgpa <= 10)),
                target_role TEXT NOT NULL DEFAULT '' CHECK(length(target_role) <= 100),
                study_hours REAL NOT NULL DEFAULT 1 CHECK(study_hours > 0 AND study_hours <= 12),
                created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
                updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
            );
            CREATE TABLE IF NOT EXISTS learning_tasks (
                id TEXT NOT NULL,
                student_id TEXT NOT NULL REFERENCES students(id) ON DELETE CASCADE,
                title TEXT NOT NULL CHECK(length(title) <= 160),
                topic TEXT NOT NULL CHECK(length(topic) <= 160),
                skill TEXT NOT NULL CHECK(skill IN ('dsa','web','aptitude')),
                difficulty TEXT NOT NULL DEFAULT 'Beginner',
                estimated_minutes INTEGER NOT NULL CHECK(estimated_minutes BETWEEN 1 AND 600),
                completed INTEGER NOT NULL DEFAULT 0 CHECK(completed IN (0,1)),
                completed_at TEXT,
                PRIMARY KEY(student_id, id)
            );
            CREATE TABLE IF NOT EXISTS assessments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT NOT NULL REFERENCES students(id) ON DELETE CASCADE,
                skill TEXT NOT NULL CHECK(skill IN ('programming','dsa','web','aptitude')),
                score INTEGER NOT NULL CHECK(score BETWEEN 0 AND 100),
                total INTEGER NOT NULL CHECK(total > 0),
                answers_json TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
            );
            CREATE TABLE IF NOT EXISTS interview_sessions (
                id TEXT PRIMARY KEY,
                student_id TEXT NOT NULL REFERENCES students(id) ON DELETE CASCADE,
                target_role TEXT NOT NULL CHECK(length(target_role) BETWEEN 1 AND 100),
                category TEXT NOT NULL CHECK(length(category) <= 40),
                difficulty TEXT NOT NULL CHECK(length(difficulty) <= 20),
                question_ids_json TEXT NOT NULL,
                duration_seconds INTEGER NOT NULL DEFAULT 0 CHECK(duration_seconds BETWEEN 0 AND 86400),
                time_limit_seconds INTEGER NOT NULL DEFAULT 0 CHECK(time_limit_seconds BETWEEN 0 AND 7200),
                status TEXT NOT NULL DEFAULT 'in_progress' CHECK(status IN ('in_progress','completed')),
                overall_score INTEGER CHECK(overall_score IS NULL OR overall_score BETWEEN 0 AND 100),
                created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
                completed_at TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_interview_student_created
                ON interview_sessions(student_id, created_at);
            CREATE TABLE IF NOT EXISTS interview_answers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL REFERENCES interview_sessions(id) ON DELETE CASCADE,
                question_id TEXT NOT NULL,
                question TEXT NOT NULL CHECK(length(question) <= 1200),
                submitted_answer TEXT NOT NULL CHECK(length(submitted_answer) BETWEEN 1 AND 6000),
                evaluation_score INTEGER NOT NULL CHECK(evaluation_score BETWEEN 0 AND 100),
                feedback_json TEXT NOT NULL,
                UNIQUE(session_id, question_id)
            );
            CREATE TABLE IF NOT EXISTS achievements (
                id TEXT NOT NULL,
                student_id TEXT NOT NULL REFERENCES students(id) ON DELETE CASCADE,
                title TEXT NOT NULL CHECK(length(title) BETWEEN 1 AND 120),
                detail TEXT NOT NULL DEFAULT '' CHECK(length(detail) <= 500),
                awarded_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
                PRIMARY KEY(student_id, id)
            );
            CREATE TABLE IF NOT EXISTS resumes (
                student_id TEXT PRIMARY KEY REFERENCES students(id) ON DELETE CASCADE,
                career_objective TEXT NOT NULL DEFAULT '' CHECK(length(career_objective) <= 1500),
                education TEXT NOT NULL DEFAULT '' CHECK(length(education) <= 2000),
                technical_skills TEXT NOT NULL DEFAULT '' CHECK(length(technical_skills) <= 1500),
                projects_json TEXT NOT NULL DEFAULT '[]',
                certifications_json TEXT NOT NULL DEFAULT '[]',
                achievements_json TEXT NOT NULL DEFAULT '[]',
                updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
            );
            """
        )
        resume_columns = {row["name"] for row in db.execute("PRAGMA table_info(resumes)")}
        if "achievements_json" not in resume_columns:
            db.execute("ALTER TABLE resumes ADD COLUMN achievements_json TEXT NOT NULL DEFAULT '[]'")
        interview_columns = {row["name"] for row in db.execute("PRAGMA table_info(interview_sessions)")}
        if "time_limit_seconds" not in interview_columns:
            db.execute("ALTER TABLE interview_sessions ADD COLUMN time_limit_seconds INTEGER NOT NULL DEFAULT 0")
        db.commit()
    finally:
        db.close()


def decode_json(value, fallback):
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return fallback
