"""
Create SQLite databases from CSV files.

Usage:
    python scripts/create_sql_db.py

Run from the project root directory.
Input:  data/csv_db/*.csv
Output: data/databases/movie.db
"""
import csv
import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CSV_FOLDER = PROJECT_ROOT / "data" / "csv_db"
DB_FILE = PROJECT_ROOT / "data" / "databases" / "movie.db"


def clean_column_name(name: str) -> str:
    return name.strip().replace(" ", "_").replace("-", "_").lower()


def clean_value(value: str):
    return None if value == "" else value


def infer_sql_type(value: str) -> str:
    if not value:
        return "TEXT"
    try:
        int(value)
        return "INTEGER"
    except ValueError:
        pass
    try:
        float(value)
        return "REAL"
    except ValueError:
        pass
    return "TEXT"


def create_table(csv_file: Path, table_name: str, conn: sqlite3.Connection) -> list:
    cursor = conn.cursor()
    with open(csv_file, encoding="utf-8") as f:
        reader = csv.reader(f)
        headers = next(reader)
        first_row = next(reader, None)

    columns = [clean_column_name(h) for h in headers]
    col_defs = [
        f"{col} {infer_sql_type(first_row[i] if first_row else None)}"
        for i, col in enumerate(columns)
    ]
    cursor.execute(
        f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(col_defs)})"
    )
    conn.commit()
    print(f"  Created table '{table_name}' ({len(columns)} columns)")
    return columns, headers


def import_csv(
    csv_file: Path,
    table_name: str,
    columns: list,
    original_headers: list,
    conn: sqlite3.Connection,
):
    cursor = conn.cursor()
    placeholders = ", ".join(["?" for _ in columns])
    rows = 0
    with open(csv_file, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            values = [clean_value(row[h]) for h in original_headers]
            cursor.execute(
                f"INSERT INTO {table_name} VALUES ({placeholders})", values
            )
            rows += 1
            if rows % 1000 == 0:
                conn.commit()
    conn.commit()
    print(f"  Imported {rows} rows into '{table_name}'")


def print_stats(conn: sqlite3.Connection):
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(f"\nDatabase summary: {len(tables)} table(s)")
    for (name,) in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {name}")
        print(f"  {name}: {cursor.fetchone()[0]:,} rows")


if __name__ == "__main__":
    if not CSV_FOLDER.exists():
        print(f"CSV folder not found: {CSV_FOLDER}")
        print("Create data/csv_db/ and place your CSV files there.")
        exit(1)

    csv_files = sorted(CSV_FOLDER.glob("*.csv"))
    if not csv_files:
        print(f"No CSV files found in {CSV_FOLDER}")
        exit(1)

    DB_FILE.parent.mkdir(parents=True, exist_ok=True)
    if DB_FILE.exists():
        DB_FILE.unlink()
        print(f"Removed existing: {DB_FILE.name}")

    print(f"Creating: {DB_FILE}\n")

    with sqlite3.connect(DB_FILE) as conn:
        for csv_file in csv_files:
            table_name = csv_file.stem.replace("-", "_").replace(" ", "_").lower()
            print(f"Processing: {csv_file.name}")
            columns, original_headers = create_table(csv_file, table_name, conn)
            import_csv(csv_file, table_name, columns, original_headers, conn)

        print_stats(conn)

    print(f"\nDone: {DB_FILE}")
