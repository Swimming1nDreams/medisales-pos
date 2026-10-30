import pytest
import json
import datetime
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
def bridge():
    db = DatabaseManager(":memory:")
    MigrationsManager(db).apply_migrations()
    
    inv = InventoryService(db)
    prod = ProductService(db)
    sales = SalesService(db, inv)
    supp = SupplierService(db)
    purch = PurchaseService(db)
    exp = ExpenseService(db)
    fin = FinanceService(db)
    dash = DashboardService(db, fin)
    rep = ReportService(db)
    recon = ReconciliationService(db)
    
    services = {
        'db_manager': db, 'inventory_service': inv, 'product_service': prod,
        'sales_service': sales, 'supplier_service': supp, 'purchase_service': purch,
        'expense_service': exp, 'finance_service': fin, 'dashboard_service': dash,
        'report_service': rep, 'reconciliation_service': recon
    }
    
    return FrontendBridge(services)

def test_1_create_product_and_persist(bridge):
    cat_res = json.loads(bridge.create_category("Test Cat"))
    cat_id = cat_res['data']['category_id']
    prod_res = json.loads(bridge.create_product("General Item", cat_id, "pcs", 1500.0, 5, False))
    assert prod_res['status'] == 'success'
    
    products = json.loads(bridge.list_products())['data']
    assert len(products) == 1
    assert products[0]['name'] == "General Item"
    assert products[0]['selling_price'] == 1500.0

def test_2_record_purchase_and_confirm_stock(bridge):
    cat_res = json.loads(bridge.create_category("Test Cat"))
    cat_id = cat_res['data']['category_id']
    prod_res = json.loads(bridge.create_product("General Item", cat_id, "pcs", 1500.0, 5, False))
    prod_id = prod_res['data']['product_id']
    
    supp_res = json.loads(bridge.create_supplier("Supplier A", "123", "Addr"))
    supp_id = supp_res['data']['supplier_id']
    
    items = json.dumps([{'product_id': prod_id, 'quantity': 10, 'unit_cost': 1000.0, 'batch_number': None, 'expiry_date': None}])
    purch_res = json.loads(bridge.create_purchase("INV-001", supp_id, "2023-01-01", items))
    assert purch_res['status'] == 'success'
    
    stock = json.loads(bridge.get_current_stock())['data']
    item_stock = next(s for s in stock if s['id'] == prod_id)
    assert item_stock['current_stock'] == 10

def test_3_record_medicine_purchase(bridge):
    cat_res = json.loads(bridge.create_category("Test Cat"))
    cat_id = cat_res['data']['category_id']
    prod_res = json.loads(bridge.create_product("Medicine A", cat_id, "box", 2500.0, 5, True))
    prod_id = prod_res['data']['product_id']
    
    supp_res = json.loads(bridge.create_supplier("Supplier B", "123", "Addr"))
    supp_id = supp_res['data']['supplier_id']
    
    future_date = (datetime.date.today() + datetime.timedelta(days=365)).isoformat()
    items = json.dumps([{'product_id': prod_id, 'quantity': 20, 'unit_cost': 2000.0, 'batch_number': "BATCH-1", 'expiry_date': future_date}])
    purch_res = json.loads(bridge.create_purchase("INV-002", supp_id, "2023-01-01", items))
    assert purch_res['status'] == 'success'
    
    batches = json.loads(bridge.get_sellable_medicine_batches(prod_id))['data']
    assert len(batches) == 1
    assert batches[0]['batch_number'] == "BATCH-1"
    assert batches[0]['current_qty'] == 20

def test_4_record_sale_and_confirm_stock_decrease(bridge):
    # Setup product, supplier, purchase
    cat_id = json.loads(bridge.create_category("C"))['data']['category_id']
    prod_id = json.loads(bridge.create_product("Item", cat_id, "pcs", 1000, 5, False))['data']['product_id']
    supp_id = json.loads(bridge.create_supplier("S", "1", "A"))['data']['supplier_id']
    items = json.dumps([{'product_id': prod_id, 'quantity': 10, 'unit_cost': 500.0, 'batch_number': None, 'expiry_date': None}])
    bridge.create_purchase("REF-1", supp_id, "2023-01-01", items)
    
    # Sale
    sale_items = json.dumps([{'product_id': prod_id, 'quantity': 3, 'unit_price': 1000.0}])
    sale_res = json.loads(bridge.create_sale("SALE-1", sale_items, 3000.0))
    assert sale_res['status'] == 'success'
    
    # Check Stock
    stock = json.loads(bridge.get_current_stock())['data']
    item_stock = next(s for s in stock if s['id'] == prod_id)
    assert item_stock['current_stock'] == 7

def test_5_expired_medicine_cannot_be_sold(bridge):
    cat_id = json.loads(bridge.create_category("C"))['data']['category_id']
    prod_id = json.loads(bridge.create_product("Med", cat_id, "pcs", 1000, 5, True))['data']['product_id']
    supp_id = json.loads(bridge.create_supplier("S", "1", "A"))['data']['supplier_id']
    
    past_date = "2020-01-01"
    items = json.dumps([{'product_id': prod_id, 'quantity': 10, 'unit_cost': 500.0, 'batch_number': "B1", 'expiry_date': past_date}])
    bridge.create_purchase("REF-1", supp_id, "2023-01-01", items)
    
    sale_items = json.dumps([{'product_id': prod_id, 'quantity': 1, 'unit_price': 1000.0}])
    sale_res = json.loads(bridge.create_sale("SALE-1", sale_items, 1000.0))
    assert sale_res['status'] == 'error'
    assert 'expired' in sale_res['message'].lower() or 'insufficient' in sale_res['message'].lower()

