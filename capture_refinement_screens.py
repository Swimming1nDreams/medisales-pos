import os
import sys
import time
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer, QUrl, QEventLoop

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

def run_js_sync(window, js_code, wait_ms=100):
    window.view.page().runJavaScript(js_code)
    loop = QEventLoop()
    QTimer.singleShot(wait_ms, loop.quit)
    loop.exec()

def wait_page_rendered(window, page_id, timeout_ms=5000):
    start = time.time()
    while (time.time() - start) * 1000 < timeout_ms:
        rendered = False
        loop = QEventLoop()
        def cb(res):
            nonlocal rendered
            rendered = bool(res)
            loop.quit()
        window.view.page().runJavaScript(
            f"Boolean(window._pageRendered === true && window._renderedPage === '{page_id}');",
            cb
        )
        loop.exec()
        if rendered:
            break
        sub_loop = QEventLoop()
        QTimer.singleShot(100, sub_loop.quit)
        sub_loop.exec()

    # Settle render & paint
    settle_loop = QEventLoop()
    QTimer.singleShot(400, settle_loop.quit)
    settle_loop.exec()

def capture_state(window, output_dir, filename):
    pixmap = window.grab()
    target_path = os.path.join(output_dir, filename)
    saved = pixmap.save(target_path)
    print(f"Captured: {filename} -> {target_path} (success: {saved})")
    return saved, target_path

def main():
    output_dir = "screenshots/refinement"
    os.makedirs(output_dir, exist_ok=True)
    db_path = "demo_medisales.db"
    if not os.path.exists(db_path):
        db_path = "medisales.db"

    app = QApplication.instance() or QApplication(sys.argv)
    db_manager = DatabaseManager(db_path)
    
    services = {
        'db_manager': db_manager,
        'inventory_service': InventoryService(db_manager),
        'product_service': ProductService(db_manager),
        'sales_service': SalesService(db_manager, InventoryService(db_manager)),
        'supplier_service': SupplierService(db_manager),
        'purchase_service': PurchaseService(db_manager),
        'expense_service': ExpenseService(db_manager),
        'finance_service': FinanceService(db_manager),
        'dashboard_service': DashboardService(db_manager, FinanceService(db_manager)),
        'report_service': ReportService(db_manager),
        'reconciliation_service': ReconciliationService(db_manager)
    }

    window = MainWindowWeb(services)
    window.resize(1280, 800)
    window.show()

    # Wait for webview initial load
    init_loop = QEventLoop()
    QTimer.singleShot(2500, init_loop.quit)
    init_loop.exec()

    # 1. 01_dashboard.png
    print("Capturing 01_dashboard.png...")
    run_js_sync(window, "window._pageRendered = false; window._renderedPage = null; navigate('dashboard');")
    wait_page_rendered(window, 'dashboard')
    capture_state(window, output_dir, "01_dashboard.png")

    # 2. 02_sales_empty_cart.png
    print("Capturing 02_sales_empty_cart.png...")
    run_js_sync(window, "window._pageRendered = false; window._renderedPage = null; navigate('sales');")
    wait_page_rendered(window, 'sales')
    capture_state(window, output_dir, "02_sales_empty_cart.png")

    # 3. 02_sales_populated_cart.png
    print("Capturing 02_sales_populated_cart.png...")
    # Add products to cart and enter tender
    run_js_sync(window, """
        if (typeof salesProducts !== 'undefined' && salesProducts.length > 0) {
            salesAddToCart(salesProducts[0].id);
            if (salesProducts.length > 1) {
                salesAddToCart(salesProducts[1].id);
            }
            const tenderInput = document.getElementById('sales-received');
            if (tenderInput) {
                tenderInput.value = '15000';
                salesCalcChange();
            }
        }
    """, wait_ms=400)
    capture_state(window, output_dir, "02_sales_populated_cart.png")

    # 4. 03_products_normal.png
    print("Capturing 03_products_normal.png...")
    run_js_sync(window, "window._pageRendered = false; window._renderedPage = null; navigate('products');")
    wait_page_rendered(window, 'products')
    capture_state(window, output_dir, "03_products_normal.png")

    # 5. 03_products_no_results.png
    print("Capturing 03_products_no_results.png...")
    run_js_sync(window, "filterProducts('NonExistentMedicineNameXYZ999');", wait_ms=400)
    capture_state(window, output_dir, "03_products_no_results.png")

    # 6. 04_inventory_stock.png
    print("Capturing 04_inventory_stock.png...")
    run_js_sync(window, "window._pageRendered = false; window._renderedPage = null; navigate('inventory');")
    wait_page_rendered(window, 'inventory')
    run_js_sync(window, "switchInventoryTab('stock');", wait_ms=400)
    capture_state(window, output_dir, "04_inventory_stock.png")

    # 7. 04_inventory_all_batches.png
    print("Capturing 04_inventory_all_batches.png...")
    run_js_sync(window, "switchInventoryTab('all_batches');", wait_ms=600)
    capture_state(window, output_dir, "04_inventory_all_batches.png")

    # 8. 04_inventory_expiring_soon.png
    print("Capturing 04_inventory_expiring_soon.png...")
    run_js_sync(window, "switchInventoryTab('expiring_soon');", wait_ms=600)
    capture_state(window, output_dir, "04_inventory_expiring_soon.png")

    # 9. 04_inventory_expired.png
    print("Capturing 04_inventory_expired.png...")
    run_js_sync(window, "switchInventoryTab('expired');", wait_ms=600)
    capture_state(window, output_dir, "04_inventory_expired.png")

    window.close()
    db_manager.close()
    print("All 9 screenshots captured successfully.")

if __name__ == "__main__":
    main()
