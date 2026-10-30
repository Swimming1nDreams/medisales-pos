import pytest
import sqlite3
from database.connection import DatabaseManager
from database.migrations_manager import MigrationsManager

@pytest.fixture
def db_manager():
    """Provides a fresh, migrated in-memory database for each test."""
    manager = DatabaseManager(db_path=":memory:")
    mig_manager = MigrationsManager(manager)
    mig_manager.apply_migrations()
    yield manager
    manager.close()

@pytest.fixture
def db_connection(db_manager):
    """Provides a connection to the test database."""
    return db_manager.get_connection()

@pytest.fixture
def product_service(db_manager):
    from src.services.product_service import ProductService
    return ProductService(db_manager)

@pytest.fixture
def inventory_service(db_manager):
    from src.services.inventory_service import InventoryService
    return InventoryService(db_manager)

@pytest.fixture
def reconciliation_service(db_manager):
    from src.services.reconciliation_service import ReconciliationService
    return ReconciliationService(db_manager)
@pytest.fixture
def supplier_service(db_manager):
    from src.services.supplier_service import SupplierService
    return SupplierService(db_manager)

@pytest.fixture
def customer_service(db_manager):
    from src.services.customer_service import CustomerService
    return CustomerService(db_manager)

@pytest.fixture
def purchase_service(db_manager):
    from src.services.purchase_service import PurchaseService
    return PurchaseService(db_manager)

@pytest.fixture
def sales_service(db_manager, inventory_service):
    from src.services.sales_service import SalesService
    return SalesService(db_manager, inventory_service)

@pytest.fixture
def expense_service(db_manager):
    from src.services.expense_service import ExpenseService
    return ExpenseService(db_manager)

@pytest.fixture
def finance_service(db_manager):
    from src.services.finance_service import FinanceService
    return FinanceService(db_manager)

@pytest.fixture
def dashboard_service(db_manager, finance_service):
    from src.services.dashboard_service import DashboardService
    return DashboardService(db_manager, finance_service)

@pytest.fixture
def report_service(db_manager):
    from src.services.report_service import ReportService
    return ReportService(db_manager)

@pytest.fixture(scope="session")
def qapp():
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance()
    if app is None:
        app = QApplication(["--platform", "offscreen"])
    yield app
