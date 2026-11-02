import os
import re
import sqlite3
import pytest
from pathlib import Path
from datetime import date, timedelta
import openpyxl

from database.connection import DatabaseManager
from database.migrations_manager import MigrationsManager
from src.services.export_service import ExportService
from src.services.product_service import ProductService
from src.services.inventory_service import InventoryService
from src.services.sales_service import SalesService
from src.services.purchase_service import PurchaseService
from src.services.supplier_service import SupplierService
from src.services.expense_service import ExpenseService
from src.services.report_service import ReportService
from src.services.finance_service import FinanceService
from src.services.dashboard_service import DashboardService


# ==============================================================================
# 1. FONT ASSETS & OFFLINE PACKAGING INTEGRITY
# ==============================================================================

def test_font_assets_and_license_offline():
    """Verify bundled font files and SIL Open Font License 1.1 exist for 100% offline usage."""
    repo_root = Path(__file__).resolve().parent.parent
    font_dir = repo_root / "src" / "ui_web" / "fonts"

    regular_font = font_dir / "NotoSansMyanmar-Regular.ttf"
    bold_font = font_dir / "NotoSansMyanmar-Bold.ttf"
    license_file = font_dir / "OFL.txt"

    assert regular_font.exists(), "NotoSansMyanmar-Regular.ttf must exist in src/ui_web/fonts"
    assert regular_font.stat().st_size > 100_000, "Font regular file appears truncated"

    assert bold_font.exists(), "NotoSansMyanmar-Bold.ttf must exist in src/ui_web/fonts"
    assert bold_font.stat().st_size > 100_000, "Font bold file appears truncated"

    assert license_file.exists(), "OFL.txt license file must exist alongside font files"
    content = license_file.read_text(encoding="utf-8")
    assert "SIL OPEN FONT LICENSE Version 1.1" in content, "Valid SIL OFL 1.1 license required"

    # Verify output.css contains offline font-face declaration
    css_file = repo_root / "src" / "ui_web" / "output.css"
    assert css_file.exists()
    css_text = css_file.read_text(encoding="utf-8")
    assert "Noto Sans Myanmar" in css_text
    assert "NotoSansMyanmar-Regular.ttf" in css_text


# ==============================================================================
# 2. LOCALIZATION SYSTEM & FALLBACKS
# ==============================================================================

def test_i18n_dictionary_completeness():
    """Verify i18n.js contains comprehensive translations for all 9 modules in both EN and MY."""
    repo_root = Path(__file__).resolve().parent.parent
    i18n_path = repo_root / "src" / "ui_web" / "js" / "i18n.js"
    assert i18n_path.exists()
    text = i18n_path.read_text(encoding="utf-8")

    # Essential module navigation keys
    required_keys = [
        "nav.dashboard", "nav.sales", "nav.products", "nav.inventory",
        "nav.purchases", "nav.suppliers", "nav.expenses", "nav.reports", "nav.settings",
        "btn.save", "btn.cancel", "btn.export_excel", "btn.void",
        "sales.complete_sale", "pur.modal_title", "sup.btn_record_payment",
        "rep.pnl_title", "set.language_card_title"
    ]

    for k in required_keys:
        assert f'"{k}"' in text or f"'{k}'" in text, f"Missing key {k} in i18n.js"


def test_language_persistence_and_backend_slot(db_manager):
    """Verify language selection persists in SQLite settings table and restores safely."""
    from src.ui_web.bridge import FrontendBridge

    # Build services map
    services = {
        'db_manager': db_manager,
        'report_service': ReportService(db_manager),
    }
    bridge = FrontendBridge(services)

    # 1. Fresh installation defaults to English
    res_raw = bridge.get_language()
    assert '"status": "success"' in res_raw
    assert '"data": "en"' in res_raw

    # 2. Switch to Myanmar
    set_raw = bridge.set_language("my")
    assert '"status": "success"' in set_raw
    assert '"data": "my"' in set_raw

    # Verify persisted in database
    conn = db_manager.get_connection()
    row = conn.execute("SELECT value FROM settings WHERE key = 'language'").fetchone()
    assert row is not None
    assert row['value'] == 'my'

    # 3. Simulate app restart: re-query get_language
    res_reopen = bridge.get_language()
    assert '"data": "my"' in res_reopen

    # 4. Fallback for invalid input safely reverts to 'en'
    bridge.set_language("fr")
    assert '"data": "en"' in bridge.get_language()


