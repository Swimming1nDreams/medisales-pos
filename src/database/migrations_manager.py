import os
import sqlite3
from pathlib import Path
from .connection import DatabaseManager

class MigrationsManager:
    def __init__(self, db_manager: DatabaseManager, sql_dir: str = None):
        self.db_manager = db_manager
        if sql_dir is None:
            from src.utils.paths import get_migrations_dir
            self.sql_dir = get_migrations_dir()
        else:
            self.sql_dir = Path(sql_dir)

    def setup_schema_versions_table(self):
        with self.db_manager.transaction() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS schema_versions (
                    version INTEGER PRIMARY KEY,
                    script_name TEXT NOT NULL,
                    applied_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

    def get_applied_versions(self):
        conn = self.db_manager.get_connection()
        cursor = conn.execute("SELECT version FROM schema_versions")
        return {row['version'] for row in cursor.fetchall()}

    def apply_migrations(self):
        self.setup_schema_versions_table()
        applied_versions = self.get_applied_versions()
        
        # Get all .sql files in the sql directory, sorted alphabetically
        sql_files = sorted([f for f in os.listdir(self.sql_dir) if f.endswith('.sql')])
        
        for file_name in sql_files:
            # Extract version number assuming format: 001_name.sql
            try:
                version = int(file_name.split('_')[0])
            except ValueError:
                continue # Skip files that don't match the numbering convention
                
            if version not in applied_versions:
                self._apply_migration_script(version, file_name)

    def _apply_migration_script(self, version: int, file_name: str):
        file_path = self.sql_dir / file_name
        with open(file_path, 'r', encoding='utf-8') as f:
            sql_script = f.read()
            
        conn = self.db_manager.get_connection()
        conn.execute("PRAGMA foreign_keys = OFF;")
        try:
            # executescript implicitly commits any pending transaction, 
            # so we manually wrap the script in BEGIN and COMMIT to ensure it rolls back on failure
            conn.executescript(f"BEGIN;\n{sql_script}\nCOMMIT;")
            conn.execute(
                "INSERT INTO schema_versions (version, script_name) VALUES (?, ?)",
                (version, file_name)
            )
            conn.commit()
        except Exception:
            # Check if we are still in an open transaction before rolling back
            # executescript with BEGIN/COMMIT might leave the transaction open if it failed inside
            if conn.in_transaction:
                conn.rollback()
            raise
        finally:
            conn.execute("PRAGMA foreign_keys = ON;")
