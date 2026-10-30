import pytest
import sqlite3
import os
from database.connection import DatabaseManager
from database.migrations_manager import MigrationsManager

def test_migration_manager_applies_forward(tmp_path):
    # Setup temporary sql directory
    sql_dir = tmp_path / "sql"
    sql_dir.mkdir()
    
    with open(sql_dir / "001_initial.sql", "w") as f:
        f.write("CREATE TABLE dummy (id INTEGER PRIMARY KEY);")
        
    with open(sql_dir / "002_add_column.sql", "w") as f:
        f.write("ALTER TABLE dummy ADD COLUMN name TEXT;")
        
    # Setup db manager in memory
    db_manager = DatabaseManager(db_path=":memory:")
    
    # Run migrations
    mig_manager = MigrationsManager(db_manager, sql_dir=str(sql_dir))
    mig_manager.apply_migrations()
    
    # Verify tables
    conn = db_manager.get_connection()
    cursor = conn.execute("PRAGMA table_info(dummy)")
    columns = [row['name'] for row in cursor.fetchall()]
    assert 'id' in columns
    assert 'name' in columns
    
    # Verify schema_versions
    cursor = conn.execute("SELECT version, script_name FROM schema_versions ORDER BY version")
    rows = cursor.fetchall()
    assert len(rows) == 2
    assert rows[0]['version'] == 1
    assert rows[0]['script_name'] == '001_initial.sql'
    assert rows[1]['version'] == 2
    assert rows[1]['script_name'] == '002_add_column.sql'
    
    db_manager.close()
