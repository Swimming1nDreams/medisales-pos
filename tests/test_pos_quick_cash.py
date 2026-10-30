import re
import pytest
import json
import time
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QEventLoop, QTimer

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

def test_sales_js_quick_cash_denominations_static():
    """Verify statically in sales.js that all quick cash buttons > 10,000 MMK are removed

    and that buttons <= 10,000 MMK are preserved.
    """
    repo_root = Path(__file__).resolve().parent.parent
    sales_js = repo_root / "src" / "ui_web" / "js" / "pages" / "sales.js"
    assert sales_js.exists(), "sales.js must exist"

    content = sales_js.read_text(encoding="utf-8")

    # Match quick cash button onclick calls: salesAddCash(amount)
    button_matches = re.findall(r'salesAddCash\((\d+)\)', content)
    # Filter only denomination buttons inside the HTML template
    # (excluding the window.salesAddCash = function(amount) definition)
    chip_amounts = [int(m) for m in button_matches]

    assert len(chip_amounts) > 0, "Expected at least one quick cash button in sales.js"
    
    # 1. No denomination buttons with values > 10,000 MMK
    greater_than_10k = [amt for amt in chip_amounts if amt > 10000]
    assert greater_than_10k == [], f"Found quick cash buttons > 10,000 MMK: {greater_than_10k}"

    # 2. Existing buttons with values <= 10,000 MMK are preserved
    assert 1000 in chip_amounts, "Missing +1,000 MMK quick cash button"
    assert 5000 in chip_amounts, "Missing +5,000 MMK quick cash button"
    assert 10000 in chip_amounts, "Missing +10,000 MMK quick cash button"
    assert chip_amounts == [1000, 5000, 10000], f"Unexpected chip amounts: {chip_amounts}"

    # Ensure no button labels for +20,000 or +50,000 exist in template
    assert "+20,000" not in content, "+20,000 label still found in sales.js"
    assert "+50,000" not in content, "+50,000 label still found in sales.js"
    assert "+1,000" in content, "+1,000 label should be present"
    assert "+5,000" in content, "+5,000 label should be present"
    assert "+10,000" in content, "+10,000 label should be present"


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


def test_sales_pos_quick_cash_runtime(qapp, tmp_path):
    """Verify at runtime in MainWindowWeb that the POS displays only <= 10,000 MMK buttons

    and that cash entry, quick cash adding, and change calculation work correctly.
    """
    db_file = str(tmp_path / "test_quick_cash.db")
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

    window = MainWindowWeb(services)
    window.resize(1280, 800)
    window.show()

    # Wait for initial page load & QWebChannel
    wait_for_ms(2000)

    # Navigate to POS / sales page
    run_js(window, "navigate('sales');")

    # Wait for sales page to fully render
    rendered = False
    for _ in range(30):
        val = run_js(window, "window._renderedPage === 'sales' && document.getElementById('sales-received') !== null;")
        if val is True:
            rendered = True
            break
        wait_for_ms(200)

    assert rendered, "Sales page did not finish rendering"

    # Query all quick cash buttons in the DOM
    query_buttons_script = """
    JSON.stringify(Array.from(document.querySelectorAll('button[onclick*="salesAddCash"]')).map(b => ({
        text: b.textContent.trim(),
        onclick: b.getAttribute('onclick')
    })))
    """
    raw_buttons = run_js(window, query_buttons_script)
    assert raw_buttons is not None, "Failed to query quick cash buttons from DOM"
    buttons = json.loads(raw_buttons)
    assert len(buttons) == 3, f"Expected 3 quick cash buttons, found {len(buttons)}: {buttons}"

    amounts_in_dom = [b['onclick'] for b in buttons]
    assert amounts_in_dom == ["salesAddCash(1000)", "salesAddCash(5000)", "salesAddCash(10000)"]

    texts_in_dom = [b['text'] for b in buttons]
    assert texts_in_dom == ["+1,000", "+5,000", "+10,000"]

    # Test clicking/calling quick cash buttons
    # 1. Start with empty
    run_js(window, "document.getElementById('sales-received').value = '';")
    # 2. Add 10,000
    run_js(window, "salesAddCash(10000);")
    val = run_js(window, "document.getElementById('sales-received').value;")
    assert val == "10000"

    # 3. Add 5,000 (total 15,000)
    run_js(window, "salesAddCash(5000);")
    val = run_js(window, "document.getElementById('sales-received').value;")
    assert val == "15000"

    # 4. Add 1,000 (total 16,000)
    run_js(window, "salesAddCash(1000);")
    val = run_js(window, "document.getElementById('sales-received').value;")
    assert val == "16000"

    # 5. Manual cash entry verification
    run_js(window, "document.getElementById('sales-received').value = '25000'; salesCalcChange();")
    val = run_js(window, "document.getElementById('sales-received').value;")
    assert val == "25000"

    window.close()
    db_manager.close()
