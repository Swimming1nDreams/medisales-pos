import re
import json
import time
import pytest
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

def test_incremental_search_static_js_signatures():
    repo_root = Path(__file__).resolve().parent.parent
    main_js = (repo_root / "src" / "ui_web" / "js" / "main.js").read_text(encoding="utf-8")
    sales_js = (repo_root / "src" / "ui_web" / "js" / "pages" / "sales.js").read_text(encoding="utf-8")
    prod_js = (repo_root / "src" / "ui_web" / "js" / "pages" / "products.js").read_text(encoding="utf-8")

    # Verify filterAndRankItems & highlightSearchMatch in main.js
    assert "window.filterAndRankItems = filterAndRankItems;" in main_js
    assert "window.highlightSearchMatch = highlightSearchMatch;" in main_js
    assert "bg-amber-200" in main_js  # Marker highlighting style

    # Verify sales.js uses filterAndRankItems and highlightSearchMatch
    assert "window.filterAndRankItems" in sales_js
    assert "window.highlightSearchMatch" in sales_js

    # Verify products.js has _renderProductsTbody and preserves input focus
    assert "_renderProductsTbody" in prod_js
    assert "products-tbody" in prod_js


def wait_for_ms(ms):
    loop = QEventLoop()
    QTimer.singleShot(ms, loop.quit)
    loop.exec()


import time

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
        if app:
            app.processEvents()
        time.sleep(0.02)
    return result


def test_runtime_incremental_search_letter_by_letter(qapp, tmp_path):
    db_path = str(tmp_path / "test_search.db")
    db_manager = DatabaseManager(db_path)
    migrations = MigrationsManager(db_manager)
    migrations.apply_migrations()

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

    # Wait for web view and QWebChannel to initialize
    for _ in range(50):
        wait_for_ms(100)
        ready = run_js(window, "typeof window.filterAndRankItems === 'function'")
        if ready:
            break

    assert run_js(window, "typeof window.filterAndRankItems === 'function'"), "filterAndRankItems must be loaded"

    # Test pure JS ranking logic letter by letter
    setup_sample_data = """
    window.testProducts = [
        { id: 1, name: "Aspirin 100mg", category_name: "Pain Relief", is_active: 1, current_stock: 50 },
        { id: 2, name: "Ampicillin 500mg", category_name: "Antibiotics", is_active: 1, current_stock: 50 },
        { id: 3, name: "Ciprofloxacin 500mg", category_name: "Antibiotics", is_active: 1, current_stock: 50 },
        { id: 4, name: "Paracetamol 500mg", category_name: "Pain Relief", is_active: 1, current_stock: 100 },
        { id: 5, name: "Panadol Extra", category_name: "Pain Relief", is_active: 1, current_stock: 80 },
        { id: 6, name: "Syrup Paracetamol", category_name: "Pain Relief", is_active: 1, current_stock: 30 },
        { id: 7, name: "Amoxicillin 500mg", category_name: "Antibiotics", is_active: 1, current_stock: 60 }
    ];
    """
    run_js(window, setup_sample_data)

    # 1. Search 'p'
    # 'Paracetamol' & 'Panadol' start with 'p' (score ~5500), 'Syrup Paracetamol' word starts with 'p' (score ~3300),
    # 'Aspirin', 'Ampicillin', 'Ciprofloxacin' contain 'p' (score ~1100). 'Amoxicillin' has no 'p' (excluded).
    p_names = json.loads(run_js(window, "JSON.stringify(window.filterAndRankItems(window.testProducts, 'p').map(x => x.name))"))
    assert "Amoxicillin 500mg" not in p_names, f"Amoxicillin has no 'p' and must be filtered out: {p_names}"
    # Prefix matches must be at top
    assert p_names[0] in ["Panadol Extra", "Paracetamol 500mg"], f"Expected prefix match at top, got {p_names}"
    assert p_names[1] in ["Panadol Extra", "Paracetamol 500mg"], f"Expected prefix match at top, got {p_names}"
    assert p_names[2] == "Syrup Paracetamol"
    assert "Aspirin 100mg" in p_names[3:]
    assert "Ciprofloxacin 500mg" in p_names[3:]

    # 2. Search 'pa'
    pa_names = json.loads(run_js(window, "JSON.stringify(window.filterAndRankItems(window.testProducts, 'pa').map(x => x.name))"))
    assert "Ampicillin 500mg" not in pa_names
    assert "Ciprofloxacin 500mg" not in pa_names
    assert "Amoxicillin 500mg" not in pa_names
    # Panadol & Paracetamol (name starts with 'pa') and Syrup Paracetamol (word starts with 'pa') must be at the top!
    assert pa_names[0] in ["Panadol Extra", "Paracetamol 500mg"]
    assert pa_names[1] in ["Panadol Extra", "Paracetamol 500mg"]
    assert pa_names[2] == "Syrup Paracetamol"
    # Aspirin only appears at the end because of its secondary category 'Pain Relief'
    assert pa_names[3] == "Aspirin 100mg"

    # 3. Search 'par'
    par_names = json.loads(run_js(window, "JSON.stringify(window.filterAndRankItems(window.testProducts, 'par').map(x => x.name))"))
    assert "Panadol Extra" not in par_names
    assert set(par_names) == {"Paracetamol 500mg", "Syrup Paracetamol"}

    # 4. Search 'para'
    para_names = json.loads(run_js(window, "JSON.stringify(window.filterAndRankItems(window.testProducts, 'para').map(x => x.name))"))
    assert set(para_names) == {"Paracetamol 500mg", "Syrup Paracetamol"}
    assert para_names[0] == "Paracetamol 500mg"

    # 5. Search 'parac'
    parac_names = json.loads(run_js(window, "JSON.stringify(window.filterAndRankItems(window.testProducts, 'parac').map(x => x.name))"))
    assert set(parac_names) == {"Paracetamol 500mg", "Syrup Paracetamol"}

    # 6. Search 'paracetamol'
    exact_names = json.loads(run_js(window, "JSON.stringify(window.filterAndRankItems(window.testProducts, 'paracetamol').map(x => x.name))"))
    assert exact_names[0] == "Paracetamol 500mg"

    # 7. Test visual text highlighting
    highlight_res = run_js(window, "window.highlightSearchMatch('Paracetamol 500mg', 'para')")
    assert "<mark" in highlight_res
    assert "para</mark>cetamol" in highlight_res.lower()

    # 8. Test navigate to products page and check DOM preservation on typing
    run_js(window, "navigate('products')")
    for _ in range(30):
        wait_for_ms(100)
        has_tbody = run_js(window, "document.getElementById('products-tbody') !== null")
        if has_tbody:
            break

    # Tag search input
    run_js(window, "document.getElementById('products-search-input')._test_marker = 'persistent_input';")
    # Call filterProducts
    run_js(window, "window.filterProducts('p')")
    wait_for_ms(100)
    # Check that input element was NOT destroyed
    marker = run_js(window, "document.getElementById('products-search-input')._test_marker")
    assert marker == "persistent_input", "Input element must not be destroyed on search typing"

    window.close()