def test_6_sale_voids_preserve_inventory_audit(bridge):
    cat_id = json.loads(bridge.create_category("C"))['data']['category_id']
    prod_id = json.loads(bridge.create_product("Item", cat_id, "pcs", 1000, 5, False))['data']['product_id']
    supp_id = json.loads(bridge.create_supplier("S", "1", "A"))['data']['supplier_id']
    items = json.dumps([{'product_id': prod_id, 'quantity': 10, 'unit_cost': 500.0, 'batch_number': None, 'expiry_date': None}])
    bridge.create_purchase("P-1", supp_id, "2023-01-01", items)
    
    sale_items = json.dumps([{'product_id': prod_id, 'quantity': 5, 'unit_price': 1000.0}])
    sale_id = json.loads(bridge.create_sale("S-1", sale_items, 5000.0))['data']['sale_id']
    
    # stock should be 5
    assert next(s for s in json.loads(bridge.get_current_stock())['data'] if s['id'] == prod_id)['current_stock'] == 5
    
    # Void
    void_res = json.loads(bridge.void_sale(sale_id, "Mistake"))
    assert void_res['status'] == 'success'
    
    # stock should be 10
    assert next(s for s in json.loads(bridge.get_current_stock())['data'] if s['id'] == prod_id)['current_stock'] == 10
    
    # Check audit log directly from DB
    conn = bridge.services['db_manager'].get_connection()
    logs = conn.execute("SELECT * FROM inventory_movements WHERE product_id = ?", (prod_id,)).fetchall()
    # P-1 (purchase), S-1 (sale out), S-1 (void return)
    assert len(logs) == 3

def test_7_record_supplier_payment_and_balances(bridge):
    supp_id = json.loads(bridge.create_supplier("S", "1", "A"))['data']['supplier_id']
    cat_id = json.loads(bridge.create_category("C"))['data']['category_id']
    prod_id = json.loads(bridge.create_product("Item", cat_id, "pcs", 1000, 5, False))['data']['product_id']
    
    items = json.dumps([{'product_id': prod_id, 'quantity': 10, 'unit_cost': 500.0, 'batch_number': None, 'expiry_date': None}])
    purch_id = json.loads(bridge.create_purchase("P-1", supp_id, "2023-01-01", items))['data']['purchase_id']
    
    # balance should be 5000
    bals = json.loads(bridge.get_supplier_balances())['data']
    assert next(b for b in bals if b['supplier_id'] == supp_id)['outstanding_balance'] == 5000.0
    
    # record payment
    allocations = json.dumps([{'purchase_id': purch_id, 'allocated_amount': 2000.0}])
    pay_res = json.loads(bridge.record_payment("PAY-1", supp_id, "2023-01-02", 2000.0, allocations, ""))
    assert pay_res['status'] == 'success'
    
    # balance should be 3000
    bals = json.loads(bridge.get_supplier_balances())['data']
    assert next(b for b in bals if b['supplier_id'] == supp_id)['outstanding_balance'] == 3000.0

def test_8_record_and_void_expense(bridge):
    exp_res = json.loads(bridge.record_expense("2023-01-01", "Office", 1500.0, "Pens"))
    assert exp_res['status'] == 'success'
    exp_id = exp_res['data']['expense_id']
    
    exps = json.loads(bridge.get_expenses("2023-01-01", "2023-01-01"))['data']
    assert len(exps) == 1
    assert exps[0]['status'] == 'Completed'
    
    void_res = json.loads(bridge.void_expense(exp_id, "Error"))
    assert void_res['status'] == 'success'
    
    exps = json.loads(bridge.get_expenses("2023-01-01", "2023-01-01"))['data']
    assert len(exps) == 1
    assert exps[0]['status'] == 'Voided'

def test_9_report_calculations(bridge):
    cat_id = json.loads(bridge.create_category("C"))['data']['category_id']
    prod_id = json.loads(bridge.create_product("Item", cat_id, "pcs", 1000, 5, False))['data']['product_id']
    supp_id = json.loads(bridge.create_supplier("S", "1", "A"))['data']['supplier_id']
    
    today = datetime.date.today().isoformat()
    
    items = json.dumps([{'product_id': prod_id, 'quantity': 10, 'unit_cost': 500.0, 'batch_number': None, 'expiry_date': None}])
    bridge.create_purchase("P-1", supp_id, today, items)
    
    sale_items = json.dumps([{'product_id': prod_id, 'quantity': 2, 'unit_price': 1000.0}])
    bridge.create_sale("S-1", sale_items, 2000.0)
    
    sales_rep = json.loads(bridge.get_sales_summary(today, today))['data']
    assert sales_rep['total_revenue'] == 2000.0
    assert sales_rep['total_cogs'] == 1000.0
    assert sales_rep['gross_profit'] == 1000.0

def test_10_invalid_operations_do_not_leave_partial_db(bridge):
    cat_id = json.loads(bridge.create_category("C"))['data']['category_id']
    prod_id = json.loads(bridge.create_product("Item", cat_id, "pcs", 1000, 5, False))['data']['product_id']
    
    today = datetime.date.today().isoformat()
    
    # Try to sell item without stock (should fail)
    sale_items = json.dumps([{'product_id': prod_id, 'quantity': 10, 'unit_price': 1000.0}])
    res = json.loads(bridge.create_sale("S-FAIL", sale_items, 10000.0))
    assert res['status'] == 'error'
    
    # Verify no partial sale was created
    conn = bridge.services['db_manager'].get_connection()
    sales = conn.execute("SELECT count(*) FROM sales").fetchone()[0]
    assert sales == 0
