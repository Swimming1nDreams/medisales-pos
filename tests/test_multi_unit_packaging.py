import pytest
import json
from src.services.product_service import ProductService
from src.services.sales_service import SalesService
from src.services.purchase_service import PurchaseService
from src.services.supplier_service import SupplierService
from src.ui_web.bridge import FrontendBridge

@pytest.fixture
def multi_unit_setup(db_manager, product_service, sales_service, supplier_service, purchase_service, report_service, dashboard_service):
    cat_id = product_service.create_category("Antibiotics")
    supp_id = supplier_service.create_supplier("Vendor BioMed", "0911223344", "Yangon")

    services_dict = {
        'product_service': product_service,
        'sales_service': sales_service,
        'supplier_service': supplier_service,
        'purchase_service': purchase_service,
        'report_service': report_service,
        'dashboard_service': dashboard_service
    }

    return {
        'cat_id': cat_id,
        'supp_id': supp_id,
        'product_service': product_service,
        'sales_service': sales_service,
        'purchase_service': purchase_service,
        'db_manager': db_manager,
        'services': services_dict
    }

def test_product_packaging_crud_and_validation(multi_unit_setup):
    ps = multi_unit_setup['product_service']
    cat_id = multi_unit_setup['cat_id']

    # 1. Create product with 2 packaging tiers: Strip (10) and Box (100)
    prod_id = ps.create_product(
        name="Amoxicillin 500mg",
        category_id=cat_id,
        unit_measure="tablet",
        selling_price=150,
        min_stock_level=20,
        is_medicine=True,
        packagings=[
            {'unit_name': 'Strip', 'conversion_factor': 10, 'selling_price': 1400},
            {'unit_name': 'Box', 'conversion_factor': 100, 'selling_price': 13500}
        ]
    )
    assert prod_id > 0

    # 2. Verify packagings attached in get_product and list_products
    prod = ps.get_product(prod_id)
    assert prod['name'] == "Amoxicillin 500mg"
    assert prod['unit_measure'] == "tablet"
    assert len(prod['packagings']) == 2
    assert prod['packagings'][0]['unit_name'] == "Strip"
    assert prod['packagings'][0]['conversion_factor'] == 10
    assert prod['packagings'][0]['selling_price'] == 1400
    assert prod['packagings'][1]['unit_name'] == "Box"
    assert prod['packagings'][1]['conversion_factor'] == 100

    prods = ps.list_products()
    found = next(p for p in prods if p['id'] == prod_id)
    assert len(found['packagings']) == 2

    # 3. Validation: factor <= 1 must raise error
    with pytest.raises(ValueError, match="must be greater than 1"):
        ps.set_product_packagings(prod_id, [{'unit_name': 'Invalid', 'conversion_factor': 1, 'selling_price': 100}])

    # 4. Validation: duplicate unit name must raise error
    with pytest.raises(ValueError, match="Duplicate packaging unit"):
        ps.set_product_packagings(prod_id, [
            {'unit_name': 'Strip', 'conversion_factor': 10, 'selling_price': 1400},
            {'unit_name': 'Strip', 'conversion_factor': 20, 'selling_price': 2500}
        ])

    # 5. Validation: packaging unit cannot have same name as base unit
    with pytest.raises(ValueError, match="same name as base unit"):
        ps.set_product_packagings(prod_id, [{'unit_name': 'tablet', 'conversion_factor': 10, 'selling_price': 1000}])

    # 6. Update packagings
    ps.update_product(
        prod_id, "Amoxicillin 500mg", cat_id, "tablet", 160, 25, True,
        packagings=[
            {'unit_name': 'Strip', 'conversion_factor': 10, 'selling_price': 1500},
            {'unit_name': 'Box', 'conversion_factor': 100, 'selling_price': 14000},
            {'unit_name': 'Carton', 'conversion_factor': 1000, 'selling_price': 130000}
        ]
    )
    updated = ps.get_product(prod_id)
    assert len(updated['packagings']) == 3
    assert updated['selling_price'] == 160
    assert updated['packagings'][2]['unit_name'] == "Carton"

def test_purchase_intake_with_packaging_conversion(multi_unit_setup):
    ps = multi_unit_setup['product_service']
    purch_s = multi_unit_setup['purchase_service']
    cat_id = multi_unit_setup['cat_id']
    supp_id = multi_unit_setup['supp_id']

    prod_id = ps.create_product(
        name="Paracetamol 500mg",
        category_id=cat_id,
        unit_measure="tablet",
        selling_price=100,
        min_stock_level=50,
        is_medicine=True,
        packagings=[
            {'unit_name': 'Box', 'conversion_factor': 100, 'selling_price': 9000}
        ]
    )

    # Receive 5 Boxes @ 7,000 Ks per Box = 35,000 Ks total.
    # Base units = 5 * 100 = 500 tablets.
    # Unit cost per tablet = 7000 / 100 = 70 Ks.
    purch_id = purch_s.create_purchase(
        reference="PO-MULTI-001",
        supplier_id=supp_id,
        date="2026-10-31",
        items=[{
            'product_id': prod_id,
            'quantity': 5,
            'unit_cost': 7000,
            'packaging_unit': 'Box',
            'packaging_factor': 100,
            'batch_number': 'BATCH-BOX-01',
            'expiry_date': '2028-12-31'
        }]
    )
    assert purch_id > 0

    # Check product stock: must be 500 tablets, total value = 35,000 Ks
    prod = ps.get_product(prod_id)
    assert prod['current_stock'] == 500
    assert prod['inventory_value'] == 35000

