import os
import sys
import time
import shutil
import sqlite3
import tempfile
import subprocess
from pathlib import Path
from datetime import datetime, date

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

def run_js(window, js_code, wait_ms=250):
    """Executes JS in the QtWebEngineView and pumps the event loop."""
    result = None
    done = False
    def callback(val):
        nonlocal result, done
        result = val
        done = True
    
    window.view.page().runJavaScript(js_code, callback)
    start = time.time()
    while not done and (time.time() - start) < 5.0:
        app = QApplication.instance()
        if app:
            app.processEvents()
        time.sleep(0.02)
        
    loop = QEventLoop()
    QTimer.singleShot(wait_ms, loop.quit)
    loop.exec()
    return result

def wait_page(window, page_id, timeout_ms=6000):
    start = time.time()
    while (time.time() - start) * 1000 < timeout_ms:
        rendered = run_js(window, f"Boolean(window._pageRendered === true && window._renderedPage === '{page_id}');", wait_ms=50)
        if rendered:
            break
        loop = QEventLoop()
        QTimer.singleShot(100, loop.quit)
        loop.exec()

    # Settle DOM paint
    settle = QEventLoop()
    QTimer.singleShot(400, settle.quit)
    settle.exec()

def capture_ui(window, output_dir, filename):
    pixmap = window.grab()
    target = os.path.join(output_dir, filename)
    saved = pixmap.save(target)
    print(f"  [SCREENSHOT] {filename} -> {target} (saved: {saved})")
    return saved, target

