import pytest
import sqlite3
from src.services.product_service import ProductService
from src.services.inventory_service import InventoryService
from src.services.reconciliation_service import ReconciliationService

@pytest.fixture
def product_service(db_manager):
    return ProductService(db_manager)

@pytest.fixture
def inventory_service(db_manager):
    return InventoryService(db_manager)

@pytest.fixture
def reconciliation_service(db_manager):
    return ReconciliationService(db_manager)

def test_category_management(product_service):
    cat_id = product_service.create_category("Test Category")
    assert cat_id > 0
    
    # Duplicate prevention
    with pytest.raises(ValueError, match="already exists"):
        product_service.create_category("Test Category")
        
    cats = product_service.list_categories()
    assert len(cats) == 1
    assert cats[0]['name'] == "Test Category"
    
    # Deactivate
    product_service.update_category(cat_id, "Test Category Updated", False)
    assert len(product_service.list_categories(include_inactive=False)) == 0
    assert len(product_service.list_categories(include_inactive=True)) == 1

def test_product_validation(product_service):
    cat_id = product_service.create_category("Merch")
    
    # Valid
    p_id = product_service.create_product("Soap", cat_id, "pcs", 100, 10, False)
    assert p_id > 0
    
    # Negative Price
    with pytest.raises(ValueError, match="cannot be negative"):
        product_service.create_product("Bad", cat_id, "pcs", -10, 10, False)
        
    # Fractional
    with pytest.raises(ValueError, match="Fractional Kyat"):
        product_service.create_product("Bad2", cat_id, "pcs", 10.5, 10, False)

def test_opening_stock_general(product_service, inventory_service, reconciliation_service, db_manager):
    cat_id = product_service.create_category("Merch")
    p_id = product_service.create_product("Soap", cat_id, "pcs", 100, 10, False)
    
    inventory_service.record_opening_stock_general(p_id, 50, 40)
    
    # Duplicate prevention
    with pytest.raises(ValueError, match="already recorded"):
        inventory_service.record_opening_stock_general(p_id, 10, 40)
        
    rec = reconciliation_service.reconcile_product_stock(p_id)
    assert rec['stock_match'] is True
    assert rec['db_stock'] == 50
    assert rec['value_match'] is True
    assert rec['db_value'] == 2000

def test_opening_stock_medicine(product_service, inventory_service, reconciliation_service):
    cat_id = product_service.create_category("Meds")
    p_id = product_service.create_product("Paracetamol", cat_id, "box", 100, 10, True)
    
    batches = [
        {"batch_number": "B1", "expiry_date": "2030-01-01", "quantity": 100, "unit_cost": 50},
        {"batch_number": "B2", "expiry_date": "2030-02-01", "quantity": 50, "unit_cost": 60}
    ]
    inventory_service.record_opening_stock_medicine(p_id, batches)
    
    rec = reconciliation_service.reconcile_medicine_batches(p_id)
    assert rec['stock_match'] is True
    assert rec['db_stock'] == 150
    assert rec['value_match'] is True
    assert rec['db_value'] == 8000 # 100*50 + 50*60
    assert len(rec['batch_discrepancies']) == 0

def test_wac_calculation(inventory_service):
    # Test integer rounding for WAC
    # 3 items cost 10 each, total 30. WAC = 10.
    val = inventory_service.calculate_wac_value_change(3, 30, 1)
    assert val == 10
    
    # 3 items cost 3.33.. each, total 10. 
    # deducting 1 item: 1 * (10/3) = 3.33 -> round to 3
    val2 = inventory_service.calculate_wac_value_change(3, 10, 1)
    assert val2 == 3
    
    # deducting ALL remaining 2 items. Should return exactly remaining value to prevent residue
    val3 = inventory_service.calculate_wac_value_change(2, 7, 2)
    assert val3 == 7

def test_rollback_on_partial_failure(product_service, inventory_service, db_manager):
    cat_id = product_service.create_category("Meds")
    p_id = product_service.create_product("Para", cat_id, "box", 100, 10, True)
    
    batches = [
        {"batch_number": "B1", "expiry_date": "2030-01-01", "quantity": 100, "unit_cost": 50},
        {"batch_number": "B2", "expiry_date": "2030-02-01", "quantity": -50, "unit_cost": 60} # Invalid quantity!
    ]
    
    with pytest.raises(ValueError, match="greater than zero"):
        inventory_service.record_opening_stock_medicine(p_id, batches)
        
    # Verify rollback: no batches should exist
    conn = db_manager.get_connection()
    count = conn.execute("SELECT COUNT(*) FROM medicine_batches WHERE product_id = ?", (p_id,)).fetchone()[0]
    assert count == 0
    # No movement logs
    mov_count = conn.execute("SELECT COUNT(*) FROM inventory_movements WHERE product_id = ?", (p_id,)).fetchone()[0]
    assert mov_count == 0

def test_reconciliation_detects_deliberate_inconsistency(product_service, inventory_service, reconciliation_service, db_manager):
    cat_id = product_service.create_category("Merch")
    p_id = product_service.create_product("Soap", cat_id, "pcs", 100, 10, False)
    
    inventory_service.record_opening_stock_general(p_id, 50, 40)
    
    # Deliberately mess up the product table directly bypassing triggers if possible
    with db_manager.transaction() as conn:
        conn.execute("UPDATE products SET current_stock = 999 WHERE id = ?", (p_id,))
    
    rec = reconciliation_service.reconcile_product_stock(p_id)
    assert rec['stock_match'] is False
    assert rec['db_stock'] == 999
    assert rec['calc_stock'] == 50

def test_sellable_medicine_batches(product_service, inventory_service):
    from datetime import datetime, timedelta
    cat_id = product_service.create_category("Meds")
    p_id = product_service.create_product("Med", cat_id, "box", 100, 10, True)
    
    today = datetime.now()
    tomorrow = (today + timedelta(days=1)).strftime("%Y-%m-%d")
    yesterday = (today - timedelta(days=1)).strftime("%Y-%m-%d")
    today_str = today.strftime("%Y-%m-%d")
    
    batches = [
        {"batch_number": "EXPIRED", "expiry_date": yesterday, "quantity": 10, "unit_cost": 50},
        {"batch_number": "TODAY", "expiry_date": today_str, "quantity": 10, "unit_cost": 50},
        {"batch_number": "UNKNOWN", "expiry_date": None, "quantity": 10, "unit_cost": 50},
        {"batch_number": "GOOD", "expiry_date": tomorrow, "quantity": 10, "unit_cost": 50}
    ]
    inventory_service.record_opening_stock_medicine(p_id, batches)
    
    sellable = inventory_service.get_sellable_medicine_batches(p_id)
    assert len(sellable) == 1
    assert sellable[0]['batch_number'] == "GOOD"
