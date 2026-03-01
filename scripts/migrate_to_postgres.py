#!/usr/bin/env python
"""
Migration script: SQLite → PostgreSQL
======================================
Reads every row from the SQLite source database and inserts them into a
target PostgreSQL database in FK-safe dependency order.

Usage
-----
  python scripts/migrate_to_postgres.py \
      --sqlite-path D:/Project/platform.db \
      --pg-url "postgresql://user:pass@host:5432/softfactory"

Options
-------
  --sqlite-path   Absolute path to the SQLite .db file (required)
  --pg-url        PostgreSQL DSN (required; may also be set via DATABASE_URL env var)
  --dry-run       Print row counts per table without writing to PostgreSQL
  --tables        Comma-separated list of tables to migrate (default: all)
  --batch-size    Rows inserted per batch / transaction (default: 500)
  --truncate      Truncate target table before inserting (default: False)

Examples
--------
  # Dry run — inspect what would be migrated
  python scripts/migrate_to_postgres.py \
      --sqlite-path D:/Project/platform.db \
      --pg-url postgresql://postgres:postgres@localhost/softfactory \
      --dry-run

  # Migrate only users and products
  python scripts/migrate_to_postgres.py \
      --sqlite-path D:/Project/platform.db \
      --pg-url postgresql://postgres:postgres@localhost/softfactory \
      --tables users,products
"""

import argparse
import json
import os
import sqlite3
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

try:
    import psycopg2
    from psycopg2 import sql as pg_sql
    from psycopg2.extras import execute_values
except ImportError:
    sys.exit(
        "ERROR: psycopg2-binary is not installed.\n"
        "  Run: pip install psycopg2-binary"
    )

# ---------------------------------------------------------------------------
# Table migration order — respects FK dependencies (parents before children)
# ---------------------------------------------------------------------------
TABLE_ORDER: List[str] = [
    # Platform (root entities)
    "users",
    "products",
    "subscriptions",
    "payments",
    # CooCook
    "chefs",
    "bookings",
    "booking_payments",
    "booking_reviews",
    "shopping_lists",
    # SNS Auto (campaign before posts because posts FK → campaigns)
    "sns_campaigns",
    "sns_accounts",
    "sns_posts",
    "sns_templates",
    "sns_analytics",
    "sns_inbox_messages",
    "sns_oauth_states",
    "sns_settings",
    "sns_link_in_bios",
    "sns_automates",
    "sns_competitors",
    # Review
    "review_listings",
    "review_bookmarks",
    "review_accounts",
    "review_applications",
    "review_auto_rules",
    # Campaigns
    "campaigns",
    "campaign_applications",
    # AI Automation
    "ai_employees",
    "scenarios",
    # Webapp Builder
    "bootcamp_enrollments",
    "webapps",
    # Experience / Crawlers
    "experience_listings",
    "crawler_logs",
    # Security / Audit
    "login_attempts",
    "error_logs",
    "error_patterns",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _log(message: str, level: str = "INFO") -> None:
    ts = datetime.now().strftime("%H:%M:%S")
    prefix = {"INFO": "[INFO]", "WARN": "[WARN]", "ERROR": "[ERROR]", "OK": "[ OK ]"}.get(level, "[    ]")
    print(f"{ts} {prefix} {message}")


def _sqlite_connect(path: str) -> sqlite3.Connection:
    if not os.path.isfile(path):
        sys.exit(f"ERROR: SQLite file not found: {path}")
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row  # dict-like rows
    # Enable WAL mode for safe concurrent reads
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def _pg_connect(dsn: str) -> "psycopg2.connection":
    # Normalize legacy postgres:// scheme
    if dsn.startswith("postgres://"):
        dsn = dsn.replace("postgres://", "postgresql://", 1)
    try:
        return psycopg2.connect(dsn)
    except psycopg2.OperationalError as exc:
        sys.exit(f"ERROR: Cannot connect to PostgreSQL:\n  {exc}")


def _get_sqlite_tables(conn: sqlite3.Connection) -> List[str]:
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    )
    return [row[0] for row in cursor.fetchall()]


def _get_column_names(conn: sqlite3.Connection, table: str) -> List[str]:
    cursor = conn.execute(f"PRAGMA table_info({table})")
    return [row["name"] for row in cursor.fetchall()]


