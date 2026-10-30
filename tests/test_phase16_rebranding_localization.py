import re
import json
import pytest
from pathlib import Path
from src.database.connection import DatabaseManager
from src.services.product_service import ProductService
from src.services.supplier_service import SupplierService
from src.services.sales_service import SalesService
from src.services.purchase_service import PurchaseService
from src.services.export_service import ExportService
from src.ui_web.bridge import FrontendBridge
from src.ui.main_window_web import MainWindowWeb

# Myanmar Unicode Range: \u1000-\u109F, \uAA60-\uAA7F
BURMESE_REGEX = re.compile(r'[\u1000-\u109F\uAA60-\uAA7F]')

def _extract_i18n_dicts(i18n_text):
    """Parse i18n.js to extract en and my dictionaries."""
    en_dict = {}
    my_dict = {}
    current_section = None
    kv_pattern = re.compile(r'^\s*\"([a-zA-Z0-9_.]+)\"\s*:\s*\"(.*)\"\s*,?\s*$')

    for line in i18n_text.splitlines():
        trimmed = line.strip()
        if trimmed.startswith('en: {'):
            current_section = 'en'
            continue
        elif trimmed.startswith('my: {'):
            current_section = 'my'
            continue
        elif trimmed.startswith('};') or trimmed == '}':
            if current_section == 'my' and trimmed.startswith('};'):
                current_section = None
            elif current_section == 'en' and trimmed.startswith('},'):
                current_section = None
            continue

        m = kv_pattern.match(line)
        if m and current_section:
            k, v = m.group(1), m.group(2)
            if current_section == 'en':
                en_dict[k] = v
            elif current_section == 'my':
                my_dict[k] = v

    return en_dict, my_dict


def test_i18n_dictionary_symmetry_and_zero_leakage():
    """Verify 100% key symmetry between EN and MY, and zero Myanmar text leakage in EN."""
    repo_root = Path(__file__).resolve().parent.parent
    i18n_path = repo_root / "src" / "ui_web" / "js" / "i18n.js"
    assert i18n_path.exists(), "i18n.js not found"
    
    text = i18n_path.read_text(encoding="utf-8")
    en_dict, my_dict = _extract_i18n_dicts(text)

    assert len(en_dict) > 200, "English dictionary appears incomplete"
    assert len(my_dict) > 200, "Myanmar dictionary appears incomplete"

    # 1. 100% Key symmetry
    missing_in_my = set(en_dict.keys()) - set(my_dict.keys())
    missing_in_en = set(my_dict.keys()) - set(en_dict.keys())
    assert not missing_in_my, f"Keys present in EN but missing in MY: {missing_in_my}"
    assert not missing_in_en, f"Keys present in MY but missing in EN: {missing_in_en}"

    # 2. Zero Myanmar text in English values
    en_leakage = {k: v for k, v in en_dict.items() if BURMESE_REGEX.search(v)}
    assert not en_leakage, f"English dictionary contains Myanmar characters (leakage): {en_leakage}"


def test_clean_english_fallbacks_in_source_code():
    """Verify that all t('key', fallback) calls across JS files have clean English fallbacks without Myanmar characters."""
    repo_root = Path(__file__).resolve().parent.parent
    js_dir = repo_root / "src" / "ui_web" / "js"
    t_call_pattern = re.compile(r'\bt\(\s*[\'\"]([a-zA-Z0-9_.]+)[\'\"]\s*(?:,\s*[\'\`\"](.*?)[\'\`\"])?\s*\)')

    leaking_fallbacks = []
    for js_file in js_dir.rglob("*.js"):
        if js_file.name == "i18n.js":
            continue
        content = js_file.read_text(encoding="utf-8")
        for match in t_call_pattern.finditer(content):
            key, fallback = match.group(1), match.group(2)
            if fallback and BURMESE_REGEX.search(fallback):
                leaking_fallbacks.append((js_file.name, key, fallback))

    assert not leaking_fallbacks, f"Found Myanmar characters in English fallback parameters: {leaking_fallbacks}"