def test_business_data_integrity_under_language_changes(db_manager):
    """Verify user-entered product names, batches, and supplier names remain unmodified."""
    from src.ui_web.bridge import FrontendBridge
    from src.services.product_service import ProductService
    from src.services.supplier_service import SupplierService

    prod_svc = ProductService(db_manager)
    supp_svc = SupplierService(db_manager)

    # Insert category, supplier, and product with mixed scripts inside transaction
    with db_manager.transaction() as tx:
        cat_id = tx.execute("INSERT INTO categories (name) VALUES ('ဆေးဝါးများ')").lastrowid
    supp_id = supp_svc.create_supplier("ရွှေမင်းသုတ ဆေးလက်ကား", "0911223344", "ရန်ကုန်မြို့")
    prod_id = prod_svc.create_product("Biogesic 500mg ပါရာစီတမော", cat_id, "ကတ်", 1500, 10, is_medicine=True)

    bridge = FrontendBridge({'db_manager': db_manager})

    # Switch languages
    bridge.set_language("my")
    bridge.set_language("en")
    bridge.set_language("my")

    # Fetch back records
    p = next(x for x in prod_svc.list_products(include_inactive=True) if x['id'] == prod_id)
    assert p['name'] == "Biogesic 500mg ပါရာစီတမော"
    assert p['unit_measure'] == "ကတ်"
    assert p['selling_price'] == 1500

    s = next(x for x in supp_svc.list_suppliers(include_inactive=True) if x['id'] == supp_id)
    assert s['name'] == "ရွှေမင်းသုတ ဆေးလက်ကား"


# ==============================================================================
# 3. EXCEL EXPORT SERVICE TESTS
# ==============================================================================

@pytest.fixture
def services_bundle(db_manager):
    inv_svc = InventoryService(db_manager)
    prod_svc = ProductService(db_manager)
    sales_svc = SalesService(db_manager, inv_svc)
    supp_svc = SupplierService(db_manager)
    purch_svc = PurchaseService(db_manager)
    exp_svc = ExpenseService(db_manager)
    fin_svc = FinanceService(db_manager)
    rep_svc = ReportService(db_manager)
    dash_svc = DashboardService(db_manager, fin_svc)

    svcs = {
        'db_manager': db_manager,
        'inventory_service': inv_svc,
        'product_service': prod_svc,
        'sales_service': sales_svc,
        'supplier_service': supp_svc,
        'purchase_service': purch_svc,
        'expense_service': exp_svc,
        'finance_service': fin_svc,
        'report_service': rep_svc,
        'dashboard_service': dash_svc,
    }
    svcs['export_service'] = ExportService(svcs)
    return svcs


def test_excel_export_empty_tables(services_bundle, tmp_path):
    """Verify all 8 Excel workbooks export cleanly on an empty database with headers and proper worksheets."""
    exporter = services_bundle['export_service']

    exports = [
        (exporter.export_sales, "sales_empty.xlsx", "Sales Transactions"),
        (exporter.export_products, "products_empty.xlsx", "Products Catalog"),
        (exporter.export_inventory_valuation, "inv_val_empty.xlsx", "Inventory Valuation"),
        (lambda p: exporter.export_medicine_batches(p, "all"), "batches_empty.xlsx", "Medicine Batches"),
        (exporter.export_purchases, "purchases_empty.xlsx", "Purchases"),
        (exporter.export_suppliers, "suppliers_empty.xlsx", "Suppliers & Balances"),
        (exporter.export_expenses, "expenses_empty.xlsx", "Operating Expenses"),
        (lambda p: exporter.export_financial_report(p, "2026-01-01", "2026-12-31"), "pnl_empty.xlsx", "Profit & Loss Statement"),
    ]

    for fn, fname, sheet_title in exports:
        out_file = str(tmp_path / fname)
        saved = fn(out_file)
        assert Path(saved).exists()
        assert Path(saved).stat().st_size > 3000

        wb = openpyxl.load_workbook(saved)
        assert sheet_title in wb.sheetnames
        ws = wb[sheet_title]
        assert ws.cell(row=1, column=1).value is not None, f"Report header missing in {fname}"


