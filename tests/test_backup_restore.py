import os
import sqlite3
import json
import pytest
from unittest.mock import patch
from PySide6.QtWidgets import QMessageBox

from src.database.connection import DatabaseManager
from src.database.migrations_manager import MigrationsManager
from src.ui_web.bridge import FrontendBridge

@pytest.fixture
def test_dbs(tmp_path):
    live_db_path = str(tmp_path / "live.db")
    backup_db_path = str(tmp_path / "backup.db")

    db_manager = DatabaseManager(live_db_path)
    mig = MigrationsManager(db_manager)
    mig.apply_migrations()

    # Seed initial test data
    with db_manager.transaction() as conn:
        conn.execute("INSERT INTO categories (name) VALUES ('Antibiotics')")
        cat_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.execute("INSERT INTO products (name, category_id, is_medicine, unit_measure, selling_price, min_stock_level, is_active) VALUES ('Amoxicillin 500mg', ?, 1, 'strip', 1000, 5, 1)", (cat_id,))

    yield db_manager, live_db_path, backup_db_path
    db_manager.close()

def test_backup_creates_valid_copy_and_preserves_active_connection(test_dbs):
    db_manager, live_path, backup_path = test_dbs

    # Perform online backup
    db_manager.backup_to_file(backup_path)

    assert os.path.exists(backup_path)
    assert os.path.getsize(backup_path) > 0

    # Verify backup is a valid SQLite DB with integrity ok
    with sqlite3.connect(backup_path) as b_conn:
        check = b_conn.execute("PRAGMA integrity_check").fetchone()
        assert check[0] == "ok"
        prod = b_conn.execute("SELECT name FROM products").fetchone()
        assert prod[0] == "Amoxicillin 500mg"

    # Verify live connection remains open, responsive, and can write immediately
    with db_manager.transaction() as live_conn:
        live_conn.execute("INSERT INTO categories (name) VALUES ('Painkillers')")
        cat2_id = live_conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        live_conn.execute("INSERT INTO products (name, category_id, is_medicine, unit_measure, selling_price, min_stock_level, is_active) VALUES ('Paracetamol 500mg', ?, 1, 'strip', 500, 10, 1)", (cat2_id,))

    # Confirm live DB has 2 products and backup still has 1
    with db_manager.get_connection() as live_conn:
        live_count = live_conn.execute("SELECT count(*) FROM products").fetchone()[0]
        assert live_count == 2

    with sqlite3.connect(backup_path) as b_conn:
        b_count = b_conn.execute("SELECT count(*) FROM products").fetchone()[0]
        assert b_count == 1

def test_restore_replaces_data_and_creates_safety_backup(test_dbs, tmp_path):
    db_manager, live_path, backup_path = test_dbs

    # 1. Create a backup of state 1 (1 product: Amoxicillin)
    db_manager.backup_to_file(backup_path)

    # 2. Modify live database to state 2 (add Ibuprofen)
    with db_manager.transaction() as live_conn:
        cat_id = live_conn.execute("SELECT id FROM categories WHERE name = 'Antibiotics'").fetchone()[0]
        live_conn.execute("INSERT INTO products (name, category_id, is_medicine, unit_measure, selling_price, min_stock_level, is_active) VALUES ('Ibuprofen 400mg', ?, 1, 'tablet', 800, 20, 1)", (cat_id,))

    live_prods_before = [r[0] for r in db_manager.get_connection().execute("SELECT name FROM products ORDER BY id").fetchall()]
    assert live_prods_before == ['Amoxicillin 500mg', 'Ibuprofen 400mg']

    # 3. Restore state 1 from backup
    safety_backup = db_manager.restore_from_file(backup_path)

    # Verify safety backup was created and contains state 2
    assert os.path.exists(safety_backup)
    with sqlite3.connect(safety_backup) as s_conn:
        s_prods = [r[0] for r in s_conn.execute("SELECT name FROM products ORDER BY id").fetchall()]
        assert s_prods == ['Amoxicillin 500mg', 'Ibuprofen 400mg']

    # Verify live database connection immediately sees state 1 (only Amoxicillin)
    live_prods_after = [r[0] for r in db_manager.get_connection().execute("SELECT name FROM products ORDER BY id").fetchall()]
    assert live_prods_after == ['Amoxicillin 500mg']

