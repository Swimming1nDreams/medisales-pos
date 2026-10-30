import pytest
from datetime import datetime, timedelta

def test_record_payment_updates_outstanding(db_manager, product_service, supplier_service, purchase_service):
    # Setup
    cat_id = product_service.create_category("Cat")
    p1 = product_service.create_product("Merch", cat_id, "pcs", 100, 10, False)
    
    s_id = supplier_service.create_supplier("Test Supp")
    
    # Create Purchase
    p_id = purchase_service.create_purchase("P-001", s_id, "2026-01-01", [{"product_id": p1, "quantity": 10, "unit_cost": 200}])
    
    conn = db_manager.get_connection()
    purch = conn.execute("SELECT total_amount, amount_paid FROM purchases WHERE id = ?", (p_id,)).fetchone()
    assert purch['total_amount'] == 2000
    assert purch['amount_paid'] == 0
    
    # Record Payment
    allocations = [{'purchase_id': p_id, 'allocated_amount': 1500}]
    pay_id = purchase_service.record_payment("PAY-001", s_id, "2026-01-02", 1500, allocations)
    
    # Verify Payment Updates
    purch_updated = conn.execute("SELECT total_amount, amount_paid FROM purchases WHERE id = ?", (p_id,)).fetchone()
    assert purch_updated['amount_paid'] == 1500
    
    payment = conn.execute("SELECT allocated_amount FROM supplier_payments WHERE id = ?", (pay_id,)).fetchone()
    assert payment['allocated_amount'] == 1500
    
    # Verify overpayment rejection
    allocations_2 = [{'purchase_id': p_id, 'allocated_amount': 600}] # Only 500 left
    with pytest.raises(ValueError, match="exceeds outstanding balance"):
        purchase_service.record_payment("PAY-002", s_id, "2026-01-03", 600, allocations_2)
