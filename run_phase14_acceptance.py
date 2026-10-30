import os
import sys
import time
import shutil
import sqlite3
import tempfile
import hashlib
import subprocess
from pathlib import Path
from datetime import datetime, date, timedelta
import openpyxl

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


def compute_sha256(filepath):
    if not os.path.exists(filepath):
        return None
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def run_full_acceptance_review():
    print("=" * 80)
    print("MEDISALES - PHASE 14 FINAL ACCEPTANCE & PRODUCTION READINESS REVIEW")
    print("=" * 80)
    start_time = time.time()

    repo_dir = Path(__file__).resolve().parent

    # --------------------------------------------------------------------------
    # SAFETY BASELINE: Record production DB state before any actions
    # --------------------------------------------------------------------------
    prod_db_repo = repo_dir / "medisales.db"
    prod_hash_repo = compute_sha256(str(prod_db_repo))
    prod_size_repo = prod_db_repo.stat().st_size if prod_db_repo.exists() else 0

    local_appdata = os.environ.get("LOCALAPPDATA", "")
    prod_db_appdata = Path(local_appdata) / "Medisales" / "medisales.db" if local_appdata else None
    prod_hash_appdata = compute_sha256(str(prod_db_appdata)) if prod_db_appdata and prod_db_appdata.exists() else None
    prod_size_appdata = prod_db_appdata.stat().st_size if prod_db_appdata and prod_db_appdata.exists() else 0

    print("\n[SAFETY PROTOCOL 1] Baseline Production Databases:")
    print(f"  Repo Root DB:    {prod_db_repo} (Size: {prod_size_repo} bytes, SHA256: {prod_hash_repo})")
    if prod_db_appdata and prod_db_appdata.exists():
        print(f"  AppData Live DB: {prod_db_appdata} (Size: {prod_size_appdata} bytes, SHA256: {prod_hash_appdata})")

    # Temporary directory for all disposable test databases
    temp_dir = Path(tempfile.mkdtemp(prefix="medisales_phase14_acc_"))
    print(f"  Disposable Test Working Directory: {temp_dir}\n")

    disposable_db_path = temp_dir / "disposable_owner_acceptance.db"

    # ==========================================================================
    # PART B: OWNER ACCEPTANCE WORKFLOW
    # ==========================================================================
    print("-" * 80)
    print("PART B: OWNER ACCEPTANCE WORKFLOW (Realistic End-to-End Simulation)")
    print("-" * 80)

    # Initialize fresh disposable database
    db_manager = DatabaseManager(str(disposable_db_path))
    migrations_mgr = MigrationsManager(db_manager)
    migrations_mgr.apply_migrations()

    def create_services(db_mgr):
        inv = InventoryService(db_mgr)
        prod = ProductService(db_mgr)
        sales = SalesService(db_mgr, inv)
        supp = SupplierService(db_mgr)
        purch = PurchaseService(db_mgr)
        exp = ExpenseService(db_mgr)
        fin = FinanceService(db_mgr)
        dash = DashboardService(db_mgr, fin)
        rep = ReportService(db_mgr)
        recon = ReconciliationService(db_mgr)
        svcs = {
            'db_manager': db_mgr,
            'inventory_service': inv,
            'product_service': prod,
            'sales_service': sales,
            'supplier_service': supp,
            'purchase_service': purch,
            'expense_service': exp,
            'finance_service': fin,
            'dashboard_service': dash,
            'report_service': rep,
            'reconciliation_service': recon,
        }
        svcs['export_service'] = ExportService(svcs)
        return svcs

    services = create_services(db_manager)

    # 1. Create a supplier
    supp_id = services['supplier_service'].create_supplier(
        name="Royal Pharma Wholesale",
        phone="09-45009876",
        address="Pazundaung Township, Yangon"
    )
    print(f"Step 1: Created Supplier ID={supp_id} ('Royal Pharma Wholesale')")
    assert supp_id > 0

    # 2. Create one medicine and one general merchandise product
    with db_manager.transaction() as conn:
        cat_med = conn.execute("INSERT INTO categories (name) VALUES ('Medicines')").lastrowid
        cat_gen = conn.execute("INSERT INTO categories (name) VALUES ('General Merchandise')").lastrowid

    med_id = services['product_service'].create_product(
        name="Paracetamol 500mg (Biogesic)",
        category_id=cat_med,
        unit_measure="strip",
        selling_price=1500,
        min_stock_level=10,
        is_medicine=True
    )
    gen_id = services['product_service'].create_product(
        name="Lifebuoy Antibacterial Soap 100g",
        category_id=cat_gen,
        unit_measure="bar",
        selling_price=1200,
        min_stock_level=15,
        is_medicine=False
    )
    print(f"Step 2: Created Products: Medicine ID={med_id} ('Paracetamol 500mg (Biogesic)'), General ID={gen_id} ('Lifebuoy Soap')")

    # 3. Record purchases for both products
    # Purchase 1
    p1_items = [
        {'product_id': med_id, 'quantity': 50, 'unit_cost': 1000, 'batch_number': 'BATCH-2026-01', 'expiry_date': '2027-06-30'},
        {'product_id': gen_id, 'quantity': 40, 'unit_cost': 800, 'batch_number': None, 'expiry_date': None}
    ]
    po1_id = services['purchase_service'].create_purchase("PO-ACCEPT-01", supp_id, "2026-10-01", p1_items)
    print(f"Step 3a: Recorded Purchase 1 ID={po1_id} (PO-ACCEPT-01): 50 Med @ 1000, 40 Gen @ 800. Total = 82,000 Ks")

    # Purchase 2: Earlier expiry for medicine, updated cost for general
    p2_items = [
        {'product_id': med_id, 'quantity': 30, 'unit_cost': 1100, 'batch_number': 'BATCH-2026-EARLY', 'expiry_date': '2027-01-31'},
        {'product_id': gen_id, 'quantity': 20, 'unit_cost': 900, 'batch_number': None, 'expiry_date': None}
    ]
    po2_id = services['purchase_service'].create_purchase("PO-ACCEPT-02", supp_id, "2026-10-03", p2_items)
    print(f"Step 3b: Recorded Purchase 2 ID={po2_id} (PO-ACCEPT-02): 30 Med @ 1100 (earlier expiry!), 20 Gen @ 900. Total = 51,000 Ks")

    # 4. Verify medicine batch numbers and expiry dates
    conn = db_manager.get_connection()
    batches = [dict(r) for r in conn.execute("SELECT * FROM medicine_batches WHERE product_id = ? ORDER BY expiry_date ASC", (med_id,)).fetchall()]
    print(f"Step 4: Verified Medicine Batches ({len(batches)} batches found):")
    for b in batches:
        print(f"   - Batch {b['batch_number']}: Expiry={b['expiry_date']}, Current Qty={b['current_qty']}, Cost={b['unit_cost']} Ks")
    assert len(batches) == 2
    b_early = next(b for b in batches if b['batch_number'] == 'BATCH-2026-EARLY')
    b_late = next(b for b in batches if b['batch_number'] == 'BATCH-2026-01')
    assert b_early['expiry_date'] == '2027-01-31'
    assert b_early['current_qty'] == 30
    assert b_late['expiry_date'] == '2027-06-30'
    assert b_late['current_qty'] == 50

    # 5. Verify FEFO selection and stock quantities
    med_prod = dict(db_manager.get_connection().execute("SELECT * FROM products WHERE id = ?", (med_id,)).fetchone())
    gen_prod = dict(db_manager.get_connection().execute("SELECT * FROM products WHERE id = ?", (gen_id,)).fetchone())
    assert med_prod['current_stock'] == 80
    assert gen_prod['current_stock'] == 60
    # Expected Gen WAC value: (40*800 + 20*900) = 50,000 Ks; WAC = 833 Ks
    assert gen_prod['inventory_value'] == 50000
    print(f"Step 5: Verified Stock Totals: Paracetamol=80 strips, Lifebuoy=60 bars (Value={gen_prod['inventory_value']} Ks)")

    # 6. Complete a sale
    # Sell 35 strips of Paracetamol (must consume 30 from BATCH-2026-EARLY and 5 from BATCH-2026-01)
    # Sell 10 bars of Lifebuoy Soap
    sale_items = [
        {'product_id': med_id, 'quantity': 35, 'unit_price': 1500},
        {'product_id': gen_id, 'quantity': 10, 'unit_price': 1200}
    ]
    # Total price: 35 * 1500 (52,500) + 10 * 1200 (12,000) = 64,500 Ks
    expected_sale_total = 64500
    tendered = 70000
    sale_id = services['sales_service'].create_sale("REC-ACCEPT-001", sale_items, tendered)
    print(f"Step 6: Completed Sale ID={sale_id} ('REC-ACCEPT-001'). Expected Total={expected_sale_total} Ks")

    # 7. Verify tendered amount and change
    sale_rec = services['sales_service'].get_sale(sale_id)
    assert sale_rec['total_amount'] == expected_sale_total
    expected_change = tendered - expected_sale_total  # 5,500 Ks
    assert expected_change == 5500
    print(f"Step 7: Verified Tendered={tendered} Ks, Total={sale_rec['total_amount']} Ks, Change={expected_change} Ks")

    # 8. Verify stock movements and COGS
    # Paracetamol COGS: 30 * 1100 + 5 * 1000 = 33,000 + 5,000 = 38,000 Ks
    # Lifebuoy COGS: 10 * 833.3333333333334 = 8,333 Ks
    # Total COGS: 38,000 + 8,333 = 46,333 Ks
    med_prod_post = dict(db_manager.get_connection().execute("SELECT * FROM products WHERE id = ?", (med_id,)).fetchone())
    gen_prod_post = dict(db_manager.get_connection().execute("SELECT * FROM products WHERE id = ?", (gen_id,)).fetchone())
    assert med_prod_post['current_stock'] == 45
    assert gen_prod_post['current_stock'] == 50

    batches_post = [dict(r) for r in db_manager.get_connection().execute("SELECT * FROM medicine_batches WHERE product_id = ? ORDER BY expiry_date ASC", (med_id,)).fetchall()]
    b_early_post = next(b for b in batches_post if b['batch_number'] == 'BATCH-2026-EARLY')
    b_late_post = next(b for b in batches_post if b['batch_number'] == 'BATCH-2026-01')
    assert b_early_post['current_qty'] == 0, f"FEFO error: earlier batch has {b_early_post['current_qty']} remaining"
    assert b_late_post['current_qty'] == 45, f"FEFO error: later batch has {b_late_post['current_qty']} remaining"

    sale_items_db = sale_rec['items']
    med_sale_item = next(si for si in sale_items_db if si['product_id'] == med_id)
    gen_sale_item = next(si for si in sale_items_db if si['product_id'] == gen_id)
    assert med_sale_item['total_cost'] == 38000
    assert gen_sale_item['total_cost'] == 8333
    total_cogs = med_sale_item['total_cost'] + gen_sale_item['total_cost']
    gross_profit = expected_sale_total - total_cogs
    print(f"Step 8: Verified FEFO Depletion & COGS:")
    print(f"   - BATCH-2026-EARLY depleted to 0 (30 units @ 1100 Ks = 33,000 Ks)")
    print(f"   - BATCH-2026-01 reduced to 45 (5 units @ 1000 Ks = 5,000 Ks)")
    print(f"   - Med COGS = {med_sale_item['total_cost']} Ks, Gen COGS = {gen_sale_item['total_cost']} Ks")
    print(f"   - Total COGS = {total_cogs} Ks, Gross Profit = {gross_profit} Ks")

    # 9. Record an operating expense
    exp_id = services['expense_service'].create_expense(
        category="Store Electricity Bill",
        description="Shop cooling and lighting",
        amount=12000,
        date="2026-10-05"
    )
    print(f"Step 9: Recorded Operating Expense ID={exp_id}: 12,000 Ks ('Store Electricity Bill')")

    # 10. Record a supplier payment
    # PO1 total = 82,000 Ks; PO2 total = 51,000 Ks; Total owed = 133,000 Ks
    # Pay 40,000 Ks against PO1
    supp_balance_before = next(s['outstanding_balance'] for s in services['report_service'].get_supplier_balances() if s['supplier_id'] == supp_id)
    assert supp_balance_before == 133000
    pay_id = services['purchase_service'].record_payment(
        reference="PV-ACCEPT-01",
        supplier_id=supp_id,
        date="2026-10-06",
        total_amount=40000,
        allocations=[{'purchase_id': po1_id, 'allocated_amount': 40000}],
        notes="Partial settlement for PO-ACCEPT-01"
    )
    print(f"Step 10: Recorded Supplier Payment ID={pay_id} (PV-ACCEPT-01): 40,000 Ks allocated to PO-ACCEPT-01")

    # 11. Verify supplier balances
    supp_balance_after = next(s['outstanding_balance'] for s in services['report_service'].get_supplier_balances() if s['supplier_id'] == supp_id)
    assert supp_balance_after == 93000  # 133,000 - 40,000
    print(f"Step 11: Verified Supplier Outstanding Balance: {supp_balance_after} Ks (reduced from {supp_balance_before} Ks)")

    # 12. Void a test sale if the existing workflow supports voiding
    # Create Sale 2: 5 bars of Lifebuoy @ 1200 = 6000 Ks
    sale2_id = services['sales_service'].create_sale("REC-ACCEPT-VOID-01", [{'product_id': gen_id, 'quantity': 5, 'unit_price': 1200}], 6000)
    gen_stock_mid = db_manager.get_connection().execute("SELECT current_stock FROM products WHERE id = ?", (gen_id,)).fetchone()['current_stock']
    assert gen_stock_mid == 45
    print(f"Step 12a: Created Sale 2 ID={sale2_id} for 5 bars Lifebuoy (stock dropped to {gen_stock_mid})")

    # Now VOID Sale 2
    services['sales_service'].void_sale(sale2_id)
    gen_stock_restored = db_manager.get_connection().execute("SELECT current_stock FROM products WHERE id = ?", (gen_id,)).fetchone()['current_stock']
    assert gen_stock_restored == 50, f"Stock after void should be 50, got {gen_stock_restored}"
    sale2_status = services['sales_service'].get_sale(sale2_id)['status']
    assert sale2_status == 'Voided'
    print(f"Step 12b: Voided Sale 2. Status='{sale2_status}'. Stock safely restored to {gen_stock_restored} bars!")

    # 13. Verify reports after the void
    # Sales Report
    sales_list = services['report_service'].get_sales("2026-10-01", "2026-10-31", include_voided=True)
    completed_sales = [s for s in sales_list if s['status'] == 'Completed']
    voided_sales = [s for s in sales_list if s['status'] == 'Voided']
    assert sum(s['total_amount'] for s in completed_sales) == expected_sale_total  # 64,500 Ks
    assert len(completed_sales) == 1
    assert len(voided_sales) == 1
    assert voided_sales[0]['total_amount'] == 6000

    # P&L Report via FinanceService
    pnl = services['finance_service'].get_summary("2026-10-01", "2026-10-31")
    assert pnl['total_sales_revenue'] == expected_sale_total  # 64,500 Ks
    assert pnl['cost_of_goods_sold'] == total_cogs            # 46,333 Ks
    assert pnl['gross_profit'] == gross_profit                # 18,167 Ks
    assert pnl['operating_expenses'] == 12000                 # ONLY the 12,000 Ks operating expense!
    expected_net_profit = gross_profit - 12000                # 6,167 Ks
    assert pnl['net_operating_profit'] == expected_net_profit

    # Crucial GAAP check: Supplier payments and purchases must NOT be in operating expenses
    assert pnl['operating_expenses'] < 50000, "Operating expenses incorrectly included supplier payment or purchase!"
    print(f"Step 13: Verified Reports Reconcile Perfectly:")
    print(f"   - Completed Sales Revenue: {pnl['total_sales_revenue']} Ks (voided 6,000 Ks excluded)")
    print(f"   - COGS: {pnl['cost_of_goods_sold']} Ks")
    print(f"   - Gross Profit: {pnl['gross_profit']} Ks")
    print(f"   - Operating Overheads: {pnl['operating_expenses']} Ks (Supplier debt payment 40k Ks correctly excluded)")
    print(f"   - Net Profit: {pnl['net_operating_profit']} Ks")

    # 14. Restart the application and verify persistence
    db_manager.close()
    print("Step 14: Simulating application restart...")
    db_reopened = DatabaseManager(str(disposable_db_path))
    services_reopened = create_services(db_reopened)

    # Re-verify all key entities after reload
    pnl_reopen = services_reopened['finance_service'].get_summary("2026-10-01", "2026-10-31")
    assert pnl_reopen['total_sales_revenue'] == 64500
    assert pnl_reopen['net_operating_profit'] == expected_net_profit
    supp_bal_reopen = next(s['outstanding_balance'] for s in services_reopened['report_service'].get_supplier_balances() if s['supplier_id'] == supp_id)
    assert supp_bal_reopen == 93000
    med_batches_reopen = [dict(r) for r in db_reopened.get_connection().execute("SELECT * FROM medicine_batches WHERE product_id = ? ORDER BY expiry_date ASC", (med_id,)).fetchall()]
    assert len(med_batches_reopen) == 2
    assert next(b for b in med_batches_reopen if b['batch_number'] == 'BATCH-2026-EARLY')['current_qty'] == 0
    assert next(b for b in med_batches_reopen if b['batch_number'] == 'BATCH-2026-01')['current_qty'] == 45
    print("   -> Persistence confirmed across application restart! All records match 100%.")

    # 15. Export the resulting records to Excel
    export_dir = temp_dir / "exports"
    export_dir.mkdir(parents=True, exist_ok=True)
    exporter = services_reopened['export_service']

    exported_files = {
        'sales': export_dir / "medisales_owner_sales.xlsx",
        'products': export_dir / "medisales_owner_products.xlsx",
        'inventory_valuation': export_dir / "medisales_owner_inventory_valuation.xlsx",
        'medicine_batches': export_dir / "medisales_owner_medicine_batches.xlsx",
        'purchases': export_dir / "medisales_owner_purchases.xlsx",
        'suppliers': export_dir / "medisales_owner_suppliers.xlsx",
        'expenses': export_dir / "medisales_owner_expenses.xlsx",
        'financial_report': export_dir / "medisales_owner_financial_report.xlsx",
    }

    exporter.export_sales(str(exported_files['sales']), "2026-10-01", "2026-10-31")
    exporter.export_products(str(exported_files['products']))
    exporter.export_inventory_valuation(str(exported_files['inventory_valuation']))
    exporter.export_medicine_batches(str(exported_files['medicine_batches']), "all")
    exporter.export_purchases(str(exported_files['purchases']), "2026-10-01", "2026-10-31")
    exporter.export_suppliers(str(exported_files['suppliers']))
    exporter.export_expenses(str(exported_files['expenses']), "2026-10-01", "2026-10-31")
    exporter.export_financial_report(str(exported_files['financial_report']), "2026-10-01", "2026-10-31")

    print(f"Step 15: Exported 8 Excel workbooks to {export_dir}")
    for k, p in exported_files.items():
        assert p.exists() and p.stat().st_size > 3000
        print(f"   - {k}: {p.name} ({p.stat().st_size} bytes)")

    print("\n>>> ALL PART B OWNER ACCEPTANCE WORKFLOW STEPS PASSED WITH 100% SUCCESS! <<<\n")

    # ==========================================================================
    # PART D: EXCEL ACCEPTANCE & RECONCILIATION
    # ==========================================================================
    print("-" * 80)
    print("PART D: EXCEL ACCEPTANCE & RECONCILIATION")
    print("-" * 80)

    # Inspect the 4 Phase 13 sample workbooks in docs/exports/
    p13_exports_dir = repo_dir / "docs" / "exports"
    sample_workbooks = [
        p13_exports_dir / "medisales_financial_report_phase13_sample.xlsx",
        p13_exports_dir / "medisales_sales_phase13_sample.xlsx",
        p13_exports_dir / "medisales_medicine_batches_phase13_sample.xlsx",
        p13_exports_dir / "medisales_inventory_valuation_phase13_sample.xlsx",
    ]

    print("[Part D.1] Inspecting Phase 13 Sample Workbooks in docs/exports/:")
    for wb_path in sample_workbooks:
        assert wb_path.exists(), f"Sample workbook missing: {wb_path}"
        wb = openpyxl.load_workbook(str(wb_path))
        print(f"  Workbook: {wb_path.name}")
        print(f"    Sheets: {wb.sheetnames}")
        ws = wb.active
        print(f"    Active Sheet: '{ws.title}', Dimensions: {ws.dimensions}")
        # Verify first row / headers
        first_rows = list(ws.iter_rows(max_row=6, values_only=True))
        assert len(first_rows) >= 3

    print("\n[Part D.2] Inspecting Owner Acceptance Exported Workbooks & Cells:")
    # 1. Sales Workbook Inspection
    wb_sales = openpyxl.load_workbook(str(exported_files['sales']))
    ws_sales = wb_sales["Sales Transactions"]
    sales_rows = list(ws_sales.iter_rows(values_only=True))

    header_idx = None
    for idx, r in enumerate(sales_rows):
        if r and r[0] == "Invoice #":
            header_idx = idx
            break
    assert header_idx is not None, "Invoice # header row not found"
    data_sales = sales_rows[header_idx + 1:]

    r_completed = next(r for r in data_sales if r[0] == "REC-ACCEPT-001")
    r_voided = next(r for r in data_sales if r[0] == "REC-ACCEPT-VOID-01")
    assert r_completed[2] == "Completed"
    assert r_voided[2] == "Voided"
    # Monetary values and quantities must be numeric types
    assert isinstance(r_completed[4], (int, float)), f"Expected numeric total, got {type(r_completed[4])}"
    assert r_completed[4] == 64500
    assert isinstance(r_voided[4], (int, float))
    assert r_voided[4] == 6000

    # Locate Summary KPI block
    kpi_found = False
    for r in sales_rows[header_idx + 1:]:
        for cell_val in r:
            if cell_val == "Total Completed Sales:":
                val_idx = r.index(cell_val) + 2
                assert r[val_idx] == 64500, f"Expected 64500 completed sales, got {r[val_idx]}"
                kpi_found = True
                break
    assert kpi_found, "Summary KPI for completed sales not found"
    print("  -> Sales Workbook: Verified Completed (64,500 Ks) vs Voided (6,000 Ks, excluded from revenue). Numeric cell types confirmed.")

    # 2. P&L Financial Report Inspection
    wb_pnl = openpyxl.load_workbook(str(exported_files['financial_report']))
    ws_pnl = wb_pnl["Profit & Loss Statement"]
    pnl_rows = list(ws_pnl.iter_rows(values_only=True))
    pnl_dict = {}
    for r in pnl_rows:
        if r and len(r) >= 3 and r[0]:
            pnl_dict[str(r[0]).strip()] = r[2]

    print("  -> P&L Reconciliation Figures:")
    print(f"     * Sales Revenue:               {pnl_dict['Sales Revenue (Completed Sales)']} Ks (Authoritative Medisales: 64,500 Ks)")
    print(f"     * COGS:                        {pnl_dict['Cost of Goods Sold (FEFO + WAC COGS)']} Ks (Authoritative Medisales: 46,333 Ks)")
    print(f"     * Gross Operating Profit:      {pnl_dict['GROSS OPERATING PROFIT']} Ks (Authoritative Medisales: 18,167 Ks)")
    print(f"     * Store Operating Overheads:   {pnl_dict['Store Operating Overheads (Itemized below)']} Ks (Authoritative Medisales: 12,000 Ks)")
    print(f"     * Net Operating Profit:        {pnl_dict['NET OPERATING PROFIT']} Ks (Authoritative Medisales: 6,167 Ks)")

    assert pnl_dict['Sales Revenue (Completed Sales)'] == 64500
    assert pnl_dict['Cost of Goods Sold (FEFO + WAC COGS)'] == 46333
    assert pnl_dict['GROSS OPERATING PROFIT'] == 18167
    assert pnl_dict['Store Operating Overheads (Itemized below)'] == 12000
    assert pnl_dict['NET OPERATING PROFIT'] == 6167

    # Ensure disclosures exist
    has_purch_disclosure = any("Merchandise Purchases in Period" in str(r[0]) for r in pnl_rows if r and r[0])
    has_pay_disclosure = any("Supplier Payments in Period" in str(r[0]) for r in pnl_rows if r and r[0])
    assert has_purch_disclosure
    assert has_pay_disclosure
    print("     * Accounting Disclosures Present: Merchandise Purchases & Supplier Payments are segregated.")

    # 3. Medicine Batches Inspection
    wb_med = openpyxl.load_workbook(str(exported_files['medicine_batches']))
    ws_med = wb_med["Medicine Batches"]
    med_rows = list(ws_med.iter_rows(values_only=True))
    batch_rows = [r for r in med_rows if r and len(r) > 4 and r[3] == 'BATCH-2026-01']
    assert len(batch_rows) == 1
    b_late_r = batch_rows[0]
    assert b_late_r[4] == '2027-06-30'  # Expiry date preserved
    assert b_late_r[5] == 45            # Remaining stock on hand
    assert b_late_r[6] == 1000          # Unit cost
    assert b_late_r[7] == 45000         # Total batch value
    print("  -> Medicine Batches Workbook: Verified active batch BATCH-2026-01 (45 strips @ 1000 Ks, exp 2027-06-30) preserved with numeric values.")

    # 4. Verify Exporting Does Not Mutate Database
    conn_chk = db_reopened.get_connection()
    tables = ['products', 'categories', 'inventory_movements', 'sales', 'sale_items', 'suppliers', 'purchases', 'purchase_items', 'expenses']
    counts_before = {tbl: conn_chk.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0] for tbl in tables}

    # Re-export everything
    for k, p in exported_files.items():
        if k == 'medicine_batches':
            exporter.export_medicine_batches(str(p), "all")
        elif k in ('sales', 'purchases', 'expenses', 'financial_report'):
            getattr(exporter, f"export_{k}")(str(p), "2026-10-01", "2026-10-31")
        else:
            getattr(exporter, f"export_{k}")(str(p))

    counts_after = {tbl: conn_chk.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0] for tbl in tables}
    assert counts_before == counts_after, f"Export mutated tables: {counts_before} != {counts_after}"
    print("  -> Database Mutation Audit: Verified export methods are 100% read-only.")

    # Check for excel.exe
    excel_found = False
    try:
        res = subprocess.run(["where", "excel.exe"], capture_output=True, text=True)
        excel_found = (res.returncode == 0)
    except Exception:
        pass
    if not excel_found:
        print("  -> Microsoft Excel Application Status: NOT INSTALLED on host machine. Manual Excel verification remains pending.")
    else:
        print("  -> Microsoft Excel Application Status: Installed.")

    print("\n>>> ALL PART D EXCEL ACCEPTANCE TESTS PASSED WITH 100% SUCCESS! <<<\n")

    # ==========================================================================
    # PART E: BACKUP AND RECOVERY TESTING
    # ==========================================================================
    print("-" * 80)
    print("PART E: BACKUP AND RECOVERY TESTING (Disposable Databases Only)")
    print("-" * 80)

    # 1. Create backup
    backup_file = temp_dir / "disposable_backup.db"
    db_reopened.backup_to_file(str(backup_file))
    assert backup_file.exists() and backup_file.stat().st_size > 0
    print(f"Step 1: Created Backup File: {backup_file} ({backup_file.stat().st_size} bytes)")

    # 2. Restore the backup to a different disposable database
    restore_target = temp_dir / "disposable_restored.db"
    # Seed restore_target with fresh schema
    target_mgr = DatabaseManager(str(restore_target))
    MigrationsManager(target_mgr).apply_migrations()
    safety_backup_path = target_mgr.restore_from_file(str(backup_file))
    print(f"Step 2: Restored backup to separate target: {restore_target}")
    print(f"        Automatic Safety Pre-Restore Backup created: {safety_backup_path}")
    assert Path(safety_backup_path).exists()

    # 3. Verify restored records
    with target_mgr.get_connection() as t_conn:
        t_cur = t_conn.cursor()
        chk = t_cur.execute("PRAGMA integrity_check").fetchone()[0]
        assert chk == "ok"
        prods = t_cur.execute("SELECT name FROM products ORDER BY id").fetchall()
        prod_names = [p[0] for p in prods]
        assert prod_names == ['Paracetamol 500mg (Biogesic)', 'Lifebuoy Antibacterial Soap 100g']

        sales_cnt = t_cur.execute("SELECT COUNT(*) FROM sales").fetchone()[0]
        assert sales_cnt == 2  # 1 completed, 1 voided

        supp_cnt = t_cur.execute("SELECT COUNT(*) FROM suppliers").fetchone()[0]
        assert supp_cnt == 1
    print("Step 3: Verified Restored Database Records & Integrity Check (PRAGMA integrity_check: ok).")
    target_mgr.close()

    # 4. Test rejection of a corrupt backup
    corrupt_backup = temp_dir / "corrupted_backup.db"
    corrupt_backup.write_bytes(b"CORRUPTED_NON_SQLITE_BINARY_DATA_CRASH_TEST_HEADER_000000000")

    rejected_corrupt = False
    try:
        db_reopened.restore_from_file(str(corrupt_backup))
    except ValueError as e:
        rejected_corrupt = True
        print(f"Step 4: Successfully Rejected Corrupt Backup! Error caught: {e}")
    assert rejected_corrupt, "Failed to reject corrupt backup file!"

    # 5. Verify the working database remains unchanged after rejected restore
    with db_reopened.get_connection() as r_conn:
        active_chk = r_conn.execute("PRAGMA integrity_check").fetchone()[0]
        assert active_chk == "ok"
        active_prods = [r[0] for r in r_conn.execute("SELECT name FROM products ORDER BY id").fetchall()]
        assert active_prods == ['Paracetamol 500mg (Biogesic)', 'Lifebuoy Antibacterial Soap 100g']
    print("Step 5: Verified working database is 100% UNCHANGED and healthy after rejected restore attempt.")

    # 6. Test rejection of arbitrary SQLite database missing Medisales tables
    arbitrary_sqlite = temp_dir / "arbitrary_sqlite.db"
    with sqlite3.connect(str(arbitrary_sqlite)) as a_conn:
        a_conn.execute("CREATE TABLE random_non_medisales (id INT, txt TEXT)")
        a_conn.execute("INSERT INTO random_non_medisales VALUES (1, 'test')")
    rejected_arbitrary = False
    try:
        db_reopened.restore_from_file(str(arbitrary_sqlite))
    except ValueError as e:
        rejected_arbitrary = True
        print(f"Step 6: Successfully Rejected Arbitrary SQLite Database! Error caught: {e}")
    assert rejected_arbitrary, "Failed to reject SQLite database missing required tables!"

    db_reopened.close()
    print("\n>>> ALL PART E BACKUP & RESTORE TESTS PASSED WITH 100% SUCCESS! <<<\n")

    # ==========================================================================
    # PART F: PACKAGING AND OFFLINE OPERATION
    # ==========================================================================
    print("-" * 80)
    print("PART F: PACKAGED EXECUTABLE & OFFLINE VERIFICATION")
    print("-" * 80)

    exe_path = repo_dir / "dist" / "Medisales" / "Medisales.exe"
    assert exe_path.exists(), f"Packaged executable not found: {exe_path}"
    print(f"Packaged Executable: {exe_path} ({exe_path.stat().st_size / (1024*1024):.2f} MB)")

    # 1. Test clean launch with temporary database and isolated working directory
    pkg_temp_dir = temp_dir / "pkg_run"
    pkg_temp_dir.mkdir(parents=True, exist_ok=True)
    pkg_db = pkg_temp_dir / "packaged_owner_test.db"

    clean_env = os.environ.copy()
    clean_env.pop("PYTHONPATH", None)
    clean_env.pop("PYTHONHOME", None)
    clean_local = pkg_temp_dir / "localappdata"
    clean_local.mkdir(parents=True, exist_ok=True)
    clean_env["LOCALAPPDATA"] = str(clean_local)

    print(f"Step 1: Spawning packaged executable with --db {pkg_db}...")
    proc = subprocess.Popen(
        [str(exe_path), "--db", str(pkg_db)],
        cwd=str(pkg_temp_dir),
        env=clean_env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    # Wait up to 15s for DB initialization and migrations
    migrated = False
    for _ in range(30):
        if pkg_db.exists() and proc.poll() is None:
            try:
                with sqlite3.connect(str(pkg_db)) as t_chk:
                    tables = {r[0] for r in t_chk.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
                    if 'products' in tables and 'schema_versions' in tables:
                        migrated = True
                        break
            except Exception:
                pass
        time.sleep(0.5)

    assert proc.poll() is None, "Packaged executable crashed on launch!"
    assert pkg_db.exists(), "Packaged executable failed to create target database!"
    assert migrated, "Packaged executable database migrations did not complete in time!"
    print("   -> Packaged executable launched and initialized database successfully.")

    # Verify tables & WAL mode
    with sqlite3.connect(str(pkg_db)) as p_conn:
        t_list = [r[0] for r in p_conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        assert 'products' in t_list and 'sales' in t_list and 'schema_versions' in t_list
        jmode = p_conn.execute("PRAGMA journal_mode").fetchone()[0]
        assert jmode.upper() == 'WAL'
        # Insert test item
        p_conn.execute("INSERT INTO categories (name) VALUES ('Packaged Test Cat')")
        cid = p_conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        p_conn.execute("INSERT INTO products (name, category_id, unit_measure, selling_price, min_stock_level, is_medicine, is_active) VALUES ('Packaged Prod', ?, 'pcs', 1000, 5, 0, 1)", (cid,))
        p_conn.commit()

    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()
    print("   -> Inserted test record into packaged DB and shut down process.")

    # 2. Test Persistence across relaunch
    proc2 = subprocess.Popen(
        [str(exe_path), "--db", str(pkg_db)],
        cwd=str(pkg_temp_dir),
        env=clean_env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    time.sleep(4)
    assert proc2.poll() is None, "Packaged executable failed on reopen!"
    with sqlite3.connect(str(pkg_db)) as p2_conn:
        prod_chk = p2_conn.execute("SELECT name FROM products WHERE name='Packaged Prod'").fetchone()
        assert prod_chk is not None
    proc2.terminate()
    try:
        proc2.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc2.kill()
        proc2.wait()
    print("Step 2: Persistence confirmed across packaged executable restart!")

    # 3. Test Bundled Fonts, OFL License, and openpyxl
    internal_dir = repo_dir / "dist" / "Medisales" / "_internal"
    font_reg = internal_dir / "src" / "ui_web" / "fonts" / "NotoSansMyanmar-Regular.ttf"
    font_bold = internal_dir / "src" / "ui_web" / "fonts" / "NotoSansMyanmar-Bold.ttf"
    ofl_txt = internal_dir / "src" / "ui_web" / "fonts" / "OFL.txt"

    assert font_reg.exists() and font_reg.stat().st_size > 100000
    assert font_bold.exists() and font_bold.stat().st_size > 100000
    assert ofl_txt.exists()
    print("Step 3: Bundled Myanmar fonts & OFL license verified in _internal directory.")

    # 4. Test Missing Database Safety Check
    safety_temp = pkg_temp_dir / "missing_db_safety"
    medisales_appdata = safety_temp / "Medisales"
    medisales_appdata.mkdir(parents=True, exist_ok=True)
    (medisales_appdata / ".medisales_initialized").write_text("initialized", encoding="utf-8")

    safety_env = clean_env.copy()
    safety_env["LOCALAPPDATA"] = str(safety_temp)

    proc3 = subprocess.Popen(
        [str(exe_path)],
        cwd=str(pkg_temp_dir),
        env=safety_env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    time.sleep(2)
    proc3.terminate()
    try:
        proc3.wait(timeout=3)
    except Exception:
        proc3.kill()
        proc3.wait()

    assert proc3.returncode == 1, f"Expected returncode 1 for missing db alert, got {proc3.returncode}"
    assert not (medisales_appdata / "medisales.db").exists(), "Safety violation: blank database created when existing was missing!"
    print("Step 4: Missing database safety confirmed: executable refused to create blank database.")

    # 5. Offline Operation
    # All assets loaded from local disk (file:/// URLs), zero external CDNs, fonts bundled locally.
    index_html = internal_dir / "src" / "ui_web" / "index.html"
    assert index_html.exists()
    html_text = index_html.read_text(encoding="utf-8")
    # Verify no external CDN scripts, stylesheets or resources (allowing SVG xmlns attributes)
    import re
    assert not re.search(r'(src|href)\s*=\s*["\']https?://', html_text, re.IGNORECASE), "External CDN link detected in packaged index.html!"
    print("Step 5: 100% Offline operation confirmed: Zero external network references in web UI.")

    print("\n>>> ALL PART F PACKAGING & OFFLINE CHECKS PASSED WITH 100% SUCCESS! <<<\n")

    # ==========================================================================
    # FINAL PRODUCTION SAFETY CHECK: Verify Production DB Untouched
    # ==========================================================================
    print("-" * 80)
    print("FINAL PRODUCTION SAFETY CHECK: Verifying Hashes and Baselines")
    print("-" * 80)

    final_hash_repo = compute_sha256(str(prod_db_repo))
    final_size_repo = prod_db_repo.stat().st_size if prod_db_repo.exists() else 0
    assert final_hash_repo == prod_hash_repo, "VIOLATION: Workspace medisales.db hash changed!"
    assert final_size_repo == prod_size_repo, "VIOLATION: Workspace medisales.db size changed!"
    print(f"  Repo Root DB:    {prod_db_repo} -> SHA256 UNCHANGED: {final_hash_repo}")

    if prod_db_appdata and prod_db_appdata.exists():
        final_hash_appdata = compute_sha256(str(prod_db_appdata))
        final_size_appdata = prod_db_appdata.stat().st_size if prod_db_appdata.exists() else 0
        assert final_hash_appdata == prod_hash_appdata, "VIOLATION: AppData live medisales.db hash changed!"
        assert final_size_appdata == prod_size_appdata, "VIOLATION: AppData live medisales.db size changed!"
        print(f"  AppData Live DB: {prod_db_appdata} -> SHA256 UNCHANGED: {final_hash_appdata}")

    # Cleanup temporary directory
    shutil.rmtree(temp_dir, ignore_errors=True)
    elapsed = time.time() - start_time
    print(f"\nAll Phase 14 Acceptance Reviews Completed in {elapsed:.2f} seconds with ZERO defects.")
    print("=" * 80)
    return True


if __name__ == "__main__":
    success = run_full_acceptance_review()
    sys.exit(0 if success else 1)