def test_restore_rejects_corrupted_file(test_dbs, tmp_path):
    db_manager, live_path, _ = test_dbs

    # Create a corrupted file
    corrupt_file = str(tmp_path / "corrupt.db")
    with open(corrupt_file, "wb") as f:
        f.write(b"NOT_A_SQLITE_DATABASE_INVALID_BINARY_DATA_CORRUPTION_TEST")

    with pytest.raises(ValueError, match="corrupt or not a valid SQLite database"):
        db_manager.restore_from_file(corrupt_file)

    # Ensure live database was untouched
    live_prods = [r[0] for r in db_manager.get_connection().execute("SELECT name FROM products").fetchall()]
    assert live_prods == ['Amoxicillin 500mg']

def test_restore_rejects_arbitrary_sqlite_missing_required_tables(test_dbs, tmp_path):
    db_manager, live_path, _ = test_dbs

    # Create a valid SQLite database but without medisales schema
    other_db = str(tmp_path / "arbitrary.db")
    with sqlite3.connect(other_db) as conn:
        conn.execute("CREATE TABLE random_stuff (id INTEGER PRIMARY KEY, note TEXT)")
        conn.execute("INSERT INTO random_stuff VALUES (1, 'hello')")

    with pytest.raises(ValueError, match="missing required tables"):
        db_manager.restore_from_file(other_db)

    # Ensure live database was untouched
    live_prods = [r[0] for r in db_manager.get_connection().execute("SELECT name FROM products").fetchall()]
    assert live_prods == ['Amoxicillin 500mg']

def test_restore_rejects_nonexistent_file(test_dbs):
    db_manager, _, _ = test_dbs
    with pytest.raises(FileNotFoundError):
        db_manager.restore_from_file("C:/does_not_exist/random_nonexistent_file.db")

def test_bridge_backup_and_restore_flow(test_dbs, tmp_path):
    db_manager, live_path, backup_path = test_dbs
    bridge = FrontendBridge({'db_manager': db_manager})

    # Test Cancel in backup file dialog
    with patch("PySide6.QtWidgets.QFileDialog.getSaveFileName", return_value=("", "")):
        res = json.loads(bridge.backup_database())
        assert res['status'] == 'success'
        assert res['data']['cancelled'] is True

    # Test successful backup through bridge
    with patch("PySide6.QtWidgets.QFileDialog.getSaveFileName", return_value=(backup_path, "")):
        res = json.loads(bridge.backup_database())
        assert res['status'] == 'success'
        assert res['data']['cancelled'] is False
        assert os.path.exists(backup_path)

    # Test Cancel in restore file dialog
    with patch("PySide6.QtWidgets.QFileDialog.getOpenFileName", return_value=("", "")):
        res = json.loads(bridge.restore_database())
        assert res['status'] == 'success'
        assert res['data']['cancelled'] is True

    # Test Reject confirmation dialog
    with patch("PySide6.QtWidgets.QFileDialog.getOpenFileName", return_value=(backup_path, "")), \
         patch("PySide6.QtWidgets.QMessageBox.warning", return_value=QMessageBox.No):
        res = json.loads(bridge.restore_database())
        assert res['status'] == 'success'
        assert res['data']['cancelled'] is True

    # Test successful restore through bridge
    signals_received = []
    bridge.dataChanged.connect(lambda domain: signals_received.append(domain))

    with patch("PySide6.QtWidgets.QFileDialog.getOpenFileName", return_value=(backup_path, "")), \
         patch("PySide6.QtWidgets.QMessageBox.warning", return_value=QMessageBox.Yes):
        res = json.loads(bridge.restore_database())
        assert res['status'] == 'success'
        assert res['data']['cancelled'] is False
        assert "Database successfully restored" in res['data']['message']
        assert "medisales_pre_restore_" in res['data']['safety_backup']

    # Check signals emitted for UI reload
    for expected in ["dashboard", "sales", "inventory", "purchases", "suppliers", "expenses", "products", "reports"]:
        assert expected in signals_received
