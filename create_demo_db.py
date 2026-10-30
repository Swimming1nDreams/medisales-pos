import os
import sys
import json
from pathlib import Path
from datetime import datetime, date, timedelta

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
from src.ui_web.bridge import FrontendBridge

def setup_demo_db(db_path="demo_medisales.db"):
    db_file = Path(db_path)
    if db_file.exists():
        db_file.unlink()

    db_manager = DatabaseManager(str(db_file))
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
    bridge = FrontendBridge(services)

    print("Populating Demo Database...")

    # 1. Categories
    cats = [
        "Antibiotics & Prescription",
        "Analgesics & Pain Relief",
        "Cardiovascular Care",
        "Gastrointestinal",
        "Vitamins & Wellness",
        "Personal Care & Hygiene",
        "Baby & Mother Care"
    ]
    cat_ids = {}
    for c in cats:
        res = json.loads(bridge.create_category(c))
        cat_ids[c] = res['data']['category_id']

    # 2. Suppliers
    suppliers_data = [
        ("Apex Myanmar Pharmaceutical Distribution", "09-795123456", "No. 45 Bayintnaung Rd, Mayangone, Yangon"),
        ("Mega Lifesciences Wholesale Myanmar", "09-421987654", "No. 12 78th Street, Chanayethazan, Mandalay"),
        ("City Health Medical Supplies Ltd", "09-250112233", "Thapyaygone Commercial Area, Naypyitaw"),
        ("Golden Lotus Healthcare & Consumer Goods", "09-965443322", "Industrial Zone 1, Hlaing Tharyar, Yangon")
    ]
    supp_ids = {}
    for s_name, s_phone, s_addr in suppliers_data:
        res = json.loads(bridge.create_supplier(s_name, s_phone, s_addr))
        supp_ids[s_name] = res['data']['supplier_id']

    # 3. Products
    products_data = [
        # (Name, Category, Unit, SellingPrice, MinStock, IsMed)
        ("Amoxicillin & Clavulanate Potassium 625mg (Augmentin)", "Antibiotics & Prescription", "strip", 12500, 10, True),
        ("Paracetamol 500mg Tablets (Biogesic Blister Pack)", "Analgesics & Pain Relief", "strip", 1500, 30, True),
        ("Omeprazole 20mg Capsules (Gasec-20 Acid Reducer)", "Gastrointestinal", "strip", 3800, 15, True),
        ("Amlodipine Besylate 5mg Tablets (Norvasc)", "Cardiovascular Care", "strip", 4500, 10, True),
        ("Cefixime 200mg Capsules (Cefspan Broad-Spectrum)", "Antibiotics & Prescription", "strip", 18500, 8, True),
        ("Metformin Hydrochloride 500mg (Glucophage)", "Cardiovascular Care", "strip", 2800, 25, True),
        ("Multivitamin with Zinc Softgels (Enervon-C Daily)", "Vitamins & Wellness", "bottle", 8500, 12, True),
        ("Cetirizine Hydrochloride 10mg Tablets (Zyrtec)", "Analgesics & Pain Relief", "strip", 2400, 15, True),
        ("Antiseptic Disinfectant Liquid 500ml (Dettol Original)", "Personal Care & Hygiene", "bottle", 6800, 8, False),
        ("Baby Soft Care Diapers Large Size (Pack of 48)", "Baby & Mother Care", "pack", 24500, 6, False),
        ("Head & Shoulders Anti-Dandruff Shampoo 350ml", "Personal Care & Hygiene", "bottle", 7800, 5, False),
        ("Sensodyne Daily Care Fluoride Toothpaste 160g", "Personal Care & Hygiene", "tube", 4500, 10, False)
    ]

    prod_ids = {}
    for name, cat_name, unit, price, min_stock, is_med in products_data:
        res = json.loads(bridge.create_product(name, cat_ids[cat_name], unit, price, min_stock, is_med))
        prod_ids[name] = res['data']['product_id']

    # 4. Purchases with Medicine Batches (FEFO testing)
    today = date.today()
    
    # Purchase 1 - Apex Myanmar
    p1_items = [
        {
            "product_id": prod_ids["Amoxicillin & Clavulanate Potassium 625mg (Augmentin)"],
            "quantity": 25,
            "unit_cost": 8500,
            "batch_number": "AUG-2026-X1",
            "expiry_date": (today + timedelta(days=240)).isoformat()
        },
        {
            "product_id": prod_ids["Amoxicillin & Clavulanate Potassium 625mg (Augmentin)"],
            "quantity": 15,
            "unit_cost": 8200,
            "batch_number": "AUG-2026-E0",
            "expiry_date": (today + timedelta(days=45)).isoformat() # Expiring soon
        },
        {
            "product_id": prod_ids["Paracetamol 500mg Tablets (Biogesic Blister Pack)"],
            "quantity": 80,
            "unit_cost": 950,
            "batch_number": "BIO-B88",
            "expiry_date": (today + timedelta(days=365)).isoformat()
        },
        {
            "product_id": prod_ids["Cefixime 200mg Capsules (Cefspan Broad-Spectrum)"],
            "quantity": 20,
            "unit_cost": 13500,
            "batch_number": "CEF-9921",
            "expiry_date": (today + timedelta(days=180)).isoformat()
        }
    ]
    p1_date = (today - timedelta(days=12)).isoformat()
    bridge.create_purchase("PO-2026-0081", supp_ids["Apex Myanmar Pharmaceutical Distribution"], p1_date, json.dumps(p1_items))

    # Purchase 2 - Mega Lifesciences
    p2_items = [
        {
            "product_id": prod_ids["Omeprazole 20mg Capsules (Gasec-20 Acid Reducer)"],
            "quantity": 40,
            "unit_cost": 2400,
            "batch_number": "GAS-301",
            "expiry_date": (today + timedelta(days=300)).isoformat()
        },
        {
            "product_id": prod_ids["Amlodipine Besylate 5mg Tablets (Norvasc)"],
            "quantity": 30,
            "unit_cost": 2900,
            "batch_number": "NOR-554",
            "expiry_date": (today + timedelta(days=400)).isoformat()
        },
        {
            "product_id": prod_ids["Metformin Hydrochloride 500mg (Glucophage)"],
            "quantity": 50,
            "unit_cost": 1750,
            "batch_number": "GLU-808",
            "expiry_date": (today + timedelta(days=500)).isoformat()
        },
        {
            "product_id": prod_ids["Multivitamin with Zinc Softgels (Enervon-C Daily)"],
            "quantity": 35,
            "unit_cost": 5800,
            "batch_number": "ENV-771",
            "expiry_date": (today + timedelta(days=280)).isoformat()
        },
        {
            "product_id": prod_ids["Cetirizine Hydrochloride 10mg Tablets (Zyrtec)"],
            "quantity": 40,
            "unit_cost": 1500,
            "batch_number": "ZYR-404",
            "expiry_date": (today + timedelta(days=320)).isoformat()
        }
    ]
    p2_date = (today - timedelta(days=8)).isoformat()
    bridge.create_purchase("PO-2026-0094", supp_ids["Mega Lifesciences Wholesale Myanmar"], p2_date, json.dumps(p2_items))

    # Purchase 3 - Golden Lotus (General Goods)
    p3_items = [
        {
            "product_id": prod_ids["Antiseptic Disinfectant Liquid 500ml (Dettol Original)"],
            "quantity": 24,
            "unit_cost": 4800,
            "batch_number": None,
            "expiry_date": None
        },
        {
            "product_id": prod_ids["Baby Soft Care Diapers Large Size (Pack of 48)"],
            "quantity": 18,
            "unit_cost": 18000,
            "batch_number": None,
            "expiry_date": None
        },
        {
            "product_id": prod_ids["Head & Shoulders Anti-Dandruff Shampoo 350ml"],
            "quantity": 20,
            "unit_cost": 5400,
            "batch_number": None,
            "expiry_date": None
        },
        {
            "product_id": prod_ids["Sensodyne Daily Care Fluoride Toothpaste 160g"],
            "quantity": 30,
            "unit_cost": 3100,
            "batch_number": None,
            "expiry_date": None
        }
    ]
    p3_date = (today - timedelta(days=4)).isoformat()
    bridge.create_purchase("PO-2026-0105", supp_ids["Golden Lotus Healthcare & Consumer Goods"], p3_date, json.dumps(p3_items))

    # Settle partial payment to Apex
    allocations_1 = [{"purchase_id": 1, "allocated_amount": 300000}]
    bridge.record_payment("PV-2026-001", supp_ids["Apex Myanmar Pharmaceutical Distribution"], today.isoformat(), 300000, json.dumps(allocations_1), "Partial invoice payment bank transfer")

    # Full settlement to Mega Lifesciences
    mega_purchases = json.loads(bridge.get_outstanding_purchases(supp_ids["Mega Lifesciences Wholesale Myanmar"]))['data']
    if mega_purchases:
        mega_p_id = mega_purchases[0]['id']
        mega_owed = mega_purchases[0]['total_amount'] - mega_purchases[0]['amount_paid']
        allocations_2 = [{"purchase_id": mega_p_id, "allocated_amount": mega_owed}]
        bridge.record_payment("PV-2026-002", supp_ids["Mega Lifesciences Wholesale Myanmar"], today.isoformat(), mega_owed, json.dumps(allocations_2), "Full settlement cheque")

    # 5. Sales Transactions
    # Sale 1
    s1_items = [
        {"product_id": prod_ids["Amoxicillin & Clavulanate Potassium 625mg (Augmentin)"], "quantity": 2, "unit_price": 12500},
        {"product_id": prod_ids["Paracetamol 500mg Tablets (Biogesic Blister Pack)"], "quantity": 4, "unit_price": 1500}
    ]
    # Total: 25000 + 6000 = 31,000 Ks
    bridge.create_sale("INV-2026-0001", json.dumps(s1_items), 35000)

    # Sale 2
    s2_items = [
        {"product_id": prod_ids["Baby Soft Care Diapers Large Size (Pack of 48)"], "quantity": 1, "unit_price": 24500},
        {"product_id": prod_ids["Antiseptic Disinfectant Liquid 500ml (Dettol Original)"], "quantity": 1, "unit_price": 6800},
        {"product_id": prod_ids["Sensodyne Daily Care Fluoride Toothpaste 160g"], "quantity": 2, "unit_price": 4500}
    ]
    # Total: 24500 + 6800 + 9000 = 40,300 Ks
    bridge.create_sale("INV-2026-0002", json.dumps(s2_items), 50000)

    # Sale 3
    s3_items = [
        {"product_id": prod_ids["Multivitamin with Zinc Softgels (Enervon-C Daily)"], "quantity": 2, "unit_price": 8500},
        {"product_id": prod_ids["Omeprazole 20mg Capsules (Gasec-20 Acid Reducer)"], "quantity": 3, "unit_price": 3800}
    ]
    # Total: 17000 + 11400 = 28,400 Ks
    bridge.create_sale("INV-2026-0003", json.dumps(s3_items), 30000)

    # 6. Expenses
    bridge.record_expense(today.isoformat(), "Utilities", 185000, "Shop Electricity & Backup Generator Diesel Fuel")
    bridge.record_expense(today.isoformat(), "Salaries", 350000, "Licensed Pharmacist Monthly Shift Advance")
    bridge.record_expense(today.isoformat(), "Store Supplies", 35000, "Customer Medicine Envelopes & POS 80mm Paper Rolls")

    db_manager.close()
    print("Demo database populated successfully at:", db_path)

if __name__ == "__main__":
    setup_demo_db()