def test_pos_sale_with_multi_unit_and_inventory_deduction(multi_unit_setup):
    ps = multi_unit_setup['product_service']
    sales_s = multi_unit_setup['sales_service']
    purch_s = multi_unit_setup['purchase_service']
    cat_id = multi_unit_setup['cat_id']
    supp_id = multi_unit_setup['supp_id']

    prod_id = ps.create_product(
        name="Cetirizine 10mg",
        category_id=cat_id,
        unit_measure="tablet",
        selling_price=200,
        min_stock_level=10,
        is_medicine=True,
        packagings=[
            {'unit_name': 'Strip', 'conversion_factor': 10, 'selling_price': 1800},
            {'unit_name': 'Box', 'conversion_factor': 100, 'selling_price': 17000}
        ]
    )

    # Initial stock: 1 Box = 100 tablets @ 10,000 Ks total
    purch_s.create_purchase(
        reference="PO-CET-001",
        supplier_id=supp_id,
        date="2026-10-31",
        items=[{
            'product_id': prod_id,
            'quantity': 1,
            'unit_cost': 10000,
            'packaging_factor': 100,
            'batch_number': 'BATCH-C01',
            'expiry_date': '2027-10-31'
        }]
    )

    assert ps.get_product(prod_id)['current_stock'] == 100

    # 1. Sell 2 Strips (2 x 10 = 20 tablets) @ 1,800 Ks = 3,600 Ks
    sale_id = sales_s.create_sale(
        reference="INV-UOM-001",
        items=[{
            'product_id': prod_id,
            'quantity': 2,
            'unit_price': 1800,
            'packaging_unit': 'Strip',
            'packaging_factor': 10
        }],
        amount_received=3600
    )
    assert sale_id > 0

    # Stock must now be 100 - 20 = 80 tablets
    assert ps.get_product(prod_id)['current_stock'] == 80

    # 2. Sell 5 Tablets (base unit) @ 200 Ks = 1,000 Ks
    sale_id_2 = sales_s.create_sale(
        reference="INV-UOM-002",
        items=[{
            'product_id': prod_id,
            'quantity': 5,
            'unit_price': 200,
            'packaging_unit': None,
            'packaging_factor': 1
        }],
        amount_received=1000
    )
    assert sale_id_2 > 0

    # Stock must now be 80 - 5 = 75 tablets
    assert ps.get_product(prod_id)['current_stock'] == 75

    # 3. Stock warning: Attempting to sell 1 Box (100 tablets) when only 75 available must fail
    with pytest.raises(ValueError, match="Insufficient stock"):
        sales_s.create_sale(
            reference="INV-UOM-FAIL",
            items=[{
                'product_id': prod_id,
                'quantity': 1,
                'unit_price': 17000,
                'packaging_unit': 'Box',
                'packaging_factor': 100
            }],
            amount_received=17000
        )

    # 4. Void sale 1: Voiding the 2 Strips sale must restore exactly 20 tablets
    sales_s.void_sale(sale_id)
    assert ps.get_product(prod_id)['current_stock'] == 95

def test_bridge_multi_unit_product_and_sale(multi_unit_setup):
    services = multi_unit_setup['services']
    bridge = FrontendBridge(services)
    cat_id = multi_unit_setup['cat_id']
    supp_id = multi_unit_setup['supp_id']

    # 1. Create product via bridge with packaging JSON
    pkgs = [
        {'unit_name': 'Strip', 'conversion_factor': 10, 'selling_price': 2000},
        {'unit_name': 'Box', 'conversion_factor': 100, 'selling_price': 19000}
    ]
    res_str = bridge.create_product(
        "Ibuprofen 400mg", cat_id, "tablet", 220.0, 15, True, json.dumps(pkgs)
    )
    res = json.loads(res_str)
    assert res['status'] == 'success'
    prod_id = res['data']['product_id']

    # 2. Get packagings via bridge
    pkgs_str = bridge.get_product_packagings(prod_id)
    retrieved_pkgs = json.loads(pkgs_str)['data']
    assert len(retrieved_pkgs) == 2
    assert retrieved_pkgs[0]['unit_name'] == "Strip"

    # 3. Stock intake via purchase service
    services['purchase_service'].create_purchase(
        reference="PO-IBU-001",
        supplier_id=supp_id,
        date="2026-10-31",
        items=[{
            'product_id': prod_id,
            'quantity': 2,
            'unit_cost': 15000,
            'packaging_factor': 100,
            'batch_number': 'BATCH-IBU-01',
            'expiry_date': '2028-05-01'
        }]
    )

    # 4. Sell 1 Box (100 tablets) via bridge create_sale
    items = json.dumps([{
        'product_id': prod_id,
        'quantity': 1,
        'unit_price': 19000,
        'packaging_unit': 'Box',
        'packaging_factor': 100
    }])
    sale_str = bridge.create_sale("INV-BRIDGE-UOM", items, 19000.0, 0.0, "cash", "")
    assert json.loads(sale_str)['status'] == 'success'

    # 5. Verify remaining stock: 200 - 100 = 100 tablets
    prod = services['product_service'].get_product(prod_id)
    assert prod['current_stock'] == 100
