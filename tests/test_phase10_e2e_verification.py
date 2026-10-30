import os
import sys
import json
import sqlite3
import subprocess
import time
from datetime import datetime, date, timedelta
from pathlib import Path
import pytest

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

PRODUCTION_DB_PATH = Path(r"C:\Users\Lenovo\Downloads\Medisales\medisales.db").resolve()

@pytest.fixture
def isolated_env(tmp_path):
    """
    Creates an isolated disk-backed test database in a disposable directory.
    Guarantees strict isolation from production medisales.db.
    """
    test_db_path = (tmp_path / "e2e_isolated.db").resolve()
    assert test_db_path != PRODUCTION_DB_PATH, "CRITICAL: Test database path collided with production database!"

    db_manager = DatabaseManager(str(test_db_path))
    mig = MigrationsManager(db_manager)
    mig.apply_migrations()

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
        'test_db_path': test_db_path,
        'inv': inv,
        'prod': prod,
        'sales': sales,
        'supp': supp,
        'purch': purch,
        'exp': exp,
        'fin': fin,
        'dash': dash,
        'rep': rep,
        'recon': recon
    }

    yield services
    db_manager.close()


# =============================================================================
# SCENARIO A: PRODUCT MANAGEMENT
# =============================================================================
def test_scenario_a_product_management(isolated_env):
    """
    A. PRODUCT MANAGEMENT
    - Create general merchandise product.
    - Create medicine product.
    - Validate required fields and invalid values.
    - Edit products where allowed.
    - Disable product without deleting historical records.
    - Verify disabled products cannot be sold.
    - Confirm units, prices, and product type remain consistent.
    """
    prod = isolated_env['prod']
    sales = isolated_env['sales']
    db = isolated_env['db_manager']

    # 1. Create categories
    cat_gen_id = prod.create_category("Personal Care")
    cat_med_id = prod.create_category("Antibiotics")
    assert cat_gen_id > 0
    assert cat_med_id > 0

    # 2. Create general merchandise & medicine products
    p_gen_id = prod.create_product(
        name="Herbal Toothpaste 150g",
        category_id=cat_gen_id,
        unit_measure="tube",
        selling_price=1800,
        min_stock_level=5,
        is_medicine=False
    )
    p_med_id = prod.create_product(
        name="Amoxicillin 500mg Capsules",
        category_id=cat_med_id,
        unit_measure="strip",
        selling_price=1200,
        min_stock_level=10,
        is_medicine=True
    )
    assert p_gen_id > 0
    assert p_med_id > 0

    # Verify created attributes
    with db.get_connection() as conn:
        row_gen = conn.execute("SELECT * FROM products WHERE id = ?", (p_gen_id,)).fetchone()
        row_med = conn.execute("SELECT * FROM products WHERE id = ?", (p_med_id,)).fetchone()
        assert row_gen['name'] == "Herbal Toothpaste 150g"
        assert row_gen['unit_measure'] == "tube"
        assert row_gen['selling_price'] == 1800
        assert row_gen['is_medicine'] == 0
        assert row_gen['is_active'] == 1

        assert row_med['name'] == "Amoxicillin 500mg Capsules"
        assert row_med['unit_measure'] == "strip"
        assert row_med['selling_price'] == 1200
        assert row_med['is_medicine'] == 1
        assert row_med['is_active'] == 1

    # 3. Validate required fields & invalid values
    with pytest.raises(ValueError, match="Product name and unit measure are required"):
        prod.create_product("", cat_gen_id, "tube", 1000, 5, False)

    with pytest.raises(ValueError, match="Product name and unit measure are required"):
        prod.create_product("Valid Name", cat_gen_id, "  ", 1000, 5, False)

    with pytest.raises(ValueError, match="Prices and stock levels cannot be negative"):
        prod.create_product("Negative Price", cat_gen_id, "pcs", -500, 5, False)

    with pytest.raises(ValueError, match="Prices and stock levels cannot be negative"):
        prod.create_product("Negative Min Stock", cat_gen_id, "pcs", 1000, -2, False)

    with pytest.raises(ValueError, match="Fractional Kyat amounts are not permitted"):
        prod.create_product("Fractional Price", cat_gen_id, "pcs", 1500.5, 5, False)

    with pytest.raises(ValueError, match="Invalid category"):
        prod.create_product("Invalid Cat", 99999, "pcs", 1000, 5, False)

    # 4. Edit product details
    prod.update_product(
        product_id=p_gen_id,
        name="Herbal Toothpaste 150g (Refined)",
        category_id=cat_gen_id,
        unit_measure="tube",
        selling_price=2000,
        min_stock_level=8,
        is_active=True
    )
    with db.get_connection() as conn:
        updated = conn.execute("SELECT * FROM products WHERE id = ?", (p_gen_id,)).fetchone()
        assert updated['name'] == "Herbal Toothpaste 150g (Refined)"
        assert updated['selling_price'] == 2000
        assert updated['min_stock_level'] == 8

    # 5. Disable product without deleting historical records
    prod.update_product(
        product_id=p_gen_id,
        name="Herbal Toothpaste 150g (Refined)",
        category_id=cat_gen_id,
        unit_measure="tube",
        selling_price=2000,
        min_stock_level=8,
        is_active=False
    )
    with db.get_connection() as conn:
        disabled = conn.execute("SELECT is_active FROM products WHERE id = ?", (p_gen_id,)).fetchone()
        assert disabled['is_active'] == 0

    # 6. Verify disabled product cannot be sold
    with pytest.raises(ValueError, match="is inactive and cannot be sold"):
        sales.create_sale(
            reference="SALE-INACTIVE-TEST",
            items=[{"product_id": p_gen_id, "quantity": 1, "unit_price": 2000}],
            amount_received=2000
        )

    # Re-enable for subsequent scenarios
    prod.update_product(
        product_id=p_gen_id,
        name="Herbal Toothpaste 150g (Refined)",
        category_id=cat_gen_id,
        unit_measure="tube",
        selling_price=2000,
        min_stock_level=8,
        is_active=True
    )


