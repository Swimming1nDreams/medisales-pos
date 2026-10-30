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

def capture_all_pages(output_dir="screenshots/before", db_path="demo_medisales.db"):
    os.makedirs(output_dir, exist_ok=True)
    app = QApplication.instance() or QApplication(sys.argv)
    
    # Use specified or demo database
    db_file = Path(db_path)
    if not db_file.exists():
        db_file = Path("medisales.db")
    db_manager = DatabaseManager(str(db_file))
    
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
    
    pages = [
        ('dashboard', '01_dashboard.png'),
        ('sales', '02_sales.png'),
        ('products', '03_products.png'),
        ('inventory', '04_inventory.png'),
        ('purchases', '05_purchases.png'),
        ('suppliers', '06_suppliers.png'),
        ('expenses', '07_expenses.png'),
        ('reports', '08_reports.png'),
        ('settings', '09_settings.png'),
    ]
    
    # Wait for webview initial load
    loop = QEventLoop()
    QTimer.singleShot(2500, loop.quit)
    loop.exec()
    
    results = {}
    for page_id, filename in pages:
        # Navigate to page and reset render flag
        window.view.page().runJavaScript(f"window._pageRendered = false; window._renderedPage = null; navigate('{page_id}');")
        
        # Wait until window._pageRendered is True and window._renderedPage is page_id
        for _ in range(50): # up to 5 seconds
            loop = QEventLoop()
            QTimer.singleShot(100, loop.quit)
            loop.exec()
            
            rendered = False
            check_loop = QEventLoop()
            def on_check(val):
                nonlocal rendered
                rendered = bool(val)
                check_loop.quit()
            window.view.page().runJavaScript(f"Boolean(window._pageRendered === true && window._renderedPage === '{page_id}');", on_check)
            check_loop.exec()
            if rendered:
                break
                
        # Settle layout and paint
        loop = QEventLoop()
        QTimer.singleShot(600, loop.quit)
        loop.exec()
        
        # Capture pixmap
        pixmap = window.grab()
        target_path = os.path.join(output_dir, filename)
        saved = pixmap.save(target_path)
        results[page_id] = (saved, target_path)
        print(f"Captured {page_id} -> {target_path} (success: {saved})")
        
    window.close()
    db_manager.close()
    return results

if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "screenshots/before"
    db = sys.argv[2] if len(sys.argv) > 2 else "demo_medisales.db"
    capture_all_pages(out, db)
