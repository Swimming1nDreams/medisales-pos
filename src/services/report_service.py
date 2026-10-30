from datetime import datetime, timedelta
from typing import List, Dict, Any

class ReportService:
    def __init__(self, db_manager):
        self.db = db_manager

    # --- Sales Reports ---
    
    def get_sales_summary(self, start_date: str, end_date: str) -> Dict[str, Any]:
        conn = self.db.get_connection()
        row = conn.execute('''
            SELECT 
                COUNT(DISTINCT s.id) as sales_count,
                COALESCE(SUM(si.line_total), 0) as total_revenue,
                SUM(si.total_cost) as total_cogs
            FROM sales s
            LEFT JOIN sale_items si ON s.id = si.sale_id
            WHERE s.status = 'Completed'
              AND substr(s.date_time, 1, 10) >= ?
              AND substr(s.date_time, 1, 10) <= ?
        ''', (start_date, end_date)).fetchone()
        
        rev = row['total_revenue'] or 0
        cogs = row['total_cogs'] or 0
        
        return {
            "sales_count": row['sales_count'],
            "total_revenue": rev,
            "revenue": rev,
            "total_cogs": cogs,
            "cogs": cogs,
            "gross_profit": rev - cogs
        }

    def get_daily_sales_totals(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        conn = self.db.get_connection()
        rows = conn.execute('''
            SELECT 
                substr(date_time, 1, 10) as sale_date,
                COUNT(id) as sales_count,
                SUM(total_amount) as total_revenue
            FROM sales
            WHERE status = 'Completed'
              AND substr(date_time, 1, 10) >= ?
              AND substr(date_time, 1, 10) <= ?
            GROUP BY substr(date_time, 1, 10)
            ORDER BY sale_date
        ''', (start_date, end_date)).fetchall()
        return [dict(row) for row in rows]

    def get_sales_by_product(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        conn = self.db.get_connection()
        rows = conn.execute('''
            SELECT 
                p.id as product_id,
                p.name as product_name,
                SUM(si.quantity) as total_quantity,
                SUM(si.line_total) as total_revenue,
                SUM(si.total_cost) as total_cogs
            FROM sale_items si
            JOIN sales s ON s.id = si.sale_id
            JOIN products p ON p.id = si.product_id
            WHERE s.status = 'Completed'
              AND substr(s.date_time, 1, 10) >= ?
              AND substr(s.date_time, 1, 10) <= ?
            GROUP BY p.id, p.name
            ORDER BY total_revenue DESC
        ''', (start_date, end_date)).fetchall()
        
        result = []
        for r in rows:
            d = dict(r)
            d['gross_profit'] = (d['total_revenue'] or 0) - (d['total_cogs'] or 0)
            d['quantity_sold'] = d.get('total_quantity', 0)
            d['revenue'] = d.get('total_revenue', 0)
            d['cogs'] = d.get('total_cogs', 0)
            result.append(d)
        return result

    def get_sales_by_category(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        conn = self.db.get_connection()
        rows = conn.execute('''
            SELECT 
                c.name as category_name,
                SUM(si.quantity) as total_quantity,
                SUM(si.line_total) as total_revenue,
                SUM(si.total_cost) as total_cogs
            FROM sale_items si
            JOIN sales s ON s.id = si.sale_id
            JOIN products p ON p.id = si.product_id
            JOIN categories c ON c.id = p.category_id
            WHERE s.status = 'Completed'
              AND substr(s.date_time, 1, 10) >= ?
              AND substr(s.date_time, 1, 10) <= ?
            GROUP BY c.id, c.name
            ORDER BY total_revenue DESC
        ''', (start_date, end_date)).fetchall()
        
        result = []
        for r in rows:
            d = dict(r)
            d['gross_profit'] = (d['total_revenue'] or 0) - (d['total_cogs'] or 0)
            d['revenue'] = d.get('total_revenue', 0)
            d['cogs'] = d.get('total_cogs', 0)
            result.append(d)
        return result

    # --- Inventory Reports ---
    
    def get_current_stock(self) -> List[Dict[str, Any]]:
        conn = self.db.get_connection()
        return [dict(row) for row in conn.execute('''
            SELECT p.id, p.name, p.unit_measure, p.current_stock, p.inventory_value, p.min_stock_level, p.is_medicine,
                   c.name as category_name
            FROM products p
            LEFT JOIN categories c ON c.id = p.category_id
            WHERE p.is_active = 1
            ORDER BY p.name
        ''').fetchall()]

    def get_medicine_batches_report(self, filter_type: str = 'all', days: int = 30) -> List[Dict[str, Any]]:
        today = datetime.now().strftime("%Y-%m-%d")
        conn = self.db.get_connection()
        
        query = '''
            SELECT mb.*, p.name as product_name
            FROM medicine_batches mb
            JOIN products p ON p.id = mb.product_id
            WHERE mb.current_qty > 0
        '''
        
        if filter_type == 'expired':
            query += " AND mb.expiry_date != '' AND mb.expiry_date <= ?"
            params = (today,)
        elif filter_type == 'expiring_soon':
            soon_date = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
            query += " AND mb.expiry_date != '' AND mb.expiry_date > ? AND mb.expiry_date <= ?"
            params = (today, soon_date)
        elif filter_type == 'unknown_expiry':
            query += " AND (mb.expiry_date IS NULL OR mb.expiry_date = '')"
            params = ()
        else:
            params = ()
            
        rows = [dict(row) for row in conn.execute(query, params).fetchall()]
        for r in rows:
            r['remaining_quantity'] = r.get('current_qty', 0)
        return rows

    def get_low_stock_products(self) -> List[Dict[str, Any]]:
        conn = self.db.get_connection()
        return [dict(row) for row in conn.execute('''
            SELECT id, name, current_stock, min_stock_level
            FROM products
            WHERE is_active = 1 AND current_stock <= min_stock_level
            ORDER BY current_stock ASC
        ''').fetchall()]

    def get_inventory_movement_history(self, product_id: int, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        conn = self.db.get_connection()
        return [dict(row) for row in conn.execute('''
            SELECT * FROM inventory_movements
            WHERE product_id = ?
              AND substr(date_time, 1, 10) >= ?
              AND substr(date_time, 1, 10) <= ?
            ORDER BY date_time DESC, id DESC
        ''', (product_id, start_date, end_date)).fetchall()]

    # --- Purchase and Supplier Reports ---
    
    def get_purchases(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        conn = self.db.get_connection()
        return [dict(row) for row in conn.execute('''
            SELECT p.*, s.name as supplier_name
            FROM purchases p
            JOIN suppliers s ON s.id = p.supplier_id
            WHERE p.date >= ? AND p.date <= ?
            ORDER BY p.date DESC, p.id DESC
        ''', (start_date, end_date)).fetchall()]
        
    def get_daily_purchase_totals(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        conn = self.db.get_connection()
        return [dict(row) for row in conn.execute('''
            SELECT date, COUNT(id) as purchase_count, SUM(total_amount) as total_amount
            FROM purchases
            WHERE status = 'Completed' AND date >= ? AND date <= ?
            GROUP BY date
            ORDER BY date
        ''', (start_date, end_date)).fetchall()]

    def get_supplier_balances(self) -> List[Dict[str, Any]]:
        conn = self.db.get_connection()
        return [dict(row) for row in conn.execute('''
            SELECT 
                s.id as supplier_id,
                s.name as supplier_name,
                COALESCE(SUM(p.total_amount), 0) as total_purchased,
                COALESCE(SUM(p.amount_paid), 0) as total_paid,
                COALESCE(SUM(p.total_amount - p.amount_paid), 0) as outstanding_balance
            FROM suppliers s
            LEFT JOIN purchases p ON s.id = p.supplier_id AND p.status = 'Completed'
            GROUP BY s.id, s.name
            HAVING outstanding_balance > 0
            ORDER BY outstanding_balance DESC
        ''').fetchall()]

    def get_supplier_payment_balances(self) -> List[Dict[str, Any]]:
        conn = self.db.get_connection()
        return [dict(row) for row in conn.execute('''
            SELECT 
                id as payment_id,
                date,
                supplier_id,
                total_amount,
                allocated_amount,
                (total_amount - allocated_amount) as unallocated_balance
            FROM supplier_payments
            WHERE total_amount > allocated_amount
            ORDER BY date DESC
        ''').fetchall()]

    # --- Expense Reports ---
    
    def get_expenses_by_category(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        conn = self.db.get_connection()
        return [dict(row) for row in conn.execute('''
            SELECT category, category as category_name, SUM(amount) as total_amount
            FROM expenses
            WHERE status = 'Completed' AND date >= ? AND date <= ?
            GROUP BY category
            ORDER BY total_amount DESC
        ''', (start_date, end_date)).fetchall()]
        
    def get_daily_expense_totals(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        conn = self.db.get_connection()
        return [dict(row) for row in conn.execute('''
            SELECT date, COUNT(id) as expense_count, SUM(amount) as total_amount
            FROM expenses
            WHERE status = 'Completed' AND date >= ? AND date <= ?
            GROUP BY date
            ORDER BY date
        ''', (start_date, end_date)).fetchall()]

    def get_voided_expenses(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        conn = self.db.get_connection()
        return [dict(row) for row in conn.execute('''
            SELECT * FROM expenses
            WHERE status = 'Voided' AND date >= ? AND date <= ?
            ORDER BY date DESC, id DESC
        ''', (start_date, end_date)).fetchall()]

    def get_sales(self, start_date: str = None, end_date: str = None, include_voided: bool = True) -> List[Dict[str, Any]]:
        conn = self.db.get_connection()
        query = '''
            SELECT s.id, s.reference, s.date_time, s.subtotal, s.discount_amount, s.total_amount, 
                   s.amount_received, s.change_given, s.payment_type, s.customer_id, s.credit_amount, s.status,
                   c.name as customer_name,
                   COUNT(si.id) as items_count
            FROM sales s
            LEFT JOIN sale_items si ON s.id = si.sale_id
            LEFT JOIN customers c ON s.customer_id = c.id
            WHERE 1=1
        '''
        params = []
        if start_date:
            query += " AND substr(s.date_time, 1, 10) >= ?"
            params.append(start_date)
        if end_date:
            query += " AND substr(s.date_time, 1, 10) <= ?"
            params.append(end_date)
        if not include_voided:
            query += " AND s.status = 'Completed'"
        query += " GROUP BY s.id ORDER BY s.date_time DESC, s.id DESC"
        return [dict(row) for row in conn.execute(query, params).fetchall()]
