import pytest
from datetime import datetime, timedelta

def test_expense_creation_and_validation(expense_service):
    # 1. Creating valid expenses
    exp1 = expense_service.create_expense("Rent", "Monthly rent", 500000, "2026-10-10")
    assert exp1 > 0
    
    exp_data = expense_service.get_expense(exp1)
    assert exp_data['category'] == "Rent"
    assert exp_data['amount'] == 500000

    # 2. Rejecting invalid or non-positive amounts
    with pytest.raises(ValueError, match="must be a positive integer"):
        expense_service.create_expense("Rent", "", 0, "2026-10-10")
        
    with pytest.raises(ValueError, match="must be a positive integer"):
        expense_service.create_expense("Rent", "", -500, "2026-10-10")
        
    with pytest.raises(ValueError, match="Category is required"):
        expense_service.create_expense("", "", 500, "2026-10-10")

def test_retrieve_and_filter_expenses(expense_service):
    # 3. Retrieving expenses by date range and category
    expense_service.create_expense("Wages", "", 10000, "2026-10-01")
    expense_service.create_expense("Wages", "", 10000, "2026-10-02")
    expense_service.create_expense("Electricity", "", 5000, "2026-10-02")
    
    all_exp = expense_service.list_expenses()
    assert len(all_exp) >= 3
    
    wages_exp = expense_service.list_expenses(category="Wages")
    assert len(wages_exp) == 2
    
    oct2_exp = expense_service.list_expenses(start_date="2026-10-02", end_date="2026-10-02")
    assert len(oct2_exp) == 2

def test_expense_voiding_and_updating(expense_service):
    # Update is blocked, use void
    exp_id = expense_service.create_expense("Transport", "", 2000, "2026-10-10")
    
    with pytest.raises(ValueError, match="Updating expenses directly is not permitted"):
        expense_service.update_expense(exp_id, "Transport", "", 3000, "2026-10-10")
        
    expense_service.void_expense(exp_id)
    
    voided_exp = expense_service.get_expense(exp_id)
    assert voided_exp['status'] == 'Voided'
    
    # Excluded by default
    assert len(expense_service.list_expenses(category="Transport")) == 0
    # Included if requested
    assert len(expense_service.list_expenses(category="Transport", include_voided=True)) == 1

def test_financial_summary_totals(finance_service, expense_service, sales_service, product_service, inventory_service, db_manager):
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Reset/clear previous tests from affecting this by relying on unique products
    cat_id = product_service.create_category("Cat Fin")
    p1 = product_service.create_product("Merch Fin", cat_id, "pcs", 100, 10, False)
    
    # Stock 10 items @ 50 Kyat each
    inventory_service.record_opening_stock_general(p1, 10, 50) 
    
    # Sale: 2 items @ 100 = 200 Revenue, COGS = 100
    sales_service.create_sale("S-FIN1", [{"product_id": p1, "quantity": 2, "unit_price": 100}], 200)
    
    # Expense: 40 Kyat
    expense_service.create_expense("Wages", "", 40, today)
    
    # Check finance summary
    summary = finance_service.get_today_summary()
    
    # 4. Correct expense totals
    assert summary['operating_expenses'] >= 40
    
    # 5. Correct sales revenue totals
    assert summary['total_sales_revenue'] >= 200
    
    # 6. Correct COGS and gross profit
    # 200 revenue - 100 cogs = 100 gross profit
    assert summary['cost_of_goods_sold'] >= 100
    assert summary['gross_profit'] >= 100
    
    # 7. Correct net operating profit after expenses
    # 100 gross profit - 40 expenses = 60
    # Since other tests might run in the same DB, we check relative
    assert summary['net_operating_profit'] == summary['gross_profit'] - summary['operating_expenses']

