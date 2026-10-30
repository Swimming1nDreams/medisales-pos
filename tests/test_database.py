import pytest
import sqlite3

def test_foreign_keys_enabled(db_connection):
    cursor = db_connection.execute("PRAGMA foreign_keys")
    assert cursor.fetchone()[0] == 1

def test_insert_category(db_connection):
    db_connection.execute("INSERT INTO categories (name) VALUES ('Medicine')")
    db_connection.commit()
    cursor = db_connection.execute("SELECT * FROM categories")
    row = cursor.fetchone()
    assert row['name'] == 'Medicine'

def test_foreign_key_constraint(db_connection):
    # Try to insert product with invalid category_id
    with pytest.raises(sqlite3.IntegrityError):
        db_connection.execute("""
            INSERT INTO products (name, category_id, unit_measure, selling_price, min_stock_level, is_medicine)
            VALUES ('Paracetamol', 999, 'Box', 1000, 5, 1)
        """)

def test_check_constraint_negative_price(db_connection):
    db_connection.execute("INSERT INTO categories (name) VALUES ('Medicine')")
    db_connection.commit()
    cat_id = db_connection.execute("SELECT id FROM categories").fetchone()[0]

    with pytest.raises(sqlite3.IntegrityError):
        db_connection.execute(f"""
            INSERT INTO products (name, category_id, unit_measure, selling_price, min_stock_level, is_medicine)
            VALUES ('Paracetamol', {cat_id}, 'Box', -1000, 5, 1)
        """)

def test_immutable_inventory_audit_log(db_connection):
    db_connection.execute("INSERT INTO categories (name) VALUES ('General')")
    db_connection.commit()
    cat_id = db_connection.execute("SELECT id FROM categories").fetchone()[0]
    
    db_connection.execute(f"""
        INSERT INTO products (name, category_id, unit_measure, selling_price, min_stock_level, is_medicine)
        VALUES ('Soap', {cat_id}, 'Piece', 500, 5, 0)
    """)
    db_connection.commit()
    prod_id = db_connection.execute("SELECT id FROM products").fetchone()[0]
    
    db_connection.execute(f"""
        INSERT INTO inventory_movements (product_id, quantity_change, value_change, movement_type, reference_type, reference_id, date_time)
        VALUES ({prod_id}, 10, 5000, 'Opening Stock', 'Init', 1, '2026-10-09T00:00:00')
    """)
    db_connection.commit()
    mov_id = db_connection.execute("SELECT id FROM inventory_movements").fetchone()[0]

    # Try to update
    with pytest.raises(sqlite3.IntegrityError, match="Audit log is immutable"):
        db_connection.execute(f"UPDATE inventory_movements SET quantity_change = 20 WHERE id = {mov_id}")
        
    # Try to delete
    with pytest.raises(sqlite3.IntegrityError, match="Audit log is immutable"):
        db_connection.execute(f"DELETE FROM inventory_movements WHERE id = {mov_id}")

def test_supplier_payment_allocation_triggers(db_connection):
    # Setup supplier, purchase, payment
    db_connection.execute("INSERT INTO suppliers (name) VALUES ('Supplier A')")
    sup_id = db_connection.execute("SELECT last_insert_rowid()").fetchone()[0]
    
    db_connection.execute(f"INSERT INTO purchases (reference, supplier_id, date, total_amount, status) VALUES ('PUR001', {sup_id}, '2026-10-09', 10000, 'Completed')")
    pur_id = db_connection.execute("SELECT last_insert_rowid()").fetchone()[0]
    
    db_connection.execute(f"INSERT INTO supplier_payments (reference, supplier_id, date, total_amount) VALUES ('PAY001', {sup_id}, '2026-10-09', 10000)")
    pay_id = db_connection.execute("SELECT last_insert_rowid()").fetchone()[0]
    
    # Insert allocation
    db_connection.execute(f"INSERT INTO supplier_payment_allocations (payment_id, purchase_id, allocated_amount) VALUES ({pay_id}, {pur_id}, 4000)")
    db_connection.commit()
    
    # Check trigger updated purchases and supplier_payments
    pur_paid = db_connection.execute(f"SELECT amount_paid FROM purchases WHERE id = {pur_id}").fetchone()[0]
    assert pur_paid == 4000
    
    pay_alloc = db_connection.execute(f"SELECT allocated_amount FROM supplier_payments WHERE id = {pay_id}").fetchone()[0]
    assert pay_alloc == 4000
    
def test_cross_supplier_allocation_fails(db_connection):
    db_connection.execute("INSERT INTO suppliers (name) VALUES ('Supplier A')")
    sup_a = db_connection.execute("SELECT last_insert_rowid()").fetchone()[0]
    db_connection.execute("INSERT INTO suppliers (name) VALUES ('Supplier B')")
    sup_b = db_connection.execute("SELECT last_insert_rowid()").fetchone()[0]
    
    db_connection.execute(f"INSERT INTO purchases (reference, supplier_id, date, total_amount, status) VALUES ('PUR001', {sup_a}, '2026-10-09', 10000, 'Completed')")
    pur_id = db_connection.execute("SELECT last_insert_rowid()").fetchone()[0]
    
    db_connection.execute(f"INSERT INTO supplier_payments (reference, supplier_id, date, total_amount) VALUES ('PAY001', {sup_b}, '2026-10-09', 10000)")
    pay_id = db_connection.execute("SELECT last_insert_rowid()").fetchone()[0]
    
    with pytest.raises(sqlite3.IntegrityError, match="Payment and Purchase must belong to same supplier"):
        db_connection.execute(f"INSERT INTO supplier_payment_allocations (payment_id, purchase_id, allocated_amount) VALUES ({pay_id}, {pur_id}, 4000)")

def test_cannot_void_paid_purchase(db_connection):
    db_connection.execute("INSERT INTO suppliers (name) VALUES ('Supplier A')")
    sup_id = db_connection.execute("SELECT last_insert_rowid()").fetchone()[0]
    
    db_connection.execute(f"INSERT INTO purchases (reference, supplier_id, date, total_amount, amount_paid, status) VALUES ('PUR001', {sup_id}, '2026-10-09', 10000, 4000, 'Completed')")
    pur_id = db_connection.execute("SELECT last_insert_rowid()").fetchone()[0]
    
    with pytest.raises(sqlite3.IntegrityError, match="Cannot void purchase with existing payment allocations"):
        db_connection.execute(f"UPDATE purchases SET status = 'Voided' WHERE id = {pur_id}")
