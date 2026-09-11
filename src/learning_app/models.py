import csv
import sqlite3
from pathlib import Path
from datetime import datetime

STATUS_UNTRAINED = "未学習"
STATUS_IN_PROGRESS = "勉強中"
STATUS_MASTERED = "理解済み"

# New statuses requested by the user (keep old ones for backward compatibility)
STATUS_UNDERSTOOD = "理解済み"
STATUS_AMBIGUOUS = "あいまい"
STATUS_NOT_UNDERSTOOD = "未理解"

# Accept both legacy and new labels
LEARNING_STATUSES = [
    STATUS_UNTRAINED,
    STATUS_IN_PROGRESS,
    STATUS_MASTERED,
    STATUS_UNDERSTOOD,
    STATUS_AMBIGUOUS,
    STATUS_NOT_UNDERSTOOD,
]

KEYWORD_SELECT_COLUMNS = """
    keywords.id AS id,
    keywords.big_category AS big_category,
    keywords.category AS category,
    keywords.item_no AS item_no,
    keywords.item_name AS item_name,
    keywords.keyword AS keyword,
    keywords.meaning AS meaning,
    keywords.learning_order AS learning_order
"""


def connect_db(db_path):
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path):
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with connect_db(db_path) as db:
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS keywords (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                big_category TEXT NOT NULL,
                category TEXT NOT NULL,
                item_no TEXT,
                item_name TEXT,
                keyword TEXT NOT NULL,
                meaning TEXT NOT NULL,
                learning_order INTEGER DEFAULT NULL,
                learning_status TEXT NOT NULL DEFAULT '未学習',
                last_studied_at TEXT DEFAULT NULL
            );

            CREATE UNIQUE INDEX IF NOT EXISTS idx_keywords_unique ON keywords(big_category, category, item_no, keyword);

            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_type TEXT NOT NULL,
                item_id INTEGER,
                result TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS keyword_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                keyword_id INTEGER NOT NULL,
                learning_status TEXT NOT NULL DEFAULT '未学習',
                last_studied_at TEXT DEFAULT NULL,
                UNIQUE(user_id, keyword_id)
            );

            CREATE TABLE IF NOT EXISTS keyword_status_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                term_id INTEGER NOT NULL,
                selected_status TEXT NOT NULL,
                reviewed_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES user(id),
                FOREIGN KEY(term_id) REFERENCES keywords(id)
            );

            CREATE INDEX IF NOT EXISTS idx_keyword_status_history_user_term
                ON keyword_status_history(user_id, term_id, reviewed_at);

            CREATE TABLE IF NOT EXISTS flashcard_resume (
                user_id INTEGER PRIMARY KEY,
                current_index INTEGER NOT NULL DEFAULT 0,
                total INTEGER NOT NULL DEFAULT 0,
                direction TEXT NOT NULL DEFAULT 'term_to_meaning',
                card_ids TEXT NOT NULL,
                learning_mode TEXT DEFAULT NULL,
                learning_category TEXT DEFAULT NULL,
                range_label TEXT DEFAULT NULL,
                saved_at TEXT NOT NULL,
                started_at TEXT DEFAULT NULL,
                FOREIGN KEY(user_id) REFERENCES user(id)
            );

            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY,
                category TEXT NOT NULL,
                question TEXT NOT NULL,
                correct_answer TEXT NOT NULL,
                incorrect_answer_1 TEXT,
                incorrect_answer_2 TEXT,
                incorrect_answer_3 TEXT,
                explanation TEXT NOT NULL DEFAULT '',
                learning_order INTEGER DEFAULT NULL
            );

            CREATE TABLE IF NOT EXISTS app_settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS courses (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                database_path TEXT NOT NULL UNIQUE,
                owner_user_id INTEGER DEFAULT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """
        )
        db.execute(
            "INSERT OR IGNORE INTO app_settings (key, value) VALUES ('material_title', 'G検定学習')"
        )
        
        # Add last_studied_at column if it doesn't exist (for backward compatibility)
        try:
            db.execute("ALTER TABLE keywords ADD COLUMN last_studied_at TEXT DEFAULT NULL;")
            db.commit()
        except sqlite3.OperationalError:
            pass  # column already exists

        for statement in [
            "ALTER TABLE history ADD COLUMN category TEXT DEFAULT NULL;",
            "ALTER TABLE history ADD COLUMN amount INTEGER NOT NULL DEFAULT 1;",
            "ALTER TABLE history ADD COLUMN correct INTEGER DEFAULT NULL;",
            "ALTER TABLE history ADD COLUMN duration_seconds INTEGER NOT NULL DEFAULT 0;",
            "ALTER TABLE history ADD COLUMN user_id INTEGER DEFAULT NULL;",
            "ALTER TABLE history ADD COLUMN practice_mode TEXT DEFAULT NULL;",
            "ALTER TABLE history ADD COLUMN learning_type TEXT DEFAULT NULL;",
            "ALTER TABLE history ADD COLUMN learning_mode TEXT DEFAULT NULL;",
            "ALTER TABLE history ADD COLUMN learning_category TEXT DEFAULT NULL;",
            "ALTER TABLE history ADD COLUMN started_at TEXT DEFAULT NULL;",
            "ALTER TABLE history ADD COLUMN ended_at TEXT DEFAULT NULL;",
            "ALTER TABLE keyword_status_history ADD COLUMN user_id INTEGER DEFAULT NULL;",
            "ALTER TABLE keyword_progress ADD COLUMN review_later INTEGER NOT NULL DEFAULT 0;",
            "ALTER TABLE keyword_progress ADD COLUMN note TEXT DEFAULT '';",
            "ALTER TABLE keywords ADD COLUMN learning_order INTEGER DEFAULT NULL;",
            "ALTER TABLE questions ADD COLUMN learning_order INTEGER DEFAULT NULL;",
            "ALTER TABLE courses ADD COLUMN owner_user_id INTEGER DEFAULT NULL;",
        ]:
            try:
                db.execute(statement)
                db.commit()
            except sqlite3.OperationalError:
                pass
        db.execute(
            """
            INSERT INTO keyword_status_history (user_id, term_id, selected_status, reviewed_at)
            SELECT h.user_id, h.item_id, h.result, h.created_at
            FROM history h
            WHERE h.session_type = 'term'
              AND h.item_id IS NOT NULL
              AND h.result IN ('理解済み', 'あいまい', '未理解')
              AND NOT EXISTS (
                SELECT 1
                FROM keyword_status_history ksh
                WHERE COALESCE(ksh.user_id, -1) = COALESCE(h.user_id, -1)
                  AND ksh.term_id = h.item_id
                  AND ksh.selected_status = h.result
                  AND ksh.reviewed_at = h.created_at
              )
            """
        )
        db.execute(
            """
            INSERT INTO keyword_status_history (user_id, term_id, selected_status, reviewed_at)
            SELECT kp.user_id, kp.keyword_id, kp.learning_status, kp.last_studied_at
            FROM keyword_progress kp
            WHERE kp.last_studied_at IS NOT NULL
              AND kp.learning_status IN ('理解済み', 'あいまい', '未理解')
              AND NOT EXISTS (
                SELECT 1
                FROM keyword_status_history ksh
                WHERE COALESCE(ksh.user_id, -1) = COALESCE(kp.user_id, -1)
                  AND ksh.term_id = kp.keyword_id
                  AND ksh.selected_status = kp.learning_status
                  AND ksh.reviewed_at = kp.last_studied_at
              )
            """
        )
        db.commit()


def query_db(db_path, query, args=(), one=False):
    with connect_db(db_path) as db:
        cur = db.execute(query, args)
        rv = cur.fetchall()
        return (rv[0] if rv else None) if one else rv


def get_material_title(db_path):
    row = query_db(db_path, "SELECT value FROM app_settings WHERE key = 'material_title'", one=True)
    return row["value"] if row else "G検定学習"


def get_material_description(db_path):
    row = query_db(
        db_path,
        "SELECT value FROM app_settings WHERE key = 'material_description'",
        one=True,
    )
    return row["value"] if row else ""


def update_material_description(db_path, description):
    with connect_db(db_path) as db:
        db.execute(
            """
            INSERT INTO app_settings (key, value) VALUES ('material_description', ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """,
            (description,),
        )
        db.commit()


def ensure_default_course(registry_db_path):
    now = datetime.now().isoformat(timespec="seconds")
    title = get_material_title(registry_db_path)
    with connect_db(registry_db_path) as db:
        db.execute(
            """
            INSERT OR IGNORE INTO courses (id, title, database_path, created_at, updated_at)
            VALUES ('default', ?, ?, ?, ?)
            """,
            (title, str(Path(registry_db_path).resolve()), now, now),
        )
        db.commit()


def list_courses(registry_db_path, owner_user_id=None):
    if owner_user_id is None:
        rows = query_db(registry_db_path, "SELECT * FROM courses ORDER BY created_at, title")
    else:
        rows = query_db(
            registry_db_path,
            """
            SELECT * FROM courses
            WHERE owner_user_id = ?
            ORDER BY created_at, title
            """,
            (owner_user_id,),
        )
    return [dict(row) for row in rows]


def get_course(registry_db_path, course_id):
    row = query_db(
        registry_db_path,
        "SELECT * FROM courses WHERE id = ?",
        (course_id,),
        one=True,
    )
    return dict(row) if row else None


def create_course(registry_db_path, course_id, title, database_path, owner_user_id=None):
    now = datetime.now().isoformat(timespec="seconds")
    with connect_db(registry_db_path) as db:
        db.execute(
            """
            INSERT INTO courses (id, title, database_path, owner_user_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (course_id, title, str(Path(database_path).resolve()), owner_user_id, now, now),
        )
        db.commit()


def update_course_title(registry_db_path, course_id, title):
    with connect_db(registry_db_path) as db:
        db.execute(
            "UPDATE courses SET title = ?, updated_at = ? WHERE id = ?",
            (title, datetime.now().isoformat(timespec="seconds"), course_id),
        )
        db.commit()


def delete_course(registry_db_path, course_id):
    with connect_db(registry_db_path) as db:
        db.execute("DELETE FROM courses WHERE id = ?", (course_id,))
        db.commit()


def get_material_counts(db_path):
    with connect_db(db_path) as db:
        return {
            "keywords": db.execute("SELECT COUNT(*) FROM keywords").fetchone()[0],
            "questions": db.execute("SELECT COUNT(*) FROM questions").fetchone()[0],
        }


def get_exam_settings(db_path):
    rows = query_db(
        db_path,
        "SELECT key, value FROM app_settings WHERE key IN ('exam_enabled', 'exam_question_count', 'exam_time_minutes')",
    )
    values = {row["key"]: row["value"] for row in rows}
    question_count = int(values.get("exam_question_count") or 0)
    time_minutes = int(values.get("exam_time_minutes") or 0)
    available_questions = query_db(
        db_path, "SELECT COUNT(*) AS count FROM questions", one=True
    )["count"]
    return {
        "enabled": (
            values.get("exam_enabled") == "1"
            and 1 <= question_count <= available_questions
            and time_minutes > 0
        ),
        "questions": question_count,
        "minutes": time_minutes,
    }


def update_exam_settings(db_path, enabled, question_count=None, time_minutes=None):
    settings = {
        "exam_enabled": "1" if enabled else "0",
        "exam_question_count": str(int(question_count or 0)),
        "exam_time_minutes": str(int(time_minutes or 0)),
    }
    with connect_db(db_path) as db:
        db.executemany(
            """
            INSERT INTO app_settings (key, value) VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """,
            settings.items(),
        )
        db.commit()


def initialize_exam_settings(db_path, enabled, question_count, time_minutes):
    row = query_db(
        db_path,
        "SELECT value FROM app_settings WHERE key = 'exam_enabled'",
        one=True,
    )
    if row is None:
        update_exam_settings(db_path, enabled, question_count, time_minutes)


def import_questions_from_csv_if_empty(db_path, csv_path):
    csv_path = Path(csv_path)
    if not csv_path.exists():
        return 0
    with connect_db(db_path) as db:
        if db.execute("SELECT COUNT(*) FROM questions").fetchone()[0]:
            return 0
        with csv_path.open(newline="", encoding="utf-8-sig") as handle:
            rows = list(csv.DictReader(handle))
        values = []
        for index, row in enumerate(rows, start=1):
            question = (row.get("問題") or "").strip()
            correct = (row.get("正答") or "").strip()
            if not question or not correct:
                continue
            values.append((
                int(row.get("ID") or index),
                (row.get("カテゴリ") or "未分類").strip(),
                question,
                correct,
                (row.get("誤答1") or "").strip(),
                (row.get("誤答2") or "").strip(),
                (row.get("誤答3") or "").strip(),
                (row.get("解説") or "").strip(),
                int(row["学習順"]) if (row.get("学習順") or "").strip().isdigit() else None,
            ))
        db.executemany(
            """
            INSERT INTO questions
                (id, category, question, correct_answer, incorrect_answer_1,
                 incorrect_answer_2, incorrect_answer_3, explanation, learning_order)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            values,
        )
        db.commit()
        return len(values)


def update_material_data(db_path, title, keyword_rows=None, question_rows=None):
    """Update the material metadata and only the supplied datasets."""
    with connect_db(db_path) as db:
        db.execute("BEGIN")
        if keyword_rows is not None:
            for table in ("flashcard_resume", "keyword_status_history", "keyword_progress"):
                db.execute(f"DELETE FROM {table}")
            db.execute("DELETE FROM history WHERE session_type = 'term'")
            db.execute("DELETE FROM keywords")
            db.executemany(
                """
                INSERT INTO keywords
                    (big_category, category, item_no, item_name, keyword, meaning, learning_order, learning_status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (row["big_category"], row["category"], row["item_no"], row["item_name"],
                     row["keyword"], row["meaning"], row.get("learning_order"), STATUS_UNTRAINED)
                    for row in keyword_rows
                ],
            )
        if question_rows is not None:
            db.execute("DELETE FROM history WHERE session_type = 'practice'")
            db.execute("DELETE FROM questions")
            db.executemany(
                """
                INSERT INTO questions
                    (id, category, question, correct_answer, incorrect_answer_1,
                     incorrect_answer_2, incorrect_answer_3, explanation, learning_order)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (row["id"], row["category"], row["question"], row["correct_answer"],
                     *row["incorrect_answers"], row["explanation"], row.get("learning_order"))
                    for row in question_rows
                ],
            )
        db.execute(
            """
            INSERT INTO app_settings (key, value) VALUES ('material_title', ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """,
            (title,),
        )
        db.commit()


def replace_material_data(db_path, title, keyword_rows, question_rows):
    """Backward-compatible full replacement helper."""
    update_material_data(db_path, title, keyword_rows, question_rows)


def get_dashboard(db_path, user_id=None):
    user_join = ""
    user_params = []
    status_expr = "keywords.learning_status"
    if user_id is not None:
        user_join = "LEFT JOIN keyword_progress kp ON kp.keyword_id = keywords.id AND kp.user_id = ?"
        user_params = [user_id]
        status_expr = "COALESCE(kp.learning_status, ?)"
        user_params.append(STATUS_UNTRAINED)

    total = query_db(db_path, "SELECT COUNT(*) AS count FROM keywords", one=True)["count"]
    untrained = query_db(
        db_path,
        f"SELECT COUNT(*) AS count FROM keywords {user_join} WHERE {status_expr} = ?",
        (*user_params, STATUS_UNTRAINED),
        one=True,
    )["count"]
    in_progress = query_db(
        db_path,
        f"SELECT COUNT(*) AS count FROM keywords {user_join} WHERE {status_expr} = ?",
        (*user_params, STATUS_IN_PROGRESS),
        one=True,
    )["count"]
    mastered = query_db(
        db_path,
        f"SELECT COUNT(*) AS count FROM keywords {user_join} WHERE {status_expr} = ?",
        (*user_params, STATUS_MASTERED),
        one=True,
    )["count"]
    if user_id is not None:
        recent_keywords = query_db(
            db_path,
            """
            SELECT keywords.*,
                   COALESCE(kp.learning_status, ?) AS learning_status,
                   kp.last_studied_at AS last_studied_at
            FROM keywords
            LEFT JOIN keyword_progress kp ON kp.keyword_id = keywords.id AND kp.user_id = ?
            WHERE COALESCE(kp.learning_status, ?) != ?
            ORDER BY kp.last_studied_at DESC, keywords.id DESC
            LIMIT 5
            """,
            (STATUS_UNTRAINED, user_id, STATUS_UNTRAINED, STATUS_UNTRAINED),
        )
        recommended = query_db(
            db_path,
            """
            SELECT keywords.*,
                   COALESCE(kp.learning_status, ?) AS learning_status,
                   kp.last_studied_at AS last_studied_at
            FROM keywords
            LEFT JOIN keyword_progress kp ON kp.keyword_id = keywords.id AND kp.user_id = ?
            WHERE COALESCE(kp.learning_status, ?) = ?
            ORDER BY big_category, category, keyword
            LIMIT 5
            """,
            (STATUS_UNTRAINED, user_id, STATUS_UNTRAINED, STATUS_UNTRAINED),
        )
    else:
        recent_keywords = query_db(
            db_path,
            "SELECT * FROM keywords WHERE learning_status != ? ORDER BY id DESC LIMIT 5",
            (STATUS_UNTRAINED,),
        )
        recommended = query_db(
            db_path,
            "SELECT * FROM keywords WHERE learning_status = ? ORDER BY big_category, category, keyword LIMIT 5",
            (STATUS_UNTRAINED,),
        )

    return {
        "total": total,
        "untrained": untrained,
        "in_progress": in_progress,
        "mastered": mastered,
        "progress_rate": int(((mastered + in_progress) / total) * 100) if total else 0,
        "recent_keywords": [dict(row) for row in recent_keywords],
        "recommended_keywords": [dict(row) for row in recommended],
    }


def get_big_categories(db_path):
    rows = query_db(
        db_path,
        "SELECT big_category, COUNT(*) AS count FROM keywords GROUP BY big_category ORDER BY big_category",
    )
    return [dict(row) for row in rows]


def get_categories(db_path, big_category=None):
    query = "SELECT category, COUNT(*) AS count FROM keywords"
    params = []
    if big_category:
        query += " WHERE big_category = ?"
        params.append(big_category)
    query += " GROUP BY category ORDER BY category"
    rows = query_db(db_path, query, params)
    return [dict(row) for row in rows]


def get_keywords(db_path, big_category=None, category=None, status=None, search=None, user_id=None, review_later=False):
    params = []
    if user_id is not None:
        query = """
            SELECT
                   """ + KEYWORD_SELECT_COLUMNS + """,
                   COALESCE(kp.learning_status, ?) AS learning_status,
                   kp.last_studied_at AS last_studied_at,
                   COALESCE(kp.review_later, 0) AS review_later,
                   COALESCE(kp.note, '') AS note
            FROM keywords
            LEFT JOIN keyword_progress kp ON kp.keyword_id = keywords.id AND kp.user_id = ?
        """
        params.extend([STATUS_UNTRAINED, user_id])
        status_expr = "COALESCE(kp.learning_status, ?)"
    else:
        query = "SELECT * FROM keywords"
        status_expr = "learning_status"
    conditions = []

    if big_category:
        conditions.append("keywords.big_category = ?")
        params.append(big_category)
    if category:
        conditions.append("keywords.category = ?")
        params.append(category)
    if status:
        if user_id is not None:
            conditions.append(f"{status_expr} = ?")
            params.append(STATUS_UNTRAINED)
        else:
            conditions.append(f"{status_expr} = ?")
        params.append(status)
    if search:
        conditions.append("(keywords.keyword LIKE ? OR keywords.meaning LIKE ? OR keywords.item_name LIKE ?)")
        params.extend([f"%{search}%"] * 3)
    if review_later and user_id is not None:
        conditions.append("COALESCE(kp.review_later, 0) = 1")

    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY keywords.big_category, keywords.category, keywords.item_no, keywords.keyword"

    rows = query_db(db_path, query, params)
    return [dict(row) for row in rows]


def get_keyword(db_path, keyword_id, user_id=None):
    if user_id is not None:
        row = query_db(
            db_path,
            """
            SELECT
                   """ + KEYWORD_SELECT_COLUMNS + """,
                   COALESCE(kp.learning_status, ?) AS learning_status,
                   kp.last_studied_at AS last_studied_at,
                   COALESCE(kp.review_later, 0) AS review_later,
                   COALESCE(kp.note, '') AS note
            FROM keywords
            LEFT JOIN keyword_progress kp ON kp.keyword_id = keywords.id AND kp.user_id = ?
            WHERE keywords.id = ?
            """,
            (STATUS_UNTRAINED, user_id, keyword_id),
            one=True,
        )
    else:
        row = query_db(db_path, "SELECT * FROM keywords WHERE id = ?", (keyword_id,), one=True)
    return dict(row) if row else None


def set_review_later(db_path, keyword_id, review_later, user_id=None):
    if user_id is None:
        return False
    now = datetime.now().isoformat()
    with connect_db(db_path) as db:
        exists = db.execute("SELECT 1 FROM keywords WHERE id = ?", (keyword_id,)).fetchone()
        if not exists:
            return False
        db.execute(
            """
            INSERT INTO keyword_progress (user_id, keyword_id, learning_status, last_studied_at, review_later)
            VALUES (?, ?, ?, NULL, ?)
            ON CONFLICT(user_id, keyword_id)
            DO UPDATE SET review_later = excluded.review_later
            """,
            (user_id, keyword_id, STATUS_UNTRAINED, 1 if review_later else 0),
        )
        db.commit()
    return True


def set_keyword_note(db_path, keyword_id, note, user_id=None):
    if user_id is None:
        return False
    note = (note or "")[:1000]
    with connect_db(db_path) as db:
        exists = db.execute("SELECT 1 FROM keywords WHERE id = ?", (keyword_id,)).fetchone()
        if not exists:
            return False
        db.execute(
            """
            INSERT INTO keyword_progress (user_id, keyword_id, learning_status, last_studied_at, note)
            VALUES (?, ?, ?, NULL, ?)
            ON CONFLICT(user_id, keyword_id)
            DO UPDATE SET note = excluded.note
            """,
            (user_id, keyword_id, STATUS_UNTRAINED, note),
        )
        db.commit()
    return True


def set_learning_status(db_path, keyword_id, status, duration_seconds=0, user_id=None, learning_mode=None, learning_category=None):
    if status not in LEARNING_STATUSES:
        return False

    now = datetime.now().isoformat()
    with connect_db(db_path) as db:
        keyword = db.execute("SELECT category FROM keywords WHERE id = ?", (keyword_id,)).fetchone()
        category = keyword["category"] if keyword else None
        if user_id is None:
            db.execute(
                "UPDATE keywords SET learning_status = ?, last_studied_at = ? WHERE id = ?",
                (status, now, keyword_id),
            )
        else:
            db.execute(
                """
                INSERT INTO keyword_progress (user_id, keyword_id, learning_status, last_studied_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(user_id, keyword_id)
                DO UPDATE SET learning_status = excluded.learning_status,
                              last_studied_at = excluded.last_studied_at
                """,
                (user_id, keyword_id, status, now),
            )
        db.execute(
            """
            INSERT INTO history (
                session_type, item_id, result, created_at, category, amount, duration_seconds, user_id,
                learning_type, learning_mode, learning_category, started_at, ended_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "term",
                keyword_id,
                status,
                now,
                category,
                1,
                max(0, int(duration_seconds or 0)),
                user_id,
                "vocabulary",
                learning_mode,
                learning_category,
                now,
                now,
            ),
        )
        db.execute(
            "INSERT INTO keyword_status_history (user_id, term_id, selected_status, reviewed_at) VALUES (?, ?, ?, ?)",
            (user_id, keyword_id, status, now),
        )
        db.commit()

    return True


def load_keywords_from_csv(db_path, csv_path):
    csv_path = Path(csv_path)
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    init_db(db_path)

    with csv_path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        with connect_db(db_path) as db:
            for row in reader:
                big_category = row.get("大分類", "").strip() or "未設定"
                category = row.get("カテゴリ", "").strip() or "未設定"
                item_no = row.get("項目No", "").strip()
                item_name = row.get("項目名", "").strip()
                keyword = row.get("キーワード", "").strip() or item_name
                meaning = row.get("意味", "").replace("\n", " ").replace("\r", " ").strip()
                learning_order_text = (row.get("学習順") or "").strip()
                learning_order = int(learning_order_text) if learning_order_text.isdigit() else None

                if not keyword or not meaning:
                    continue

                db.execute(
                    "INSERT OR IGNORE INTO keywords (big_category, category, item_no, item_name, keyword, meaning, learning_order, learning_status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        big_category,
                        category,
                        item_no,
                        item_name,
                        keyword,
                        meaning,
                        learning_order,
                        STATUS_UNTRAINED,
                    ),
                )
            db.commit()


def _status_count_query(user_id):
    if user_id is None:
        return "", "learning_status", []
    return (
        "LEFT JOIN keyword_progress kp ON kp.keyword_id = keywords.id AND kp.user_id = ?",
        "COALESCE(kp.learning_status, ?)",
        [user_id, STATUS_UNTRAINED],
    )


def get_big_category_stats(db_path, big_category, user_id=None):
    """Get stats for a specific big category"""
    join, status_expr, _user_params = _status_count_query(user_id)
    total = query_db(
        db_path,
        "SELECT COUNT(*) AS count FROM keywords WHERE big_category = ?",
        (big_category,),
        one=True,
    )["count"]
    def status_params(status):
        if user_id is None:
            return (big_category, status)
        return (user_id, big_category, STATUS_UNTRAINED, status)

    understood = query_db(
        db_path,
        f"SELECT COUNT(*) AS count FROM keywords {join} WHERE big_category = ? AND {status_expr} = ?",
        status_params(STATUS_UNDERSTOOD),
        one=True,
    )["count"]
    ambiguous = query_db(
        db_path,
        f"SELECT COUNT(*) AS count FROM keywords {join} WHERE big_category = ? AND {status_expr} = ?",
        status_params(STATUS_AMBIGUOUS),
        one=True,
    )["count"]
    not_understood = query_db(
        db_path,
        f"SELECT COUNT(*) AS count FROM keywords {join} WHERE big_category = ? AND {status_expr} = ?",
        status_params(STATUS_NOT_UNDERSTOOD),
        one=True,
    )["count"]
    
    progress_rate = int(((understood + ambiguous) / total) * 100) if total > 0 else 0
    return {
        "total": total,
        "understood": understood,
        "ambiguous": ambiguous,
        "not_understood": not_understood,
        "progress_rate": progress_rate,
    }


def get_category_stats(db_path, big_category, category, user_id=None):
    """Get stats for a specific category"""
    join, status_expr, _user_params = _status_count_query(user_id)
    total = query_db(
        db_path,
        "SELECT COUNT(*) AS count FROM keywords WHERE big_category = ? AND category = ?",
        (big_category, category),
        one=True,
    )["count"]
    def status_params(status):
        if user_id is None:
            return (big_category, category, status)
        return (user_id, big_category, category, STATUS_UNTRAINED, status)

    understood = query_db(
        db_path,
        f"SELECT COUNT(*) AS count FROM keywords {join} WHERE big_category = ? AND category = ? AND {status_expr} = ?",
        status_params(STATUS_UNDERSTOOD),
        one=True,
    )["count"]
    ambiguous = query_db(
        db_path,
        f"SELECT COUNT(*) AS count FROM keywords {join} WHERE big_category = ? AND category = ? AND {status_expr} = ?",
        status_params(STATUS_AMBIGUOUS),
        one=True,
    )["count"]
    not_understood = query_db(
        db_path,
        f"SELECT COUNT(*) AS count FROM keywords {join} WHERE big_category = ? AND category = ? AND {status_expr} = ?",
        status_params(STATUS_NOT_UNDERSTOOD),
        one=True,
    )["count"]
    
    progress_rate = int(((understood + ambiguous) / total) * 100) if total > 0 else 0
    return {
        "total": total,
        "understood": understood,
        "ambiguous": ambiguous,
        "not_understood": not_understood,
        "progress_rate": progress_rate,
    }

def get_category_overview(db_path, big_category):
    categories = get_categories(db_path, big_category=big_category)
    overview = []
    for category in categories:
        stats = get_category_stats(db_path, big_category, category["category"])
        overview.append({**category, **stats})
    return overview
