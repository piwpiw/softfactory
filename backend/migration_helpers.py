"""
Database Migration Helpers — Manual migration support for Flask-SQLAlchemy
Created: 2026-02-26
Purpose: Support schema modifications without Flask-Migrate
"""

from sqlalchemy import text
from datetime import datetime
from .models import db


class MigrationHelper:
    """Helper class for manual database migrations"""

    @staticmethod
    def check_column_exists(table_name: str, column_name: str) -> bool:
        """Check if a column exists in a table"""
        try:
            # For SQLite
            result = db.session.execute(
                text(f"PRAGMA table_info({table_name})")
            ).fetchall()
            columns = [row[1] for row in result]
            return column_name in columns
        except Exception as e:
            print(f"Error checking column: {e}")
            return False

    @staticmethod
    def add_column(table_name: str, column_name: str, column_definition: str) -> bool:
        """Add a column to a table (SQLite compatible)"""
        try:
            if MigrationHelper.check_column_exists(table_name, column_name):
                print(f"Column {table_name}.{column_name} already exists")
                return True

            query = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}"
            db.session.execute(text(query))
            db.session.commit()
            print(f"✓ Added column {table_name}.{column_name}")
            return True
        except Exception as e:
            db.session.rollback()
            print(f"✗ Error adding column: {e}")
            return False

    @staticmethod
    def run_migrations(app) -> dict:
        """Run all pending migrations"""
        results = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'details': []
        }

        with app.app_context():
            migrations = [
                # Migration 1: Add review_content to ReviewApplication
                {
                    'name': 'Add review_content to ReviewApplication',
                    'table': 'review_applications',
                    'column': 'review_content',
                    'definition': 'TEXT'
                },
                # Migration 2: Add last_reviewed to ReviewAccount
                {
                    'name': 'Add last_reviewed to ReviewAccount',
                    'table': 'review_accounts',
                    'column': 'last_reviewed',
                    'definition': 'DATETIME'
                },
            ]

            for migration in migrations:
                results['total'] += 1
                try:
                    success = MigrationHelper.add_column(
                        migration['table'],
                        migration['column'],
                        migration['definition']
                    )
                    if success:
                        results['success'] += 1
                        results['details'].append({
                            'migration': migration['name'],
                            'status': 'success'
                        })
                    else:
                        results['failed'] += 1
                        results['details'].append({
                            'migration': migration['name'],
                            'status': 'failed'
                        })
                except Exception as e:
                    results['failed'] += 1
                    results['details'].append({
                        'migration': migration['name'],
                        'status': 'failed',
                        'error': str(e)
                    })

        return results


def verify_schema(app) -> dict:
    """Verify database schema integrity"""
    verification = {
        'timestamp': datetime.utcnow().isoformat(),
        'tables': {},
        'issues': []
    }

    with app.app_context():
        # Check SNS models
        required_tables = [
            'sns_link_in_bios',
            'sns_automates',
            'sns_competitors',
            'review_accounts',
            'review_applications',
        ]

        for table in required_tables:
            try:
                result = db.session.execute(
                    text(f"PRAGMA table_info({table})")
                ).fetchall()
                columns = {row[1]: row[2] for row in result}
                verification['tables'][table] = {
                    'exists': True,
                    'columns': columns
                }
            except Exception as e:
                verification['tables'][table] = {
                    'exists': False,
                    'error': str(e)
                }
                verification['issues'].append(f"Table {table} missing or error: {e}")

        # Check specific required columns
        required_columns = [
            ('review_applications', 'review_content'),
            ('review_accounts', 'last_reviewed'),
            ('sns_link_in_bios', 'slug'),
            ('sns_automates', 'next_run'),
        ]

        for table, column in required_columns:
            if not MigrationHelper.check_column_exists(table, column):
                verification['issues'].append(f"Required column missing: {table}.{column}")

    return verification


if __name__ == '__main__':
    import os
    import sys

    # Set environment variables before importing app
    os.environ.setdefault('FLASK_ENV', 'development')

    try:
        from .app import create_app
        app = create_app()
    except AttributeError as e:
        print(f"Warning: Config initialization issue: {e}")
        print("Creating app with minimal config...")

        from flask import Flask
        from .models import db, init_db

        app = Flask(__name__)
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'platform.db')
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

        db.init_app(app)

    print("=" * 60)
    print("Database Schema Verification")
    print("=" * 60)

    # Verify schema
    verification = verify_schema(app)
    print(f"\nVerification timestamp: {verification['timestamp']}")
    print(f"\nTables found: {len(verification['tables'])}")

    if verification['issues']:
        print(f"\nIssues found: {len(verification['issues'])}")
        for issue in verification['issues']:
            print(f"  - {issue}")
    else:
        print("\n✓ All schema checks passed!")

    # Run migrations
    print("\n" + "=" * 60)
    print("Running Pending Migrations")
    print("=" * 60)

    results = MigrationHelper.run_migrations(app)
    print(f"\nTotal migrations: {results['total']}")
    print(f"Successful: {results['success']}")
    print(f"Failed: {results['failed']}")

    if results['details']:
        print("\nMigration details:")
        for detail in results['details']:
            status_icon = "[OK]" if detail['status'] == 'success' else "[FAIL]"
            print(f"  {status_icon} {detail['migration']}")
            if 'error' in detail:
                print(f"    Error: {detail['error']}")