def test_natural_myanmar_glossary_adherence():
    """Verify that the natural Myanmar pharmacy owner glossary is faithfully applied."""
    repo_root = Path(__file__).resolve().parent.parent
    text = (repo_root / "src" / "ui_web" / "js" / "i18n.js").read_text(encoding="utf-8")
    en_dict, my_dict = _extract_i18n_dicts(text)

    expected_glossary = {
        # Branding
        "app.name": "ဆေးမဟာ",
        # Navigation
        "nav.dashboard": "ပင်မစာမျက်နှာ",
        "nav.sales": "အရောင်း",
        "nav.products": "ကုန်ပစ္စည်းများ",
        "nav.inventory": "လက်ကျန်ပစ္စည်း",
        "nav.purchases": "အဝယ်စာရင်း",
        "nav.suppliers": "ကုန်သွင်းသူများ",
        "nav.expenses": "ဆိုင်သုံးစရိတ်",
        "nav.reports": "အစီရင်ခံစာများ",
        "nav.settings": "ဆက်တင်များ",
        # Products & Inventory
        "col.stock": "လက်ကျန်",
        "col.batch_no": "ဆေးအသုတ် #",
        "col.expiry_date": "သက်တမ်းကုန်ဆုံးရက်",
        "status.expired": "သက်တမ်းကုန်ပြီး",
        "status.expiring_soon": "သက်တမ်းကုန်ရန်နီးသောဆေးများ",
        "col.cost": "တစ်ခုချင်းဝယ်ဈေး (ကျပ်)",
        "col.price": "ရောင်းဈေး",
        "inv.total_valuation": "လက်ကျန်ပစ္စည်းတန်ဖိုး",
        "dash.inventory_valuation": "လက်ကျန်ပစ္စည်းတန်ဖိုး",
        # Sales
        "sales.complete_sale": "အရောင်းသိမ်းမည် (F2)",
        "col.receipt": "ငွေလက်ခံပြေစာ",
        "sales.receipt_subtitle": "ငွေလက်ခံပြေစာ",
        "sales.tendered": "လက်ခံရရှိငွေ",
        "sales.change_due": "ပြန်အမ်းငွေ",
        "sales.search_placeholder": "ကုန်ပစ္စည်းရှာရန်...",
        "btn.void": "အရောင်းမှတ်တမ်းကို ပယ်ဖျက်မည်",
        "sales.void_confirm_title": "အရောင်းမှတ်တမ်းကို ပယ်ဖျက်မည်",
        # Purchases & Suppliers
        "pur.add_button": "အဝယ်စာရင်းသွင်းမည်",
        "pur.modal_title": "အဝယ်စာရင်းသွင်းမည်",
        "col.paid": "ပေးချေပြီးငွေ (ကျပ်)",
        "col.balance": "ပေးရန်ကျန်ငွေ (ကျပ်)",
        "pur.outstanding": "ပေးရန်ကျန်ငွေ (ကျပ်)",
        "sup.modal_payment_title": "ကုန်သွင်းသူထံ ငွေပေးချေမှု",
        # Finance & System
        "rep.kpi_revenue": "အရောင်းရငွေ",
        "dash.revenue_today": "ယနေ့ အရောင်းရငွေ",
        "rep.kpi_cogs": "ရောင်းကုန်တန်ဖိုး (COGS)",
        "rep.kpi_gross_profit": "အကြမ်းဖျင်းအမြတ်",
        "dash.gross_profit_today": "ယနေ့ အကြမ်းဖျင်းအမြတ်",
        "rep.kpi_expenses": "လုပ်ငန်းလည်ပတ်စရိတ်",
        "rep.kpi_net_profit": "လုပ်ငန်းလည်ပတ်မှု အသားတင်အမြတ်",
        "set.backup_btn": "ဒေတာအရန်သိမ်းမည်",
        "set.restore_title": "အရန်သိမ်းထားသောဒေတာ ပြန်လည်ရယူခြင်း (Restore)",
        "btn.export_excel": "Excel ဖိုင်ထုတ်မည်",
        "btn.cancel": "မလုပ်တော့ပါ",
        "btn.save": "သိမ်းမည်",
        "btn.edit": "ပြင်ဆင်မည်",
    }

    for key, expected_val in expected_glossary.items():
        assert key in my_dict, f"Missing key {key} in my_dict"
        assert my_dict[key] == expected_val, f"Glossary mismatch for {key}: expected '{expected_val}', got '{my_dict[key]}'"


