import argparse
import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication, QMessageBox

from src.utils.paths import resolve_database_path, mark_database_initialized
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
from src.services.customer_service import CustomerService
from src.services.export_service import ExportService

from src.ui.main_window_web import MainWindowWeb

def main():
    parser = argparse.ArgumentParser(description="Say Mahar Pharmacy & Retail POS")
    parser.add_argument("--db", "--database", dest="db_path", help="Path to SQLite database file", default=None)
    args, _ = parser.parse_known_args()

    app = QApplication(sys.argv)
    
    # Resolve DB path safely (separate writable AppData directory in packaged builds)
    try:
        db_path, is_first_launch = resolve_database_path(args.db_path)
        print(f"Effective Database Path: {db_path.resolve()}", flush=True)
    except FileNotFoundError as e:
        QMessageBox.critical(
            None,
            "Database Missing - Say Mahar",
            str(e)
        )
        sys.exit(1)
    except Exception as e:
        QMessageBox.critical(
            None,
            "Database Configuration Error",
            f"Failed to resolve database path: {str(e)}"
        )
        sys.exit(1)

    db_manager = DatabaseManager(str(db_path))
    
    try:
        # Run migrations
        migrations_manager = MigrationsManager(db_manager)
        migrations_manager.apply_migrations()
        
        # Mark as initialized on first run to protect against accidental missing db creation
        if is_first_launch:
            mark_database_initialized(db_path)
        
        # Initialize Services
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
        customer_service = CustomerService(db_manager)
        
        services = {
            'db_manager': db_manager,
            'inventory_service': inventory_service,
            'product_service': product_service,
            'sales_service': sales_service,
            'supplier_service': supplier_service,
            'customer_service': customer_service,
            'purchase_service': purchase_service,
            'expense_service': expense_service,
            'finance_service': finance_service,
            'dashboard_service': dashboard_service,
            'report_service': report_service,
            'reconciliation_service': reconciliation_service
        }
        export_service = ExportService(services)
        services['export_service'] = export_service
        
        # Start UI
        window = MainWindowWeb(services)
        window.show()
        
        sys.exit(app.exec())
        
    except Exception as e:
        QMessageBox.critical(None, "Database Error", f"Failed to initialize database: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
