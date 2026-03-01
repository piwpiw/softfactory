#!/usr/bin/env python
"""
Automated database backup script
=================================
Supports both SQLite and PostgreSQL targets.

SQLite  : copies the .db file with a UTC timestamp suffix
PostgreSQL : runs pg_dump to produce a compressed .dump file

Optionally uploads the backup to an S3-compatible bucket.

Usage
-----
  # Manual run (auto-detects DB type from DATABASE_URL env var)
  python scripts/backup_db.py

  # Override SQLite path
  python scripts/backup_db.py --sqlite-path D:/Project/platform.db

  # Force PostgreSQL backup
  python scripts/backup_db.py --pg-url postgresql://user:pass@host/db

  # Upload to S3 after backup
  python scripts/backup_db.py --s3-bucket my-bucket --s3-prefix backups/softfactory

Cron example (daily at 03:00)
------------------------------
  0 3 * * * /usr/bin/python /path/to/scripts/backup_db.py >> /var/log/backup_db.log 2>&1
"""

import argparse
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_BACKUP_DIR = PROJECT_ROOT / "backups"
DEFAULT_SQLITE_PATH = PROJECT_ROOT / "platform.db"
TIMESTAMP_FORMAT = "%Y%m%d_%H%M%S"
KEEP_BACKUPS = int(os.getenv("BACKUP_KEEP", "14"))  # keep last N backups


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _log(msg: str, level: str = "INFO") -> None:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    tag = {"INFO": "INFO", "OK": "OK  ", "WARN": "WARN", "ERROR": "ERROR"}.get(level, level)
    print(f"[{ts}] [{tag}] {msg}")


def _ensure_backup_dir(backup_dir: Path) -> None:
    backup_dir.mkdir(parents=True, exist_ok=True)


def _timestamp() -> str:
    return datetime.now(timezone.utc).strftime(TIMESTAMP_FORMAT)


# ---------------------------------------------------------------------------
# SQLite backup
# ---------------------------------------------------------------------------

def backup_sqlite(
    sqlite_path: Path,
    backup_dir: Path,
) -> Optional[Path]:
    """Copy the SQLite .db file with a timestamp suffix.

    Uses SQLite's Online Backup API via the sqlite3 module to produce a
    consistent snapshot even if the DB is open.
    """
    import sqlite3

    if not sqlite_path.is_file():
        _log(f"SQLite file not found: {sqlite_path}", "ERROR")
        return None

    _ensure_backup_dir(backup_dir)
    dest = backup_dir / f"platform_{_timestamp()}.db"

    try:
        src_conn = sqlite3.connect(str(sqlite_path))
        dst_conn = sqlite3.connect(str(dest))
        # Use the Online Backup API — safe while DB is live
        src_conn.backup(dst_conn)
        dst_conn.close()
        src_conn.close()
        _log(f"SQLite backup created: {dest}", "OK")
        return dest
    except sqlite3.Error as exc:
        _log(f"SQLite backup failed: {exc}", "ERROR")
        return None


# ---------------------------------------------------------------------------
# PostgreSQL backup
# ---------------------------------------------------------------------------

def backup_postgres(
    pg_url: str,
    backup_dir: Path,
) -> Optional[Path]:
    """Run pg_dump to produce a custom-format compressed backup (.dump).

    Requires pg_dump to be installed and on PATH.
    The custom format (-Fc) supports parallel restore with pg_restore.
    """
    if shutil.which("pg_dump") is None:
        _log("pg_dump not found on PATH — install postgresql-client", "ERROR")
        return None

    # Normalize legacy postgres:// scheme
    if pg_url.startswith("postgres://"):
        pg_url = pg_url.replace("postgres://", "postgresql://", 1)

    _ensure_backup_dir(backup_dir)
    dest = backup_dir / f"softfactory_{_timestamp()}.dump"

    cmd = [
        "pg_dump",
        "--format=custom",         # Custom compressed format
        "--compress=9",            # Maximum compression
        "--no-acl",                # Skip GRANT/REVOKE (not needed for restore)
        "--no-owner",              # Skip ownership (restore to any user)
        f"--file={dest}",
        pg_url,
    ]

    _log(f"Running pg_dump → {dest}")
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600,  # 10-minute timeout for large databases
        )
        if result.returncode != 0:
            _log(f"pg_dump failed (exit {result.returncode}):\n{result.stderr}", "ERROR")
            return None
        _log(f"PostgreSQL backup created: {dest} ({dest.stat().st_size // 1024} KB)", "OK")
        return dest
    except subprocess.TimeoutExpired:
        _log("pg_dump timed out after 600s", "ERROR")
        return None
    except Exception as exc:
        _log(f"pg_dump error: {exc}", "ERROR")
        return None


# ---------------------------------------------------------------------------
# S3 upload (optional)
# ---------------------------------------------------------------------------

