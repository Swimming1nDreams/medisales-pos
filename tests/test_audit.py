import pytest
import sqlite3
from database.connection import DatabaseManager
from database.migrations_manager import MigrationsManager

def test_migration_executescript_rollback_failure(tmp_path):
    """
    Proves that executescript might commit implicitly, 
    but we can test if our manager handles rollbacks.
    """
    sql_dir = tmp_path / "sql"
    sql_dir.mkdir()
    
    with open(sql_dir / "001_initial.sql", "w") as f:
        f.write("CREATE TABLE dummy (id INTEGER PRIMARY KEY);")
        
    # This script has an error halfway
    with open(sql_dir / "002_bad.sql", "w") as f:
        f.write("CREATE TABLE valid_table (id INTEGER);\n")
        f.write("CREATE TABLE invalid_table (id INTEGER, ,);\n")
        
    db_manager = DatabaseManager(db_path=":memory:")
    mig_manager = MigrationsManager(db_manager, sql_dir=str(sql_dir))
    
    with pytest.raises(sqlite3.OperationalError):
        mig_manager.apply_migrations()
        
    # If transaction works, valid_table should NOT exist because it rolled back
    conn = db_manager.get_connection()
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='valid_table'")
    row = cursor.fetchone()
    # If the row IS NOT None, the rollback failed!
    assert row is None, "executescript implicitly committed the first table before the error!"
    db_manager.close()

def test_cannot_delete_completed_sale(db_connection):
    db_connection.execute("INSERT INTO sales (reference, date_time, total_amount, amount_received, change_given, status) VALUES ('S001', '2026-10-09', 1000, 1000, 0, 'Completed')")
    sale_id = db_connection.execute("SELECT last_insert_rowid()").fetchone()[0]
    
    with pytest.raises(sqlite3.IntegrityError, match="Cannot delete completed sales"):
        db_connection.execute(f"DELETE FROM sales WHERE id = {sale_id}")

def test_cannot_delete_completed_purchase(db_connection):
    db_connection.execute("INSERT INTO suppliers (name) VALUES ('Supplier A')")
    sup_id = db_connection.execute("SELECT last_insert_rowid()").fetchone()[0]
    
    db_connection.execute(f"INSERT INTO purchases (reference, supplier_id, date, total_amount, status) VALUES ('P001', {sup_id}, '2026-10-09', 1000, 'Completed')")
    pur_id = db_connection.execute("SELECT last_insert_rowid()").fetchone()[0]
    
    with pytest.raises(sqlite3.IntegrityError, match="Cannot delete completed purchases"):
        db_connection.execute(f"DELETE FROM purchases WHERE id = {pur_id}")

def test_update_payment_allocation_prevented(db_connection):
    db_connection.execute("INSERT INTO suppliers (name) VALUES ('Supplier A')")
    sup_id = db_connection.execute("SELECT last_insert_rowid()").fetchone()[0]
    
    db_connection.execute(f"INSERT INTO purchases (reference, supplier_id, date, total_amount, status) VALUES ('P001', {sup_id}, '2026-10-09', 10000, 'Completed')")
    pur_id = db_connection.execute("SELECT last_insert_rowid()").fetchone()[0]
    
    db_connection.execute(f"INSERT INTO supplier_payments (reference, supplier_id, date, total_amount) VALUES ('PAY001', {sup_id}, '2026-10-09', 10000)")
    pay_id = db_connection.execute("SELECT last_insert_rowid()").fetchone()[0]
    
    db_connection.execute(f"INSERT INTO supplier_payment_allocations (payment_id, purchase_id, allocated_amount) VALUES ({pay_id}, {pur_id}, 4000)")
    alloc_id = db_connection.execute("SELECT last_insert_rowid()").fetchone()[0]
    
    with pytest.raises(sqlite3.IntegrityError, match="Allocations cannot be updated"):
        db_connection.execute(f"UPDATE supplier_payment_allocations SET allocated_amount = 5000 WHERE id = {alloc_id}")
