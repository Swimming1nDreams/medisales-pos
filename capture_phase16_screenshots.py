import os
import sys
import time
from pathlib import Path
from datetime import date, timedelta
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
from src.services.export_service import ExportService
from src.ui.main_window_web import MainWindowWeb

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
        if app:
            app.processEvents()
        time.sleep(0.02)
    return result

def seed_demo_database(db_manager, services):
    inv_svc = services['inventory_service']
    prod_svc = services['product_service']
    supp_svc = services['supplier_service']
    purch_svc = services['purchase_service']
    sales_svc = services['sales_service']
    exp_svc = services['expense_service']

    with db_manager.transaction() as tx:
        c1 = tx.execute("INSERT INTO categories (name) VALUES ('ဆေးဝါးများ (Medicines)')").lastrowid
        c2 = tx.execute("INSERT INTO categories (name) VALUES ('အထွေထွေကုန်စုံ (General Goods)')").lastrowid
        c3 = tx.execute("INSERT INTO categories (name) VALUES ('ကျန်းမာရေးနှင့် တစ်ကိုယ်ရေသုံး (Personal Care)')").lastrowid

    # Create Suppliers
    s1 = supp_svc.create_supplier("ရွှေမင်းသုတ ဆေးလက်ကား (Shwe Min Thuta Pharma)", "09-250123456", "ဘုရင့်နောင်လမ်း၊ ရန်ကုန်")
    s2 = supp_svc.create_supplier("AA Medical Products Ltd", "09-420987654", "လမ်းမတော်၊ ရန်ကုန်")
    s3 = supp_svc.create_supplier("အောင်သပြေ အထွေထွေကုန်စုံ (Aung Thabyay Wholesale)", "09-790112233", "၈၀ လမ်း၊ မန္တလေး")

    # Create Products
    p1 = prod_svc.create_product("Biogesic 500mg ပါရာစီတမော", c1, "ကတ် (Strip)", 1500, 15, is_medicine=True)
    p2 = prod_svc.create_product("Amoxicillin 500mg ပဋိဇီဝဆေး", c1, "ကတ် (Strip)", 2200, 20, is_medicine=True)
    p3 = prod_svc.create_product("Vitamin C 1000mg Effervescent", c1, "ဗူး (Tube)", 4500, 10, is_medicine=True)
    p4 = prod_svc.create_product("Lux Velvet Touch Soap 100g", c2, "တုံး (Bar)", 1200, 25, is_medicine=False)
    p5 = prod_svc.create_product("Colgate Total Toothpaste 150g", c3, "ဗူး (Tube)", 3800, 12, is_medicine=False)

    # Inward Purchases with Batches
    exp_amx = (date.today() + timedelta(days=180)).isoformat()
    exp_bio = (date.today() + timedelta(days=365)).isoformat()
    exp_vit = (date.today() + timedelta(days=45)).isoformat() # Expiring soon

    purch_svc.create_purchase("PO-2026-001", s1, "2026-10-01", [
        {'product_id': p1, 'quantity': 50, 'unit_cost': 1000, 'batch_number': 'BIO-2026-B1', 'expiry_date': exp_bio},
        {'product_id': p2, 'quantity': 40, 'unit_cost': 1500, 'batch_number': 'AMX-2026-B1', 'expiry_date': exp_amx},
    ])

    purch_svc.create_purchase("PO-2026-002", s2, "2026-10-03", [
        {'product_id': p3, 'quantity': 30, 'unit_cost': 3200, 'batch_number': 'VIT-2026-X1', 'expiry_date': exp_vit},
    ])

    purch_svc.create_purchase("PO-2026-003", s3, "2026-10-05", [
        {'product_id': p4, 'quantity': 60, 'unit_cost': 850, 'batch_number': None, 'expiry_date': None},
        {'product_id': p5, 'quantity': 35, 'unit_cost': 2700, 'batch_number': None, 'expiry_date': None},
    ])

    # Record completed sales
    s_id1 = sales_svc.create_sale("REC-2026-001", [
        {'product_id': p1, 'quantity': 2, 'unit_price': 1500},
        {'product_id': p4, 'quantity': 3, 'unit_price': 1200}
    ], 10000)

    s_id2 = sales_svc.create_sale("REC-2026-002", [
        {'product_id': p2, 'quantity': 1, 'unit_price': 2200},
        {'product_id': p3, 'quantity': 1, 'unit_price': 4500}
    ], 7000)

    # Record a voided sale
    s_id3 = sales_svc.create_sale("REC-2026-003", [
        {'product_id': p5, 'quantity': 2, 'unit_price': 3800}
    ], 8000)
    sales_svc.void_sale(s_id3)

    # Operating Expenses
    exp_svc.create_expense("ဆိုင်ခန်းငှားရမ်းခ (Shop Rent)", "အောက်တိုဘာလ ဆိုင်ခန်းငှားရမ်းခ", 150000, "2026-10-02")
    exp_svc.create_expense("လျှပ်စစ်နှင့် ရေဖိုး (Electricity & Water)", "မီတာခနှင့် ရေဖိုး ပေးသွင်းခြင်း", 35000, "2026-10-06")
    exp_svc.create_expense("အထွေထွေအသုံးစရိတ် (General Supplies)", "ဘောက်ချာစာအုပ်နှင့် စာရေးကိရိယာများ", 12000, "2026-10-08")

    # Supplier Payments (Debt Settlements)
    conn = db_manager.get_connection()
    p_rows = conn.execute("SELECT id FROM purchases WHERE supplier_id = ?", (s1,)).fetchall()
    purch_svc.record_payment("PV-2026-001", s1, "2026-10-07", 50000, [
        {'purchase_id': p_rows[0]['id'], 'allocated_amount': 50000}
    ], "ရွှေမင်းသုတ ဆေးလက်ကားသို့ တပိုင်းကြေ ပေးသွင်းငွေ")

    return s_id1

