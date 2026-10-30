import pytest
import json
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

def test_bridge_dashboard(bridge):
    res = bridge.get_dashboard_summary()
    data = json.loads(res)
    assert data['status'] == 'success'
    assert 'total_sales_revenue' in data['data']

def test_bridge_products(bridge):
    cat_res = json.loads(bridge.create_category("Test Cat"))
    cat_id = cat_res['data']['category_id']
    
    prod_res = json.loads(bridge.create_product("Test Prod", cat_id, "pcs", 1000, 10, False))
    assert prod_res['status'] == 'success'
    
    list_res = json.loads(bridge.list_products())
    assert len(list_res['data']) == 1
    assert list_res['data'][0]['name'] == "Test Prod"
