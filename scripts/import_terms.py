from learning_app.config import Config, PROJECT_ROOT
from learning_app.models import init_db, load_keywords_from_csv


def main():
    db_path = Config.DATABASE
    csv_path = PROJECT_ROOT / "data" / "default_terms.csv"

    print("Initializing database if needed...")
    init_db(db_path)

    print(f"Loading keywords from CSV: {csv_path}")
    load_keywords_from_csv(db_path, csv_path)
    print("CSV import complete.")


if __name__ == "__main__":
    try:
        main()
    except FileNotFoundError as exc:
        print(exc)
        raise SystemExit(1)
