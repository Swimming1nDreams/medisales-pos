import re
import json
import time
import pytest
from pathlib import Path
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
from src.ui_web.bridge import FrontendBridge
from src.ui.main_window_web import MainWindowWeb


@pytest.fixture
def recon_services(tmp_path):
    db_file = str(tmp_path / "test_cash_recon.db")
    db_manager = DatabaseManager(db_file)
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
    yield services
    db_manager.close()


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
        app.processEvents()
        time.sleep(0.02)
    return result


def test_settings_reconciliation_static_inspection():
    """Verify statically that 20,000 MMK and 50,000 MMK notes and 100/200 small-change pieces

    are not present, and that the manual small-change amount input and valid banknotes exist.
    """
    repo_root = Path(__file__).resolve().parent.parent
    settings_js = repo_root / "src" / "ui_web" / "js" / "pages" / "settings.js"
    assert settings_js.exists(), "settings.js must exist"

    content = settings_js.read_text(encoding="utf-8")

    # 1. 20,000 MMK and 50,000 MMK denominations must be absent from getDenominations
    # getDenominations should only contain 10000, 5000, 1000, 500
    denom_match = re.search(r'function getDenominations\(\)\s*\{[\s\S]*?return\s*\[([\s\S]*?)\];', content)
    assert denom_match is not None, "getDenominations function not found"
    denom_block = denom_match.group(1)

    assert "50000" not in denom_block, "50000 MMK denomination still present in getDenominations"
    assert "20000" not in denom_block, "20000 MMK denomination still present in getDenominations"
    assert "10000" in denom_block, "10000 MMK denomination should be present"
    assert "5000" in denom_block, "5000 MMK denomination should be present"
    assert "1000" in denom_block, "1000 MMK denomination should be present"
    assert "500" in denom_block, "500 MMK denomination should be present"

    # 2. No buttons or piece-counting for 100 or 200 MMK
    assert "denom_100" not in content, "100 MMK piece denomination found"
    assert "denom_200" not in content, "200 MMK piece denomination found"

    # 3. Manual small-change input field id exists
    assert 'id="denom-small-change"' in content, "denom-small-change input field missing"
    assert "updateSmallChange" in content, "updateSmallChange function missing"
    assert "saveReconciliation" in content, "saveReconciliation function missing"
    assert "loadSavedReconciliation" in content, "loadSavedReconciliation function missing"


def test_reconciliation_service_logic_and_validation(recon_services):
    """Test backend ReconciliationService calculation, validation, persistence, and reopening."""
    recon_svc = recon_services['reconciliation_service']

    # 1. Entering 1,700 MMK with valid banknotes calculates correctly
    record = recon_svc.save_cash_reconciliation({
        "date": "2026-10-12",
        "denominations": {
            "10000": 3,  # 30,000 Ks
            "5000": 2,   # 10,000 Ks
            "1000": 5,   # 5,000 Ks
            "500": 4     # 2,000 Ks
        },               # Subtotal banknotes: 47,000 Ks
        "small_change_amount": 1700,
        "expected_sales": 48000
    })

    # Total counted must be 47,000 + 1,700 = 48,700 MMK
    assert record['small_change_amount'] == 1700
    assert record['total_counted'] == 48700
    # Expected: 48,000 -> Variance: +700 MMK
    assert record['variance'] == 700

    # 2. Reopening / retrieving the saved reconciliation preserves small change
    reopened = recon_svc.get_cash_reconciliation("2026-10-12")
    assert reopened is not None
    assert reopened['date'] == "2026-10-12"
    assert reopened['small_change_amount'] == 1700
    assert reopened['total_counted'] == 48700
    assert reopened['variance'] == 700
    assert reopened['denominations'] == {"10000": 3, "5000": 2, "1000": 5, "500": 4}

    # Also check latest
    latest = recon_svc.get_cash_reconciliation()
    assert latest is not None
    assert latest['small_change_amount'] == 1700

    # 3. Empty small change defaults to 0
    record_empty = recon_svc.save_cash_reconciliation({
        "date": "2026-10-13",
        "denominations": {"10000": 1},
        "small_change_amount": "",
        "expected_sales": 10000
    })
    assert record_empty['small_change_amount'] == 0
    assert record_empty['total_counted'] == 10000
    assert record_empty['variance'] == 0

    # 4. Zero small change works
    record_zero = recon_svc.save_cash_reconciliation({
        "date": "2026-10-14",
        "denominations": {"10000": 1},
        "small_change_amount": 0,
        "expected_sales": 12000
    })
    assert record_zero['small_change_amount'] == 0
    assert record_zero['total_counted'] == 10000
    assert record_zero['variance'] == -2000  # shortage

    # 5. Negative small change amount is rejected
    with pytest.raises(ValueError, match="non-negative"):
        recon_svc.save_cash_reconciliation({
            "date": "2026-10-15",
            "denominations": {"10000": 1},
            "small_change_amount": -500,
            "expected_sales": 10000
        })

    # 6. Invalid text small change is rejected
    with pytest.raises(ValueError, match="non-negative"):
        recon_svc.save_cash_reconciliation({
            "date": "2026-10-15",
            "denominations": {"10000": 1},
            "small_change_amount": "invalid_text",
            "expected_sales": 10000
        })

    # 7. Negative denomination count is rejected
    with pytest.raises(ValueError, match="cannot be negative"):
        recon_svc.save_cash_reconciliation({
            "date": "2026-10-15",
            "denominations": {"10000": -2},
            "small_change_amount": 100,
            "expected_sales": 10000
        })


