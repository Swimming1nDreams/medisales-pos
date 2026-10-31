from datetime import datetime
import sqlite3
from typing import List, Dict, Any

class PurchaseService:
    def __init__(self, db_manager):
        self.db = db_manager

    def _ensure_integer(self, val: Any) -> int:
        if isinstance(val, float) and not val.is_integer():
            raise ValueError("Fractional Kyat amounts are not permitted.")
        return int(val)

    def create_purchase(self, reference: str, supplier_id: int, date: str, items: List[Dict[str, Any]]) -> int:
        reference = reference.strip()
        if not reference:
            raise ValueError("Purchase reference is required.")
        if not items:
            raise ValueError("Purchase must contain at least one item.")
            
        with self.db.transaction() as conn:
            # Check supplier
            supp = conn.execute("SELECT is_active FROM suppliers WHERE id = ?", (supplier_id,)).fetchone()
            if not supp:
                raise ValueError("Invalid supplier.")
            if not supp['is_active']:
                raise ValueError("Cannot create purchase for deactivated supplier.")

            # First pass: validate items and compute total amount
            total_amount = 0
            for item in items:
                qty = self._ensure_integer(item['quantity'])
                cost = self._ensure_integer(item['unit_cost'])
                if qty <= 0:
                    raise ValueError("Quantity must be greater than zero.")
                if cost < 0:
                    raise ValueError("Unit cost cannot be negative.")
                total_amount += (qty * cost)
            
            try:
                cursor = conn.execute(
                    "INSERT INTO purchases (reference, supplier_id, date, total_amount, amount_paid, status) VALUES (?, ?, ?, ?, 0, 'Completed')",
                    (reference, supplier_id, date, total_amount)
                )
                purchase_id = cursor.lastrowid
            except sqlite3.IntegrityError as e:
                if 'UNIQUE' in str(e):
                    raise ValueError(f"Purchase reference '{reference}' already exists.")
                raise

            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            prod_movements = {} # prod_id -> (total_qty, total_val)

            for item in items:
                prod_id = item['product_id']
                qty = self._ensure_integer(item['quantity'])
                cost = self._ensure_integer(item['unit_cost'])
                
                if qty <= 0:
                    raise ValueError("Quantity must be greater than zero.")
                if cost < 0:
                    raise ValueError("Unit cost cannot be negative.")
                    
                line_total = qty * cost

                pkg_unit = (item.get('packaging_unit') or '').strip() or None
                pkg_factor = self._ensure_integer(item.get('packaging_factor', 1))
                if pkg_factor < 1:
                    pkg_factor = 1

                base_qty = qty * pkg_factor
                base_cost = line_total // base_qty if base_qty > 0 else cost

                prod = conn.execute("SELECT is_medicine FROM products WHERE id = ?", (prod_id,)).fetchone()
                if not prod:
                    raise ValueError(f"Product {prod_id} not found.")

                # Insert purchase item (stores base_qty for inventory balance, plus packaging metadata)
                pi_cursor = conn.execute(
                    "INSERT INTO purchase_items (purchase_id, product_id, quantity, unit_cost, line_total, packaging_unit, packaging_factor) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (purchase_id, prod_id, base_qty, base_cost, line_total, pkg_unit, pkg_factor)
                )
                pi_id = pi_cursor.lastrowid

                # Update stock
                conn.execute('''
                    UPDATE products 
                    SET current_stock = current_stock + ?, inventory_value = inventory_value + ?
                    WHERE id = ?
                ''', (base_qty, line_total, prod_id))

                if prod_id not in prod_movements:
                    prod_movements[prod_id] = {'qty': 0, 'value': 0}
                prod_movements[prod_id]['qty'] += base_qty
                prod_movements[prod_id]['value'] += line_total

                if prod['is_medicine']:
                    # Requires batch information
                    batch_no = item.get('batch_number')
                    expiry = item.get('expiry_date')
                    if not batch_no:
                        raise ValueError("Medicine purchase items must include a batch_number.")
                        
                    batch_cursor = conn.execute('''
                        INSERT INTO medicine_batches 
                        (product_id, purchase_item_id, batch_number, expiry_date, initial_qty, current_qty, unit_cost)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (prod_id, pi_id, batch_no, expiry, base_qty, base_qty, base_cost))
                    batch_id = batch_cursor.lastrowid

                    conn.execute('''
                        INSERT INTO medicine_batch_movements 
                        (batch_id, quantity_change, movement_type, reference_type, reference_id, date_time)
                        VALUES (?, ?, 'In', 'Purchase', ?, ?)
                    ''', (batch_id, base_qty, purchase_id, now))

            # Record inventory movement once per distinct product for this purchase
            for p_id, mov in prod_movements.items():
                conn.execute('''
                    INSERT INTO inventory_movements 
                    (product_id, quantity_change, value_change, movement_type, reference_type, reference_id, date_time)
                    VALUES (?, ?, ?, 'In', 'Purchase', ?, ?)
                ''', (p_id, mov['qty'], mov['value'], purchase_id, now))

            return purchase_id

    def record_payment(self, reference: str, supplier_id: int, date: str, total_amount: int, allocations: List[Dict[str, Any]], notes: str = None) -> int:
        reference = reference.strip()
        total_amount = self._ensure_integer(total_amount)
        if total_amount <= 0:
            raise ValueError("Payment amount must be greater than zero.")
            
        with self.db.transaction() as conn:
            supp = conn.execute("SELECT is_active FROM suppliers WHERE id = ?", (supplier_id,)).fetchone()
            if not supp:
                raise ValueError("Invalid supplier.")
                
            # First pass: validate all allocation amounts and verify total
            total_allocated = 0
            for alloc in allocations:
                alloc_amt = self._ensure_integer(alloc['allocated_amount'])
                if alloc_amt <= 0:
                    raise ValueError("Allocation amount must be greater than zero.")
                total_allocated += alloc_amt

            if total_allocated > total_amount:
                raise ValueError("Total allocated amount cannot exceed the payment total amount.")

            try:
                p_cursor = conn.execute(
                    "INSERT INTO supplier_payments (reference, supplier_id, date, total_amount, allocated_amount, notes) VALUES (?, ?, ?, ?, 0, ?)",
                    (reference, supplier_id, date, total_amount, notes)
                )
                payment_id = p_cursor.lastrowid
            except sqlite3.IntegrityError:
                raise ValueError(f"Payment reference '{reference}' already exists.")

            for alloc in allocations:
                purch_id = alloc['purchase_id']
                alloc_amt = self._ensure_integer(alloc['allocated_amount'])

                # Check purchase
                purch = conn.execute("SELECT supplier_id, total_amount, amount_paid FROM purchases WHERE id = ?", (purch_id,)).fetchone()
                if not purch:
                    raise ValueError(f"Purchase {purch_id} not found.")
                if purch['supplier_id'] != supplier_id:
                    raise ValueError("Cannot allocate payment to a purchase from a different supplier.")
                
                outstanding = purch['total_amount'] - purch['amount_paid']
                if alloc_amt > outstanding:
                    raise ValueError(f"Allocation amount ({alloc_amt}) exceeds outstanding balance ({outstanding}) for purchase {purch_id}.")

                conn.execute(
                    "INSERT INTO supplier_payment_allocations (payment_id, purchase_id, allocated_amount) VALUES (?, ?, ?)",
                    (payment_id, purch_id, alloc_amt)
                )

            return payment_id

    def void_purchase_correction(self, purchase_id: int):
        """
        Safely reverses a purchase by explicit negative stock movements, avoiding deletion.
        """
        with self.db.transaction() as conn:
            purch = conn.execute("SELECT status, amount_paid FROM purchases WHERE id = ?", (purchase_id,)).fetchone()
            if not purch:
                raise ValueError("Purchase not found.")
            if purch['status'] == 'Voided':
                raise ValueError("Purchase is already voided.")
            if purch['amount_paid'] > 0:
                raise ValueError("Cannot void a purchase with existing payment allocations. Remove allocations first.")

            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Check if all stock is still available (for medicines, specific batches must still have full current_qty)
            # For general merch, current_stock must be >= purchase quantity
            items = conn.execute("SELECT * FROM purchase_items WHERE purchase_id = ?", (purchase_id,)).fetchall()
            for item in items:
                prod = conn.execute("SELECT is_medicine, current_stock, inventory_value FROM products WHERE id = ?", (item['product_id'],)).fetchone()
                if prod['current_stock'] < item['quantity']:
                    raise ValueError(f"Insufficient stock to void purchase. Product {item['product_id']} has already been sold.")

                if prod['is_medicine']:
                    # Check specific batch
                    batch = conn.execute("SELECT id, current_qty FROM medicine_batches WHERE purchase_item_id = ?", (item['id'],)).fetchone()
                    if not batch or batch['current_qty'] < item['quantity']:
                        raise ValueError("Medicine batch from this purchase has already been deducted. Cannot void.")
                        
                    # Reverse batch stock
                    conn.execute("UPDATE medicine_batches SET current_qty = current_qty - ? WHERE id = ?", (item['quantity'], batch['id']))
                    conn.execute('''
                        INSERT INTO medicine_batch_movements 
                        (batch_id, quantity_change, movement_type, reference_type, reference_id, date_time)
                        VALUES (?, ?, 'Out', 'PurchaseVoid', ?, ?)
                    ''', (batch['id'], item['quantity'], purchase_id, now))

            # Aggregate reversal per distinct product
            prod_void_movements = {}
            for item in items:
                pid = item['product_id']
                if pid not in prod_void_movements:
                    prod_void_movements[pid] = {'qty': 0, 'value': 0}
                prod_void_movements[pid]['qty'] += item['quantity']
                prod_void_movements[pid]['value'] += item['line_total']

            for pid, mov in prod_void_movements.items():
                conn.execute('''
                    UPDATE products 
                    SET current_stock = current_stock - ?, inventory_value = inventory_value - ?
                    WHERE id = ?
                ''', (mov['qty'], mov['value'], pid))

                conn.execute('''
                    INSERT INTO inventory_movements 
                    (product_id, quantity_change, value_change, movement_type, reference_type, reference_id, date_time)
                    VALUES (?, ?, ?, 'Out', 'PurchaseVoid', ?, ?)
                ''', (pid, mov['qty'], mov['value'], purchase_id, now))

            # Mark voided
            conn.execute("UPDATE purchases SET status = 'Voided' WHERE id = ?", (purchase_id,))