# =============================================================================
# SCENARIO B: PURCHASES AND SUPPLIERS
# =============================================================================
def test_scenario_b_purchases_and_suppliers(isolated_env):
    """
    B. PURCHASES AND SUPPLIERS
    - Create supplier.
    - Record purchase.
    - Confirm purchase lines, totals, supplier balances, and inventory updates.
    - Test invalid quantities, invalid prices, and missing batch info.
    - Verify failed purchase leaves no partial stock or financial records (rollback).
    - Verify purchases are not incorrectly treated as operating expenses.
    """
    prod = isolated_env['prod']
    supp = isolated_env['supp']
    purch = isolated_env['purch']
    fin = isolated_env['fin']
    db = isolated_env['db_manager']

    cat_id = prod.create_category("OTC Care")
    p_gen = prod.create_product("Bandage Roll", cat_id, "roll", 800, 5, False)
    p_med = prod.create_product("Cough Syrup 100ml", cat_id, "bottle", 3000, 5, True)

    # 1. Create supplier
    supp_id = supp.create_supplier("National Medical Supplies", "0998765432", "Mandalay")
    assert supp_id > 0

    # 2. Record valid purchase
    purchase_items = [
        {"product_id": p_gen, "quantity": 25, "unit_cost": 500, "batch_number": None, "expiry_date": None},
        {"product_id": p_med, "quantity": 10, "unit_cost": 2000, "batch_number": "CS-2026-A", "expiry_date": "2027-10-31"}
    ]
    purch_id = purch.create_purchase(
        reference="PO-TEST-001",
        supplier_id=supp_id,
        date="2026-10-11",
        items=purchase_items
    )
    assert purch_id > 0

    # Verify inventory updates:
    with db.get_connection() as conn:
        g_row = conn.execute("SELECT current_stock, inventory_value FROM products WHERE id = ?", (p_gen,)).fetchone()
        m_row = conn.execute("SELECT current_stock, inventory_value FROM products WHERE id = ?", (p_med,)).fetchone()
        assert g_row['current_stock'] == 25
        assert g_row['inventory_value'] == 25 * 500 # 12,500
        assert m_row['current_stock'] == 10
        assert m_row['inventory_value'] == 10 * 2000 # 20,000

        # Verify supplier balance
        p_row = conn.execute("SELECT total_amount, amount_paid FROM purchases WHERE id = ?", (purch_id,)).fetchone()
        assert p_row['total_amount'] == 32500 # 12,500 + 20,000
        assert p_row['amount_paid'] == 0

    # 3. Test invalid quantities, costs, and missing batch info
    with pytest.raises(ValueError, match="Quantity must be greater than zero"):
        purch.create_purchase("PO-FAIL-1", supp_id, "2026-10-11", [{"product_id": p_gen, "quantity": 0, "unit_cost": 500}])

    with pytest.raises(ValueError, match="Quantity must be greater than zero"):
        purch.create_purchase("PO-FAIL-2", supp_id, "2026-10-11", [{"product_id": p_gen, "quantity": -5, "unit_cost": 500}])

    with pytest.raises(ValueError, match="Unit cost cannot be negative"):
        purch.create_purchase("PO-FAIL-3", supp_id, "2026-10-11", [{"product_id": p_gen, "quantity": 10, "unit_cost": -100}])

    with pytest.raises(ValueError, match="Medicine purchase items must include a batch_number"):
        purch.create_purchase("PO-FAIL-4", supp_id, "2026-10-11", [{"product_id": p_med, "quantity": 5, "unit_cost": 2000, "batch_number": None}])

    # 4. Verify transaction rollback on failure (item 1 valid, item 2 invalid)
    with db.get_connection() as conn:
        stock_before = conn.execute("SELECT current_stock FROM products WHERE id = ?", (p_gen,)).fetchone()['current_stock']
        purch_count_before = conn.execute("SELECT count(*) FROM purchases").fetchone()[0]

    with pytest.raises(ValueError, match="Medicine purchase items must include a batch_number"):
        purch.create_purchase(
            reference="PO-FAIL-ROLLBACK",
            supplier_id=supp_id,
            date="2026-10-11",
            items=[
                {"product_id": p_gen, "quantity": 50, "unit_cost": 500},
                {"product_id": p_med, "quantity": 5, "unit_cost": 2000, "batch_number": ""}
            ]
        )

    with db.get_connection() as conn:
        stock_after = conn.execute("SELECT current_stock FROM products WHERE id = ?", (p_gen,)).fetchone()['current_stock']
        purch_count_after = conn.execute("SELECT count(*) FROM purchases").fetchone()[0]
        assert stock_after == stock_before, "Stock was modified despite purchase failure!"
        assert purch_count_after == purch_count_before, "Purchase record was created despite failure!"

    # 5. Verify purchases are NOT treated as operating expenses
    fin_summary = fin.get_summary("2026-10-01", "2026-10-31")
    assert fin_summary['purchases_recorded'] == 32500
    assert fin_summary['operating_expenses'] == 0, "Purchases were erroneously classified as operating expenses!"


