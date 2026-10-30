from datetime import datetime
from typing import List, Dict, Any
import sqlite3

class InventoryService:
    def __init__(self, db_manager):
        self.db = db_manager

    def _ensure_integer(self, val: Any) -> int:
        if isinstance(val, float) and not val.is_integer():
            raise ValueError("Fractional Kyat amounts are not permitted.")
        return int(val)

    def record_opening_stock_general(self, product_id: int, quantity: int, unit_cost: int):
        quantity = self._ensure_integer(quantity)
        unit_cost = self._ensure_integer(unit_cost)
        if quantity <= 0:
            raise ValueError("Quantity must be greater than zero.")
        if unit_cost < 0:
            raise ValueError("Unit cost cannot be negative.")

        with self.db.transaction() as conn:
            # Prevent duplicate opening stock
            self._verify_no_opening_stock(conn, product_id)

            prod = conn.execute("SELECT is_medicine FROM products WHERE id = ?", (product_id,)).fetchone()
            if not prod:
                raise ValueError("Product not found.")
            if prod['is_medicine']:
                raise ValueError("Cannot use general opening stock for medicines.")

            # Record Opening Stock Operation
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            conn.execute(
                "INSERT INTO opening_stock_operations (product_id, date_time) VALUES (?, ?)",
                (product_id, now)
            )
            op_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

            total_cost = quantity * unit_cost

            # Update product
            conn.execute('''
                UPDATE products 
                SET current_stock = current_stock + ?, 
                    inventory_value = inventory_value + ?
                WHERE id = ?
            ''', (quantity, total_cost, product_id))

            # Audit log
            conn.execute('''
                INSERT INTO inventory_movements 
                (product_id, quantity_change, value_change, movement_type, reference_type, reference_id, date_time)
                VALUES (?, ?, ?, 'In', 'OpeningStock', ?, ?)
            ''', (product_id, quantity, total_cost, op_id, now))

    def record_opening_stock_medicine(self, product_id: int, batches: List[Dict[str, Any]]):
        if not batches:
            raise ValueError("At least one batch is required for medicine opening stock.")

        with self.db.transaction() as conn:
            # Prevent duplicate
            self._verify_no_opening_stock(conn, product_id)

            prod = conn.execute("SELECT is_medicine FROM products WHERE id = ?", (product_id,)).fetchone()
            if not prod:
                raise ValueError("Product not found.")
            if not prod['is_medicine']:
                raise ValueError("Cannot use medicine opening stock for general merchandise.")

            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            conn.execute(
                "INSERT INTO opening_stock_operations (product_id, date_time) VALUES (?, ?)",
                (product_id, now)
            )
            op_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

            total_qty = 0
            total_value = 0

            for batch in batches:
                qty = self._ensure_integer(batch.get('quantity', 0))
                cost = self._ensure_integer(batch.get('unit_cost', 0))
                batch_no = batch.get('batch_number')
                expiry = batch.get('expiry_date') # YYYY-MM-DD or None

                if qty <= 0:
                    raise ValueError("Batch quantity must be greater than zero.")
                if cost < 0:
                    raise ValueError("Batch cost cannot be negative.")

                # Insert batch (purchase_item_id is NULL for opening stock)
                conn.execute('''
                    INSERT INTO medicine_batches 
                    (product_id, purchase_item_id, batch_number, expiry_date, initial_qty, current_qty, unit_cost)
                    VALUES (?, NULL, ?, ?, ?, ?, ?)
                ''', (product_id, batch_no, expiry, qty, qty, cost))
                batch_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

                # Batch movement log
                conn.execute('''
                    INSERT INTO medicine_batch_movements 
                    (batch_id, quantity_change, movement_type, reference_type, reference_id, date_time)
                    VALUES (?, ?, 'In', 'OpeningStock', ?, ?)
                ''', (batch_id, qty, op_id, now))

                total_qty += qty
                total_value += (qty * cost)

            # Update product stock (for medicines, inventory_value tracks movement value sync for reconciliation, 
            # though true authoritative value is sum of batches)
            conn.execute('''
                UPDATE products 
                SET current_stock = current_stock + ?,
                    inventory_value = inventory_value + ?
                WHERE id = ?
            ''', (total_qty, total_value, product_id))

            # Product movement log
            conn.execute('''
                INSERT INTO inventory_movements 
                (product_id, quantity_change, value_change, movement_type, reference_type, reference_id, date_time)
                VALUES (?, ?, ?, 'In', 'OpeningStock', ?, ?)
            ''', (product_id, total_qty, total_value, op_id, now))

    def _verify_no_opening_stock(self, conn, product_id: int):
        existing = conn.execute("SELECT 1 FROM opening_stock_operations WHERE product_id = ?", (product_id,)).fetchone()
        if existing:
            raise ValueError("Opening stock already recorded for this product.")

    def calculate_wac_value_change(self, current_stock: int, inventory_value: int, qty_deducted: int) -> int:
        """
        Calculates the integer-rounded value change for a given quantity deduction using WAC.
        If current_stock == qty_deducted, returns the exact remaining inventory_value to prevent rounding residue.
        """
        if qty_deducted == current_stock:
            return inventory_value
        if current_stock == 0:
            return 0
        wac = inventory_value / current_stock
        return round(qty_deducted * wac)

    def get_sellable_medicine_batches(self, product_id: int) -> List[Dict[str, Any]]:
        """
        Returns batches eligible for sale (FEFO).
        Excludes batches with unknown, expired, or today's expiry dates.
        """
        today = datetime.now().strftime("%Y-%m-%d")
        conn = self.db.get_connection()
        query = '''
            SELECT * FROM medicine_batches 
            WHERE product_id = ? 
              AND current_qty > 0 
              AND expiry_date IS NOT NULL 
              AND expiry_date != ''
              AND expiry_date > ?
            ORDER BY expiry_date ASC
        '''
        return [dict(row) for row in conn.execute(query, (product_id, today)).fetchall()]
