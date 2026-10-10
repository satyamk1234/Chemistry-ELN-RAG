"""Validate and import lab experiment CSV exports into the Mini-ELN.

This deliberately treats the CSV as an instrument or notebook export: rows are
validated before anything is written, and each retained record stores its
source file and import timestamp for provenance.
"""
from __future__ import annotations

import argparse
import csv
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
REQUIRED_COLUMNS = {
    "experiment_id", "experiment_date", "operator", "sample_id",
    "procedure", "outcome", "source_file",
}
OPTIONAL_COLUMNS = {"conditions", "instrument"}


def validate_rows(rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], list[str]]:
    """Return cleaned rows and human-readable validation errors."""
    cleaned, errors, seen_ids = [], [], set()
    for line_number, row in enumerate(rows, start=2):
        row = {(key or "").strip(): (value or "").strip() for key, value in row.items()}
        missing = sorted(column for column in REQUIRED_COLUMNS if not row.get(column))
        if missing:
            errors.append(f"row {line_number}: missing {', '.join(missing)}")
            continue
        try:
            datetime.strptime(row["experiment_date"], "%Y-%m-%d")
        except ValueError:
            errors.append(f"row {line_number}: experiment_date must use YYYY-MM-DD")
            continue
        if row["experiment_id"] in seen_ids:
            errors.append(f"row {line_number}: duplicate experiment_id {row['experiment_id']}")
            continue
        seen_ids.add(row["experiment_id"])
        cleaned.append({column: row.get(column, "") for column in REQUIRED_COLUMNS | OPTIONAL_COLUMNS})
    return cleaned, errors


def read_and_validate_csv(file_obj) -> tuple[list[dict[str, str]], list[str]]:
    reader = csv.DictReader(file_obj)
    headers = set(reader.fieldnames or [])
    missing_headers = sorted(REQUIRED_COLUMNS - headers)
    if missing_headers:
        return [], [f"CSV is missing required columns: {', '.join(missing_headers)}"]
    return validate_rows(list(reader))


def import_rows(db_path: Path, rows: list[dict[str, str]], import_file: str) -> int:
    conn = sqlite3.connect(db_path)
    imported_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    try:
        conn.executemany(
            """INSERT INTO lab_experiments
            (experiment_id, experiment_date, operator, sample_id, procedure, conditions,
             outcome, instrument, source_file, imported_at)
            VALUES (:experiment_id, :experiment_date, :operator, :sample_id, :procedure,
                    :conditions, :outcome, :instrument, :source_file, :imported_at)
            ON CONFLICT(experiment_id) DO UPDATE SET
                experiment_date=excluded.experiment_date, operator=excluded.operator,
                sample_id=excluded.sample_id, procedure=excluded.procedure,
                conditions=excluded.conditions, outcome=excluded.outcome,
                instrument=excluded.instrument, source_file=excluded.source_file,
                imported_at=excluded.imported_at""",
            [{**row, "source_file": row["source_file"] or import_file, "imported_at": imported_at} for row in rows],
        )
        conn.commit()
        return len(rows)
    finally:
        conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate and import Mini-ELN lab CSV records.")
    parser.add_argument("csv_file", type=Path)
    parser.add_argument("--db", type=Path, default=APP_DIR / "eln.db")
    parser.add_argument("--check", action="store_true", help="Validate only; do not write to SQLite.")
    args = parser.parse_args()
    with args.csv_file.open(encoding="utf-8", newline="") as source:
        rows, errors = read_and_validate_csv(source)
    if errors:
        raise SystemExit("Validation failed:\n- " + "\n- ".join(errors))
    if args.check:
        print(f"Validation passed: {len(rows)} records would be imported.")
        return
    print(f"Imported {import_rows(args.db, rows, args.csv_file.name)} records into {args.db}.")


if __name__ == "__main__":
    main()
