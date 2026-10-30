import pytest
from datetime import datetime, timedelta
import sqlite3

def test_successful_sale_multiple_products(product_service, supplier_service, inventory_service, sales_service, db_manager):
    cat_id = product_service.create_category("Cat")
    p1 = product_service.create_product("Merch 1", cat_id, "box", 100, 10, False)
    p2 = product_service.create_product("Merch 2", cat_id, "box", 150, 10, False)
    
    inventory_service.record_opening_stock_general(p1, 50, 80)
    inventory_service.record_opening_stock_general(p2, 30, 100)

    items = [
        {"product_id": p1, "quantity": 2, "unit_price": 100},
        {"product_id": p2, "quantity": 1, "unit_price": 150}
    ]
    sale_id = sales_service.create_sale("S-001", items, 350)
    
    sale = sales_service.get_sale(sale_id)
    assert sale['total_amount'] == 350
    assert sale['amount_received'] == 350
    assert sale['change_given'] == 0
    assert len(sale['items']) == 2

def test_sale_medicine_and_general(product_service, inventory_service, sales_service):
    cat_id = product_service.create_category("Cat")
    p1 = product_service.create_product("Merch", cat_id, "pcs", 100, 10, False)
    p2 = product_service.create_product("Med", cat_id, "box", 200, 10, True)

    inventory_service.record_opening_stock_general(p1, 10, 50)
    future_date = (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d")
    inventory_service.record_opening_stock_medicine(p2, [
        {"batch_number": "B1", "expiry_date": future_date, "quantity": 10, "unit_cost": 100}
    ])

    items = [
        {"product_id": p1, "quantity": 2, "unit_price": 100},
        {"product_id": p2, "quantity": 1, "unit_price": 200}
    ]
    sale_id = sales_service.create_sale("S-002", items, 400)
    
    sale = sales_service.get_sale(sale_id)
    assert sale['total_amount'] == 400

def test_fefo_batch_selection(product_service, inventory_service, sales_service, db_manager):
    cat_id = product_service.create_category("Cat")
    p2 = product_service.create_product("Med", cat_id, "box", 200, 10, True)

    date1 = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    date2 = (datetime.now() + timedelta(days=60)).strftime("%Y-%m-%d")

    inventory_service.record_opening_stock_medicine(p2, [
        {"batch_number": "B_LATE", "expiry_date": date2, "quantity": 10, "unit_cost": 100},
        {"batch_number": "B_EARLY", "expiry_date": date1, "quantity": 5, "unit_cost": 100}
    ])

    items = [{"product_id": p2, "quantity": 8, "unit_price": 200}]
    sale_id = sales_service.create_sale("S-003", items, 1600)
    
    conn = db_manager.get_connection()
    batches = conn.execute("SELECT batch_number, current_qty FROM medicine_batches WHERE product_id = ?", (p2,)).fetchall()
    for b in batches:
        if b['batch_number'] == "B_EARLY":
            assert b['current_qty'] == 0 # 5 consumed
        if b['batch_number'] == "B_LATE":
            assert b['current_qty'] == 7 # 3 consumed out of 10

def test_rejection_of_expired_medicine(product_service, inventory_service, sales_service):
    cat_id = product_service.create_category("Cat")
    p2 = product_service.create_product("Med", cat_id, "box", 200, 10, True)

    past_date = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d")
    inventory_service.record_opening_stock_medicine(p2, [
        {"batch_number": "B_EXP", "expiry_date": past_date, "quantity": 10, "unit_cost": 100}
    ])

    items = [{"product_id": p2, "quantity": 1, "unit_price": 200}]
    with pytest.raises(ValueError, match="Insufficient eligible batch stock"):
        sales_service.create_sale("S-EXP", items, 200)

def test_rejection_of_medicine_expiring_today(product_service, inventory_service, sales_service):
    cat_id = product_service.create_category("Cat")
    p2 = product_service.create_product("Med", cat_id, "box", 200, 10, True)

    today_date = datetime.now().strftime("%Y-%m-%d")
    inventory_service.record_opening_stock_medicine(p2, [
        {"batch_number": "B_TODAY", "expiry_date": today_date, "quantity": 10, "unit_cost": 100}
    ])

    items = [{"product_id": p2, "quantity": 1, "unit_price": 200}]
    with pytest.raises(ValueError, match="Insufficient eligible batch stock"):
        sales_service.create_sale("S-TODAY", items, 200)

def test_rejection_of_unknown_expiry(product_service, inventory_service, sales_service):
    cat_id = product_service.create_category("Cat")
    p2 = product_service.create_product("Med", cat_id, "box", 200, 10, True)

    inventory_service.record_opening_stock_medicine(p2, [
        {"batch_number": "B_UNK", "expiry_date": None, "quantity": 10, "unit_cost": 100}
    ])

    items = [{"product_id": p2, "quantity": 1, "unit_price": 200}]
    with pytest.raises(ValueError, match="Insufficient eligible batch stock"):
        sales_service.create_sale("S-UNK", items, 200)

def test_insufficient_stock_rejections(product_service, inventory_service, sales_service):
    cat_id = product_service.create_category("Cat")
    p1 = product_service.create_product("Merch", cat_id, "pcs", 100, 10, False)
    
    inventory_service.record_opening_stock_general(p1, 5, 50)

    # Ask for 6
    items = [{"product_id": p1, "quantity": 6, "unit_price": 100}]
    with pytest.raises(ValueError, match="Insufficient stock"):
        sales_service.create_sale("S-FAIL", items, 600)

def test_invalid_quantities_and_prices(product_service, inventory_service, sales_service):
    cat_id = product_service.create_category("Cat")
    p1 = product_service.create_product("Merch", cat_id, "pcs", 100, 10, False)
    inventory_service.record_opening_stock_general(p1, 10, 50)

    with pytest.raises(ValueError, match="Sale quantity must be greater than zero"):
        sales_service.create_sale("S-Q0", [{"product_id": p1, "quantity": 0, "unit_price": 100}], 0)
        
    with pytest.raises(ValueError, match="Unit price cannot be negative"):
        sales_service.create_sale("S-PNEG", [{"product_id": p1, "quantity": 1, "unit_price": -10}], 0)
        
    with pytest.raises(ValueError, match="Amount received is less than total sale amount"):
        sales_service.create_sale("S-SHORT", [{"product_id": p1, "quantity": 1, "unit_price": 100}], 50)

def test_inactive_product_rejection(product_service, inventory_service, sales_service):
    cat_id = product_service.create_category("Cat")
    p1 = product_service.create_product("Merch", cat_id, "pcs", 100, 10, False)
    inventory_service.record_opening_stock_general(p1, 10, 50)
    
    product_service.update_product(p1, "Merch", cat_id, "pcs", 100, 10, False)
    
    with pytest.raises(ValueError, match="is inactive and cannot be sold"):
        sales_service.create_sale("S-INAC", [{"product_id": p1, "quantity": 1, "unit_price": 100}], 100)

def test_wac_reaches_zero_on_full_sale(product_service, inventory_service, sales_service, db_manager):
    cat_id = product_service.create_category("Cat")
    p1 = product_service.create_product("Merch", cat_id, "pcs", 100, 10, False)
    
    inventory_service.record_opening_stock_general(p1, 3, 33) # total 99
    
    sales_service.create_sale("S-ZERO", [{"product_id": p1, "quantity": 3, "unit_price": 100}], 300)
    
    conn = db_manager.get_connection()
    prod = conn.execute("SELECT current_stock, inventory_value FROM products WHERE id = ?", (p1,)).fetchone()
    assert prod['current_stock'] == 0
    assert prod['inventory_value'] == 0

def test_cost_and_profit(product_service, inventory_service, sales_service):
    cat_id = product_service.create_category("Cat")
    p1 = product_service.create_product("Merch", cat_id, "pcs", 100, 10, False)
    inventory_service.record_opening_stock_general(p1, 10, 50) # WAC = 50
    
    sale_id = sales_service.create_sale("S-PROFIT", [{"product_id": p1, "quantity": 2, "unit_price": 120}], 240)
    sale = sales_service.get_sale(sale_id)
    
    # Cost of goods sold should be 2 * 50 = 100
    assert sale['items'][0]['total_cost'] == 100
    assert sale['items'][0]['line_total'] == 240
    # Gross profit = 240 - 100 = 140
    
    # Later purchase shouldn't affect historical sale cost
    # Let's verify in next test

def test_historical_cost_stable_after_purchase(product_service, inventory_service, purchase_service, supplier_service, sales_service):
    cat_id = product_service.create_category("Cat")
    p1 = product_service.create_product("Merch", cat_id, "pcs", 100, 10, False)
    inventory_service.record_opening_stock_general(p1, 10, 50)
    
    sale_id = sales_service.create_sale("S-STABLE", [{"product_id": p1, "quantity": 2, "unit_price": 120}], 240)
    
    s_id = supplier_service.create_supplier("Supp")
    purchase_service.create_purchase("P-LATER", s_id, "2026-01-01", [{"product_id": p1, "quantity": 10, "unit_cost": 200}])
    
    sale = sales_service.get_sale(sale_id)
    assert sale['items'][0]['total_cost'] == 100 # Should not change

def test_atomic_rollback_on_failure(product_service, inventory_service, sales_service, db_manager):
    cat_id = product_service.create_category("Cat")
    p1 = product_service.create_product("Merch", cat_id, "pcs", 100, 10, False)
    p2 = product_service.create_product("Merch 2", cat_id, "pcs", 100, 10, False)
    
    inventory_service.record_opening_stock_general(p1, 10, 50)
    inventory_service.record_opening_stock_general(p2, 2, 50)
    
    items = [
        {"product_id": p1, "quantity": 2, "unit_price": 100},
        {"product_id": p2, "quantity": 5, "unit_price": 100} # Will fail (only 2 in stock)
    ]
    
    with pytest.raises(ValueError, match="Insufficient stock"):
        sales_service.create_sale("S-ROLLBACK", items, 700)
        
    conn = db_manager.get_connection()
    # P1 stock should remain 10, not 8
    prod1 = conn.execute("SELECT current_stock FROM products WHERE id = ?", (p1,)).fetchone()
    assert prod1['current_stock'] == 10
    # No sale should be created
    assert conn.execute("SELECT COUNT(*) FROM sales").fetchone()[0] == 0

def test_sale_void_behavior(product_service, inventory_service, sales_service, db_manager):
    cat_id = product_service.create_category("Cat")
    p1 = product_service.create_product("Merch", cat_id, "pcs", 100, 10, False)
    inventory_service.record_opening_stock_general(p1, 10, 50)
    
    sale_id = sales_service.create_sale("S-VOID", [{"product_id": p1, "quantity": 3, "unit_price": 100}], 300)
    
    sales_service.void_sale(sale_id)
    
    conn = db_manager.get_connection()
    sale = conn.execute("SELECT status FROM sales WHERE id = ?", (sale_id,)).fetchone()
    assert sale['status'] == 'Voided'
    
    prod = conn.execute("SELECT current_stock, inventory_value FROM products WHERE id = ?", (p1,)).fetchone()
    assert prod['current_stock'] == 10
    assert prod['inventory_value'] == 500

    # Prevent double void
    with pytest.raises(ValueError, match="already voided"):
        sales_service.void_sale(sale_id)

def test_reconciliation_after_sale_and_void(product_service, inventory_service, sales_service, reconciliation_service):
    cat_id = product_service.create_category("Cat")
    p1 = product_service.create_product("Merch", cat_id, "pcs", 100, 10, False)
    inventory_service.record_opening_stock_general(p1, 10, 50)
    
    sale_id = sales_service.create_sale("S-REC", [{"product_id": p1, "quantity": 2, "unit_price": 100}], 200)
    
    rec_sale = reconciliation_service.reconcile_sale(sale_id)
    assert rec_sale['is_consistent'] is True
    
    rec_prod = reconciliation_service.reconcile_product_stock(p1)
    assert rec_prod['stock_match'] is True
    assert rec_prod['value_match'] is True
    
    sales_service.void_sale(sale_id)
    
    rec_sale_void = reconciliation_service.reconcile_sale(sale_id)
    assert rec_sale_void['is_consistent'] is True
    
    rec_prod_void = reconciliation_service.reconcile_product_stock(p1)
    assert rec_prod_void['stock_match'] is True
    assert rec_prod_void['value_match'] is True
    assert rec_prod_void['db_stock'] == 10

