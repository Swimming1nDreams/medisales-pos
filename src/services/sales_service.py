from datetime import datetime
import sqlite3
from typing import List, Dict, Any, Optional

class SalesService:
    def __init__(self, db_manager, inventory_service):
        self.db = db_manager
        self.inventory_service = inventory_service

    def _ensure_integer(self, val: Any) -> int:
        if isinstance(val, float) and not val.is_integer():
            raise ValueError("Fractional Kyat amounts are not permitted.")
        return int(val)

    def create_sale(
        self, 
        reference: str, 
        items: List[Dict[str, Any]], 
        amount_received: int,
        discount_amount: int = 0,
        payment_type: str = 'cash',
        customer_id: Any = None,
        date_time: Optional[str] = None
    ) -> int:
        reference = reference.strip()
        if not reference:
            raise ValueError("Sale reference is required.")
        if not items:
            raise ValueError("Sale must contain at least one item.")
            
        amount_received = self._ensure_integer(amount_received)
        if amount_received < 0:
            raise ValueError("Amount received cannot be negative.")

        discount_amount = self._ensure_integer(discount_amount)
        if discount_amount < 0:
            raise ValueError("Discount amount cannot be negative.")

        if payment_type not in ('cash', 'credit'):
            raise ValueError("Payment type must be 'cash' or 'credit'.")

        with self.db.transaction() as conn:
            # First pass: calculate subtotal amount and validate basic structure
            subtotal = 0
            for item in items:
                qty = self._ensure_integer(item['quantity'])
                price = self._ensure_integer(item['unit_price'])
                if qty <= 0:
                    raise ValueError("Sale quantity must be greater than zero.")
                if price < 0:
                    raise ValueError("Unit price cannot be negative.")
                subtotal += (qty * price)

            if discount_amount > subtotal:
                raise ValueError("Discount cannot exceed sale subtotal.")

            total_amount = subtotal - discount_amount

            if payment_type == 'cash':
                if amount_received < total_amount:
                    raise ValueError("Amount received is less than total sale amount.")
                change_given = amount_received - total_amount
                credit_amount = 0
                cid = customer_id
            else:  # credit
                if not customer_id:
                    raise ValueError("A customer must be selected to record a credit sale.")
                cust = conn.execute("SELECT id, is_active FROM customers WHERE id = ?", (customer_id,)).fetchone()
                if not cust or not cust['is_active']:
                    raise ValueError(f"Customer #{customer_id} does not exist or is inactive.")
                
                cid = customer_id
                # In credit sales: amount_received is upfront cash payment (if any)
                if amount_received >= total_amount:
                    change_given = amount_received - total_amount
                    credit_amount = 0
                else:
                    change_given = 0
                    credit_amount = total_amount - amount_received

            now = str(date_time).strip() if date_time else datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            try:
                s_cursor = conn.execute(
                    """INSERT INTO sales 
                    (reference, date_time, subtotal, discount_amount, total_amount, amount_received, change_given, payment_type, customer_id, credit_amount, status) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Completed')""",
                    (reference, now, subtotal, discount_amount, total_amount, amount_received, change_given, payment_type, cid, credit_amount)
                )
                sale_id = s_cursor.lastrowid
            except sqlite3.IntegrityError as e:
                if 'UNIQUE' in str(e):
                    raise ValueError(f"Sale reference '{reference}' already exists.")
                raise

            for item in items:
                prod_id = item['product_id']
                req_qty = self._ensure_integer(item['quantity'])
                price = self._ensure_integer(item['unit_price'])
                line_total = req_qty * price

                pkg_unit = (item.get('packaging_unit') or '').strip() or None
                pkg_factor = self._ensure_integer(item.get('packaging_factor', 1))
                if pkg_factor < 1:
                    pkg_factor = 1
                base_qty = req_qty * pkg_factor

                prod = conn.execute("SELECT is_medicine, is_active, current_stock, inventory_value FROM products WHERE id = ?", (prod_id,)).fetchone()
                if not prod:
                    raise ValueError(f"Product {prod_id} not found.")
                if not prod['is_active']:
                    raise ValueError(f"Product {prod_id} is inactive and cannot be sold.")
                if prod['current_stock'] < base_qty:
                    unit_desc = f"{pkg_unit} ({base_qty} base units)" if pkg_unit else f"units"
                    raise ValueError(f"Insufficient stock for product {prod_id}. Requested {req_qty} {unit_desc}, but only {prod['current_stock']} available.")

                item_total_cost = 0

                if prod['is_medicine']:
                    batches = self.inventory_service.get_sellable_medicine_batches(prod_id)
                    total_available = sum(b['current_qty'] for b in batches)
                    if total_available < base_qty:
                        raise ValueError(f"Insufficient eligible batch stock for medicine product {prod_id}.")

                    # Insert sale item first to get ID for sale_item_batches
                    # quantity stores base_qty for exact inventory integrity and void restoration
                    si_cursor = conn.execute(
                        "INSERT INTO sale_items (sale_id, product_id, quantity, unit_price, total_cost, line_total, packaging_unit, packaging_factor) VALUES (?, ?, ?, ?, 0, ?, ?, ?)",
                        (sale_id, prod_id, base_qty, price, line_total, pkg_unit, pkg_factor)
                    )
                    sale_item_id = si_cursor.lastrowid

                    rem_qty = base_qty
                    for batch in batches:
                        if rem_qty <= 0:
                            break
                        deduct = min(rem_qty, batch['current_qty'])
                        batch_cost_deduction = deduct * batch['unit_cost']
                        item_total_cost += batch_cost_deduction

                        # Update batch
                        conn.execute("UPDATE medicine_batches SET current_qty = current_qty - ? WHERE id = ?", (deduct, batch['id']))
                        # Log batch movement
                        conn.execute('''
                            INSERT INTO medicine_batch_movements 
                            (batch_id, quantity_change, movement_type, reference_type, reference_id, date_time)
                            VALUES (?, ?, 'Out', 'Sale', ?, ?)
                        ''', (batch['id'], deduct, sale_id, now))
                        # Link batch to sale item
                        conn.execute('''
                            INSERT INTO sale_item_batches (sale_item_id, batch_id, quantity_deducted)
                            VALUES (?, ?, ?)
                        ''', (sale_item_id, batch['id'], deduct))

                        rem_qty -= deduct

                    # Update total_cost on sale_item
                    conn.execute("UPDATE sale_items SET total_cost = ? WHERE id = ?", (item_total_cost, sale_item_id))

                else:
                    item_total_cost = self.inventory_service.calculate_wac_value_change(prod['current_stock'], prod['inventory_value'], base_qty)
                    
                    conn.execute(
                        "INSERT INTO sale_items (sale_id, product_id, quantity, unit_price, total_cost, line_total, packaging_unit, packaging_factor) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                        (sale_id, prod_id, base_qty, price, item_total_cost, line_total, pkg_unit, pkg_factor)
                    )

                # Update product stock & value
                conn.execute('''
                    UPDATE products 
                    SET current_stock = current_stock - ?, inventory_value = inventory_value - ?
                    WHERE id = ?
                ''', (base_qty, item_total_cost, prod_id))

                # Log inventory movement
                conn.execute('''
                    INSERT INTO inventory_movements 
                    (product_id, quantity_change, value_change, movement_type, reference_type, reference_id, date_time)
                    VALUES (?, ?, ?, 'Out', 'Sale', ?, ?)
                ''', (prod_id, base_qty, item_total_cost, sale_id, now))

            return sale_id

    def get_sale(self, sale_id: int) -> Dict[str, Any]:
        conn = self.db.get_connection()
        sale = conn.execute("SELECT * FROM sales WHERE id = ?", (sale_id,)).fetchone()
        if not sale:
            return None
            
        sale_dict = dict(sale)
        items = conn.execute("SELECT * FROM sale_items WHERE sale_id = ?", (sale_id,)).fetchall()
        sale_dict['items'] = [dict(item) for item in items]
        return sale_dict

    def void_sale(self, sale_id: int):
        """
        Safely reverses a sale, returning stock and value exactly as it was.
        """
        with self.db.transaction() as conn:
            sale = conn.execute("SELECT status FROM sales WHERE id = ?", (sale_id,)).fetchone()
            if not sale:
                raise ValueError("Sale not found.")
            if sale['status'] == 'Voided':
                raise ValueError("Sale is already voided.")

            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            items = conn.execute("SELECT * FROM sale_items WHERE sale_id = ?", (sale_id,)).fetchall()
            for item in items:
                prod = conn.execute("SELECT is_medicine FROM products WHERE id = ?", (item['product_id'],)).fetchone()
                
                if prod['is_medicine']:
                    batches = conn.execute("SELECT batch_id, quantity_deducted FROM sale_item_batches WHERE sale_item_id = ?", (item['id'],)).fetchall()
                    for batch_info in batches:
                        b_id = batch_info['batch_id']
                        b_qty = batch_info['quantity_deducted']
                        
                        conn.execute("UPDATE medicine_batches SET current_qty = current_qty + ? WHERE id = ?", (b_qty, b_id))
                        
                        conn.execute('''
                            INSERT INTO medicine_batch_movements 
                            (batch_id, quantity_change, movement_type, reference_type, reference_id, date_time)
                            VALUES (?, ?, 'In', 'SaleVoid', ?, ?)
                        ''', (b_id, b_qty, sale_id, now))

                # Reverse product stock exactly matching the item's total_cost (WAC snapshot or precise batch sum)
                conn.execute('''
                    UPDATE products 
                    SET current_stock = current_stock + ?, inventory_value = inventory_value + ?
                    WHERE id = ?
                ''', (item['quantity'], item['total_cost'], item['product_id']))

                conn.execute('''
                    INSERT INTO inventory_movements 
                    (product_id, quantity_change, value_change, movement_type, reference_type, reference_id, date_time)
                    VALUES (?, ?, ?, 'In', 'SaleVoid', ?, ?)
                ''', (item['product_id'], item['quantity'], item['total_cost'], sale_id, now))

            conn.execute("UPDATE sales SET status = 'Voided' WHERE id = ?", (sale_id,))
