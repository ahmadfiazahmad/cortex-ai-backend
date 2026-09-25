from pathlib import Path

from config.database import connect_to_database

MIGRATION_FILE = Path(__file__).resolve().parents[1] / "migrations" / "001_documents.sql"


def run_migration() -> None:
    sql = MIGRATION_FILE.read_text(encoding="utf-8")
    with connect_to_database() as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql)
    print("Week 3-4 migration applied successfully.")


if __name__ == "__main__":
    run_migration()
