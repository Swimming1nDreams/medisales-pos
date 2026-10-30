import pytest
import json
from src.services.customer_service import CustomerService
from src.services.sales_service import SalesService
from src.services.product_service import ProductService
from src.services.purchase_service import PurchaseService
from src.services.supplier_service import SupplierService
from src.ui_web.bridge import FrontendBridge

@pytest.fixture
def test_setup(db_manager, product_service, sales_service, customer_service, supplier_service, purchase_service, report_service, dashboard_service):
    # Create test product (general)
    cat_id = product_service.create_category("Vitamins")
    prod_id = product_service.create_product(
        name="Vitamin C 500mg",
        category_id=cat_id,
        unit_measure="bottle",
        selling_price=5200,
        min_stock_level=5,
        is_medicine=False
    )

    # Stock up product via purchase
    supp_id = supplier_service.create_supplier("Vendor A", "091111111", "Yangon")
    purchase_service.create_purchase(
        reference="PUR-INIT-001",
        supplier_id=supp_id,
        date="2026-10-30",
        items=[{
            'product_id': prod_id,
            'quantity': 100,
            'unit_cost': 3500,
            'batch_number': None,
            'expiry_date': None
        }]
    )

    services_dict = {
        'product_service': product_service,
        'sales_service': sales_service,
        'customer_service': customer_service,
        'supplier_service': supplier_service,
        'purchase_service': purchase_service,
        'report_service': report_service,
        'dashboard_service': dashboard_service
    }

    return {
        'product_id': prod_id,
        'customer_service': customer_service,
        'sales_service': sales_service,
        'db_manager': db_manager,
        'services': services_dict
    }

def test_customer_crud_and_balances(test_setup):
    cs = test_setup['customer_service']
    
    # 1. Create customer
    cid = cs.create_customer("Daw Hla", "0912345678", "No 12 Main St", "VIP Customer")
    assert cid > 0

    # 2. Get customer
    cust = cs.get_customer(cid)
    assert cust['name'] == "Daw Hla"
    assert cust['phone'] == "0912345678"
    assert cust['is_active'] == 1

    # 3. Initial balance check
    bals = cs.get_customer_balances()
    cust_bal = next(b for b in bals if b['customer_id'] == cid)
    assert cust_bal['total_credit'] == 0
    assert cust_bal['total_repaid'] == 0
    assert cust_bal['outstanding_balance'] == 0

    # 4. Update customer
    cs.update_customer(cid, "Daw Hla (Market)", "0999999999", "No 12 Market Rd", "Notes", True)
    updated = cs.get_customer(cid)
    assert updated['name'] == "Daw Hla (Market)"
    assert updated['phone'] == "0999999999"

def test_sale_with_discount_and_rounding(test_setup):
    ss = test_setup['sales_service']
    pid = test_setup['product_id']

    # Subtotal = 5,200 Ks. Cashier gives 200 Ks round-off discount -> Net = 5,000 Ks
    sale_id = ss.create_sale(
        reference="INV-DISC-001",
        items=[{'product_id': pid, 'quantity': 1, 'unit_price': 5200}],
        amount_received=5000,
        discount_amount=200,
        payment_type='cash'
    )
    assert sale_id > 0
    sale = ss.get_sale(sale_id)
    assert sale['subtotal'] == 5200
    assert sale['discount_amount'] == 200
    assert sale['total_amount'] == 5000
    assert sale['amount_received'] == 5000
    assert sale['change_given'] == 0
    assert sale['payment_type'] == 'cash'

def test_discount_cannot_exceed_subtotal(test_setup):
    ss = test_setup['sales_service']
    pid = test_setup['product_id']

    with pytest.raises(ValueError, match="Discount cannot exceed sale subtotal"):
        ss.create_sale(
            reference="INV-DISC-FAIL",
            items=[{'product_id': pid, 'quantity': 1, 'unit_price': 5200}],
            amount_received=5000,
            discount_amount=6000
        )

