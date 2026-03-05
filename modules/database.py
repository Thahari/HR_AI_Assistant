import sqlite3
from datetime import datetime
from pathlib import Path


DB_PATH = Path("storage/database.db")


def _utc_now():
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"


def get_connection(db_path=DB_PATH):
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(db_path)


def init_database(db_path=DB_PATH):
    with get_connection(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS interview_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                candidate_id TEXT NOT NULL UNIQUE,
                resume_text TEXT NOT NULL,
                selected_role TEXT NOT NULL,
                compatibility_score REAL NOT NULL,
                total_questions INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                hr_status TEXT NOT NULL DEFAULT 'Review',
                hr_remarks TEXT NOT NULL DEFAULT '',
                hr_reviewed_at TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS interview_responses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                question_index INTEGER NOT NULL,
                question_text TEXT NOT NULL,
                transcript_text TEXT,
                video_path TEXT,
                transcript_path TEXT,
                start_time REAL,
                end_time REAL,
                duration_seconds REAL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(session_id) REFERENCES interview_sessions(id),
                UNIQUE(session_id, question_index)
            )
            """
        )
        # Lightweight migration for existing databases created before HR review fields.
        existing_columns = {
            row[1]
            for row in conn.execute("PRAGMA table_info(interview_sessions)").fetchall()
        }
        if "hr_status" not in existing_columns:
            conn.execute(
                "ALTER TABLE interview_sessions ADD COLUMN hr_status TEXT NOT NULL DEFAULT 'Review'"
            )
        if "hr_remarks" not in existing_columns:
            conn.execute(
                "ALTER TABLE interview_sessions ADD COLUMN hr_remarks TEXT NOT NULL DEFAULT ''"
            )
        if "hr_reviewed_at" not in existing_columns:
            conn.execute(
                "ALTER TABLE interview_sessions ADD COLUMN hr_reviewed_at TEXT"
            )
        conn.commit()


def save_interview_session(
    candidate_id,
    resume_text,
    selected_role,
    compatibility_score,
    questions,
    transcripts,
    db_path=DB_PATH,
):
    init_database(db_path=db_path)
    created_at = _utc_now()

    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO interview_sessions
            (candidate_id, resume_text, selected_role, compatibility_score, total_questions, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                candidate_id,
                resume_text,
                selected_role,
                float(compatibility_score or 0.0),
                len(questions),
                created_at,
            ),
        )
        session_id = cursor.lastrowid

        for index, question in enumerate(questions):
            transcript_record = transcripts[index] if index < len(transcripts) else {}
            cursor.execute(
                """
                INSERT INTO interview_responses
                (
                    session_id,
                    question_index,
                    question_text,
                    transcript_text,
                    video_path,
                    transcript_path,
                    start_time,
                    end_time,
                    duration_seconds,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    index,
                    question,
                    transcript_record.get("transcript", ""),
                    transcript_record.get("video_path", ""),
                    transcript_record.get("transcript_path", ""),
                    transcript_record.get("start_time"),
                    transcript_record.get("end_time"),
                    transcript_record.get("duration_seconds"),
                    transcript_record.get("created_at", created_at),
                ),
            )

        conn.commit()

    return session_id


def update_hr_review(session_id, hr_status, hr_remarks="", db_path=DB_PATH):
    init_database(db_path=db_path)
    reviewed_at = _utc_now()
    with get_connection(db_path) as conn:
        conn.execute(
            """
            UPDATE interview_sessions
            SET hr_status = ?, hr_remarks = ?, hr_reviewed_at = ?
            WHERE id = ?
            """,
            (hr_status, hr_remarks, reviewed_at, session_id),
        )
        conn.commit()
