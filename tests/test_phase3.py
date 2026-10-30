import pytest
import sqlite3

def test_supplier_management(supplier_service):
    s_id = supplier_service.create_supplier("Supplier A", "12345")
    assert s_id > 0
    
    with pytest.raises(ValueError, match="already exists"):
        supplier_service.create_supplier("Supplier A")
        
    supplier_service.update_supplier(s_id, "Supplier A Updated", is_active=False)
    
    sups = supplier_service.list_suppliers(include_inactive=False)
    assert len(sups) == 0
    
    sups_all = supplier_service.list_suppliers(include_inactive=True)
    assert len(sups_all) == 1
    assert sups_all[0]['name'] == "Supplier A Updated"

def test_purchase_creation_and_receipt(product_service, supplier_service, purchase_service, db_manager, reconciliation_service):
    s_id = supplier_service.create_supplier("Supp A")
    cat_id = product_service.create_category("Cat")
    p1 = product_service.create_product("Merch 1", cat_id, "box", 100, 10, False)
    p2 = product_service.create_product("Med 1", cat_id, "box", 200, 10, True)

    items = [
        {"product_id": p1, "quantity": 10, "unit_cost": 50},
        {"product_id": p2, "quantity": 20, "unit_cost": 60, "batch_number": "B1", "expiry_date": "2030-01-01"}
    ]
    
    purch_id = purchase_service.create_purchase("REF-001", s_id, "2026-01-01", items)
    
    # Check duplicate ref
    with pytest.raises(ValueError, match="already exists"):
        purchase_service.create_purchase("REF-001", s_id, "2026-01-01", items)

    # Reconciliation check
    rec_purch = reconciliation_service.reconcile_purchase(purch_id)
    assert rec_purch['is_consistent'] is True
    
    rec_merch = reconciliation_service.reconcile_product_stock(p1)
    assert rec_merch['db_stock'] == 10
    assert rec_merch['db_value'] == 500
    assert rec_merch['stock_match'] is True
    
    rec_med = reconciliation_service.reconcile_medicine_batches(p2)
    assert rec_med['db_stock'] == 20
    assert rec_med['db_value'] == 1200
    assert rec_med['stock_match'] is True
    assert rec_med['value_match'] is True

def test_supplier_payment_allocations(supplier_service, purchase_service, db_manager, product_service, reconciliation_service):
    s_id = supplier_service.create_supplier("Supp B")
    s2_id = supplier_service.create_supplier("Supp C")
    cat_id = product_service.create_category("Cat")
    p1 = product_service.create_product("Merch", cat_id, "pcs", 100, 10, False)
    
    # Purchase 1 for Supp B (Cost 500)
    p_id1 = purchase_service.create_purchase("P1", s_id, "2026-01-01", [{"product_id": p1, "quantity": 10, "unit_cost": 50}])
    # Purchase 2 for Supp B (Cost 1000)
    p_id2 = purchase_service.create_purchase("P2", s_id, "2026-01-02", [{"product_id": p1, "quantity": 20, "unit_cost": 50}])
    # Purchase 3 for Supp C (Cost 500)
    p_id3 = purchase_service.create_purchase("P3", s2_id, "2026-01-02", [{"product_id": p1, "quantity": 10, "unit_cost": 50}])

    # Pay Supp B 1000. Allocate 500 to P1, 500 to P2
    pay_id = purchase_service.record_payment("PAY-1", s_id, "2026-01-03", 1000, [
        {"purchase_id": p_id1, "allocated_amount": 500},
        {"purchase_id": p_id2, "allocated_amount": 500}
    ])

    rec = reconciliation_service.reconcile_supplier_payment(pay_id)
    assert rec['is_consistent'] is True
    assert rec['db_allocated'] == 1000
    
    conn = db_manager.get_connection()
    purch1 = conn.execute("SELECT amount_paid FROM purchases WHERE id = ?", (p_id1,)).fetchone()
    assert purch1['amount_paid'] == 500

    # Over-allocate purchase balance
    with pytest.raises(ValueError, match="exceeds outstanding balance"):
        purchase_service.record_payment("PAY-2", s_id, "2026-01-04", 600, [
            {"purchase_id": p_id2, "allocated_amount": 600} # P2 only has 500 outstanding
        ])

    # Cross-supplier allocation
    with pytest.raises(ValueError, match="different supplier"):
        purchase_service.record_payment("PAY-3", s_id, "2026-01-04", 500, [
            {"purchase_id": p_id3, "allocated_amount": 500}
        ])

def test_purchase_voiding_safeguards(product_service, supplier_service, purchase_service, db_manager):
    s_id = supplier_service.create_supplier("Supp D")
    cat_id = product_service.create_category("Cat")
    p1 = product_service.create_product("Merch", cat_id, "pcs", 100, 10, False)
    
    purch_id = purchase_service.create_purchase("P-VOID", s_id, "2026-01-01", [{"product_id": p1, "quantity": 10, "unit_cost": 50}])
    
    # Void successfully
    purchase_service.void_purchase_correction(purch_id)
    
    conn = db_manager.get_connection()
    purch = conn.execute("SELECT status FROM purchases WHERE id = ?", (purch_id,)).fetchone()
    assert purch['status'] == 'Voided'
    
    prod = conn.execute("SELECT current_stock, inventory_value FROM products WHERE id = ?", (p1,)).fetchone()
    assert prod['current_stock'] == 0
    assert prod['inventory_value'] == 0
    
    # Try voiding again
    with pytest.raises(ValueError, match="already voided"):
        purchase_service.void_purchase_correction(purch_id)

def test_purchase_voiding_fails_if_paid(product_service, supplier_service, purchase_service):
    s_id = supplier_service.create_supplier("Supp E")
    cat_id = product_service.create_category("Cat")
    p1 = product_service.create_product("Merch", cat_id, "pcs", 100, 10, False)
    
    purch_id = purchase_service.create_purchase("P-VOID2", s_id, "2026-01-01", [{"product_id": p1, "quantity": 10, "unit_cost": 50}])
    
    # Pay it
    purchase_service.record_payment("PAY-VOID", s_id, "2026-01-01", 500, [{"purchase_id": purch_id, "allocated_amount": 500}])
    
    # Try voiding
    with pytest.raises(ValueError, match="existing payment allocations"):
        purchase_service.void_purchase_correction(purch_id)

def test_purchase_wac_updates(product_service, supplier_service, purchase_service, db_manager):
    s_id = supplier_service.create_supplier("Supp F")
    cat_id = product_service.create_category("Cat")
    p1 = product_service.create_product("Merch", cat_id, "pcs", 100, 10, False)
    
    # 1st Purchase: 10 qty @ 50 = 500
    purchase_service.create_purchase("P-WAC1", s_id, "2026-01-01", [{"product_id": p1, "quantity": 10, "unit_cost": 50}])
    
    # 2nd Purchase: 10 qty @ 70 = 700
    purchase_service.create_purchase("P-WAC2", s_id, "2026-01-02", [{"product_id": p1, "quantity": 10, "unit_cost": 70}])
    
    conn = db_manager.get_connection()
    prod = conn.execute("SELECT current_stock, inventory_value FROM products WHERE id = ?", (p1,)).fetchone()
    assert prod['current_stock'] == 20
    assert prod['inventory_value'] == 1200 # WAC is 60 now
