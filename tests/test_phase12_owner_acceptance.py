import os
import sqlite3
import pytest
from datetime import datetime, date, timedelta
from pathlib import Path

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


@pytest.fixture
def test_db_setup(tmp_path):
    """
    Creates an isolated disposable SQLite database in a temporary directory.
    Guarantees that production medisales.db is never touched.
    """
    db_path = tmp_path / "phase12_test.db"
    db_manager = DatabaseManager(str(db_path))
    migrations = MigrationsManager(db_manager)
    migrations.apply_migrations()

    inv_svc = InventoryService(db_manager)
    prod_svc = ProductService(db_manager)
    sales_svc = SalesService(db_manager, inv_svc)
    supp_svc = SupplierService(db_manager)
    purch_svc = PurchaseService(db_manager)
    exp_svc = ExpenseService(db_manager)
    fin_svc = FinanceService(db_manager)
    dash_svc = DashboardService(db_manager, fin_svc)
    rep_svc = ReportService(db_manager)
    recon_svc = ReconciliationService(db_manager)

    services = {
        'db_path': db_path,
        'db_manager': db_manager,
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
    yield services
    db_manager.close()


def test_invalid_product_submissions_recovery(test_db_setup):
    """
    Verifies that invalid or incomplete product submissions fail safely
    without polluting the product catalog.
    """
    ps = test_db_setup['product_service']
    conn = test_db_setup['db_manager'].get_connection()

    cat_id = ps.create_category("Test Category")

    # 1. Empty or whitespace name
    with pytest.raises(ValueError, match="Product name and unit measure are required"):
        ps.create_product(name="", category_id=cat_id, unit_measure="pcs", selling_price=1000, min_stock_level=5, is_medicine=False)
    with pytest.raises(ValueError, match="Product name and unit measure are required"):
        ps.create_product(name="   ", category_id=cat_id, unit_measure="pcs", selling_price=1000, min_stock_level=5, is_medicine=False)

    # 2. Empty unit measure
    with pytest.raises(ValueError, match="Product name and unit measure are required"):
        ps.create_product(name="Valid Name", category_id=cat_id, unit_measure="", selling_price=1000, min_stock_level=5, is_medicine=False)

    # 3. Negative selling price
    with pytest.raises(ValueError, match="Prices and stock levels cannot be negative"):
        ps.create_product(name="Valid Name", category_id=cat_id, unit_measure="pcs", selling_price=-500, min_stock_level=5, is_medicine=False)

    # 4. Fractional selling price (non-integer Kyat)
    with pytest.raises(ValueError, match="Fractional Kyat amounts are not permitted"):
        ps.create_product(name="Valid Name", category_id=cat_id, unit_measure="pcs", selling_price=1200.75, min_stock_level=5, is_medicine=False)

    # 5. Negative min stock level
    with pytest.raises(ValueError, match="Prices and stock levels cannot be negative"):
        ps.create_product(name="Valid Name", category_id=cat_id, unit_measure="pcs", selling_price=1000, min_stock_level=-1, is_medicine=False)

    # 6. Non-existent category
    with pytest.raises(ValueError, match="Invalid category"):
        ps.create_product(name="Valid Name", category_id=99999, unit_measure="pcs", selling_price=1000, min_stock_level=5, is_medicine=False)

    # Confirm 0 products inserted
    count = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    assert count == 0, "Failed product creations left residual rows!"


def test_similar_and_duplicate_product_names(test_db_setup):
    """
    Verifies handling of similar or duplicate product names and validates
    unit-of-measure immutability once inventory transactions exist.
    """
    ps = test_db_setup['product_service']
    purch_svc = test_db_setup['purchase_service']
    supp_svc = test_db_setup['supplier_service']
    conn = test_db_setup['db_manager'].get_connection()

    cat_id = ps.create_category("Analgesics")
    supp_id = supp_svc.create_supplier("Vendor A", "09-123456", "Yangon")

    # Product 1: "Paracetamol 500mg" in strip
    pid1 = ps.create_product("Paracetamol 500mg", cat_id, "strip", 1000, 5, True)
    # Product 2: "Paracetamol 500mg" in box (different packaging / form)
    pid2 = ps.create_product("Paracetamol 500mg", cat_id, "box", 9500, 2, True)

    assert pid1 != pid2, "Duplicate names must receive distinct unique primary keys"
    prods = ps.list_products()
    assert len(prods) == 2

    # Stock Product 1 via purchase
    purch_svc.create_purchase(
        reference="PO-DUP-01",
        supplier_id=supp_id,
        date=date.today().isoformat(),
        items=[{"product_id": pid1, "quantity": 20, "unit_cost": 700, "batch_number": "B1", "expiry_date": "2027-12-31"}]
    )

    # Attempt to change unit measure of Product 1 (already has transactions)
    with pytest.raises(ValueError, match="Cannot change unit measure: product already has inventory transactions"):
        ps.update_product(pid1, "Paracetamol 500mg", cat_id, "bottle", 1000, 5, True)

    # Product 2 has no transactions yet -> changing unit measure is permitted
    ps.update_product(pid2, "Paracetamol 500mg (10x10)", cat_id, "carton", 9500, 2, True)
    p2_updated = next(p for p in ps.list_products() if p['id'] == pid2)
    assert p2_updated['unit_measure'] == "carton"


def test_invalid_purchase_submissions_recovery(test_db_setup):
    """
    Verifies that invalid purchases roll back completely without leaving partial
    records or orphaned inventory movements.
    """
    ps = test_db_setup['product_service']
    purch_svc = test_db_setup['purchase_service']
    supp_svc = test_db_setup['supplier_service']
    conn = test_db_setup['db_manager'].get_connection()

    cat_id = ps.create_category("General")
    pid = ps.create_product("Soap Bar", cat_id, "pcs", 1500, 5, False)
    supp_id = supp_svc.create_supplier("Active Supplier", "09-111111", "Mandalay")

    # 1. Invalid supplier
    with pytest.raises(ValueError, match="Invalid supplier"):
        purch_svc.create_purchase("PO-INV-1", 9999, "2026-10-11", [{"product_id": pid, "quantity": 10, "unit_cost": 800}])

    # 2. Deactivated supplier
    supp_svc.update_supplier(supp_id, "Active Supplier", "09-111111", "Mandalay", is_active=False)
    with pytest.raises(ValueError, match="Cannot create purchase for deactivated supplier"):
        purch_svc.create_purchase("PO-INV-2", supp_id, "2026-10-11", [{"product_id": pid, "quantity": 10, "unit_cost": 800}])

    # Re-activate supplier
    supp_svc.update_supplier(supp_id, "Active Supplier", "09-111111", "Mandalay", is_active=True)

    # 3. Empty item list
    with pytest.raises(ValueError, match="Purchase must contain at least one item"):
        purch_svc.create_purchase("PO-INV-3", supp_id, "2026-10-11", [])

    # 4. Non-positive quantity
    with pytest.raises(ValueError, match="Quantity must be greater than zero"):
        purch_svc.create_purchase("PO-INV-4", supp_id, "2026-10-11", [{"product_id": pid, "quantity": 0, "unit_cost": 800}])
    with pytest.raises(ValueError, match="Quantity must be greater than zero"):
        purch_svc.create_purchase("PO-INV-5", supp_id, "2026-10-11", [{"product_id": pid, "quantity": -5, "unit_cost": 800}])

    # 5. Negative unit cost
    with pytest.raises(ValueError, match="Unit cost cannot be negative"):
        purch_svc.create_purchase("PO-INV-6", supp_id, "2026-10-11", [{"product_id": pid, "quantity": 10, "unit_cost": -200}])

    # 6. Fractional Kyat cost
    with pytest.raises(ValueError, match="Fractional Kyat amounts are not permitted"):
        purch_svc.create_purchase("PO-INV-7", supp_id, "2026-10-11", [{"product_id": pid, "quantity": 10, "unit_cost": 800.5}])

    # Confirm zero purchases or inventory movements created
    p_count = conn.execute("SELECT COUNT(*) FROM purchases").fetchone()[0]
    pi_count = conn.execute("SELECT COUNT(*) FROM purchase_items").fetchone()[0]
    mov_count = conn.execute("SELECT COUNT(*) FROM inventory_movements").fetchone()[0]
    assert p_count == 0 and pi_count == 0 and mov_count == 0, "Failed purchases left partial records!"


def test_insufficient_stock_and_expired_medicine_enforcement(test_db_setup):
    """
    Verifies that:
    1. Expired, today-expiring, and unknown-expiry batches cannot be sold.
    2. Over-selling attempts fail atomically without partial stock decrements.
    """
    ps = test_db_setup['product_service']
    inv_svc = test_db_setup['inventory_service']
    purch_svc = test_db_setup['purchase_service']
    sales_svc = test_db_setup['sales_service']
    supp_svc = test_db_setup['supplier_service']
    conn = test_db_setup['db_manager'].get_connection()

    cat_id = ps.create_category("Pharmacy")
    med_id = ps.create_product("Cipro 500mg", cat_id, "strip", 3000, 5, True)
    supp_id = supp_svc.create_supplier("Pharma Direct", "09-222222", "Yangon")

    today_str = date.today().isoformat()
    yesterday_str = (date.today() - timedelta(days=1)).isoformat()
    future_str = (date.today() + timedelta(days=180)).isoformat()

    # Purchase with 1 valid future batch
    purch_svc.create_purchase(
        reference="PO-CIP-01",
        supplier_id=supp_id,
        date=today_str,
        items=[{"product_id": med_id, "quantity": 10, "unit_cost": 2000, "batch_number": "VALID-B1", "expiry_date": future_str}]
    )

    # Manually inject expired batch and same-day expiry batch into medicine_batches
    conn.execute("""
        INSERT INTO medicine_batches (product_id, batch_number, expiry_date, initial_qty, current_qty, unit_cost)
        VALUES (?, 'EXPIRED-B', ?, 15, 15, 1500)
    """, (med_id, yesterday_str))
    conn.execute("""
        INSERT INTO medicine_batches (product_id, batch_number, expiry_date, initial_qty, current_qty, unit_cost)
        VALUES (?, 'TODAY-B', ?, 10, 10, 1500)
    """, (med_id, today_str))
    conn.execute("""
        INSERT INTO medicine_batches (product_id, batch_number, expiry_date, initial_qty, current_qty, unit_cost)
        VALUES (?, 'NO-EXP-B', NULL, 10, 10, 1500)
    """, (med_id,))
    # Update product total stock to reflect all rows
    conn.execute("UPDATE products SET current_stock = 45 WHERE id = ?", (med_id,))
    conn.commit()

    # Verify sellable filter only sees VALID-B1
    sellable = inv_svc.get_sellable_medicine_batches(med_id)
    assert len(sellable) == 1, f"Expected only 1 sellable batch, found {len(sellable)}"
    assert sellable[0]['batch_number'] == "VALID-B1"
    assert sellable[0]['current_qty'] == 10

    # Attempt to sell 11 units (more than the 10 eligible)
    with pytest.raises(ValueError, match="Insufficient .* stock"):
        sales_svc.create_sale(
            reference="INV-ERR-01",
            items=[{"product_id": med_id, "quantity": 11, "unit_price": 3000}],
            amount_received=50000
        )

    # Verify VALID-B1 batch quantity is completely untouched
    batch_fresh = conn.execute("SELECT current_qty FROM medicine_batches WHERE batch_number='VALID-B1'").fetchone()[0]
    assert batch_fresh == 10, "Eligible batch was partially decremented despite failed transaction!"

    # Successfully sell the 10 eligible units
    sale_id = sales_svc.create_sale(
        reference="INV-OK-01",
        items=[{"product_id": med_id, "quantity": 10, "unit_price": 3000}],
        amount_received=30000
    )
    assert sale_id > 0

    # VALID-B1 is now depleted (current_qty = 0)
    batch_depleted = conn.execute("SELECT current_qty FROM medicine_batches WHERE batch_number='VALID-B1'").fetchone()[0]
    assert batch_depleted == 0

    # Sellable list is now empty (even though 35 units of expired/today batches exist)
    sellable_now = inv_svc.get_sellable_medicine_batches(med_id)
    assert len(sellable_now) == 0

    # Attempting any subsequent sale must fail
    with pytest.raises(ValueError, match="Insufficient .* stock"):
        sales_svc.create_sale(
            reference="INV-ERR-02",
            items=[{"product_id": med_id, "quantity": 1, "unit_price": 3000}],
            amount_received=3000
        )


def test_sale_validation_rollback_and_void_recovery(test_db_setup):
    """
    Verifies that:
    1. Inactive products cannot be sold.
    2. Completed sales can be voided with exact stock restoration.
    3. Duplicate void attempts are strictly rejected.
    4. Financial reports correctly reflect voided transactions.
    """
    ps = test_db_setup['product_service']
    purch_svc = test_db_setup['purchase_service']
    sales_svc = test_db_setup['sales_service']
    supp_svc = test_db_setup['supplier_service']
    rep_svc = test_db_setup['report_service']
    conn = test_db_setup['db_manager'].get_connection()

    cat_id = ps.create_category("Stationery")
    pid = ps.create_product("Notebook A5", cat_id, "pcs", 2000, 5, False)
    supp_id = supp_svc.create_supplier("Stationery Hub", "09-333333", "Yangon")

    today_str = date.today().isoformat()
    purch_svc.create_purchase(
        reference="PO-NB-01",
        supplier_id=supp_id,
        date=today_str,
        items=[{"product_id": pid, "quantity": 50, "unit_cost": 1200}]
    )

    # Deactivate product and verify checkout rejection
    ps.update_product(pid, "Notebook A5", cat_id, "pcs", 2000, 5, is_active=False)
    with pytest.raises(ValueError, match="is inactive and cannot be sold"):
        sales_svc.create_sale("INV-INACT", [{"product_id": pid, "quantity": 5, "unit_price": 2000}], 10000)

    # Reactivate and complete sale
    ps.update_product(pid, "Notebook A5", cat_id, "pcs", 2000, 5, is_active=True)
    sale_id = sales_svc.create_sale("INV-VOID-TEST", [{"product_id": pid, "quantity": 20, "unit_price": 2000}], 50000)

    stock_after_sale = conn.execute("SELECT current_stock FROM products WHERE id=?", (pid,)).fetchone()[0]
    assert stock_after_sale == 30  # 50 - 20

    # Void the sale
    sales_svc.void_sale(sale_id)
    sale_status = conn.execute("SELECT status FROM sales WHERE id=?", (sale_id,)).fetchone()[0]
    assert sale_status == "Voided"

    # Stock must be restored to 50
    stock_after_void = conn.execute("SELECT current_stock FROM products WHERE id=?", (pid,)).fetchone()[0]
    assert stock_after_void == 50

    # Audit movement logged with SaleVoid
    mov = conn.execute("SELECT movement_type, reference_type, quantity_change FROM inventory_movements WHERE reference_id=? AND reference_type='SaleVoid'", (sale_id,)).fetchone()
    assert mov is not None
    assert mov['quantity_change'] == 20

    # Duplicate void attempt must fail
    with pytest.raises(ValueError, match="Sale is already voided"):
        sales_svc.void_sale(sale_id)

    # Stock must NOT be double-restored
    stock_after_dup = conn.execute("SELECT current_stock FROM products WHERE id=?", (pid,)).fetchone()[0]
    assert stock_after_dup == 50

    # Financial report must show 0 net sales for voided sale
    summary = rep_svc.get_sales_summary(today_str, today_str)
    assert summary['total_revenue'] == 0
    assert summary['sales_count'] == 0


def test_supplier_payment_validation_and_rollback(test_db_setup):
    """
    Verifies that invalid supplier payments fail cleanly and roll back completely
    without corrupting purchase balances or leaving orphan allocations.
    """
    ps = test_db_setup['product_service']
    purch_svc = test_db_setup['purchase_service']
    supp_svc = test_db_setup['supplier_service']
    rep_svc = test_db_setup['report_service']
    conn = test_db_setup['db_manager'].get_connection()

    cat_id = ps.create_category("Hardware")
    pid = ps.create_product("Lock 40mm", cat_id, "pcs", 5000, 2, False)

    supp1 = supp_svc.create_supplier("Supplier 1", "09-444444", "Yangon")
    supp2 = supp_svc.create_supplier("Supplier 2", "09-555555", "Mandalay")

    today_str = date.today().isoformat()
    p1 = purch_svc.create_purchase("PO-PAY-01", supp1, today_str, [{"product_id": pid, "quantity": 10, "unit_cost": 3000}])  # Total 30,000 Ks
    p2 = purch_svc.create_purchase("PO-PAY-02", supp2, today_str, [{"product_id": pid, "quantity": 10, "unit_cost": 3000}])  # Total 30,000 Ks

    # 1. Allocation exceeding purchase balance
    with pytest.raises(ValueError, match="exceeds outstanding balance"):
        purch_svc.record_payment("PV-FAIL-1", supp1, today_str, 35000, [{"purchase_id": p1, "allocated_amount": 35000}])

    # 2. Allocation to purchase belonging to a different supplier
    with pytest.raises(ValueError, match="Cannot allocate payment to a purchase from a different supplier"):
        purch_svc.record_payment("PV-FAIL-2", supp1, today_str, 20000, [{"purchase_id": p2, "allocated_amount": 20000}])

    # 3. Total allocated amount exceeds total payment amount
    with pytest.raises(ValueError, match="cannot exceed .*total amount"):
        purch_svc.record_payment("PV-FAIL-3", supp1, today_str, 10000, [{"purchase_id": p1, "allocated_amount": 15000}])

    # Verify zero payments recorded and supplier balance untouched
    pay_count = conn.execute("SELECT COUNT(*) FROM supplier_payments").fetchone()[0]
    alloc_count = conn.execute("SELECT COUNT(*) FROM supplier_payment_allocations").fetchone()[0]
    assert pay_count == 0 and alloc_count == 0

    supp1_bal = next(b['outstanding_balance'] for b in rep_svc.get_supplier_balances() if b['supplier_id'] == supp1)
    assert supp1_bal == 30000


def test_backup_and_restore_safety_and_error_messages(test_db_setup, tmp_path):
    """
    Verifies that:
    1. Valid backup creation succeeds.
    2. Restoring missing, corrupt, or non-Medisales databases fails cleanly with descriptive errors.
    3. The active database connection remains untouched on restore failures.
    """
    db_mgr = test_db_setup['db_manager']
    ps = test_db_setup['product_service']
    conn = db_mgr.get_connection()

    cat_id = ps.create_category("Beverages")
    ps.create_product("Green Tea Bottle", cat_id, "bottle", 800, 10, False)

    # Create valid backup
    backup_file = str(tmp_path / "valid_backup.db")
    db_mgr.backup_to_file(backup_file)
    assert os.path.exists(backup_file) and os.path.getsize(backup_file) > 0

    # 1. Non-existent file
    with pytest.raises(FileNotFoundError, match="Backup file not found"):
        db_mgr.restore_from_file(str(tmp_path / "non_existent_file.db"))

    # 2. Corrupted file (random garbage bytes)
    corrupt_file = tmp_path / "corrupt.db"
    corrupt_file.write_bytes(b"NOT_A_VALID_SQLITE_DATABASE_HEADER_GARBAGE_1234567890")
    with pytest.raises(ValueError, match="The selected backup file is corrupt or not a valid SQLite database"):
        db_mgr.restore_from_file(str(corrupt_file))

    # 3. Valid SQLite file but lacking Medisales schema
    alien_file = tmp_path / "alien.db"
    alien_conn = sqlite3.connect(str(alien_file))
    alien_conn.execute("CREATE TABLE some_random_table (id INT, note TEXT)")
    alien_conn.commit()
    alien_conn.close()
    with pytest.raises(ValueError, match="missing required tables"):
        db_mgr.restore_from_file(str(alien_file))

    # Verify active database still has Green Tea Bottle intact
    prod_count = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    assert prod_count == 1, "Active database was modified by failed restore attempts!"


def test_restart_persistence_and_invariants_audit(test_db_setup):
    """
    Populates a full realistic lifecycle, closes the database, re-opens,
    and audits mathematical invariants across all domain models.
    """
    db_mgr = test_db_setup['db_manager']
    db_path = test_db_setup['db_path']
    ps = test_db_setup['product_service']
    purch_svc = test_db_setup['purchase_service']
    sales_svc = test_db_setup['sales_service']
    supp_svc = test_db_setup['supplier_service']
    exp_svc = test_db_setup['expense_service']

    cat_id = ps.create_category("Vitamins")
    supp_id = supp_svc.create_supplier("HealthCorp", "09-666666", "Yangon")

    # 1. Products
    med_id = ps.create_product("Vitamin C 1000mg", cat_id, "tube", 4500, 5, True)
    gen_id = ps.create_product("Cotton Buds 200s", cat_id, "box", 1200, 5, False)

    today_str = date.today().isoformat()

    # 2. Purchases
    # Vitamin C: Batch 1 (30 @ 3000 Ks, Exp: 2027-06-30), Batch 2 (20 @ 3200 Ks, Exp: 2027-12-31) -> 154,000 Ks
    purch_svc.create_purchase(
        reference="PO-VIT-01",
        supplier_id=supp_id,
        date=today_str,
        items=[
            {"product_id": med_id, "quantity": 30, "unit_cost": 3000, "batch_number": "VC-A", "expiry_date": "2027-06-30"},
            {"product_id": med_id, "quantity": 20, "unit_cost": 3200, "batch_number": "VC-B", "expiry_date": "2027-12-31"}
        ]
    )
    # Cotton Buds: 40 @ 800 Ks -> 32,000 Ks
    purch_svc.create_purchase(
        reference="PO-COT-01",
        supplier_id=supp_id,
        date=today_str,
        items=[{"product_id": gen_id, "quantity": 40, "unit_cost": 800}]
    )

    # 3. Sales
    # Sell 10 Vitamin C (deducted from Batch VC-A) + 5 Cotton Buds
    sales_svc.create_sale(
        reference="INV-CYCLE-01",
        items=[
            {"product_id": med_id, "quantity": 10, "unit_price": 4500},
            {"product_id": gen_id, "quantity": 5, "unit_price": 1200}
        ],
        amount_received=60000
    )

    # 4. Operating Expense
    exp_svc.create_expense("Electricity", "Shop utility bill", 15000, today_str)

    # 5. Supplier Payment: Settle 50,000 Ks towards PO-VIT-01
    purch_id = test_db_setup['db_manager'].get_connection().execute("SELECT id FROM purchases WHERE reference='PO-VIT-01'").fetchone()[0]
    purch_svc.record_payment("PV-CYCLE-01", supp_id, today_str, 50000, [{"purchase_id": purch_id, "allocated_amount": 50000}])

    # Close and Reopen Database Connection
    db_mgr.close()
    reopened_mgr = DatabaseManager(str(db_path))
    conn = reopened_mgr.get_connection()

    # --- INVARIANT AUDIT ---
    # Invariant 1: Medicine current stock == sum of active batch quantities
    med_stock = conn.execute("SELECT current_stock FROM products WHERE id=?", (med_id,)).fetchone()[0]
    batch_sum = conn.execute("SELECT SUM(current_qty) FROM medicine_batches WHERE product_id=?", (med_id,)).fetchone()[0]
    assert med_stock == batch_sum == 40  # 50 - 10 sold

    # Invariant 2: General stock == net sum of movements
    gen_stock = conn.execute("SELECT current_stock FROM products WHERE id=?", (gen_id,)).fetchone()[0]
    gen_mov_sum = conn.execute("SELECT SUM(CASE WHEN movement_type = 'In' THEN quantity_change ELSE -quantity_change END) FROM inventory_movements WHERE product_id=?", (gen_id,)).fetchone()[0]
    assert gen_stock == gen_mov_sum == 35  # 40 - 5 sold

    # Invariant 3: Purchase total_paid == sum of allocations
    for purch_row in conn.execute("SELECT id, total_amount, amount_paid FROM purchases").fetchall():
        p_id = purch_row['id']
        alloc_sum = conn.execute("SELECT COALESCE(SUM(allocated_amount), 0) FROM supplier_payment_allocations WHERE purchase_id=?", (p_id,)).fetchone()[0]
        assert purch_row['amount_paid'] == alloc_sum
        assert purch_row['amount_paid'] <= purch_row['total_amount']

    # Invariant 4: Supplier remaining debt == sum of outstanding purchase balances
    supp_owed = conn.execute("SELECT SUM(total_amount - amount_paid) FROM purchases WHERE supplier_id=?", (supp_id,)).fetchone()[0]
    assert supp_owed == (154000 - 50000) + 32000 == 136000

    # Invariant 5: No negative numbers or floats in integer Kyat columns
    neg_check = conn.execute('''
        SELECT COUNT(*) FROM products 
        WHERE current_stock < 0 OR inventory_value < 0 OR selling_price < 0
    ''').fetchone()[0]
    assert neg_check == 0

    reopened_mgr.close()
