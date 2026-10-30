import pytest
import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from src.ui.main_window import MainWindow
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
def mock_services(db_manager):
    inventory_service = InventoryService(db_manager)
    product_service = ProductService(db_manager)
    sales_service = SalesService(db_manager, inventory_service)
    supplier_service = SupplierService(db_manager)
    purchase_service = PurchaseService(db_manager)
    expense_service = ExpenseService(db_manager)
    finance_service = FinanceService(db_manager)
    dashboard_service = DashboardService(db_manager, finance_service)
    report_service = ReportService(db_manager)
    reconciliation_service = ReconciliationService(db_manager)
    
    return {
        'db_manager': db_manager,
        'inventory_service': inventory_service,
        'product_service': product_service,
        'sales_service': sales_service,
        'supplier_service': supplier_service,
        'purchase_service': purchase_service,
        'expense_service': expense_service,
        'finance_service': finance_service,
        'dashboard_service': dashboard_service,
        'report_service': report_service,
        'reconciliation_service': reconciliation_service
    }

def test_main_window_loads_and_navigates(qapp, mock_services):
    window = MainWindow(mock_services)
    
    # Check that sidebar has items
    assert window.sidebar.count() == 9
    
    for i in range(9):
        window.sidebar.setCurrentRow(i)
        assert window.content_stack.currentIndex() == i

def test_main_window_web_initialization(qapp, mock_services):
    from src.ui.main_window_web import MainWindowWeb
    window = MainWindowWeb(mock_services)
    assert window.bridge is not None
    assert window.channel is not None
    assert window.view is not None
    assert "Say Mahar" in window.windowTitle()
