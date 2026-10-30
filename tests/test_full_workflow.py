import pytest
import json
from datetime import datetime, date, timedelta
from src.ui_web.bridge import FrontendBridge
from src.database.connection import DatabaseManager
from src.database.migrations_manager import MigrationsManager
from src.services.product_service import ProductService
from src.services.inventory_service import InventoryService
from src.services.sales_service import SalesService
from src.services.supplier_service import SupplierService
from src.services.purchase_service import PurchaseService
from src.services.expense_service import ExpenseService
from src.services.finance_service import FinanceService
from src.services.dashboard_service import DashboardService
from src.services.report_service import ReportService
from src.services.reconciliation_service import ReconciliationService

@pytest.fixture
def workflow_bridge(tmp_path):
    """Provides a fresh, isolated disk-based database for full workflow verification."""
    db_file = tmp_path / "test_workflow.db"
    db_manager = DatabaseManager(str(db_file))
    mig = MigrationsManager(db_manager)
    mig.apply_migrations()

    inv = InventoryService(db_manager)
    prod = ProductService(db_manager)
    sales = SalesService(db_manager, inv)
    supp = SupplierService(db_manager)
    purch = PurchaseService(db_manager)
    exp = ExpenseService(db_manager)
    fin = FinanceService(db_manager)
    dash = DashboardService(db_manager, fin)
    rep = ReportService(db_manager)
    recon = ReconciliationService(db_manager)

    services = {
        'db_manager': db_manager,
        'inventory_service': inv,
        'product_service': prod,
        'sales_service': sales,
        'supplier_service': supp,
        'purchase_service': purch,
        'expense_service': exp,
        'finance_service': fin,
        'dashboard_service': dash,
        'report_service': rep,
        'reconciliation_service': recon
    }
    bridge = FrontendBridge(services)
    yield bridge, services, db_manager
    db_manager.close()

