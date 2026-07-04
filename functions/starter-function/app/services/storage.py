from __future__ import annotations

import hashlib
import sqlite3
from datetime import datetime
from pathlib import Path


class Storage:
    def __init__(self, db_path: str = "academasync.db") -> None:
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        cur = self.conn.cursor()
        cur.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              email TEXT UNIQUE NOT NULL,
              password_hash TEXT NOT NULL,
              academic_year TEXT,
              semester_name TEXT,
              semester_start TEXT,
              semester_end TEXT
            );

            CREATE TABLE IF NOT EXISTS subjects (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              user_id INTEGER NOT NULL,
              name TEXT NOT NULL,
              location TEXT,
              instructor TEXT,
              credits INTEGER NOT NULL,
              day_of_week TEXT NOT NULL,
              start_time TEXT NOT NULL,
              end_time TEXT NOT NULL,
              FOREIGN KEY(user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS tasks (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              user_id INTEGER NOT NULL,
              title TEXT NOT NULL,
              task_type TEXT NOT NULL,
              subject_id INTEGER,
              due_at TEXT NOT NULL,
              is_completed INTEGER NOT NULL DEFAULT 0,
              FOREIGN KEY(user_id) REFERENCES users(id),
              FOREIGN KEY(subject_id) REFERENCES subjects(id)
            );

            CREATE TABLE IF NOT EXISTS grades (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              user_id INTEGER NOT NULL,
              subject_id INTEGER NOT NULL,
              isa1 REAL NOT NULL,
              isa2 REAL NOT NULL,
              esa REAL NOT NULL,
              assignments REAL NOT NULL,
              lab_marks REAL,
              updated_at TEXT NOT NULL,
              UNIQUE(user_id, subject_id),
              FOREIGN KEY(user_id) REFERENCES users(id),
              FOREIGN KEY(subject_id) REFERENCES subjects(id)
            );
            """
        )
        self.conn.commit()

    @staticmethod
    def _hash_password(password: str) -> str:
        return hashlib.sha256(password.encode("utf-8")).hexdigest()

    def create_user(self, email: str, password: str) -> int:
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO users(email, password_hash) VALUES(?, ?)",
            (email.lower().strip(), self._hash_password(password)),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def login_user(self, email: str, password: str) -> int | None:
        cur = self.conn.cursor()
        cur.execute(
            "SELECT id, password_hash FROM users WHERE email=?",
            (email.lower().strip(),),
        )
        row = cur.fetchone()
        if not row:
            return None
        return int(row["id"]) if row["password_hash"] == self._hash_password(password) else None

    def get_user(self, user_id: int) -> sqlite3.Row | None:
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM users WHERE id=?", (user_id,))
        return cur.fetchone()

    def update_onboarding(self, user_id: int, year: str, semester: str, start: str, end: str) -> None:
        self.conn.execute(
            """UPDATE users
               SET academic_year=?, semester_name=?, semester_start=?, semester_end=?
               WHERE id=?""",
            (year, semester, start, end, user_id),
        )
        self.conn.commit()

    def add_subject(self, user_id: int, name: str, location: str, instructor: str, credits: int, day: str, start: str, end: str) -> None:
        self.conn.execute(
            """INSERT INTO subjects(user_id, name, location, instructor, credits, day_of_week, start_time, end_time)
               VALUES(?,?,?,?,?,?,?,?)""",
            (user_id, name, location, instructor, credits, day, start, end),
        )
        self.conn.commit()

    def list_subjects(self, user_id: int) -> list[sqlite3.Row]:
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM subjects WHERE user_id=? ORDER BY day_of_week, start_time", (user_id,))
        return list(cur.fetchall())

    def delete_subject(self, subject_id: int, user_id: int) -> None:
        self.conn.execute("DELETE FROM subjects WHERE id=? AND user_id=?", (subject_id, user_id))
        self.conn.commit()

    def add_task(self, user_id: int, title: str, task_type: str, due_at: str, subject_id: int | None) -> None:
        self.conn.execute(
            "INSERT INTO tasks(user_id, title, task_type, due_at, subject_id) VALUES(?,?,?,?,?)",
            (user_id, title, task_type, due_at, subject_id),
        )
        self.conn.commit()

    def list_tasks(self, user_id: int) -> list[sqlite3.Row]:
        cur = self.conn.cursor()
        cur.execute(
            """SELECT t.*, s.name AS subject_name
               FROM tasks t LEFT JOIN subjects s ON s.id=t.subject_id
               WHERE t.user_id=? ORDER BY t.due_at""",
            (user_id,),
        )
        return list(cur.fetchall())

    def toggle_task(self, task_id: int, user_id: int, completed: bool) -> None:
        self.conn.execute(
            "UPDATE tasks SET is_completed=? WHERE id=? AND user_id=?",
            (1 if completed else 0, task_id, user_id),
        )
        self.conn.commit()

    def delete_task(self, task_id: int, user_id: int) -> None:
        self.conn.execute("DELETE FROM tasks WHERE id=? AND user_id=?", (task_id, user_id))
        self.conn.commit()

    def upsert_grade(self, user_id: int, subject_id: int, isa1: float, isa2: float, esa: float, assignments: float, lab_marks: float | None) -> None:
        now = datetime.utcnow().isoformat()
        self.conn.execute(
            """INSERT INTO grades(user_id, subject_id, isa1, isa2, esa, assignments, lab_marks, updated_at)
               VALUES(?,?,?,?,?,?,?,?)
               ON CONFLICT(user_id, subject_id) DO UPDATE SET
                   isa1=excluded.isa1,
                   isa2=excluded.isa2,
                   esa=excluded.esa,
                   assignments=excluded.assignments,
                   lab_marks=excluded.lab_marks,
                   updated_at=excluded.updated_at""",
            (user_id, subject_id, isa1, isa2, esa, assignments, lab_marks, now),
        )
        self.conn.commit()

    def list_grades(self, user_id: int) -> list[sqlite3.Row]:
        cur = self.conn.cursor()
        cur.execute(
            """SELECT g.*, s.name AS subject_name, s.credits
               FROM grades g JOIN subjects s ON s.id=g.subject_id
               WHERE g.user_id=?
               ORDER BY s.name""",
            (user_id,),
        )
        return list(cur.fetchall())
