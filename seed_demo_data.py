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
from src.services.customer_service import CustomerService
from src.services.finance_service import FinanceService
from src.services.dashboard_service import DashboardService
from src.services.report_service import ReportService
from src.services.reconciliation_service import ReconciliationService
from src.ui_web.bridge import FrontendBridge


def seed_database(db_path: str):
    print(f"\n=======================================================")
    print(f"[*] Seeding Database at: {db_path}")
    print(f"=======================================================")

    p = Path(db_path)
    p.parent.mkdir(parents=True, exist_ok=True)

    # 1. Start with a clean database file
    print("-> Resetting database file cleanly...")
    for ext in ["", "-wal", "-shm"]:
        f = Path(str(p) + ext)
        if f.exists():
            try:
                f.unlink()
            except Exception as e:
                print(f"Warning unlinking {f}: {e}")

    db_manager = DatabaseManager(str(p))

    # 2. Apply migrations to ensure all tables, triggers, and indices exist (001 -> 005)
    print("-> Applying database migrations...")
    migrations_mgr = MigrationsManager(db_manager)
    migrations_mgr.apply_migrations()

    # 3. Instantiate services and bridge
    inv = InventoryService(db_manager)
    prod = ProductService(db_manager)
    sales = SalesService(db_manager, inv)
    supp = SupplierService(db_manager)
    purch = PurchaseService(db_manager)
    exp = ExpenseService(db_manager)
    cust = CustomerService(db_manager)
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
        'customer_service': cust,
        'finance_service': fin,
        'dashboard_service': dash,
        'report_service': rep,
        'reconciliation_service': recon
    }
    bridge = FrontendBridge(services)

    # 4. Categories (Localized Myanmar Pharmacy Categories)
    print("-> Creating localized categories...")
    categories = [
        "ဆေးဝါးများ (အကိုက်အခဲပျောက်နှင့် ဖျားနာ)",
        "ပဋိဇီဝဆေးများနှင့် ဆရာဝန်ညွှန်ဆေးများ",
        "အစာအိမ်နှင့် အူလမ်းကြောင်းဆေးများ",
        "သွေးတိုး၊ ဆီးချိုနှင့် နှလုံးရောဂါဆေးများ",
        "ဗီတာမင်နှင့် အားဆေးများ",
        "တစ်ကိုယ်ရေသန့်ရှင်းရေးနှင့် လူသုံးကုန်",
        "မိခင်နှင့် ကလေးအသုံးအဆောင်"
    ]
    cat_ids = {}
    for c in categories:
        res = json.loads(bridge.create_category(c))
        cat_ids[c] = res['data']['category_id']

    # 5. Suppliers (Realistic Myanmar Distributors)
    print("-> Creating localized suppliers...")
    suppliers_data = [
        ("ရွှေဆေးဝါး ကုန်သည်ကြီးများ (ရန်ကုန်)", "09-795123456", "အမှတ် (၄၅)၊ ဘုရင့်နောင်လမ်း၊ မရမ်းကုန်းမြို့နယ်၊ ရန်ကုန်"),
        ("Mega Lifesciences Wholesale Myanmar", "09-421987654", "အမှတ် (၁၂)၊ ၇၈ လမ်း၊ ချမ်းအေးသာစံမြို့နယ်၊ မန္တလေး"),
        ("အောင်မင်္ဂလာ ဆေးဝါးနှင့် ကျန်းမာရေးဖြန့်ချိရေး", "09-250112233", "သပြေကုန်း ကုန်သွယ်မှုဇုန်၊ နေပြည်တော်"),
        ("ရွှေကြာဖြူ လူသုံးကုန်နှင့် ဆေးဝါး လက်ကားရောင်းဝယ်ရေး", "09-965443322", "စက်မှုဇုန် (၁)၊ လှိုင်သာယာမြို့နယ်၊ ရန်ကုန်")
    ]
    supp_ids = {}
    for s_name, s_phone, s_addr in suppliers_data:
        res = json.loads(bridge.create_supplier(s_name, s_phone, s_addr))
        supp_ids[s_name] = res['data']['supplier_id']

    # 6. Customers (Neighborhood Credit Customers)
    print("-> Creating neighborhood credit customers...")
    customers_data = [
        ("ဦးသန်းနိုင်", "09-450011223", "လမ်း ၅၀၊ အမှတ် (၄)၊ ပုဇွန်တောင်", "မနက်ပိုင်း ပုံမှန်ဝယ်ယူသူ (အကြွေးစာရင်းဖွင့်ထားသူ)"),
        ("ဒေါ်လှလှ", "09-790112233", "အမှတ် (၁၈)၊ မေတ္တာလမ်း၊ တောင်ဥက္ကလာ", "မိသားစုသုံး ဆေးဝါးများ အကြွေးဝယ်ယူသူ"),
        ("ကိုအောင်ကျော်", "09-254009988", "အမှတ် (၅)၊ ဈေးနား၊ သင်္ဃန်းကျွန်း", "လမ်းထိပ် ကုန်စုံဆိုင်ပိုင်ရှင် (အကြွေးကျေပြီး)"),
        ("ဒေါ်သန်းသန်းစိုး", "09-420088776", "အမှတ် (၃၂)၊ ဆေးရုံလမ်း၊ ရန်ကင်း", "သွေးတိုး၊ ဆီးချို ပုံမှန်ဖောက်သည်")
    ]
    cust_ids = {}
    for c_name, c_phone, c_addr, c_notes in customers_data:
        res = json.loads(bridge.create_customer(c_name, c_phone, c_addr, c_notes))
        cust_ids[c_name] = res['data']['customer_id']

    # 7. Products with Multi-Unit Packaging (အလုံး/ကတ်/ဗူး/ဖာ)
    print("-> Creating products with multi-unit packaging...")
    products_def = [
        # 1. Biogesic
        {
            "name": "ပါရာစီတမော ၅၀၀ မီလီဂရမ် (Biogesic)",
            "cat": "ဆေးဝါးများ (အကိုက်အခဲပျောက်နှင့် ဖျားနာ)",
            "unit": "အလုံး",
            "price": 150,
            "min_stock": 50,
            "is_med": True,
            "packagings": [
                {"unit_name": "ကတ်", "conversion_factor": 10, "selling_price": 1400, "barcode": "885012300001"},
                {"unit_name": "ဗူး", "conversion_factor": 100, "selling_price": 13500, "barcode": "885012300002"}
            ]
        },
        # 2. Amoxicillin
        {
            "name": "အမောက်ဆီဆီလင် ၅၀၀ မီလီဂရမ် (Amoxicillin 500mg)",
            "cat": "ပဋိဇီဝဆေးများနှင့် ဆရာဝန်ညွှန်ဆေးများ",
            "unit": "အလုံး",
            "price": 350,
            "min_stock": 30,
            "is_med": True,
            "packagings": [
                {"unit_name": "ကတ်", "conversion_factor": 10, "selling_price": 3400, "barcode": "885012300003"},
                {"unit_name": "ဗူး", "conversion_factor": 100, "selling_price": 33000, "barcode": "885012300004"}
            ]
        },
        # 3. Omeprazole
        {
            "name": "အိုမီပရာဇော ၂၀ မီလီဂရမ် (Omeprazole 20mg - Gasec)",
            "cat": "အစာအိမ်နှင့် အူလမ်းကြောင်းဆေးများ",
            "unit": "အလုံး",
            "price": 400,
            "min_stock": 20,
            "is_med": True,
            "packagings": [
                {"unit_name": "ကတ်", "conversion_factor": 14, "selling_price": 5400, "barcode": "885012300005"}
            ]
        },
        # 4. Amlodipine
        {
            "name": "အမ်လိုဒီပင်း ၅ မီလီဂရမ် (Amlodipine 5mg - Norvasc)",
            "cat": "သွေးတိုး၊ ဆီးချိုနှင့် နှလုံးရောဂါဆေးများ",
            "unit": "အလုံး",
            "price": 450,
            "min_stock": 30,
            "is_med": True,
            "packagings": [
                {"unit_name": "ကတ်", "conversion_factor": 10, "selling_price": 4300, "barcode": "885012300007"}
            ]
        },
        # 5. Metformin
        {
            "name": "မက်ဖော်မင် ၅၀၀ မီလီဂရမ် (Metformin 500mg - Glucophage)",
            "cat": "သွေးတိုး၊ ဆီးချိုနှင့် နှလုံးရောဂါဆေးများ",
            "unit": "အလုံး",
            "price": 300,
            "min_stock": 40,
            "is_med": True,
            "packagings": [
                {"unit_name": "ကတ်", "conversion_factor": 10, "selling_price": 2800, "barcode": "885012300009"}
            ]
        },
        # 6. Enervon-C
        {
            "name": "အန်နာဗွန်စီ နေ့စဉ်အားဆေး (Enervon-C Daily Multivitamins)",
            "cat": "ဗီတာမင်နှင့် အားဆေးများ",
            "unit": "အလုံး",
            "price": 300,
            "min_stock": 20,
            "is_med": True,
            "packagings": [
                {"unit_name": "ဗူး", "conversion_factor": 30, "selling_price": 8500, "barcode": "885012300011"}
            ]
        },
        # 7. Cetirizine
        {
            "name": "စက်ထရီဇင်း ၁၀ မီလီဂရမ် (Cetirizine 10mg - Zyrtec)",
            "cat": "ဆေးဝါးများ (အကိုက်အခဲပျောက်နှင့် ဖျားနာ)",
            "unit": "အလုံး",
            "price": 250,
            "min_stock": 20,
            "is_med": True,
            "packagings": [
                {"unit_name": "ကတ်", "conversion_factor": 10, "selling_price": 2400, "barcode": "885012300012"}
            ]
        },
        # 8. Cefixime
        {
            "name": "ဆီဖစ်ဇင်း ၂၀၀ မီလီဂရမ် (Cefixime 200mg - Cefspan)",
            "cat": "ပဋိဇီဝဆေးများနှင့် ဆရာဝန်ညွှန်ဆေးများ",
            "unit": "အလုံး",
            "price": 1900,
            "min_stock": 30, # Min stock 30, but initial purchase will be 15 units -> triggers Low Stock Alert!
            "is_med": True,
            "packagings": [
                {"unit_name": "ကတ်", "conversion_factor": 10, "selling_price": 18500, "barcode": "885012300013"}
            ]
        },
        # 9. Dettol (General Goods)
        {
            "name": "ဒက်တော ပိုးသတ်ဆေးရည် ၅၀၀ မီလီလီတာ (Dettol Antiseptic 500ml)",
            "cat": "တစ်ကိုယ်ရေသန့်ရှင်းရေးနှင့် လူသုံးကုန်",
            "unit": "ဗူး",
            "price": 6800,
            "min_stock": 10,
            "is_med": False,
            "packagings": [
                {"unit_name": "ဖာ", "conversion_factor": 12, "selling_price": 78000, "barcode": "885012300014"}
            ]
        },
        # 10. Sensodyne Toothpaste
        {
            "name": "ဆင်ဆိုဒိုင်း သွားတိုက်ဆေး ၁၆၀ ဂရမ် (Sensodyne Toothpaste 160g)",
            "cat": "တစ်ကိုယ်ရေသန့်ရှင်းရေးနှင့် လူသုံးကုန်",
            "unit": "ဗူး",
            "price": 4500,
            "min_stock": 15,
            "is_med": False,
            "packagings": [
                {"unit_name": "ဖာ", "conversion_factor": 12, "selling_price": 52000, "barcode": "885012300015"}
            ]
        },
        # 11. Head & Shoulders Shampoo
        {
            "name": "ဟတ်အန်ရှိုးဒါး ဗောက်ပျောက်ခေါင်းလျှော်ရည် ၃၅၀ မီလီလီတာ (Head & Shoulders 350ml)",
            "cat": "တစ်ကိုယ်ရေသန့်ရှင်းရေးနှင့် လူသုံးကုန်",
            "unit": "ဗူး",
            "price": 7800,
            "min_stock": 8,
            "is_med": False,
            "packagings": [
                {"unit_name": "ဖာ", "conversion_factor": 12, "selling_price": 90000, "barcode": "885012300016"}
            ]
        },
        # 12. Baby Diapers
        {
            "name": "ကလေးဒိုင်ပါ အကြီးဆိုဒ် (Baby Diapers Large Size 48s)",
            "cat": "မိခင်နှင့် ကလေးအသုံးအဆောင်",
            "unit": "ထုပ်",
            "price": 24500,
            "min_stock": 5,
            "is_med": False,
            "packagings": [
                {"unit_name": "ဖာ", "conversion_factor": 4, "selling_price": 96000, "barcode": "885012300017"}
            ]
        }
    ]

    prod_ids = {}
    for p_def in products_def:
        res = json.loads(bridge.create_product(
            p_def["name"],
            cat_ids[p_def["cat"]],
            p_def["unit"],
            p_def["price"],
            p_def["min_stock"],
            p_def["is_med"],
            json.dumps(p_def["packagings"])
        ))
        prod_ids[p_def["name"]] = res['data']['product_id']

    # 8. Purchases with FEFO Batches (Including Expiring Soon Alerts)
    print("-> Recording stock purchases with FEFO batches...")
    today = date.today()

    # Purchase 1 - ရွှေဆေးဝါး ကုန်သည်ကြီးများ
    p1_items = [
        {
            "product_id": prod_ids["ပါရာစီတမော ၅၀၀ မီလီဂရမ် (Biogesic)"],
            "quantity": 1000,
            "unit_cost": 95,
            "batch_number": "BIO-2026-A1",
            "expiry_date": (today + timedelta(days=365)).isoformat()
        },
        {
            "product_id": prod_ids["ပါရာစီတမော ၅၀၀ မီလီဂရမ် (Biogesic)"],
            "quantity": 200,
            "unit_cost": 90,
            "batch_number": "BIO-2026-EXP",
            "expiry_date": (today + timedelta(days=20)).isoformat() # Expiring soon alert (within 20 days!)
        },
        {
            "product_id": prod_ids["အမောက်ဆီဆီလင် ၅၀၀ မီလီဂရမ် (Amoxicillin 500mg)"],
            "quantity": 500,
            "unit_cost": 220,
            "batch_number": "AMX-2026-B1",
            "expiry_date": (today + timedelta(days=500)).isoformat()
        },
        {
            "product_id": prod_ids["ဆီဖစ်ဇင်း ၂၀၀ မီလီဂရမ် (Cefixime 200mg - Cefspan)"],
            "quantity": 15, # 15 units <= 30 min stock -> triggers Low Stock Alert!
            "unit_cost": 1350,
            "batch_number": "CEF-2026-C1",
            "expiry_date": (today + timedelta(days=240)).isoformat()
        }
    ]
    p1_date = (today - timedelta(days=10)).isoformat()
    p1_res = json.loads(bridge.create_purchase("PO-2026-001", supp_ids["ရွှေဆေးဝါး ကုန်သည်ကြီးများ (ရန်ကုန်)"], p1_date, json.dumps(p1_items)))
    if p1_res.get('status') != 'success':
        raise RuntimeError(f"create_purchase P1 failed: {p1_res}")
    p1_id = p1_res['data']['purchase_id']

    # Purchase 2 - Mega Lifesciences Wholesale Myanmar
    p2_items = [
        {
            "product_id": prod_ids["အိုမီပရာဇော ၂၀ မီလီဂရမ် (Omeprazole 20mg - Gasec)"],
            "quantity": 400,
            "unit_cost": 260,
            "batch_number": "OME-2026-D1",
            "expiry_date": (today + timedelta(days=300)).isoformat()
        },
        {
            "product_id": prod_ids["အမ်လိုဒီပင်း ၅ မီလီဂရမ် (Amlodipine 5mg - Norvasc)"],
            "quantity": 300,
            "unit_cost": 300,
            "batch_number": "AML-2026-E1",
            "expiry_date": (today + timedelta(days=400)).isoformat()
        },
        {
            "product_id": prod_ids["မက်ဖော်မင် ၅၀၀ မီလီဂရမ် (Metformin 500mg - Glucophage)"],
            "quantity": 500,
            "unit_cost": 190,
            "batch_number": "MET-2026-F1",
            "expiry_date": (today + timedelta(days=500)).isoformat()
        },
        {
            "product_id": prod_ids["အန်နာဗွန်စီ နေ့စဉ်အားဆေး (Enervon-C Daily Multivitamins)"],
            "quantity": 300,
            "unit_cost": 200,
            "batch_number": "ENV-2026-G1",
            "expiry_date": (today + timedelta(days=55)).isoformat() # Expiring soon alert (within 55 days!)
        },
        {
            "product_id": prod_ids["စက်ထရီဇင်း ၁၀ မီလီဂရမ် (Cetirizine 10mg - Zyrtec)"],
            "quantity": 300,
            "unit_cost": 150,
            "batch_number": "CET-2026-H1",
            "expiry_date": (today + timedelta(days=320)).isoformat()
        }
    ]
    p2_date = (today - timedelta(days=7)).isoformat()
    p2_res = json.loads(bridge.create_purchase("PO-2026-002", supp_ids["Mega Lifesciences Wholesale Myanmar"], p2_date, json.dumps(p2_items)))
    p2_id = p2_res['data']['purchase_id']

    # Purchase 3 - ရွှေကြာဖြူ လူသုံးကုန်နှင့် ဆေးဝါး လက်ကားရောင်းဝယ်ရေး (General Goods)
    p3_items = [
        {
            "product_id": prod_ids["ဒက်တော ပိုးသတ်ဆေးရည် ၅၀၀ မီလီလီတာ (Dettol Antiseptic 500ml)"],
            "quantity": 36,
            "unit_cost": 5000,
            "batch_number": None,
            "expiry_date": None
        },
        {
            "product_id": prod_ids["ဆင်ဆိုဒိုင်း သွားတိုက်ဆေး ၁၆၀ ဂရမ် (Sensodyne Toothpaste 160g)"],
            "quantity": 48,
            "unit_cost": 3200,
            "batch_number": None,
            "expiry_date": None
        },
        {
            "product_id": prod_ids["ဟတ်အန်ရှိုးဒါး ဗောက်ပျောက်ခေါင်းလျှော်ရည် ၃၅၀ မီလီလီတာ (Head & Shoulders 350ml)"],
            "quantity": 24,
            "unit_cost": 5500,
            "batch_number": None,
            "expiry_date": None
        },
        {
            "product_id": prod_ids["ကလေးဒိုင်ပါ အကြီးဆိုဒ် (Baby Diapers Large Size 48s)"],
            "quantity": 20,
            "unit_cost": 18500,
            "batch_number": None,
            "expiry_date": None
        }
    ]
    p3_date = (today - timedelta(days=4)).isoformat()
    p3_res = json.loads(bridge.create_purchase("PO-2026-003", supp_ids["ရွှေကြာဖြူ လူသုံးကုန်နှင့် ဆေးဝါး လက်ကားရောင်းဝယ်ရေး"], p3_date, json.dumps(p3_items)))
    p3_id = p3_res['data']['purchase_id']

    # 9. Supplier Payments (Showing Accounts Payable & Partial Settlements)
    print("-> Recording supplier payments...")
    # Partial payment of 350,000 Ks to ရွှေဆေးဝါး ကုန်သည်ကြီးများ (remaining debt shows on dashboard)
    alloc_1 = [{"purchase_id": p1_id, "allocated_amount": 350000}]
    bridge.record_payment("PV-2026-001", supp_ids["ရွှေဆေးဝါး ကုန်သည်ကြီးများ (ရန်ကုန်)"], (today - timedelta(days=5)).isoformat(), 350000, json.dumps(alloc_1), "ဘဏ်လွှဲငွေဖြင့် တစိတ်တပိုင်း ပေးချေခြင်း")

    # Full payment to Mega Lifesciences Wholesale Myanmar
    mega_purchases = json.loads(bridge.get_outstanding_purchases(supp_ids["Mega Lifesciences Wholesale Myanmar"]))['data']
    if mega_purchases:
        mega_p_id = mega_purchases[0]['id']
        mega_owed = mega_purchases[0]['total_amount'] - mega_purchases[0]['amount_paid']
        alloc_2 = [{"purchase_id": mega_p_id, "allocated_amount": mega_owed}]
        bridge.record_payment("PV-2026-002", supp_ids["Mega Lifesciences Wholesale Myanmar"], (today - timedelta(days=3)).isoformat(), mega_owed, json.dumps(alloc_2), "ချက်လက်မှတ်ဖြင့် အကြွေးအကျေ ပေးချေခြင်း")

    # 10. Completed Sales Transactions (Cash, Credit Ledger, Multi-Units, and Discounts)
    print("-> Recording sales transactions (Cash, Credit Ledger, Multi-Unit)...")
    now_dt = datetime.now()

    # Sale 1 (Today): Walk-in Cash Customer
    # - 20 Biogesic pills (2 strips equivalent) @ 150 Ks = 3,000 Ks
    # - 1 Dettol 500ml @ 6,800 Ks
    s1_items = [
        {"product_id": prod_ids["ပါရာစီတမော ၅၀၀ မီလီဂရမ် (Biogesic)"], "quantity": 20, "unit_price": 150},
        {"product_id": prod_ids["ဒက်တော ပိုးသတ်ဆေးရည် ၅၀၀ မီလီလီတာ (Dettol Antiseptic 500ml)"], "quantity": 1, "unit_price": 6800}
    ]
    # Total = 9,800 Ks. Paid = 10,000 Ks, Change = 200 Ks.
    bridge.create_sale(
        "INV-2026-0001",
        json.dumps(s1_items),
        10000,
        discount_amount=0,
        payment_type="cash",
        customer_id="",
        date_time=now_dt.strftime("%Y-%m-%d 09:30:00")
    )

    # Sale 2 (Today): Neighborhood Credit Sale to ဦးသန်းနိုင်
    # - 1 Baby Diapers @ 24,500 Ks
    # - 2 Sensodyne Toothpastes @ 4,500 Ks = 9,000 Ks
    # Subtotal = 33,500 Ks, Discount = 500 Ks -> Total = 33,000 Ks
    # Cash Paid upfront = 18,000 Ks, Credit Debt = 15,000 Ks
    s2_items = [
        {"product_id": prod_ids["ကလေးဒိုင်ပါ အကြီးဆိုဒ် (Baby Diapers Large Size 48s)"], "quantity": 1, "unit_price": 24500},
        {"product_id": prod_ids["ဆင်ဆိုဒိုင်း သွားတိုက်ဆေး ၁၆၀ ဂရမ် (Sensodyne Toothpaste 160g)"], "quantity": 2, "unit_price": 4500}
    ]
    bridge.create_sale(
        "INV-2026-0002",
        json.dumps(s2_items),
        18000,
        discount_amount=500,
        payment_type="credit",
        customer_id=str(cust_ids["ဦးသန်းနိုင်"]),
        date_time=now_dt.strftime("%Y-%m-%d 11:15:00")
    )

    # Sale 3 (Yesterday): Neighborhood Credit Sale to ဒေါ်လှလှ
    # - 14 Omeprazole pills (1 strip) @ 400 Ks = 5,600 Ks
    # - 10 Amlodipine pills (1 strip) @ 450 Ks = 4,500 Ks
    # Subtotal = 10,100 Ks, Discount = 600 Ks -> Total = 9,500 Ks
    # Cash Paid upfront = 1,000 Ks, Credit Debt = 8,500 Ks
    s3_items = [
        {"product_id": prod_ids["အိုမီပရာဇော ၂၀ မီလီဂရမ် (Omeprazole 20mg - Gasec)"], "quantity": 14, "unit_price": 400},
        {"product_id": prod_ids["အမ်လိုဒီပင်း ၅ မီလီဂရမ် (Amlodipine 5mg - Norvasc)"], "quantity": 10, "unit_price": 450}
    ]
    bridge.create_sale(
        "INV-2026-0003",
        json.dumps(s3_items),
        1000,
        discount_amount=600,
        payment_type="credit",
        customer_id=str(cust_ids["ဒေါ်လှလှ"]),
        date_time=(now_dt - timedelta(days=1)).strftime("%Y-%m-%d 14:20:00")
    )

    # Sale 4 (2 days ago): Customer ကိုအောင်ကျော် (Credit sale, then settled in full)
    # - 30 Enervon-C pills (1 bottle) @ 300 Ks = 9,000 Ks
    s4_items = [
        {"product_id": prod_ids["အန်နာဗွန်စီ နေ့စဉ်အားဆေး (Enervon-C Daily Multivitamins)"], "quantity": 30, "unit_price": 300}
    ]
    bridge.create_sale(
        "INV-2026-0004",
        json.dumps(s4_items),
        0,
        discount_amount=0,
        payment_type="credit",
        customer_id=str(cust_ids["ကိုအောင်ကျော်"]),
        date_time=(now_dt - timedelta(days=2)).strftime("%Y-%m-%d 10:05:00")
    )
    # Ko Aung Kyaw pays back his debt in full yesterday:
    bridge.record_customer_payment(
        cust_ids["ကိုအောင်ကျော်"],
        9000,
        "အကြွေးငွေ အပြေအကျေ လာရောက်ပေးသွင်းခြင်း"
    )

    # Sale 5 (Today): Walk-in Cash Sale
    # - 10 Amoxicillin pills (1 strip) @ 350 Ks = 3,500 Ks
    # - 10 Cetirizine pills (1 strip) @ 250 Ks = 2,500 Ks
    # Total = 6,000 Ks. Paid = 10,000 Ks, Change = 4,000 Ks.
    s5_items = [
        {"product_id": prod_ids["အမောက်ဆီဆီလင် ၅၀၀ မီလီဂရမ် (Amoxicillin 500mg)"], "quantity": 10, "unit_price": 350},
        {"product_id": prod_ids["စက်ထရီဇင်း ၁၀ မီလီဂရမ် (Cetirizine 10mg - Zyrtec)"], "quantity": 10, "unit_price": 250}
    ]
    bridge.create_sale(
        "INV-2026-0005",
        json.dumps(s5_items),
        10000,
        discount_amount=0,
        payment_type="cash",
        customer_id="",
        date_time=now_dt.strftime("%Y-%m-%d 15:45:00")
    )

    # 11. Shop Running Expenses (Overheads)
    print("-> Recording shop operating expenses...")
    exp_date = today.isoformat()
    bridge.record_expense(exp_date, "ဆိုင်မီးဖိုးနှင့် မီးစက်ဒီဇယ်ဆီဖိုး", 120000, "လစဉ် လျှပ်စစ်မီတာခနှင့် မီးစက်မောင်းနှင်ရန် ဒီဇယ်ဆီဖိုး")
    bridge.record_expense(exp_date, "ဆိုင်ခန်းလခ", 250000, "ယခုလအတွက် ဆိုင်ခန်းငှားရမ်းခ")
    bridge.record_expense(exp_date, "အရောင်းစာရေး လစာစပေါ်ငွေ", 150000, "ဆိုင်ဝန်ထမ်း လစာကြိုထုတ်ငွေ")
    bridge.record_expense(exp_date, "ဆိုင်သုံးပစ္စည်းများ", 25000, "ဆေးထည့်စက္ကူအိတ်နှင့် POS ပြေစာစက္ကူလိပ်များ ဝယ်ယူခြင်း")

    db_manager.close()
    print(f"[+] Successfully seeded: {db_path}\n")


def main():
    # 1. Dev DB (Repo Root)
    dev_db = Path(r"C:\Users\Lenovo\Downloads\Medisales\medisales.db")
    seed_database(str(dev_db))

    # 2. Local AppData DB (Used by Packaged EXE SayMahar.exe)
    appdata_dir = os.environ.get("LOCALAPPDATA", r"C:\Users\Lenovo\AppData\Local")
    appdata_db = Path(appdata_dir) / "Medisales" / "medisales.db"
    seed_database(str(appdata_db))

    print("ALL DATABASES SEEDED SUCCESSFULLY!")


if __name__ == "__main__":
    main()