def upload_to_s3(
    local_path: Path,
    bucket: str,
    prefix: str = "backups/softfactory",
) -> bool:
    """Upload a backup file to an S3-compatible bucket.

    Requires the boto3 library and AWS credentials:
      - AWS_ACCESS_KEY_ID
      - AWS_SECRET_ACCESS_KEY
      - AWS_DEFAULT_REGION (optional, defaults to us-east-1)
      - AWS_ENDPOINT_URL (optional — for S3-compatible services like R2, MinIO)

    Returns True on success, False on failure.
    """
    try:
        import boto3
        from botocore.exceptions import BotoCoreError, ClientError
    except ImportError:
        _log("boto3 not installed — skipping S3 upload (pip install boto3)", "WARN")
        return False

    s3_key = f"{prefix.rstrip('/')}/{local_path.name}"
    endpoint_url = os.getenv("AWS_ENDPOINT_URL")  # e.g., https://account.r2.cloudflarestorage.com

    kwargs: dict = {}
    if endpoint_url:
        kwargs["endpoint_url"] = endpoint_url

    _log(f"Uploading {local_path.name} to s3://{bucket}/{s3_key} ...")
    try:
        s3 = boto3.client("s3", **kwargs)
        s3.upload_file(str(local_path), bucket, s3_key)
        _log(f"S3 upload complete: s3://{bucket}/{s3_key}", "OK")
        return True
    except (BotoCoreError, ClientError) as exc:
        _log(f"S3 upload failed: {exc}", "ERROR")
        return False


# ---------------------------------------------------------------------------
# Rotation — remove old backups
# ---------------------------------------------------------------------------

def rotate_backups(backup_dir: Path, keep: int = KEEP_BACKUPS) -> None:
    """Delete oldest backup files when count exceeds `keep`."""
    patterns = ["*.db", "*.dump"]
    all_backups = sorted(
        [f for pat in patterns for f in backup_dir.glob(pat)],
        key=lambda p: p.stat().st_mtime,
    )
    to_delete = all_backups[: max(0, len(all_backups) - keep)]
    for old in to_delete:
        try:
            old.unlink()
            _log(f"Rotated (deleted) old backup: {old.name}", "WARN")
        except OSError as exc:
            _log(f"Could not delete {old}: {exc}", "WARN")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="SoftFactory automated database backup",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--sqlite-path",
        default=str(DEFAULT_SQLITE_PATH),
        metavar="PATH",
        help=f"Path to SQLite .db file (default: {DEFAULT_SQLITE_PATH})",
    )
    parser.add_argument(
        "--pg-url",
        default=os.getenv("DATABASE_URL", ""),
        metavar="DSN",
        help="PostgreSQL DSN; defaults to DATABASE_URL env var",
    )
    parser.add_argument(
        "--backup-dir",
        default=str(DEFAULT_BACKUP_DIR),
        metavar="DIR",
        help=f"Directory for backup files (default: {DEFAULT_BACKUP_DIR})",
    )
    parser.add_argument(
        "--s3-bucket",
        default=os.getenv("BACKUP_S3_BUCKET", ""),
        metavar="BUCKET",
        help="S3 bucket name for off-site backup (optional)",
    )
    parser.add_argument(
        "--s3-prefix",
        default=os.getenv("BACKUP_S3_PREFIX", "backups/softfactory"),
        metavar="PREFIX",
        help="S3 key prefix (default: backups/softfactory)",
    )
    parser.add_argument(
        "--keep",
        type=int,
        default=KEEP_BACKUPS,
        metavar="N",
        help=f"Number of local backups to keep (default: {KEEP_BACKUPS})",
    )
    parser.add_argument(
        "--no-rotate",
        action="store_true",
        help="Disable automatic rotation of old local backups",
    )

    args = parser.parse_args()

    backup_dir = Path(args.backup_dir)
    _log("SoftFactory — Database Backup")
    _log(f"  Backup dir: {backup_dir}")

    backup_path: Optional[Path] = None

    # Determine DB type from pg_url or DATABASE_URL
    effective_pg_url = args.pg_url
    if effective_pg_url and ("postgresql" in effective_pg_url or "postgres" in effective_pg_url):
        _log("Database type: PostgreSQL")
        backup_path = backup_postgres(effective_pg_url, backup_dir)
    else:
        _log("Database type: SQLite")
        backup_path = backup_sqlite(Path(args.sqlite_path), backup_dir)

    if backup_path is None:
        _log("Backup FAILED — see errors above", "ERROR")
        sys.exit(1)

    # Optional S3 upload
    if args.s3_bucket:
        upload_to_s3(backup_path, args.s3_bucket, args.s3_prefix)
    else:
        _log("S3 upload skipped (--s3-bucket not provided)")

    # Rotate old backups
    if not args.no_rotate:
        rotate_backups(backup_dir, keep=args.keep)

    _log("Backup complete", "OK")


if __name__ == "__main__":
    main()
