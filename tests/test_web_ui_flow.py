import pytest
import sys
import json
import time
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QEventLoop, QTimer
from PySide6.QtWebEngineCore import QWebEnginePage

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
from src.ui.main_window_web import MainWindowWeb

@pytest.fixture
def test_services(tmp_path):
    db_file = str(tmp_path / "test_medisales.db")
    db_manager = DatabaseManager(db_file)
    MigrationsManager(db_manager).apply_migrations()

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
    yield services
    db_manager.close()

def wait_for_ms(ms):
    loop = QEventLoop()
    QTimer.singleShot(ms, loop.quit)
    loop.exec()

def run_js(window, script):
    result = None
    done = False
    def callback(res):
        nonlocal result, done
        result = res
        done = True

    window.view.page().runJavaScript(script, callback)
    start = time.time()
    while not done and time.time() - start < 5.0:
        app = QApplication.instance()
        app.processEvents()
        time.sleep(0.02)
    return result

def test_web_ui_navigation_and_zero_errors(qapp, test_services):
    window = MainWindowWeb(test_services)
    window.resize(1280, 800)
    window.show()

    js_errors = []
    def handle_console_message(level, msg, line, source):
        # QWebEnginePage.JavaScriptConsoleMessageLevel.ErrorMessageLevel is 2
        if level == QWebEnginePage.JavaScriptConsoleMessageLevel.ErrorMessageLevel:
            js_errors.append(f"Line {line} ({source}): {msg}")

    window.view.page().javaScriptConsoleMessage = handle_console_message

    # Allow page to load & QWebChannel to connect
    wait_for_ms(2000)

    pages = [
        'dashboard',
        'sales',
        'products',
        'inventory',
        'purchases',
        'suppliers',
        'expenses',
        'reports',
        'settings'
    ]

    for p in pages:
        run_js(window, f"navigate('{p}');")
        wait_for_ms(400)
        # Check that page title or content area rendered
        content_html = run_js(window, "document.getElementById('content-area').innerHTML;")
        assert content_html is not None and len(content_html) > 0, f"Page {p} had empty content"

    # Verify zero JS errors across all 9 pages
    assert len(js_errors) == 0, f"JavaScript errors encountered: {js_errors}"
    window.close()
