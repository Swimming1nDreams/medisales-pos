class ReconciliationService:
    def __init__(self, db_manager):
        self.db = db_manager

    def reconcile_product_stock(self, product_id: int) -> dict:
        """Compares product current_stock against SUM of inventory_movements."""
        with self.db.transaction() as conn:
            prod = conn.execute("SELECT current_stock, inventory_value FROM products WHERE id = ?", (product_id,)).fetchone()
            if not prod:
                raise ValueError("Product not found.")
            
            mov = conn.execute('''
                SELECT SUM(CASE WHEN movement_type = 'In' THEN quantity_change ELSE -quantity_change END) as calc_qty,
                       SUM(CASE WHEN movement_type = 'In' THEN value_change ELSE -value_change END) as calc_val
                FROM inventory_movements WHERE product_id = ?
            ''', (product_id,)).fetchone()

            calc_qty = mov['calc_qty'] or 0
            calc_val = mov['calc_val'] or 0

            return {
                'product_id': product_id,
                'db_stock': prod['current_stock'],
                'calc_stock': calc_qty,
                'stock_match': prod['current_stock'] == calc_qty,
                'db_value': prod['inventory_value'],
                'calc_value': calc_val,
                'value_match': prod['inventory_value'] == calc_val
            }

    def reconcile_medicine_batches(self, product_id: int) -> dict:
        """Compares medicine product stock/value against the SUM of its batches, and batch qty against movements."""
        with self.db.transaction() as conn:
            prod = conn.execute("SELECT current_stock, inventory_value, is_medicine FROM products WHERE id = ?", (product_id,)).fetchone()
            if not prod or not prod['is_medicine']:
                raise ValueError("Medicine product not found.")
                
            batches = conn.execute("SELECT id, current_qty, unit_cost FROM medicine_batches WHERE product_id = ?", (product_id,)).fetchall()
            
            total_batch_qty = sum(b['current_qty'] for b in batches)
            total_batch_val = sum(b['current_qty'] * b['unit_cost'] for b in batches)
            
            batch_discrepancies = []
            for b in batches:
                mov = conn.execute('''
                    SELECT SUM(CASE WHEN movement_type = 'In' THEN quantity_change ELSE -quantity_change END) as calc_qty
                    FROM medicine_batch_movements WHERE batch_id = ?
                ''', (b['id'],)).fetchone()
                calc_qty = mov['calc_qty'] or 0
                if calc_qty != b['current_qty']:
                    batch_discrepancies.append({
                        'batch_id': b['id'],
                        'db_qty': b['current_qty'],
                        'calc_qty': calc_qty
                    })

            return {
                'product_id': product_id,
                'db_stock': prod['current_stock'],
                'batch_sum_qty': total_batch_qty,
                'stock_match': prod['current_stock'] == total_batch_qty,
                'db_value': prod['inventory_value'],
                'batch_sum_val': total_batch_val,
                'value_match': prod['inventory_value'] == total_batch_val,
                'batch_discrepancies': batch_discrepancies
            }

    def reconcile_purchase(self, purchase_id: int) -> dict:
        """Verifies purchase line quantities match actual inventory_movement logged for that purchase."""
        with self.db.transaction() as conn:
            purch = conn.execute("SELECT * FROM purchases WHERE id = ?", (purchase_id,)).fetchone()
            if not purch:
                raise ValueError("Purchase not found.")
                
            items = conn.execute("SELECT product_id, quantity FROM purchase_items WHERE purchase_id = ?", (purchase_id,)).fetchall()
            
            discrepancies = []
            for item in items:
                # Find movement for this purchase
                mov = conn.execute('''
                    SELECT quantity_change FROM inventory_movements 
                    WHERE reference_type = 'Purchase' AND reference_id = ? AND product_id = ?
                ''', (purchase_id, item['product_id'])).fetchone()
                
                # If voided, we might have multiple movements or we look at net movement.
                # Just checking net movement for the purchase
                net_mov = conn.execute('''
                    SELECT SUM(CASE WHEN movement_type = 'In' THEN quantity_change ELSE -quantity_change END) as net
                    FROM inventory_movements 
                    WHERE reference_type IN ('Purchase', 'PurchaseVoid') AND reference_id = ? AND product_id = ?
                ''', (purchase_id, item['product_id'])).fetchone()['net'] or 0

                expected = item['quantity'] if purch['status'] == 'Completed' else 0
                
                if net_mov != expected:
                    discrepancies.append({
                        'product_id': item['product_id'],
                        'expected_net': expected,
                        'actual_net': net_mov
                    })
                    
            return {
                'purchase_id': purchase_id,
                'status': purch['status'],
                'discrepancies': discrepancies,
                'is_consistent': len(discrepancies) == 0
            }

    def reconcile_supplier_payment(self, payment_id: int) -> dict:
        """Verifies payment allocated_amount matches sum of its allocations."""
        with self.db.transaction() as conn:
            pay = conn.execute("SELECT allocated_amount FROM supplier_payments WHERE id = ?", (payment_id,)).fetchone()
            if not pay:
                raise ValueError("Payment not found.")
                
            allocs = conn.execute("SELECT SUM(allocated_amount) as total FROM supplier_payment_allocations WHERE payment_id = ?", (payment_id,)).fetchone()
            sum_allocs = allocs['total'] or 0
            
            return {
                'payment_id': payment_id,
                'db_allocated': pay['allocated_amount'],
                'sum_allocations': sum_allocs,
                'is_consistent': pay['allocated_amount'] == sum_allocs
            }

    def reconcile_sale(self, sale_id: int) -> dict:
        """Verifies sale line quantities match actual inventory_movement logged for that sale."""
        with self.db.transaction() as conn:
            sale = conn.execute("SELECT * FROM sales WHERE id = ?", (sale_id,)).fetchone()
            if not sale:
                raise ValueError("Sale not found.")
                
            items = conn.execute("SELECT id, product_id, quantity, total_cost FROM sale_items WHERE sale_id = ?", (sale_id,)).fetchall()
            
            discrepancies = []
            for item in items:
                # Find net movement for this sale
                net_mov_qty = conn.execute('''
                    SELECT SUM(CASE WHEN movement_type = 'Out' THEN quantity_change ELSE -quantity_change END) as net
                    FROM inventory_movements 
                    WHERE reference_type IN ('Sale', 'SaleVoid') AND reference_id = ? AND product_id = ?
                ''', (sale_id, item['product_id'])).fetchone()['net'] or 0

                expected_qty = item['quantity'] if sale['status'] == 'Completed' else 0
                
                if net_mov_qty != expected_qty:
                    discrepancies.append({
                        'product_id': item['product_id'],
                        'expected_net_qty': expected_qty,
                        'actual_net_qty': net_mov_qty
                    })
                    
            return {
                'sale_id': sale_id,
                'status': sale['status'],
                'discrepancies': discrepancies,
                'is_consistent': len(discrepancies) == 0
            }

    def reconcile_finance_summary(self, start_date: str, end_date: str) -> dict:
        """Verifies finance summary consistency against underlying transaction lines."""
        with self.db.transaction() as conn:
            discrepancies = []
            
            # 1. Sales revenue versus sale-item totals & Gross profit
            sales = conn.execute('''
                SELECT s.id, s.total_amount, 
                       COALESCE(SUM(si.line_total), 0) as calc_amount,
                       COALESCE(SUM(si.total_cost), 0) as calc_cost
                FROM sales s
                LEFT JOIN sale_items si ON s.id = si.sale_id
                WHERE substr(s.date_time, 1, 10) >= ? AND substr(s.date_time, 1, 10) <= ?
                GROUP BY s.id
            ''', (start_date, end_date)).fetchall()
            
            for s in sales:
                if s['total_amount'] != s['calc_amount']:
                    discrepancies.append(f"Sale {s['id']} total_amount ({s['total_amount']}) != sum of line_totals ({s['calc_amount']})")
                    
            # 2. Supplier payment totals vs allocations
            payments = conn.execute('''
                SELECT p.id, p.total_amount, p.allocated_amount,
                       COALESCE(SUM(a.allocated_amount), 0) as calc_alloc
                FROM supplier_payments p
                LEFT JOIN supplier_payment_allocations a ON p.id = a.payment_id
                WHERE p.date >= ? AND p.date <= ?
                GROUP BY p.id
            ''', (start_date, end_date)).fetchall()
            
            for p in payments:
                if p['allocated_amount'] != p['calc_alloc']:
                    discrepancies.append(f"Payment {p['id']} allocated_amount ({p['allocated_amount']}) != sum of allocations ({p['calc_alloc']})")
                if p['calc_alloc'] > p['total_amount']:
                    discrepancies.append(f"Payment {p['id']} sum of allocations ({p['calc_alloc']}) > total_amount ({p['total_amount']})")

            # 3. Outstanding supplier balances (Purchases total_amount vs amount_paid + sum of active allocations)
            # amount_paid on purchase should exactly equal sum of allocations for that purchase.
            purchases = conn.execute('''
                SELECT p.id, p.total_amount, p.amount_paid,
                       COALESCE(SUM(a.allocated_amount), 0) as calc_paid
                FROM purchases p
                LEFT JOIN supplier_payment_allocations a ON p.id = a.purchase_id
                WHERE p.date >= ? AND p.date <= ?
                GROUP BY p.id
            ''', (start_date, end_date)).fetchall()

            for p in purchases:
                if p['amount_paid'] != p['calc_paid']:
                    discrepancies.append(f"Purchase {p['id']} amount_paid ({p['amount_paid']}) != sum of allocations ({p['calc_paid']})")
                if p['amount_paid'] > p['total_amount']:
                    discrepancies.append(f"Purchase {p['id']} amount_paid ({p['amount_paid']}) > total_amount ({p['total_amount']})")

            # 4. Expense amounts and expense correction/void history
            # (Just ensuring voided expenses are actually marked Voided and amounts are valid integers >= 0)
            expenses = conn.execute('''
                SELECT id, amount, status FROM expenses 
                WHERE date >= ? AND date <= ?
            ''', (start_date, end_date)).fetchall()
            
            for e in expenses:
                if e['amount'] < 0:
                    discrepancies.append(f"Expense {e['id']} has negative amount ({e['amount']})")
                if e['status'] not in ('Completed', 'Voided'):
                    discrepancies.append(f"Expense {e['id']} has invalid status ({e['status']})")

            return {
                'start_date': start_date,
                'end_date': end_date,
                'discrepancies': discrepancies,
                'is_consistent': len(discrepancies) == 0
            }

    def save_cash_reconciliation(self, recon_data: dict) -> dict:
        """Saves an end-of-day cash reconciliation record to database settings."""
        import json
        from datetime import date, datetime

        if not isinstance(recon_data, dict):
            raise ValueError("Reconciliation data must be a dictionary.")

        date_str = recon_data.get('date')
        if not date_str:
            date_str = date.today().isoformat()

        # Validate small change amount
        raw_small_change = recon_data.get('small_change_amount', 0)
        if raw_small_change is None or raw_small_change == '':
            small_change = 0
        else:
            try:
                small_change = int(raw_small_change)
            except (ValueError, TypeError):
                raise ValueError("Small change amount must be a non-negative whole number.")
        
        if small_change < 0:
            raise ValueError("Small change amount must be a non-negative whole number.")

        # Validate banknote denominations
        denoms = recon_data.get('denominations', {})
        cleaned_denoms = {}
        banknotes_total = 0
        if isinstance(denoms, dict):
            for k, v in denoms.items():
                try:
                    d_val = int(k)
                    c_val = int(v) if (v is not None and v != '') else 0
                except (ValueError, TypeError):
                    continue
                if c_val < 0:
                    raise ValueError(f"Denomination count for {k} cannot be negative.")
                cleaned_denoms[str(d_val)] = c_val
                banknotes_total += d_val * c_val

        total_counted = banknotes_total + small_change

        try:
            expected_sales = int(recon_data.get('expected_sales', 0))
        except (ValueError, TypeError):
            expected_sales = 0

        variance = total_counted - expected_sales

        record = {
            'date': str(date_str),
            'denominations': cleaned_denoms,
            'small_change_amount': small_change,
            'total_counted': total_counted,
            'expected_sales': expected_sales,
            'variance': variance,
            'saved_at': recon_data.get('saved_at', datetime.now().isoformat())
        }

        payload = json.dumps(record)
        key_date = f"cash_reconciliation:{date_str}"
        key_latest = "cash_reconciliation:latest"

        with self.db.transaction() as conn:
            conn.execute("""
                INSERT INTO settings (key, value) VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """, (key_date, payload))
            conn.execute("""
                INSERT INTO settings (key, value) VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """, (key_latest, payload))

        return record

    def get_cash_reconciliation(self, date_str: str = None) -> dict | None:
        """Retrieves a saved cash reconciliation record by date or latest."""
        import json
        conn = self.db.get_connection()
        if date_str:
            key = f"cash_reconciliation:{date_str}"
            row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
            if row and row['value']:
                return json.loads(row['value'])
        
        row = conn.execute("SELECT value FROM settings WHERE key = 'cash_reconciliation:latest'").fetchone()
        if row and row['value']:
            return json.loads(row['value'])
        return None

