import pytest
from datetime import datetime, timedelta

def test_dashboard_with_transactions(dashboard_service, finance_service, sales_service, expense_service, product_service, inventory_service, db_manager):
    today = datetime.now().strftime("%Y-%m-%d")
    
    cat_id = product_service.create_category("Cat Dash 1")
    p1 = product_service.create_product("Merch Dash 1", cat_id, "pcs", 200, 5, False)
    inventory_service.record_opening_stock_general(p1, 20, 100)
    
    sales_service.create_sale("S-DASH1", [{"product_id": p1, "quantity": 5, "unit_price": 200}], 1000)
    expense_service.create_expense("Wages", "", 200, today)
    
    summary = dashboard_service.get_dashboard_summary(today)
    assert summary['number_of_completed_sales'] >= 1
    assert summary['total_sales_revenue'] >= 1000
    assert summary['cost_of_goods_sold'] >= 500
    assert summary['operating_expenses'] >= 200
    assert summary['total_inventory_quantity'] > 0
    assert summary['total_inventory_value'] > 0
    assert summary['active_products_count'] >= 1

def test_dashboard_without_transactions(dashboard_service, db_manager):
    # Use a future date to ensure no transactions
    future = (datetime.now() + timedelta(days=3650)).strftime("%Y-%m-%d")
    summary = dashboard_service.get_dashboard_summary(future)
    assert summary['number_of_completed_sales'] == 0
    assert summary['total_sales_revenue'] == 0
    assert summary['operating_expenses'] == 0
    
    # Inventory snapshots are not bound to the selected date
    assert summary['active_products_count'] >= 0

def test_daily_sales_summaries_and_range_filtering(report_service, sales_service, product_service, inventory_service):
    date1 = "2026-08-01"
    date2 = "2026-08-02"
    
    cat_id = product_service.create_category("Cat Rep 1")
    p1 = product_service.create_product("Merch Rep 1", cat_id, "pcs", 100, 10, False)
    inventory_service.record_opening_stock_general(p1, 50, 50)
    
    s1 = sales_service.create_sale("S-REP1", [{"product_id": p1, "quantity": 1, "unit_price": 100}], 100)
    s2 = sales_service.create_sale("S-REP2", [{"product_id": p1, "quantity": 2, "unit_price": 100}], 200)
    
    with report_service.db.transaction() as conn:
        conn.execute("UPDATE sales SET date_time = ? WHERE id = ?", (f"{date1} 10:00:00", s1))
        conn.execute("UPDATE sales SET date_time = ? WHERE id = ?", (f"{date2} 10:00:00", s2))
    
    # Arbitrary date range
    range_sum = report_service.get_sales_summary("2026-08-01", "2026-08-02")
    assert range_sum['sales_count'] == 2
    assert range_sum['total_revenue'] == 300
    
    # Daily sales totals
    daily = report_service.get_daily_sales_totals("2026-08-01", "2026-08-02")
    assert len(daily) == 2
    assert daily[0]['sale_date'] == "2026-08-01"
    assert daily[0]['total_revenue'] == 100

def test_product_sales_and_void_exclusion(report_service, sales_service, product_service, inventory_service):
    date = "2026-09-01"
    cat_id = product_service.create_category("Cat Rep 2")
    p1 = product_service.create_product("Merch Rep 2", cat_id, "pcs", 100, 10, False)
    inventory_service.record_opening_stock_general(p1, 50, 50)
    
    s1 = sales_service.create_sale("S-REP3", [{"product_id": p1, "quantity": 3, "unit_price": 100}], 300)
    s2 = sales_service.create_sale("S-REP4-VOID", [{"product_id": p1, "quantity": 5, "unit_price": 100}], 500)
    
    with report_service.db.transaction() as conn:
        conn.execute("UPDATE sales SET date_time = ? WHERE id IN (?, ?)", (f"{date} 10:00:00", s1, s2))
    
    sales_service.void_sale(s2)
    
    by_prod = report_service.get_sales_by_product("2026-09-01", "2026-09-01")
    # find p1
    prod_report = next((r for r in by_prod if r['product_id'] == p1), None)
    assert prod_report is not None
    assert prod_report['total_quantity'] == 3 # excluded the voided 5
    assert prod_report['total_revenue'] == 300
    assert prod_report['total_cogs'] == 150
    assert prod_report['gross_profit'] == 150