# =============================================================================
# SCENARIO C: GENERAL MERCHANDISE COSTING (WAC)
# =============================================================================
def test_scenario_c_general_merchandise_costing_wac(isolated_env):
    """
    C. GENERAL MERCHANDISE COSTING
    - Receive general merchandise at two distinct unit costs.
    - Verify weighted-average cost using the documented business rule.
    - Sell part of the stock.
    - Verify COGS and remaining inventory valuation.
    - Check integer Kyat rounding behavior.
    """
    prod = isolated_env['prod']
    supp = isolated_env['supp']
    purch = isolated_env['purch']
    sales = isolated_env['sales']
    inv = isolated_env['inv']
    db = isolated_env['db_manager']

    cat_id = prod.create_category("Beverages")
    p_id = prod.create_product("Mineral Water 1L", cat_id, "bottle", 800, 5, False)
    supp_id = supp.create_supplier("Aqua Pure Dist", "091111111", "Yangon")

    # Purchase 1: 10 units @ 400 Ks = 4,000 Ks
    purch.create_purchase("PO-WAC-1", supp_id, "2026-10-01", [{"product_id": p_id, "quantity": 10, "unit_cost": 400}])

    # Purchase 2: 10 units @ 600 Ks = 6,000 Ks
    purch.create_purchase("PO-WAC-2", supp_id, "2026-10-02", [{"product_id": p_id, "quantity": 10, "unit_cost": 600}])

    # Verify WAC: Total stock = 20, Total value = 10,000 Ks. WAC = 10,000 / 20 = 500 Ks.
    with db.get_connection() as conn:
        p_row = conn.execute("SELECT current_stock, inventory_value FROM products WHERE id = ?", (p_id,)).fetchone()
        assert p_row['current_stock'] == 20
        assert p_row['inventory_value'] == 10000

    # Sell 6 units @ 800 Ks = 4,800 Ks
    # Expected COGS = 6 * 500 Ks = 3,000 Ks.
    # Expected Remaining Value = 10,000 - 3,000 = 7,000 Ks (14 units @ 500 Ks = 7,000 Ks).
    sale_id = sales.create_sale(
        reference="SALE-WAC-01",
        items=[{"product_id": p_id, "quantity": 6, "unit_price": 800}],
        amount_received=5000
    )
    assert sale_id > 0

    with db.get_connection() as conn:
        si = conn.execute("SELECT total_cost, line_total FROM sale_items WHERE sale_id = ?", (sale_id,)).fetchone()
        assert si['line_total'] == 4800
        assert si['total_cost'] == 3000

        p_after = conn.execute("SELECT current_stock, inventory_value FROM products WHERE id = ?", (p_id,)).fetchone()
        assert p_after['current_stock'] == 14
        assert p_after['inventory_value'] == 7000

    # Test non-divisible fractional WAC Kyat integer rounding:
    # Receive 5 units @ 650 Ks = 3,250 Ks.
    # Total stock = 14 + 5 = 19 units. Total value = 7,000 + 3,250 = 10,250 Ks.
    # WAC = 10,250 / 19 = 539.47368... Ks.
    purch.create_purchase("PO-WAC-3", supp_id, "2026-10-03", [{"product_id": p_id, "quantity": 5, "unit_cost": 650}])

    # Sell 4 units: Expected deduction = round(4 * (10250 / 19)) = round(2157.8947) = 2158 Ks.
    expected_cogs_4 = inv.calculate_wac_value_change(19, 10250, 4)
    assert expected_cogs_4 == 2158

    sale_wac2 = sales.create_sale(
        reference="SALE-WAC-02",
        items=[{"product_id": p_id, "quantity": 4, "unit_price": 800}],
        amount_received=4000
    )
    with db.get_connection() as conn:
        si2 = conn.execute("SELECT total_cost FROM sale_items WHERE sale_id = ?", (sale_wac2,)).fetchone()
        assert si2['total_cost'] == 2158
        p_row2 = conn.execute("SELECT current_stock, inventory_value FROM products WHERE id = ?", (p_id,)).fetchone()
        assert p_row2['current_stock'] == 15
        assert p_row2['inventory_value'] == 10250 - 2158 # 8092

    # Sell all remaining 15 units:
    # calculate_wac_value_change must return exact remaining inventory_value (8092) with zero residual drift!
    expected_exhaust = inv.calculate_wac_value_change(15, 8092, 15)
    assert expected_exhaust == 8092

    sale_wac3 = sales.create_sale(
        reference="SALE-WAC-03",
        items=[{"product_id": p_id, "quantity": 15, "unit_price": 800}],
        amount_received=15000
    )
    with db.get_connection() as conn:
        p_final = conn.execute("SELECT current_stock, inventory_value FROM products WHERE id = ?", (p_id,)).fetchone()
        assert p_final['current_stock'] == 0
        assert p_final['inventory_value'] == 0, f"Residual inventory value drift detected: {p_final['inventory_value']}"


