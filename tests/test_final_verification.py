import pytest
import sqlite3
from database.connection import DatabaseManager
from database.migrations_manager import MigrationsManager

def test_migration_atomicity(tmp_path):
    sql_dir = tmp_path / "sql"
    sql_dir.mkdir()
    
    with open(sql_dir / "001_initial.sql", "w") as f:
        f.write("CREATE TABLE dummy (id INTEGER PRIMARY KEY);")
        
    with open(sql_dir / "002_bad.sql", "w") as f:
        f.write("CREATE TABLE valid_table (id INTEGER);\n")
        f.write("CREATE TABLE invalid_table (id INTEGER, ,);\n")
        
    db_manager = DatabaseManager(db_path=":memory:")
    mig_manager = MigrationsManager(db_manager, sql_dir=str(sql_dir))
    
    with pytest.raises(sqlite3.OperationalError):
        mig_manager.apply_migrations()
        
    conn = db_manager.get_connection()
    # Verify the earlier valid statement in the bad script rolled back
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='valid_table'")
    assert cursor.fetchone() is None, "Partial migration was not rolled back"
    
    # Verify the failed migration was not recorded
    cursor = conn.execute("SELECT * FROM schema_versions WHERE version=2")
    assert cursor.fetchone() is None, "Failed migration was incorrectly recorded"
    db_manager.close()

def test_fractional_kyat_vulnerability(db_connection):
    db_connection.execute("INSERT INTO categories (name, is_active) VALUES ('Merch', 1)")
    cat_id = db_connection.execute("SELECT last_insert_rowid()").fetchone()[0]
    
    db_connection.execute(f"INSERT INTO products (name, category_id, unit_measure, is_medicine, current_stock, selling_price, min_stock_level, is_active, inventory_value) VALUES ('Test', {cat_id}, 'pcs', 0, 10, 100, 5, 1, 500)")
    p_id = db_connection.execute("SELECT last_insert_rowid()").fetchone()[0]
    
    # Test if we can insert a fractional value into total_amount
    with pytest.raises(sqlite3.IntegrityError):
        db_connection.execute(f"INSERT INTO sales (reference, date_time, total_amount, amount_received, change_given, status) VALUES ('S002', '2026-10-09', 100.5, 100.5, 0, 'Completed')")

def test_payment_allocation_atomicity(db_connection):
    db_connection.execute("INSERT INTO suppliers (name) VALUES ('Supplier A')")
    sup_id = db_connection.execute("SELECT last_insert_rowid()").fetchone()[0]
    
    db_connection.execute(f"INSERT INTO purchases (reference, supplier_id, date, total_amount, status) VALUES ('P001', {sup_id}, '2026-10-09', 10000, 'Completed')")
    pur_id = db_connection.execute("SELECT last_insert_rowid()").fetchone()[0]
    
    db_connection.execute(f"INSERT INTO supplier_payments (reference, supplier_id, date, total_amount) VALUES ('PAY001', {sup_id}, '2026-10-09', 10000)")
    pay_id = db_connection.execute("SELECT last_insert_rowid()").fetchone()[0]
    
    # Establish baseline
    db_connection.execute(f"INSERT INTO supplier_payment_allocations (payment_id, purchase_id, allocated_amount) VALUES ({pay_id}, {pur_id}, 4000)")
    
    pur = db_connection.execute(f"SELECT amount_paid FROM purchases WHERE id={pur_id}").fetchone()
    assert pur[0] == 4000
    
    # Now simulate a transaction failure during reallocation
    try:
        # SQLite transaction block inside our manager
        db_connection.execute("SAVEPOINT test_alloc")
        db_connection.execute(f"DELETE FROM supplier_payment_allocations WHERE payment_id={pay_id}")
        # Insert too much to force a CHECK constraint error: amount_paid > total_amount, wait, is there such a check?
        # Actually total_amount is 10000, let's insert 20000 to violate constraint if one exists.
        # Let's see if we have check amount_paid <= total_amount.
        # We should check if we can force an error.
        db_connection.execute(f"INSERT INTO supplier_payment_allocations (payment_id, purchase_id, allocated_amount) VALUES ({pay_id}, {pur_id}, 20000)")
        db_connection.execute("RELEASE test_alloc")
    except sqlite3.IntegrityError:
        db_connection.execute("ROLLBACK TO test_alloc")
        
    pur_after = db_connection.execute(f"SELECT amount_paid FROM purchases WHERE id={pur_id}").fetchone()
    assert pur_after[0] == 4000, "Rollback failed to restore allocation balance"
