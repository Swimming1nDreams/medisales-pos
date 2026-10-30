import pytest
import sqlite3
import os
from pathlib import Path

def test_migration_safety(tmp_path):
    from src.database.connection import DatabaseManager
    from src.database.migrations_manager import MigrationsManager
    
    db_path = tmp_path / "test.db"
    db_manager = DatabaseManager(db_path)
    mig_manager = MigrationsManager(db_manager)
    mig_manager.sql_dir = Path(os.path.join(os.path.dirname(os.path.dirname(__file__)), "src", "database", "sql"))
    
    # 1. Apply ONLY migration 001
    mig_manager.setup_schema_versions_table()
    mig_manager._apply_migration_script(1, "001_initial_schema.sql")
    
    # 2. Insert representative data
    with db_manager.transaction() as conn:
        conn.execute("INSERT INTO categories (name) VALUES ('Med Category')")
        conn.execute("INSERT INTO products (name, category_id, unit_measure, is_medicine, selling_price, min_stock_level) VALUES ('Med A', 1, 'box', 1, 100, 10)")
        conn.execute("INSERT INTO suppliers (name) VALUES ('Supp')")
        conn.execute("INSERT INTO purchases (reference, supplier_id, date, total_amount, status) VALUES ('P1', 1, '2026-01-01', 1000, 'Completed')")
        conn.execute("INSERT INTO purchase_items (purchase_id, product_id, quantity, unit_cost, line_total) VALUES (1, 1, 10, 100, 1000)")
        
        # medicine batch tied to purchase
        conn.execute("INSERT INTO medicine_batches (product_id, purchase_item_id, batch_number, initial_qty, current_qty, unit_cost) VALUES (1, 1, 'B1', 10, 10, 100)")
        conn.execute("INSERT INTO medicine_batch_movements (batch_id, quantity_change, movement_type, reference_type, reference_id, date_time) VALUES (1, 10, 'In', 'Purchase', 1, '2026-01-01')")
        
        # sale
        conn.execute("INSERT INTO sales (reference, date_time, total_amount, amount_received, change_given, status) VALUES ('S1', '2026-01-02', 100, 100, 0, 'Completed')")
        conn.execute("INSERT INTO sale_items (sale_id, product_id, quantity, unit_price, total_cost, line_total) VALUES (1, 1, 1, 100, 100, 100)")
        conn.execute("INSERT INTO sale_item_batches (sale_item_id, batch_id, quantity_deducted) VALUES (1, 1, 1)")

    # 3. Run migration 002
    mig_manager._apply_migration_script(2, "002_phase2_schema_updates.sql")
    
    # 4. Verify data preservation
    conn = db_manager.get_connection()
    batches = conn.execute("SELECT * FROM medicine_batches").fetchall()
    assert len(batches) == 1
    assert dict(batches[0])['batch_number'] == 'B1'
    
    movs = conn.execute("SELECT * FROM medicine_batch_movements").fetchall()
    assert len(movs) == 1
    assert dict(movs[0])['batch_id'] == 1
    
    # 5. Verify foreign keys
    fks = conn.execute("PRAGMA foreign_key_check").fetchall()
    assert len(fks) == 0, f"Foreign key violations found: {fks}"
    
    db_manager.close()

def test_wac_costing_scenario(inventory_service, product_service, db_manager):
    # WAC testing scenario explicitly requested
    cat_id = product_service.create_category("Merch")
    p_id = product_service.create_product("Soap", cat_id, "pcs", 1500, 10, False)
    
    # Receive 10 at 1000
    inventory_service.record_opening_stock_general(p_id, 10, 1000)
    
    # Cannot do opening stock again, so simulate a second "receive" by manually bumping product table and audit log
    # In a real app this would be a Purchase operation. Since Purchasing isn't implemented, we simulate it via db injection
    with db_manager.transaction() as conn:
        conn.execute("UPDATE products SET current_stock = current_stock + 10, inventory_value = inventory_value + 12000 WHERE id = ?", (p_id,))
        conn.execute("INSERT INTO inventory_movements (product_id, quantity_change, value_change, movement_type, reference_type, reference_id, date_time) VALUES (?, 10, 12000, 'In', 'Purchase', 99, '2026-01-01')", (p_id,))
    
    # Verify current state: 20 units, 22000 Kyat
    conn = db_manager.get_connection()
    prod = conn.execute("SELECT current_stock, inventory_value FROM products WHERE id = ?", (p_id,)).fetchone()
    assert prod['current_stock'] == 20
    assert prod['inventory_value'] == 22000
    
    # Simulate removing 3 units at current WAC
    # calculate WAC: 22000 / 20 = 1100
    value_change = inventory_service.calculate_wac_value_change(prod['current_stock'], prod['inventory_value'], 3)
    assert value_change == 3300  # 3 * 1100
    
    # Apply deduction
    with db_manager.transaction() as conn:
        conn.execute("UPDATE products SET current_stock = current_stock - 3, inventory_value = inventory_value - ? WHERE id = ?", (value_change, p_id))
    
    prod2 = conn.execute("SELECT current_stock, inventory_value FROM products WHERE id = ?", (p_id,)).fetchone()
    assert prod2['current_stock'] == 17
    assert prod2['inventory_value'] == 18700

    # Test removing all remaining stock
    # If we remove 17 units, it should exactly match 18700
    value_change_full = inventory_service.calculate_wac_value_change(prod2['current_stock'], prod2['inventory_value'], 17)
    assert value_change_full == 18700
    
    with db_manager.transaction() as conn:
        conn.execute("UPDATE products SET current_stock = current_stock - 17, inventory_value = inventory_value - ? WHERE id = ?", (value_change_full, p_id))
    
    prod3 = conn.execute("SELECT current_stock, inventory_value FROM products WHERE id = ?", (p_id,)).fetchone()
    assert prod3['current_stock'] == 0
    assert prod3['inventory_value'] == 0

def test_product_validation_safety(product_service, inventory_service, db_manager):
    # Test that unit_measure cannot be changed if stock exists
    cat_id = product_service.create_category("Merch")
    p_id = product_service.create_product("Soap", cat_id, "pcs", 100, 10, False)
    
    # It CAN be changed before transactions exist
    product_service.update_product(p_id, "Soap", cat_id, "box", 100, 10, True)
    
    # Add stock
    inventory_service.record_opening_stock_general(p_id, 10, 50)
    
    # Try changing unit_measure when stock exists
    with pytest.raises(ValueError, match="Cannot change unit measure"):
        product_service.update_product(p_id, "Soap", cat_id, "pcs", 100, 10, True)