def test_reconciliation_bridge_methods(recon_services):
    """Test FrontendBridge integration with cash reconciliation."""
    bridge = FrontendBridge(recon_services)

    save_payload = json.dumps({
        "date": "2026-10-12",
        "denominations": {"10000": 2, "5000": 1},
        "small_change_amount": 1700,
        "expected_sales": 26000
    })
    res_str = bridge.save_cash_reconciliation(save_payload)
    res = json.loads(res_str)
    assert res['status'] == 'success'
    assert res['data']['small_change_amount'] == 1700
    assert res['data']['total_counted'] == 26700
    assert res['data']['variance'] == 700

    # Get back
    get_str = bridge.get_cash_reconciliation("2026-10-12")
    get_res = json.loads(get_str)
    assert get_res['status'] == 'success'
    assert get_res['data']['small_change_amount'] == 1700


def test_settings_reconciliation_runtime_ui(qapp, recon_services):
    """Full UI test in MainWindowWeb QWebEngine:

    - Verifies 20,000 MMK and 50,000 MMK buttons/inputs are absent.
    - Verifies no 100 MMK or 200 MMK pieces buttons.
    - Verifies manual small-change input exists.
    - Verifies entering 1,700 MMK adds exactly 1,700 MMK.
    - Verifies cash difference calculation.
    - Verifies empty, zero, invalid, and negative input handling.
    - Verifies saving and reopening preserves the entered small-change amount.
    - Verifies existing banknote counting still works.
    """
    window = MainWindowWeb(recon_services)
    window.resize(1280, 800)
    window.show()

    # Wait for page load
    wait_for_ms(2000)

    # Navigate to Settings
    run_js(window, "navigate('settings');")

    rendered = False
    for _ in range(30):
        val = run_js(window, "window._renderedPage === 'settings' && document.getElementById('denom-small-change') !== null;")
        if val is True:
            rendered = True
            break
        wait_for_ms(200)

    assert rendered, "Settings page did not render reconciliation widget"

    # 1. 20k and 50k buttons/inputs are absent from DOM
    assert run_js(window, "document.getElementById('denom-50000') === null;") is True
    assert run_js(window, "document.getElementById('denom-20000') === null;") is True
    assert run_js(window, "document.getElementById('denom-100') === null;") is True
    assert run_js(window, "document.getElementById('denom-200') === null;") is True

    # 2. Banknote denominations 10000, 5000, 1000, 500 and manual small-change input exist
    assert run_js(window, "document.getElementById('denom-10000') !== null;") is True
    assert run_js(window, "document.getElementById('denom-5000') !== null;") is True
    assert run_js(window, "document.getElementById('denom-1000') !== null;") is True
    assert run_js(window, "document.getElementById('denom-500') !== null;") is True
    assert run_js(window, "document.getElementById('denom-small-change') !== null;") is True

    # 3. Test Reset
    run_js(window, "resetDenominations();")
    assert run_js(window, "document.getElementById('recon-counted').innerText.trim();") == "0 Ks"

    # 4. Banknote counting test:
    # 2 x 10,000 Ks = 20,000 Ks
    run_js(window, "updateDenomination(10000, '2', 20000);")
    assert run_js(window, "document.getElementById('subtotal-10000').innerText.trim();") == "20,000 Ks"
    assert run_js(window, "document.getElementById('recon-counted').innerText.trim();") == "20,000 Ks"
    # Balanced (20,000 - 20,000 = 0)
    variance_txt = run_js(window, "document.getElementById('recon-variance').innerText;")
    assert "Balanced" in variance_txt or "0 Ks" in variance_txt

    # 5. Entering 1,700 MMK adds exactly 1,700 MMK to total counted cash
    run_js(window, "updateSmallChange('1700', 20000);")
    assert run_js(window, "document.getElementById('subtotal-small-change').innerText.trim();") == "1,700 Ks"
    assert run_js(window, "document.getElementById('recon-counted').innerText.trim();") == "21,700 Ks"

    # Cash difference: 21,700 - 20,000 = +1,700 Ks Surplus
    variance_txt = run_js(window, "document.getElementById('recon-variance').innerText;")
    assert "+1,700 Ks" in variance_txt
    assert "Surplus" in variance_txt

    # 6. Validation tests:
    # (a) Negative input: "-500"
    run_js(window, "updateSmallChange('-500', 20000);")
    is_err_visible = run_js(window, "!document.getElementById('small-change-error').classList.contains('hidden');")
    assert is_err_visible is True, "Error message should be visible on negative input"
    is_save_disabled = run_js(window, "document.getElementById('save-recon-btn').disabled;")
    assert is_save_disabled is True, "Save button should be disabled on invalid input"

    # (b) Invalid text: "abc"
    run_js(window, "updateSmallChange('abc', 20000);")
    is_err_visible = run_js(window, "!document.getElementById('small-change-error').classList.contains('hidden');")
    assert is_err_visible is True, "Error message should be visible on text input"

    # (c) Empty input: "" -> treated as 0
    run_js(window, "updateSmallChange('', 20000);")
    is_err_visible = run_js(window, "!document.getElementById('small-change-error').classList.contains('hidden');")
    assert is_err_visible is False, "Error message should be hidden on empty input"
    is_save_disabled = run_js(window, "document.getElementById('save-recon-btn').disabled;")
    assert is_save_disabled is False, "Save button should be enabled on empty input"
    assert run_js(window, "document.getElementById('recon-counted').innerText.trim();") == "20,000 Ks"

    # (d) Zero input: "0" -> treated as 0
    run_js(window, "updateSmallChange('0', 20000);")
    assert run_js(window, "document.getElementById('recon-counted').innerText.trim();") == "20,000 Ks"

    # 7. Set 1,700 MMK again and save reconciliation
    run_js(window, "updateSmallChange('1700', 20000);")
    assert run_js(window, "document.getElementById('recon-counted').innerText.trim();") == "21,700 Ks"

    # Save via UI
    saved_res = run_js(window, "saveReconciliation();")
    wait_for_ms(500)

    # 8. Reset form and verify it resets to 0
    run_js(window, "resetDenominations();")
    assert run_js(window, "document.getElementById('recon-counted').innerText.trim();") == "0 Ks"
    assert run_js(window, "document.getElementById('denom-small-change').value;") == "0"
    assert run_js(window, "document.getElementById('denom-10000').value;") == "0"

    # 9. Reopen / reload saved reconciliation
    run_js(window, "loadSavedReconciliation();")
    wait_for_ms(500)

    # Verify small-change amount 1,700 is restored and counted cash is 21,700 Ks
    val_change = run_js(window, "document.getElementById('denom-small-change').value;")
    assert val_change == "1700"
    val_10k = run_js(window, "document.getElementById('denom-10000').value;")
    assert val_10k == "2"
    counted_txt = run_js(window, "document.getElementById('recon-counted').innerText.trim();")
    assert counted_txt == "21,700 Ks"

    window.close()