def _coerce_value(value: Any) -> Any:
    """Convert SQLite value types to PostgreSQL-compatible Python types.

    SQLite stores JSON as TEXT, booleans as 0/1 integers, etc.
    psycopg2 handles most conversions natively; we only fix edge cases.
    """
    if isinstance(value, bytes):
        # Attempt UTF-8 decode; fall back to raw bytes
        try:
            return value.decode("utf-8")
        except UnicodeDecodeError:
            return value
    return value


def _coerce_row(row: sqlite3.Row) -> Tuple:
    return tuple(_coerce_value(v) for v in row)


def _migrate_table(
    sqlite_conn: sqlite3.Connection,
    pg_conn: "psycopg2.connection",
    table: str,
    batch_size: int,
    truncate: bool,
    dry_run: bool,
) -> Dict[str, Any]:
    """Migrate a single table. Returns a result dict."""
    result: Dict[str, Any] = {
        "table": table,
        "rows_read": 0,
        "rows_written": 0,
        "skipped": False,
        "error": None,
    }

    # Check table exists in SQLite
    cursor_sq = sqlite_conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)
    )
    if cursor_sq.fetchone() is None:
        _log(f"  Skipping '{table}' — not found in SQLite", "WARN")
        result["skipped"] = True
        return result

    columns = _get_column_names(sqlite_conn, table)
    if not columns:
        _log(f"  Skipping '{table}' — no columns detected", "WARN")
        result["skipped"] = True
        return result

    # Count rows
    count_row = sqlite_conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
    total_rows: int = count_row[0] if count_row else 0
    result["rows_read"] = total_rows

    if total_rows == 0:
        _log(f"  '{table}': 0 rows — nothing to migrate")
        return result

    if dry_run:
        _log(f"  [DRY RUN] '{table}': {total_rows} rows (not written)")
        return result

    pg_cursor = pg_conn.cursor()

    # Optionally truncate target table (restart identity resets sequences)
    if truncate:
        pg_cursor.execute(
            pg_sql.SQL("TRUNCATE TABLE {} RESTART IDENTITY CASCADE").format(
                pg_sql.Identifier(table)
            )
        )
        _log(f"  '{table}': TRUNCATED", "WARN")

    # Build INSERT statement using psycopg2 sql composition (SQL-injection safe)
    col_identifiers = [pg_sql.Identifier(c) for c in columns]
    insert_stmt = pg_sql.SQL(
        "INSERT INTO {table} ({cols}) VALUES %s ON CONFLICT DO NOTHING"
    ).format(
        table=pg_sql.Identifier(table),
        cols=pg_sql.SQL(", ").join(col_identifiers),
    )

    rows_written = 0
    offset = 0

    try:
        while True:
            batch_cursor = sqlite_conn.execute(
                f"SELECT * FROM {table} LIMIT ? OFFSET ?", (batch_size, offset)
            )
            batch = batch_cursor.fetchall()
            if not batch:
                break

            rows = [_coerce_row(r) for r in batch]
            execute_values(pg_cursor, insert_stmt, rows)
            rows_written += len(rows)
            offset += batch_size

            _log(f"  '{table}': {rows_written}/{total_rows} rows written...")

        pg_conn.commit()
        result["rows_written"] = rows_written

    except psycopg2.Error as exc:
        pg_conn.rollback()
        result["error"] = str(exc)
        _log(f"  ERROR migrating '{table}': {exc}", "ERROR")

    return result


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="SQLite → PostgreSQL data migration for SoftFactory",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--sqlite-path",
        required=True,
        metavar="PATH",
        help="Absolute path to platform.db",
    )
    parser.add_argument(
        "--pg-url",
        default=os.getenv("DATABASE_URL", ""),
        metavar="DSN",
        help="PostgreSQL DSN (e.g. postgresql://user:pass@host/db). "
             "Defaults to DATABASE_URL env var.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print row counts per table without writing to PostgreSQL",
    )
    parser.add_argument(
        "--tables",
        default="",
        metavar="TABLE1,TABLE2",
        help="Comma-separated list of tables to migrate (default: all in FK order)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=500,
        metavar="N",
        help="Rows inserted per batch (default: 500)",
    )
    parser.add_argument(
        "--truncate",
        action="store_true",
        help="TRUNCATE … RESTART IDENTITY CASCADE before inserting rows",
    )

    args = parser.parse_args()

    if not args.pg_url and not args.dry_run:
        parser.error(
            "Provide --pg-url or set DATABASE_URL env var "
            "(or use --dry-run to inspect without a PostgreSQL connection)"
        )

    # Determine table list
    if args.tables:
        requested = [t.strip() for t in args.tables.split(",") if t.strip()]
        # Preserve FK-safe order for requested subset
        tables_to_migrate = [t for t in TABLE_ORDER if t in requested]
        unknown = set(requested) - set(TABLE_ORDER)
        if unknown:
            _log(f"Unknown tables (will attempt anyway): {unknown}", "WARN")
            tables_to_migrate += list(unknown)
    else:
        tables_to_migrate = list(TABLE_ORDER)

    _log("SoftFactory — SQLite → PostgreSQL Migration")
    _log(f"  Source  : {args.sqlite_path}")
    _log(f"  Target  : {'[DRY RUN]' if args.dry_run else args.pg_url}")
    _log(f"  Tables  : {len(tables_to_migrate)}")
    _log(f"  Batch   : {args.batch_size} rows/batch")
    _log(f"  Truncate: {args.truncate}")
    print()

    sqlite_conn = _sqlite_connect(args.sqlite_path)
    pg_conn: Optional["psycopg2.connection"] = None

    if not args.dry_run:
        pg_conn = _pg_connect(args.pg_url)
        # Disable FK checks during migration for speed; re-enable after
        with pg_conn.cursor() as cur:
            cur.execute("SET session_replication_role = 'replica'")
        pg_conn.commit()
        _log("PostgreSQL FK checks temporarily disabled (session_replication_role=replica)")

    # ----- Migrate each table -----
    summary: List[Dict[str, Any]] = []
    errors: List[str] = []
    start_time = datetime.now()

    for table in tables_to_migrate:
        _log(f"Migrating: {table}")
        result = _migrate_table(
            sqlite_conn=sqlite_conn,
            pg_conn=pg_conn,  # type: ignore[arg-type]
            table=table,
            batch_size=args.batch_size,
            truncate=args.truncate,
            dry_run=args.dry_run,
        )
        summary.append(result)
        if result["error"]:
            errors.append(f"{table}: {result['error']}")
        elif not result["skipped"] and not args.dry_run:
            _log(f"  '{table}': {result['rows_written']} rows OK", "OK")

    # Re-enable FK checks
    if pg_conn and not args.dry_run:
        with pg_conn.cursor() as cur:
            cur.execute("SET session_replication_role = 'origin'")
        pg_conn.commit()
        _log("PostgreSQL FK checks re-enabled")

    # Reset PostgreSQL sequences to max(id)+1 to avoid PK conflicts
    if pg_conn and not args.dry_run:
        _log("Resetting PostgreSQL sequences...")
        with pg_conn.cursor() as cur:
            for table in tables_to_migrate:
                try:
                    cur.execute(
                        f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), "
                        f"COALESCE(MAX(id), 0) + 1, false) FROM {table}"
                    )
                except psycopg2.Error:
                    # Table may not have a serial 'id' column — skip silently
                    pg_conn.rollback()
                    continue
        pg_conn.commit()
        _log("Sequences reset", "OK")

    # Close connections
    sqlite_conn.close()
    if pg_conn:
        pg_conn.close()

    # ----- Print summary -----
    elapsed = (datetime.now() - start_time).total_seconds()
    total_read = sum(r["rows_read"] for r in summary)
    total_written = sum(r["rows_written"] for r in summary)
    skipped = sum(1 for r in summary if r["skipped"])

    print()
    _log("=" * 60)
    _log(f"Migration complete in {elapsed:.1f}s")
    _log(f"  Tables   : {len(summary)} total, {skipped} skipped")
    _log(f"  Rows read: {total_read}")
    _log(f"  Rows written: {total_written}")

    if errors:
        _log(f"  ERRORS ({len(errors)}):", "ERROR")
        for err in errors:
            _log(f"    - {err}", "ERROR")
        sys.exit(1)
    else:
        _log("All tables migrated successfully", "OK")


if __name__ == "__main__":
    main()
