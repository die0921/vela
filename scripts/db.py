# scripts/db.py
import sqlite3
import json
from pathlib import Path


class Database:
    def __init__(self, db_path: str = None):
        if db_path is None:
            base = Path(__file__).parent.parent / "data"
            base.mkdir(exist_ok=True)
            db_path = str(base / "persona.db")
        self.db_path = db_path
        self._init_schema()

    def _conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        with self._conn() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS personas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    base_emotion INTEGER DEFAULT 70,
                    base_sadness INTEGER DEFAULT 80,
                    base_anger INTEGER DEFAULT 80,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS questionnaire_answers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    persona_id INTEGER NOT NULL,
                    dimension TEXT NOT NULL,
                    question TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS values_profile (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    persona_id INTEGER NOT NULL UNIQUE,
                    core_values TEXT DEFAULT '[]',
                    red_lines TEXT DEFAULT '[]',
                    scenarios TEXT DEFAULT '{}'
                );
                CREATE TABLE IF NOT EXISTS emotion_state (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    persona_id INTEGER NOT NULL UNIQUE,
                    instant_emotion INTEGER DEFAULT 70,
                    sadness INTEGER DEFAULT 80,
                    anger INTEGER DEFAULT 80,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    persona_id INTEGER NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    emotion_snapshot TEXT DEFAULT '{}',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS interaction_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    persona_id INTEGER NOT NULL,
                    action_type TEXT NOT NULL,
                    emotion_delta TEXT DEFAULT '{}',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS maintenance_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    persona_id INTEGER NOT NULL,
                    task_type TEXT NOT NULL,
                    result TEXT DEFAULT '{}',
                    ran_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
            """)

    def create_persona(self, name: str, base_emotion: int, base_sadness: int, base_anger: int) -> int:
        with self._conn() as conn:
            cur = conn.execute(
                "INSERT INTO personas (name, base_emotion, base_sadness, base_anger) VALUES (?,?,?,?)",
                (name, base_emotion, base_sadness, base_anger)
            )
            return cur.lastrowid

    def get_persona(self, persona_id: int) -> dict | None:
        with self._conn() as conn:
            row = conn.execute("SELECT * FROM personas WHERE id=?", (persona_id,)).fetchone()
            return dict(row) if row else None

    def list_personas(self) -> list:
        with self._conn() as conn:
            rows = conn.execute("SELECT * FROM personas ORDER BY created_at DESC").fetchall()
            return [dict(r) for r in rows]

    def save_answer(self, persona_id: int, dimension: str, question: str, answer: str) -> None:
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO questionnaire_answers (persona_id, dimension, question, answer) VALUES (?,?,?,?)",
                (persona_id, dimension, question, answer)
            )

    def get_answers(self, persona_id: int, dimension: str = None) -> list:
        with self._conn() as conn:
            if dimension:
                rows = conn.execute(
                    "SELECT * FROM questionnaire_answers WHERE persona_id=? AND dimension=?",
                    (persona_id, dimension)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM questionnaire_answers WHERE persona_id=?",
                    (persona_id,)
                ).fetchall()
            return [dict(r) for r in rows]

    def save_values_profile(self, persona_id: int, core_values: list, red_lines: list, scenarios: dict) -> None:
        with self._conn() as conn:
            conn.execute(
                """INSERT INTO values_profile (persona_id, core_values, red_lines, scenarios)
                   VALUES (?,?,?,?)
                   ON CONFLICT(persona_id) DO UPDATE SET
                   core_values=excluded.core_values,
                   red_lines=excluded.red_lines,
                   scenarios=excluded.scenarios""",
                (persona_id, json.dumps(core_values, ensure_ascii=False),
                 json.dumps(red_lines, ensure_ascii=False),
                 json.dumps(scenarios, ensure_ascii=False))
            )

    def get_values_profile(self, persona_id: int) -> dict:
        with self._conn() as conn:
            row = conn.execute("SELECT * FROM values_profile WHERE persona_id=?", (persona_id,)).fetchone()
            if not row:
                return {"core_values": [], "red_lines": [], "scenarios": {}}
            return {
                "core_values": json.loads(row["core_values"]),
                "red_lines": json.loads(row["red_lines"]),
                "scenarios": json.loads(row["scenarios"])
            }

    def init_emotion_state(self, persona_id: int) -> None:
        persona = self.get_persona(persona_id)
        if persona is None:
            raise ValueError(f"Persona {persona_id} not found")
        with self._conn() as conn:
            conn.execute(
                """INSERT INTO emotion_state (persona_id, instant_emotion, sadness, anger)
                   VALUES (?,?,?,?)
                   ON CONFLICT(persona_id) DO NOTHING""",
                (persona_id, persona["base_emotion"], persona["base_sadness"], persona["base_anger"])
            )

    def get_emotion_state(self, persona_id: int) -> dict | None:
        with self._conn() as conn:
            row = conn.execute("SELECT * FROM emotion_state WHERE persona_id=?", (persona_id,)).fetchone()
            return dict(row) if row else None

    def update_emotion_state(self, persona_id: int, instant_emotion: int, sadness: int, anger: int) -> None:
        with self._conn() as conn:
            conn.execute(
                """UPDATE emotion_state
                   SET instant_emotion=?, sadness=?, anger=?, updated_at=CURRENT_TIMESTAMP
                   WHERE persona_id=?""",
                (int(max(0, min(100, instant_emotion))),
                 int(max(0, min(100, sadness))),
                 int(max(0, min(100, anger))),
                 persona_id)
            )

    def save_conversation(self, persona_id: int, role: str, content: str, emotion_snapshot: dict) -> None:
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO conversations (persona_id, role, content, emotion_snapshot) VALUES (?,?,?,?)",
                (persona_id, role, content, json.dumps(emotion_snapshot))
            )

    def get_recent_conversations(self, persona_id: int, limit: int = 10) -> list:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM conversations WHERE persona_id=? ORDER BY created_at ASC LIMIT ?",
                (persona_id, limit)
            ).fetchall()
            return [dict(r) for r in rows]

    def log_interaction(self, persona_id: int, action_type: str, emotion_delta: dict) -> None:
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO interaction_log (persona_id, action_type, emotion_delta) VALUES (?,?,?)",
                (persona_id, action_type, json.dumps(emotion_delta))
            )

    def log_maintenance(self, persona_id: int, task_type: str, result: dict) -> None:
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO maintenance_log (persona_id, task_type, result) VALUES (?,?,?)",
                (persona_id, task_type, json.dumps(result, ensure_ascii=False))
            )

    def get_last_maintenance(self, persona_id: int, task_type: str) -> dict:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM maintenance_log WHERE persona_id=? AND task_type=? ORDER BY ran_at DESC LIMIT 1",
                (persona_id, task_type)
            ).fetchone()
            return dict(row) if row else None