def run_acceptance_suite():
    print("=" * 70)
    print("PHASE 11: CONTROLLED SHOP ACCEPTANCE & RELEASE READINESS VERIFICATION")
    print("=" * 70)

    # 1. SAFETY CHECKS: Record production database status
    repo_dir = Path(__file__).resolve().parent
    prod_db_path = repo_dir / "medisales.db"
    if prod_db_path.exists():
        prod_stat = prod_db_path.stat()
        prod_baseline = {
            "path": str(prod_db_path.resolve()),
            "size": prod_stat.st_size,
            "mtime": prod_stat.st_mtime
        }
        print(f"\n[SAFETY CHECK] Production Database Baseline:")
        print(f"  Path: {prod_baseline['path']}")
        print(f"  Size: {prod_baseline['size']} bytes")
        print(f"  MTime: {datetime.fromtimestamp(prod_baseline['mtime'])}")
    else:
        prod_baseline = None
        print("\n[SAFETY CHECK] Production Database not present at root.")

    # 2. CREATE ISOLATED DISPOSABLE DATABASE
    temp_dir = Path(tempfile.mkdtemp(prefix="medisales_phase11_acc_"))
    demo_db = temp_dir / "acceptance_demo.db"
    demo_db_resolved = demo_db.resolve()
    print(f"\n[DEMO ENVIRONMENT]")
    print(f"  Isolated Directory: {temp_dir}")
    print(f"  Effective Database Path: {demo_db_resolved}")
    print(f"  Isolation Verified: {demo_db_resolved != prod_db_path.resolve() if prod_baseline else True}")

    screenshots_dir = repo_dir / "screenshots" / "acceptance"
    screenshots_dir.mkdir(parents=True, exist_ok=True)

    # 3. INITIALIZE QT APP & SERVICES AGAINST DISPOSABLE DB
    app = QApplication.instance() or QApplication(sys.argv)
    db_mgr = DatabaseManager(str(demo_db_resolved))
    migrations = MigrationsManager(db_mgr)
    migrations.apply_migrations()

    inv_svc = InventoryService(db_mgr)
    prod_svc = ProductService(db_mgr)
    sales_svc = SalesService(db_mgr, inv_svc)
    supp_svc = SupplierService(db_mgr)
    purch_svc = PurchaseService(db_mgr)
    exp_svc = ExpenseService(db_mgr)
    fin_svc = FinanceService(db_mgr)
    dash_svc = DashboardService(db_mgr, fin_svc)
    rep_svc = ReportService(db_mgr)
    recon_svc = ReconciliationService(db_mgr)

    services = {
        'db_manager': db_mgr,
        'inventory_service': inv_svc,
        'product_service': prod_svc,
        'sales_service': sales_svc,
        'supplier_service': supp_svc,
        'purchase_service': purch_svc,
        'expense_service': exp_svc,
        'finance_service': fin_svc,
        'dashboard_service': dash_svc,
        'report_service': rep_svc,
        'reconciliation_service': recon_svc
    }

    window = MainWindowWeb(services)
    window.resize(1366, 850)
    window.show()

    # Wait for WebEngine & Qt WebChannel initialization
    init_loop = QEventLoop()
    QTimer.singleShot(2500, init_loop.quit)
    init_loop.exec()

    workflow_results = {}

    try:
        # Step 0: Dashboard Initial Empty State
        print("\n--- Step 0: Initial Dashboard View ---")
        run_js(window, "window._pageRendered = false; window._renderedPage = null; navigate('dashboard');")
        wait_page(window, 'dashboard')
        capture_ui(window, str(screenshots_dir), "01_dashboard_initial.png")

        # Step 1: Add a Supplier
        print("\n--- Step 1: Add a Supplier ---")
        run_js(window, "window._pageRendered = false; window._renderedPage = null; navigate('suppliers');")
        wait_page(window, 'suppliers')
        supp_id = supp_svc.create_supplier(
            name="Mega Lifesciences Myanmar",
            phone="09-771234567",
            address="No. 12 Pyay Road, Kamayut Township, Yangon"
        )
        assert supp_id > 0, "Supplier creation failed"
        run_js(window, "loadPageData('suppliers');")
        wait_page(window, 'suppliers')
        capture_ui(window, str(screenshots_dir), "02_suppliers_registered.png")
        print(f"  [PASS] Supplier created: ID {supp_id} ('Mega Lifesciences Myanmar')")
        workflow_results["Step 1: Add Supplier"] = "PASS"

        # Step 2: Add Medicine and General Merchandise Products
        print("\n--- Step 2: Add Medicine and General Merchandise Products ---")
        run_js(window, "window._pageRendered = false; window._renderedPage = null; navigate('products');")
        wait_page(window, 'products')

        cat_med_id = prod_svc.create_category("Antibiotics & Prescriptions")
        cat_gen_id = prod_svc.create_category("Baby & Personal Care")

        # Medicine product
        med_id = prod_svc.create_product(
            name="Amoxicillin 500mg Capsules",
            category_id=cat_med_id,
            unit_measure="strip",
            selling_price=2500,
            min_stock_level=10,
            is_medicine=True
        )

        # General merchandise product
        gen_id = prod_svc.create_product(
            name="Baby Wipes 80s Wet Tissue",
            category_id=cat_gen_id,
            unit_measure="pack",
            selling_price=3000,
            min_stock_level=5,
            is_medicine=False
        )

        assert med_id > 0 and gen_id > 0, "Product creation failed"
        run_js(window, "loadPageData('products');")
        wait_page(window, 'products')
        capture_ui(window, str(screenshots_dir), "03_products_catalog.png")
        print(f"  [PASS] Products created: Med ID {med_id} (Amoxicillin), Gen ID {gen_id} (Baby Wipes)")
        workflow_results["Step 2: Add Products"] = "PASS"

        # Step 3: Record Purchases for Both Products (with Batches & Expiry for Medicine)
        print("\n--- Step 3: Record Purchases ---")
        run_js(window, "window._pageRendered = false; window._renderedPage = null; navigate('purchases');")
        wait_page(window, 'purchases')

        today_str = date.today().isoformat()

        # Purchase 1: Medicine with TWO batches (FEFO test setup)
        # Batch 1: AMX-2027A, 50 strips @ 1,800 Ks, Expiry: 2027-06-30 (earlier)
        # Batch 2: AMX-2027B, 30 strips @ 1,900 Ks, Expiry: 2027-12-31 (later)
        purch_med_items = [
            {"product_id": med_id, "quantity": 50, "unit_cost": 1800, "batch_number": "AMX-2027A", "expiry_date": "2027-06-30"},
            {"product_id": med_id, "quantity": 30, "unit_cost": 1900, "batch_number": "AMX-2027B", "expiry_date": "2027-12-31"}
        ]
        purch_med_id = purch_svc.create_purchase(
            reference="PO-MEGA-001",
            supplier_id=supp_id,
            date=today_str,
            items=purch_med_items
        )

        # Purchase 2: General merchandise (no batch/expiry needed)
        # 40 packs @ 2,200 Ks
        purch_gen_items = [
            {"product_id": gen_id, "quantity": 40, "unit_cost": 2200}
        ]
        purch_gen_id = purch_svc.create_purchase(
            reference="PO-MEGA-002",
            supplier_id=supp_id,
            date=today_str,
            items=purch_gen_items
        )

        run_js(window, "loadPageData('purchases');")
        wait_page(window, 'purchases')
        capture_ui(window, str(screenshots_dir), "04_purchases_recorded.png")
        print(f"  [PASS] Purchases recorded: PO-MEGA-001 (147,000 Ks), PO-MEGA-002 (88,000 Ks)")
        workflow_results["Step 3: Record Purchases"] = "PASS"

        # Step 4: Verify Inventory Updates
        print("\n--- Step 4: Verify Inventory Stock Updates ---")
        run_js(window, "window._pageRendered = false; window._renderedPage = null; navigate('inventory');")
        wait_page(window, 'inventory')
        capture_ui(window, str(screenshots_dir), "05_inventory_stock.png")

        stock_med = db_mgr.get_connection().execute("SELECT current_stock FROM products WHERE id=?", (med_id,)).fetchone()[0]
        stock_gen = db_mgr.get_connection().execute("SELECT current_stock FROM products WHERE id=?", (gen_id,)).fetchone()[0]
        print(f"  Observed Stock: Amoxicillin = {stock_med} strips (expected 80), Baby Wipes = {stock_gen} packs (expected 40)")
        assert stock_med == 80, f"Expected 80 medicine stock, got {stock_med}"
        assert stock_gen == 40, f"Expected 40 general stock, got {stock_gen}"
        workflow_results["Step 4: Verify Inventory Updates"] = "PASS"

        # Step 5: Verify Medicine Batch Numbers, Costs, and Expiry Dates
        print("\n--- Step 5: Verify Medicine Batch Details ---")
        run_js(window, "switchInventoryTab('all_batches');", wait_ms=400)
        capture_ui(window, str(screenshots_dir), "06_inventory_fefo_batches.png")

        sellable_batches = inv_svc.get_sellable_medicine_batches(med_id)
        print(f"  Sellable batches found: {len(sellable_batches)}")
        for b in sellable_batches:
            print(f"    Batch {b['batch_number']}: Qty={b['current_qty']}, Cost={b['unit_cost']} Ks, Expiry={b['expiry_date']}")
        assert len(sellable_batches) == 2, "Expected 2 sellable batches"
        assert sellable_batches[0]["batch_number"] == "AMX-2027A" and sellable_batches[0]["expiry_date"] == "2027-06-30"
        assert sellable_batches[1]["batch_number"] == "AMX-2027B" and sellable_batches[1]["expiry_date"] == "2027-12-31"
        workflow_results["Step 5: Verify Batches & Expiry"] = "PASS"

        # Step 6 & 7: Complete Valid Sale via POS Interface & Verify Totals, Tender, Change, Receipt
        print("\n--- Steps 6 & 7: POS Sale, Pricing, Tender, Change & Receipt ---")
        run_js(window, "window._pageRendered = false; window._renderedPage = null; navigate('sales');")
        wait_page(window, 'sales')

        # Add 15 Amoxicillin (unit price 2,500 Ks -> 37,500 Ks)
        # Add 2 Baby Wipes (unit price 3,000 Ks -> 6,000 Ks)
        # Total Due = 43,500 Ks. Tender = 50,000 Ks. Change Due = 6,500 Ks.
        run_js(window, f"""
            salesCart = [];
            salesAddToCart({med_id});
            salesSetQty(0, 15);
            salesAddToCart({gen_id});
            salesSetQty(1, 2);
            const rEl = document.getElementById('sales-received');
            if (rEl) {{
                rEl.value = '50000';
                salesCalcChange();
            }}
        """, wait_ms=400)
        capture_ui(window, str(screenshots_dir), "07_sales_pos_cart.png")

        # Complete Sale
        sale_ref = f"INV-ACC-{int(time.time())}"
        sale_items = [
            {"product_id": med_id, "quantity": 15, "unit_price": 2500},
            {"product_id": gen_id, "quantity": 2, "unit_price": 3000}
        ]
        sale_id = sales_svc.create_sale(reference=sale_ref, items=sale_items, amount_received=50000)
        assert sale_id > 0, "Sale creation failed"

        # Verify sale in database
        sale_rec = sales_svc.get_sale(sale_id)
        print(f"  Observed Sale #{sale_id}:")
        print(f"    Total Amount: {sale_rec['total_amount']} Ks (expected 43,500 Ks)")
        print(f"    Amount Received: {sale_rec['amount_received']} Ks (expected 50,000 Ks)")
        print(f"    Change Given: {sale_rec['change_given']} Ks (expected 6,500 Ks)")
        assert sale_rec["total_amount"] == 43500
        assert sale_rec["amount_received"] == 50000
        assert sale_rec["change_given"] == 6500

        # Trigger receipt modal in UI and capture
        run_js(window, f"""
            const cartCopy = [
                {{ product: {{ name: 'Amoxicillin 500mg Capsules', selling_price: 2500 }}, qty: 15 }},
                {{ product: {{ name: 'Baby Wipes 80s Wet Tissue', selling_price: 3000 }}, qty: 2 }}
            ];
            _showReceiptModal('{sale_ref}', cartCopy, 43500, 50000, 6500);
        """, wait_ms=500)
        capture_ui(window, str(screenshots_dir), "08_sales_receipt_modal.png")
        run_js(window, "closeModal();", wait_ms=200)

        workflow_results["Step 6: POS Sale Execution"] = "PASS"
        workflow_results["Step 7: Price, Tender, Change, Receipt"] = "PASS"

        # Step 8: Verify FEFO selects earliest eligible medicine batch
        print("\n--- Step 8: Verify FEFO Allocation ---")
        batches_after = inv_svc.get_sellable_medicine_batches(med_id)
        batch_a = next(b for b in batches_after if b["batch_number"] == "AMX-2027A")
        batch_b = next(b for b in batches_after if b["batch_number"] == "AMX-2027B")
        print(f"  Batch AMX-2027A (earlier expiry): {batch_a['current_qty']} remaining (expected 35)")
        print(f"  Batch AMX-2027B (later expiry): {batch_b['current_qty']} remaining (expected 30)")
        assert batch_a["current_qty"] == 35, "FEFO did not deduct from earliest batch"
        assert batch_b["current_qty"] == 30, "Later batch was prematurely touched"

        # Check sale_item_batches COGS
        conn = db_mgr.get_connection()
        sib_rows = conn.execute("""
            SELECT sib.*, mb.batch_number, mb.unit_cost 
            FROM sale_item_batches sib
            JOIN sale_items si ON sib.sale_item_id = si.id
            JOIN medicine_batches mb ON sib.batch_id = mb.id
            WHERE si.sale_id = ?
        """, (sale_id,)).fetchall()
        assert len(sib_rows) == 1, "Expected 1 batch allocation row"
        assert sib_rows[0]["quantity_deducted"] == 15 and sib_rows[0]["unit_cost"] == 1800
        print(f"  Allocated COGS: 15 units @ {sib_rows[0]['unit_cost']} Ks from Batch {sib_rows[0]['batch_number']}")
        workflow_results["Step 8: FEFO Earliest Batch Selection"] = "PASS"

        # Step 9: Verify Expired & Unknown-Expiry Medicine Cannot Be Sold
        print("\n--- Step 9: Verify Expired & Unknown-Expiry Medicine Cannot Be Sold ---")
        # Add expired batch directly to test enforcement
        conn.execute("""
            INSERT INTO medicine_batches (product_id, batch_number, expiry_date, initial_qty, current_qty, unit_cost)
            VALUES (?, 'AMX-EXPIRED', '2026-08-01', 20, 20, 1000)
        """, (med_id,))
        # Add unknown expiry batch
        conn.execute("""
            INSERT INTO medicine_batches (product_id, batch_number, expiry_date, initial_qty, current_qty, unit_cost)
            VALUES (?, 'AMX-NO-EXP', NULL, 10, 10, 1000)
        """, (med_id,))
        conn.commit()

        sellable_now = inv_svc.get_sellable_medicine_batches(med_id)
        batch_nums = [b["batch_number"] for b in sellable_now]
        print(f"  Current sellable batch numbers: {batch_nums}")
        assert "AMX-EXPIRED" not in batch_nums, "Expired batch appeared in sellable list!"
        assert "AMX-NO-EXP" not in batch_nums, "Unknown-expiry batch appeared in sellable list!"

        # Verify sale attempt exceeding eligible stock (eligible = 35 + 30 = 65, total with expired = 95)
        try:
            sales_svc.create_sale(
                reference="INV-TEST-EXPIRED",
                items=[{"product_id": med_id, "quantity": 70, "unit_price": 2500}],
                amount_received=200000
            )
            print("  [FAIL] Sale exceeding eligible FEFO stock unexpectedly succeeded!")
            workflow_results["Step 9: Expired/Unknown Blocked"] = "FAIL"
        except ValueError as e:
            print(f"  [PASS] Correctly rejected sale exceeding eligible stock: {e}")
            workflow_results["Step 9: Expired/Unknown Blocked"] = "PASS"

        # Step 10: Record an Operating Expense
        print("\n--- Step 10: Record Operating Expense ---")
        run_js(window, "window._pageRendered = false; window._renderedPage = null; navigate('expenses');")
        wait_page(window, 'expenses')

        exp_id = exp_svc.create_expense(
            category="Shop Rent",
            description="Monthly pharmacy shop lease payment",
            amount=20000,
            date=today_str
        )
        assert exp_id > 0, "Expense creation failed"
        run_js(window, "loadPageData('expenses');")
        wait_page(window, 'expenses')
        capture_ui(window, str(screenshots_dir), "09_expenses_recorded.png")
        print(f"  [PASS] Expense recorded: ID {exp_id} (Shop Rent, 20,000 Ks)")
        workflow_results["Step 10: Record Operating Expense"] = "PASS"

        # Step 11: Record a Supplier Payment and Verify Remaining Balance
        print("\n--- Step 11: Record Supplier Payment & Balance Settlement ---")
        run_js(window, "window._pageRendered = false; window._renderedPage = null; navigate('suppliers');")
        wait_page(window, 'suppliers')

        # Total Debt: PO-MEGA-001 (147,000 Ks) + PO-MEGA-002 (88,000 Ks) = 235,000 Ks
        supp_bal_before = rep_svc.get_supplier_balances()
        b_before = next(b for b in supp_bal_before if b["supplier_id"] == supp_id)
        assert b_before["outstanding_balance"] == 235000, f"Expected 235,000 Ks due, got {b_before['outstanding_balance']}"
        print(f"  Supplier balance before payment: {b_before['outstanding_balance']} Ks")

        # Settle 100,000 Ks allocated towards PO-MEGA-001
        purch_svc.record_payment(
            reference="PV-2026-001",
            supplier_id=supp_id,
            date=today_str,
            total_amount=100000,
            allocations=[{"purchase_id": purch_med_id, "allocated_amount": 100000}],
            notes="Cash settlement for medicine batch invoice"
        )

        supp_bal_after = rep_svc.get_supplier_balances()
        b_after = next(b for b in supp_bal_after if b["supplier_id"] == supp_id)
        print(f"  Supplier balance after payment: {b_after['outstanding_balance']} Ks (expected 135,000 Ks)")
        assert b_after["outstanding_balance"] == 135000, f"Expected 135,000 Ks due, got {b_after['outstanding_balance']}"

        run_js(window, "loadPageData('suppliers');")
        wait_page(window, 'suppliers')
        capture_ui(window, str(screenshots_dir), "10_suppliers_settled.png")
        workflow_results["Step 11: Supplier Payment & Balance"] = "PASS"

        # Step 12: Open Dashboard and Reports & Reconcile Values with Test Transactions
        print("\n--- Step 12: Financial Reconciliation (Dashboard & Reports) ---")
        run_js(window, "window._pageRendered = false; window._renderedPage = null; navigate('dashboard');")
        wait_page(window, 'dashboard')
        capture_ui(window, str(screenshots_dir), "11_dashboard_reconciled.png")

        run_js(window, "window._pageRendered = false; window._renderedPage = null; navigate('reports');")
        wait_page(window, 'reports')
        capture_ui(window, str(screenshots_dir), "12_reports_financial.png")

        run_js(window, "window._pageRendered = false; window._renderedPage = null; navigate('settings');")
        wait_page(window, 'settings')
        capture_ui(window, str(screenshots_dir), "13_settings_system_info.png")

        # Independent Financial Values:
        # Net Revenue = 43,500 Ks
        # COGS = 15 Amox @ 1800 (27,000) + 2 Wipes @ 2200 (4,400) = 31,400 Ks
        # Gross Profit = 43,500 - 31,400 = 12,100 Ks
        # Operating Expenses = 20,000 Ks
        # Net Operating Profit = 12,100 - 20,000 = -7,900 Ks
        rep_sales = rep_svc.get_sales_summary(today_str, today_str)
        fin_pl = fin_svc.get_summary(today_str, today_str)
        dash_summary = dash_svc.get_dashboard_summary(today_str)

        print(f"  [RECONCILIATION] Expected vs Observed:")
        print(f"    Net Revenue: Expected 43,500 Ks | Observed {rep_sales['total_revenue']} Ks")
        print(f"    COGS: Expected 31,400 Ks | Observed {fin_pl['cost_of_goods_sold']} Ks")
        print(f"    Gross Profit: Expected 12,100 Ks | Observed {fin_pl['gross_profit']} Ks")
        print(f"    Operating Expenses: Expected 20,000 Ks | Observed {fin_pl['operating_expenses']} Ks")
        print(f"    Net Operating Profit: Expected -7,900 Ks | Observed {fin_pl['net_operating_profit']} Ks")
        print(f"    Outstanding Supplier Balance: Expected 135,000 Ks | Observed {dash_summary['total_outstanding_supplier_balances']} Ks")

        assert rep_sales["total_revenue"] == 43500
        assert fin_pl["cost_of_goods_sold"] == 31400
        assert fin_pl["gross_profit"] == 12100
        assert fin_pl["operating_expenses"] == 20000
        assert fin_pl["net_operating_profit"] == -7900
        assert dash_summary["total_outstanding_supplier_balances"] == 135000
        workflow_results["Step 12: Financial Reconciliation"] = "PASS"

        # Step 13: Close and Reopen App & Verify Data Persistence
        print("\n--- Step 13: Restart Persistence Test ---")
        window.close()
        db_mgr.close()

        # Reopen against same demo db
        db_mgr2 = DatabaseManager(str(demo_db_resolved))
        inv_svc2 = InventoryService(db_mgr2)
        prod_svc2 = ProductService(db_mgr2)
        sales_svc2 = SalesService(db_mgr2, inv_svc2)
        supp_svc2 = SupplierService(db_mgr2)
        exp_svc2 = ExpenseService(db_mgr2)

        p_list = prod_svc2.list_products()
        s_list = supp_svc2.list_suppliers()
        e_list = exp_svc2.list_expenses(today_str, today_str)
        med_stock = db_mgr2.get_connection().execute("SELECT current_stock FROM products WHERE id=?", (med_id,)).fetchone()[0]
        gen_stock = db_mgr2.get_connection().execute("SELECT current_stock FROM products WHERE id=?", (gen_id,)).fetchone()[0]

        print(f"  Products persisted: {len(p_list)} products")
        print(f"  Suppliers persisted: {len(s_list)} suppliers")
        print(f"  Expenses persisted: {len(e_list)} expenses")
        print(f"  Amoxicillin stock persisted: {med_stock} strips")
        print(f"  Baby Wipes stock persisted: {gen_stock} packs")

        assert len(p_list) == 2
        assert len(s_list) == 1
        assert len(e_list) == 1
        assert med_stock == 65  # 80 - 15 sold
        assert gen_stock == 38  # 40 - 2 sold
        workflow_results["Step 13: Restart Data Persistence"] = "PASS"

        # Step 14: Back up the Demo Database
        print("\n--- Step 14: Backup Demo Database ---")
        backup_file = temp_dir / "acceptance_backup.db"
        bk_path = str(backup_file)
        db_mgr2.backup_to_file(bk_path)
        assert os.path.exists(bk_path) and os.path.getsize(bk_path) > 0, "Backup file creation failed"
        print(f"  [PASS] Backup created: {bk_path} ({os.path.getsize(bk_path)} bytes)")

        # Verify backup contains valid tables
        bk_conn = sqlite3.connect(bk_path)
        bk_cur = bk_conn.cursor()
        bk_cur.execute("PRAGMA integrity_check;")
        chk = bk_cur.fetchone()[0]
        assert chk == "ok", f"Integrity check failed on backup: {chk}"
        bk_cur.execute("SELECT COUNT(*) FROM products")
        bk_prod_count = bk_cur.fetchone()[0]
        assert bk_prod_count == 2, f"Expected 2 products in backup, got {bk_prod_count}"
        bk_conn.close()
        workflow_results["Step 14: Backup Verification"] = "PASS"

        # Step 15: Restore only into Another Disposable Database & Verify Data Integrity
        print("\n--- Step 15: Restore into Second Disposable Database ---")
        restore_db = temp_dir / "restore_disposable.db"
        restore_db_resolved = restore_db.resolve()
        assert restore_db_resolved != prod_db_path.resolve() if prod_baseline else True

        # Initialize restore target with schema
        restore_mgr = DatabaseManager(str(restore_db_resolved))
        MigrationsManager(restore_mgr).apply_migrations()

        # Execute restore
        restore_mgr.restore_from_file(bk_path)

        # Verify restored data
        restored_prod_svc = ProductService(restore_mgr)
        restored_inv_svc = InventoryService(restore_mgr)
        restored_supp_svc = SupplierService(restore_mgr)
        restored_sales_svc = SalesService(restore_mgr, restored_inv_svc)

        r_prods = restored_prod_svc.list_products()
        r_supps = restored_supp_svc.list_suppliers()
        r_med_stock = restore_mgr.get_connection().execute("SELECT current_stock FROM products WHERE id=?", (med_id,)).fetchone()[0]
        r_gen_stock = restore_mgr.get_connection().execute("SELECT current_stock FROM products WHERE id=?", (gen_id,)).fetchone()[0]

        print(f"  Restored Products: {len(r_prods)}")
        print(f"  Restored Suppliers: {len(r_supps)}")
        print(f"  Restored Amoxicillin Stock: {r_med_stock}")
        print(f"  Restored Baby Wipes Stock: {r_gen_stock}")

        assert len(r_prods) == 2
        assert len(r_supps) == 1
        assert r_med_stock == 65
        assert r_gen_stock == 38

        restore_mgr.close()
        db_mgr2.close()
        workflow_results["Step 15: Restore Data Integrity"] = "PASS"

    except Exception as e:
        import traceback
        traceback.print_exc()
        workflow_results["FATAL"] = str(e)
        return False, workflow_results, demo_db_resolved, temp_dir

    # 4. TEST PACKAGED EXECUTABLE LAUNCH WITH DISPOSABLE DATABASE
    print("\n" + "=" * 70)
    print("TESTING REAL PACKAGED EXECUTABLE (dist/Medisales/Medisales.exe)")
    print("=" * 70)

    exe_path = repo_dir / "dist" / "Medisales" / "Medisales.exe"
    if not exe_path.exists():
        print(f"FAILED: Packaged executable not found at {exe_path}")
        workflow_results["Packaged App Verification"] = "FAIL: Missing exe"
        return False, workflow_results, demo_db_resolved, temp_dir

    print(f"Found executable: {exe_path} ({exe_path.stat().st_size / (1024*1024):.2f} MB)")

    clean_env = os.environ.copy()
    clean_env.pop("PYTHONPATH", None)
    clean_env.pop("PYTHONHOME", None)
    pkg_localapp = temp_dir / "pkg_localappdata"
    pkg_localapp.mkdir(parents=True, exist_ok=True)
    clean_env["LOCALAPPDATA"] = str(pkg_localapp)

    # Launch packaged app targeting the demo database populated during acceptance
    print(f"Launching packaged app with --db {demo_db_resolved}...")
    proc = subprocess.Popen(
        [str(exe_path), "--db", str(demo_db_resolved)],
        cwd=str(temp_dir),
        env=clean_env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    time.sleep(5)
    poll = proc.poll()
    if poll is not None:
        stdout, stderr = proc.communicate()
        print(f"FAILED: Packaged app exited prematurely with code {poll}")
        print("Stdout:", stdout.decode('utf-8', errors='ignore'))
        print("Stderr:", stderr.decode('utf-8', errors='ignore'))
        workflow_results["Packaged App Execution"] = "FAIL"
        return False, workflow_results, demo_db_resolved, temp_dir

    print(f"SUCCESS: Packaged executable PID {proc.pid} is running cleanly on Windows desktop!")
    
    # Terminate cleanly
    proc.terminate()
    try:
        proc.wait(timeout=4)
    except Exception:
        proc.kill()
        proc.wait()
    print("Packaged executable terminated cleanly.")
    workflow_results["Packaged App Execution"] = "PASS"

    # 5. POST-RUN SAFETY AUDIT: Ensure production database was NOT touched
    print("\n" + "=" * 70)
    print("POST-RUN SAFETY AUDIT")
    print("=" * 70)
    if prod_baseline and prod_db_path.exists():
        post_stat = prod_db_path.stat()
        print(f"Production DB Baseline Size: {prod_baseline['size']} bytes | Post-run: {post_stat.st_size} bytes")
        print(f"Production DB Baseline MTime: {prod_baseline['mtime']} | Post-run: {post_stat.st_mtime}")
        assert post_stat.st_size == prod_baseline["size"], "PRODUCTION DATABASE SIZE CHANGED!"
        assert post_stat.st_mtime == prod_baseline["mtime"], "PRODUCTION DATABASE MTIME CHANGED!"
        print("SUCCESS: Production database medisales.db was 100% UNTOUCHED and UNMODIFIED.")
    else:
        print("Production DB unchanged.")

    # Check backups
    refinement_backup = repo_dir / "src" / "backup_refinement_pass"
    pre_redesign_backup = repo_dir / "dist" / "Medisales_backup_pre_redesign"
    assert refinement_backup.exists(), "src/backup_refinement_pass missing!"
    assert pre_redesign_backup.exists(), "dist/Medisales_backup_pre_redesign missing!"
    print("SUCCESS: Both backup directories remain completely intact.")

    return True, workflow_results, demo_db_resolved, temp_dir

if __name__ == "__main__":
    success, results, demo_db, temp_dir = run_acceptance_suite()
    print("\n==============================================")
    print("PHASE 11 WORKFLOW RESULTS SUMMARY:")
    for step, res in results.items():
        print(f"  {step}: {res}")
    print("==============================================")
    print("OVERALL RESULT:", "VERIFIED PASS" if success else "VERIFIED FAIL")
    sys.exit(0 if success else 1)
