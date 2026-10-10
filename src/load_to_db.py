"""
Load recipes_readable.csv and characterization_readable.csv into a SQLite database
matching schema.sql. Run once to build eln.db.

Usage: python3 load_to_db.py
"""
import argparse
import sqlite3
import csv
import re
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
DB_PATH = APP_DIR / "eln.db"
SCHEMA_PATH = APP_DIR / "schema.sql"
RECIPES_CSV = APP_DIR.parent / "data" / "recipes_readable.csv"
CHAR_CSV = APP_DIR.parent / "data" / "characterization_readable.csv"

parser = argparse.ArgumentParser(description="Load the processed literature CSVs into the Mini-ELN SQLite database.")
parser.add_argument("--reset", action="store_true", help="Replace an existing database before loading to avoid duplicate rows.")
args = parser.parse_args()
if DB_PATH.exists() and not args.reset:
    raise SystemExit(f"{DB_PATH} already exists. Use --reset to rebuild it reproducibly.")
if args.reset:
    DB_PATH.unlink(missing_ok=True)

conn = sqlite3.connect(DB_PATH)
with SCHEMA_PATH.open() as f:
    conn.executescript(f.read())

seen_dois = set()


def split_precursors(field):
    """Turn 'HAuCl4 (10 mL 0.0005 M); CTAB (10 mL 0.2 M)' into
    [('HAuCl4', '10 mL 0.0005 M'), ('CTAB', '10 mL 0.2 M')]."""
    out = []
    if not field:
        return out
    for chunk in field.split(";"):
        chunk = chunk.strip()
        if not chunk:
            continue
        m = re.match(r"^(.*?)\s*\((.*?)\)$", chunk)
        if m:
            out.append((m.group(1).strip(), m.group(2).strip()))
        else:
            out.append((chunk, None))
    return out


# --- load recipes ---
with RECIPES_CSV.open(encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        doi = row["doi"]
        if doi not in seen_dois:
            conn.execute(
                "INSERT OR IGNORE INTO articles (doi, year, citations) VALUES (?, ?, ?)",
                (doi, row["year"] or None, row["citations"] or None),
            )
            seen_dois.add(doi)

        conn.execute(
            """INSERT OR IGNORE INTO recipes
               (paragraph_id, doi, seed_mediated, target, conditions, text_snippet)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                row["paragraph_id"],
                doi,
                row["seed_mediated"] == "True",
                row["targets"],
                row["conditions"],
                row["text"],
            ),
        )

        for material, amount in split_precursors(row["precursors"]):
            conn.execute(
                "INSERT INTO precursors (paragraph_id, material, amount) VALUES (?, ?, ?)",
                (row["paragraph_id"], material, amount),
            )

# --- load characterization ---
with CHAR_CSV.open(encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        doi = row["doi"]
        if doi not in seen_dois:
            conn.execute(
                "INSERT OR IGNORE INTO articles (doi, year, citations) VALUES (?, ?, ?)",
                (doi, row["year"] or None, row["citations"] or None),
            )
            seen_dois.add(doi)

        conn.execute(
            """INSERT OR IGNORE INTO characterization
               (paragraph_id, doi, morphologies, sizes, units, text_snippet)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                row["paragraph_id"],
                doi,
                row["morphologies"],
                row["sizes"],
                row["units"],
                row["text"],
            ),
        )

conn.commit()

# quick sanity check
c = conn.cursor()
for table in ["articles", "recipes", "precursors", "characterization"]:
    n = c.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    print(f"{table}: {n} rows")

conn.close()