def test_inventory_and_medicine_reports(report_service, product_service, inventory_service):
    cat_id = product_service.create_category("Med Cat 1")
    med1 = product_service.create_product("Med Rep 1", cat_id, "box", 500, 5, True)
    
    today = datetime.now().strftime("%Y-%m-%d")
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    soon = (datetime.now() + timedelta(days=10)).strftime("%Y-%m-%d")
    
    batches = [
        {"batch_number": "B1", "quantity": 10, "unit_cost": 200, "expiry_date": yesterday}, # Expired
        {"batch_number": "B2", "quantity": 10, "unit_cost": 200, "expiry_date": soon}, # Expiring soon
        {"batch_number": "B3", "quantity": 10, "unit_cost": 200, "expiry_date": ""} # Unknown expiry
    ]
    inventory_service.record_opening_stock_medicine(med1, batches)
    
    expired = report_service.get_medicine_batches_report('expired')
    assert any(b['batch_number'] == 'B1' and b['product_id'] == med1 for b in expired)
    
    soon_rep = report_service.get_medicine_batches_report('expiring_soon', 30)
    assert any(b['batch_number'] == 'B2' and b['product_id'] == med1 for b in soon_rep)
    
    unk = report_service.get_medicine_batches_report('unknown_expiry')
    assert any(b['batch_number'] == 'B3' and b['product_id'] == med1 for b in unk)
    
    # Movement history
    hist = report_service.get_inventory_movement_history(med1, "2000-01-01", "2100-01-01")
    assert len(hist) >= 1
    # Find the specific movement to ensure it aggregated all 3 batches (30 items)
    assert any(h['quantity_change'] == 30 for h in hist)

def test_supplier_and_expense_reports(report_service, purchase_service, supplier_service, product_service, expense_service):
    s_id = supplier_service.create_supplier("Supp Rep 1")
    cat_id = product_service.create_category("Cat Rep 3")
    p1 = product_service.create_product("Merch Rep 3", cat_id, "pcs", 100, 10, False)
    
    purch_id = purchase_service.create_purchase("P-REP1", s_id, "2026-10-01", [{"product_id": p1, "quantity": 10, "unit_cost": 50}])
    # Payment leaves outstanding balance 200, unallocated 50
    pay_id = purchase_service.record_payment("PAY-REP1", s_id, "2026-10-02", 350, [{"purchase_id": purch_id, "allocated_amount": 300}])
    
    bals = report_service.get_supplier_balances()
    supp_bal = next((b for b in bals if b['supplier_id'] == s_id), None)
    assert supp_bal is not None
    assert supp_bal['total_purchased'] == 500
    assert supp_bal['total_paid'] == 300
    assert supp_bal['outstanding_balance'] == 200
    
    pay_bals = report_service.get_supplier_payment_balances()
    pay_bal = next((p for p in pay_bals if p['payment_id'] == pay_id), None)
    assert pay_bal is not None
    assert pay_bal['unallocated_balance'] == 50
    
    # Expenses
    e1 = expense_service.create_expense("Transport", "", 100, "2026-11-01")
    e2 = expense_service.create_expense("Transport", "", 200, "2026-11-01")
    e3 = expense_service.create_expense("Misc", "", 50, "2026-11-01")
    expense_service.void_expense(e3)
    
    cat_rep = report_service.get_expenses_by_category("2026-11-01", "2026-11-01")
    assert any(r['category'] == 'Transport' and r['total_amount'] == 300 for r in cat_rep)
    assert not any(r['category'] == 'Misc' for r in cat_rep)
    
    voids = report_service.get_voided_expenses("2026-11-01", "2026-11-01")
    assert any(v['id'] == e3 for v in voids)

def test_empty_datasets(report_service):
    # Empty date range
    range_sum = report_service.get_sales_summary("1990-01-01", "1990-01-02")
    assert range_sum['sales_count'] == 0
    assert range_sum['total_revenue'] == 0
    assert range_sum['total_cogs'] == 0
    assert range_sum['gross_profit'] == 0
    
    assert report_service.get_daily_sales_totals("1990-01-01", "1990-01-02") == []
    assert report_service.get_sales_by_product("1990-01-01", "1990-01-02") == []
    assert report_service.get_sales_by_category("1990-01-01", "1990-01-02") == []
    assert report_service.get_purchases("1990-01-01", "1990-01-02") == []
    assert report_service.get_expenses_by_category("1990-01-01", "1990-01-02") == []
    
def test_consistency_with_finance_service(report_service, finance_service):
    f_sum = finance_service.get_summary("2026-08-01", "2026-08-02")
    r_sum = report_service.get_sales_summary("2026-08-01", "2026-08-02")
    
    assert f_sum['total_sales_revenue'] == r_sum['total_revenue']
    assert f_sum['cost_of_goods_sold'] == r_sum['total_cogs']
    assert f_sum['gross_profit'] == r_sum['gross_profit']