def test_complete_business_workflow_14_steps(workflow_bridge):
    """
    TASK 1 — Verification of the complete 14-step business workflow
    exercised through bridge and service interfaces on an isolated test database.
    """
    bridge, services, db_manager = workflow_bridge

    # -------------------------------------------------------------------------
    # 1. Create a medicine product and a general merchandise product.
    # -------------------------------------------------------------------------
    cat_med_res = json.loads(bridge.create_category("Medicines"))
    assert cat_med_res['status'] == 'success'
    med_cat_id = cat_med_res['data']['category_id']

    cat_gen_res = json.loads(bridge.create_category("General Goods"))
    assert cat_gen_res['status'] == 'success'
    gen_cat_id = cat_gen_res['data']['category_id']

    # Create Medicine Product
    p_med_res = json.loads(bridge.create_product(
        "Paracetamol 500mg", med_cat_id, "strip", 1000, 5, True
    ))
    assert p_med_res['status'] == 'success'
    med_id = p_med_res['data']['product_id']

    # Create General Merchandise Product
    p_gen_res = json.loads(bridge.create_product(
        "Shampoo Bottle 200ml", gen_cat_id, "bottle", 3500, 2, False
    ))
    assert p_gen_res['status'] == 'success'
    gen_id = p_gen_res['data']['product_id']

    # Verify products listed with category names
    products = json.loads(bridge.list_products())['data']
    assert len(products) == 2
    med_prod = next(p for p in products if p['id'] == med_id)
    gen_prod = next(p for p in products if p['id'] == gen_id)
    assert med_prod['category_name'] == "Medicines"
    assert gen_prod['category_name'] == "General Goods"
    assert med_prod['is_medicine'] == 1
    assert gen_prod['is_medicine'] == 0

    # -------------------------------------------------------------------------
    # 2. Create a supplier.
    # -------------------------------------------------------------------------
    supp_res = json.loads(bridge.create_supplier("Apex Myanmar Distribution", "0912345678", "Yangon, Myanmar"))
    assert supp_res['status'] == 'success'
    supplier_id = supp_res['data']['supplier_id']

    # -------------------------------------------------------------------------
    # 3. Record purchases for both products.
    # -------------------------------------------------------------------------
    # Purchase 1 (PO-2026-001):
    # - Shampoo: 10 units @ 2000 Ks = 20,000 Ks
    # - Paracetamol (Batch A1, expires later: 2027-06-01): 20 units @ 600 Ks = 12,000 Ks
    # Total purchase 1: 32,000 Ks
    purchase_1_items = [
        {
            "product_id": gen_id,
            "quantity": 10,
            "unit_cost": 2000,
            "batch_number": None,
            "expiry_date": None
        },
        {
            "product_id": med_id,
            "quantity": 20,
            "unit_cost": 600,
            "batch_number": "BATCH-A1",
            "expiry_date": "2027-06-01"
        }
    ]
    purch_1_res = json.loads(bridge.create_purchase(
        "PO-2026-001", supplier_id, "2026-10-01", json.dumps(purchase_1_items)
    ))
    assert purch_1_res['status'] == 'success'
    purchase_1_id = purch_1_res['data']['purchase_id']

    # Purchase 2 (PO-2026-002):
    # - Paracetamol (Batch B2, expires sooner: 2026-12-01): 15 units @ 700 Ks = 10,500 Ks
    purchase_2_items = [
        {
            "product_id": med_id,
            "quantity": 15,
            "unit_cost": 700,
            "batch_number": "BATCH-B2",
            "expiry_date": "2026-12-01"
        }
    ]
    purch_2_res = json.loads(bridge.create_purchase(
        "PO-2026-002", supplier_id, "2026-10-02", json.dumps(purchase_2_items)
    ))
    assert purch_2_res['status'] == 'success'
    purchase_2_id = purch_2_res['data']['purchase_id']

    # -------------------------------------------------------------------------
    # 4. Verify medicine batch numbers, expiry dates, stock quantities, and costs.
    # -------------------------------------------------------------------------
    batches = json.loads(bridge.get_sellable_medicine_batches(med_id))['data']
    assert len(batches) == 2
    # Verify FEFO ordering (earliest expiry first: BATCH-B2 then BATCH-A1)
    assert batches[0]['batch_number'] == "BATCH-B2"
    assert batches[0]['expiry_date'] == "2026-12-01"
    assert batches[0]['current_qty'] == 15
    assert batches[0]['unit_cost'] == 700

    assert batches[1]['batch_number'] == "BATCH-A1"
    assert batches[1]['expiry_date'] == "2027-06-01"
    assert batches[1]['current_qty'] == 20
    assert batches[1]['unit_cost'] == 600

    # Verify overall stock records
    stock_list = json.loads(bridge.get_current_stock())['data']
    med_stock = next(s for s in stock_list if s['id'] == med_id)
    gen_stock = next(s for s in stock_list if s['id'] == gen_id)
    assert med_stock['current_stock'] == 35 # 20 + 15
    assert gen_stock['current_stock'] == 10
    assert med_stock['category_name'] == "Medicines"
    assert gen_stock['category_name'] == "General Goods"

    # Verify initial supplier balance
    balances = json.loads(bridge.get_supplier_balances())['data']
    apex_bal = next(b for b in balances if b['supplier_id'] == supplier_id)
    assert apex_bal['total_purchased'] == 42500
    assert apex_bal['total_paid'] == 0
    assert apex_bal['outstanding_balance'] == 42500

    # -------------------------------------------------------------------------
    # 5. Record supplier payments and verify outstanding balances.
    # -------------------------------------------------------------------------
    allocations = [{"purchase_id": purchase_1_id, "allocated_amount": 15000}]
    pay_res = json.loads(bridge.record_payment(
        "PAY-2026-001", supplier_id, "2026-10-05", 15000, json.dumps(allocations), "Partial payment"
    ))
    assert pay_res['status'] == 'success'

    # Verify updated balance: 42,500 - 15,000 = 27,500
    balances_after = json.loads(bridge.get_supplier_balances())['data']
    apex_after = next(b for b in balances_after if b['supplier_id'] == supplier_id)
    assert apex_after['total_paid'] == 15000
    assert apex_after['outstanding_balance'] == 27500

    # -------------------------------------------------------------------------
    # 6. Sell general merchandise and verify stock reduction and COGS.
    # -------------------------------------------------------------------------
    # Sell 3 bottles of Shampoo @ 3,500 Ks = 10,500 Ks. Paid 15,000 Ks.
    sale_gen_items = [{"product_id": gen_id, "quantity": 3, "unit_price": 3500}]
    sale_gen_res = json.loads(bridge.create_sale(
        "SALE-SHAMPOO-01", json.dumps(sale_gen_items), 15000
    ))
    assert sale_gen_res['status'] == 'success'
    gen_sale_id = sale_gen_res['data']['sale_id']

    # Stock reduction: 10 - 3 = 7
    stock_after_sale = json.loads(bridge.get_current_stock())['data']
    gen_stock_after = next(s for s in stock_after_sale if s['id'] == gen_id)
    assert gen_stock_after['current_stock'] == 7

    # Verify COGS for this sale item: 3 * 2000 Ks = 6000 Ks
    conn = db_manager.get_connection()
    si_row = conn.execute("SELECT total_cost, line_total FROM sale_items WHERE sale_id = ?", (gen_sale_id,)).fetchone()
    assert si_row['total_cost'] == 6000
    assert si_row['line_total'] == 10500

    # -------------------------------------------------------------------------
    # 7. Sell medicine and verify FEFO batch selection.
    # -------------------------------------------------------------------------
    # We sell 18 strips of Paracetamol.
    # Expected FEFO:
    # 15 strips from BATCH-B2 (cost: 15 * 700 = 10,500)
    # 3 strips from BATCH-A1 (cost: 3 * 600 = 1,800)
    # Total COGS: 12,300 Ks. Total revenue: 18 * 1000 = 18,000 Ks.
    sale_med_items = [{"product_id": med_id, "quantity": 18, "unit_price": 1000}]
    sale_med_res = json.loads(bridge.create_sale(
        "SALE-MED-01", json.dumps(sale_med_items), 18000
    ))
    assert sale_med_res['status'] == 'success'
    med_sale_id = sale_med_res['data']['sale_id']

    # Verify batch stocks after sale:
    batches_after_med = json.loads(bridge.get_sellable_medicine_batches(med_id))['data']
    # BATCH-B2 is completely exhausted (current_qty = 0), so only BATCH-A1 remains sellable
    assert len(batches_after_med) == 1
    assert batches_after_med[0]['batch_number'] == "BATCH-A1"
    assert batches_after_med[0]['current_qty'] == 17 # 20 - 3 = 17

    # Verify medicine total stock: 35 - 18 = 17
    stock_med_after = next(s for s in json.loads(bridge.get_current_stock())['data'] if s['id'] == med_id)
    assert stock_med_after['current_stock'] == 17

    # Verify exact medicine sale item total cost
    med_si = conn.execute("SELECT total_cost, line_total FROM sale_items WHERE sale_id = ?", (med_sale_id,)).fetchone()
    assert med_si['total_cost'] == 12300 # 10500 + 1800
    assert med_si['line_total'] == 18000

    # -------------------------------------------------------------------------
    # 8. Attempt to sell expired medicine, medicine expiring today, and
    #    medicine with unknown expiry. All must be rejected.
    # -------------------------------------------------------------------------
    # Create test medicine product for expiry verification
    p_exp_res = json.loads(bridge.create_product("Expiry Test Product", med_cat_id, "box", 2000, 1, True))
    exp_test_id = p_exp_res['data']['product_id']

    today_str = datetime.now().strftime("%Y-%m-%d")
    past_date_str = "2022-01-01"

    # Add 3 batches: Expired, Expiring Today, and Unknown Expiry
    expiry_batches_items = [
        {"product_id": exp_test_id, "quantity": 10, "unit_cost": 500, "batch_number": "EXP-PAST", "expiry_date": past_date_str},
        {"product_id": exp_test_id, "quantity": 10, "unit_cost": 500, "batch_number": "EXP-TODAY", "expiry_date": today_str},
        {"product_id": exp_test_id, "quantity": 10, "unit_cost": 500, "batch_number": "EXP-UNKNOWN", "expiry_date": None}
    ]
    json.loads(bridge.create_purchase("PO-EXP-TEST", supplier_id, "2026-10-06", json.dumps(expiry_batches_items)))

    # Verify sellable batches list excludes all three
    sellable_exp = json.loads(bridge.get_sellable_medicine_batches(exp_test_id))['data']
    assert len(sellable_exp) == 0, f"Expected 0 sellable batches, found: {sellable_exp}"

    # Attempt to sell: Must be rejected
    fail_sale_res = json.loads(bridge.create_sale(
        "SALE-EXP-FAIL", json.dumps([{"product_id": exp_test_id, "quantity": 1, "unit_price": 2000}]), 2000
    ))
    assert fail_sale_res['status'] == 'error'
    assert 'insufficient eligible batch stock' in fail_sale_res['message'].lower()

    # -------------------------------------------------------------------------
    # 9. Attempt an out-of-stock sale and confirm that no partial transaction is committed.
    # -------------------------------------------------------------------------
    initial_sales_count = conn.execute("SELECT count(*) FROM sales").fetchone()[0]
    initial_shampoo_stock = next(s for s in json.loads(bridge.get_current_stock())['data'] if s['id'] == gen_id)['current_stock']

    # Attempt multi-item sale where item 1 has stock (1 shampoo) but item 2 exceeds stock (999 shampoo)
    invalid_sale_items = [
        {"product_id": gen_id, "quantity": 1, "unit_price": 3500},
        {"product_id": gen_id, "quantity": 999, "unit_price": 3500}
    ]
    out_of_stock_res = json.loads(bridge.create_sale(
        "SALE-OOS-FAIL", json.dumps(invalid_sale_items), 4000000
    ))
    assert out_of_stock_res['status'] == 'error'

    # Confirm no partial transaction was committed
    final_sales_count = conn.execute("SELECT count(*) FROM sales").fetchone()[0]
    assert final_sales_count == initial_sales_count

    shampoo_stock_after_fail = next(s for s in json.loads(bridge.get_current_stock())['data'] if s['id'] == gen_id)['current_stock']
    assert shampoo_stock_after_fail == initial_shampoo_stock

    # -------------------------------------------------------------------------
    # 10. Void a sale and verify stock restoration and immutable movement history.
    # -------------------------------------------------------------------------
    # Void the shampoo sale (gen_sale_id)
    void_res = json.loads(bridge.void_sale(gen_sale_id, "Customer returned unopened shampoo"))
    assert void_res['status'] == 'success'

    # Verify stock restored: was 7, should be back to 10
    restored_shampoo = next(s for s in json.loads(bridge.get_current_stock())['data'] if s['id'] == gen_id)
    assert restored_shampoo['current_stock'] == 10

    # Verify inventory movement recorded
    movs = conn.execute(
        "SELECT movement_type, reference_type, quantity_change FROM inventory_movements WHERE product_id = ? AND reference_id = ?",
        (gen_id, gen_sale_id)
    ).fetchall()
    # Should have Out (Sale) and In (SaleVoid)
    mov_types = [(m['movement_type'], m['reference_type'], m['quantity_change']) for m in movs]
    assert ('Out', 'Sale', 3) in mov_types
    assert ('In', 'SaleVoid', 3) in mov_types

    # Verify immutability trigger prevents tampering with inventory_movements
    with pytest.raises(Exception):
        conn.execute("UPDATE inventory_movements SET quantity_change = 999 WHERE product_id = ?", (gen_id,))
    conn.rollback()
    with pytest.raises(Exception):
        conn.execute("DELETE FROM inventory_movements WHERE product_id = ?", (gen_id,))
    conn.rollback()

    # -------------------------------------------------------------------------
    # 11. Record and void an operating expense.
    # -------------------------------------------------------------------------
    exp_res = json.loads(bridge.record_expense(
        "2026-10-08", "Electricity", 5000, "Generator diesel fuel"
    ))
    assert exp_res['status'] == 'success', exp_res.get('message')
    diesel_exp_id = exp_res['data']['expense_id']

    # Void the electricity expense
    void_exp_res = json.loads(bridge.void_expense(diesel_exp_id, "Entered under wrong date"))
    assert void_exp_res['status'] == 'success'

    # Verify status is Voided
    expenses = json.loads(bridge.get_expenses("2026-10-01", "2026-10-31"))['data']
    diesel_exp = next(e for e in expenses if e['id'] == diesel_exp_id)
    assert diesel_exp['status'] == 'Voided'

    # Record a valid, active operating expense
    exp_active_res = json.loads(bridge.record_expense(
        "2026-10-09", "Staff Refreshment", 3000, "Coffee and snacks"
    ))
    assert exp_active_res['status'] == 'success'

    # Verify expense cannot be deleted (trigger immutability check)
    with pytest.raises(Exception):
        conn.execute("DELETE FROM expenses WHERE id = ?", (diesel_exp_id,))
    conn.rollback()

    # -------------------------------------------------------------------------
    # 12. Verify that supplier payments and stock purchases are not
    #     incorrectly counted as operating expenses.
    # -------------------------------------------------------------------------
    today_dash = json.loads(bridge.get_dashboard_summary())['data']
    # Supplier payments: 15,000 Ks. Stock purchases: 42,500 + PO-EXP-TEST.
    # The active operating expense is strictly 3,000 Ks.
    fin_summary = services['finance_service'].get_summary("2026-10-01", "2026-10-31")
    assert fin_summary['operating_expenses'] == 3000
    assert fin_summary['supplier_payments_made'] == 15000
    assert fin_summary['purchases_recorded'] >= 42500
    assert fin_summary['operating_expenses'] != fin_summary['supplier_payments_made']
    assert fin_summary['operating_expenses'] != fin_summary['purchases_recorded']

    # -------------------------------------------------------------------------
    # 13. Verify gross profit, operating expenses, and net operating profit
    #     against manually calculated expected values.
    # -------------------------------------------------------------------------
    # Only active completed sale is med_sale_id:
    # Revenue: 18,000 Ks
    # COGS: 12,300 Ks
    # Manually expected Gross Profit: 18,000 - 12,300 = 5,700 Ks
    # Manually expected Operating Expenses: 3,000 Ks
    # Manually expected Net Operating Profit: 5,700 - 3,000 = 2,700 Ks
    sales_rep = json.loads(bridge.get_sales_summary("2026-10-01", "2026-10-31"))['data']
    assert sales_rep['total_revenue'] == 18000
    assert sales_rep['total_cogs'] == 12300
    assert sales_rep['gross_profit'] == 5700

    assert fin_summary['total_sales_revenue'] == 18000
    assert fin_summary['cost_of_goods_sold'] == 12300
    assert fin_summary['gross_profit'] == 5700
    assert fin_summary['operating_expenses'] == 3000
    assert fin_summary['net_operating_profit'] == 2700

    # -------------------------------------------------------------------------
    # 14. Verify that duplicate submissions or repeated button clicks
    #     cannot create duplicate sales, purchases, payments, or expenses.
    # -------------------------------------------------------------------------
    # Resubmit sale with same reference -> must reject duplicate
    dup_sale = json.loads(bridge.create_sale("SALE-MED-01", json.dumps(sale_med_items), 18000))
    assert dup_sale['status'] == 'error'
    assert 'already exists' in dup_sale['message'].lower()

    # Resubmit purchase with same reference -> must reject duplicate
    dup_purch = json.loads(bridge.create_purchase("PO-2026-001", supplier_id, "2026-10-01", json.dumps(purchase_1_items)))
    assert dup_purch['status'] == 'error'
    assert 'already exists' in dup_purch['message'].lower()

    # Resubmit payment with same reference -> must reject duplicate
    dup_pay = json.loads(bridge.record_payment("PAY-2026-001", supplier_id, "2026-10-05", 1000, json.dumps([]), ""))
    assert dup_pay['status'] == 'error'
    assert 'already exists' in dup_pay['message'].lower()
