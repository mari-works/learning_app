import sqlite3
from datetime import datetime
from pathlib import Path

from learning_app.config import PROJECT_ROOT
from learning_app.models import (
    connect_db,
    create_course,
    get_material_title,
    import_questions_from_csv_if_empty,
    init_db,
    list_courses,
    load_keywords_from_csv,
    update_course_title,
    update_exam_settings,
    update_material_data,
)


PRIMARY_DATABASE = PROJECT_ROOT / "instance" / "learning.db"
COURSES_DIRECTORY = PROJECT_ROOT / "instance" / "courses"


def activity_user_ids(database_path):
    with connect_db(database_path) as db:
        rows = db.execute(
            """
            SELECT DISTINCT user_id FROM keyword_progress WHERE user_id IS NOT NULL
            UNION
            SELECT DISTINCT user_id FROM history WHERE user_id IS NOT NULL
            """
        ).fetchall()
    return {row[0] for row in rows}


def assign_existing_course_owners():
    with connect_db(PRIMARY_DATABASE) as registry:
        courses = registry.execute(
            "SELECT id, database_path FROM courses WHERE id != 'default' AND owner_user_id IS NULL"
        ).fetchall()
        for course in courses:
            owners = activity_user_ids(course["database_path"])
            if len(owners) == 1:
                registry.execute(
                    "UPDATE courses SET owner_user_id = ?, updated_at = ? WHERE id = ?",
                    (owners.pop(), datetime.now().isoformat(timespec="seconds"), course["id"]),
                )
        registry.commit()


def preserve_custom_default_and_restore_starter():
    if get_material_title(PRIMARY_DATABASE) == "G検定学習":
        return
    owners = activity_user_ids(PRIMARY_DATABASE)
    if len(owners) == 1:
        owner_id = owners.pop()
        course_id = f"migrated-default-{owner_id}"
        if not any(course["id"] == course_id for course in list_courses(PRIMARY_DATABASE)):
            destination = COURSES_DIRECTORY / f"{course_id}.db"
            with sqlite3.connect(PRIMARY_DATABASE) as source, sqlite3.connect(destination) as target:
                source.backup(target)
            create_course(
                PRIMARY_DATABASE,
                course_id,
                get_material_title(destination),
                destination,
                owner_id,
            )

    with connect_db(PRIMARY_DATABASE) as db:
        for table in ("flashcard_resume", "keyword_status_history", "keyword_progress", "history"):
            db.execute(f"DELETE FROM {table}")
        db.execute("DELETE FROM keywords")
        db.execute("DELETE FROM questions")
        db.commit()
    load_keywords_from_csv(PRIMARY_DATABASE, PROJECT_ROOT / "data" / "default_terms.csv")
    import_questions_from_csv_if_empty(PRIMARY_DATABASE, PROJECT_ROOT / "data" / "default_questions.csv")
    update_material_data(PRIMARY_DATABASE, "G検定学習")
    update_exam_settings(PRIMARY_DATABASE, True, 145, 100)
    update_course_title(PRIMARY_DATABASE, "default", "G検定学習")


def main():
    COURSES_DIRECTORY.mkdir(parents=True, exist_ok=True)
    init_db(PRIMARY_DATABASE)
    assign_existing_course_owners()
    preserve_custom_default_and_restore_starter()
    assign_existing_course_owners()


if __name__ == "__main__":
    main()