def test_excel_sales_completed_vs_voided_reconciliation(services_bundle, tmp_path):
    """Verify voided sales are visibly marked but excluded from completed sales revenue totals."""
    db_manager = services_bundle['db_manager']
    prod_svc = services_bundle['product_service']
    purch_svc = services_bundle['purchase_service']
    supp_svc = services_bundle['supplier_service']
    sales_svc = services_bundle['sales_service']
    exporter = services_bundle['export_service']

    with db_manager.transaction() as tx:
        cat_id = tx.execute("INSERT INTO categories (name) VALUES ('General')").lastrowid
    p1 = prod_svc.create_product("Item A", cat_id, "pcs", 10000, 5, is_medicine=False)
    p2 = prod_svc.create_product("Item B", cat_id, "pcs", 5000, 5, is_medicine=False)

    supp_id = supp_svc.create_supplier("Vendor 1", "09111", "Yangon")
    purch_svc.create_purchase("PO-01", supp_id, "2026-10-01", [
        {'product_id': p1, 'quantity': 20, 'unit_cost': 6000, 'batch_number': None, 'expiry_date': None},
        {'product_id': p2, 'quantity': 20, 'unit_cost': 3000, 'batch_number': None, 'expiry_date': None},
    ])

    # Sale 1: Completed (10,000 Ks)
    s1_id = sales_svc.create_sale("REC-001", [{'product_id': p1, 'quantity': 1, 'unit_price': 10000}], 10000)

    # Sale 2: Voided (5,000 Ks)
    s2_id = sales_svc.create_sale("REC-002", [{'product_id': p2, 'quantity': 1, 'unit_price': 5000}], 5000)
    sales_svc.void_sale(s2_id)

    out_file = str(tmp_path / "sales_reconciliation.xlsx")
    exporter.export_sales(out_file)

    wb = openpyxl.load_workbook(out_file)
    ws = wb["Sales Transactions"]

    # Locate data rows
    rows_data = list(ws.iter_rows(values_only=True))
    header_idx = None
    for idx, r in enumerate(rows_data):
        if r and r[0] == "Invoice #":
            header_idx = idx
            break

    assert header_idx is not None, "Invoice table header not found"
    data_rows = rows_data[header_idx + 1:]

    # Check REC-001 (Completed) and REC-002 (Voided)
    rec1 = next(r for r in data_rows if r[0] == "REC-001")
    rec2 = next(r for r in data_rows if r[0] == "REC-002")

    assert rec1[2] == "Completed"
    assert rec2[2] == "Voided"

    # Numeric check: amount must be numeric integer/float, not string
    assert isinstance(rec1[4], (int, float))
    assert rec1[4] == 10000

    # Summary KPI row in summary block: Completed Revenue must be exactly 10,000, excluding voided 5,000
    completed_rev_found = False
    for r in rows_data[header_idx + 1:]:
        for cell_val in r:
            if cell_val == "Total Completed Sales:":
                val_idx = r.index(cell_val) + 2
                assert r[val_idx] == 10000
                completed_rev_found = True
                break
    assert completed_rev_found, "Completed sales revenue KPI was not found or did not match"


def test_excel_financial_report_reconciliation_and_disclosures(services_bundle, tmp_path):
    """
    Verify Profit & Loss Statement export reconciles strictly with business rules:
    - Revenue, COGS, Gross Profit follow POS rules.
    - Operating expenses include overheads only.
    - Supplier payments and inventory purchases are excluded from operating expenses.
    """
    db_manager = services_bundle['db_manager']
    prod_svc = services_bundle['product_service']
    purch_svc = services_bundle['purchase_service']
    supp_svc = services_bundle['supplier_service']
    sales_svc = services_bundle['sales_service']
    exp_svc = services_bundle['expense_service']
    exporter = services_bundle['export_service']

    with db_manager.transaction() as tx:
        cat_id = tx.execute("INSERT INTO categories (name) VALUES ('General')").lastrowid
    p1 = prod_svc.create_product("Item X", cat_id, "pcs", 20000, 5, is_medicine=False)

    supp_id = supp_svc.create_supplier("Vendor X", "09999", "Mandalay")
    # Inventory purchase: 10 units @ 12,000 Ks = 120,000 Ks
    purch_svc.create_purchase("PO-X", supp_id, "2026-10-01", [
        {'product_id': p1, 'quantity': 10, 'unit_cost': 12000, 'batch_number': None, 'expiry_date': None}
    ])

    # Completed sale: 1 unit @ 20,000 Ks -> Revenue=20,000, COGS=12,000, Gross Profit=8,000
    sales_svc.create_sale("REC-X", [{'product_id': p1, 'quantity': 1, 'unit_price': 20000}], 20000)

    # Operating Expense: 3,000 Ks
    exp_svc.create_expense("Shop Rent", "Monthly stall rent", 3000, "2026-10-05")

    # Voided Expense: 1,500 Ks (should be excluded)
    ve_id = exp_svc.create_expense("Repairs", "Faulty bulb", 1500, "2026-10-06")
    exp_svc.void_expense(ve_id)

    # Supplier Debt Payment: 50,000 Ks (liability settlement, NOT operating expense)
    conn = db_manager.get_connection()
    purch_rows = conn.execute("SELECT id FROM purchases WHERE supplier_id=?", (supp_id,)).fetchall()
    purch_svc.record_payment("PV-01", supp_id, "2026-10-07", 50000, [{'purchase_id': purch_rows[0]['id'], 'allocated_amount': 50000}], "Partial debt settlement")

    out_file = str(tmp_path / "pnl_reconciled.xlsx")
    exporter.export_financial_report(out_file, "2026-10-01", "2026-12-31")

    wb = openpyxl.load_workbook(out_file)
    ws = wb["Profit & Loss Statement"]
    rows = list(ws.iter_rows(values_only=True))

    row_dict = {}
    for r in rows:
        if r and len(r) >= 3 and r[0]:
            row_dict[str(r[0]).strip()] = r[2]

    # Accounting Reconciliation Checks
    assert row_dict["Sales Revenue (Completed Sales)"] == 20000
    assert row_dict["Cost of Goods Sold (FEFO + WAC COGS)"] == 12000
    assert row_dict["GROSS OPERATING PROFIT"] == 8000
    assert row_dict["Store Operating Overheads (Itemized below)"] == 3000
    assert row_dict["NET OPERATING PROFIT"] == 5000  # 8,000 - 3,000

    # Ensure Supplier Debt Payment (50,000) and Inventory Purchases (120,000) were NOT added to expenses
    assert row_dict["Store Operating Overheads (Itemized below)"] < 10000

    # Check disclosures
    assert any("Merchandise Purchases in Period" in str(r[0]) for r in rows if r and r[0])
    assert any("Supplier Payments in Period" in str(r[0]) for r in rows if r and r[0])