def main():
    root_dir = Path(__file__).resolve().parent
    out_dir = root_dir / "docs" / "screenshots" / "phase16"
    out_dir.mkdir(parents=True, exist_ok=True)

    db_path = root_dir / "docs" / "temp_phase16_demo.db"
    if db_path.exists():
        try:
            db_path.unlink()
        except Exception:
            pass

    app = QApplication.instance() or QApplication(sys.argv)

    db_manager = DatabaseManager(str(db_path))
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
    exporter = ExportService(services)
    services['export_service'] = exporter

    demo_sale_id = seed_demo_database(db_manager, services)

    window = MainWindowWeb(services)
    window.resize(1280, 800)
    window.show()

    # Wait for page load and QWebChannel connection
    wait_for_ms(2500)

    modules = [
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

    for lang in ['en', 'my']:
        print(f"\n--- Capturing UI in {lang.upper()} ---")
        run_js(window, f"setLanguage('{lang}');")
        wait_for_ms(800)

        for mod in modules:
            print(f"Navigating to {mod} [{lang}]...")
            run_js(window, f"navigate('{mod}');")
            wait_for_ms(700)

            shot_path = out_dir / f"{mod}_{lang}.png"
            pixmap = window.grab()
            pixmap.save(str(shot_path), "PNG")
            print(f"  Saved: {shot_path.name} ({shot_path.stat().st_size} bytes)")

        # In sales page, show the receipt modal and capture it
        print(f"Capturing receipt modal [{lang}]...")
        run_js(window, "navigate('sales');")
        wait_for_ms(500)
        run_js(window, """
            if (window._showReceiptModal) {
                window._showReceiptModal('REC-2026-001', [
                    {product: {name: 'Biogesic 500mg ပါရာစီတမော', selling_price: 1500}, qty: 2},
                    {product: {name: 'Lux Velvet Touch Soap 100g', selling_price: 1200}, qty: 3}
                ], 6600, 10000, 3400);
            }
        """)
        wait_for_ms(700)
        receipt_path = out_dir / f"receipt_modal_{lang}.png"
        pixmap = window.grab()
        pixmap.save(str(receipt_path), "PNG")
        print(f"  Saved receipt: {receipt_path.name} ({receipt_path.stat().st_size} bytes)")
        run_js(window, "closeModal();")
        wait_for_ms(300)

    window.close()
    db_manager.close()

    print("\nPhase 16 visual review screenshots captured successfully at 1280x800!")

if __name__ == "__main__":
    main()