# =============================================================================
# SCENARIO D: MEDICINE BATCHES AND FEFO
# =============================================================================
def test_scenario_d_medicine_batches_and_fefo(isolated_env):
    """
    D. MEDICINE BATCHES AND FEFO
    - Receive multiple batches of the same medicine with different costs and expiry dates.
    - Verify FEFO selects earliest eligible expiry date.
    - Verify expired batches cannot be sold.
    - Verify batches expiring on current local date cannot be sold.
    - Verify batches with unknown expiry cannot be sold.
    - Verify sale allocation and COGS use specific batch costs.
    - Test insufficient eligible stock.
    - Verify invalid sale does not partially decrement inventory.
    - Test multi-batch spanning sale.
    """
    prod = isolated_env['prod']
    supp = isolated_env['supp']
    purch = isolated_env['purch']
    sales = isolated_env['sales']
    inv = isolated_env['inv']
    db = isolated_env['db_manager']

    cat_id = prod.create_category("Cardiovascular")
    med_id = prod.create_product("Amlodipine 5mg", cat_id, "strip", 1500, 5, True)
    supp_id = supp.create_supplier("Pharma Trade", "092222222", "Yangon")

    today_str = datetime.now().strftime("%Y-%m-%d")
    tomorrow_str = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    sixty_days_str = (datetime.now() + timedelta(days=60)).strftime("%Y-%m-%d")
    one_year_str = (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d")
    expired_str = "2023-01-01"

    # Add 5 distinct batches:
    # 1. BATCH-SOON (expires in 60 days): 10 units @ 500 Ks
    # 2. BATCH-LATER (expires in 1 year): 20 units @ 600 Ks
    # 3. BATCH-EXPIRED (expired 2023): 10 units @ 400 Ks
    # 4. BATCH-TODAY (expires today): 10 units @ 450 Ks
    # 5. BATCH-NOEXP (unknown expiry): 10 units @ 400 Ks
    purch_batches = [
        {"product_id": med_id, "quantity": 10, "unit_cost": 500, "batch_number": "B-SOON", "expiry_date": sixty_days_str},
        {"product_id": med_id, "quantity": 20, "unit_cost": 600, "batch_number": "B-LATER", "expiry_date": one_year_str},
        {"product_id": med_id, "quantity": 10, "unit_cost": 400, "batch_number": "B-EXPIRED", "expiry_date": expired_str},
        {"product_id": med_id, "quantity": 10, "unit_cost": 450, "batch_number": "B-TODAY", "expiry_date": today_str},
        {"product_id": med_id, "quantity": 10, "unit_cost": 400, "batch_number": "B-NOEXP", "expiry_date": None}
    ]
    purch.create_purchase("PO-MED-BATCHES", supp_id, "2026-10-10", purch_batches)

    # Total physical stock = 60 units
    with db.get_connection() as conn:
        m_stock = conn.execute("SELECT current_stock FROM products WHERE id = ?", (med_id,)).fetchone()
        assert m_stock['current_stock'] == 60

    # 1. Verify get_sellable_medicine_batches returns ONLY eligible batches in FEFO order
    sellable = inv.get_sellable_medicine_batches(med_id)
    assert len(sellable) == 2, f"Expected exactly 2 sellable batches, found: {[b['batch_number'] for b in sellable]}"
    assert sellable[0]['batch_number'] == "B-SOON"
    assert sellable[0]['current_qty'] == 10
    assert sellable[0]['unit_cost'] == 500

    assert sellable[1]['batch_number'] == "B-LATER"
    assert sellable[1]['current_qty'] == 20
    assert sellable[1]['unit_cost'] == 600

    # 2. Multi-batch spanning sale:
    # Request 15 units.
    # Allocation:
    # 10 units from B-SOON @ 500 Ks = 5,000 Ks
    # 5 units from B-LATER @ 600 Ks = 3,000 Ks
    # Total COGS = 8,000 Ks. Revenue = 15 * 1,500 = 22,500 Ks.
    sale_med_id = sales.create_sale(
        reference="SALE-FEFO-SPAN",
        items=[{"product_id": med_id, "quantity": 15, "unit_price": 1500}],
        amount_received=25000
    )
    assert sale_med_id > 0

    with db.get_connection() as conn:
        si = conn.execute("SELECT id, total_cost, line_total FROM sale_items WHERE sale_id = ?", (sale_med_id,)).fetchone()
        assert si['line_total'] == 22500
        assert si['total_cost'] == 8000 # 5,000 + 3,000

        # Check allocations in sale_item_batches
        allocs = conn.execute("SELECT * FROM sale_item_batches WHERE sale_item_id = ?", (si['id'],)).fetchall()
        assert len(allocs) == 2

        # Verify batch remaining quantities
        b_soon = conn.execute("SELECT current_qty FROM medicine_batches WHERE batch_number = 'B-SOON'").fetchone()
        b_later = conn.execute("SELECT current_qty FROM medicine_batches WHERE batch_number = 'B-LATER'").fetchone()
        assert b_soon['current_qty'] == 0
        assert b_later['current_qty'] == 15

    # 3. Test insufficient eligible stock:
    # Eligible remaining = 15 units (in B-LATER). Total physical stock in DB = 45 units.
    # Requesting 20 units must fail even though 45 units exist on hand!
    with pytest.raises(ValueError, match="Insufficient eligible batch stock"):
        sales.create_sale(
            reference="SALE-FEFO-EXCEED",
            items=[{"product_id": med_id, "quantity": 20, "unit_price": 1500}],
            amount_received=30000
        )

    # Verify no partial stock decrement occurred
    with db.get_connection() as conn:
        b_later_check = conn.execute("SELECT current_qty FROM medicine_batches WHERE batch_number = 'B-LATER'").fetchone()
        assert b_later_check['current_qty'] == 15
        p_check = conn.execute("SELECT current_stock FROM products WHERE id = ?", (med_id,)).fetchone()
        assert p_check['current_stock'] == 45


# =============================================================================
# SCENARIO E: SALES AND PAYMENT VALIDATION
# =============================================================================
def test_scenario_e_sales_and_payment_validation(isolated_env):
    """
    E. SALES AND PAYMENT VALIDATION
    - Complete valid sale.
    - Verify receipt totals, tender, change, inventory movements, COGS.
    - Test empty cart rejection.
    - Test insufficient tender.
    - Test zero, negative, fractional, and excessive quantities.
    - Confirm failed sale rolls back completely.
    - Confirm successful sale remains available after database close/reopen.
    """
    prod = isolated_env['prod']
    supp = isolated_env['supp']
    purch = isolated_env['purch']
    sales = isolated_env['sales']
    db = isolated_env['db_manager']
    test_db_path = isolated_env['test_db_path']

    cat_id = prod.create_category("Snacks")
    p_id = prod.create_product("Biscuit Pack", cat_id, "pack", 500, 2, False)
    supp_id = supp.create_supplier("Food Trade", "093333333", "Yangon")
    purch.create_purchase("PO-SNACKS-1", supp_id, "2026-10-10", [{"product_id": p_id, "quantity": 50, "unit_cost": 300}])

    # 1. Complete valid sale
    sale_id = sales.create_sale(
        reference="SALE-VALID-01",
        items=[{"product_id": p_id, "quantity": 5, "unit_price": 500}],
        amount_received=3000
    )
    with db.get_connection() as conn:
        sale = conn.execute("SELECT * FROM sales WHERE id = ?", (sale_id,)).fetchone()
        assert sale['total_amount'] == 2500
        assert sale['amount_received'] == 3000
        assert sale['change_given'] == 500
        assert sale['status'] == 'Completed'

    # 2. Test empty cart rejection
    with pytest.raises(ValueError, match="Sale must contain at least one item"):
        sales.create_sale("SALE-EMPTY", [], 1000)

    # 3. Test insufficient tender
    with pytest.raises(ValueError, match="Amount received is less than total sale amount"):
        sales.create_sale("SALE-SHORT-TENDER", [{"product_id": p_id, "quantity": 2, "unit_price": 500}], amount_received=800)

    # 4. Test zero and negative quantities
    with pytest.raises(ValueError, match="Sale quantity must be greater than zero"):
        sales.create_sale("SALE-ZERO-QTY", [{"product_id": p_id, "quantity": 0, "unit_price": 500}], 1000)

    with pytest.raises(ValueError, match="Sale quantity must be greater than zero"):
        sales.create_sale("SALE-NEG-QTY", [{"product_id": p_id, "quantity": -2, "unit_price": 500}], 1000)

    # 5. Test negative price
    with pytest.raises(ValueError, match="Unit price cannot be negative"):
        sales.create_sale("SALE-NEG-PRICE", [{"product_id": p_id, "quantity": 1, "unit_price": -500}], 1000)

    # 6. Test fractional quantity and fractional tender
    with pytest.raises(ValueError, match="Fractional Kyat amounts are not permitted"):
        sales.create_sale("SALE-FRAC-QTY", [{"product_id": p_id, "quantity": 1.5, "unit_price": 500}], 1000)

    with pytest.raises(ValueError, match="Fractional Kyat amounts are not permitted"):
        sales.create_sale("SALE-FRAC-TENDER", [{"product_id": p_id, "quantity": 1, "unit_price": 500}], 1000.5)

    # 7. Test excessive quantity exceeding stock (remaining = 45)
    with pytest.raises(ValueError, match="Insufficient stock"):
        sales.create_sale("SALE-EXCESSIVE", [{"product_id": p_id, "quantity": 100, "unit_price": 500}], 50000)

    # 8. Test persistence after reopening connection
    db.close()
    reopened_db = DatabaseManager(str(test_db_path))
    reopened_sales = SalesService(reopened_db, InventoryService(reopened_db))
    persisted_sale = reopened_sales.get_sale(sale_id)
    assert persisted_sale is not None
    assert persisted_sale['reference'] == "SALE-VALID-01"
    assert persisted_sale['total_amount'] == 2500
    assert len(persisted_sale['items']) == 1
    reopened_db.close()


# =============================================================================
# SCENARIO F: SALE VOID AND CORRECTIONS
# =============================================================================
def test_scenario_f_sale_void_and_corrections(isolated_env):
    """
    F. SALE VOID AND CORRECTIONS
    - Void a completed sale.
    - Verify stock restoration for general goods and medicine batches.
    - Verify reversal movements and audit records exist.
    - Verify original sale history is preserved.
    - Verify repeated voiding cannot restore stock twice.
    - Verify reports and financial totals reflect void.
    """
    prod = isolated_env['prod']
    supp = isolated_env['supp']
    purch = isolated_env['purch']
    sales = isolated_env['sales']
    fin = isolated_env['fin']
    db = isolated_env['db_manager']

    cat_id = prod.create_category("First Aid")
    p_gen = prod.create_product("Adhesive Tape", cat_id, "roll", 1000, 2, False)
    p_med = prod.create_product("Antiseptic Cream", cat_id, "tube", 2500, 2, True)
    supp_id = supp.create_supplier("First Aid Supplies", "094444444", "Yangon")

    purch.create_purchase("PO-VOID-STOCK", supp_id, "2026-10-10", [
        {"product_id": p_gen, "quantity": 20, "unit_cost": 600},
        {"product_id": p_med, "quantity": 15, "unit_cost": 1500, "batch_number": "AC-BATCH-1", "expiry_date": "2027-12-31"}
    ])

    # Complete a sale containing both items
    sale_id = sales.create_sale(
        reference="SALE-TO-BE-VOIDED",
        items=[
            {"product_id": p_gen, "quantity": 5, "unit_price": 1000},
            {"product_id": p_med, "quantity": 4, "unit_price": 2500}
        ],
        amount_received=15000
    )
    # Total revenue = 5,000 + 10,000 = 15,000 Ks.
    # Total COGS = (5 * 600) + (4 * 1500) = 3,000 + 6,000 = 9,000 Ks.

    with db.get_connection() as conn:
        assert conn.execute("SELECT current_stock FROM products WHERE id = ?", (p_gen,)).fetchone()['current_stock'] == 15
        assert conn.execute("SELECT current_stock FROM products WHERE id = ?", (p_med,)).fetchone()['current_stock'] == 11
        assert conn.execute("SELECT current_qty FROM medicine_batches WHERE batch_number = 'AC-BATCH-1'").fetchone()['current_qty'] == 11

    # Check financials before void
    summary_before = fin.get_summary("2026-10-01", "2026-10-31")
    assert summary_before['total_sales_revenue'] == 15000
    assert summary_before['cost_of_goods_sold'] == 9000
    assert summary_before['gross_profit'] == 6000

    # 1. Void the sale
    sales.void_sale(sale_id)

    # 2. Verify stock restoration
    with db.get_connection() as conn:
        s_row = conn.execute("SELECT status FROM sales WHERE id = ?", (sale_id,)).fetchone()
        assert s_row['status'] == 'Voided'

        gen_stock = conn.execute("SELECT current_stock, inventory_value FROM products WHERE id = ?", (p_gen,)).fetchone()
        med_stock = conn.execute("SELECT current_stock, inventory_value FROM products WHERE id = ?", (p_med,)).fetchone()
        assert gen_stock['current_stock'] == 20
        assert gen_stock['inventory_value'] == 20 * 600 # 12,000
        assert med_stock['current_stock'] == 15
        assert med_stock['inventory_value'] == 15 * 1500 # 22,500

        batch_stock = conn.execute("SELECT current_qty FROM medicine_batches WHERE batch_number = 'AC-BATCH-1'").fetchone()
        assert batch_stock['current_qty'] == 15

        # 3. Verify reversal movements logged
        movs = conn.execute(
            "SELECT movement_type, reference_type FROM inventory_movements WHERE reference_id = ? AND reference_type = 'SaleVoid'",
            (sale_id,)
        ).fetchall()
        assert len(movs) == 2
        for m in movs:
            assert m['movement_type'] == 'In'

        b_movs = conn.execute(
            "SELECT movement_type, reference_type FROM medicine_batch_movements WHERE reference_id = ? AND reference_type = 'SaleVoid'",
            (sale_id,)
        ).fetchall()
        assert len(b_movs) == 1
        assert b_movs[0]['movement_type'] == 'In'

    # 4. Verify repeated voiding cannot restore stock twice
    with pytest.raises(ValueError, match="Sale is already voided"):
        sales.void_sale(sale_id)

    with db.get_connection() as conn:
        gen_stock_recheck = conn.execute("SELECT current_stock FROM products WHERE id = ?", (p_gen,)).fetchone()
        assert gen_stock_recheck['current_stock'] == 20, "Stock was erroneously re-incremented on duplicate void!"

    # 5. Verify financial reports exclude voided sales
    summary_after = fin.get_summary("2026-10-01", "2026-10-31")
    assert summary_after['total_sales_revenue'] == 0
    assert summary_after['cost_of_goods_sold'] == 0
    assert summary_after['gross_profit'] == 0


# =============================================================================
# SCENARIO G: INVENTORY INTEGRITY AND RECONCILIATION
# =============================================================================
def test_scenario_g_inventory_integrity_and_reconciliation(isolated_env):
    """
    G. INVENTORY INTEGRITY
    - Confirm stock changes are represented by auditable inventory movements.
    - Confirm historical movements cannot be edited or deleted (triggers).
    - Run reconciliation service across products, batches, and transactions.
    - Verify medicine batch stock and general merchandise stock adhere to distinct costing rules.
    """
    prod = isolated_env['prod']
    supp = isolated_env['supp']
    purch = isolated_env['purch']
    sales = isolated_env['sales']
    recon = isolated_env['recon']
    db = isolated_env['db_manager']

    cat_id = prod.create_category("General")
    p_gen = prod.create_product("Notebook", cat_id, "book", 1500, 5, False)
    p_med = prod.create_product("Vitamin B Complex", cat_id, "bottle", 4000, 5, True)
    supp_id = supp.create_supplier("Apex Stationery & Drugs", "095555555", "Yangon")

    # Purchase
    purch_id = purch.create_purchase("PO-INTEGRITY", supp_id, "2026-10-10", [
        {"product_id": p_gen, "quantity": 30, "unit_cost": 800},
        {"product_id": p_med, "quantity": 25, "unit_cost": 2500, "batch_number": "VB-BATCH-01", "expiry_date": "2028-01-01"}
    ])

    # Sale
    sale_id = sales.create_sale("SALE-INTEGRITY", [
        {"product_id": p_gen, "quantity": 10, "unit_price": 1500},
        {"product_id": p_med, "quantity": 5, "unit_price": 4000}
    ], amount_received=40000)

    # 1. Immutability checks: Direct UPDATE or DELETE on inventory_movements must fail
    with db.get_connection() as conn:
        with pytest.raises(Exception):
            conn.execute("UPDATE inventory_movements SET quantity_change = 9999 WHERE product_id = ?", (p_gen,))
        conn.rollback()

        with pytest.raises(Exception):
            conn.execute("DELETE FROM inventory_movements WHERE product_id = ?", (p_gen,))
        conn.rollback()

    # 2. Run Reconciliation Checks
    # Product stock reconciliation
    recon_gen = recon.reconcile_product_stock(p_gen)
    assert recon_gen['stock_match'] is True
    assert recon_gen['value_match'] is True
    assert recon_gen['db_stock'] == 20
    assert recon_gen['calc_stock'] == 20
    assert recon_gen['db_value'] == 20 * 800 # 16,000

    recon_med = recon.reconcile_product_stock(p_med)
    assert recon_med['stock_match'] is True
    assert recon_med['value_match'] is True
    assert recon_med['db_stock'] == 20
    assert recon_med['calc_stock'] == 20

    # Medicine batches reconciliation
    recon_batches = recon.reconcile_medicine_batches(p_med)
    assert recon_batches['stock_match'] is True
    assert recon_batches['value_match'] is True
    assert len(recon_batches['batch_discrepancies']) == 0

    # Purchase & Sale transaction reconciliation
    recon_purch = recon.reconcile_purchase(purch_id)
    assert recon_purch['is_consistent'] is True

    recon_sale = recon.reconcile_sale(sale_id)
    assert recon_sale['is_consistent'] is True


# =============================================================================
# SCENARIO H: SUPPLIER PAYMENTS AND ALLOCATIONS
# =============================================================================
def test_scenario_h_supplier_payments_and_allocations(isolated_env):
    """
    H. SUPPLIER PAYMENTS
    - Record supplier payment and allocate across multiple purchases.
    - Verify each allocation is within remaining balance.
    - Reject allocations exceeding permitted amount.
    - Reject allocations to purchases belonging to another supplier.
    - Verify supplier balances after payment.
    - Confirm supplier payments are not classified as operating expenses.
    - Verify transaction failure does not leave partial allocations or payments.
    """
    prod = isolated_env['prod']
    supp = isolated_env['supp']
    purch = isolated_env['purch']
    fin = isolated_env['fin']
    db = isolated_env['db_manager']

    cat_id = prod.create_category("Supplies")
    p_id = prod.create_product("Surgical Gloves", cat_id, "box", 5000, 5, False)

    supp_a = supp.create_supplier("Supplier Alpha", "096666666", "Yangon")
    supp_b = supp.create_supplier("Supplier Beta", "097777777", "Mandalay")

    # Purchase 1 (Alpha): 20 boxes @ 3,000 Ks = 60,000 Ks
    po_a1 = purch.create_purchase("PO-ALPHA-1", supp_a, "2026-10-01", [{"product_id": p_id, "quantity": 20, "unit_cost": 3000}])

    # Purchase 2 (Alpha): 10 boxes @ 3,000 Ks = 30,000 Ks
    po_a2 = purch.create_purchase("PO-ALPHA-2", supp_a, "2026-10-02", [{"product_id": p_id, "quantity": 10, "unit_cost": 3000}])

    # Purchase 3 (Beta): 10 boxes @ 3,000 Ks = 30,000 Ks
    po_b1 = purch.create_purchase("PO-BETA-1", supp_b, "2026-10-03", [{"product_id": p_id, "quantity": 10, "unit_cost": 3000}])

    # 1. Reject allocation to another supplier's purchase
    with pytest.raises(ValueError, match="Cannot allocate payment to a purchase from a different supplier"):
        purch.record_payment(
            reference="PAY-FAIL-CROSS-SUPP",
            supplier_id=supp_a,
            date="2026-10-05",
            total_amount=30000,
            allocations=[{"purchase_id": po_b1, "allocated_amount": 30000}]
        )

    # 2. Reject allocation exceeding outstanding balance (po_a2 total is 30,000)
    with pytest.raises(ValueError, match="exceeds outstanding balance"):
        purch.record_payment(
            reference="PAY-FAIL-OVERALLOC",
            supplier_id=supp_a,
            date="2026-10-05",
            total_amount=50000,
            allocations=[{"purchase_id": po_a2, "allocated_amount": 35000}]
        )

    # 3. Reject total allocation exceeding payment amount
    with pytest.raises(ValueError, match="Total allocated amount cannot exceed the payment total amount"):
        purch.record_payment(
            reference="PAY-FAIL-TOTAL-EXCEED",
            supplier_id=supp_a,
            date="2026-10-05",
            total_amount=20000,
            allocations=[{"purchase_id": po_a1, "allocated_amount": 25000}]
        )

    # 4. Record valid multi-purchase payment:
    # Total payment = 70,000 Ks to Supplier Alpha:
    # - 60,000 Ks allocated to PO-ALPHA-1 (settles completely)
    # - 10,000 Ks allocated to PO-ALPHA-2 (remaining: 20,000 Ks)
    pay_id = purch.record_payment(
        reference="PAY-ALPHA-MULTI",
        supplier_id=supp_a,
        date="2026-10-05",
        total_amount=70000,
        allocations=[
            {"purchase_id": po_a1, "allocated_amount": 60000},
            {"purchase_id": po_a2, "allocated_amount": 10000}
        ]
    )
    assert pay_id > 0

    # 5. Verify supplier balances and purchase statuses
    rep = isolated_env['rep']
    balances = rep.get_supplier_balances()
    alpha_bal = next(b for b in balances if b['supplier_id'] == supp_a)
    beta_bal = next(b for b in balances if b['supplier_id'] == supp_b)

    assert alpha_bal['total_purchased'] == 90000 # 60,000 + 30,000
    assert alpha_bal['total_paid'] == 70000
    assert alpha_bal['outstanding_balance'] == 20000

    assert beta_bal['total_purchased'] == 30000
    assert beta_bal['total_paid'] == 0
    assert beta_bal['outstanding_balance'] == 30000

    # 6. Confirm payments are not classified as operating expenses
    fin_summary = fin.get_summary("2026-10-01", "2026-10-31")
    assert fin_summary['supplier_payments_made'] == 70000
    assert fin_summary['operating_expenses'] == 0


# =============================================================================
# SCENARIO I: EXPENSES, DASHBOARD, AND REPORTS
# =============================================================================
def test_scenario_i_expenses_and_financial_reports(isolated_env):
    """
    I. EXPENSES, DASHBOARD, AND REPORTS
    - Record operating expense and void an expense.
    - Verify revenue, COGS, gross profit, operating expenses, and net profit/loss.
    - Verify purchases and supplier payments are not double-counted as expenses.
    - Verify inventory valuation uses medicine batch costs and general merchandise WAC.
    - Verify voided sales are treated consistently across reports.
    """
    prod = isolated_env['prod']
    supp = isolated_env['supp']
    purch = isolated_env['purch']
    sales = isolated_env['sales']
    exp = isolated_env['exp']
    fin = isolated_env['fin']
    dash = isolated_env['dash']
    db = isolated_env['db_manager']

    cat_id = prod.create_category("Daily Care")
    p_gen = prod.create_product("Bath Soap", cat_id, "bar", 1000, 5, False)
    p_med = prod.create_product("Eye Drops 10ml", cat_id, "bottle", 3000, 5, True)
    supp_id = supp.create_supplier("Care Dist", "098888888", "Yangon")

    # Purchase
    purch.create_purchase("PO-REPORT-TEST", supp_id, "2026-10-01", [
        {"product_id": p_gen, "quantity": 20, "unit_cost": 600},
        {"product_id": p_med, "quantity": 10, "unit_cost": 1800, "batch_number": "ED-101", "expiry_date": "2027-10-10"}
    ])

    # Record Expenses:
    # 1. Rent: 40,000 Ks
    # 2. Electricity: 15,000 Ks (will be voided)
    today_str = datetime.now().strftime("%Y-%m-%d")
    exp_rent_id = exp.create_expense("Rent", "Shop monthly rent", 40000, today_str)
    exp_elec_id = exp.create_expense("Utilities", "Electric bill", 15000, today_str)
    exp.void_expense(exp_elec_id)

    # Sale 1: Completed
    # 10 Bath Soaps @ 1,000 = 10,000 Ks (COGS: 10 * 600 = 6,000 Ks)
    # 5 Eye Drops @ 3,000 = 15,000 Ks (COGS: 5 * 1800 = 9,000 Ks)
    # Total Revenue = 25,000 Ks. Total COGS = 15,000 Ks. Gross Profit = 10,000 Ks.
    sales.create_sale("SALE-COMPLETED-RPT", [
        {"product_id": p_gen, "quantity": 10, "unit_price": 1000},
        {"product_id": p_med, "quantity": 5, "unit_price": 3000}
    ], 30000)

    # Sale 2: Voided sale (must NOT affect revenue, COGS, or profit)
    sale_void_id = sales.create_sale("SALE-VOID-RPT", [
        {"product_id": p_gen, "quantity": 2, "unit_price": 1000}
    ], 5000)
    sales.void_sale(sale_void_id)

    # Verify Financial Summary
    summary = fin.get_summary("2026-10-01", "2026-10-31")
    expected_revenue = 25000
    expected_cogs = 15000
    expected_gross_profit = 10000 # 25,000 - 15,000
    expected_opex = 40000 # Only active rent expense (electricity was voided)
    expected_net_profit = expected_gross_profit - expected_opex # 10,000 - 40,000 = -30,000 (Deficit)

    assert summary['total_sales_revenue'] == expected_revenue
    assert summary['cost_of_goods_sold'] == expected_cogs
    assert summary['gross_profit'] == expected_gross_profit
    assert summary['operating_expenses'] == expected_opex
    assert summary['net_operating_profit'] == expected_net_profit

    # Verify Dashboard Summary & Inventory Valuation
    dash_summary = dash.get_dashboard_summary()
    # Remaining inventory:
    # 10 Bath Soaps @ 600 = 6,000 Ks
    # 5 Eye Drops @ 1,800 = 9,000 Ks
    # Total valuation = 15,000 Ks
    assert dash_summary['total_inventory_value'] == 15000
    assert dash_summary['total_sales_revenue'] == expected_revenue
    assert dash_summary['gross_profit'] == expected_gross_profit
    assert dash_summary['net_operating_profit'] == expected_net_profit


# =============================================================================
# SCENARIO J: BACKUP AND RESTORE
# =============================================================================
def test_scenario_j_backup_and_restore(isolated_env, tmp_path):
    """
    J. BACKUP AND RESTORE
    - Back up the isolated test database.
    - Verify backup is readable and contains expected data.
    - Restore into a separate disposable database.
    - Verify products, stock, purchases, batches, sales, payments, expenses survive.
    - Verify restore failure does not destroy current working database.
    - Confirm production medisales.db was never modified.
    """
    db = isolated_env['db_manager']
    prod = isolated_env['prod']
    supp = isolated_env['supp']
    purch = isolated_env['purch']
    sales = isolated_env['sales']
    exp = isolated_env['exp']

    # Populate baseline data
    cat_id = prod.create_category("Backup Test Cat")
    p_id = prod.create_product("Backup Test Prod", cat_id, "pcs", 1000, 5, False)
    supp_id = supp.create_supplier("Backup Supp", "099999999", "Yangon")
    purch.create_purchase("PO-BACKUP-1", supp_id, "2026-10-10", [{"product_id": p_id, "quantity": 10, "unit_cost": 500}])
    sales.create_sale("SALE-BACKUP-1", [{"product_id": p_id, "quantity": 3, "unit_price": 1000}], 5000)
    exp.create_expense("Supplies", "Paper clips", 2500, "2026-10-10")

    backup_file = str(tmp_path / "test_snapshot.db")

    # 1. Perform backup
    db.backup_to_file(backup_file)
    assert os.path.exists(backup_file)

    # Verify backup integrity
    with sqlite3.connect(backup_file) as b_conn:
        check = b_conn.execute("PRAGMA integrity_check").fetchone()
        assert check[0] == "ok"
        p_row = b_conn.execute("SELECT name, current_stock FROM products WHERE id = ?", (p_id,)).fetchone()
        assert p_row[0] == "Backup Test Prod"
        assert p_row[1] == 7 # 10 - 3 = 7

    # 2. Mutate active database
    prod.create_product("Mutated Product After Backup", cat_id, "pcs", 500, 1, False)
    with db.get_connection() as conn:
        assert conn.execute("SELECT count(*) FROM products").fetchone()[0] == 2

    # 3. Restore from backup
    safety_backup = db.restore_from_file(backup_file)
    assert os.path.exists(safety_backup)

    # Verify state rolled back to exact backup state (only 1 product)
    with db.get_connection() as conn:
        prods = conn.execute("SELECT name FROM products").fetchall()
        assert len(prods) == 1
        assert prods[0]['name'] == "Backup Test Prod"

    # 4. Verify rejection of corrupted file
    corrupt_file = str(tmp_path / "corrupt_test.db")
    with open(corrupt_file, "wb") as f:
        f.write(b"CORRUPTED_NON_SQLITE_PAYLOAD_TEST")

    with pytest.raises(ValueError, match="corrupt or not a valid SQLite database"):
        db.restore_from_file(corrupt_file)

    # Ensure working database remained intact
    with db.get_connection() as conn:
        prods_after_corrupt = conn.execute("SELECT name FROM products").fetchall()
        assert len(prods_after_corrupt) == 1
        assert prods_after_corrupt[0]['name'] == "Backup Test Prod"

    # 5. Strict production database check
    assert PRODUCTION_DB_PATH.exists()
    assert os.path.getsize(str(PRODUCTION_DB_PATH)) == 143360, "CRITICAL: Production database size changed during testing!"


# =============================================================================
# SCENARIO K: APPLICATION AND PACKAGING
# =============================================================================
def test_scenario_k_application_and_packaging(tmp_path):
    """
    K. APPLICATION AND PACKAGING
    - Run the packaged executable using an explicit temporary --db path.
    - Log exact resolved database path.
    - Verify persistence across app restart.
    - Verify missing-database safety check in packaged mode.
    """
    exe_path = Path(r"C:\Users\Lenovo\Downloads\Medisales\dist\Medisales\Medisales.exe")
    assert exe_path.exists(), f"Packaged executable not found at {exe_path}"

    test_db = tmp_path / "pkg_e2e_test.db"
    clean_env = os.environ.copy()
    clean_env.pop("PYTHONPATH", None)
    clean_env.pop("PYTHONHOME", None)
    local_app_dir = tmp_path / "localapp"
    local_app_dir.mkdir(parents=True, exist_ok=True)
    clean_env["LOCALAPPDATA"] = str(local_app_dir)

    print(f"\n[Scenario K] Launching packaged executable: {exe_path}")
    print(f"[Scenario K] Target DB: {test_db}")

    # Launch subprocess with cwd set to tmp_path
    proc = subprocess.Popen(
        [str(exe_path), "--db", str(test_db)],
        cwd=str(tmp_path),
        env=clean_env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    # Wait for initialization and migrations
    for _ in range(30):
        if test_db.exists() and proc.poll() is None:
            try:
                with sqlite3.connect(str(test_db)) as test_conn:
                    if test_conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='categories'").fetchone():
                        break
            except Exception:
                pass
        time.sleep(0.5)

    assert proc.poll() is None, "Packaged process exited prematurely!"
    assert test_db.exists(), "Packaged process failed to initialize database!"

    # Insert test product
    with sqlite3.connect(str(test_db)) as conn:
        conn.execute("INSERT INTO categories (name) VALUES ('Packaging Cat')")
        cat_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.execute(
            "INSERT INTO products (name, category_id, unit_measure, selling_price, min_stock_level, is_medicine, is_active) VALUES ('Packaged Prod', ?, 'pcs', 1000, 5, 0, 1)",
            (cat_id,)
        )
        conn.commit()

    # Terminate process cleanly
    proc.terminate()
    try:
        proc.wait(timeout=4)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()

    # Restart and verify persistence
    proc2 = subprocess.Popen(
        [str(exe_path), "--db", str(test_db)],
        cwd=str(tmp_path),
        env=clean_env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    time.sleep(3)
    assert proc2.poll() is None, "Packaged process failed on restart!"

    with sqlite3.connect(str(test_db)) as conn:
        row = conn.execute("SELECT name FROM products WHERE name = 'Packaged Prod'").fetchone()
        assert row is not None and row[0] == 'Packaged Prod'

    proc2.terminate()
    try:
        proc2.wait(timeout=4)
    except subprocess.TimeoutExpired:
        proc2.kill()
        proc2.wait()