def test_excel_medicine_batches_fefo_preservation(services_bundle, tmp_path):
    """Verify medicine batches export retains batch numbers, costs, and expiry dates."""
    db_manager = services_bundle['db_manager']
    prod_svc = services_bundle['product_service']
    purch_svc = services_bundle['purchase_service']
    supp_svc = services_bundle['supplier_service']
    exporter = services_bundle['export_service']

    with db_manager.transaction() as tx:
        cat_id = tx.execute("INSERT INTO categories (name) VALUES ('Pharma')").lastrowid
    p_med = prod_svc.create_product("Amoxicillin 500mg", cat_id, "strip", 2000, 10, is_medicine=True)

    supp_id = supp_svc.create_supplier("Pharma Dist", "09777", "Yangon")
    expiry_target = (date.today() + timedelta(days=60)).isoformat()
    purch_svc.create_purchase("PO-MED-1", supp_id, "2026-10-01", [
        {'product_id': p_med, 'quantity': 50, 'unit_cost': 1200, 'batch_number': 'AMX-2026-B1', 'expiry_date': expiry_target}
    ])

    out_file = str(tmp_path / "medicine_batches.xlsx")
    exporter.export_medicine_batches(out_file, filter_type="all")

    wb = openpyxl.load_workbook(out_file)
    ws = wb["Medicine Batches"]
    rows = list(ws.iter_rows(values_only=True))

    batch_row = next(r for r in rows if r and len(r) > 4 and r[3] == "AMX-2026-B1")
    assert batch_row[2] == "Amoxicillin 500mg"
    assert batch_row[4] == expiry_target
    assert batch_row[5] == 50  # Qty
    assert batch_row[6] == 1200  # Cost
    assert batch_row[7] == 60000  # Batch Value


def test_excel_export_does_not_modify_database(services_bundle, tmp_path):
    """Verify that calling Excel export methods is strictly read-only and causes zero DB mutations."""
    db_manager = services_bundle['db_manager']
    exporter = services_bundle['export_service']

    conn = db_manager.get_connection()

    # Capture initial table row counts
    tables = [
        'products', 'categories', 'inventory_movements', 'sales', 'sale_items',
        'suppliers', 'purchases', 'purchase_items', 'expenses', 'settings'
    ]
    before_counts = {tbl: conn.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0] for tbl in tables}

    # Run all exports
    exporter.export_sales(str(tmp_path / "t_sales.xlsx"))
    exporter.export_products(str(tmp_path / "t_prod.xlsx"))
    exporter.export_inventory_valuation(str(tmp_path / "t_inv.xlsx"))
    exporter.export_medicine_batches(str(tmp_path / "t_batch.xlsx"))
    exporter.export_purchases(str(tmp_path / "t_purch.xlsx"))
    exporter.export_suppliers(str(tmp_path / "t_supp.xlsx"))
    exporter.export_expenses(str(tmp_path / "t_exp.xlsx"))
    exporter.export_financial_report(str(tmp_path / "t_pnl.xlsx"), "2026-01-01", "2026-12-31")

    # Capture after counts
    after_counts = {tbl: conn.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0] for tbl in tables}
    assert before_counts == after_counts, "Excel exports mutated database records!"
