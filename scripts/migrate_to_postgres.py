#!/usr/bin/env python
"""SQLite → PostgreSQL Migration Script"""
import os
import sqlite3
import psycopg2
from psycopg2.extras import execute_values

DB_SQLITE = "platform.db"
DB_PG = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost/softfactory")

def migrate():
    print("🔄 Starting SQLite → PostgreSQL migration...")
    
    # Read SQLite
    conn_sqlite = sqlite3.connect(DB_SQLITE)
    cursor_sqlite = conn_sqlite.cursor()
    cursor_sqlite.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor_sqlite.fetchall()]
    
    print(f"Found {len(tables)} tables: {tables}")
    
    # Connect PostgreSQL
    conn_pg = psycopg2.connect(DB_PG)
    cursor_pg = conn_pg.cursor()
    
    # Copy schema & data
    for table in tables:
        print(f"  → Migrating {table}...")
        cursor_sqlite.execute(f"PRAGMA table_info({table})")
        columns = [(row[1], row[2]) for row in cursor_sqlite.fetchall()]
        
        # Create table
        col_defs = ", ".join([f"{name} {type_}" for name, type_ in columns])
        cursor_pg.execute(f"CREATE TABLE IF NOT EXISTS {table} ({col_defs})")
        
        # Copy data
        cursor_sqlite.execute(f"SELECT * FROM {table}")
        rows = cursor_sqlite.fetchall()
        if rows:
            placeholders = ", ".join(["%s"] * len(columns))
            cursor_pg.execute(f"INSERT INTO {table} VALUES ({placeholders})", rows)
    
    conn_pg.commit()
    conn_sqlite.close()
    conn_pg.close()
    
    print("✅ Migration complete!")

if __name__ == "__main__":
    migrate()