def test_credit_sale_and_repayment(test_setup):
    cs = test_setup['customer_service']
    ss = test_setup['sales_service']
    pid = test_setup['product_id']

    cid = cs.create_customer("Ko Min", "0977777777", "Downtown", "")
    
    # 1. Credit sale: 2 items @ 5,200 = 10,400 Ks.
    # Discount 400 Ks -> Net Total = 10,000 Ks.
    # Customer pays 3,000 Ks cash upfront -> Remaining Credit = 7,000 Ks.
    sale_id = ss.create_sale(
        reference="INV-CRED-001",
        items=[{'product_id': pid, 'quantity': 2, 'unit_price': 5200}],
        amount_received=3000,
        discount_amount=400,
        payment_type='credit',
        customer_id=cid
    )
    assert sale_id > 0
    
    sale = ss.get_sale(sale_id)
    assert sale['subtotal'] == 10400
    assert sale['discount_amount'] == 400
    assert sale['total_amount'] == 10000
    assert sale['amount_received'] == 3000
    assert sale['credit_amount'] == 7000
    assert sale['payment_type'] == 'credit'

    # Check customer debt
    bals = cs.get_customer_balances()
    cust_bal = next(b for b in bals if b['customer_id'] == cid)
    assert cust_bal['total_credit'] == 7000
    assert cust_bal['total_repaid'] == 0
    assert cust_bal['outstanding_balance'] == 7000

    # 2. Customer pays 5,000 Ks toward their debt
    pay_ref = cs.record_debt_repayment(cid, 5000, "Partial cash repayment")
    assert pay_ref.startswith("CPAY-")

    bals_after = cs.get_customer_balances()
    cust_bal_after = next(b for b in bals_after if b['customer_id'] == cid)
    assert cust_bal_after['total_credit'] == 7000
    assert cust_bal_after['total_repaid'] == 5000
    assert cust_bal_after['outstanding_balance'] == 2000

    # 3. Statement check
    stmt = cs.get_customer_statement(cid)
    assert stmt['total_credit'] == 7000
    assert stmt['total_repaid'] == 5000
    assert stmt['outstanding_balance'] == 2000
    assert len(stmt['entries']) == 2

def test_void_credit_sale_reverses_customer_debt(test_setup):
    cs = test_setup['customer_service']
    ss = test_setup['sales_service']
    pid = test_setup['product_id']

    cid = cs.create_customer("Daw Mya", "0988888888", "Ward 5", "")
    sale_id = ss.create_sale(
        reference="INV-CRED-VOID",
        items=[{'product_id': pid, 'quantity': 1, 'unit_price': 5200}],
        amount_received=0,
        discount_amount=200,
        payment_type='credit',
        customer_id=cid
    )
    
    bals = cs.get_customer_balances()
    cust_bal = next(b for b in bals if b['customer_id'] == cid)
    assert cust_bal['outstanding_balance'] == 5000

    # Void sale
    ss.void_sale(sale_id)

    bals_void = cs.get_customer_balances()
    cust_bal_void = next(b for b in bals_void if b['customer_id'] == cid)
    assert cust_bal_void['outstanding_balance'] == 0

def test_bridge_customer_and_sales_slots(test_setup):
    services = test_setup['services']
    bridge = FrontendBridge(services)

    # 1. Create customer via bridge
    res_str = bridge.create_customer("U Ba", "0944444444", "Insein", "Friend")
    res = json.loads(res_str)
    assert res['status'] == "success"
    cid = res['data']['customer_id']

    # 2. List customers
    list_str = bridge.list_customers()
    custs = json.loads(list_str)['data']
    assert any(c['id'] == cid for c in custs)

    # 3. Create sale with discount & credit via bridge
    items = json.dumps([{'product_id': test_setup['product_id'], 'quantity': 1, 'unit_price': 5200}])
    sale_res_str = bridge.create_sale("INV-BRIDGE-001", items, 0.0, 200.0, "credit", str(cid))
    sale_res = json.loads(sale_res_str)
    assert sale_res['status'] == "success"

    # 4. Get customer balances via bridge
    bal_str = bridge.get_customer_balances()
    bals = json.loads(bal_str)['data']
    cust_bal = next(b for b in bals if b['customer_id'] == cid)
    assert cust_bal['outstanding_balance'] == 5000

    # 5. Record repayment via bridge
    repay_str = bridge.record_customer_payment(cid, 5000, "Cleared debt")
    assert json.loads(repay_str)['status'] == "success"

    # 6. Customer statement via bridge
    stmt_str = bridge.get_customer_statement(cid)
    stmt = json.loads(stmt_str)['data']
    assert stmt['outstanding_balance'] == 0