def test_payments_and_purchases_not_double_counted(finance_service, purchase_service, supplier_service, product_service):
    date = "2026-11-01"
    s_id = supplier_service.create_supplier("Supp Fin")
    cat_id = product_service.create_category("Cat Fin2")
    p1 = product_service.create_product("Merch Fin2", cat_id, "pcs", 100, 10, False)
    
    purch_id = purchase_service.create_purchase("P-FIN1", s_id, date, [{"product_id": p1, "quantity": 10, "unit_cost": 50}])
    purchase_service.record_payment("PAY-FIN1", s_id, date, 500, [{"purchase_id": purch_id, "allocated_amount": 500}])
    
    summary = finance_service.get_daily_summary(date)
    
    # 8 & 9: purchases/payments are not in operating expenses
    assert summary['operating_expenses'] == 0
    assert summary['supplier_payments_made'] == 500
    assert summary['purchases_recorded'] == 500
    
def test_excluding_voided_transactions(finance_service, expense_service, sales_service, product_service, inventory_service):
    date = "2026-11-02"
    cat_id = product_service.create_category("Cat Fin3")
    p1 = product_service.create_product("Merch Fin3", cat_id, "pcs", 100, 10, False)
    inventory_service.record_opening_stock_general(p1, 10, 50)
    
    s_id = sales_service.create_sale("S-FIN-VOID", [{"product_id": p1, "quantity": 1, "unit_price": 100}], 100)
    # hack to change sale date for test
    with finance_service.db.transaction() as conn:
        conn.execute("UPDATE sales SET date_time = ? WHERE id = ?", (f"{date} 10:00:00", s_id))
    
    e_id = expense_service.create_expense("Wages", "", 50, date)
    
    # Void them
    sales_service.void_sale(s_id)
    expense_service.void_expense(e_id)
    
    summary = finance_service.get_daily_summary(date)
    
    # 10. Exclude voided sales and expenses
    assert summary['total_sales_revenue'] == 0
    assert summary['operating_expenses'] == 0

def test_daily_and_range_summaries_and_categories(finance_service, expense_service):
    expense_service.create_expense("Cat A", "", 10, "2026-12-01")
    expense_service.create_expense("Cat A", "", 20, "2026-12-02")
    expense_service.create_expense("Cat B", "", 30, "2026-12-02")
    
    sum_dec1 = finance_service.get_daily_summary("2026-12-01")
    assert sum_dec1['operating_expenses'] == 10
    
    sum_dec2 = finance_service.get_daily_summary("2026-12-02")
    assert sum_dec2['operating_expenses'] == 50
    assert sum_dec2['expenses_by_category']["Cat A"] == 20
    assert sum_dec2['expenses_by_category']["Cat B"] == 30
    
    sum_range = finance_service.get_summary("2026-12-01", "2026-12-02")
    assert sum_range['operating_expenses'] == 60
    assert sum_range['expenses_by_category']["Cat A"] == 30

def test_supplier_balance_and_reconciliation(finance_service, reconciliation_service, purchase_service, supplier_service, product_service):
    s_id = supplier_service.create_supplier("Supp Fin 4")
    cat_id = product_service.create_category("Cat Fin4")
    p1 = product_service.create_product("Merch Fin4", cat_id, "pcs", 100, 10, False)
    
    purch_id = purchase_service.create_purchase("P-BAL1", s_id, "2026-01-01", [{"product_id": p1, "quantity": 10, "unit_cost": 50}]) # total 500
    
    # Initial balance should include this 500
    summary = finance_service.get_today_summary()
    initial_bal = summary['total_outstanding_supplier_balances']
    assert initial_bal >= 500
    
    purchase_service.record_payment("PAY-BAL1", s_id, "2026-01-01", 200, [{"purchase_id": purch_id, "allocated_amount": 200}])
    
    # Balance should decrease by 200
    summary2 = finance_service.get_today_summary()
    assert summary2['total_outstanding_supplier_balances'] == initial_bal - 200
    
    # 14. Reconciliation
    rec = reconciliation_service.reconcile_finance_summary("2026-01-01", "2026-12-31")
    assert rec['is_consistent'] is True