def test_branding_consistency_across_layers(qapp, db_manager):
    """Verify Say Mahar / ဆေးမဟာ branding is consistently present across UI chrome, window title, and export workbooks."""
    repo_root = Path(__file__).resolve().parent.parent
    
    # 1. i18n app name and receipt titles
    text = (repo_root / "src" / "ui_web" / "js" / "i18n.js").read_text(encoding="utf-8")
    en_dict, my_dict = _extract_i18n_dicts(text)
    assert en_dict["app.name"] == "Say Mahar"
    assert my_dict["app.name"] == "ဆေးမဟာ"
    assert en_dict["sales.receipt_title"] == "SAY MAHAR PHARMACY & RETAIL"
    assert my_dict["sales.receipt_title"] == "ဆေးမဟာ ဆေးဆိုင်နှင့် ကုန်စုံဆိုင်"

    # 2. Window title in MainWindowWeb
    services = {'db_manager': db_manager}
    main_win = MainWindowWeb(services)
    assert "Say Mahar" in main_win.windowTitle()
    main_win.update_language_title("my")
    assert "ဆေးမဟာ" in main_win.windowTitle()
    main_win.update_language_title("en")
    assert "Say Mahar" in main_win.windowTitle()

    # 3. Excel Export Service Title Block
    export_service = ExportService(services)
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    export_service._write_title_block(ws, "Test Report", "Test Subtitle", 5)
    row1_val = ws.cell(row=1, column=1).value
    assert "Say Mahar" in row1_val, f"Expected 'Say Mahar' in export title row 1, got {row1_val}"


def test_burmese_data_preservation_under_both_languages(db_manager):
    """Verify user-entered Burmese product & supplier names remain intact and unmutated under language switching."""
    from src.services.product_service import ProductService
    from src.services.supplier_service import SupplierService

    prod_service = ProductService(db_manager)
    sup_service = SupplierService(db_manager)

    # 1. Create a Burmese-named supplier and product
    sup_id = sup_service.create_supplier(
        name="ရွှေဆေးဝါး ကုန်သည်ကြီးများ",
        phone="09-123456789",
        address="ရန်ကုန်မြို့၊ မင်္ဂလာတောင်ညွန့်မြို့နယ်"
    )

    # Create category first
    with db_manager.transaction() as tx:
        tx.execute("INSERT OR IGNORE INTO categories (name) VALUES ('ဆေးဝါးများ')")
        cat_id = tx.execute("SELECT id FROM categories WHERE name = 'ဆေးဝါးများ'").fetchone()[0]

    prod_id = prod_service.create_product(
        name="ပါရာစီတမော ၅၀၀ မီလီဂရမ် (Biogesic)",
        category_id=cat_id,
        unit_measure="ကတ်",
        selling_price=1500,
        min_stock_level=10,
        is_medicine=True
    )

    # 2. Test language switching via bridge
    bridge = FrontendBridge({'db_manager': db_manager})
    bridge.set_language('my')
    assert json.loads(bridge.get_language())['data'] == 'my'

    # Read records back
    conn = db_manager.get_connection()
    p_row = conn.execute("SELECT name, unit_measure FROM products WHERE id = ?", (prod_id,)).fetchone()
    s_row = conn.execute("SELECT name, address FROM suppliers WHERE id = ?", (sup_id,)).fetchone()

    assert p_row['name'] == "ပါရာစီတမော ၅၀၀ မီလီဂရမ် (Biogesic)"
    assert p_row['unit_measure'] == "ကတ်"
    assert s_row['name'] == "ရွှေဆေးဝါး ကုန်သည်ကြီးများ"

    # Switch back to English mode
    bridge.set_language('en')
    assert json.loads(bridge.get_language())['data'] == 'en'

    # Verify Burmese user data is 100% UNCHANGED in English mode
    p_row_en = conn.execute("SELECT name, unit_measure FROM products WHERE id = ?", (prod_id,)).fetchone()
    s_row_en = conn.execute("SELECT name, address FROM suppliers WHERE id = ?", (sup_id,)).fetchone()

    assert p_row_en['name'] == "ပါရာစီတမော ၅၀၀ မီလီဂရမ် (Biogesic)"
    assert p_row_en['unit_measure'] == "ကတ်"
    assert s_row_en['name'] == "ရွှေဆေးဝါး ကုန်သည်ကြီးများ"
